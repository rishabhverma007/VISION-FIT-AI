"""Shared Ollama helpers: model discovery and chat-capable model selection.

Used by gemini.py (local fallback), yoga_service.py, and diet_service.py so all
three resolve the same locally installed model instead of drifting apart.
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Preferred chat models, most-preferred first. Matched against the model's
# base name (the part before ':') so 'qwen2.5' never grabs 'qwen2.5vl' variants.
CHAT_PREFERRED = ['llama3.2', 'qwen2.5', 'mistral', 'llama3', 'gemma', 'tinyllama', 'phi3', 'deepseek-r1']

# Name fragments identifying embedding/reranking models, which cannot run chat.
_NON_CHAT_MARKERS = ('embed', 'minilm', 'rerank', 'bge-', 'e5-', 'gte-')


def is_chat_model(name: str) -> bool:
    """True if the model name does not look like an embedding/rerank model."""
    base = (name or '').split(':')[0].lower()
    return not any(marker in base for marker in _NON_CHAT_MARKERS)


def list_models() -> List[str]:
    """Return installed Ollama model names ([] if Ollama is unreachable).

    Tolerates both the newer object-style ollama.list() response and the older
    dict-style one.
    """
    try:
        import ollama
        models_info = ollama.list()
    except Exception as e:
        logger.warning("Failed to list Ollama models: %s", e)
        return []

    names: List[str] = []
    models = []
    if hasattr(models_info, 'models'):
        models = models_info.models
    elif isinstance(models_info, dict) and 'models' in models_info:
        models = models_info['models']

    for m in models:
        name = getattr(m, 'model', None) or getattr(m, 'name', None)
        if not name and isinstance(m, dict):
            name = m.get('model') or m.get('name')
        names.append(name if name else str(m))
    return names


def pick_chat_model(available: List[str], default: str = 'llama3.2') -> Optional[str]:
    """Pick the best chat-capable model from the installed list.

    Order: exact base-name match on CHAT_PREFERRED, then the first
    chat-capable model present, else None (caller should degrade gracefully
    rather than call an embedding model that cannot chat).
    """
    if not available:
        return default

    chat_models = [m for m in available if is_chat_model(m)]
    if not chat_models:
        return None

    by_base = {m.split(':')[0]: m for m in chat_models}
    for preferred in CHAT_PREFERRED:
        if preferred in by_base:
            return by_base[preferred]

    return chat_models[0]
