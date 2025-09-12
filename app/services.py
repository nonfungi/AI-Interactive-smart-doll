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

# Import the settings GETTER function
from .config import get_settings
# Import the memory_manager instance (it will be initialized at startup)
from .memory import memory_manager

# --- Custom Exception for clear error handling ---
class AIServiceError(Exception):
    """Custom exception for AI service failures to be caught in the router."""
    pass

# --- Initialize clients using the settings getter ---
# This ensures that settings are loaded before clients are created.
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
        # Save the uploaded file temporarily to disk
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
        print(f"ERROR - Whisper Transcription Failed: {e}")
        raise AIServiceError(f"Failed to transcribe audio: {e}")


async def convert_text_to_speech_elevenlabs(text: str) -> bytes:
    """
    Converts text to speech using the ElevenLabs API.
    This service is reliable in server environments.
    """
    try:
        # Generate audio stream from the text
        audio_stream = elevenlabs_client.generate(
            text=text,
            voice=Voice(
                voice_id='Rachel', # A good, clear voice
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2" # This model supports Persian
        )
        
        # Collect the audio bytes from the stream
        audio_bytes = b"".join(chunk for chunk in audio_stream)
        
        if not audio_bytes:
            raise AIServiceError("ElevenLabs returned an empty audio stream.")
            
        return audio_bytes
    except Exception as e:
        print(f"ERROR - ElevenLabs TTS Failed: {e}")
        raise AIServiceError(f"Failed to generate speech with ElevenLabs: {e}")


async def get_gemini_response(user_text: str, child_id: str) -> str:
    """
    Gets a contextual response from the Gemini model using long-term memory.
    """
    # Ensure memory_manager is initialized before using it.
    if not memory_manager:
        raise RuntimeError("Memory manager is not initialized.")

    try:
        # Retrieve relevant memories from Qdrant
        relevant_memories = await memory_manager.search_memory(
            child_id=child_id,
            query_text=user_text
        )

        # Create a detailed prompt for the AI
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
        
        # Generate the AI's response
        response = await gemini_model.generate_content_async(prompt)
        ai_text = response.text

        # Save the new interaction to memory
        await memory_manager.save_to_memory(
            child_id=child_id,
            user_text=user_text,
            ai_text=ai_text
        )
        
        return ai_text
    except google_exceptions.GoogleAPICallError as e:
        print(f"ERROR - Google Gemini API Failed: {e}")
        error_details = str(e)
        if hasattr(e, 'message'):
            error_details = e.message
        raise AIServiceError(f"Google Generative AI failed: {error_details}")
    except Exception as e:
        print(f"ERROR - Unexpected error in Gemini response: {e}")
        raise AIServiceError(f"An unexpected error occurred in Gemini response generation: {e}")

