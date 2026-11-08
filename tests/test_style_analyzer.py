"""Unit tests for Personal Omniscience Engine Style Analyzer & Prompt Builder."""

import tempfile
from pathlib import Path
from style.analyzer import analyze_style, StyleProfile
from style.prompt_builder import build_system_prompt


def test_analyze_style_on_markdown_notes():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "notes.md"
        p.write_text(
            "# Yapay Zeka Mimarisi\n\n"
            "**Qdrant** ve **LlamaIndex** kullanarak yerel RAG sistemleri geliştiriyoruz. "
            "Veri gizliliği kurumsal projelerde çok kritik bir gereksinimdir.\n\n"
            "- Vektör indeksleme ve semantik arama\n"
            "- Yerel model çıkarımı ve önbellekleme\n"
            "```python\nprint('hello')\n```\n",
            encoding="utf-8",
        )
        profile = analyze_style(Path(tmpdir))
        assert isinstance(profile, StyleProfile)
        assert profile.total_words > 10
        assert profile.language_hint == "tr"
        assert profile.uses_bold is True
        assert profile.uses_code_blocks is True
        assert profile.bullet_ratio > 0.0

        prompt = build_system_prompt(profile)
        assert isinstance(prompt, str)
        assert len(prompt) > 30
