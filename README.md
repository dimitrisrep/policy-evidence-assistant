# Policy Evidence Assistant

Hybrid lexical retrieval and quote-grounded answers over versioned policy documents, with optional local-LLM evidence selection.

The assistant searches a document corpus using BM25 and character TF-IDF, combines ranks with reciprocal-rank fusion and filters results by carrier and policy validity date. It returns exact source passages with document IDs and character offsets. An optional local language model can select passages, but its output is accepted only when each quote is an exact substring of a retrieved source.

The default corpus is fictional. It is for regression tests and demonstrations and must not be used as an airline policy reference.

## What this demonstrates

- Validated ingestion and deterministic overlapping chunks with stable IDs.
- BM25 and TF-IDF retrieval ablations and reciprocal-rank fusion.
- Metadata filtering for carrier and effective policy dates.
- Evidence citations that can be checked against the original text.
- Conservative missing-evidence responses and explicit generation-failure states.
- A structured local-model adapter with exact-quote validation and mocked contract tests.
- APIs, offline evaluation, tests and container packaging.

This is a constrained retrieval-augmented application, not a free-form chatbot. The default path returns an evidence passage without a language model. The optional LLM path selects and organizes verbatim evidence rather than producing unconstrained advice. There are no dense embeddings, vector database or semantic entailment verifier in this implementation.

## Quick start

Use Python 3.12 for the locked environment. Run from this project directory.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.lock
pip install --no-deps -e .

policy-evidence search "When does online check-in open?" --airline EXAMPLE --as-of 2026-10-27
policy-evidence answer "How long does an approved refund take?" --airline EXAMPLE --as-of 2026-10-27
policy-evidence evaluate
uvicorn policy_evidence.api:app --host 127.0.0.1 --port 8002
```

```bash
curl http://127.0.0.1:8002/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"When does online check-in open?","airline":"EXAMPLE","as_of":"2026-10-27"}'
```

`POST /search` supports `hybrid`, `bm25` and `tfidf`; `POST /answer` deliberately uses hybrid retrieval. `GET /health` and `GET /ready` expose index readiness. Set `POLICY_CORPUS` to another JSONL corpus. Sources are metadata references only; the service never fetches document-provided URLs.

## Optional local language model

Install and start Ollama separately and select a model you already have available:

```bash
export OLLAMA_MODEL="your-installed-model-name"
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
policy-evidence answer "When does online check-in open?" --airline EXAMPLE --as-of 2026-10-27
```

The adapter uses the [Ollama `/api/chat` contract](https://docs.ollama.com/api/chat) with a JSON schema, non-streaming output and temperature zero. The source text and question are labelled as untrusted data in the prompt. The validation layer rejects invented quotations and chunk IDs. This validates provenance, not relevance or policy correctness; an exact quotation can still be irrelevant, outdated because of bad metadata, or misleading out of context.

The client contract and failure paths were tested with simulated HTTP responses. No live Ollama/model output or generation-quality benchmark was run in the recorded validation. If the model is unavailable, the response is `generation_unavailable`, not a fabricated answer.

## Evaluation

The evaluation includes 14 fictional documents: 12 current Example Air policies, one expired version and one different carrier. It has 36 answerable queries and six unanswerable/carrier-filter queries.

| Method | MRR@5 | Hit rate@1 | Hit rate@3 |
| --- | ---: | ---: | ---: |
| BM25 | 0.9861 | 0.9722 | 1.0000 |
| Character TF-IDF | 1.0000 | 1.0000 | 1.0000 |
| Hybrid RRF | 1.0000 | 1.0000 | 1.0000 |

The default path refused five of six unanswerable questions. One unrelated question still passed the lexical gate because of a shared word. That limitation is retained and reported; the refusal mechanism is not a semantic safety guarantee. Strong scores on this tiny authored corpus do not establish performance on a real policy collection. See [the full retrieval report](reports/retrieval.json) and [data card](docs/DATA_CARD.md).

## Tests and container

```bash
pytest
ruff check src tests scripts
docker build -t policy-evidence-assistant .
docker run --rm -p 127.0.0.1:8002:8002 policy-evidence-assistant
```

The default container requires no API key, model download or external call. Local-LLM configuration is optional and depends on the host/network setup. Python tests cover exact offsets, retrieval, date/carrier filtering, unknown queries, fabricated evidence, adapter payloads, service failure and API contracts. Docker execution and real-model inference require separate verification.

## Boundaries

The corpus loader accepts local JSONL only. It does not ingest PDFs, fetch websites, enforce multi-tenant authorization, sanitize source truth, or provide legal/regulatory guidance. There is no production authentication, load test, operational monitoring or validated prompt-injection benchmark. The service is for localhost demonstrations. No passenger messages are persisted.
