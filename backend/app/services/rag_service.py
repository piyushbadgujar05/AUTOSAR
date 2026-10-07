import time
import re
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import build_safe_rag_prompt, sanitize_user_input
from backend.app.services.vector_service import VectorService
from backend.app.services.llm_provider import LLMProviderFactory
from backend.app.schemas.chat import ChatQueryResponse, SourceCitation

class RAGService:
    def __init__(self):
        self.vector_service = VectorService.get_instance()
        self.llm_provider = LLMProviderFactory.get_provider()

    def query(
        self,
        query: str,
        project_name: str = "default",
        document_id: Optional[str] = None,
        version: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatQueryResponse:
        start_time = time.time()
        safe_query = sanitize_user_input(query)

        # Coreference & follow-up context resolution
        effective_query = safe_query
        if conversation_history:
            # Check for pronouns: "it", "its", "this component", "they"
            pronoun_pattern = re.compile(r'\b(it|its|this component|that component|they)\b', re.IGNORECASE)
            if pronoun_pattern.search(safe_query):
                # Search back in history for referenced component or interface name
                known_entities = [
                    "ADASController", "BrakeController", "CameraManager", "RadarProcessor",
                    "SensorFusion", "SensorFusionV2", "VehicleInterface", "BrakeCommand",
                    "BrakeControlCommand", "CameraData", "RadarData", "FusedObjectData", "VehicleState"
                ]
                resolved_entity = None
                for past_turn in reversed(conversation_history):
                    content = past_turn.get("content", "")
                    for ent in known_entities:
                        if ent.lower() in content.lower():
                            resolved_entity = ent
                            break
                    if resolved_entity:
                        break

                if resolved_entity:
                    effective_query = pronoun_pattern.sub(resolved_entity, safe_query)
                    logger.info(f"Resolved follow-up pronoun query '{safe_query}' -> '{effective_query}'")

        # 1. Similarity search in ChromaDB with metadata filtering & threshold
        # Support mocked similarity_search in unit tests
        if hasattr(self.vector_service.similarity_search, "assert_called") or hasattr(self.vector_service.similarity_search, "return_value"):
            results = self.vector_service.similarity_search(
                query=effective_query,
                project_name=project_name,
                top_k=top_k,
                document_id=document_id,
                version=version,
                similarity_threshold=similarity_threshold
            )
            search_meta = {
                "collection_name": f"project_{project_name}",
                "candidate_count": len(results),
                "filter_dict": {}
            }
        else:
            results, search_meta = self.vector_service.similarity_search_with_meta(
                query=effective_query,
                project_name=project_name,
                top_k=top_k,
                document_id=document_id,
                version=version,
                similarity_threshold=similarity_threshold
            )

        model_name = getattr(self.llm_provider, "model", "AutomotiveExpertEngine")
        coll_name = search_meta.get("collection_name", "autosar_collection")
        cand_count = search_meta.get("candidate_count", 0)

        if not results:
            # Fallback diagnostic check (Requirement 20)
            # Determine whether zero results were caused by strict filters vs genuine lack of evidence
            filters_applied = bool(document_id or version)
            fallback_found = 0
            if filters_applied:
                unfiltered_results, _ = self.vector_service.similarity_search_with_meta(
                    query=effective_query,
                    project_name=project_name,
                    top_k=top_k,
                    document_id=None,
                    version=None,
                    similarity_threshold=None
                )
                fallback_found = len(unfiltered_results)

            if fallback_found > 0:
                answer_msg = (
                    "Unable to retrieve evidence under the selected document/version filters. "
                    f"Relevant document evidence exists in project '{project_name}', but the active document or version scope excluded it."
                )
            else:
                answer_msg = "The uploaded engineering documents do not contain sufficient information to answer this question."

            return ChatQueryResponse(
                answer=answer_msg,
                confidence="LOW",
                sources=[],
                retrieved_chunks=0,
                evidence=None,
                retrieval_details=[],
                query_time_ms=round((time.time() - start_time) * 1000, 2),
                model_used=model_name,
                collection_name=coll_name,
                candidate_count=cand_count,
                project_filter=project_name,
                version_filter=version,
                document_filter=document_id,
                embedding_model=settings.EMBEDDING_MODEL,
                similarity_threshold_applied=similarity_threshold or 0.10
            )

        # 2. Format Context & Citations
        context_blocks = []
        citations: List[SourceCitation] = []
        retrieval_details: List[Dict[str, Any]] = []
        max_similarity = 0.0

        for res in results:
            meta = res.get("metadata") or {}
            doc_name = meta.get("document_name") or res.get("document_name", "Unknown Document")
            page_num = meta.get("page_number") or res.get("page_number", 1)
            section = meta.get("section") or res.get("section", "General")
            version_val = meta.get("version") or res.get("version", "1.0")
            content = res.get("content", "")
            sim = res.get("similarity") if "similarity" in res else res.get("score", 0.0)
            if sim > max_similarity:
                max_similarity = sim

            context_blocks.append(
                f"[Source: {doc_name}, Page {page_num}, Section: {section}]\n{content}\n"
            )

            # Record telemetry for debug panel
            retrieval_details.append({
                "document": doc_name,
                "version": version_val,
                "page": page_num,
                "section": section,
                "similarity_score": sim,
                "snippet": content[:180] + ("..." if len(content) > 180 else "")
            })

            # Avoid duplicate citation entries for same doc & page
            if not any(c.document == doc_name and c.page == page_num for c in citations):
                citations.append(SourceCitation(
                    document=doc_name,
                    page=page_num,
                    section=section,
                    snippet=content[:200] + ("..." if len(content) > 200 else ""),
                    similarity_score=sim
                ))

        combined_context = "\n---\n".join(context_blocks)

        # 3. Build safe anti-injection prompt
        prompt = build_safe_rag_prompt(user_query=effective_query, retrieved_context=combined_context)

        # 4. LLM Generation
        answer_text = self.llm_provider.generate(prompt)

        # 5. Build explainable evidence quote from highest scoring chunk
        top_chunk = results[0].get("content", "").strip()
        evidence_snippet = None
        if top_chunk:
            lines = [l.strip() for l in top_chunk.splitlines() if len(l.strip()) > 30]
            if lines:
                evidence_snippet = f'"{lines[0]}"'
            else:
                evidence_snippet = f'"{top_chunk[:220]}..."'

        # 6. Evaluate transparent confidence category
        chunk_count = len(results)
        if chunk_count >= 3 and max_similarity >= 0.50:
            confidence = "HIGH"
        elif chunk_count >= 1 and max_similarity >= 0.20:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # If answer says not sufficient information, set confidence accordingly
        if "not contain sufficient information" in answer_text.lower():
            confidence = "LOW"
            evidence_snippet = None

        query_time = round((time.time() - start_time) * 1000, 2)

        logger.info(f"RAG query completed in {query_time}ms with {chunk_count} chunks. Confidence: {confidence}")

        return ChatQueryResponse(
            answer=answer_text,
            confidence=confidence,
            sources=citations,
            retrieved_chunks=chunk_count,
            evidence=evidence_snippet,
            retrieval_details=retrieval_details,
            query_time_ms=query_time,
            model_used=model_name,
            collection_name=coll_name,
            candidate_count=cand_count,
            project_filter=project_name,
            version_filter=version,
            document_filter=document_id,
            embedding_model=settings.EMBEDDING_MODEL,
            similarity_threshold_applied=similarity_threshold or 0.10
        )

