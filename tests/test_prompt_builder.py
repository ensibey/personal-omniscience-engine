"""Tests for bilingual English/Turkish style-conditioned prompt builder."""

from style.analyzer import analyze_text
from style.prompt_builder import build_system_prompt


def test_prompt_builder_emits_english_directives_for_english_corpus():
    profile = analyze_text(
        "## Architecture\n- **Qdrant** indexes vectors.\n```python\nprint(1)\n```\n"
    )
    prompt = build_system_prompt(use_style=True, profile=profile)
    assert "STYLE INSTRUCTIONS" in prompt
    assert "Do not use emojis" in prompt
    assert "Markdown headings" in prompt


def test_prompt_builder_emits_turkish_directives_for_turkish_corpus():
    profile = analyze_text(
        "## Notlar\n- **Yerel** arama motoru hızlı çalışıyor.\n"
    )
    prompt = build_system_prompt(use_style=True, profile=profile)
    assert "YAZIM TARZI TALİMATLARI" in prompt
    assert "Emoji kullanma" in prompt


def test_prompt_builder_disables_style_when_requested():
    prompt = build_system_prompt(use_style=False)
    assert "STYLE INSTRUCTIONS" not in prompt
    assert "YAZIM TARZI TALİMATLARI" not in prompt
