import io
from typing import Annotated

from fastapi import APIRouter, Header, Form, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse

from ..config import settings
from ..services import (
    transcribe_audio, 
    get_gemini_response, 
    convert_text_to_speech_google,
    AIServiceError  # وارد کردن استثناء سفارشی
)

router = APIRouter()

# --- اندپوینت مکالمه با مدیریت خطای بهبودیافته ---
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
        # ۱. تبدیل صدا به متن
        transcribed_text = await transcribe_audio(audio_file)
        print(f"Transcribed text for child '{child_id}': {transcribed_text}")

        # ۲. دریافت پاسخ هوش مصنوعی
        ai_response_text = await get_gemini_response(user_text=transcribed_text, child_id=child_id)
        print(f"AI response for child '{child_id}': {ai_response_text}")

        # ۳. تبدیل متن به صدا
        response_audio_bytes = await convert_text_to_speech_google(ai_response_text)

        # ۴. ارسال پاسخ صوتی
        return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

    except AIServiceError as e:
        # این بخش خطاهای مشخص سرویس‌های هوش مصنوعی را مدیریت می‌کند
        print(f"A handled AI service error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"An error occurred with an AI service: {e}"
        )
    except Exception as e:
        # این بخش برای خطاهای پیش‌بینی نشده دیگر است
        print(f"An unexpected critical error occurred in /talk endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A critical unexpected error occurred in the conversation pipeline."
        )

