# JarvisAI - Fully Automated Agent

JarvisAI is a sophisticated, fully automated AI agent designed to assist with complex tasks, automation, and information management. Inspired by the legendary JARVIS system, it combines a powerful reasoning core with a premium, interactive dashboard.

## Features

- **Autonomous Task Execution**: Decomposes complex goals into actionable steps.
- **Voice-to-Voice Interaction**: Fully AI-driven voice input and high-quality voice output.
- **Tool Integration**: Capable of interacting with the file system, web APIs, and more.
- **Futuristic UI**: A high-performance dashboard for monitoring agent state and output.
- **Memory Management**: Retains context across sessions for consistent assistance.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- API Keys (OpenAI/Anthropic/Gemini/Groq/ElevenLabs)

### Installation

1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install UI dependencies:
   ```bash
   cd ui && npm install
   ```

## Architecture

- `core/`: Python-based logic core.
- `ui/`: React/Vite-based dashboard.
- `voice/`: Voice input (STT) and output (TTS) handlers.
- `tools/`: Extensible toolset for the agent.
