import numpy as np
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_service import VectorService

def test_embedding():
    service = EmbeddingService.get_instance()
    texts = [
        "Component: ADASController",
        "Interface: BrakeCommand via CAN"
    ]
    vectors = service.embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384

    # Check similarity of identical text is high
    q_vec = service.embed_query("Component: ADASController")
    dot = np.dot(vectors[0], q_vec)
    assert dot > 0.75

def test_vector_search():
    vservice = VectorService.get_instance()
    project = "test_search_proj"
    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "document_name": "Test1.pdf",
            "version": "1.0",
            "page_number": 18,
            "section": "Interfaces",
            "content": "ADASController sends BrakeCommand to BrakeController over CAN bus."
        },
        {
            "chunk_id": "c2",
            "document_id": "d1",
            "document_name": "Test1.pdf",
            "version": "1.0",
            "page_number": 3,
            "section": "Perception",
            "content": "CameraManager processes high resolution front camera frames."
        }
    ]
    vservice.add_chunks(project, chunks)

    results = vservice.similarity_search("BrakeCommand interface", project_name=project, top_k=2)
    assert len(results) >= 1
    assert "BrakeCommand" in results[0]["content"]
    assert results[0]["metadata"]["page_number"] == 18
