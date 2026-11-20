"""End-to-end integration tests for vault sync, Markdown parsing, wikilink graph, and style conditioning."""

from pathlib import Path

from engine.local_retriever import LocalVaultRetriever
from ingestion.markdown_parser import load_markdown_file
from ingestion.sync_state import VaultSyncState
from style.analyzer import analyze_style
from style.drift import evaluate_style_drift
from style.prompt_builder import build_system_prompt


def test_full_vault_ingestion_graph_and_style_loop(tmp_path: Path):
    vault = tmp_path / "obsidian_vault"
    vault.mkdir()
    (vault / "ml_notes.md").write_text(
        "---\ntitle: ML Notes\ntags: [ml, pytorch]\n---\n"
        "# Training Loop\n- Always log validation loss.\n- Link to [[Optimization]].\n",
        encoding="utf-8",
    )
    (vault / "optimization.md").write_text(
        "# Optimization\n- Use AdamW with cosine warmup schedule.\n",
        encoding="utf-8",
    )

    # 1. Incremental sync
    sync = VaultSyncState(tmp_path / "sync.json")
    diff = sync.scan_diff(vault)
    assert len(diff.added) == 2
    sync.commit()
    assert sync.scan_diff(vault).unchanged == ["ml_notes.md", "optimization.md"]

    # 2. Parse & index into graph-boosted retriever
    notes = [load_markdown_file(p) for p in sorted(vault.glob("*.md"))]
    retriever = LocalVaultRetriever()
    retriever.index_notes(notes)
    hits = retriever.search("Training Loop validation loss", top_k=2, use_graph_boost=True)
    assert {h.note_id for h in hits} == {"ml_notes", "optimization"}

    # 3. Profile style, build prompt, and verify drift score
    profile = analyze_style(vault)
    prompt = build_system_prompt(use_style=True, profile=profile)
    assert "STYLE INSTRUCTIONS" in prompt
    drift = evaluate_style_drift("- Log validation loss.\n- Use AdamW with cosine schedule.", profile)
    assert drift.alignment_score >= 0.70
