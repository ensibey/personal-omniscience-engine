"""
Offline BM25 + KnowledgeGraph-boosted vault retriever.

Ranks Markdown note sections using Okapi BM25 and optionally applies a graph
proximity boost to notes directly linked via Obsidian `[[wikilinks]]`.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from engine.knowledge_graph import KnowledgeGraph
from ingestion.markdown_parser import ParsedNote

TOKEN_RE = re.compile(r"[0-9a-zA-ZçğıöşüÇĞİÖŞÜ]+")


def _tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.replace("İ", "i").replace("I", "ı").lower())


@dataclass
class VaultHit:
    note_id: str
    title: str
    heading: str
    score: float
    graph_boost: float
    content: str
    source_path: str


class LocalVaultRetriever:
    """Zero-dependency BM25 + wikilink graph-boosted retriever for Markdown vaults."""

    def __init__(self, k1: float = 1.5, b: float = 0.75, graph_boost_weight: float = 0.25) -> None:
        self.k1 = k1
        self.b = b
        self.graph_boost_weight = graph_boost_weight
        self.graph = KnowledgeGraph()
        self._records: List[Dict[str, object]] = []
        self._tfs: List[Counter] = []
        self._lens: List[int] = []
        self._df: Counter = Counter()
        self._avgdl: float = 0.0

    def index_notes(self, notes: Iterable[ParsedNote]) -> int:
        note_list = list(notes)
        self.graph.build(note_list)
        self._records.clear()
        self._tfs.clear()
        self._lens.clear()
        self._df.clear()

        for note in note_list:
            sections = note.sections or []
            if not sections and note.body:
                sections_data = [(note.title, note.body)]
            else:
                sections_data = [(s.heading, s.content) for s in sections]

            for heading, content in sections_data:
                searchable = f"{note.title} {heading} {' '.join(note.tags)} {content}"
                tokens = _tokenize(searchable)
                tf = Counter(tokens)
                self._records.append(
                    {
                        "note_id": note.note_id,
                        "title": note.title,
                        "heading": heading,
                        "content": content,
                        "source_path": note.source_path,
                    }
                )
                self._tfs.append(tf)
                self._lens.append(len(tokens))
                for term in tf:
                    self._df[term] += 1

        self._avgdl = (sum(self._lens) / len(self._lens)) if self._lens else 0.0
        return len(self._records)

    def _idf(self, term: str) -> float:
        n = len(self._lens)
        df = self._df.get(term, 0)
        if n == 0 or df == 0:
            return 0.0
        return math.log(1.0 + (n - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 5, use_graph_boost: bool = True) -> List[VaultHit]:
        if not self._records or top_k <= 0:
            return []
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        raw_scores: List[float] = []
        for idx, tf in enumerate(self._tfs):
            dl = self._lens[idx]
            s = 0.0
            for term in q_tokens:
                freq = tf.get(term, 0)
                if freq == 0:
                    continue
                idf = self._idf(term)
                denom = freq + self.k1 * (1.0 - self.b + self.b * (dl / (self._avgdl or 1.0)))
                s += idf * (freq * (self.k1 + 1.0)) / denom
            raw_scores.append(s)

        # Graph proximity boost from top-2 lexical anchor notes
        boost_by_note: Dict[str, float] = {}
        if use_graph_boost:
            top_indices = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)[:2]
            for idx in top_indices:
                anchor_score = raw_scores[idx]
                if anchor_score <= 0:
                    continue
                anchor_id = str(self._records[idx]["note_id"])
                for nb_id, dist in self.graph.related_notes(anchor_id, max_hops=1).items():
                    boost = (anchor_score * self.graph_boost_weight) / dist
                    boost_by_note[nb_id] = max(boost_by_note.get(nb_id, 0.0), boost)

        hits: List[VaultHit] = []
        for idx, base_score in enumerate(raw_scores):
            rec = self._records[idx]
            nid = str(rec["note_id"])
            g_boost = boost_by_note.get(nid, 0.0) if use_graph_boost else 0.0
            total = base_score + g_boost
            if total > 0:
                hits.append(
                    VaultHit(
                        note_id=nid,
                        title=str(rec["title"]),
                        heading=str(rec["heading"]),
                        score=round(total, 5),
                        graph_boost=round(g_boost, 5),
                        content=str(rec["content"]),
                        source_path=str(rec["source_path"]),
                    )
                )

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]
