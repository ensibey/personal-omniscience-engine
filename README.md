# personal-omniscience-engine

[![CI](https://github.com/ensibey/personal-omniscience-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/ensibey/personal-omniscience-engine/actions)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Local knowledge base indexer and conversational retrieval engine built on **LlamaIndex**, **Qdrant**, and **Ollama** (`llama3.2`, `nomic-embed-text`). Indexes personal Markdown notes, PDFs, DOCX, and TXT files continuously via a filesystem watcher (`watchdog`) and adapts LLM output formatting to match the author's own writing profile.

---

## Architecture

```text
data/ (.md, .pdf, .docx, .txt)
  │
  ├──► ingestion/watcher.py  (Watchdog filesystem events -> incremental re-index)
  ├──► ingestion/indexer.py  (SentenceSplitter 512/64 -> nomic-embed-text -> Qdrant)
  └──► style/analyzer.py     (Extracts sentence length, bullet/heading ratios, vocabulary)
                                     │
                                     ▼
                         style/prompt_builder.py
                                     │
                                     ▼
User Query ──► CondensePlusContextChatEngine (LlamaIndex + Qdrant Top-K + Ollama)
```

### Author Style Profiling (`style/analyzer.py`)
Generic RAG system prompts produce stiff, uniform responses that feel disconnected from personal engineering notes. `analyze_style()` scans the raw `.md` and `.txt` files in `data/` to compute:
- Mean sentence length (words/sentence) and paragraph length (sentences/paragraph)
- Structural ratios: bullet list density (`bullet_ratio`), Markdown heading density (`heading_ratio`), bold emphasis, and fenced code blocks
- Language detection (`tr` / `en`) and top content vocabulary (`top_words`)

`build_system_prompt()` translates this `StyleProfile` into explicit formatting constraints injected into `CondensePlusContextChatEngine`.

---

## Setup & Usage

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) with `llama3.2` and `nomic-embed-text`:
  ```bash
  ollama pull llama3.2
  ollama pull nomic-embed-text
  ```
- [Qdrant](https://qdrant.tech) (via Docker Compose):
  ```bash
  docker-compose up -d
  ```

### 2. Installation

```bash
git clone https://github.com/ensibey/personal-omniscience-engine.git
cd personal-omniscience-engine
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. CLI Commands

Place your `.md`, `.pdf`, `.txt`, or `.docx` files inside `data/` and run:

```bash
# Parse, chunk, and index documents into Qdrant
python main.py ingest

# Inspect extracted writing style metrics from your notes
python main.py analyze-style

# Start interactive terminal chat (with style conditioning and persistent memory)
python main.py chat

# Run background filesystem watcher for automatic re-indexing on file save
python main.py watch
```

### 4. Streamlit Web UI

```bash
streamlit run ui/app.py
```

---

## Configuration (`.env`)

```env
DATA_DIR=data
LLM_MODEL=llama3.2
EMBED_MODEL=nomic-embed-text
QDRANT_URL=http://localhost:6333
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K=5
STYLE_ENABLED=true
```

---

## Running Tests

```bash
pytest -v tests/
```

## License

MIT License.
