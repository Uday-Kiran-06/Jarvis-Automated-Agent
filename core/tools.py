import os
import sys
import subprocess
import platform
import json
import re
import datetime
from typing import Dict, Any
from duckduckgo_search import DDGS

# ─── App name map (Windows) ──────────────────────────────────────
APP_MAP = {
    "notepad":        "notepad.exe",
    "chrome":         "chrome",
    "google chrome":  "chrome",
    "browser":        "chrome",
    "firefox":        "firefox",
    "edge":           "msedge",
    "spotify":        "spotify",
    "calculator":     "calc.exe",
    "paint":          "mspaint.exe",
    "file explorer":  "explorer.exe",
    "explorer":       "explorer.exe",
    "task manager":   "taskmgr.exe",
    "cmd":            "cmd.exe",
    "powershell":     "powershell.exe",
    "word":           "winword.exe",
    "excel":          "excel.exe",
    "powerpoint":     "powerpnt.exe",
    "vs code":        "code",
    "vscode":         "code",
    "discord":        "discord",
    "vlc":            "vlc",
    "terminal":       "wt.exe",  # Windows Terminal
}


# ─── File & System Tools ────────────────────────────────────────

def read_file(file_path: str) -> str:
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(file_path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"

def list_directory(directory: str = ".") -> str:
    try:
        return ", ".join(os.listdir(directory))
    except Exception as e:
        return f"Error: {e}"

def execute_command(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {e}"


# ─── App Launcher ────────────────────────────────────────────────

def open_application(name: str) -> str:
    """Opens any Windows application by name."""
    key = name.lower().strip()
    exe = APP_MAP.get(key, key)  # fallback: try the name directly
    try:
        subprocess.Popen(f'start "" "{exe}"', shell=True)
        return f"Opening {name}, Sir."
    except Exception as e:
        # try without quotes for executables in PATH
        try:
            subprocess.Popen(exe, shell=True)
            return f"Launching {name}."
        except Exception as e2:
            return f"Could not open {name}: {e2}"

def search_and_open(query: str) -> str:
    """Opens a web search in the default browser."""
    import urllib.parse
    import webbrowser
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searching for '{query}' in your browser, Sir."

def open_url(url: str) -> str:
    """Opens a specific URL in the default browser."""
    import webbrowser
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url} in your browser."

def get_system_info() -> str:
    """Returns system information: time, date, CPU, RAM, battery."""
    try:
        now = datetime.datetime.now()
        info = {
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%A, %B %d, %Y"),
            "platform": platform.system() + " " + platform.release(),
        }
        try:
            import psutil
            info["cpu_percent"] = f"{psutil.cpu_percent(interval=0.1)}%"
            info["ram_used"]    = f"{psutil.virtual_memory().percent}%"
            bat = psutil.sensors_battery()
            if bat:
                info["battery"] = f"{int(bat.percent)}% {'(Charging)' if bat.power_plugged else '(On Battery)'}"
        except ImportError:
            info["note"] = "Install psutil for CPU/RAM/battery info"

        lines = [f"{k}: {v}" for k, v in info.items()]
        return "\n".join(lines)
    except Exception as e:
        return f"Error getting system info: {e}"

def list_running_apps() -> str:
    """Lists currently running applications."""
    try:
        result = subprocess.run(
            'tasklist /fo csv /nh', shell=True, capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')[:20]
        apps = [l.split(',')[0].strip('"') for l in lines if l]
        return ", ".join(set(apps))
    except Exception as e:
        return f"Error: {e}"

def set_volume(level: int) -> str:
    """Sets the system volume (0-100) on Windows."""
    try:
        level = max(0, min(100, int(level)))
        # Use PowerShell to set volume
        script = (
            f"$wshShell = New-Object -ComObject WScript.Shell;"
            f"$currentVol = [Math]::Round((Get-WmiObject Win32_SoundDevice).Name);"
            f"[audio]::Volume = {level / 100};"
        )
        # Simpler alternative using nircmd if available, else PowerShell
        cmd = f'powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)" '
        # Use PowerShell Audio API
        ps = f"""
        Add-Type -TypeDefinition @'
        using System.Runtime.InteropServices;
        [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
        interface IAudioEndpointVolume {{ int _0(); int _1(); int _2(); int _3(); int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext); }}
        '@
        """
        # Simplest reliable way on Windows:
        subprocess.run(
            f'powershell -Command "[System.Media.SystemSounds]::Beep.Play()"',
            shell=True, capture_output=True
        )
        # Use nircmdc if available, otherwise inform user
        result = subprocess.run(
            f'nircmdc setsysvolume {int(level * 655.35)}',
            shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Volume command sent. (Install nircmd for precise control, Sir.)"
        return f"Volume set to {level}%, Sir."
    except Exception as e:
        return f"Could not set volume: {e}"

def take_screenshot() -> str:
    """Takes a screenshot and saves it to the Desktop."""
    try:
        import datetime, subprocess
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"jarvis_screenshot_{ts}.png")
        ps   = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen | Out-Null; $b = [System.Drawing.Bitmap]::new([System.Windows.Forms.SystemInformation]::PrimaryMonitorSize.Width, [System.Windows.Forms.SystemInformation]::PrimaryMonitorSize.Height); $g = [System.Drawing.Graphics]::FromImage($b); $g.CopyFromScreen(0,0,0,0,$b.Size); $b.Save("{path}")'
        subprocess.run(f'powershell -Command "{ps}"', shell=True, capture_output=True)
        return f"Screenshot saved to Desktop as jarvis_screenshot_{ts}.png, Sir."
    except Exception as e:
        return f"Screenshot failed: {e}"


# ─── DuckDuckGo Tools ─────────────────────────────────────────────

def search_web(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        return "\n\n".join(
            f"[{i+1}] {r.get('title','')}\n    {r.get('href','')}\n    {r.get('body','')[:200]}"
            for i, r in enumerate(results)
        )
    except Exception as e:
        return f"Search error: {e}"

def search_news(query: str = "latest news", max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
        if not results:
            return "No news found."
        return "\n\n".join(
            f"[{i+1}] {r.get('title','')}\n    Source: {r.get('source','?')} — {r.get('date','')}\n    {r.get('body','')[:200]}"
            for i, r in enumerate(results)
        )
    except Exception as e:
        return f"News error: {e}"


# ─── Tool Registry ─────────────────────────────────────────────

TOOLS = {
    # Search
    "search_web":         search_web,
    "search_news":        search_news,
    # System
    "open_application":   open_application,
    "search_and_open":    search_and_open,
    "open_url":           open_url,
    "get_system_info":    get_system_info,
    "list_running_apps":  list_running_apps,
    "set_volume":         set_volume,
    "take_screenshot":    take_screenshot,
    # File
    "read_file":          read_file,
    "write_file":         write_file,
    "list_directory":     list_directory,
    "execute_command":    execute_command,
}

TOOL_DESCRIPTIONS = """
AVAILABLE TOOLS — respond ONLY with JSON to use one:
{"tool": "name", "args": {"key": "value"}}

SEARCH:
  search_web(query, max_results=5)         — DuckDuckGo web search
  search_news(query, max_results=5)        — DuckDuckGo news headlines

APPS & BROWSER:
  open_application(name)                   — open Chrome, Spotify, Notepad, VS Code, etc.
  search_and_open(query)                   — open Google search in browser
  open_url(url)                            — open a specific URL

SYSTEM:
  get_system_info()                        — time, date, CPU, RAM, battery
  list_running_apps()                      — list running processes
  set_volume(level)                        — 0–100
  take_screenshot()                        — save screenshot to Desktop

FILE:
  read_file(file_path)
  write_file(file_path, content)
  list_directory(directory)
  execute_command(command)                 — run any terminal command
"""

def call_tool(name: str, args: Dict[str, Any]) -> str:
    if name in TOOLS:
        return TOOLS[name](**args)
    return f"Tool '{name}' not found. Available: {list(TOOLS.keys())}"
