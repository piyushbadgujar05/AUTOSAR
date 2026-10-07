import os
import sys
import json
from typing import List, Dict, Any

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.models import SessionLocal
from backend.app.models.document import Document
from backend.app.models.architecture import ArchitectureEntity
from backend.app.models.analysis import Finding
from backend.app.services.rag_service import RAGService

def run_evaluation():
    questions_file = os.path.join(settings.BASE_DIR, "evaluation", "questions.json")
    if not os.path.exists(questions_file):
        print("Evaluation not executed: evaluation/questions.json benchmark dataset not found.")
        return

    try:
        with open(questions_file, "r", encoding="utf-8") as f:
            benchmark_cases = json.load(f)
    except Exception as e:
        print(f"Evaluation not executed: Failed to read benchmark dataset ({e})")
        return

    if not benchmark_cases:
        print("Evaluation not executed: Benchmark dataset is empty.")
        return

    db = SessionLocal()
    try:
        target_doc = db.query(Document).filter(Document.status == "INDEXED").first()
        if not target_doc:
            print("Evaluation not executed: No indexed documents found in database. Run seed_demo_data.py first.")
            return

        rag_service = RAGService()

        print("=" * 68)
        print("AUTOSAR HLD DOCUMENT ANALYSIS ASSISTANT — REAL BENCHMARK EVALUATION")
        print("=" * 68)
        print(f"Target Specification : {target_doc.name} (v{target_doc.version}) | Project: {target_doc.project}")
        print(f"Benchmark Cases Count: {len(benchmark_cases)} questions\n")

        total_queries = len(benchmark_cases)
        retrieval_hits = 0
        total_retrieved_chunks = 0
        valid_citations = 0
        total_citations = 0
        grounded_answers = 0

        for case in benchmark_cases:
            res = rag_service.query(
                query=case["question"],
                project_name=target_doc.project,
                document_id=target_doc.id,
                top_k=5
            )

            retrieved_pages = [s.page for s in res.sources]
            total_retrieved_chunks += res.retrieved_chunks
            total_citations += len(res.sources)

            # Check if any retrieved page matches expected pages
            expected_pages = case.get("expected_pages", [])
            page_overlap = set(retrieved_pages).intersection(set(expected_pages))
            if page_overlap:
                retrieval_hits += 1

            # Check citation correctness (citations must be genuine pages present in document)
            for s in res.sources:
                if 1 <= s.page <= target_doc.total_pages:
                    valid_citations += 1

            # Check keyword match in synthesized answer
            kws = case.get("expected_answer_keywords", [])
            matches = [kw for kw in kws if kw.lower() in res.answer.lower()]
            if len(matches) > 0:
                grounded_answers += 1

            print(f"[{case['id']}/{total_queries}] '{case['question'][:42]}...'")
            print(f"     • Confidence: {res.confidence} | Chunks: {res.retrieved_chunks} | Cited Pages: {retrieved_pages}")
            print(f"     • Grounded Keywords: {len(matches)}/{len(kws)}")

        # Entity Extraction Accuracy
        entities = db.query(ArchitectureEntity).filter(ArchitectureEntity.document_id == target_doc.id).all()
        extracted_names = set(e.name for e in entities)
        benchmark_entities = set()
        for c in benchmark_cases:
            for ent in c.get("expected_entities", []):
                benchmark_entities.add(ent)

        found_entities = benchmark_entities.intersection(extracted_names)
        entity_acc = (len(found_entities) / max(1, len(benchmark_entities))) * 100

        # Finding Precision (valid, structured, non-empty findings with evidence)
        findings = db.query(Finding).filter(Finding.document_id == target_doc.id).all()
        valid_findings = [f for f in findings if f.evidence and f.severity in ["HIGH", "MEDIUM", "LOW"]]
        finding_precision = (len(valid_findings) / max(1, len(findings))) * 100 if findings else 100.0

        retrieval_precision = (retrieval_hits / total_queries) * 100
        citation_accuracy = (valid_citations / max(1, total_citations)) * 100
        groundedness_ratio = (grounded_answers / total_queries) * 100

        print("\n" + "=" * 68)
        print("REAL BENCHMARK METRIC MEASUREMENTS")
        print("=" * 68)
        print(f"Retrieval Precision (Page Match)     : {retrieval_precision:.1f}% ({retrieval_hits}/{total_queries})")
        print(f"Citation Accuracy (Document Grounded) : {citation_accuracy:.1f}% ({valid_citations}/{max(1, total_citations)})")
        print(f"Answer Groundedness (Keyword Match)   : {groundedness_ratio:.1f}% ({grounded_answers}/{total_queries})")
        print(f"Entity Extraction Accuracy            : {entity_acc:.1f}% ({len(found_entities)}/{len(benchmark_entities)})")
        print(f"Finding Precision                     : {finding_precision:.1f}% ({len(valid_findings)}/{len(findings)})")
        print("=" * 68)
        print("Evaluation successfully executed on real database and vector index.\n")

    finally:
        db.close()

if __name__ == "__main__":
    run_evaluation()
