# Being Agent FastAPI – Usage Guide

This document explains how to start the server and call each API exposed by `fastapi_server.py`, including request/response shapes and example invocations.

## Start the server

Recommended (project root):

```powershell
# From the project root (folder that contains the `agent/` directory)
.\.venv\Scripts\Activate.ps1
pip install -r agent\requirements.txt
python -m agent.fastapi_server
```

Alternate (inside `agent/`):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python fastapi_server.py
```

- Server: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- CORS: allowed for all origins (useful for Flutter/Web dev)

## Models

- ConversationRequest
  - conversation: string (required, non-empty)
  - user_id: string (required)

- EventDetailResponse
  - title: string
  - description: string
  - emoji_path: string (Flutter asset path)
  - timestamp: string (ISO 8601, UTC with `Z` suffix)
  - agent_response: string (optional; agent text or fallback message)

- HealthResponse
  - status: string
  - service: string
  - timestamp: string (ISO 8601)

## Endpoints

### GET `/`
Returns basic service metadata.

- Response 200 (application/json):
```json
{
  "service": "Being Agent API",
  "status": "running",
  "version": "1.0.0",
  "description": "Emotional tracking agent service for Flutter app"
}
```

### GET `/health`
Health check.

- Response 200 (application/json):
```json
{
  "status": "healthy",
  "service": "Being Agent Service",
  "timestamp": "2025-10-05T12:34:56.789Z"
}
```

### POST `/chat`
Gets an empathetic conversational response from the agent.

- Request (application/json): ConversationRequest
```json
{
  "conversation": "I feel nervous about my exam tomorrow.",
  "user_id": "user_123"
}
```

- Validation: returns 400 if `conversation` is missing or empty/whitespace.

- Success Response 200 (application/json):
```json
{
  "response": "I hear how much this matters to you...",
  "timestamp": "2025-10-05T12:35:10.123Z"
}
```

- Failure behavior: If the agent backend errors, a context-aware fallback message is returned with 200 and current timestamp.

- PowerShell example:
```powershell
$body = @{ conversation = "I feel nervous about my exam tomorrow."; user_id = "user_123" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/chat -ContentType 'application/json' -Body $body
```

- curl example:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation":"I feel nervous about my exam tomorrow.","user_id":"user_123"}'
```

### POST `/analyze_conversation`
Analyzes a conversation and returns an EventDetail-compatible payload, including title/description/emoji. If the agent call fails, it falls back to lightweight client-side heuristics.

- Request (application/json): ConversationRequest
```json
{
  "conversation": "I had a great day today! Everything went well and I'm feeling happy.",
  "user_id": "user_123"
}
```

- Validation: returns 400 if `conversation` is missing or empty/whitespace.

- Success Response 200 (application/json): EventDetailResponse
```json
{
  "title": "Happy Day",
  "description": "I had a wonderful day...",
  "emoji_path": "assets/images/goodmood.png",
  "timestamp": "2025-10-05T12:36:22.456Z",
  "agent_response": "<agent text>"
}
```

Notes about `emoji_path`:
- Positive content -> `assets/images/goodmood.png`
- Negative content -> `assets/images/badmood.png`
- Neutral/mixed -> `assets/images/moderatemode.png`

- PowerShell example:
```powershell
$body = @{ conversation = "I had a great day today! Everything went well and I'm feeling happy."; user_id = "user_123" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/analyze_conversation -ContentType 'application/json' -Body $body
```

- curl example:
```bash
curl -X POST http://localhost:8000/analyze_conversation \
  -H "Content-Type: application/json" \
  -d '{"conversation":"I had a great day today! Everything went well and I\u0027m feeling happy.","user_id":"user_123"}'
```

### GET `/test/{user_id}`
Quick test endpoint that runs a predefined positive conversation through the analyzer.

- Example: `GET /test/user_123`

- Response 200 (application/json):
```json
{
  "test_status": "success",
  "test_conversation": "I had a great day today! Everything went well and I'm feeling happy.",
  "result": {
    "title": "Happy Day",
    "description": "I had a wonderful day...",
    "emoji_path": "assets/images/goodmood.png",
    "timestamp": "2025-10-05T12:37:40.000Z",
    "agent_response": "<agent text>"
  }
}
```

If it fails, you get:
```json
{
  "test_status": "failed",
  "error": "<message>"
}
```

## Behavior details and notes
- All timestamps are UTC ISO 8601; analyzer appends `Z` explicitly.
- CORS is permissive: `allow_origins=["*"]` (helpful for dev/testing).
- On analysis failure, the server synthesizes reasonable defaults for title/description/emoji and still responds 200 (with `agent_response` set to an explanatory/fallback message).
- Emoji assets are Flutter paths; ensure these exist in your Flutter app under `assets/images/` and are declared in `pubspec.yaml`.
- Large inputs are accepted; description generation truncates long text with ellipses.

## Common errors
- 400 Bad Request: `conversation` is empty or missing.
- 500 Internal Error: only for unexpected server crashes; analyze endpoint generally catches errors and returns a synthesized response.
- Import errors when running directly: Prefer `python -m agent.fastapi_server` from project root, or run `python fastapi_server.py` from inside `agent/` (bootstrap included).

## Troubleshooting
- Ensure your virtual environment is active and packages are installed:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  pip install -r agent\requirements.txt
  ```
- Ensure `.env` under `agent/` contains your Google API key if using Google AI Studio:
  ```
  GOOGLE_GENAI_USE_VERTEXAI=FALSE
  GOOGLE_API_KEY=your_google_api_key_here
  ```
- Use Swagger UI at http://localhost:8000/docs to send test requests.
