import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_factory import chat_completion
from voice.stt_handler import STTHandler
from voice.tts_handler import TTSHandler
import time

class JarvisAgent:
    def __init__(self, llm_provider: str = "groq", voice_provider: str = "gtts"):
        self.llm_provider = llm_provider
        self.stt = STTHandler()
        self.tts = TTSHandler(provider=voice_provider)
        self.system_prompt = "You are Jarvis, a highly advanced, sophisticated AI assistant. Your responses should be concise, professional, and slightly witty, just like the fictional JARVIS."

    def run_voice_loop(self):
        self.tts.speak("Systems online. How can I help you, Sir?")
        
        while True:
            user_input = self.stt.listen()
            
            if user_input:
                if any(word in user_input.lower() for word in ["exit", "shutdown", "stop"]):
                    self.tts.speak("Shutting down systems. Goodbye, Sir.")
                    break
                
                # Get response from LLM
                response = chat_completion(
                    user_input, 
                    provider=self.llm_provider, 
                    system_prompt=self.system_prompt
                )
                
                print(f"Jarvis: {response}")
                self.tts.speak(response)
            
            time.sleep(0.1)

if __name__ == "__main__":
    agent = JarvisAgent()
    # To run this, you'll need API keys set in .env
    # agent.run_voice_loop()
    print("Jarvis Agent initialized. Set your API keys in .env to run the loop.")
