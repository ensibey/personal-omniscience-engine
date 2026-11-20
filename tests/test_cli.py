"""Tests for standalone offline Personal Omniscience Engine CLI."""

import json
from pathlib import Path

from cli import main


def test_cli_profile_search_graph_and_drift(tmp_path: Path, capsys):
    (tmp_path / "rag.md").write_text(
        "# Local RAG\n- Uses [[Qdrant]] for vector indexing.\n- Keeps data private.\n",
        encoding="utf-8",
    )
    (tmp_path / "qdrant.md").write_text(
        "# Qdrant\nHigh-performance Rust vector database with HNSW.\n",
        encoding="utf-8",
    )

    assert main(["profile", str(tmp_path)]) == 0
    prof = json.loads(capsys.readouterr().out)
    assert prof["total_words"] > 0

    assert main(["search", str(tmp_path), "vector database HNSW"]) == 0
    hits = json.loads(capsys.readouterr().out)
    assert hits[0]["note_id"] == "qdrant"

    assert main(["graph", str(tmp_path)]) == 0
    g = json.loads(capsys.readouterr().out)
    assert g["notes"] == 2

    assert main(["drift", str(tmp_path), "- Uses Qdrant for fast vector search."]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["alignment_score"] > 0.5
