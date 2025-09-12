# app/routers/conversation.py
import io
from typing import Annotated

from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse

# Import the specific services and custom exception needed
from ..services import (
    transcribe_audio, 
    get_gemini_response, 
    convert_text_to_speech_elevenlabs,
    AIServiceError
)
# Import the settings getter function
from ..config import get_settings

# --- Router Setup ---
# All endpoints defined here will be prefixed with /conversation
router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"]
)


@router.post("/talk")
async def talk(
    # Use Annotated for cleaner dependency injection and metadata
    x_auth_token: Annotated[str, Header(description="The secret master token for the doll.")],
    child_id: Annotated[str, Form(description="The unique identifier for the child.")],
    audio_file: UploadFile = File(..., description="The audio file of the child's speech (.webm format recommended).")
):
    """
    Handles a full voice conversation turn:
    1. Authenticates the device.
    2. Transcribes user audio to text (Whisper).
    3. Gets a contextual AI response (Gemini with RAG from Qdrant).
    4. Converts the response text back to audio (ElevenLabs).
    5. Streams the audio back to the client.
    """
    settings = get_settings()

    # --- 1. Authentication ---
    # Simple master token authentication for the hardware
    if x_auth_token != settings.doll_master_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication token."
        )

    # --- 2. AI Processing Pipeline ---
    try:
        # Transcribe the incoming audio file to text
        print(f"Received audio for child '{child_id}'. Transcribing...")
        transcribed_text = await transcribe_audio(audio_file)
        print(f"Transcribed text: '{transcribed_text}'")

        # Get a contextual response from the generative AI model
        print("Getting AI response from Gemini...")
        ai_response_text = await get_gemini_response(
            user_text=transcribed_text, 
            child_id=child_id
        )
        print(f"AI response text: '{ai_response_text}'")

        # Convert the AI's text response back into speech
        print("Converting response to speech with ElevenLabs...")
        response_audio_bytes = await convert_text_to_speech_elevenlabs(ai_response_text)
        print("Speech conversion successful.")

        # --- 3. Stream Audio Response ---
        # Stream the generated audio bytes back to the client
        return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

    except AIServiceError as e:
        # This is a handled error from one of our AI services (Whisper, Gemini, ElevenLabs)
        # We return a specific 503 error to indicate a temporary downstream service failure.
        print(f"A handled AI service error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"An AI service failed: {e}"
        )
    except Exception as e:
        # This catches any other unexpected errors in the pipeline.
        print(f"An unhandled exception occurred in /talk endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A critical internal error occurred."
        )

