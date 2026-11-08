"""
ingestion/indexer.py
LlamaIndex + Qdrant entegrasyonu. Dökümanları vektöre dönüştürüp saklar.
"""

import logging
from typing import List, Optional

from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.schema import Document
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    EMBED_MODEL,
    LLM_MODEL,
    OLLAMA_BASE_URL,
    QDRANT_URL,
)

logger = logging.getLogger(__name__)


# ── Global Settings (LlamaIndex v0.10+ akışı) ─────────────────────────────────

def configure_settings() -> None:
    """LlamaIndex global ayarlarını Ollama modellerine yönlendirir."""
    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=120.0,
    )
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP
    logger.info(
        f"⚙️  Ayarlar: LLM={LLM_MODEL}, Embed={EMBED_MODEL}, "
        f"Chunk={CHUNK_SIZE}/{CHUNK_OVERLAP}"
    )


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def ensure_collection(client: QdrantClient, vector_size: int = 768) -> None:
    """Koleksiyon yoksa oluşturur."""
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(f"🗄️  '{COLLECTION_NAME}' koleksiyonu oluşturuldu.")
    else:
        logger.info(f"🗄️  '{COLLECTION_NAME}' koleksiyonu mevcut, devam ediliyor.")


def build_index(documents: List[Document]) -> Optional[VectorStoreIndex]:
    """
    Dökümanları vektörleştirip Qdrant'a yazar.
    Boş döküman listesinde None döner.
    """
    if not documents:
        logger.warning("İndekslenecek döküman yok.")
        return None

    configure_settings()
    client = get_qdrant_client()

    # nomic-embed-text 768-dims üretir
    ensure_collection(client, vector_size=768)

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    logger.info(f"🔄 {len(documents)} döküman indeksleniyor…")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )
    logger.info("✅ İndeksleme tamamlandı.")
    return index


def load_existing_index() -> Optional[VectorStoreIndex]:
    """
    Qdrant'taki mevcut indeksi bağlar (yeniden vektörleştirme yapmaz).
    Sorgu ve watcher modunda kullanılır.
    """
    configure_settings()
    client = get_qdrant_client()

    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        logger.warning("Henüz bir indeks yok. Önce 'ingest' komutunu çalıştır.")
        return None

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )
    logger.info("✅ Mevcut indeks yüklendi.")
    return index
