from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class SourceCitation(BaseModel):
    document: str
    page: int
    section: str
    snippet: Optional[str] = None
    similarity_score: Optional[float] = None

class ChatQueryRequest(BaseModel):
    query: str
    project: Optional[str] = None
    document_id: Optional[str] = None
    version: Optional[str] = None
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatQueryResponse(BaseModel):
    answer: str
    confidence: str  # HIGH, MEDIUM, LOW
    sources: List[SourceCitation]
    retrieved_chunks: int
    evidence: Optional[str] = None
    retrieval_details: Optional[List[Dict[str, Any]]] = None
    query_time_ms: Optional[float] = None
    model_used: Optional[str] = None
    # Debug observability metadata (Requirement 18)
    collection_name: Optional[str] = None
    candidate_count: Optional[int] = None
    project_filter: Optional[str] = None
    version_filter: Optional[str] = None
    document_filter: Optional[str] = None
    embedding_model: Optional[str] = None
    similarity_threshold_applied: Optional[float] = None

class DebugRetrievalRequest(BaseModel):
    query: str
    project: Optional[str] = "ADAS Control System"
    version: Optional[str] = None
    document_id: Optional[str] = None
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = None

class DebugRetrievalResultItem(BaseModel):
    score: float
    page: int
    section: str
    document: str
    version: str
    text_preview: str

class DebugRetrievalResponse(BaseModel):
    query: str
    collection: str
    filters: Dict[str, Any]
    candidate_count: int
    retrieved_count: int
    results: List[DebugRetrievalResultItem]
