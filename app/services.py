# app/services.py

import tempfile
import os
from fastapi import UploadFile
from openai import OpenAI
import requests
import io

from langchain_openai import ChatOpenAI
from .config import settings
from .memory import memory_manager

# Initialize clients once
llm = ChatOpenAI(openai_api_key=settings.openai_api_key, model_name="gpt-3.5-turbo")
openai_client = OpenAI(api_key=settings.openai_api_key)

# --- FINAL UPDATE: Using a reliable and compatible model ---
HF_API_URL = "https://api-inference.huggingface.co/models/karim23657/persian-tts-vits"
HF_HEADERS = {"Authorization": f"Bearer {settings.huggingface_api_key}"}


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

async def convert_text_to_speech(text: str) -> bytes:
    """
    Converts text to Persian speech using a reliable model on Hugging Face.
    """
    payload = {"inputs": text}
    
    # Send the request to the Hugging Face Inference API
    response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload)
    
    if response.status_code == 200:
        # The response content is the raw audio bytes
        return response.content
    else:
        # Handle errors
        print(f"Error from Hugging Face API: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception("Failed to generate speech from Hugging Face API.")


async def get_ai_response(user_text: str, child_id: str) -> str:
    """
    Gets a response from the AI model, including context from memory.
    """
    relevant_memories = await memory_manager.search_memory(
        child_id=child_id,
        query_text=user_text
    )

    prompt = f"""
    You are a friendly, curious, and safe companion for a child named {child_id}.
    Your name is 'Abenek' and you are a blue robot.
    Always respond in Persian.
    
    Here is some of your past conversation history with {child_id}:
    ---
    {relevant_memories}
    ---
    
    Now, continue the conversation. The child just said: '{user_text}'
    """
    
    ai_message = await llm.ainvoke(prompt)
    ai_text = ai_message.content

    await memory_manager.save_to_memory(
        child_id=child_id,
        user_text=user_text,
        ai_text=ai_text
    )
    
    return ai_text
