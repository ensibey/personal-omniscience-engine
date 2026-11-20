"""Tests for style drift evaluation between candidate responses and target StyleProfile."""

from style.analyzer import analyze_text
from style.drift import evaluate_style_drift


def test_aligned_response_scores_higher_than_drifted_response():
    corpus = (
        "Distributed indexing pipelines require deterministic hashing and structured evaluation.\n"
        "- Vector search handles semantic similarity.\n"
        "- BM25 preserves exact identifiers and acronyms.\n"
    )
    target = analyze_text(corpus)

    good_reply = (
        "Hybrid indexing pipelines combine deterministic chunking with semantic vector retrieval.\n"
        "- Qdrant indexes dense embeddings efficiently.\n"
        "- Sparse search preserves exact technical terms.\n"
    )
    bad_reply = "OMG!! 🔥🔥🚀 Süper harika bir şey bu!! Çok beğendim!! 🎉🎉"

    good_report = evaluate_style_drift(good_reply, target)
    bad_report = evaluate_style_drift(bad_reply, target)

    assert good_report.alignment_score > bad_report.alignment_score
    assert good_report.language_match is True
    assert bad_report.language_match is False
    assert any("emoji" in w.lower() for w in bad_report.warnings)
