# app/routers/conversation.py
import io
from typing import Annotated
from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse

from ..config import settings
from ..services import (
    transcribe_audio,
    get_gemini_response,
    AIServiceError,
    convert_text_to_speech_gcloud
)

router = APIRouter()

@router.post("/talk", tags=["Conversation"])
async def talk(
    x_auth_token: Annotated[str, Header(description="The secret master token for the doll.")],
    child_id: Annotated[str, Form()],
    audio_file: UploadFile = File(...)
):
    """
    چرخه کامل: Audio → Text → (LLM) → Text → TTS → MP3 Stream
    """
    if x_auth_token != settings.doll_master_auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    try:
        # 1) STT
        transcribed_text = await transcribe_audio(audio_file)
        if not transcribed_text or not transcribed_text.strip():
            raise AIServiceError("Empty transcription")

        # 2) LLM پاسخ
        ai_response_text = await get_gemini_response(user_text=transcribed_text, child_id=child_id)

        # 3) TTS با Google Cloud
        response_audio_bytes = await convert_text_to_speech_gcloud(ai_response_text)

        # 4) استریم خروجی MP3
        return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

    except AIServiceError as e:
        # خطای قابل پیش‌بینی سرویس‌های AI
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        # خطای داخلی غیرمنتظره
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
