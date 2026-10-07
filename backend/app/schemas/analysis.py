from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class FindingBase(BaseModel):
    finding_type: str
    title: str
    description: str
    severity: str = "MEDIUM"
    confidence: float = 0.85
    status: str = "NEW"
    evidence: Optional[str] = None
    source_page: int = 1

class FindingResponse(FindingBase):
    id: int
    document_id: str
    created_at: datetime
    reviews: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)

class ReviewCreate(BaseModel):
    reviewer: str = "Engineering Reviewer"
    status: str  # NEW, UNDER_REVIEW, ACCEPTED, REJECTED, RESOLVED, NEEDS_REVIEW
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    finding_id: int
    reviewer: str
    status: str
    comment: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    user: str
    action: str
    details: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ComparisonRequest(BaseModel):
    doc1_id: str
    doc2_id: str

class EntityDiff(BaseModel):
    added: List[str] = []
    removed: List[str] = []
    changed: List[Dict[str, Any]] = []

class ComparisonResponse(BaseModel):
    doc1_id: str
    doc1_name: str
    doc1_version: str
    doc2_id: str
    doc2_name: str
    doc2_version: str
    components_diff: EntityDiff
    interfaces_diff: EntityDiff
    dependencies_diff: EntityDiff
    potential_impacts: List[Dict[str, Any]] = []
    summary: str

class ReportGenerateRequest(BaseModel):
    document_id: Optional[str] = None
    project: Optional[str] = None
    report_format: str = "json"  # "json" or "pdf"

class ReportGenerateResponse(BaseModel):
    report_id: str
    report_type: str
    file_path: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
