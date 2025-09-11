import os
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- مهم: نام فایل JSON خود را اینجا وارد کنید ---
# مطمئن شوید این فایل در همان پوشه اسکریپت قرار دارد.
CREDENTIALS_FILENAME = "credentials.json"

try:
    # --- مرحله ۱: احراز هویت مستقیم با فایل JSON ---
    print(f"در حال خواندن اعتبارسنجی از فایل: '{CREDENTIALS_FILENAME}'...")
    if not os.path.exists(CREDENTIALS_FILENAME):
        raise FileNotFoundError(f"فایل '{CREDENTIALS_FILENAME}' پیدا نشد. لطفاً فایل JSON را در این پوشه قرار دهید.")
    
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILENAME)
    project_id = credentials.project_id
    print(f"اعتبارسنجی برای پروژه '{project_id}' با موفقیت خوانده شد.")

    # --- مرحله ۲: ساخت کلاینت با اعتبارسنجی مشخص ---
    print("در حال ساخت کلاینت TTS با اعتبارسنجی مشخص...")
    client = texttospeech.TextToSpeechClient(credentials=credentials)

    text_to_speak = "سلام، این یک آزمایش موفقیت‌آمیز است."
    synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)

    voice = texttospeech.VoiceSelectionParams(
        language_code="fa-IR",
        name="fa-IR-Standard-A"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # --- مرحله ۳: ارسال درخواست ---
    print(f"در حال ارسال درخواست به گوگل برای پروژه: {project_id}...")
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    print("پاسخ با موفقیت دریافت شد!")

    # --- مرحله ۴: ذخیره فایل صوتی ---
    output_filename = "local_test_output.mp3"
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)

    print(f"فایل صوتی با موفقیت در '{output_filename}' ذخیره شد.")
    print("این تست ثابت می‌کند که کلید JSON و پروژه گوگل شما کاملاً سالم هستند.")

except Exception as e:
    print("\n" + "="*20 + " خطا " + "="*20)
    print(f"یک خطا رخ داد: {e}")
    print("="*45)

