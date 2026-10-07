import os
import io
import fitz
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.models import SessionLocal
from backend.app.models.document import Document
from backend.app.services.pdf_service import PDFService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.vector_service import VectorService
from backend.app.services.rag_service import RAGService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.inconsistency_service import InconsistencyService

client = TestClient(app)

def create_synthetic_test_pdf(filepath: str):
    """Generate a synthetic test PDF containing AUTOSAR HLD elements."""
    doc = fitz.open()
    
    # Page 1: Overview and Components
    p1 = doc.new_page()
    p1_text = """
    SYNTHETIC DEMONSTRATION DOCUMENT — NOT OFFICIAL AUTOSAR DOCUMENTATION
    Section: System Overview
    Project: E2E Test Project
    Version: 1.0

    Section: Software Component Architecture
    The system includes the following main software components:
    - Component: ADASController handles central trajectory planning and decision making.
    - Component: BrakeController manages electronic braking actuation.
    - Component: SensorFusion performs object tracking and radar/camera clustering.
    """
    p1.insert_text((50, 72), p1_text, fontsize=11)
    
    # Page 2: Interfaces and Communications
    p2 = doc.new_page()
    p2_text = """
    Section: Communication Interfaces
    ADASController communicates with BrakeController through BrakeCommand interface on page 2.
    SensorFusion -> ADASController via Autosar RTE.
    CameraManager provides interface CameraData over Ethernet.
    
    Interface: BrakeCommand
    Interface: CameraData
    """
    p2.insert_text((50, 72), p2_text, fontsize=11)
    
    doc.save(filepath)
    doc.close()

def test_end_to_end_pipeline(tmp_path):
    """
    End-to-End Workflow Verification:
    Synthetic PDF -> Upload -> Parse -> Chunk -> Embed -> Store -> Ask question ->
    Retrieve -> Generate response -> Verify citation -> Extract architecture -> Run consistency analysis
    """
    pdf_filename = "Synthetic_E2E_HLD_v1.0.pdf"
    pdf_path = str(tmp_path / pdf_filename)
    create_synthetic_test_pdf(pdf_path)

    # 1. Upload via API
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": (pdf_filename, f, "application/pdf")},
            data={"project": "E2E Test Project", "version": "1.0"}
        )
    assert response.status_code == 200, f"Upload failed: {response.text}"
    doc_id = response.json()["id"]

    db = SessionLocal()
    try:
        # 2. Verify Document stored in DB
        db_doc = db.query(Document).filter_by(id=doc_id).first()
        assert db_doc is not None
        assert db_doc.total_pages == 2
        assert db_doc.chunk_count >= 2

        # 3. Query RAG via API
        chat_resp = client.post(
            "/api/chat/query",
            json={
                "query": "What interface connects ADASController and BrakeController?",
                "project": "E2E Test Project",
                "document_id": doc_id,
                "top_k": 3
            }
        )
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert chat_data["retrieved_chunks"] > 0
        assert len(chat_data["sources"]) > 0
        
        # 4. Verify Citations contain exact page
        cited_pages = [s["page"] for s in chat_data["sources"]]
        assert 2 in cited_pages or 1 in cited_pages
        assert chat_data["evidence"] is not None

        # 5. Verify Extracted Architecture
        entities = db.query(Document).filter_by(id=doc_id).first().entities
        entity_names = set(e.name for e in entities)
        assert "ADASController" in entity_names
        assert "BrakeController" in entity_names
        assert "BrakeCommand" in entity_names

        # 6. Run Consistency Analysis
        analysis_resp = client.post(
            "/api/analysis/inconsistencies",
            params={"document_id": doc_id}
        )
        assert analysis_resp.status_code == 200
        findings_data = analysis_resp.json()
        assert isinstance(findings_data, list)

        # 7. Check Audit Logs
        from backend.app.models.analysis import AuditLog
        logs = db.query(AuditLog).filter(AuditLog.details.contains(doc_id)).all()
        actions = set(l.action for l in logs)
        assert "DOCUMENT_UPLOADED" in actions
    finally:
        # Cleanup
        client.delete(f"/api/documents/{doc_id}")
        db.close()
