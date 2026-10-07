from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.document import Document
from backend.app.services.extraction_service import ExtractionService

def test_entity_extraction():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    doc = Document(id="test_doc_ent", name="Test.pdf", project="ADAS", version="1.0", file_path="dummy.pdf")
    db.add(doc)
    db.commit()

    mock_chunks = [
        {
            "page_number": 3,
            "content": "Component: CameraManager provides interface CameraData over Ethernet.\nPPort_CameraRaw is defined on page 3.\nRunnable: re_ProcessOpticalFlow executes cyclically at 20ms."
        }
    ]

    entities, _ = ExtractionService.extract_architecture_from_chunks(
        db=db,
        document_id="test_doc_ent",
        document_name="Test.pdf",
        chunks=mock_chunks
    )

    types = set(e.entity_type for e in entities)
    names = set(e.name for e in entities)

    assert "COMPONENT" in types
    assert "INTERFACE" in types
    assert "PROTOCOL" in types
    assert "CameraManager" in names
    assert "CameraData" in names
    assert "Ethernet" in names

    # Verify entity fields
    for e in entities:
        assert e.name
        assert e.entity_type
        assert e.page == 3
        assert e.confidence > 0

def test_relationship_extraction():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    doc = Document(id="test_doc_rel", name="Test.pdf", project="ADAS", version="1.0", file_path="dummy.pdf")
    db.add(doc)
    db.commit()

    mock_chunks = [
        {
            "page_number": 21,
            "content": "ADASController communicates with BrakeController through BrakeCommand interface.\nSensorFusion -> ADASController via Autosar RTE."
        }
    ]

    _, relationships = ExtractionService.extract_architecture_from_chunks(
        db=db,
        document_id="test_doc_rel",
        document_name="Test.pdf",
        chunks=mock_chunks
    )

    assert len(relationships) >= 2
    # Verify relationship structure
    rel_types = set(r.relationship_type for r in relationships)
    assert "USES_INTERFACE" in rel_types or "COMMUNICATES_WITH" in rel_types or "DEPENDS_ON" in rel_types

    for r in relationships:
        assert r.source_entity
        assert r.relationship_type
        assert r.target_entity
        assert r.page == 21
        assert r.confidence > 0
