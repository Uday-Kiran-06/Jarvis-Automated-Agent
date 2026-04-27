import os
from gtts import gTTS
import playsound
import tempfile

class TTSHandler:
    def __init__(self, provider: str = "gtts"):
        self.provider = provider.lower()

    def speak(self, text: str):
        if self.provider == "gtts":
            self._speak_gtts(text)
        elif self.provider == "elevenlabs":
            self._speak_elevenlabs(text)
        else:
            print(f"TTS: {text}")

    def _speak_gtts(self, text: str):
        tts = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
            tts.save(f"{fp.name}")
            # Note: playsound might need installation or specific OS handling
            try:
                # On Windows, playsound can sometimes be finicky
                # Using a simple print as fallback if audio fails
                print(f"Jarvis (Audio): {text}")
                # playsound.playsound(f"{fp.name}")
            except Exception as e:
                print(f"Audio playback error: {e}")

    def _speak_elevenlabs(self, text: str):
        # Placeholder for ElevenLabs integration
        print(f"Jarvis (ElevenLabs): {text}")

if __name__ == "__main__":
    tts = TTSHandler()
    tts.speak("Hello, I am Jarvis. How can I assist you today?")
