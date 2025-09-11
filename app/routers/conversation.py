import io
from typing import Annotated

from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse

from ..config import settings
from ..services import transcribe_audio, get_gemini_response, AIServiceError, convert_text_to_speech_gtts

router = APIRouter()

@router.post("/talk", tags=["Conversation"])
async def talk(
    x_auth_token: Annotated[str, Header(description="The secret master token for the doll.")],
    child_id: Annotated[str, Form()],
    audio_file: UploadFile = File(...)
):
    """
    یک چرخه کامل مکالمه صوتی را مدیریت می‌کند.
    """
    if x_auth_token != settings.doll_master_auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    try:
        # 1. تبدیل صدا به متن
        transcribed_text = await transcribe_audio(audio_file)
        print(f"Transcribed text for child '{child_id}': {transcribed_text}")

        # 2. دریافت پاسخ هوش مصنوعی
        ai_response_text = await get_gemini_response(user_text=transcribed_text, child_id=child_id)
        print(f"AI response for child '{child_id}': {ai_response_text}")

        # 3. تبدیل متن پاسخ به صدا با gTTS
        response_audio_bytes = await convert_text_to_speech_gtts(ai_response_text)

        # 4. استریم کردن پاسخ صوتی
        return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

    except AIServiceError as e:
        # این یک خطای مدیریت شده از سرویس‌های هوش مصنوعی ماست
        print(f"A handled AI service error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"A critical error occurred in the AI services: {e}")
    
    except Exception as e:
        # این یک خطای پیش‌بینی نشده در سرور است
        print(f"An unhandled exception occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected internal server error occurred.")

