from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    section = Column(String(255), default="General")
    content = Column(Text, nullable=False)
    chunk_id = Column(String(100), nullable=False, unique=True)

    document = relationship("Document", back_populates="chunks")
