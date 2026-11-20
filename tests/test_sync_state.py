"""Tests for SHA-256 incremental vault sync state."""

from pathlib import Path

from ingestion.sync_state import VaultSyncState


def test_vault_sync_tracks_added_modified_unchanged_and_deleted(tmp_path: Path):
    vault = tmp_path / "vault"
    vault.mkdir()
    f1 = vault / "a.md"
    f2 = vault / "b.md"
    f1.write_text("Note A v1", encoding="utf-8")
    f2.write_text("Note B v1", encoding="utf-8")

    state_file = tmp_path / "sync.json"
    sync = VaultSyncState(state_file)
    d1 = sync.scan_diff(vault)
    assert set(d1.added) == {"a.md", "b.md"}
    sync.commit()

    # Modify a.md, delete b.md, add c.md
    f1.write_text("Note A v2", encoding="utf-8")
    f2.unlink()
    (vault / "c.md").write_text("Note C", encoding="utf-8")

    sync2 = VaultSyncState(state_file)
    d2 = sync2.scan_diff(vault)
    assert d2.added == ["c.md"]
    assert d2.modified == ["a.md"]
    assert d2.deleted == ["b.md"]
    assert d2.unchanged == []
