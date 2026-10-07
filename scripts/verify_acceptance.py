import httpx

base_url = 'http://127.0.0.1:8000'

# Find the test document id dynamically
r_docs = httpx.get(f'{base_url}/api/documents', timeout=10)
docs = r_docs.json()
test_doc = next((d for d in docs if 'synthetic' in d['name'].lower()), None)
if not test_doc:
    print('Error: Synthetic test doc not found!')
    exit(1)

doc_id = test_doc['id']
print(f"Found test doc: {test_doc['name']} (v{test_doc['version']}) ID: {doc_id}")

tests = [
    {
        "name": "Q1: Main Software Components (Req 22)",
        "query": "What are the main software components?",
        "expected": ["CameraManager", "RadarProcessor", "SensorFusion", "ADASController", "BrakeController", "VehicleInterface"]
    },
    {
        "name": "Q2: ADASController Interfaces (Req 23)",
        "query": "What interfaces does ADASController use?",
        "expected": ["VehicleState", "BrakeCommand"]
    },
    {
        "name": "Q3: CameraData Provider (Req 24)",
        "query": "Which component provides CameraData?",
        "expected": ["CameraManager"]
    },
    {
        "name": "Q4: BrakeCommand Consumer (Req 25)",
        "query": "Which component consumes BrakeCommand?",
        "expected": ["BrakeController"]
    },
    {
        "name": "Q5: Out-of-Scope ASIL (Req 26)",
        "query": "What is the official AUTOSAR ASIL classification of this architecture?",
        "expected": ["do not contain sufficient information"]
    }
]

for t in tests:
    print("=" * 60)
    print(t["name"])
    print(f"Query: {t['query']}")
    req = {
        "query": t["query"],
        "project": "ADAS Control System",
        "document_id": doc_id,
        "version": "1.0",
        "top_k": 5,
        "similarity_threshold": 0.10
    }
    resp = httpx.post(f"{base_url}/api/chat/query", json=req, timeout=15)
    data = resp.json()
    chunks = data.get("retrieved_chunks", 0)
    conf = data.get("confidence", "UNKNOWN")
    ans = data.get("answer", "")
    sources = [f"{s['document']} p.{s['page']}" for s in data.get("sources", [])]

    print(f"Status: {resp.status_code} | Retrieved Chunks: {chunks} | Confidence: {conf}")
    print(f"Sources: {sources}")
    print(f"Answer:\n{ans}\n")

    # Verification
    passed = all(exp.lower() in ans.lower() for exp in t["expected"])
    print(f"Test Result: {'PASS' if passed else 'FAIL'}")
