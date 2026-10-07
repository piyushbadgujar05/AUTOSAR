from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.document import Document
from backend.app.models.architecture import ArchitectureEntity, Relationship
from backend.app.services.inconsistency_service import InconsistencyService

def test_missing_interface_detection():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    doc = Document(id="doc_missing_if", name="Test.pdf", project="ADAS", version="1.0", file_path="dummy.pdf")
    db.add(doc)

    # Component references interface 'UnregisteredInterface' in relationship without definition
    c1 = ArchitectureEntity(document_id=doc.id, entity_type="COMPONENT", name="ADASController", page=5)
    rel = Relationship(document_id=doc.id, source_entity="ADASController", relationship_type="USES_INTERFACE", target_entity="UnregisteredBrakeBus", page=5)
    db.add_all([c1, rel])
    db.commit()

    findings = InconsistencyService.detect_inconsistencies(db, doc.id)
    types = [f.finding_type for f in findings]
    assert "MISSING_INTERFACE" in types
    
    missing_if_finding = next(f for f in findings if f.finding_type == "MISSING_INTERFACE")
    assert missing_if_finding.evidence is not None
    assert missing_if_finding.source_page == 5
    assert missing_if_finding.severity in ["HIGH", "MEDIUM", "LOW"]

def test_missing_component_detection():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    doc = Document(id="doc_missing_comp", name="Test.pdf", project="ADAS", version="1.0", file_path="dummy.pdf")
    db.add(doc)

    # Relationship references source component 'GhostSensor' not registered in SWC catalog
    c1 = ArchitectureEntity(document_id=doc.id, entity_type="COMPONENT", name="ADASController", page=4)
    rel = Relationship(document_id=doc.id, source_entity="GhostSensor", relationship_type="COMMUNICATES_WITH", target_entity="ADASController", page=4)
    db.add_all([c1, rel])
    db.commit()

    findings = InconsistencyService.detect_inconsistencies(db, doc.id)
    types = [f.finding_type for f in findings]
    assert "MISSING_COMPONENT" in types
    
    comp_finding = next(f for f in findings if f.finding_type == "MISSING_COMPONENT")
    assert "GhostSensor" in comp_finding.title
    assert comp_finding.evidence is not None

def test_inconsistency_rules():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    doc = Document(id="doc_inconsistent", name="Inconsistent.pdf", project="ADAS", version="1.0", file_path="dummy.pdf")
    db.add(doc)

    # Add components & interfaces with intentional naming discrepancy
    c1 = ArchitectureEntity(document_id=doc.id, entity_type="COMPONENT", name="ADASController", page=5)
    c2 = ArchitectureEntity(document_id=doc.id, entity_type="COMPONENT", name="BrakeController", page=6)
    i1 = ArchitectureEntity(document_id=doc.id, entity_type="INTERFACE", name="BrakeCommand", page=5)
    i2 = ArchitectureEntity(document_id=doc.id, entity_type="INTERFACE", name="BrakeControlCommand", page=6)
    
    # Broken dependency pointing to undefined component
    rel = Relationship(document_id=doc.id, source_entity="ADASController", relationship_type="DEPENDS_ON", target_entity="NonExistentECU", page=5)

    db.add_all([c1, c2, i1, i2, rel])
    db.commit()

    findings = InconsistencyService.detect_inconsistencies(db, doc.id)

    assert len(findings) >= 2
    types = [f.finding_type for f in findings]
    assert "NAMING_MISMATCH" in types
    assert "BROKEN_DEPENDENCY" in types
    for f in findings:
        assert f.status == "NEW"
        assert f.severity in ["HIGH", "MEDIUM", "LOW"]
        assert f.evidence is not None
