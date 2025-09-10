# app/routers/conversation.py

import io
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Header, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from ..config import settings
from ..services import transcribe_audio, get_gemini_response, convert_text_to_speech_google
from ..schemas import AuthRequest

router = APIRouter()

@router.post("/auth/doll", tags=["Authentication"])
async def authenticate_doll(request: AuthRequest):
    if request.auth_token == settings.doll_master_auth_token:
        return {"status": "ok", "message": "Doll authenticated successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )

@router.post("/talk", tags=["Conversation"])
async def talk(
    x_auth_token: Annotated[str, Header(description="The secret master token for the doll.")],
    child_id: Annotated[str, Form()],
    audio_file: UploadFile = File(...)
):
    """
    Handles a full voice conversation turn with robust error handling.
    """
    if x_auth_token != settings.doll_master_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )

    try:
        # 1. Transcribe Audio to Text
        transcribed_text = await transcribe_audio(audio_file)
        print(f"Transcribed text for child '{child_id}': {transcribed_text}")

        # 2. Get AI Response
        ai_response_text = await get_gemini_response(user_text=transcribed_text, child_id=child_id)
        print(f"AI response for child '{child_id}': {ai_response_text}")

        # 3. Convert Text to Speech
        response_audio_bytes = await convert_text_to_speech_google(ai_response_text)

        # 4. Stream Audio Back
        return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

    except Exception as e:
        # --- NEW: Robust Error Handling ---
        # If any step in the process fails, log the error and send a
        # pre-defined, friendly audio message back to the user.
        print(f"An error occurred during the conversation pipeline: {e}")
        
        error_message = "اوپس، الان نمیتونم فکر کنم. میشه چند لحظه دیگه دوباره امتحان کنی؟"
        
        try:
            # Attempt to generate an audio error message
            error_audio_bytes = await convert_text_to_speech_google(error_message)
            return StreamingResponse(
                io.BytesIO(error_audio_bytes),
                media_type="audio/mpeg",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as tts_error:
            # If even the TTS service fails, return a standard JSON error
            print(f"Failed to generate TTS for error message: {tts_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A critical error occurred in the AI services."
            )
