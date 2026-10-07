import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_list_documents_endpoint():
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_chat_query_endpoint():
    resp = client.post("/api/chat/query", json={
        "query": "What are the main software components?",
        "project": "ADAS Control System",
        "top_k": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "confidence" in data
    assert "sources" in data

def test_architecture_endpoints():
    r1 = client.get("/api/architecture/components")
    assert r1.status_code == 200
    assert isinstance(r1.json(), list)

    r2 = client.get("/api/architecture/interfaces")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

    r3 = client.get("/api/architecture/graph")
    assert r3.status_code == 200
    assert "nodes" in r3.json()
    assert "edges" in r3.json()

def test_api():
    """Verify all required API endpoints respond with valid schemas and HTTP status codes."""
    # Health
    r = client.get("/api/health")
    assert r.status_code == 200

    # Documents
    r = client.get("/api/documents")
    assert r.status_code == 200

    # Architecture components, interfaces, dependencies, graph
    r = client.get("/api/architecture/components")
    assert r.status_code == 200
    r = client.get("/api/architecture/interfaces")
    assert r.status_code == 200
    r = client.get("/api/architecture/dependencies")
    assert r.status_code == 200
    r = client.get("/api/architecture/graph")
    assert r.status_code == 200

    # Consistency analysis findings
    r = client.get("/api/analysis/findings")
    assert r.status_code == 200

    # Report generation
    r = client.post("/api/reports/generate", json={"project": "ADAS Control System"})
    assert r.status_code == 200
    assert "report_id" in r.json()

