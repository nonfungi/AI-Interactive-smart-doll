import os
import tempfile
import json
from fastapi import UploadFile
from openai import OpenAI
import google.generativeai as genai
from google.cloud import texttospeech

from .config import settings
from .memory import memory_manager

# --- NEW: Google Cloud Authentication Setup ---
# We check for the JSON content from the secret. If it exists, we write it to a
# temporary file and set the required environment variable for the Google Cloud client library.
if settings.google_credentials_json:
    # Use a temporary file that persists for the lifetime of the application
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as temp_creds_file:
        temp_creds_file.write(settings.google_credentials_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_creds_file.name
else:
    print("WARNING: GOOGLE_CREDENTIALS_JSON secret not found. Google Cloud TTS will likely fail.")

# --- Initialize clients once ---
# We still use OpenAI for Whisper.
openai_client = OpenAI(api_key=settings.openai_api_key)

# Configure Google clients. Gemini uses the simple API Key.
genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# The TTS client will now automatically find and use the credentials file
# specified by the GOOGLE_APPLICATION_CREDENTIALS environment variable.
tts_client = texttospeech.TextToSpeechClient()


# The rest of the functions (transcribe_audio, convert_text_to_speech_google, etc.)
# remain exactly the same.
async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Converts an audio file to text using OpenAI's Whisper model.
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
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="fa-IR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
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
