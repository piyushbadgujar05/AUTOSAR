from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    project = Column(String(100), nullable=False, default="Default Project")
    version = Column(String(50), nullable=False, default="1.0")
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(100), default="High-Level Design")
    description = Column(String(500), nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="PROCESSING")  # PROCESSING, INDEXED, ERROR
    total_pages = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    file_hash = Column(String(64), nullable=True, index=True)

    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("ArchitectureEntity", back_populates="document", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="document", cascade="all, delete-orphan")
