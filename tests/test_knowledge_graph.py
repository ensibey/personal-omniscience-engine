"""Tests for local wikilink & tag KnowledgeGraph."""

from engine.knowledge_graph import KnowledgeGraph
from ingestion.markdown_parser import parse_markdown_note


def test_knowledge_graph_backlinks_tags_and_multihop():
    n1 = parse_markdown_note("# RAG\nUses [[Qdrant]] and [[BM25]]. #ai #search", "rag")
    n2 = parse_markdown_note("# Qdrant\nVector store supporting [[HNSW]]. #ai", "qdrant")
    n3 = parse_markdown_note("# HNSW\nGraph-based approximate nearest neighbor index. #search", "hnsw")
    n4 = parse_markdown_note("# BM25\nSparse lexical scoring. #search", "bm25")

    kg = KnowledgeGraph()
    kg.build([n1, n2, n3, n4])

    assert kg.outbound("rag") == ["bm25", "qdrant"]
    assert kg.backlinks("qdrant") == ["rag"]
    assert kg.notes_by_tag("ai") == ["qdrant", "rag"]

    hops = kg.related_notes("rag", max_hops=2)
    assert hops["qdrant"] == 1
    assert hops["hnsw"] == 2

    top_note, degree = kg.degree_centrality()[0]
    assert degree == 2
    assert top_note in {"qdrant", "rag"}
