# Copilot Instructions for Being

## Project Overview
- **Being** is a cross-platform mental wellness app (Flutter frontend, Python backend) focused on AI-driven journaling, mood tracking, and emotional support.
- The core AI logic lives in `agent/` (Python), exposing a Flask API for integration with the Flutter app (`lib/`).
- The agent system is modular: a root agent delegates to sub-agents for journaling and mood analysis.

## Key Components
- `agent/agent.py`: Root agent orchestration, model selection, and main entry point.
- `agent/flask_server.py`: Flask API server exposing endpoints for the Flutter app.
- `agent/subagent/journal_agent.py`: Summarizes conversations, manages diary entries.
- `agent/subagent/mood_agent.py`: Sentiment analysis, mood tracking, crisis detection.
- `lib/`: Flutter app UI and integration logic.

## Developer Workflows
- **Backend (Python):**
  - Use a virtual environment (`.venv`). Activate before running/installing anything.
  - Install dependencies: `pip install -r requirements.txt` (in `agent/`).
  - For local LLMs, install and run Ollama (`ollama serve`). Download models as needed (`ollama pull llama3.2`).
  - Start the Flask server: `python flask_server.py` (runs on `localhost:5000`).
  - Test endpoints with `curl` or Postman (see `README.md` for example payloads).
- **Frontend (Flutter):**
  - Standard Flutter workflows apply (`flutter run`, `flutter build`, etc.).
  - Communicates with the backend via HTTP requests to Flask endpoints.

## Patterns & Conventions
- **Agent Delegation:**
  - The root agent decides when to delegate to sub-agents (e.g., journaling, mood analysis) based on user input.
  - Sub-agents are responsible for their own model selection and logic.
- **EventDetail JSON:**
  - All conversation analysis returns a standard JSON structure with `title`, `description`, `emoji_path`, and `timestamp`.
- **Environment Variables:**
  - Use `.env` in `agent/` to configure API keys and model endpoints. Ollama is default for local dev.
- **Crisis Detection:**
  - `mood_agent.py` auto-detects crisis language and triggers supportive responses.
- **No persistent storage** (MVP):
  - All data is in-memory; restarting the server clears conversation history.

## Integration Points
- **Flask API Endpoints:**
  - `POST /analyze_conversation`: Main entry for chat analysis from Flutter.
  - `GET /health`: Health check for backend status.
- **Model Switching:**
  - Change model source (Ollama vs. Google AI Studio) by editing the `model` parameter in agent/sub-agent files and updating `.env`.

## Troubleshooting
- Ensure Ollama is running and the correct model is downloaded for local dev.
- Activate the Python virtual environment before running backend commands.
- Check `.env` for correct API keys and endpoints if using Google AI Studio.
- Use debug commands in `agent/README.md` to verify agent and sub-agent loading.

## Example: Adding a New Sub-Agent
1. Create a new file in `agent/subagent/` (e.g., `gratitude_agent.py`).
2. Implement the agent logic and required tools.
3. Register the new sub-agent in `agent/agent.py`.
4. Expose new functionality via Flask if needed.

---

**Note:** Being Buddy is for emotional support only, not medical advice. All data is ephemeral unless persistent storage is implemented.
