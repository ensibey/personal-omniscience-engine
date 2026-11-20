"""Regression test ensuring Graph-Boosted retrieval outperforms plain BM25 on linked notes."""

from benchmarks.run_benchmark import run_benchmark


def test_graph_boosted_retrieval_improves_linked_recall():
    report = run_benchmark()
    assert report["graph_boosted"]["recall_at_3"] > report["bm25_only"]["recall_at_3"]
    assert report["graph_boosted"]["recall_at_3"] == 1.0
    assert report["stylometry"]["separation_margin"] >= 0.40
