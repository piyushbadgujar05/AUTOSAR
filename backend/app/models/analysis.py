from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    finding_type = Column(String(100), nullable=False)  # MISSING_INTERFACE, MISSING_COMPONENT, RELATIONSHIP_CONFLICT, BROKEN_DEPENDENCY, NAMING_MISMATCH, REVISION_INCONSISTENCY
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW
    confidence = Column(Float, default=0.85)
    status = Column(String(30), default="NEW")  # NEW, UNDER_REVIEW, ACCEPTED, REJECTED, RESOLVED
    evidence = Column(Text, nullable=True)
    source_page = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="findings")
    reviews = relationship("Review", back_populates="finding", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    reviewer = Column(String(100), nullable=False, default="Engineering Reviewer")
    status = Column(String(30), nullable=False)  # ACCEPTED, REJECTED, NEEDS_REVIEW, RESOLVED
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    finding = relationship("Finding", back_populates="reviews")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String(100), nullable=False, default="Engineer")
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ComparisonResult(Base):
    __tablename__ = "comparison_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc1_id = Column(String(36), nullable=False)
    doc2_id = Column(String(36), nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
