"""
engine/query.py
LlamaIndex CondensePlusContextChatEngine wrapper backed by Qdrant and local Ollama.
"""

from __future__ import annotations

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
    """Create a conversational retrieval engine over the Qdrant VectorStoreIndex."""
    if memory is None:
        memory = load_history()

    retriever = index.as_retriever(similarity_top_k=TOP_K)
    system_prompt = build_system_prompt(use_style=use_style)
    logger.info("initialized chat engine (style=%s)", use_style)

    return CondensePlusContextChatEngine.from_defaults(
        retriever=retriever,
        memory=memory,
        system_prompt=system_prompt,
        verbose=False,
    )


def query(
    index: VectorStoreIndex,
    question: str,
    use_style: bool = True,
    persist: bool = True,
) -> str:
    """Execute a single-turn query and optionally persist chat history."""
    memory = load_history()
    chat_engine = get_chat_engine(index, use_style=use_style, memory=memory)
    response = chat_engine.chat(question)

    if persist:
        save_history(memory)

    return str(response)
