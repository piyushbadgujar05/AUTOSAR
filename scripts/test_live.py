import time
import httpx

base_url = 'http://127.0.0.1:8000'

try:
    r_health = httpx.get(f'{base_url}/api/health', timeout=10)
    print('Health check:', r_health.status_code, r_health.json())
except Exception as e:
    print('Health error:', e)

try:
    r_docs = httpx.get(f'{base_url}/api/documents', timeout=10)
    print('Documents status:', r_docs.status_code, f'Count: {len(r_docs.json())}')
    for d in r_docs.json():
        print(f"  - {d['name']} (v{d['version']}) in {d['project']} -> {d['status']}")
except Exception as e:
    print('Docs error:', e)

try:
    dbg_req = {
        'query': 'What are the main software components?',
        'project': 'ADAS Control System',
        'version': '1.0'
    }
    r_dbg = httpx.post(f'{base_url}/debug/retrieval', json=dbg_req, timeout=15)
    print('Debug retrieval status:', r_dbg.status_code)
    data = r_dbg.json()
    print('  Collection:', data.get('collection'))
    print('  Candidate count:', data.get('candidate_count'))
    print('  Retrieved count:', data.get('retrieved_count'))
    for r in data.get('results', [])[:3]:
        print(f"    - Score: {r['score']} | Page: {r['page']} | Section: {r['section']} | Doc: {r['document']} (v{r['version']})")
except Exception as e:
    print('Debug error:', e)

try:
    chat_req = {
        'query': 'What are the main software components?',
        'project': 'ADAS Control System',
        'version': '1.0'
    }
    r_chat = httpx.post(f'{base_url}/api/chat/query', json=chat_req, timeout=15)
    print('Chat query status:', r_chat.status_code)
    cdata = r_chat.json()
    print('  Retrieved chunks:', cdata.get('retrieved_chunks'))
    print('  Confidence:', cdata.get('confidence'))
    print('  Sources:', [f"{s['document']} p.{s['page']}" for s in cdata.get('sources', [])])
    print('  Answer excerpt:', cdata.get('answer', '')[:160].replace('\n', ' '))
except Exception as e:
    print('Chat error:', e)
