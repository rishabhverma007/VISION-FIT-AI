"""
Bilingual (Hindi/English) Voice Chatbot using Sarvam AI.

- Speech-to-text: Sarvam Speech-to-Text REST API (saaras:v3)
- Chat: Sarvam Chat Completions API (sarvam-30b)
- Text-to-speech: Sarvam Text-to-Speech REST API (bulbul:v3)

Run: streamlit run voice_chatbot_app.py

Important:
- Set the SARVAM_API_KEY environment variable to your Sarvam API key.
"""

import base64
import os
from pathlib import Path
from typing import Tuple

import requests
import streamlit as st

# -----------------------------------------------------------------------------
# Sarvam configuration
# -----------------------------------------------------------------------------
SARVAM_API_KEY_ENV_VAR = "SARVAM_API_KEY"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

SARVAM_STT_MODEL = "saaras:v3"
SARVAM_CHAT_MODEL = "sarvam-30b"
SARVAM_TTS_MODEL = "bulbul:v3"

SYSTEM_PROMPT = """You are a helpful bilingual assistant. If the user speaks Hindi, reply in Hindi (Devanagari script). If the user speaks English, reply in English. Keep answers concise and conversational."""


def _get_sarvam_api_key() -> str:
    api_key = os.getenv(SARVAM_API_KEY_ENV_VAR)
    if not api_key:
        raise RuntimeError(
            f"{SARVAM_API_KEY_ENV_VAR} environment variable is not set. "
            "Set it to your Sarvam API key to use this app."
        )
    return api_key

def _transcribe_audio(audio_bytes: bytes) -> Tuple[str, str]:
    """
    Transcribe audio using Sarvam Speech-to-Text.
    Returns (text, detected_language_simple) where language is "hi" or "en".
    """
    if not audio_bytes:
        return "", "en"

    headers = {
        "api-subscription-key": _get_sarvam_api_key(),
    }
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
        payload = resp.json()
    except Exception as e:
        st.error(f"Sarvam STT failed: {e}")
        return "", "en"

    text = (payload.get("transcript") or "").strip()
    lang_code = (payload.get("language_code") or "en-IN").lower()
    if lang_code.startswith("hi"):
        simple = "hi"
    elif lang_code.startswith("en"):
        simple = "en"
    else:
        simple = "hi"
    return text, simple


def _chat_with_sarvam(messages: list) -> str:
    """Call Sarvam chat completions (sarvam-30b) and return the reply."""
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
        choices = data.get("choices") or []
        if not choices:
            return "Sorry, I could not generate a reply."
        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        return content or "Sorry, I could not generate a reply."
    except Exception as e:
        st.error(f"Sarvam chat failed: {e}")
        return "Sorry, I am having trouble connecting to Sarvam AI right now."


def _detect_response_language(text: str) -> str:
    """
    Detect if response is Hindi or English for TTS voice selection.
    Uses langdetect if available; else simple heuristic (Devanagari = Hindi).
    """
    try:
        import langdetect
        lang = langdetect.detect(text)
        return "hi" if lang == "hi" else "en"
    except Exception:
        pass
    # Heuristic: Devanagari Unicode range
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
    return "en"


def _text_to_speech(text: str) -> str:
    """
    Convert response text to speech using Sarvam Text-to-Speech.
    Saves to a temp MP3 and returns the path.
    """
    if not text or not text.strip():
        return ""

    lang = _detect_response_language(text)
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
        audios = data.get("audios") or []
        if not audios:
            st.warning("No audio returned from Sarvam TTS. Showing text only.")
            return ""
        audio_b64 = audios[0]
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        st.warning(f"TTS failed: {e}. You can read the text reply.")
        return ""

    import tempfile

    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(audio_bytes)
    return path


# -----------------------------------------------------------------------------
# Session state: conversation history
# -----------------------------------------------------------------------------
def _init_session():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Bilingual Voice Assistant (Sarvam AI)", page_icon="🎤", layout="centered")
    st.title("🎤 Bilingual Voice Assistant (Sarvam AI)")
    st.caption("Hindi & English • Powered by Sarvam AI cloud APIs")

    _init_session()

    # Chat history
    for i, msg in enumerate(st.session_state["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("audio_path") and Path(msg["audio_path"]).exists():
                st.audio(msg["audio_path"], format="audio/mp3")
                # Autoplay the most recent assistant audio
                is_last = i == len(st.session_state["messages"]) - 1
                if is_last and msg["role"] == "assistant":
                    try:
                        import streamlit.components.v1 as components
                        with open(msg["audio_path"], "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        components.html(
                            f'<audio src="data:audio/mp3;base64,{b64}" autoplay></audio>',
                            height=0,
                        )
                    except Exception:
                        pass

    # Voice input: Start Recording (st.audio_input in Streamlit 1.31+) or file upload fallback
    audio_input = None
    try:
        if hasattr(st, "audio_input"):
            audio_input = st.audio_input("Start Recording — speak in Hindi or English", key="mic")
        else:
            st.info("Use file upload below to send a voice message.")
    except Exception:
        pass

    if not audio_input:
        audio_input = st.file_uploader("Or upload WAV/MP3", type=["wav", "mp3"], key="upload_audio")

    if audio_input:
        audio_bytes = audio_input.read()

        with st.spinner("Listening..."):
            text, detected_lang = _transcribe_audio(audio_bytes)

        if not text:
            st.warning("No speech detected. Try again.")
        else:
            # Append user message and rerun so we generate reply on next run
            st.session_state["messages"].append({"role": "user", "content": text})
            st.rerun()

    # Generate assistant reply when the last message is from the user (one turn at a time)
    if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
        user_text = st.session_state["messages"][-1]["content"]
        ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in st.session_state["messages"]:
            ollama_messages.append({"role": m["role"], "content": m["content"]})

        with st.spinner("Thinking..."):
            reply = _chat_with_sarvam(ollama_messages)

        audio_path = ""
        with st.spinner("Speaking..."):
            audio_path = _text_to_speech(reply)

        st.session_state["messages"].append({
            "role": "assistant",
            "content": reply,
            "audio_path": audio_path or None,
        })
        st.rerun()

    # Start Recording hint
    if not st.session_state["messages"]:
        st.markdown("---")
        st.markdown("**How to use:** Click **Start Recording** (or allow mic), speak in Hindi or English, then wait for reply and playback.")

    # Sidebar: clear chat
    with st.sidebar:
        st.header("Settings")
        if st.button("Clear chat history"):
            st.session_state["messages"] = []
            st.rerun()
        st.markdown("---")
        st.markdown("**Tech:** Sarvam Speech-to-Text • Sarvam Chat (sarvam-30b) • Sarvam Text-to-Speech (bulbul:v3)")


if __name__ == "__main__":
    main()
