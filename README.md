# AUTOSAR HLD Document Analysis Assistant
### AI-Powered RAG System for Automotive Architecture Analysis

---

> **ENGINEERING NOTICE:**  
> This system is an **engineering assistant**, not an autonomous decision-making system. It grounds answers strictly in uploaded High-Level Design (HLD) documents, produces verifiable page-level citations, detects potential architectural inconsistencies using deterministic rules, and requires human engineering review for consequential findings. It does not replace formal ISO 26262 functional safety governance.

---

## 1. Project Overview

The **AUTOSAR HLD Document Analysis Assistant** is an intelligent automotive architecture intelligence system. It ingests complex, multi-page High-Level Design (HLD) specifications (PDF format), extracts architectural components, interfaces, ports, signals, and dependencies, grounds natural-language queries with verified page citations, runs a deterministic 7-rule consistency engine, and tracks human engineering reviews in an immutable SQLite audit log.

---

## 2. Problem

Automotive High-Level Design (HLD) specifications are lengthy, complex documents spanning hundreds of pages. They detail critical software components (SWCs), sender-receiver and client-server interfaces, communication ports, signals, bus protocols (CAN, CAN-FD, Automotive Ethernet, Autosar RTE), functional flows, and revision modifications.

Manual review of these documents suffers from significant challenges:
- High engineering effort required to trace signals and dependencies across distributed ECU partitions.
- Difficulties in detecting subtle port naming mismatches (e.g. `BrakeCommand` vs `BrakeControlCommand`) that cause Runtime Environment (RTE) compilation failures.
- Risk of unverified dependencies pointing to non-existent or deprecated software components.
- Time-consuming revision delta reviews between release versions (e.g. v1.0 baseline vs v2.0 update).
- High hallucination risk in generic AI systems lacking strict page-level citation boundaries.

---

## 3. Solution

The assistant transforms static PDF engineering documents into a structured, queryable knowledge base:
1. **Section-Aware Ingestion**: Preserves exact page numbers, section headers, and tables without chunk boundary truncation.
2. **Deterministic Architecture Extraction**: Auto-extracts components, interfaces, ports, runnables, signals, and communication protocols.
3. **Strictly Grounded RAG Pipeline**: Answers questions exclusively using retrieved document evidence; when evidence is absent, it responds with: *"The uploaded engineering documents do not contain sufficient information to answer this question."*
4. **Transparent Evidence View**: Surfaces exact extracted sentences, confidence categories (`HIGH`, `MEDIUM`, `LOW`), and clickable citations.
5. **Deterministic 7-Rule Consistency Engine**: Evaluates architecture catalogs against formal rules with zero hallucination.
6. **Cross-Revision Impact Comparison**: Computes delta across component, interface, and dependency catalogs between release versions.
7. **Human-in-the-Loop Review**: Tracks reviews (`NEW`, `UNDER_REVIEW`, `ACCEPTED`, `REJECTED`, `RESOLVED`) with reviewer notes in SQLite.
8. **10-Section Engineering Reports**: Generates formal PDF and JSON architecture documentation with one click.

---

## 4. Features

- **Document Management**: Upload, view, filter by project/version, delete, and duplicate detection via SHA-256 hash.
- **Section-Aware Chunking**: Chunks preserve `document_id`, `document_name`, `version`, `page_number`, `section`, `chunk_id`.
- **Grounded Vector Search**: ChromaDB semantic search with similarity thresholding and multi-attribute metadata filtering (`project`, `document_id`, `version`).
- **Prompt Injection Defense**: PDF content is strictly treated as untrusted data; instruction overrides are neutralized.
- **Explainable Evidence**: Displays verbatim evidence snippet alongside confidence and page sources.
- **Interactive Architecture Graph**: Network topology of documented software components and communication links.
- **Human Review Workflow**: Complete lifecycle review with comment logs and audit trails.
- **10-Section Architecture Report**: Formally structured PDF/JSON export covering all project aspects.

---

## 5. Architecture

```
┌────────────────────────────────────────────────────────┐
│                   STREAMLIT FRONTEND                   │
│   (Dashboard, Q&A, Explorer, Graph, Consistency, Diff) │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / REST
┌───────────────────────────▼────────────────────────────┐
│                    FASTAPI BACKEND                     │
│  ┌──────────────┬───────────────┬───────────────────┐  │
│  │ Documents API│ Chat / RAG API│ Architecture API  │  │
│  ├──────────────┼───────────────┼───────────────────┤  │
│  │ Analysis API │ Comparison API│ Reports & Audit   │  │
│  └──────────────┴───────────────┴───────────────────┘  │
└──────┬────────────────────┬─────────────────────┬──────┘
       │                    │                     │
┌──────▼──────┐      ┌──────▼──────┐       ┌──────▼──────┐
│  PyMuPDF &  │      │  ChromaDB   │       │   SQLite    │
│  Chunking   │      │ Vector DB   │       │ SQLAlchemy  │
│  (Page Map) │      │ (Embeddings)│       │  Entities   │
└─────────────┘      └─────────────┘       └─────────────┘
       │
┌──────▼─────────────────────────────────────────────────┐
│                 LLM ABSTRACTION LAYER                  │
│   • Built-in Automotive Expert Reasoning Engine        │
│   • Local Ollama (e.g. LLaMA 3.1)                      │
│   • OpenAI-Compatible Endpoints                        │
└────────────────────────────────────────────────────────┘
```

---

## 6. RAG Workflow

```
User Question
    ↓
Coreference Resolution ("it" -> "ADASController")
    ↓
Query Embedding (BAAI/bge-small-en-v1.5)
    ↓
Vector Similarity Search (ChromaDB)
    ↓
Metadata Filtering (Project, Version, Document ID)
    ↓
Top-K Context Construction (Page, Section, Snippets)
    ↓
Strict Anti-Injection Boundary System Prompt
    ↓
LLM Synthesis / Built-in Automotive Engine
    ↓
Page-level Citation & Evidence Extraction
    ↓
Transparent Response (Answer + Confidence + Sources + Evidence)
```

---

## 7. Tech Stack

- **Frontend**: Streamlit, Custom Automotive CSS, Plotly Graphs, NetworkX
- **Backend**: FastAPI, Python 3.11, Uvicorn, Pydantic v2
- **Document Processing**: PyMuPDF (`fitz`), Section-Aware Chunking Service
- **Vector Database**: ChromaDB (persistent embedded)
- **Embeddings**: Sentence Transformers (`BAAI/bge-small-en-v1.5` / fast semantic vector engine)
- **Structured Database**: SQLite with SQLAlchemy ORM (enforcing `PRAGMA foreign_keys = ON;`)
- **Report Generation**: ReportLab (PDF) & JSON
- **Testing**: pytest (24 comprehensive tests + end-to-end test)
- **Containerization**: Docker & Docker Compose

---

## 8. Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd "d:/tata techpulse"

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # On Windows
source .venv/bin/activate  # On Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 9. Environment Setup

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Key environment configuration variables:
```env
LLM_PROVIDER=mock          # Options: "mock", "ollama", "openai"
LLM_MODEL=llama3.1
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CHROMA_PATH=./data/chroma
DATABASE_URL=sqlite:///./data/autosar.db
TOP_K=5
CHUNK_SIZE=800
CHUNK_OVERLAP=100
MAX_FILE_SIZE_MB=50
```

---

## 10. Local LLM Setup (Ollama)

To run fully offline with local open-weights LLMs:
1. Install [Ollama](https://ollama.com/)
2. Pull the model:
   ```bash
   ollama pull llama3.1
   ```
3. Set in `.env`:
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.1
   OLLAMA_BASE_URL=http://localhost:11434
   ```

---

## 11. Cloud LLM Setup (OpenAI)

To use cloud OpenAI or OpenAI-compatible models:
1. Set in `.env`:
   ```env
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini
   OPENAI_API_KEY=your_api_key_here
   ```
If no external provider is configured, the system automatically falls back to its **Built-in Automotive Expert Reasoning Engine** with zero runtime crashes.

---

## 12. Running Backend

Start the FastAPI backend with Uvicorn:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- OpenAPI JSON Specification: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 13. Running Frontend

Launch the Streamlit dashboard:
```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```
Open [http://127.0.0.1:8501](http://127.0.0.1:8501) in your browser.

Or launch both concurrently via the unified runner:
```bash
python run.py
```

---

## 14. Docker

Run the entire application in a self-contained container with persistent volume mounts:
```bash
# Build and start
docker compose up --build

# Run in background
docker compose up -d
```
All uploaded documents, SQLite database records, and ChromaDB vector embeddings persist in `./data`.

---

## 15. Demo Workflow

1. **Seed Synthetic Demonstrations**:
   Run `python scripts/seed_demo_data.py` (or click *Seed Demo Datasets* in Document Manager).
2. **Dashboard**: View real-time component, interface, and review statistics.
3. **AI Assistant**: Click sample questions like:
   - *"What are the main software components?"*
   - *"What interfaces does ADASController use?"*
   - *"Show me all references to BrakeController."*
4. **Evidence View**: Inspect grounded page citations and verbatim evidence snippets.
5. **Architecture Explorer & Graph**: Inspect SWC components and interactive NetworkX topological graph.
6. **Consistency Analysis**: View detected findings (e.g. `BrakeCommand` vs `BrakeControlCommand`) and record engineering reviews (`ACCEPTED`, `UNDER_REVIEW`).
7. **Revision Comparison**: Compare `v1.0` vs `v2.0` to inspect added, removed, and changed interfaces with impact assessments.
8. **Report Generation**: Export a 10-section formal architecture report in PDF or JSON.
9. **Audit Trail**: Review logged actions in the system audit log.

---

## 16. API Specification

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and version |
| `POST` | `/api/documents/upload` | Upload and index HLD PDF |
| `GET` | `/api/documents` | List indexed documents with entity counts |
| `GET` | `/api/documents/{id}` | Get document metadata and chunks |
| `DELETE` | `/api/documents/{id}` | Remove document and vector embeddings |
| `POST` | `/api/chat/query` | Grounded RAG query with citations |
| `GET` | `/api/architecture/components` | Retrieve extracted SWCs |
| `GET` | `/api/architecture/interfaces` | Retrieve communication interfaces |
| `GET` | `/api/architecture/dependencies` | Retrieve architecture dependency links |
| `GET` | `/api/architecture/graph` | Graph node/edge topology |
| `POST` | `/api/analysis/inconsistencies` | Execute 7-rule consistency engine |
| `GET` | `/api/analysis/findings` | Retrieve consistency findings |
| `POST` | `/api/findings/{id}/review` | Submit human engineering review |
| `POST` | `/api/comparison` | Cross-revision architecture diff |
| `POST` | `/api/reports/generate` | Generate formal 10-section PDF/JSON report |
| `GET` | `/api/reports/download/{filename}` | Download generated report |

---

## 17. Testing

Run the full automated test suite using pytest:
```bash
# Run all tests
pytest backend/tests tests -v

# Run end-to-end integration test
pytest tests/test_end_to_end.py -v
```
All 24 test suites validate:
- PDF text extraction & OCR scanned fallback detection
- Section-aware chunking & page metadata preservation
- Embedding generation & vector similarity search
- Grounded RAG synthesis, page citations & anti-injection defense
- Entity & relationship extraction
- 7 deterministic consistency rules
- Cross-revision comparison
- SQLite foreign key cascade deletion
- REST API endpoint contracts
- End-to-end document upload -> chunking -> vector search -> RAG -> analysis pipeline

---

## 18. Evaluation

Execute real empirical benchmarking against ground-truth automotive test cases:
```bash
python scripts/evaluate.py
```

### Real Benchmark Metrics:
- **Retrieval Precision (Page Match)**: **75.0%** (12/16)
- **Citation Accuracy (Document Grounded)**: **100.0%** (80/80 citations verified in retrieved text)
- **Answer Groundedness (Keyword Match)**: **62.5%** (10/16)
- **Entity Extraction Accuracy**: **40.7%** (11/27)
- **Finding Precision**: **100.0%** (deterministic rules)

---

## 19. Limitations

- **Multimodal Block Diagrams**: Vector embeddings analyze text, headings, and tables; complex vector graphics require vision model extensions for full netlist parsing.
- **Scanned Documents**: Scanned documents require Tesseract OCR installed on the host OS.
- **Advisory Nature**: Findings are advisory and do not replace certified ISO 26262 functional safety sign-offs.
- **Synthetic Data**: Sample documents are synthetic demonstrations and not official AUTOSAR consortium publications.

---

## 20. Future Scope

- Direct AUTOSAR ARXML file bi-directional import/export.
- ISO 26262 ASIL hazard traceability matrices.
- Cross-encoder reranking for ultra-low latency Top-3 retrieval.
- Integration with DBC/FIBEX CAN network databases.
- Integration with Vector DaVinci Developer and CANoe test suites.
