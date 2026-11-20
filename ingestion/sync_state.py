"""
SHA-256 incremental vault sync tracker for Personal Omniscience Engine.

Computes added, modified, deleted, and unchanged files between indexing runs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class VaultDiff:
    added: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class VaultSyncState:
    """Persists file content hashes for incremental vault synchronization."""

    SUPPORTED_EXTS: Tuple[str, ...] = (".md", ".txt", ".pdf")

    def __init__(self, state_path: Optional[Path] = None) -> None:
        self.state_path = state_path
        self._hashes: Dict[str, str] = {}
        if self.state_path and self.state_path.exists():
            try:
                self._hashes = json.loads(self.state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self._hashes = {}

    def scan_diff(self, vault_dir: Path) -> VaultDiff:
        current: Dict[str, str] = {}
        for p in sorted(vault_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in self.SUPPORTED_EXTS:
                rel = p.relative_to(vault_dir).as_posix()
                current[rel] = _hash_file(p)

        diff = VaultDiff()
        for rel, digest in current.items():
            if rel not in self._hashes:
                diff.added.append(rel)
            elif self._hashes[rel] != digest:
                diff.modified.append(rel)
            else:
                diff.unchanged.append(rel)

        for old_rel in self._hashes:
            if old_rel not in current:
                diff.deleted.append(old_rel)

        self._latest_snapshot = current
        return diff

    def commit(self) -> None:
        if hasattr(self, "_latest_snapshot"):
            self._hashes = dict(self._latest_snapshot)
            if self.state_path:
                self.state_path.parent.mkdir(parents=True, exist_ok=True)
                self.state_path.write_text(json.dumps(self._hashes, indent=2), encoding="utf-8")
