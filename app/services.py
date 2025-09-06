import os
import tempfile
from fastapi import UploadFile
from openai import OpenAI
import google.generativeai as genai
from google.cloud import texttospeech

from .config import settings
from .memory import memory_manager

# --- Initialize clients once ---
# We still use OpenAI for Whisper, as it's excellent for transcription.
openai_client = OpenAI(api_key=settings.openai_api_key)

# Configure Google clients with the new API key
genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel('gemini-1.5-flash') # A fast and capable model
tts_client = texttospeech.TextToSpeechClient()


async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Converts an audio file to text using OpenAI's Whisper model.
    (This function remains unchanged)
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        content = await audio_file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    with open(tmp_file_path, "rb") as f:
        transcription = openai_client.audio.transcriptions.create(model="whisper-1", file=f)
    
    os.remove(tmp_file_path)
    return transcription.text


async def convert_text_to_speech_google(text: str) -> bytes:
    """
    Converts text to Persian speech using Google Cloud TTS.
    """
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    # Configure the voice request for a natural Persian voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="fa-IR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    
    # Select the type of audio file you want (MP3 is common)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    # Perform the text-to-speech request
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    return response.audio_content


async def get_gemini_response(user_text: str, child_id: str) -> str:
    """
    Gets a response from the Gemini model, including context from memory.
    """
    relevant_memories = await memory_manager.search_memory(
        child_id=child_id,
        query_text=user_text
    )

    # A more detailed and robust prompt for Gemini
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

    # Save the new interaction to memory
    await memory_manager.save_to_memory(
        child_id=child_id,
        user_text=user_text,
        ai_text=ai_text
    )
    
    return ai_text
