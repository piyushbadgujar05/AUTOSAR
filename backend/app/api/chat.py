from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.models.base import get_db
from backend.app.models.analysis import AuditLog
from backend.app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    DebugRetrievalRequest,
    DebugRetrievalResponse,
    DebugRetrievalResultItem
)
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_service import VectorService
from backend.app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/query", response_model=ChatQueryResponse)
def query_architecture(req: ChatQueryRequest, db: Session = Depends(get_db)):
    """
    RAG-based Automotive Engineering Q&A query:
    1. Preprocesses query
    2. Searches ChromaDB for top-K section-aware chunks
    3. Synthesizes response adhering strictly to automotive engineering rules
    4. Computes confidence and page citations
    5. Audits query action
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    rag_service = RAGService()
    project = req.project or "default"

    response = rag_service.query(
        query=req.query,
        project_name=project,
        document_id=req.document_id,
        version=req.version,
        top_k=req.top_k or 5,
        similarity_threshold=req.similarity_threshold,
        conversation_history=req.conversation_history
    )

    # Audit log
    db.add(AuditLog(
        user="Engineer",
        action="QUERY_EXECUTED",
        details=f"Asked: '{req.query}' | Confidence: {response.confidence} | Chunks: {response.retrieved_chunks}"
    ))
    db.commit()

    return response

@router.post("/debug/retrieval", response_model=DebugRetrievalResponse)
def debug_retrieval_endpoint(req: DebugRetrievalRequest):
    """
    Development/debugging endpoint (Requirement 17) to inspect raw vector retrieval,
    candidate counts, collection, and score filtering without LLM synthesis.
    """
    vector_service = VectorService.get_instance()
    results, search_meta = vector_service.similarity_search_with_meta(
        query=req.query,
        project_name=req.project or "default",
        top_k=req.top_k or 5,
        document_id=req.document_id,
        version=req.version,
        similarity_threshold=req.similarity_threshold
    )
    result_items = []
    for r in results:
        meta = r.get("metadata") or {}
        result_items.append(DebugRetrievalResultItem(
            score=r.get("similarity", 0.0),
            page=int(meta.get("page_number", 1)),
            section=str(meta.get("section", "General")),
            document=str(meta.get("document_name", "Unknown")),
            version=str(meta.get("version", "1.0")),
            text_preview=r.get("content", "")[:200]
        ))
    return DebugRetrievalResponse(
        query=req.query,
        collection=search_meta.get("collection_name", "unknown"),
        filters=search_meta.get("filter_dict", {}),
        candidate_count=search_meta.get("candidate_count", 0),
        retrieved_count=len(result_items),
        results=result_items
    )

