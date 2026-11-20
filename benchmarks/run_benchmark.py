"""
Reproducible Vault Retrieval & Stylometry Drift Benchmark for Personal Omniscience Engine.

Compares plain BM25 against Wikilink Graph-Boosted retrieval on Recall@2 / MRR
and measures style alignment separation between in-style and drifted responses.

Usage:
    python benchmarks/run_benchmark.py
    python benchmarks/run_benchmark.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine.local_retriever import LocalVaultRetriever
from ingestion.markdown_parser import parse_markdown_note
from style.analyzer import analyze_text
from style.drift import evaluate_style_drift

VAULT_NOTES_RAW: List[Tuple[str, str]] = [
    ("rag_overview", "# Local RAG Overview\nAir-gapped note retrieval powered by [[Qdrant]] and [[Ollama]]. #ai #rag"),
    ("qdrant", "# Qdrant\nRust vector database using [[HNSW]] indexing for millisecond cosine search. #vectors"),
    ("hnsw", "# HNSW\nHierarchical Navigable Small World graph algorithm for approximate nearest neighbors. #algorithms"),
    ("ollama", "# Ollama\nRuns quantized GGUF weights locally via llama.cpp with zero cloud egress. #llm"),
    ("stylometry", "# Stylometry\nMeasures sentence length, lexical diversity, and formality via [[Prompt Conditioning]]. #nlp"),
    ("prompt_conditioning", "# Prompt Conditioning\nInjects dynamic tone directives into the system prompt based on author notes. #nlp"),
    ("watchdog", "# Watchdog Sync\nDetects live filesystem edits and triggers [[Incremental Hashing]] updates. #infra"),
    ("incremental_hashing", "# Incremental Hashing\nComputes SHA-256 digests so unchanged notes are never re-embedded. #infra"),
    ("codesentinel", "# CodeSentinel\nPython AST security scanner paired with a multi-agent LangGraph judge. #security"),
    ("turkish_nlp", "# Turkish NLP\nHandles agglutinative stemming and dotted İ/I case folding for Turkish text. #nlp"),
]

# Queries where the target note is directly linked to the lexical anchor note (multi-hop knowledge retrieval)
LINKED_QUERIES: List[Tuple[str, str]] = [
    ("Local RAG Overview", "qdrant"),
    ("Qdrant vector database", "hnsw"),
    ("Watchdog live filesystem edits", "incremental_hashing"),
    ("Stylometry sentence length", "prompt_conditioning"),
    ("Turkish NLP stemming", "turkish_nlp"),
    ("CodeSentinel AST security", "codesentinel"),
]


def run_benchmark() -> Dict[str, Any]:
    notes = [parse_markdown_note(body, note_id=nid) for nid, body in VAULT_NOTES_RAW]
    retriever = LocalVaultRetriever(graph_boost_weight=0.35)
    sections_indexed = retriever.index_notes(notes)

    def _eval(use_graph: bool) -> Dict[str, Any]:
        r3 = 0
        mrr = 0.0
        lats: List[float] = []
        for q, expected_id in LINKED_QUERIES:
            t0 = time.perf_counter()
            hits = retriever.search(q, top_k=3, use_graph_boost=use_graph)
            lats.append((time.perf_counter() - t0) * 1000.0)
            ids = [h.note_id for h in hits]
            if expected_id in ids:
                r3 += 1
                mrr += 1.0 / (ids.index(expected_id) + 1)
        n = len(LINKED_QUERIES)
        return {
            "recall_at_3": round(r3 / n, 4),
            "mrr": round(mrr / n, 4),
            "mean_latency_ms": round(sum(lats) / n, 3),
        }

    bm25_only = _eval(use_graph=False)
    graph_boosted = _eval(use_graph=True)

    # Stylometry alignment separation benchmark
    corpus = "\n\n".join(body for _, body in VAULT_NOTES_RAW)
    target_profile = analyze_text(corpus)
    aligned_reply = (
        "Local RAG retrieval combines Qdrant vector search with quantized Ollama inference.\n"
        "Incremental SHA-256 hashing avoids redundant embedding computation."
    )
    drifted_reply = "Yooo!! 🔥🔥🚀🚀 Bu sistem efsane olmuş bence!! Süper hızlı!! 🎉"

    aligned_score = evaluate_style_drift(aligned_reply, target_profile).alignment_score
    drifted_score = evaluate_style_drift(drifted_reply, target_profile).alignment_score

    return {
        "notes_indexed": len(notes),
        "sections_indexed": sections_indexed,
        "bm25_only": bm25_only,
        "graph_boosted": graph_boosted,
        "stylometry": {
            "aligned_score": aligned_score,
            "drifted_score": drifted_score,
            "separation_margin": round(aligned_score - drifted_score, 4),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Personal Omniscience Engine benchmark.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_benchmark()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Omniscience Engine Benchmark ({report['notes_indexed']} notes, {report['sections_indexed']} sections)")
        print("=" * 62)
        print(f"BM25 Only      : R@3={report['bm25_only']['recall_at_3']*100:5.1f}% | MRR={report['bm25_only']['mrr']:.3f} | {report['bm25_only']['mean_latency_ms']:.3f} ms")
        print(f"Graph-Boosted  : R@3={report['graph_boosted']['recall_at_3']*100:5.1f}% | MRR={report['graph_boosted']['mrr']:.3f} | {report['graph_boosted']['mean_latency_ms']:.3f} ms")
        st = report["stylometry"]
        print(f"Style Drift    : aligned={st['aligned_score']:.3f} vs drifted={st['drifted_score']:.3f} (margin=+{st['separation_margin']:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
