from backend.app.models.base import Base, engine, get_db, SessionLocal
from backend.app.models.document import Document
from backend.app.models.chunk import Chunk
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.models.analysis import Finding, Review, AuditLog, ComparisonResult

def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        from sqlalchemy import inspect, text
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if "documents" in tables:
                cols = [c["name"] for c in inspector.get_columns("documents")]
                if "file_hash" not in cols:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN file_hash VARCHAR;"))
                    conn.commit()
            if "findings" in tables:
                cols = [c["name"] for c in inspector.get_columns("findings")]
                if "evidence" not in cols:
                    conn.execute(text("ALTER TABLE findings ADD COLUMN evidence TEXT;"))
                    conn.commit()
    except Exception as e:
        import logging
        logging.getLogger("autosar_assistant").warning(f"Database schema auto-migration notice: {e}")
