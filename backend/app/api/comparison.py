import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.models.base import get_db
from backend.app.models.analysis import ComparisonResult, AuditLog
from backend.app.schemas.analysis import ComparisonRequest, ComparisonResponse
from backend.app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/comparison", tags=["Revision Comparison"])

@router.post("", response_model=ComparisonResponse)
def compare_revisions(req: ComparisonRequest, db: Session = Depends(get_db)):
    """
    Compare two revisions of an AUTOSAR HLD document.
    Identifies added/removed/changed components, interfaces, dependencies,
    and potential architectural impacts requiring engineering review.
    """
    try:
        diff_res = ComparisonService.compare_documents(db, req.doc1_id, req.doc2_id)
        
        # Save comparison result
        comp_record = ComparisonResult(
            doc1_id=req.doc1_id,
            doc2_id=req.doc2_id,
            result_json=diff_res.model_dump_json()
        )
        db.add(comp_record)

        # Audit
        db.add(AuditLog(
            user="Engineer",
            action="REVISION_COMPARED",
            details=f"Compared {diff_res.doc1_name} (v{diff_res.doc1_version}) with {diff_res.doc2_name} (v{diff_res.doc2_version})"
        ))
        db.commit()

        return diff_res
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{id}")
def get_comparison_result(id: int, db: Session = Depends(get_db)):
    record = db.query(ComparisonResult).filter(ComparisonResult.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Comparison record not found")
    return json.loads(record.result_json)
