"""BM25 and character TF-IDF with reciprocal-rank fusion and metadata filters."""

import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from policy_evidence.corpus import chunk_document

STOP = set(
    "the a an is are was were be can could should would i me my we our you your to of for and or in on at with how what when where do does after if it this that about have has by as from there".split()
)


def tokens(text):
    normalized = "".join(
        c
        for c in unicodedata.normalize("NFD", text.casefold())
        if not unicodedata.combining(c)
    )
    return [
        word
        for word in re.findall(r"\b\w+\b", normalized)
        if word not in STOP and len(word) > 1
    ]


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    document_id: str
    title: str
    text: str
    source: str
    start: int
    end: int
    score: float
    method: str

    def to_dict(self):
        return asdict(self)


class EvidenceIndex:
    def __init__(self, documents):
        self.chunks = [c for d in documents for c in chunk_document(d)]
        if not self.chunks:
            raise ValueError("Cannot index an empty corpus.")
        self.counts = [Counter(tokens(c.text)) for c in self.chunks]
        self.lengths = np.array([sum(c.values()) for c in self.counts], dtype=float)
        self.average_length = max(1.0, float(self.lengths.mean()))
        self.frequency = Counter(term for counts in self.counts for term in counts)
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), strip_accents="unicode"
        )
        self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks])

    def bm25_scores(self, query):
        scores = np.zeros(len(self.chunks))
        for word in set(tokens(query)):
            frequency = self.frequency[word]
            idf = math.log(1 + (len(self.chunks) - frequency + 0.5) / (frequency + 0.5))
            for i, counts in enumerate(self.counts):
                tf = counts[word]
                if tf:
                    scores[i] += (
                        idf
                        * tf
                        * 2.5
                        / (
                            tf
                            + 1.5
                            * (0.25 + 0.75 * self.lengths[i] / self.average_length)
                        )
                    )
        return scores

    def search(self, query, top_k=5, airline=None, as_of=None, method="hybrid"):
        if not query.strip() or len(query) > 4000 or not 1 <= top_k <= 10:
            raise ValueError("Query must be 1-4000 characters and top_k must be 1-10.")
        if method not in {"hybrid", "bm25", "tfidf"}:
            raise ValueError("Unknown retrieval method.")
        as_of = as_of or date.today()
        eligible = [
            i
            for i, chunk in enumerate(self.chunks)
            if chunk.document.valid_from <= as_of <= chunk.document.valid_to
            and (
                airline is None
                or chunk.document.airline.casefold() == airline.casefold()
            )
        ]
        terms = set(tokens(query))
        # This conservative lexical gate is deliberate; it is not semantic OOD detection.
        eligible = [i for i in eligible if terms & set(self.counts[i])]
        if not eligible:
            return []
        bm25 = self.bm25_scores(query)
        tfidf = (self.matrix @ self.vectorizer.transform([query]).T).toarray().ravel()
        scores = np.zeros(len(self.chunks))
        if method == "hybrid":
            for values in [bm25, tfidf]:
                ranked = sorted(eligible, key=lambda i: (-values[i], self.chunks[i].id))
                for rank, i in enumerate(ranked, 1):
                    if values[i] > 0:
                        scores[i] += 1 / (60 + rank)
        else:
            scores = bm25 if method == "bm25" else tfidf
        selected, seen = [], set()
        for i in sorted(eligible, key=lambda i: (-scores[i], self.chunks[i].id)):
            chunk = self.chunks[i]
            if chunk.document.id in seen or scores[i] <= 0:
                continue
            selected.append(
                Hit(
                    chunk.id,
                    chunk.document.id,
                    chunk.document.title,
                    chunk.text,
                    chunk.document.source,
                    chunk.start,
                    chunk.end,
                    float(scores[i]),
                    method,
                )
            )
            seen.add(chunk.document.id)
            if len(selected) >= top_k:
                break
        return selected
