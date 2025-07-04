import asyncio
from app.services.tts_service import tts_service

async def main():
    # Generate test speech
    text = "This is a test of the audio download functionality."
    voice_id = tts_service.voice_id  # Use default voice
    raw_data = await tts_service.generate_executive_speech(text, voice_id, "urgent")
    
    if not raw_data:
        print("Failed to generate audio")
        return
    
    # Save to file
    file_path = "executive_speech.mp3"
    saved_path = await tts_service.save_audio_to_file(raw_data, file_path)
    
    if saved_path:
        print(f"Successfully saved audio to: {saved_path}")
    else:
        print("Failed to save audio file")

if __name__ == "__main__":
    asyncio.run(main())
