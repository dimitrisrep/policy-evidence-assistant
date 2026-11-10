import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from policy_evidence.answers import OllamaSelector, Quote, Selection, answer
from policy_evidence.api import create_app
from policy_evidence.corpus import Document, chunk_document, load_documents
from policy_evidence.evaluation import evaluate
from policy_evidence.retrieval import EvidenceIndex

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 10, 27)


@pytest.fixture(scope="module")
def index():
    return EvidenceIndex(load_documents(ROOT / "data/policies.jsonl"))


def test_chunks_preserve_source_offsets():
    document = Document(
        id="long",
        title="Long document",
        airline="EXAMPLE",
        valid_from="2026-01-01",
        valid_to="2027-01-01",
        source="demo://long",
        text=" ".join(f"word{i}" for i in range(300)),
    )
    chunks = chunk_document(document, words=100, overlap=20)
    assert len(chunks) == 4
    assert all(c.text == document.text[c.start : c.end] for c in chunks)
    assert len({c.id for c in chunks}) == 4


@pytest.mark.parametrize("method", ["hybrid", "bm25", "tfidf"])
def test_known_query_retrieves_relevant_document(index, method):
    hits = index.search(
        "When does online check-in open?", airline="EXAMPLE", as_of=AS_OF, method=method
    )
    assert hits[0].document_id == "checkin"


def test_metadata_filters_exclude_expired_and_wrong_carrier(index):
    hits = index.search("refund processing", airline="EXAMPLE", as_of=AS_OF, top_k=10)
    assert "expired-refund" not in {h.document_id for h in hits}
    assert "different-carrier" not in {h.document_id for h in hits}
    assert index.search("refund", airline="UNKNOWN", as_of=AS_OF) == []
    historic = index.search(
        "ninety refund days", airline="EXAMPLE", as_of=date(2024, 6, 1)
    )
    assert historic[0].document_id == "expired-refund"


def test_unknown_query_abstains(index):
    result = answer(index, "Explain quantum entanglement", as_of=AS_OF)
    assert result["status"] == "insufficient_evidence"
    assert result["answer"] is None
    assert result["citations"] == []


def test_extractive_answer_is_exactly_grounded(index):
    result = answer(index, "refund processing", airline="EXAMPLE", as_of=AS_OF)
    sources = {c.document.id: c.document for c in index.chunks}
    assert result["status"] == "evidence_found"
    for c in result["citations"]:
        assert sources[c["document_id"]].text[c["start"] : c["end"]] == c["quote"]


@pytest.mark.parametrize("invalid_quote,invalid_id", [(True, False), (False, True)])
def test_generated_claims_and_fabricated_citations_are_rejected(
    index, invalid_quote, invalid_id
):
    class Selector:
        def select(self, query, hits):
            return Selection(
                quotes=[
                    Quote(
                        chunk_id="invented" if invalid_id else hits[0].chunk_id,
                        quote="Every passenger receives 5000 euros"
                        if invalid_quote
                        else hits[0].text,
                    )
                ]
            )

    result = answer(index, "refund processing", as_of=AS_OF, selector=Selector())
    assert result["status"] == "unverified_generation"
    assert result["answer"] is None


def test_generated_exact_quote_is_accepted(index):
    class Selector:
        def select(self, query, hits):
            return Selection(
                quotes=[Quote(chunk_id=hits[0].chunk_id, quote=hits[0].text[:50])]
            )

    assert (
        answer(index, "refund", as_of=AS_OF, selector=Selector())["status"]
        == "evidence_found"
    )


def test_local_llm_request_contract(index):
    hit = index.search("refund", as_of=AS_OF)[0]

    def handle(request):
        payload = json.loads(request.content)
        assert request.url.path == "/api/chat"
        assert payload["stream"] is False
        assert payload["format"]["type"] == "object"
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": Selection(
                        quotes=[Quote(chunk_id=hit.chunk_id, quote=hit.text)]
                    ).model_dump_json()
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        selector = OllamaSelector("test-model", client=client)
        assert selector.select("refund", [hit]).quotes[0].quote == hit.text


def test_model_failure_is_explicit(index):
    class FailingSelector:
        def select(self, query, hits):
            raise httpx.ConnectError("offline")

    assert (
        answer(index, "refund", as_of=AS_OF, selector=FailingSelector())["status"]
        == "generation_unavailable"
    )


def test_retrieval_evaluation_reports_real_failures(tmp_path):
    report = evaluate(
        ROOT / "data/policies.jsonl",
        ROOT / "data/queries.jsonl",
        tmp_path / "metrics.json",
    )
    assert report["answerable_queries"] == 36
    assert report["unanswerable_queries"] == 6
    assert set(report["methods"]) == {"hybrid", "bm25", "tfidf"}
    assert 0 <= report["methods"]["hybrid"]["mrr_at_5"] <= 1


def test_api_contract_and_validation(index):
    with TestClient(create_app(index=index)) as client:
        assert client.get("/ready").status_code == 200
        response = client.post(
            "/answer",
            json={
                "query": "online check-in",
                "airline": "EXAMPLE",
                "as_of": "2026-10-27",
            },
        )
        assert response.json()["citations"][0]["document_id"] == "checkin"
        assert client.post("/search", json={"query": " "}).status_code == 422
        assert (
            client.post("/search", json={"query": "refund", "top_k": 11}).status_code
            == 422
        )
        assert (
            client.post(
                "/answer", json={"query": "refund", "method": "bm25"}
            ).status_code
            == 422
        )
