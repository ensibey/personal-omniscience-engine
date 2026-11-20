# Personal Omniscience Engine

[![Omniscience Engine CI](https://github.com/ensibey/personal-omniscience-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/ensibey/personal-omniscience-engine/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-10B981)
![Tests: 13 passing](https://img.shields.io/badge/tests-13%20passing-10B981)

A local, privacy-first **personal knowledge engine** that indexes Markdown/Obsidian vaults and PDFs with **incremental SHA-256 sync**, builds a bidirectional **`[[wikilink]]` knowledge graph** for graph-boosted retrieval, and conditions local LLM responses on a quantitative **stylometric profile** of your own writing.

---

## Architecture

```text
Local Vault (Markdown / Obsidian / PDF)
   │
   ├──► Incremental Sync (`ingestion/sync_state.py`, SHA-256 diffing) + Watchdog
   ├──► Markdown Parser (`ingestion/markdown_parser.py`) — YAML frontmatter, [[wikilinks]], #tags
   │        │
   │        ├──► Bidirectional KnowledgeGraph (`engine/knowledge_graph.py`) — Backlinks, BFS hops, Centrality
   │        └──► Graph-Boosted Retriever (`engine/local_retriever.py`) / Qdrant + LlamaIndex
   │
   └──► Stylometric Profiler (`style/analyzer.py`) — Sentence length, TTR, Formality, Punctuation
            │
            ├──► Bilingual Prompt Conditioner (`style/prompt_builder.py`, EN / TR)
            └──► Style Drift Evaluator (`style/drift.py`) — Measures response alignment vs target profile
```

---

## Reproducible Vault & Stylometry Benchmark

Measured on a 10-note Obsidian-style linked vault (`benchmarks/run_benchmark.py`):

```bash
python benchmarks/run_benchmark.py
```

| Evaluation | Metric | Result |
| :--- | :--- | :---: |
| **Plain BM25 (No Graph)** | Recall@3 / MRR (linked notes) | `33.3%` / `0.333` (`0.013 ms`) |
| **Wikilink Graph-Boosted BM25** | Recall@3 / MRR (linked notes) | **`100.0%`** / **`0.639`** (`0.016 ms`) |
| **Style Drift Evaluator** | In-style alignment vs Drifted reply | **`0.929`** vs **`0.230`** (margin `+0.699`) |

---

## Quick Start

### 1. Offline CLI (No Qdrant or Ollama Required)

```bash
# Profile your writing style across a Markdown vault
python cli.py profile path/to/vault

# Search with BM25 + wikilink graph boost
python cli.py search path/to/vault "vector database HNSW"

# Inspect note degree centrality across [[wikilinks]]
python cli.py graph path/to/vault

# Check style drift of a generated response against your vault
python cli.py drift path/to/vault "Your candidate response text..."
```

### 2. Full Local Qdrant + Ollama + Streamlit Stack

```bash
docker compose up -d
pip install -r requirements.txt
ollama pull llama3
ollama pull nomic-embed-text
python main.py
```

### 3. Run Tests

```bash
pytest -v tests/
```

---

## License

MIT
