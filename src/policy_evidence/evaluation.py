"""Reproducible retrieval ablations and answerability checks on authored queries."""

import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np

from policy_evidence.answers import answer
from policy_evidence.corpus import load_documents
from policy_evidence.retrieval import EvidenceIndex


def evaluate(corpus: Path, queries: Path, output: Path):
    index = EvidenceIndex(load_documents(corpus))
    cases = [
        json.loads(line)
        for line in queries.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    answerable = [row for row in cases if row["relevant_document_ids"]]
    negative = [row for row in cases if not row["relevant_document_ids"]]
    report = {
        "corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
        "queries_sha256": hashlib.sha256(queries.read_bytes()).hexdigest(),
        "dataset_type": "authored fictional policy corpus and queries; regression evaluation only",
        "answerable_queries": len(answerable),
        "unanswerable_queries": len(negative),
        "methods": {},
        "failures": [],
    }
    for method in ["bm25", "tfidf", "hybrid"]:
        ranks = []
        for row in answerable:
            hits = index.search(
                row["query"],
                top_k=5,
                airline=row.get("airline"),
                as_of=date.fromisoformat(row["as_of"]),
                method=method,
            )
            rank = next(
                (
                    i
                    for i, hit in enumerate(hits, 1)
                    if hit.document_id in row["relevant_document_ids"]
                ),
                None,
            )
            ranks.append(rank)
            if rank != 1:
                report["failures"].append(
                    {
                        "query_id": row["id"],
                        "method": method,
                        "rank": rank,
                        "returned_document_ids": [h.document_id for h in hits],
                    }
                )
        report["methods"][method] = {
            "mrr_at_5": float(np.mean([1 / r if r else 0 for r in ranks])),
            **{
                f"hit_rate_at_{k}": float(
                    np.mean([r is not None and r <= k for r in ranks])
                )
                for k in [1, 3, 5]
            },
        }
    refusals = []
    for row in negative:
        result = answer(
            index,
            row["query"],
            airline=row.get("airline"),
            as_of=date.fromisoformat(row["as_of"]),
        )
        refusals.append(result["status"] == "insufficient_evidence")
        if result["status"] != "insufficient_evidence":
            report["failures"].append(
                {
                    "query_id": row["id"],
                    "method": "hybrid_answerability",
                    "reason": "unanswerable_query_returned_evidence",
                    "returned_document_ids": [
                        c["document_id"] for c in result["citations"]
                    ],
                }
            )
    report["unanswerable_refusal_rate"] = float(np.mean(refusals)) if refusals else None
    report["generation_evaluation"] = (
        "Extractive path and mocked LLM contract tested; no live language model evaluated."
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
