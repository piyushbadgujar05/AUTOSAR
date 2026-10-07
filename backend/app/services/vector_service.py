import re
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.normalization import normalize_version, normalize_project_name
from backend.app.services.embedding_service import EmbeddingService

class VectorService:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        logger.info(f"Initializing persistent ChromaDB client at {settings.CHROMA_PATH}")
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_service = EmbeddingService.get_instance()

    def _sanitize_collection_name(self, name: str) -> str:
        """Chroma collection names must be 3-63 chars, start/end with alphanum, contain only alphanum, _ or -."""
        cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.lower().strip())
        cleaned = re.sub(r'_+', '_', cleaned)
        cleaned = cleaned.strip('_-')
        if len(cleaned) < 3:
            cleaned = f"col_{cleaned}"
        return cleaned[:63]

    def get_or_create_collection(self, project_name: str = "default"):
        canonical_proj = normalize_project_name(project_name)
        col_name = self._sanitize_collection_name(f"project_{canonical_proj}")
        return self._client.get_or_create_collection(
            name=col_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, project_name: str, chunks: List[Dict[str, Any]]):
        """Insert section-aware chunks into ChromaDB."""
        if not chunks:
            return

        canonical_proj = normalize_project_name(project_name)
        collection = self.get_or_create_collection(canonical_proj)

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["content"] for c in chunks]
        metadatas = [
            {
                "chunk_id": str(c["chunk_id"]),
                "document_id": str(c["document_id"]),
                "document_name": str(c["document_name"]),
                "version": str(normalize_version(c.get("version")) or "1.0"),
                "page_number": int(c["page_number"]),
                "section": str(c["section"]),
                "project": str(canonical_proj)
            }
            for c in chunks
        ]

        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_service.embed_texts(texts)

        batch_size = 200
        for i in range(0, len(ids), batch_size):
            end_idx = i + batch_size
            collection.upsert(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )

        logger.info(f"Successfully indexed {len(ids)} chunks in ChromaDB collection '{collection.name}'")

    def similarity_search_with_meta(
        self,
        query: str,
        project_name: str = "default",
        top_k: int = 5,
        document_id: Optional[str] = None,
        version: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Perform semantic search and return (retrieved_chunks, search_metadata).
        search_metadata contains:
            - collection_name
            - filter_dict
            - candidate_count
            - retrieved_count
        """
        canonical_proj = normalize_project_name(project_name)
        collection = self.get_or_create_collection(canonical_proj)
        
        search_meta = {
            "collection_name": collection.name,
            "filter_dict": {},
            "candidate_count": 0,
            "retrieved_count": 0,
            "project": canonical_proj,
            "normalized_version": normalize_version(version),
            "document_id": document_id
        }

        if collection.count() == 0:
            logger.warning(f"ChromaDB collection '{collection.name}' is empty.")
            return [], search_meta

        query_embedding = self.embedding_service.embed_query(query)
        
        # Build ChromaDB metadata filter
        conditions = []
        norm_v = normalize_version(version)
        
        if document_id:
            conditions.append({"document_id": str(document_id)})
        elif norm_v:
            conditions.append({"version": str(norm_v)})

        if where_filter:
            for k, v in where_filter.items():
                conditions.append({k: v})

        filter_dict = None
        if len(conditions) == 1:
            filter_dict = conditions[0]
        elif len(conditions) > 1:
            filter_dict = {"$and": conditions}

        search_meta["filter_dict"] = filter_dict or {}

        # Fetch candidates
        fetch_k = min(max(top_k * 2, 10), max(1, collection.count()))
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": fetch_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if filter_dict:
            kwargs["where"] = filter_dict

        try:
            results = collection.query(**kwargs)
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return [], search_meta

        retrieved = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)

            search_meta["candidate_count"] = len(docs)

            candidates_with_score = []
            for doc, meta, dist in zip(docs, metas, distances):
                sim = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
                candidates_with_score.append({
                    "content": doc,
                    "metadata": meta,
                    "similarity": round(sim, 3)
                })

            # Apply similarity threshold
            if similarity_threshold is not None and similarity_threshold > 0:
                filtered = [c for c in candidates_with_score if c["similarity"] >= similarity_threshold]
                if filtered:
                    retrieved = filtered[:top_k]
                else:
                    # Fallback to candidates above minimal noise floor
                    top_candidates = [c for c in candidates_with_score if c["similarity"] >= 0.02]
                    retrieved = top_candidates[:top_k]
            else:
                retrieved = candidates_with_score[:top_k]

            search_meta["retrieved_count"] = len(retrieved)

        return retrieved, search_meta

    def similarity_search(
        self,
        query: str,
        project_name: str = "default",
        top_k: int = 5,
        document_id: Optional[str] = None,
        version: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Backward-compatible wrapper returning List[Dict[str, Any]]."""
        results, _ = self.similarity_search_with_meta(
            query=query,
            project_name=project_name,
            top_k=top_k,
            document_id=document_id,
            version=version,
            similarity_threshold=similarity_threshold,
            where_filter=where_filter
        )
        return results

    def delete_document_chunks(self, project_name: str, document_id: str):
        """Remove chunks for a deleted document."""
        canonical_proj = normalize_project_name(project_name)
        collection = self.get_or_create_collection(canonical_proj)
        try:
            collection.delete(where={"document_id": str(document_id)})
            logger.info(f"Deleted chunks for document {document_id} from collection {collection.name}")
        except Exception as e:
            logger.warning(f"Failed to delete chunks for document {document_id}: {e}")
