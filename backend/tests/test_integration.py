import os
import pytest
from backend.app.core.config import settings
from backend.app.models import SessionLocal
from backend.app.models.document import Document
from backend.app.services.rag_service import RAGService

def test_full_rag_integration_pipeline():
    """
    Integration test:
    Validates indexed PDF documents can be queried via RAG to retrieve
    grounded answers with verifiable citations and confidence scores.
    """
    db = SessionLocal()
    try:
        # Verify indexed document exists
        doc = db.query(Document).filter(Document.version == "2.0").first()
        if not doc:
            pytest.skip("No seeded document found. Run scripts/seed_demo_data.py first.")

        rag = RAGService()
        response = rag.query(
            query="What does ADASController depend on?",
            project_name=doc.project,
            document_id=doc.id,
            top_k=5
        )

        assert response.retrieved_chunks > 0
        assert response.confidence in ["HIGH", "MEDIUM", "LOW"]
        assert len(response.sources) > 0
        assert any(s.page in [5, 7, 10] for s in response.sources)
        assert len(response.answer) > 20
    finally:
        db.close()
