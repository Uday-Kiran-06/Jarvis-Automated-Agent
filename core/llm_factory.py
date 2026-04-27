import os
from typing import Optional
from groq import Groq
from google import generativeai as genai
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class LLMFactory:
    @staticmethod
    def get_client(provider: str = "groq"):
        provider = provider.lower()
        
        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            return Groq(api_key=api_key)
        
        elif provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment")
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-1.5-flash')
        
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            return OpenAI(api_key=api_key)
        
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            return Anthropic(api_key=api_key)
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")

def chat_completion(prompt: str, provider: str = "groq", system_prompt: str = "You are Jarvis, a helpful AI assistant."):
    client = LLMFactory.get_client(provider)
    
    if provider == "groq":
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        return response.choices[0].message.content
    
    elif provider == "gemini":
        chat = client.start_chat(history=[])
        response = chat.send_message(f"{system_prompt}\n\nUser: {prompt}")
        return response.text
    
    elif provider == "openai":
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o",
        )
        return response.choices[0].message.content
    
    return "Provider logic not fully implemented yet."
