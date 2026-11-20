"""Tests for Obsidian / Markdown frontmatter, wikilink, tag, and section parser."""

from ingestion.markdown_parser import parse_markdown_note


def test_parses_frontmatter_wikilinks_tags_and_sections():
    md = (
        "---\n"
        "title: RAG Architecture\n"
        "tags: [ai, retrieval]\n"
        "---\n\n"
        "# Overview\n"
        "Connects [[Qdrant]] and [[Hybrid Search|BM25 + Dense]] for #local-llm.\n"
        "```python\n"
        "# not_a_tag_in_code\n"
        "```\n\n"
        "## Caching\n"
        "See [[Semantic Cache#TTL]] for latency details.\n"
    )

    note = parse_markdown_note(md, note_id="rag_arch")
    assert note.title == "RAG Architecture"
    assert set(note.wikilinks) == {"Qdrant", "Hybrid Search", "Semantic Cache"}
    assert "ai" in note.tags
    assert "local-llm" in note.tags
    assert "not_a_tag_in_code" not in note.tags
    assert len(note.sections) == 2
    assert note.sections[0].heading == "Overview"
    assert note.sections[1].heading == "Caching"
