"""
Bidirectional local knowledge graph over Obsidian-style `[[wikilinks]]` and `#tags`.

Supports backlink resolution, tag indexing, multi-hop neighborhood traversal,
and degree centrality ranking for graph-boosted RAG retrieval.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Set, Tuple

from ingestion.markdown_parser import ParsedNote


def _norm(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


class KnowledgeGraph:
    """In-memory bidirectional graph linking personal notes via wikilinks and shared tags."""

    def __init__(self) -> None:
        self._notes: Dict[str, ParsedNote] = {}
        self._alias_to_id: Dict[str, str] = {}
        self._outbound: Dict[str, Set[str]] = defaultdict(set)
        self._backlinks: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)

    def build(self, notes: Iterable[ParsedNote]) -> None:
        note_list = list(notes)
        for n in note_list:
            self._notes[n.note_id] = n
            self._alias_to_id[_norm(n.note_id)] = n.note_id
            self._alias_to_id[_norm(n.title)] = n.note_id
            for tag in n.tags:
                self._tag_index[tag.lower()].add(n.note_id)

        for n in note_list:
            for link in n.wikilinks:
                target_id = self._alias_to_id.get(_norm(link))
                if target_id and target_id != n.note_id:
                    self._outbound[n.note_id].add(target_id)
                    self._backlinks[target_id].add(n.note_id)

    def outbound(self, note_id: str) -> List[str]:
        return sorted(self._outbound.get(note_id, set()))

    def backlinks(self, note_id: str) -> List[str]:
        return sorted(self._backlinks.get(note_id, set()))

    def notes_by_tag(self, tag: str) -> List[str]:
        return sorted(self._tag_index.get(tag.lstrip("#").lower(), set()))

    def related_notes(self, note_id: str, max_hops: int = 2) -> Dict[str, int]:
        """BFS over undirected wikilink edges up to `max_hops`, returning {neighbor_id: distance}."""
        if note_id not in self._notes or max_hops <= 0:
            return {}
        visited: Dict[str, int] = {note_id: 0}
        queue: deque[Tuple[str, int]] = deque([(note_id, 0)])

        while queue:
            cur, dist = queue.popleft()
            if dist >= max_hops:
                continue
            neighbors = self._outbound.get(cur, set()) | self._backlinks.get(cur, set())
            for nb in neighbors:
                if nb not in visited:
                    visited[nb] = dist + 1
                    queue.append((nb, dist + 1))

        visited.pop(note_id, None)
        return visited

    def degree_centrality(self) -> List[Tuple[str, int]]:
        """Rank notes by total bidirectional link degree (outbound + backlinks)."""
        scores = [
            (nid, len(self._outbound.get(nid, set()) | self._backlinks.get(nid, set())))
            for nid in self._notes
        ]
        scores.sort(key=lambda pair: (-pair[1], pair[0]))
        return scores
