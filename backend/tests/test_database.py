import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.document import Document
from backend.app.models.chunk import Chunk
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.models.analysis import Finding, Review, AuditLog

def test_database():
    engine = create_engine("sqlite:///:memory:")
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 1. Document creation
    doc = Document(
        id="doc_db_test",
        name="Test_Arch.pdf",
        project="ADAS",
        version="1.0",
        file_path="dummy.pdf",
        total_pages=5,
        chunk_count=2,
        file_hash="abc123hash"
    )
    db.add(doc)
    db.commit()

    # 2. Associated Chunks and Entities
    chunk = Chunk(
        document_id=doc.id,
        chunk_id="doc_db_test_p1_c0",
        page_number=1,
        section="Overview",
        content="Test content"
    )
    entity = ArchitectureEntity(
        document_id=doc.id,
        entity_type="COMPONENT",
        name="ADASController",
        page=1,
        confidence=0.95
    )
    db.add_all([chunk, entity])
    db.commit()

    # Verify query
    assert db.query(Document).filter_by(id="doc_db_test").first() is not None
    assert db.query(Chunk).filter_by(document_id=doc.id).count() == 1
    assert db.query(ArchitectureEntity).filter_by(document_id=doc.id).count() == 1

    # 3. Test cascade delete (foreign key integrity)
    db.delete(doc)
    db.commit()

    assert db.query(Chunk).filter_by(document_id="doc_db_test").count() == 0
    assert db.query(ArchitectureEntity).filter_by(document_id="doc_db_test").count() == 0
    db.close()
