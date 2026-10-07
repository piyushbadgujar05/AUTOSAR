import os
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models import SessionLocal, init_db
from backend.app.models.document import Document
from backend.app.services.vector_service import VectorService
from backend.app.services.pdf_service import PDFService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.inconsistency_service import InconsistencyService

def rebuild_all():
    init_db()
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        logger.info(f"Rebuilding index for {len(documents)} documents...")
        vector_service = VectorService.get_instance()

        for doc in documents:
            if not os.path.exists(doc.file_path):
                logger.warning(f"File {doc.file_path} not found. Skipping.")
                continue

            logger.info(f"Rebuilding {doc.name} (v{doc.version})...")
            # Clear existing chunks from Chroma
            vector_service.delete_document_chunks(doc.project, doc.id)

            # Re-parse
            pages_data, _ = PDFService.extract_text_and_sections(doc.file_path)
            doc.total_pages = len(pages_data)

            chunks = ChunkingService.create_section_aware_chunks(
                document_id=doc.id,
                document_name=doc.name,
                version=doc.version,
                pages_data=pages_data
            )
            doc.chunk_count = len(chunks)

            # Re-index vectors
            vector_service.add_chunks(project_name=doc.project, chunks=chunks)

            # Refresh architecture & findings
            ExtractionService.extract_architecture_from_chunks(db, doc.id, doc.name, chunks)
            InconsistencyService.detect_inconsistencies(db, doc.id)

            doc.status = "INDEXED"
            db.commit()

        logger.info("All documents successfully re-indexed.")
    finally:
        db.close()

if __name__ == "__main__":
    rebuild_all()
