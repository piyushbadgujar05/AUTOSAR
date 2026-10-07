import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.models.base import get_db
from backend.app.models.analysis import AuditLog
from backend.app.schemas.analysis import ReportGenerateRequest, ReportGenerateResponse
from backend.app.services.report_service import ReportService
from backend.app.core.config import settings

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate", response_model=ReportGenerateResponse)
def generate_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    """Generate comprehensive automotive architecture engineering report in JSON or PDF."""
    try:
        target_doc_id = req.document_id
        if not target_doc_id:
            from backend.app.models.document import Document
            q = db.query(Document)
            if req.project:
                q = q.filter(Document.project == req.project)
            doc_obj = q.order_by(Document.upload_date.desc()).first()
            if not doc_obj:
                raise HTTPException(status_code=404, detail="No indexed document found to generate report.")
            target_doc_id = doc_obj.id

        report_data = ReportService.generate_report_data(db, target_doc_id)
        report_id = str(uuid.uuid4())[:8]
        doc_info = report_data.get("2_document", {})
        doc_name = doc_info.get("document_name", "AUTOSAR_Doc").replace(".pdf", "")

        if req.report_format.lower() == "pdf":
            filename = f"Report_{doc_name}_{report_id}.pdf"
            output_path = os.path.join(settings.PROCESSED_DIR, filename)
            ReportService.generate_pdf_report(report_data, output_path)
            
            # Audit
            db.add(AuditLog(
                user="Engineer",
                action="REPORT_GENERATED",
                details=f"Generated PDF architecture report for {doc_name}: {filename}"
            ))
            db.commit()

            return ReportGenerateResponse(
                report_id=report_id,
                report_type="PDF",
                file_path=f"/api/reports/download/{filename}",
                data=None
            )
        else:
            # JSON format
            filename = f"Report_{doc_name}_{report_id}.json"
            output_path = os.path.join(settings.PROCESSED_DIR, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)

            db.add(AuditLog(
                user="Engineer",
                action="REPORT_GENERATED",
                details=f"Generated JSON architecture report for {doc_name}: {filename}"
            ))
            db.commit()

            return ReportGenerateResponse(
                report_id=report_id,
                report_type="JSON",
                file_path=f"/api/reports/download/{filename}",
                data=report_data
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/download/{filename}")
def download_report(filename: str):
    """Download generated engineering report."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(settings.PROCESSED_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested report file not found.")

    media_type = "application/pdf" if safe_name.endswith(".pdf") else "application/json"
    return FileResponse(file_path, media_type=media_type, filename=safe_name)
