"""
engine/query.py
RAG sorgu motoru. Retrieval + Ollama ile cevap üretimi.
"""

import logging
from typing import Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer

from config import TOP_K
from engine.memory import load_history, save_history
from style.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)


def get_chat_engine(
    index: VectorStoreIndex,
    use_style: bool = True,
    memory: Optional[ChatMemoryBuffer] = None,
) -> CondensePlusContextChatEngine:
    """
    Verilen indeks üzerinde bir sohbet motoru oluşturur.

    Args:
        index: Qdrant'tan yüklenen vektör indeksi.
        use_style: Yazım tarzı taklidi aktif mi?
        memory: Dışarıdan gelen hafıza (None → diskten yükle).
    """
    if memory is None:
        memory = load_history()

    retriever = index.as_retriever(similarity_top_k=TOP_K)

    system_prompt = build_system_prompt(use_style=use_style)
    logger.info(f"🧠 Sistem prompt'u hazırlandı (stil={'açık' if use_style else 'kapalı'}).")

    chat_engine = CondensePlusContextChatEngine.from_defaults(
        retriever=retriever,
        memory=memory,
        system_prompt=system_prompt,
        verbose=False,
    )
    return chat_engine


def query(
    index: VectorStoreIndex,
    question: str,
    use_style: bool = True,
    persist: bool = True,
) -> str:
    """
    Tek seferlik soru-cevap (CLI modu için).

    Args:
        index: Qdrant vektör indeksi.
        question: Kullanıcının sorusu.
        use_style: Yazım tarzı taklidi aktif mi?
        persist: Sohbet geçmişini diske yaz.

    Returns:
        Modelin metin cevabı.
    """
    memory = load_history()
    chat_engine = get_chat_engine(index, use_style=use_style, memory=memory)

    logger.info(f"❓ Soru: {question}")
    response = chat_engine.chat(question)

    if persist:
        save_history(memory)

    return str(response)
