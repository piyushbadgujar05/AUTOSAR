from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.models.base import get_db
from backend.app.models.analysis import Finding, Review, AuditLog
from backend.app.schemas.analysis import FindingResponse, ReviewCreate, ReviewResponse, AuditLogResponse
from backend.app.services.inconsistency_service import InconsistencyService

router = APIRouter(tags=["Analysis & Consistency"])

@router.post("/analysis/inconsistencies", response_model=List[FindingResponse])
def run_inconsistency_detection(document_id: str = Query(...), db: Session = Depends(get_db)):
    """Run deterministic automotive rule engine to detect potential architectural inconsistencies."""
    findings = InconsistencyService.detect_inconsistencies(db=db, document_id=document_id)
    
    # Audit
    db.add(AuditLog(
        user="Engineer",
        action="CONSISTENCY_ANALYZED",
        details=f"Ran consistency rules for document {document_id}; detected {len(findings)} potential findings."
    ))
    db.commit()

    return findings

@router.get("/analysis/findings", response_model=List[FindingResponse])
def get_findings(
    document_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve detected architecture findings with human review statuses."""
    query = db.query(Finding)
    if document_id:
        query = query.filter(Finding.document_id == document_id)
    if status:
        query = query.filter(Finding.status == status.upper())
    if severity:
        query = query.filter(Finding.severity == severity.upper())
    
    findings = query.order_by(Finding.created_at.desc()).all()
    
    # Format with reviews
    response_items = []
    for f in findings:
        reviews = [
            {"id": r.id, "reviewer": r.reviewer, "status": r.status, "comment": r.comment, "timestamp": r.timestamp}
            for r in f.reviews
        ]
        item = FindingResponse(
            id=f.id,
            document_id=f.document_id,
            finding_type=f.finding_type,
            title=f.title,
            description=f.description,
            severity=f.severity,
            confidence=f.confidence,
            status=f.status,
            evidence=f.evidence,
            source_page=f.source_page,
            created_at=f.created_at,
            reviews=reviews
        )
        response_items.append(item)
    return response_items

@router.post("/findings/{id}/review", response_model=ReviewResponse)
def submit_human_review(id: int, review_in: ReviewCreate, db: Session = Depends(get_db)):
    """
    Submit human review decision for an architectural finding.
    Status supported: NEW, UNDER_REVIEW, ACCEPTED, REJECTED, RESOLVED.
    """
    finding = db.query(Finding).filter(Finding.id == id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found.")

    norm_status = review_in.status.strip().upper().replace(" ", "_")
    if norm_status == "NEEDS_REVIEW":
        norm_status = "UNDER_REVIEW"

    valid_statuses = ["NEW", "UNDER_REVIEW", "ACCEPTED", "REJECTED", "RESOLVED"]
    if norm_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid review status '{review_in.status}'. Must be one of {valid_statuses}")

    finding.status = norm_status

    new_review = Review(
        finding_id=finding.id,
        reviewer=review_in.reviewer,
        status=norm_status,
        comment=review_in.comment
    )
    db.add(new_review)

    # Audit
    db.add(AuditLog(
        user=review_in.reviewer,
        action="FINDING_REVIEWED",
        details=f"Finding #{id} marked as '{norm_status}'. Comment: {review_in.comment or 'None'}"
    ))

    db.commit()
    db.refresh(new_review)
    return new_review

@router.get("/audit", response_model=List[AuditLogResponse])
@router.get("/analysis/audit", response_model=List[AuditLogResponse])
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve chronological engineering and AI activity audit records."""
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
