# FastAPI Server Redesign Plan

This plan scraps the current `fastapi_server.py` and rebuilds it step-by-step around Google ADK (Runner + InMemorySessionService), ensuring clean imports, solid error handling, and Flutter-ready JSON.

## Goals
- Stable, minimal FastAPI service exposing:
  - GET /health
  - POST /chat (empathetic response)
  - POST /analyze_conversation (EventDetail JSON)
- Use a single ADK Runner with InMemorySessionService; one session per request (stateless HTTP), keyed by `user_id`.
- Keep agent logic in `agent/agent.py` with tools from subagents.
- Strict UTC ISO timestamps with a trailing Z.
- Clear diagnostics when GOOGLE_API_KEY is missing.

## Current Issues To Fix
- Mixed import styles and direct-run hacks.
- Legacy ADK API confusion (Runner constructor args, `send_message`, session usage).
- Fallback paths trigger too often when API key/config missing.

## Architecture Decisions
- Import strategy: package-relative imports (run as module: `python -m agent.fastapi_server`).
- Session management: `InMemorySessionService` created once; each request `create_session(app_name, user_id)`; pass `session_id` to `Runner.send_message`.
- Models: Use Pydantic for request/response models; keep Flutter’s EventDetail JSON fields consistent.
- Error handling: Do not return heuristic or canned fallbacks. If ADK/model calls fail, raise HTTP 500 with the exception message in the response. Log tracebacks server-side and still warn if GOOGLE_API_KEY is missing at startup.

## Endpoints
- GET /health
  - Response: `{ status, service, timestamp }`
- POST /chat
  - Request: `{ user_id: string, conversation: string }`
  - Response: `{ response: string, timestamp: string }`
- POST /analyze_conversation
  - Request: `{ user_id: string, conversation: string }`
  - Response: `{ title, description, emoji_path, timestamp, agent_response? }`

## Implementation Steps
1) Bootstrap
   - Create `now_utc_z()` helper.
   - Load `.env` and warn if GOOGLE_API_KEY missing.
   - Instantiate `FastAPI` and CORS.
   - Create single `InMemorySessionService` and lazily create `Runner`.
2) Health endpoint
3) /chat endpoint
   - Validate non-empty `conversation`.
   - Create session and call `Runner.send_message(session_id, message)`.
   - Return `response.text` and timestamp.
   - On error: raise HTTPException(500, detail=str(e)).
4) /analyze_conversation endpoint
   - Create analysis prompt: empathic reply + instruct to use tools (`create_event_detail_json`, `get_emoji_for_sentiment`).
   - Parse response; extract EventDetail using the subagent tools when applicable.
   - On error: raise HTTPException(500, detail=str(e)).
5) Testing & validation
   - Minimal smoke tests for both endpoints.
   - Verify timestamp format.
6) Docs
   - Update `agent/README.md` and `agent/fastapi_server_usage.md` if needed.

## Acceptance Criteria
- Running: `python -m agent.fastapi_server` starts without import errors.
- With valid GOOGLE_API_KEY, /chat and /analyze_conversation return agent-backed responses.
- Without API key, requests fail with HTTP 500 including the exception message; console warns clearly.
- JSON fields match the Flutter client expectations.

## Nice-to-haves (later)
- Optional request `session_id` to preserve context across multiple chats.
- Streaming endpoints or WebSocket for real-time responses.
- Metrics and structured logging.
