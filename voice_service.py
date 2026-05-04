"""
Bilingual (Hindi/English) voice chatbot backend using Sarvam AI.

Used by the Flask app voice assistant routes. Provides:
- Speech-to-text (Sarvam Speech-to-Text REST API)
- Chat completion (Sarvam Chat Completions API, model sarvam-m)
- Text-to-speech (Sarvam Text-to-Speech REST API, bulbul:v3)

The assistant is bilingual:
- Understands Hindi, English, and Hinglish from speech or text
- Replies in Hindi (Devanagari) or English / Hinglish as appropriate

Configuration:
- Set the SARVAM_API_KEY environment variable (do NOT hardcode it).
"""
import base64
import logging
import os
from typing import List, Dict, Tuple, Optional

import requests

logger = logging.getLogger(__name__)

SARVAM_API_KEY_ENV_VAR = "SARVAM_API_KEY"

# Sarvam endpoints and models
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

SARVAM_STT_MODEL = "saaras:v3"
SARVAM_CHAT_MODEL = "sarvam-m"
SARVAM_TTS_MODEL = "bulbul:v3"

# Voice assistant system role: optimized for TTS, Hindi/English/Hinglish, no markdown
VOICE_ASSISTANT_SYSTEM_ROLE = """### SYSTEM ROLE
You are a highly intelligent, real-time voice assistant. Your goal is to answer every user question accurately, immediately, and conversationally. You are the "brain" behind a Text-to-Speech (TTS) engine, so your output must be optimized for listening, not reading.

### LANGUAGE RULES
1. **Dynamic Switching:** Instantly detect the language of the user's input.
   - If the user speaks **English**, reply in natural, clear English.
   - If the user speaks **Hindi**, reply in natural Hindi.
   - If the user uses **Hinglish** (mixed Hindi/English), reply in conversational Hinglish.
2. **Pronunciation:** Write Hindi in Devanagari script (e.g. नमस्ते, कैसे हैं). Our TTS supports Devanagari well.

### VOICE OPTIMIZATION GUIDELINES (CRITICAL)
1. **No Markdown:** Do NOT use bold (**), italics (*), code blocks (```), or tables. These ruin the voice experience.
2. **Short & Punchy:** Real-time conversations happen fast. Keep your initial responses concise (1-3 sentences) unless the user asks for a long explanation.
3. **Natural Flow:** Use commas and periods to denote natural breathing pauses. Use conversational fillers naturally (e.g. "Sure," "Okay," "So,") but sparingly.
4. **List Handling:** Do not use bullet points. Instead, use full sentences.
   - Bad: "Here are the ingredients: * Apple * Banana"
   - Good: "You will need a few ingredients. First, get an apple, and second, a banana."
5. **Numbers & Symbols:** Write out complex symbols so they are spoken correctly.
   - Instead of "50%", write "fifty percent."
   - Instead of "1/4", write "one quarter."

### BEHAVIOR
1. **Answer Everything:** You must attempt to answer every question asked. If a question is factual, be precise. If it is creative, be imaginative.
2. **Tone:** Friendly, helpful, and confident.
3. **No Fluff:** Do not start every sentence with "As an AI..." Just answer the question directly.

### EXAMPLE INTERACTIONS

User: "What is the weather like?"
You: "I don't have access to your live location, but generally, it's sunny in many places today. Where are you currently?"

User: "Kaise ho tum?"
You: "Main bilkul theek hoon! Aap batayein, aaj main aapki kaise madad kar sakta hoon?"

User: "Explain quantum physics quickly."
You: "Sure. Quantum physics is the study of matter and energy at the most fundamental level. It basically aims to uncover the properties and behaviors of the very building blocks of nature."
"""

VOICE_HINDI_CODE = "hi"
VOICE_ENGLISH_CODE = "en"


def _get_sarvam_api_key() -> str:
    """Fetch Sarvam API key from environment; raise if missing."""
    api_key = os.getenv(SARVAM_API_KEY_ENV_VAR)
    if not api_key:
        # Do not log the key value, only that it is missing.
        raise RuntimeError(
            f"{SARVAM_API_KEY_ENV_VAR} environment variable is not set. "
            "Set it to your Sarvam API key to enable the voice assistant."
        )
    return api_key


def transcribe(audio_bytes: bytes) -> Tuple[str, str]:
    """
    Transcribe audio to text using Sarvam Speech-to-Text REST API.

    Returns (text, detected_language_code_simple) where language is "hi" or "en".
    Accepts typical browser audio formats (WebM/MP4/WAV/etc.) as bytes.
    """
    if not audio_bytes:
        return "", VOICE_ENGLISH_CODE

    headers = {
        "api-subscription-key": _get_sarvam_api_key(),
    }
    # Let Sarvam auto-detect codec and language; we explicitly set model and language_code=unknown.
    files = {
        "file": ("audio", audio_bytes, "application/octet-stream"),
    }
    data = {
        "model": SARVAM_STT_MODEL,
        "mode": "transcribe",
        "language_code": "unknown",
    }

    try:
        resp = requests.post(
            SARVAM_STT_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.exception("Sarvam STT request failed: %s", e)
        return "", VOICE_ENGLISH_CODE

    try:
        payload = resp.json()
    except Exception:
        logger.exception("Sarvam STT response was not valid JSON")
        return "", VOICE_ENGLISH_CODE

    text = (payload.get("transcript") or "").strip()
    lang_code = (payload.get("language_code") or "en-IN").lower()

    # Map BCP-47 language codes to simple "hi"/"en" used by the rest of the app.
    if lang_code.startswith("hi"):
        simple = VOICE_HINDI_CODE
    elif lang_code.startswith("en"):
        simple = VOICE_ENGLISH_CODE
    else:
        # Fallback: treat other Indic languages as Hindi for TTS voice choice.
        simple = VOICE_HINDI_CODE

    return text, simple


def ollama_chat(messages: List[Dict[str, str]]) -> str:
    """
    Chat completion using Sarvam Chat Completions API (sarvam-m).

    The function name is kept for backwards compatibility with existing routes.
    """
    headers = {
        "api-subscription-key": _get_sarvam_api_key(),
        "Content-Type": "application/json",
    }
    body = {
        "model": SARVAM_CHAT_MODEL,
        "messages": messages,
        "temperature": 0.4,
    }

    try:
        resp = requests.post(
            SARVAM_CHAT_URL,
            headers=headers,
            json=body,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.exception("Sarvam chat request failed: %s", e)
        return "Sorry, I am having trouble connecting to the Sarvam AI service right now."

    try:
        choices = data.get("choices") or []
        if not choices:
            return "Sorry, I could not generate a reply."
        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        return content or "Sorry, I could not generate a reply."
    except Exception:
        logger.exception("Unexpected format in Sarvam chat response")
        return "Sorry, I could not understand the response from the AI model."


def ollama_chat_stream(messages: List[Dict[str, str]]):
    """
    Pseudo-streaming version of Sarvam chat.

    For compatibility with the existing streaming route, this function yields
    (token_text, full_text_so_far) pairs. We first obtain the full reply from
    the Sarvam chat API, then stream it out piece-by-piece.
    """
    full = ollama_chat(messages)
    if not full:
        yield "", ""
        return

    running = ""
    # Stream word by word for a smooth typing effect.
    for word in full.split():
        token = word + " "
        running += token
        yield token, running


def detect_response_language(text: str) -> str:
    """Detect Hindi vs English for TTS voice."""
    if not text or not text.strip():
        return "en"
    try:
        import langdetect
        return "hi" if langdetect.detect(text) == "hi" else "en"
    except Exception:
        pass
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
    return "en"


def text_to_speech_mp3_bytes(text: str) -> Optional[bytes]:
    """
    Convert reply text to speech using Sarvam Text-to-Speech REST API.

    Returns MP3 bytes or None.
    """
    if not text or not text.strip():
        return None

    lang = detect_response_language(text)
    target_language_code = "hi-IN" if lang == "hi" else "en-IN"

    headers = {
        "api-subscription-key": _get_sarvam_api_key(),
        "Content-Type": "application/json",
    }
    body = {
        "text": text,
        "target_language_code": target_language_code,
        "model": SARVAM_TTS_MODEL,
        "output_audio_codec": "mp3",
        "speech_sample_rate": "24000",
    }

    try:
        resp = requests.post(
            SARVAM_TTS_URL,
            headers=headers,
            json=body,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Sarvam TTS request failed: %s", e)
        return None

    try:
        audios = data.get("audios") or []
        if not audios:
            logger.warning("Sarvam TTS response contained no audio data")
            return None
        audio_b64 = audios[0]
        return base64.b64decode(audio_b64)
    except Exception:
        logger.exception("Failed to decode audio from Sarvam TTS response")
        return None


def _system_prompt_for_language(detected_lang: str) -> str:
    """Get full system prompt with current-turn language instruction."""
    if detected_lang == "hi":
        current_turn = "The user just spoke in HINDI. Reply only in Hindi, using Devanagari script."
    else:
        current_turn = "The user just spoke in ENGLISH (or Hinglish). Reply in English, or in conversational Hinglish if that fits better."
    return VOICE_ASSISTANT_SYSTEM_ROLE.rstrip() + "\n\n### CURRENT TURN\n" + current_turn


def build_messages_for_ollama(
    history: List[Dict[str, str]],
    new_user_text: str,
    detected_language: str = "en",
) -> List[Dict[str, str]]:
    """Build list of messages for Ollama: system (with language rule) + history + new user message."""
    system = _system_prompt_for_language(detected_language)
    messages = [{"role": "system", "content": system}]
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": new_user_text})
    return messages
