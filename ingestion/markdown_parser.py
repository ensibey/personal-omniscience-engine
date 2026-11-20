"""
Obsidian / Markdown structure parser for Personal Omniscience Engine.

Extracts YAML frontmatter, `[[wikilinks]]`, inline `#tags` (outside fenced code blocks),
and splits documents into heading-aware sections for high-precision RAG indexing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-zçğıöşüÇĞİÖŞÜ][A-Za-z0-9_/-]*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


@dataclass
class MarkdownSection:
    note_id: str
    heading: str
    level: int
    content: str


@dataclass
class ParsedNote:
    note_id: str
    title: str
    source_path: str
    frontmatter: Dict[str, str] = field(default_factory=dict)
    wikilinks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    sections: List[MarkdownSection] = field(default_factory=list)
    body: str = ""


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    return meta, text[match.end() :]


def parse_markdown_note(text: str, note_id: str, source_path: str = "") -> ParsedNote:
    """Parse a Markdown note into structured frontmatter, wikilinks, tags, and heading sections."""
    normalized = text.replace("\r\n", "\n")
    frontmatter, body = _parse_frontmatter(normalized)

    body_no_code = FENCE_RE.sub("", body)
    wikilinks = sorted({m.group(1).strip() for m in WIKILINK_RE.finditer(body_no_code) if m.group(1).strip()})

    tag_set: Set[str] = {m.group(1).lower() for m in TAG_RE.finditer(body_no_code)}
    if "tags" in frontmatter:
        raw_tags = frontmatter["tags"].strip("[]")
        for t in raw_tags.split(","):
            cleaned = t.strip().lstrip("#").lower()
            if cleaned:
                tag_set.add(cleaned)

    sections: List[MarkdownSection] = []
    current_heading = frontmatter.get("title") or note_id
    current_level = 1
    buf: List[str] = []
    in_code = False

    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            buf.append(line)
            continue
        if not in_code:
            h_match = HEADING_RE.match(line)
            if h_match:
                if buf and "\n".join(buf).strip():
                    sections.append(
                        MarkdownSection(
                            note_id=note_id,
                            heading=current_heading,
                            level=current_level,
                            content="\n".join(buf).strip(),
                        )
                    )
                current_level = len(h_match.group(1))
                current_heading = h_match.group(2).strip()
                buf = []
                continue
        buf.append(line)

    if buf and "\n".join(buf).strip():
        sections.append(
            MarkdownSection(
                note_id=note_id,
                heading=current_heading,
                level=current_level,
                content="\n".join(buf).strip(),
            )
        )

    title = frontmatter.get("title") or (sections[0].heading if sections else note_id)
    return ParsedNote(
        note_id=note_id,
        title=title,
        source_path=source_path or f"{note_id}.md",
        frontmatter=frontmatter,
        wikilinks=wikilinks,
        tags=sorted(tag_set),
        sections=sections,
        body=body.strip(),
    )


def load_markdown_file(path: Path) -> ParsedNote:
    return parse_markdown_note(
        path.read_text(encoding="utf-8", errors="ignore"),
        note_id=path.stem,
        source_path=path.as_posix(),
    )
