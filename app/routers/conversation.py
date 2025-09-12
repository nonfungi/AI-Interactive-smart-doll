# app/routers/conversation.py
import io
from typing import Annotated

from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import StreamingResponse

from ..services import (
    transcribe_audio, 
    get_gemini_response, 
    convert_text_to_speech_elevenlabs,
    AIServiceError
)
from ..config import get_settings
# Import the new dependency function and the type
from ..memory import get_memory_manager, MemoryManager

# --- Router Setup ---
router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"]
)

@router.post("/talk")
async def talk(
    x_auth_token: Annotated[str, Header(description="The secret master token for the doll.")],
    child_id: Annotated[str, Form(description="The unique identifier for the child.")],
    audio_file: UploadFile = File(..., description="The audio file of the child's speech (.webm format recommended)."),
    # --- FIX: Inject the memory manager as a dependency ---
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Handles a full voice conversation turn.
    """
    settings = get_settings()

    if x_auth_token != settings.doll_master_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication token."
        )

    try:
        print(f"Received audio for child '{child_id}'. Transcribing...")
        transcribed_text = await transcribe_audio(audio_file)
        print(f"Transcribed text: '{transcribed_text}'")

        print("Getting AI response from Gemini...")
        ai_response_text = await get_gemini_response(
            user_text=transcribed_text, 
            child_id=child_id,
            # --- FIX: Pass the injected dependency to the service function ---
            memory_manager=memory_manager
        )
        print(f"AI response text: '{ai_response_text}'")

        print("Converting response to speech with ElevenLabs...")
        response_audio_bytes = await convert_text_to_speech_elevenlabs(ai_response_text)
        print("Speech conversion successful.")

        return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

    except AIServiceError as e:
        print(f"A handled AI service error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"An AI service failed: {e}"
        )
    except Exception as e:
        print(f"An unhandled exception occurred in /talk endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A critical internal error occurred."
        )
