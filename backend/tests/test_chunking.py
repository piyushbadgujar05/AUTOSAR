from backend.app.services.chunking_service import ChunkingService

def test_chunking():
    mock_pages = [
        {
            "page_number": 1,
            "section": "Software Component Architecture",
            "content": "Component: ADASController is responsible for vehicle dynamics.\n\nIt consumes FusedObjectData and produces BrakeCommand."
        },
        {
            "page_number": 2,
            "section": "Interface Specification",
            "content": "Interface: BrakeCommand is transmitted over CAN bus at 500kbps baud rate."
        }
    ]

    chunks = ChunkingService.create_section_aware_chunks(
        document_id="test_doc_1",
        document_name="Test_Doc.pdf",
        version="1.0",
        pages_data=mock_pages,
        chunk_size=300,
        chunk_overlap=50
    )

    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert "ADASController" in chunks[0]["content"]
    assert chunks[1]["page_number"] == 2

def test_metadata():
    mock_pages = [
        {
            "page_number": 18,
            "section": "Communication Interfaces",
            "content": "ADASController communicates with BrakeController using BrakeCommand interface."
        }
    ]

    chunks = ChunkingService.create_section_aware_chunks(
        document_id="doc_xyz",
        document_name="ADAS_HLD_v2.0.pdf",
        version="2.0",
        pages_data=mock_pages
    )

    assert len(chunks) == 1
    c = chunks[0]
    # Verify all critical metadata fields required by Specification
    assert c["document_id"] == "doc_xyz"
    assert c["document_name"] == "ADAS_HLD_v2.0.pdf"
    assert c["version"] == "2.0"
    assert c["page_number"] == 18
    assert c["section"] == "Communication Interfaces"
    assert "chunk_id" in c
    assert c["chunk_id"].startswith("doc_xyz_p18_")
