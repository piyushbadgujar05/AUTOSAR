from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.document import Document
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.services.comparison_service import ComparisonService

def test_revision_comparison():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    doc1 = Document(id="doc_v1", name="HLD_v1.pdf", project="ADAS", version="1.0", file_path="v1.pdf")
    doc2 = Document(id="doc_v2", name="HLD_v2.pdf", project="ADAS", version="2.0", file_path="v2.pdf")
    db.add_all([doc1, doc2])

    # v1 has SensorFusion, v2 replaces with SensorFusionV2
    c1 = ArchitectureEntity(document_id=doc1.id, entity_type="COMPONENT", name="SensorFusion", page=4)
    c2 = ArchitectureEntity(document_id=doc2.id, entity_type="COMPONENT", name="SensorFusionV2", page=4)

    # v1 has BrakeCommand, v2 has BrakeControlCommand
    i1 = ArchitectureEntity(document_id=doc1.id, entity_type="INTERFACE", name="BrakeCommand", page=6)
    i2 = ArchitectureEntity(document_id=doc2.id, entity_type="INTERFACE", name="BrakeControlCommand", page=6)

    db.add_all([c1, c2, i1, i2])
    db.commit()

    diff = ComparisonService.compare_documents(db, doc1.id, doc2.id)

    assert "SensorFusionV2" in diff.components_diff.added
    assert "SensorFusion" in diff.components_diff.removed
    assert "BrakeControlCommand" in diff.interfaces_diff.added
    assert len(diff.potential_impacts) >= 1
