import os
import sys
import json
import re
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_factory import chat_completion
from core.tools import call_tool, TOOL_DESCRIPTIONS

app = FastAPI(title="JarvisAI Backend v4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── System Prompt ────────────────────────────────────────────────
# Kept lean and clear to avoid confusing the LLM into always calling tools

SYSTEM_PROMPT = f"""You are Jarvis — a sophisticated AI assistant. Be concise, confident, and slightly British.

You have access to tools. Use them ONLY when truly necessary.
To use a tool, respond with ONLY this exact JSON format — nothing else before or after:
{{"tool": "tool_name", "args": {{"key": "value"}}}}

Available tools:
- search_news(query) → latest news/current events
- search_web(query) → look up facts online
- open_application(name) → launch an app like chrome, spotify, notepad
- search_and_open(query) → open Google search in browser
- open_url(url) → open a specific website
- get_system_info() → time, date, CPU, RAM, battery
- set_volume(level) → set volume 0-100
- take_screenshot() → save a screenshot
- automate_browser(url, task_type='content') → extract web content or take screenshots
- organize_files(folder_path) → sort files into subfolders by extension
- search_files(directory, pattern) → find files recursively

For normal conversation (greetings, math, opinions, general chat) — respond naturally in 1-3 sentences. Do NOT use JSON for normal chat.
"""


class CommandRequest(BaseModel):
    command: str
    provider: str = "groq"


def extract_tool_call(text: str) -> dict | None:
    """
    Finds and extracts a tool call JSON from the text.
    Prioritizes pure JSON, then code blocks, then raw braces.
    """
    stripped = text.strip()
    
    # 1. Try pure JSON (most common/intended)
    if stripped.startswith('{') and stripped.endswith('}'):
        try:
            data = json.loads(stripped)
            if "tool" in data: return data
        except Exception: pass

    # 2. Try Markdown code blocks
    match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if match:
        try:
            data = json.loads(match.group(1))
            if "tool" in data: return data
        except Exception: pass

    # 3. Aggressive: find the FIRST occurrence of something that looks like {"tool": ...}
    # This catches cases where the LLM talks before the JSON.
    match = re.search(r'(\{[\s\S]*?"tool"[\s\S]*?\})', text)
    if match:
        try:
            data = json.loads(match.group(1))
            if "tool" in data: return data
        except Exception: pass

    return None


@app.get("/health")
async def health():
    return {
        "status": "online",
        "model": "llama-3.3-70b-versatile",
        "tools_available": 8
    }


@app.post("/chat")
async def chat(request: CommandRequest):
    print(f"\n[USER] {request.command}")

    try:
        # Step 1 — LLM decides what to do
        llm_response = chat_completion(
            request.command,
            provider=request.provider,
            system_prompt=SYSTEM_PROMPT,
        )
        print(f"[LLM RAW] {llm_response[:300]}")

        # Step 2 — check if it's a strict tool call
        tool_data = extract_tool_call(llm_response)

        if tool_data:
            tool_name = tool_data["tool"]
            tool_args = tool_data.get("args", {})
            print(f"[TOOL] Calling {tool_name} with {tool_args}")

            raw_result = await call_tool(tool_name, tool_args)
            print(f"[TOOL RESULT] {str(raw_result)[:300]}")

            # Step 3 — LLM summarizes the result naturally
            summary_prompt = (
                f'The user asked: "{request.command}"\n\n'
                f"Tool '{tool_name}' returned raw data: {raw_result}\n\n"
                f"As Jarvis, provide a very brief (1-2 sentences) natural confirmation of what you found. "
                f"Do not repeat details like URLs or long summaries, as the user can see them in their dashboard. "
                f"Example: 'I have found the latest news for you, Sir. The headlines are now visible on your display.'"
            )
            final_reply = chat_completion(
                summary_prompt,
                provider=request.provider,
                system_prompt="You are Jarvis. Provide a brief, natural confirmation of tool results. Keep it to one or two sentences. Never output JSON.",
            )
            print(f"[JARVIS] {final_reply[:200]}")

            return {
                "response": final_reply,
                "tool": tool_name,
                "tool_result": raw_result,
                "type": "tool_execution",
            }

        # No tool call — plain conversation
        print(f"[JARVIS] {llm_response[:200]}")
        return {"response": llm_response, "type": "chat"}

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"I encountered a system error, Sir: {str(e)}",
            "type": "error",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
