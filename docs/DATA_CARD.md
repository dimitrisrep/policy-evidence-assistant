# Policy corpus and evaluation card

All bundled policy text is fictional and authored for this portfolio implementation with AI assistance. `Example Air` and `Alternate Air` are demonstration labels. The time limits and procedures in the corpus are invented, not quotations from or claims about any real carrier.

The corpus contains 14 JSONL documents with IDs, titles, carrier, validity interval, source reference and body. The 12 current documents cover refund processing, rebooking, airline cancellation, baggage, check-in, accessibility, name correction, compensation review, duplicate payments, vouchers, protected connections and contact details. One expired refund policy and one different-carrier policy exercise metadata exclusion.

The 42 authored evaluation queries have explicit relevant-document IDs, carrier and evaluation date. Thirty-six have a relevant document; six should yield no evidence. They are a small regression suite, not an independent retrieval benchmark. The generator `scripts/build_demo_corpus.py` deterministically reproduces both files.

Chunks retain exact character ranges in the original source. Their IDs hash the document ID, range and body so a modified source changes its chunk IDs. The retrieval report fingerprints the corpus and queries with SHA-256 and compares BM25, character TF-IDF and hybrid RRF.

No thresholds or retrieval weights were tuned after reading this evaluation report. BM25 has one top-rank error; hybrid/TF-IDF rank the gold documents first on the 36 answerable cases. The lexical gate refuses five of six negative cases and has one false positive. Provenance validation does not establish semantic relevance or whether a quoted policy is reliable.

For a meaningful next evaluation, replace the fictional corpus with permissioned, dated documents, collect independent paraphrases and near-domain negative questions, freeze the corpus and split, and assess both retrieval and answer relevance with human review. This is future work, not a current result.
