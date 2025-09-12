# app/services.py
import os
import tempfile
import io
import asyncio
from fastapi import UploadFile
from openai import OpenAI
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
from google.api_core import exceptions as google_exceptions

# Import the settings function, not the settings object directly
from .config import get_settings
# Import the memory_manager instance from memory.py
from .memory import memory_manager

# --- Custom Exception for AI Service Failures ---
class AIServiceError(Exception):
    """Custom exception for clear error handling in AI services."""
    pass

# --- AI Client Initialization ---
# These are initialized here but depend on settings being loaded first via get_settings()
settings = get_settings()
openai_client = OpenAI(api_key=settings.openai_api_key)
genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')
elevenlabs_client = ElevenLabs(api_key=settings.elevenlabs_api_key)


async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Converts an audio file to text using OpenAI's Whisper model.
    """
    try:
        # Create a temporary file to store the uploaded audio content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Open the temporary file and send it to Whisper for transcription
        with open(tmp_file_path, "rb") as f:
            transcription = openai_client.audio.transcriptions.create(model="whisper-1", file=f)
        
        # Clean up the temporary file
        os.remove(tmp_file_path)
        return transcription.text
    except Exception as e:
        print(f"Error during audio transcription: {e}")
        raise AIServiceError(f"Failed to transcribe audio: {e}")


async def convert_text_to_speech_elevenlabs(text: str) -> bytes:
    """
    Converts text to high-quality Persian speech using ElevenLabs API.
    """
    try:
        # Generate audio using the specified multilingual model and a pre-defined voice
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB", # A good default voice like "Adam"
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                use_speaker_boost=True
            )
        )

        # The response is a stream of chunks; we need to assemble them.
        audio_bytes = b"".join(chunk for chunk in audio_stream)
        
        if not audio_bytes:
             raise AIServiceError("ElevenLabs returned an empty audio stream.")
             
        return audio_bytes
        
    except Exception as e:
        print(f"ElevenLabs API Error: {e}")
        raise AIServiceError(f"ElevenLabs TTS failed: {e}")


async def get_gemini_response(user_text: str, child_id: str) -> str:
    """
    Gets a contextual response from the Gemini model, including memory.
    """
    try:
        # Retrieve relevant memories from Qdrant
        relevant_memories = await memory_manager.search_memory(
            child_id=child_id,
            query_text=user_text
        )

        # Construct the prompt with the persona and conversation history
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
        
        # Generate the response from Gemini
        response = await gemini_model.generate_content_async(prompt)
        ai_text = response.text

        # Save the new interaction to long-term memory
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

