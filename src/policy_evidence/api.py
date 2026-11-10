import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from policy_evidence.answers import answer, selector_from_environment
from policy_evidence.corpus import load_documents
from policy_evidence.retrieval import EvidenceIndex


class Query(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=3, ge=1, le=10)
    airline: str | None = Field(default=None, max_length=100)
    as_of: date | None = None
    method: Literal["hybrid", "bm25", "tfidf"] = "hybrid"


def create_app(index=None, selector=None):
    @asynccontextmanager
    async def lifespan(app):
        path = Path(os.environ.get("POLICY_CORPUS", "data/policies.jsonl"))
        app.state.index = (
            index
            if index is not None
            else EvidenceIndex(load_documents(path))
            if path.exists()
            else None
        )
        app.state.selector = (
            selector if selector is not None else selector_from_environment()
        )
        yield

    app = FastAPI(title="Policy Evidence Assistant", version="0.1.0", lifespan=lifespan)

    def require_index():
        if app.state.index is None:
            raise HTTPException(503, "No policy corpus loaded.")
        return app.state.index

    @app.get("/health")
    def health():
        return {"status": "ok", "index_ready": app.state.index is not None}

    @app.get("/ready")
    def ready():
        require_index()
        return {"status": "ready"}

    @app.post("/search")
    def search(request: Query):
        try:
            return {
                "hits": [
                    hit.to_dict()
                    for hit in require_index().search(
                        request.query,
                        request.top_k,
                        request.airline,
                        request.as_of,
                        request.method,
                    )
                ]
            }
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/answer")
    def get_answer(request: Query):
        if request.method != "hybrid":
            raise HTTPException(
                422,
                "Answers use hybrid retrieval. Use /search for retrieval ablations.",
            )
        try:
            return answer(
                require_index(),
                request.query,
                request.top_k,
                request.airline,
                request.as_of,
                app.state.selector,
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    return app


app = create_app()
