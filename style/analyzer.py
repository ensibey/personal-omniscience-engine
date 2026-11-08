"""
style/analyzer.py
Extracts quantitative writing style metrics (sentence length, paragraph density,
markdown structure, and lexical frequency) from a local notes corpus.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from config import DATA_DIR

logger = logging.getLogger(__name__)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001FA60-\U0001FA6F"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)


@dataclass
class StyleProfile:
    """Aggregated structural and lexical statistics of the user's corpus."""

    avg_sentence_length: float = 12.0
    avg_paragraph_length: float = 3.0
    emoji_density: float = 0.0
    bullet_ratio: float = 0.0
    heading_ratio: float = 0.0
    uses_bold: bool = False
    uses_code_blocks: bool = False
    top_words: List[str] = field(default_factory=list)
    sample_sentences: List[str] = field(default_factory=list)
    total_words: int = 0
    language_hint: str = "tr"

    def __str__(self) -> str:
        return (
            f"StyleProfile("
            f"avg_sent={self.avg_sentence_length:.1f}w, "
            f"emoji_density={self.emoji_density:.3f}, "
            f"bullet_ratio={self.bullet_ratio:.2f}, "
            f"top_words={self.top_words[:5]})"
        )


_STOP_WORDS = {
    "bir", "bu", "da", "de", "den", "için", "ile", "ve", "ya", "ya da",
    "ama", "fakat", "ki", "mi", "mu", "mü", "mı", "ne", "o", "şu", "çok",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "on", "at", "by", "for", "with", "about", "as", "into", "through",
    "during", "before", "after", "above", "below", "from", "up", "down",
    "out", "off", "over", "under", "again", "further", "then", "once",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
}


def _read_text_files(directory: Path) -> List[str]:
    texts: List[str] = []
    for ext in (".md", ".txt"):
        for p in directory.rglob(f"*{ext}"):
            try:
                texts.append(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception as exc:
                logger.debug("skipped %s (%s)", p.name, exc)
    return texts


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 10]


def _count_words(text: str) -> List[str]:
    return re.findall(r"\b\w{2,}\b", text.lower())


def _detect_language(words: List[str]) -> str:
    tr_chars = set("şğüöçıŞĞÜÖÇİ")
    sample = " ".join(words[:500])
    return "tr" if any(c in sample for c in tr_chars) else "en"


def analyze_style(directory: Path = DATA_DIR) -> StyleProfile:
    """Scan markdown and plain-text files in directory to compute a StyleProfile."""
    profile = StyleProfile()
    directory = Path(directory)

    texts = _read_text_files(directory)
    if not texts:
        logger.warning("no text files found in %s; returning default StyleProfile", directory)
        return profile

    full_text = "\n\n".join(texts)
    lines = full_text.splitlines()
    words = _count_words(full_text)

    if not words:
        return profile

    profile.total_words = len(words)
    profile.language_hint = _detect_language(words)

    sentences = _split_sentences(full_text)
    if sentences:
        sentence_word_counts = [len(_count_words(s)) for s in sentences]
        profile.avg_sentence_length = round(
            sum(sentence_word_counts) / len(sentence_word_counts), 1
        )
        sorted_sents = sorted(sentences, key=len)
        profile.sample_sentences = [s for s in sorted_sents if 5 < len(s) < 200][:5]

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", full_text) if p.strip()]
    if paragraphs:
        para_sent_counts = [len(_split_sentences(p)) for p in paragraphs]
        profile.avg_paragraph_length = round(
            sum(para_sent_counts) / len(para_sent_counts), 1
        )

    emoji_count = sum(len(EMOJI_PATTERN.findall(line)) for line in lines)
    profile.emoji_density = round(emoji_count / max(len(words), 1), 4)

    bullet_lines = [l for l in lines if re.match(r"^\s*[-*+]\s+|^\s*\d+\.\s+", l)]
    profile.bullet_ratio = round(len(bullet_lines) / max(len(lines), 1), 3)

    heading_lines = [l for l in lines if re.match(r"^#{1,6}\s+", l)]
    profile.heading_ratio = round(len(heading_lines) / max(len(lines), 1), 3)

    profile.uses_bold = bool(re.search(r"\*\*.+?\*\*", full_text))
    profile.uses_code_blocks = "```" in full_text

    word_freq: Dict[str, int] = {}
    for w in words:
        if w not in _STOP_WORDS and len(w) > 3:
            word_freq[w] = word_freq.get(w, 0) + 1
    profile.top_words = [
        w for w, _ in sorted(word_freq.items(), key=lambda x: -x[1])
    ][:20]

    logger.info("style analysis completed: %s", profile)
    return profile
