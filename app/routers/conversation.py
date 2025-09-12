# app/routers/conversation.py
import io
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

# Import the AI service functions and the custom exception
from ..services import (
    transcribe_audio, 
    get_gemini_response, 
    convert_text_to_speech_elevenlabs,
    AIServiceError
)
# Import the settings getter to validate the master token
from ..config import get_settings, Settings

# Create a new router for conversation-related endpoints
router = APIRouter(
    tags=["Conversation"]
)

# --- Dependency for master token authentication ---
async def verify_master_token(x_auth_token: Annotated[str, Form()], settings: Settings = Depends(get_settings)) -> bool:
    """
    Dependency that checks if the provided master token is valid.
    This is a simple form of authentication suitable for the hardware.
    """
    if x_auth_token != settings.doll_master_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication token for doll."
        )
    return True

# --- The main conversation endpoint ---
@router.post("/talk")
async def talk(
    # Use the dependency to protect this endpoint
    token_verified: Annotated[bool, Depends(verify_master_token)],
    # Receive child_id and audio_file as form data
    child_id: Annotated[str, Form()], 
    audio_file: UploadFile = File(...)
):
    """
    Handles a full voice conversation turn:
    1. Receives audio and authenticates the request.
    2. Transcribes audio to text (Whisper).
    3. Gets a contextual AI response (Gemini).
    4. Converts the response text back to audio (ElevenLabs).
    5. Streams the audio back to the client.
    """
    print(f"Received audio for child_id: {child_id}")
    try:
        # Step 1: Transcribe Audio to Text
        transcribed_text = await transcribe_audio(audio_file)
        print(f"Transcribed text: '{transcribed_text}'")

        # Step 2: Get AI Response
        ai_response_text = await get_gemini_response(
            user_text=transcribed_text, 
            child_id=child_id
        )
        print(f"AI response: '{ai_response_text}'")

        # Step 3: Convert Text to Speech
        response_audio_bytes = await convert_text_to_speech_elevenlabs(ai_response_text)
        print("Successfully generated speech audio from ElevenLabs.")

        # Step 4: Stream Audio Back
        # StreamingResponse is efficient for sending binary data like audio.
        return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

    except AIServiceError as e:
        # This is a handled error from one of our AI services.
        # We return a 503 Service Unavailable status to indicate that a
        # downstream service failed.
        print(f"AI SERVICE ERROR: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"A critical error occurred in an AI service: {e}"
        )
    except Exception as e:
        # This catches any other unexpected errors during the process.
        print(f"UNEXPECTED INTERNAL SERVER ERROR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected internal error occurred: {e}"
        )

