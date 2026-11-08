"""
engine/memory.py
Konuşma geçmişi yönetimi. LlamaIndex ChatMemoryBuffer kullanır.
"""

import json
import logging
from pathlib import Path

from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole

from config import BASE_DIR, MEMORY_TOKEN_LIMIT

logger = logging.getLogger(__name__)

HISTORY_FILE = BASE_DIR / ".chat_history.json"


def create_memory() -> ChatMemoryBuffer:
    """Yeni bir boş hafıza tamponu oluşturur."""
    return ChatMemoryBuffer.from_defaults(token_limit=MEMORY_TOKEN_LIMIT)


def save_history(memory: ChatMemoryBuffer) -> None:
    """Konuşma geçmişini diske kaydeder."""
    messages = memory.get_all()
    history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
    ]
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.debug(f"Geçmiş kaydedildi: {len(history)} mesaj.")


def load_history() -> ChatMemoryBuffer:
    """Daha önce kaydedilmiş geçmişi yükler. Yoksa boş hafıza döner."""
    memory = create_memory()

    if not HISTORY_FILE.exists():
        return memory

    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        messages = [
            ChatMessage(
                role=MessageRole(item["role"]),
                content=item["content"],
            )
            for item in history
        ]
        memory.set(messages)
        logger.info(f"💬 {len(messages)} mesajlık geçmiş yüklendi.")
    except Exception as e:
        logger.warning(f"Geçmiş yüklenemedi, sıfırlandı: {e}")

    return memory


def clear_history() -> None:
    """Geçmişi siler."""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    logger.info("Sohbet geçmişi temizlendi.")
