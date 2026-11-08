"""
config.py — Personal Omniscience Engine
Merkezi konfigürasyon. Tüm ayarlar buradan yönetilir.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Dizinler ───────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / os.getenv("DATA_DIR", "data")

# ── Qdrant ────────────────────────────────────────────────────────────────────
QDRANT_URL        = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME   = os.getenv("COLLECTION_NAME", "omniscience")

# ── Ollama Modelleri ──────────────────────────────────────────────────────────
LLM_MODEL         = os.getenv("LLM_MODEL", "llama3.2")
EMBED_MODEL       = os.getenv("EMBED_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Chunk Ayarları ────────────────────────────────────────────────────────────
CHUNK_SIZE        = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP     = int(os.getenv("CHUNK_OVERLAP", "64"))

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K             = int(os.getenv("TOP_K", "5"))

# ── Konuşma Hafızası ──────────────────────────────────────────────────────────
MEMORY_TOKEN_LIMIT = int(os.getenv("MEMORY_TOKEN_LIMIT", "4096"))

# ── Stil Analizi ──────────────────────────────────────────────────────────────
STYLE_ENABLED     = os.getenv("STYLE_ENABLED", "true").lower() == "true"

# ── Desteklenen Dosya Uzantıları ──────────────────────────────────────────────
SUPPORTED_EXTENSIONS = [".pdf", ".md", ".txt", ".docx"]
