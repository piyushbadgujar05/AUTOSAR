from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class ArchitectureEntity(Base):
    __tablename__ = "architecture_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(50), nullable=False)  # COMPONENT, INTERFACE, PORT, SIGNAL, DEPENDENCY, FUNCTION, DATA_FLOW, PROTOCOL, REQUIREMENT
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    page = Column(Integer, nullable=False, default=1)
    confidence = Column(Float, default=0.9)

    document = relationship("Document", back_populates="entities")

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    source_entity = Column(String(255), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # DEPENDS_ON, PROVIDES, CONSUMES, COMMUNICATES_VIA, SENDS_SIGNAL
    target_entity = Column(String(255), nullable=False)
    protocol = Column(String(50), nullable=True, default="CAN")
    page = Column(Integer, nullable=False, default=1)
    confidence = Column(Float, default=0.9)

    document = relationship("Document", back_populates="relationships")
