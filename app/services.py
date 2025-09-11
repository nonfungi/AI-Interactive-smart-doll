import os
import tempfile
import json
from fastapi import UploadFile, HTTPException, status
from openai import OpenAI
import google.generativeai as genai
from google.cloud import texttospeech
from google.api_core import exceptions as google_exceptions

from .config import settings
from .memory import memory_manager

# --- یک استثناء سفارشی برای خطاهای سرویس هوش مصنوعی ---
class AIServiceError(Exception):
    """Custom exception for AI service failures."""
    pass

# --- راه‌اندازی کلاینت‌ها ---
try:
    # راه‌اندازی OpenAI برای Whisper
    openai_client = OpenAI(api_key=settings.openai_api_key)

    # تنظیم کلاینت‌های گوگل
    genai.configure(api_key=settings.google_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    # راه‌اندازی کلاینت Google Cloud TTS با استفاده از کلید حساب سرویس
    if settings.google_credentials_json:
        # ساخت یک فایل موقت برای کلید
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".json") as temp_cred_file:
            temp_cred_file.write(settings.google_credentials_json)
            credential_path = temp_cred_file.name
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
        tts_client = texttospeech.TextToSpeechClient()
    else:
        # حالت جایگزین در صورتی که کلیدی ارائه نشده باشد
        tts_client = texttospeech.TextToSpeechClient()

except Exception as e:
    print(f"FATAL: Could not initialize AI clients: {e}")
    raise RuntimeError(f"Failed to initialize AI clients: {e}") from e


async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    تبدیل فایل صوتی به متن با استفاده از مدل Whisper.
    """
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
        print(f"Error during audio transcription: {e}")
        raise AIServiceError(f"Failed to transcribe audio: {e}")


async def convert_text_to_speech_google(text: str) -> bytes:
    """
    تبدیل متن به گفتار فارسی با استفاده از Google Cloud TTS و یک صدای مشخص.
    """
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # --- اصلاح نهایی: استفاده از یک صدای استاندارد و موجود ---
        voice = texttospeech.VoiceSelectionParams(
            language_code="fa-IR",
            name="fa-IR-Standard-A" # 'A' یک صدای استاندارد زنانه است
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        return response.audio_content
    except google_exceptions.GoogleAPICallError as e:
        print(f"Google TTS API Error: {e}")
        raise AIServiceError(f"Google TTS API failed: {e.message}")
    except Exception as e:
        print(f"An unexpected error occurred in TTS: {e}")
        raise AIServiceError(f"An unexpected error occurred in TTS: {e}")


async def get_gemini_response(user_text: str, child_id: str) -> str:
    """
    دریافت پاسخ از مدل Gemini با استفاده از حافظه.
    """
    try:
        relevant_memories = await memory_manager.search_memory(
            child_id=child_id,
            query_text=user_text
        )

        prompt = f"""
        You are 'Abenek', a friendly, curious, and safe blue robot companion for a child.
        Your personality is warm, encouraging, and a little bit playful.
        Always respond in clear and simple Persian. Your goal is to spark imagination and learning.
        
        Here is some of your past conversation history with this child:
        ---
        {relevant_memories}
        ---
        
        Now, continue the conversation. The child just said: '{user_text}'
        Your response in Persian:
        """
        
        response = await gemini_model.generate_content_async(prompt)
        ai_text = response.text

        await memory_manager.save_to_memory(
            child_id=child_id,
            user_text=user_text,
            ai_text=ai_text
        )
        
        return ai_text
    except google_exceptions.GoogleAPICallError as e:
        print(f"Google Generative AI API Error: {e}")
        error_details = str(e)
        if hasattr(e, 'message'):
            error_details = e.message
        raise AIServiceError(f"Google Generative AI failed: {error_details}")
    except Exception as e:
        print(f"An unexpected error occurred in Gemini response generation: {e}")
        raise AIServiceError(f"An unexpected error occurred in Gemini response generation: {e}")

