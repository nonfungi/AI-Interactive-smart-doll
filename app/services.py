# app/services.py
import os
import tempfile
import io
import asyncio
from fastapi import UploadFile
from openai import OpenAI
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Import the settings function
from .config import get_settings
from .memory import MemoryManager

# --- Custom Exception for AI Service Failures ---
class AIServiceError(Exception):
    """Custom exception for clear error handling in AI services."""
    pass

# --- AI Client Initialization ---
settings = get_settings()
openai_client = OpenAI(api_key=settings.openai_api_key)
genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Converts an audio file to text using OpenAI's Whisper model.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
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

async def convert_text_to_speech_openai(text: str) -> bytes:
    """
    Converts text to speech using OpenAI's powerful TTS model.
    """
    try:
        # Generate audio using the specified model and a pre-defined voice
        response = openai_client.audio.speech.create(
            model="tts-1",       # مدل استاندارد، سریع و باکیفیت
            voice="nova",        # یکی از صداها را انتخاب کنید: alloy, echo, fable, onyx, nova, shimmer
            input=text
        )

        # The audio content is in response.content
        audio_bytes = response.content
        
        if not audio_bytes:
            raise AIServiceError("OpenAI TTS returned an empty audio stream.")
            
        return audio_bytes
        
    except Exception as e:
        print(f"OpenAI TTS API Error: {e}")
        raise AIServiceError(f"OpenAI TTS failed: {e}")


async def get_gemini_response(user_text: str, child_id: str, memory_manager: MemoryManager) -> str:
    """
    Gets a contextual response from the Gemini model, including memory.
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
        raise AIServiceError(f"Google Generative AI failed: {getattr(e, 'message', str(e))}")
    except Exception as e:
        print(f"An unexpected error occurred in Gemini response generation: {e}")
        raise AIServiceError(f"Unexpected error in Gemini response generation: {e}")

