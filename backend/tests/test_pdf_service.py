import os
import pytest
from backend.app.services.pdf_service import PDFService
from backend.app.core.config import settings

def test_pdf_extraction():
    sample_path = os.path.join(settings.SAMPLE_DOCS_DIR, "ADAS_HLD_v1.0.pdf")
    if not os.path.exists(sample_path):
        pytest.skip("Sample PDF not found.")

    pages_data, metadata = PDFService.extract_text_and_sections(sample_path)
    assert len(pages_data) >= 10
    assert metadata["page_count"] >= 10
    assert pages_data[0]["page_number"] == 1
    assert "content" in pages_data[0]
    assert len(pages_data[0]["content"]) > 20

def test_pdf_scanned_detection():
    # Test handling of empty or scanned document
    import fitz
    empty_pdf_path = os.path.join(settings.PROCESSED_DIR, "test_empty.pdf")
    doc = fitz.open()
    doc.new_page()
    doc.save(empty_pdf_path)
    doc.close()

    try:
        with pytest.raises(ValueError) as excinfo:
            PDFService.extract_text_and_sections(empty_pdf_path)
        assert "scanned" in str(excinfo.value).lower()
    finally:
        if os.path.exists(empty_pdf_path):
            os.remove(empty_pdf_path)
