import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    airline: str = Field(min_length=1, max_length=100)
    valid_from: date
    valid_to: date
    source: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=100000)

    @model_validator(mode="after")
    def check_dates(self):
        if self.valid_to < self.valid_from:
            raise ValueError("valid_to precedes valid_from")
        return self


@dataclass(frozen=True)
class Chunk:
    id: str
    document: Document
    start: int
    end: int

    @property
    def text(self):
        return self.document.text[self.start : self.end]


def load_documents(path: Path):
    documents = [
        Document.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not documents or len({d.id for d in documents}) != len(documents):
        raise ValueError("The corpus must contain documents with unique IDs.")
    return documents


def chunk_document(document: Document, words=100, overlap=20):
    if words < 2 or not 0 <= overlap < words:
        raise ValueError("Require words >= 2 and 0 <= overlap < words.")
    matches = list(re.finditer(r"\S+", document.text))
    chunks = []
    for offset in range(0, len(matches), words - overlap):
        start = matches[offset].start()
        end = matches[min(offset + words, len(matches)) - 1].end()
        identity = hashlib.sha256(
            f"{document.id}:{start}:{end}:{document.text}".encode()
        ).hexdigest()[:12]
        chunks.append(Chunk(f"{document.id}-{identity}", document, start, end))
        if end == matches[-1].end():
            break
    return chunks
