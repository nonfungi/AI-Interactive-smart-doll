# test_audio_upload.py

import requests
import os

# --- تنظیمات ---
API_URL = "http://localhost:8001/talk"
AUTH_TOKEN = "5f8b3c9a6d1e7f0a9b8c2d5e3f4a7b9c1d0e8f7a6b5c4d3e2f1a0b9c8d7e6f5"
CHILD_ID = "ali"
AUDIO_FILE_PATH = "test_voice.mp3" # نام فایل صوتی شما
OUTPUT_FILE_PATH = "response.mp3" # نام فایل خروجی

def test_audio_endpoint():
    """
    Sends an audio file to the /talk endpoint and saves the response.
    """
    if not os.path.exists(AUDIO_FILE_PATH):
        print(f"Error: Audio file not found at '{AUDIO_FILE_PATH}'")
        print("Please make sure you have recorded a voice message and saved it with this name in the project folder.")
        return

    headers = {
        "accept": "application/json",
        "x-auth-token": AUTH_TOKEN,
    }

    data = {
        "child_id": CHILD_ID,
    }

    try:
        with open(AUDIO_FILE_PATH, "rb") as audio_file:
            files = {
                "audio_file": (os.path.basename(AUDIO_FILE_PATH), audio_file, "audio/mpeg")
            }
            
            print("Sending request to the server...")
            response = requests.post(API_URL, headers=headers, data=data, files=files)

        if response.status_code == 200:
            with open(OUTPUT_FILE_PATH, "wb") as output_file:
                output_file.write(response.content)
            print(f"Success! Audio response saved to '{OUTPUT_FILE_PATH}'")
        else:
            print(f"Error: Server returned status code {response.status_code}")
            print("Response content:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"A connection error occurred: {e}")
        print("Please make sure your docker-compose services are running.")

if __name__ == "__main__":
    test_audio_endpoint()
