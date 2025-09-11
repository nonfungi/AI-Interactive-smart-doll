import os
import tempfile
import io
import asyncio
from fastapi import UploadFile
from openai import OpenAI
import google.generativeai as genai
from gtts import gTTS
from google.api_core import exceptions as google_exceptions

from .config import settings
from .memory import memory_manager

# --- یک استثناء سفارشی برای خطاهای سرویس هوش مصنوعی ---
class AIServiceError(Exception):
    """Custom exception for AI service failures."""
    pass

# --- راه‌اندازی کلاینت‌ها ---
try:
    openai_client = OpenAI(api_key=settings.openai_api_key)
    genai.configure(api_key=settings.google_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
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


async def convert_text_to_speech_gtts(text: str) -> bytes:
    """
    تبدیل متن به گفتار فارسی با استفاده از کتابخانه ساده gTTS.
    این تابع به هیچ کلید یا احراز هویتی نیاز ندارد.
    """
    try:
        # gTTS یک کتابخانه همگام (sync) است. برای استفاده در محیط async،
        # آن را در یک executor جداگانه اجرا می‌کنیم تا برنامه مسدود نشود.
        loop = asyncio.get_running_loop()

        def tts_sync():
            tts = gTTS(text=text, lang='fa', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()

        audio_bytes = await loop.run_in_executor(None, tts_sync)
        return audio_bytes

    except Exception as e:
        print(f"An unexpected error occurred in gTTS: {e}")
        raise AIServiceError(f"An unexpected error occurred in gTTS: {e}")


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
