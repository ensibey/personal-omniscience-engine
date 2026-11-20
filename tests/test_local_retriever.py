"""Tests for BM25 + KnowledgeGraph-boosted local vault retriever."""

from engine.local_retriever import LocalVaultRetriever
from ingestion.markdown_parser import parse_markdown_note


def test_graph_boost_surfaces_linked_companion_note():
    notes = [
        parse_markdown_note("# PrivaRAG\nUses [[Semantic Cache]] for low latency.", "privarag"),
        parse_markdown_note("# Semantic Cache\nCosine similarity threshold 0.90 cuts latency.", "semantic_cache"),
        parse_markdown_note("# Grocery List\nBuy milk, eggs, and coffee.", "grocery"),
    ]
    retriever = LocalVaultRetriever(graph_boost_weight=0.30)
    assert retriever.index_notes(notes) == 3

    hits = retriever.search("PrivaRAG", top_k=2, use_graph_boost=True)
    assert len(hits) == 2
    assert hits[0].note_id == "privarag"
    assert hits[1].note_id == "semantic_cache"
    assert hits[1].graph_boost > 0
