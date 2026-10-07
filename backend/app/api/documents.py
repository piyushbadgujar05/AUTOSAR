import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.base import get_db
from backend.app.models.document import Document
from backend.app.models.chunk import Chunk
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.models.analysis import Finding, AuditLog
from backend.app.schemas.document import DocumentResponse
from backend.app.core.config import settings
from backend.app.core.security import sanitize_filename, validate_uploaded_pdf
from backend.app.core.normalization import normalize_project_name, normalize_version, extract_version_from_filename_or_text
from backend.app.core.logging import logger
from backend.app.services.pdf_service import PDFService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.vector_service import VectorService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.inconsistency_service import InconsistencyService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    project: str = Form("ADAS Control System"),
    version: str = Form("1.0"),
    document_type: str = Form("High-Level Design"),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and index an automotive HLD PDF:
    1. Validate and save PDF
    2. Extract page-by-page text & headings via PyMuPDF
    3. Generate section-aware chunks
    4. Index chunks in ChromaDB with embeddings
    5. Extract architectural entities and relationships
    6. Execute consistency check rules
    7. Record audit log
    """
    validate_uploaded_pdf(file)
    safe_name = sanitize_filename(file.filename)

    canonical_proj = normalize_project_name(project)
    # Detect version from filename or normalize supplied version
    detected_ver = extract_version_from_filename_or_text(safe_name)
    if detected_ver:
        canonical_ver = normalize_version(detected_ver)
    else:
        canonical_ver = normalize_version(version) or "1.0"

    # Compute SHA-256 hash of file for deduplication
    import hashlib
    file_bytes = file.file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file.file.seek(0)

    # Check if duplicate already indexed
    existing_doc = db.query(Document).filter(
        (Document.file_hash == file_hash) |
        ((Document.name == safe_name) & (Document.version == canonical_ver) & (Document.project == canonical_proj))
    ).first()

    if existing_doc and existing_doc.status == "INDEXED":
        logger.info(f"Document already indexed: {safe_name} (v{canonical_ver})")
        raise HTTPException(
            status_code=409,
            detail="Document already indexed."
        )
    
    # Save file to uploads folder
    save_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file {safe_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to write file to disk.")

    file_size = os.path.getsize(save_path)

    # Create document record
    doc_record = Document(
        name=safe_name,
        project=canonical_proj,
        version=canonical_ver,
        file_path=save_path,
        document_type=document_type,
        description=description,
        file_size=file_size,
        file_hash=file_hash,
        status="PROCESSING"
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    try:
        # Step 1: Parse PDF
        pages_data, meta = PDFService.extract_text_and_sections(save_path)
        doc_record.total_pages = len(pages_data)

        # Step 2: Create section-aware chunks
        chunks = ChunkingService.create_section_aware_chunks(
            document_id=doc_record.id,
            document_name=doc_record.name,
            version=doc_record.version,
            project=doc_record.project,
            pages_data=pages_data
        )
        doc_record.chunk_count = len(chunks)

        # Step 3: Save chunks to SQLite
        for c in chunks:
            db_chunk = Chunk(
                document_id=doc_record.id,
                page_number=c["page_number"],
                section=c["section"],
                content=c["content"],
                chunk_id=c["chunk_id"]
            )
            db.add(db_chunk)
        db.commit()

        # Step 4: Index chunks into ChromaDB
        vector_service = VectorService.get_instance()
        vector_service.add_chunks(project_name=doc_record.project, chunks=chunks)

        # Step 5: Extract architecture entities & relationships
        ExtractionService.extract_architecture_from_chunks(
            db=db,
            document_id=doc_record.id,
            document_name=doc_record.name,
            chunks=chunks
        )

        # Step 6: Trigger rule-based consistency analysis
        InconsistencyService.detect_inconsistencies(db=db, document_id=doc_record.id)

        # Step 7: Update status
        doc_record.status = "INDEXED"
        db.commit()

        # Audit log
        db.add(AuditLog(
            user="Engineer",
            action="DOCUMENT_UPLOADED",
            details=f"Uploaded and indexed {safe_name} (v{canonical_ver}, ID: {doc_record.id}) with {len(chunks)} chunks across {len(pages_data)} pages."
        ))
        db.commit()

        logger.info(f"Successfully processed document {doc_record.id} ({safe_name})")
        return doc_record

    except Exception as e:
        db.rollback()
        doc_record.status = "ERROR"
        db.commit()
        logger.error(f"Error processing PDF {safe_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error indexing document: {str(e)}"
        )

@router.get("", response_model=List[DocumentResponse])
def list_documents(project: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if project:
        query = query.filter(Document.project == project)
    return query.order_by(Document.upload_date.desc()).all()

@router.get("/{id}", response_model=DocumentResponse)
def get_document(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{id}")
def delete_document(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from Chroma
    vector_service = VectorService.get_instance()
    vector_service.delete_document_chunks(doc.project, doc.id)

    # Remove file on disk if exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Could not remove file {doc.file_path}: {e}")

    # Audit log
    db.add(AuditLog(
        user="Admin",
        action="DOCUMENT_DELETED",
        details=f"Deleted document {doc.name} ({doc.id})"
    ))

    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.name}' deleted successfully"}

@router.post("/{id}/reindex")
def reindex_document(id: str, db: Session = Depends(get_db)):
    """
    Re-index document (Requirement 30):
    1. Delete old ChromaDB chunks
    2. Re-extract PDF
    3. Recreate chunks with canonical normalized metadata
    4. Regenerate embeddings and index to ChromaDB
    5. Refresh architectural entities and consistency findings
    6. Verify vector count and update document status to INDEXED
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail=f"Document file not found at {doc.file_path}")

    # Canonicalize project and version
    canonical_proj = normalize_project_name(doc.project)
    doc.project = canonical_proj

    # Check if filename has an explicit version that overrides stale version
    detected_ver = extract_version_from_filename_or_text(doc.name)
    if detected_ver:
        doc.version = normalize_version(detected_ver)
    else:
        doc.version = normalize_version(doc.version) or "1.0"

    doc.status = "PROCESSING"
    db.commit()

    try:
        # 1. Delete old vector records
        vector_service = VectorService.get_instance()
        vector_service.delete_document_chunks(doc.project, doc.id)

        # Delete existing DB chunks, architecture entities, and findings
        db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
        db.query(ArchitectureEntity).filter(ArchitectureEntity.document_id == doc.id).delete()
        db.query(Relationship).filter(Relationship.document_id == doc.id).delete()
        db.query(Finding).filter(Finding.document_id == doc.id).delete()
        db.commit()

        # 2. Re-extract PDF
        pages_data, _ = PDFService.extract_text_and_sections(doc.file_path)
        doc.total_pages = len(pages_data)

        # 3. Recreate chunks
        chunks = ChunkingService.create_section_aware_chunks(
            document_id=doc.id,
            document_name=doc.name,
            version=doc.version,
            project=doc.project,
            pages_data=pages_data
        )
        doc.chunk_count = len(chunks)

        # 4. Save chunks to SQLite
        for c in chunks:
            db_chunk = Chunk(
                document_id=doc.id,
                page_number=c["page_number"],
                section=c["section"],
                content=c["content"],
                chunk_id=c["chunk_id"]
            )
            db.add(db_chunk)
        db.commit()

        # 5. Index chunks into ChromaDB
        vector_service.add_chunks(project_name=doc.project, chunks=chunks)

        # 6. Re-extract architecture & consistency findings
        entities, rels = ExtractionService.extract_architecture_from_chunks(
            db=db,
            document_id=doc.id,
            document_name=doc.name,
            chunks=chunks
        )
        InconsistencyService.detect_inconsistencies(db=db, document_id=doc.id)

        # 7. Update status to INDEXED
        doc.status = "INDEXED"
        db.commit()

        # Audit log
        db.add(AuditLog(
            user="Engineer",
            action="DOCUMENT_REINDEXED",
            details=f"Re-indexed {doc.name} (v{doc.version}, ID: {doc.id}) with {len(chunks)} chunks across {len(pages_data)} pages."
        ))
        db.commit()

        collection = vector_service.get_or_create_collection(doc.project)
        comp_count = len([e for e in entities if e.entity_type == "COMPONENT"])
        interface_count = len([e for e in entities if e.entity_type == "INTERFACE"])

        return {
            "message": "Document Re-indexed Successfully",
            "document": doc.name,
            "version": doc.version,
            "project": doc.project,
            "pages": doc.total_pages,
            "chunks": doc.chunk_count,
            "embeddings": doc.chunk_count,
            "components": comp_count,
            "interfaces": interface_count,
            "relationships": len(rels),
            "vector_collection": collection.name,
            "status": doc.status
        }
    except Exception as e:
        db.rollback()
        doc.status = "ERROR"
        db.commit()
        logger.error(f"Error re-indexing document {doc.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error re-indexing document: {str(e)}")

