# app/services.py
import os
import tempfile
import io
import asyncio
from fastapi import UploadFile
from openai import OpenAI
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.cloud import texttospeech

from .config import settings
from .memory import memory_manager

class AIServiceError(Exception):
    pass

# کلاینت‌ها
openai_client = OpenAI(api_key=settings.openai_api_key)
genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

def _ensure_gcp_credentials():
    # اگر متغیر محیطی ست باشد، همان را استفاده کن
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    # اگر JSON در .env آمده، در یک فایل temp بنویس
    if getattr(settings, "google_credentials_json", None):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(settings.google_credentials_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
        return path
    raise AIServiceError(
        "Google Cloud credentials not configured. "
        "Set GOOGLE_APPLICATION_CREDENTIALS or provide google_credentials_json in .env"
    )

async def convert_text_to_speech_gcloud(
    text: str,
    language_code: str = "fa-IR",
    voice_name: str | None = None,
    speaking_rate: float | None = None,
    pitch: float | None = None,
) -> bytes:
    try:
        _ensure_gcp_credentials()

        def synth_sync() -> bytes:
            client = texttospeech.TextToSpeechClient()

            # انتخاب voice
            _voice_name = voice_name or getattr(settings, "gcp_tts_voice", None)
            if not _voice_name:
                voices = client.list_voices(request={"language_code": language_code}).voices
                if not voices:
                    raise RuntimeError(f"No voices found for language {language_code}")
                _voice_name = voices[0].name

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=_voice_name)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=(speaking_rate or getattr(settings, "gcp_tts_rate", 1.0) or 1.0),
                pitch=(pitch or getattr(settings, "gcp_tts_pitch", 0.0) or 0.0),
            )
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            return response.audio_content

        loop = asyncio.get_running_loop()
        audio_bytes = await loop.run_in_executor(None, synth_sync)
        return audio_bytes

    except google_exceptions.GoogleAPICallError as e:
        raise AIServiceError(f"Google TTS API error: {e}") from e
    except Exception as e:
        raise AIServiceError(f"Failed to synthesize speech with Google TTS: {e}") from e

async def transcribe_audio(audio_file: UploadFile) -> str:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        with open(tmp_file_path, "rb") as f:
            transcription = openai_client.audio.transcriptions.create(model="whisper-1", file=f)
        os.remove(tmp_file_path)
        return transcription.text
    except Exception as e:
        raise AIServiceError(f"Failed to transcribe audio: {e}")

async def get_gemini_response(user_text: str, child_id: str) -> str:
    try:
        relevant_memories = await memory_manager.search_memory(child_id=child_id, query_text=user_text)
        prompt = f"""
        You are 'Abenek', a friendly, curious, and safe blue robot companion for a child.
        Your personality is warm, encouraging, and a little bit playful.
        Always respond in clear and simple Persian. Your goal is to spark imagination and learning.
        History:
        ---
        {relevant_memories}
        ---
        Child: '{user_text}'
        Reply in Persian:
        """
        response = await gemini_model.generate_content_async(prompt)
        ai_text = response.text

        await memory_manager.save_to_memory(child_id=child_id, user_text=user_text, ai_text=ai_text)
        return ai_text
    except google_exceptions.GoogleAPICallError as e:
        raise AIServiceError(f"Google Generative AI failed: {getattr(e, 'message', str(e))}")
    except Exception as e:
        raise AIServiceError(f"An unexpected error occurred in Gemini response generation: {e}")
