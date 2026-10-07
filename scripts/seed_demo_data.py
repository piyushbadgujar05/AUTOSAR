import os
import shutil
from backend.app.core.config import settings
from backend.app.models import init_db, SessionLocal
from backend.app.models.document import Document
from backend.app.models.chunk import Chunk
from backend.app.models.analysis import AuditLog
from backend.app.services.pdf_service import PDFService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.vector_service import VectorService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.inconsistency_service import InconsistencyService
from backend.app.core.logging import logger

def seed_document(pdf_name: str, version: str, project: str = "ADAS Control System"):
    src_path = os.path.join(settings.SAMPLE_DOCS_DIR, pdf_name)
    if not os.path.exists(src_path):
        logger.error(f"Sample PDF {src_path} not found.")
        return None

    dest_path = os.path.join(settings.UPLOAD_DIR, pdf_name)
    shutil.copy2(src_path, dest_path)

    db = SessionLocal()
    try:
        # Check if already present
        existing = db.query(Document).filter(Document.name == pdf_name, Document.version == version).first()
        if existing:
            logger.info(f"Document {pdf_name} (v{version}) is already indexed. ID: {existing.id}")
            return existing

        doc_record = Document(
            name=pdf_name,
            project=project,
            version=version,
            file_path=dest_path,
            document_type="High-Level Design",
            description="Synthetic Demo HLD — For Demonstration Only",
            file_size=os.path.getsize(dest_path),
            status="PROCESSING"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        pages_data, _ = PDFService.extract_text_and_sections(dest_path)
        doc_record.total_pages = len(pages_data)

        chunks = ChunkingService.create_section_aware_chunks(
            document_id=doc_record.id,
            document_name=doc_record.name,
            version=doc_record.version,
            pages_data=pages_data
        )
        doc_record.chunk_count = len(chunks)

        for c in chunks:
            db.add(Chunk(
                document_id=doc_record.id,
                page_number=c["page_number"],
                section=c["section"],
                content=c["content"],
                chunk_id=c["chunk_id"]
            ))
        db.commit()

        # Chroma vector indexing
        VectorService.get_instance().add_chunks(project_name=project, chunks=chunks)

        # Entity extraction
        ExtractionService.extract_architecture_from_chunks(
            db=db,
            document_id=doc_record.id,
            document_name=doc_record.name,
            chunks=chunks
        )

        # Inconsistency detection
        findings = InconsistencyService.detect_inconsistencies(db=db, document_id=doc_record.id)

        doc_record.status = "INDEXED"
        db.add(AuditLog(
            user="System Seeder",
            action="SEED_DEMO_DATA",
            details=f"Successfully seeded {pdf_name} (v{version}) with {len(chunks)} chunks and {len(findings)} findings."
        ))
        db.commit()

        logger.info(f"Seeded {pdf_name} (v{version}): {len(chunks)} chunks, {len(pages_data)} pages, {len(findings)} findings.")
        return doc_record
    finally:
        db.close()

def main():
    init_db()
    logger.info("Seeding Demo HLD documents...")
    doc1 = seed_document("ADAS_HLD_v1.0.pdf", version="1.0")
    doc2 = seed_document("ADAS_HLD_v2.0.pdf", version="2.0")
    logger.info("Demo data seeding completed successfully!")

if __name__ == "__main__":
    main()
