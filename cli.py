"""
Standalone offline CLI for Personal Omniscience Engine.

Usage:
    python cli.py profile path/to/vault
    python cli.py search path/to/vault "query text"
    python cli.py graph path/to/vault
    python cli.py drift path/to/vault "candidate response text"
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from engine.local_retriever import LocalVaultRetriever
from ingestion.markdown_parser import load_markdown_file
from style.analyzer import analyze_style
from style.drift import evaluate_style_drift


def _load_vault_notes(vault_dir: Path):
    return [load_markdown_file(p) for p in sorted(vault_dir.rglob("*.md"))]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="omniscience", description="Offline knowledge vault & stylometry CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prof = sub.add_parser("profile", help="Analyze writing style profile of a Markdown/txt vault.")
    p_prof.add_argument("vault")

    p_search = sub.add_parser("search", help="Run BM25 + wikilink graph-boosted search.")
    p_search.add_argument("vault")
    p_search.add_argument("query")
    p_search.add_argument("-k", "--top-k", type=int, default=5)

    p_graph = sub.add_parser("graph", help="Display top connected notes by wikilink degree centrality.")
    p_graph.add_argument("vault")

    p_drift = sub.add_parser("drift", help="Evaluate style drift of a candidate response against a vault.")
    p_drift.add_argument("vault")
    p_drift.add_argument("response")

    args = parser.parse_args(argv)
    vault = Path(args.vault)
    if not vault.exists():
        print(f"error: vault not found: {vault}", file=sys.stderr)
        return 2

    if args.command == "profile":
        prof = analyze_style(vault)
        print(json.dumps(asdict(prof), indent=2, ensure_ascii=False))
        return 0

    if args.command == "search":
        notes = _load_vault_notes(vault)
        retriever = LocalVaultRetriever()
        retriever.index_notes(notes)
        hits = retriever.search(args.query, top_k=args.top_k)
        print(json.dumps([asdict(h) for h in hits], indent=2, ensure_ascii=False))
        return 0

    if args.command == "graph":
        notes = _load_vault_notes(vault)
        retriever = LocalVaultRetriever()
        retriever.index_notes(notes)
        centrality = [{"note_id": nid, "degree": deg} for nid, deg in retriever.graph.degree_centrality()]
        print(json.dumps({"notes": len(notes), "centrality": centrality}, indent=2))
        return 0

    if args.command == "drift":
        prof = analyze_style(vault)
        rep = evaluate_style_drift(args.response, prof)
        print(json.dumps(asdict(rep), indent=2, ensure_ascii=False))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
