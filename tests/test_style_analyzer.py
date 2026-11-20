"""Tests for quantitative writing style profiling."""

from pathlib import Path

from style.analyzer import analyze_style, analyze_text


def test_analyze_style_from_directory(tmp_path: Path):
    note = tmp_path / "notes.md"
    note.write_text(
        "# Mimari Notları\n\n"
        "- **Qdrant** vektör araması için kullanılır.\n"
        "- **Ollama** yerel çıkarım sağlar.\n\n"
        "```python\nprint('hello')\n```\n",
        encoding="utf-8",
    )

    profile = analyze_style(tmp_path)
    assert profile.total_words > 0
    assert profile.language_hint == "tr"
    assert profile.uses_bold is True
    assert profile.uses_code_blocks is True
    assert profile.bullet_ratio > 0.15
    assert profile.heading_ratio > 0.0
    assert 0.0 < profile.lexical_diversity <= 1.0


def test_formality_distinguishes_formal_vs_casual_text():
    formal = analyze_text(
        "Distributed retrieval systems require deterministic indexing pipelines and reproducible evaluation benchmarks. "
        "Furthermore, vector quantization reduces memory bandwidth constraints across commodity hardware."
    )
    casual = analyze_text(
        "Hey!! Super cool stuff!! 🔥🔥 Works fast! Really really fast! 🎉"
    )
    assert formal.formality_score > casual.formality_score
    assert casual.exclamation_ratio > 0.5
