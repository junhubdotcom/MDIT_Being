"""
Being Agent FastAPI Server (simplified)
Root agent only: health + chat
"""

import os
import json
import asyncio
import warnings
from pathlib import Path
from dotenv import load_dotenv
import traceback
from datetime import datetime

from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
try:
    # Prefer enum to satisfy Pydantic expected enum type
    from google.adk.agents.run_config import ResponseModality
    _HAS_ENUM = True
except Exception:
    ResponseModality = None
    _HAS_ENUM = False
from google.genai import types

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure package context when running this file directly (python fastapi_server.py)
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    import os as _os, sys as _sys
    _sys.path.append(_os.path.dirname(_os.path.dirname(__file__)))
    __package__ = "agent"

from . import root_agent
from subagent.mood_agent import mood_agent
from subagent.journal_agent import journal_agent

# Load environment variables
load_dotenv()

# Check for GOOGLE_API_KEY
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    print("GOOGLE_API_KEY is set.")
else:
    print("⚠️  GOOGLE_API_KEY is not set. ADK calls will fail; requests will return HTTP 500.")

APP_NAME = "Being Agent Service"

# FastAPI app setup
app = FastAPI(title="Being Agent API", description="Emotional tracking agent service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ConversationRequest(BaseModel):
    conversation: str
    user_id: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str

class MoodAnalyzeRequest(BaseModel):
    text: str
    user_id: str | None = None
    date_iso: str | None = None

class JournalCreateRequest(BaseModel):
    conversation: str
    user_id: str

# Global runner instance
runner = None
journal_runner = None
mood_runner = None

def now_utc_z() -> str:
    # Use timezone-aware UTC datetime and format with trailing Z
    try:
        # Python 3.11+
        ts = datetime.now(datetime.UTC).isoformat()
    except Exception:
        # Fallback for environments without datetime.UTC
        from datetime import timezone as _tz
        ts = datetime.now(_tz.utc).isoformat()
    return ts.replace("+00:00", "Z")

async def get_runner():
    """Initialize the ADK runner"""
    global runner
    if runner is None:
        runner = InMemoryRunner(
            app_name=APP_NAME,
            agent=root_agent,
        )
    return runner

async def get_journal_runner():
    """Initialize the ADK runner for the journal_agent"""
    global journal_runner
    if journal_runner is None:
        journal_runner = InMemoryRunner(
            app_name=f"{APP_NAME} - Journal",
            agent=journal_agent,
        )
    return journal_runner

async def get_mood_runner():
    """Initialize the ADK runner for the mood_agent"""
    global mood_runner
    if mood_runner is None:
        mood_runner = InMemoryRunner(
            app_name=f"{APP_NAME} - Mood",
            agent=mood_agent,
        )
    return mood_runner

def _try_parse_json_object(text: str):
    """Best-effort to parse a JSON object from model output.
    - Accepts direct JSON
    - Strips ``` fences and optional language tags
    - Extracts the first balanced {...} object if extra prose is present
    Returns dict on success, else None.
    """
    if not text:
        return None
    s = text.strip()
    # 1) Direct parse
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # 2) Strip code fences
    if s.startswith("```"):
        # remove opening fence line and closing fence
        lines = s.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            # drop first line and any trailing closing fence line
            if lines[-1].strip() == "```":
                inner = "\n".join(lines[1:-1]).strip()
            else:
                inner = "\n".join(lines[1:]).strip()
            try:
                obj = json.loads(inner)
                return obj if isinstance(obj, dict) else None
            except Exception:
                s = inner  # continue trying on inner
    # 3) Extract first balanced JSON object
    start = s.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                candidate = s[start:i+1]
                try:
                    obj = json.loads(candidate)
                    return obj if isinstance(obj, dict) else None
                except Exception:
                    return None
    return None

## Data models
# (Already defined above)

# API Endpoints

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "Being Agent API",
        "status": "running",
        "version": "1.0.0",
        "description": "Emotional tracking agent service for Flutter app"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Flutter service testing"""
    return HealthResponse(status="healthy", service=APP_NAME, timestamp=now_utc_z())

@app.post("/chat", response_model=dict)
async def chat_with_agent(request: ConversationRequest):
    """
    Get a conversational response from the Being agent
    This provides the caring, empathetic response to the user
    """
    try:
        if not request.conversation.strip():
            raise HTTPException(status_code=400, detail="No conversation text provided")
        
        # Get the runner
        current_runner = await get_runner()
        
        # Create a session for this chat (sync in current ADK version)
        session = current_runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=request.user_id,
        )

        # Configure text-only modality using enum if available
        if _HAS_ENUM and hasattr(ResponseModality, "TEXT"):
            run_config = RunConfig(response_modalities=[ResponseModality.TEXT])
        else:
            run_config = RunConfig(response_modalities=["TEXT"])  # fallback

        # Create live queue and start live run
        live_request_queue = LiveRequestQueue()
        live_events = current_runner.run_live(
            session=session,
            live_request_queue=live_request_queue,
            run_config=run_config,
        )

        # Send user message
        from google.genai.types import Content, Part
        content = Content(role="user", parts=[Part.from_text(text=request.conversation)])
        live_request_queue.send_content(content=content)

        # Collect streamed text until turn completes
        latest_text = ""
        try:
            async for event in live_events:
                # Capture any text content (ADK partials are often cumulative)
                evt_content = getattr(event, "content", None)
                parts = getattr(evt_content, "parts", None) if evt_content else None
                if parts and len(parts) > 0:
                    p0 = parts[0]
                    txt = getattr(p0, "text", None)
                    if isinstance(txt, str) and txt:
                        latest_text = txt
                # Stop on turn completion or interruption
                if getattr(event, "turn_complete", False) or getattr(event, "interrupted", False):
                    break
        finally:
            live_request_queue.close()

        agent_text = latest_text.strip()

        return {
            "response": agent_text,
            "timestamp": now_utc_z()
        }
        
    except Exception as e:
        print(f"Error in chat_with_agent: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mood/analyze", response_model=dict)
async def mood_analyze_endpoint(req: MoodAnalyzeRequest):
    """Agent-driven mood analysis using mood_agent via ADK."""
    try:
        text = (req.text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        current_runner = await get_mood_runner()
        # Prefer JSON modality when available
        if _HAS_ENUM and hasattr(ResponseModality, "JSON"):
            run_config = RunConfig(response_modalities=[ResponseModality.JSON])
        elif _HAS_ENUM and hasattr(ResponseModality, "TEXT"):
            run_config = RunConfig(response_modalities=[ResponseModality.TEXT])
        else:
            run_config = RunConfig(response_modalities=["TEXT"])  # fallback

        live_request_queue = LiveRequestQueue()
        session = current_runner.session_service.create_session(
            app_name=f"{APP_NAME} - Mood",
            user_id=req.user_id or "anonymous",
        )
        live_events = current_runner.run_live(
            session=session,
            live_request_queue=live_request_queue,
            run_config=run_config,
        )

        from google.genai.types import Content, Part
        instruction = (
            "You are a service agent. Read the provided text and IDENTIFY sentiment yourself. "
            "Return ONLY a single JSON object with fields {score, emotions, intensity, emoji_path, mood_label}. "
            "If user_id and date_iso are provided, you may call append_mood_point(user_id, date_iso, score) to log the mood. "
            "No code fences or extra text. JSON only."
        )
        payload = {
            "text": text,
            "user_id": req.user_id,
            "date_iso": req.date_iso or now_utc_z(),
        }
        content = Content(
            role="user",
            parts=[
                Part.from_text(text=instruction),
                Part.from_text(text=json.dumps(payload)),
            ],
        )
        live_request_queue.send_content(content=content)

        latest_text = ""
        try:
            async for event in live_events:
                evt_content = getattr(event, "content", None)
                parts = getattr(evt_content, "parts", None) if evt_content else None
                if parts and len(parts) > 0:
                    p0 = parts[0]
                    txt = getattr(p0, "text", None)
                    if isinstance(txt, str) and txt:
                        latest_text = txt
                if getattr(event, "turn_complete", False) or getattr(event, "interrupted", False):
                    break
        finally:
            live_request_queue.close()

        mood = _try_parse_json_object(latest_text)
        if not isinstance(mood, dict):
            preview = (latest_text or "").strip()
            if len(preview) > 160:
                preview = preview[:160] + "..."
            raise HTTPException(status_code=502, detail=f"Invalid JSON from mood_agent. Preview: {preview}")
        mood["timestamp"] = now_utc_z()
        return mood
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /mood/analyze: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/journal/create", response_model=dict)
async def journal_create_endpoint(req: JournalCreateRequest):
    """Create EventDetail JSON using the journal_agent via ADK (agent-driven tool calls)."""
    try:
        conversation = (req.conversation or "").strip()
        user_id = (req.user_id or "").strip()
        if not conversation:
            raise HTTPException(status_code=400, detail="conversation is required")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Agent-driven mood analysis using mood_agent
        mood_runner_local = await get_mood_runner()
        if _HAS_ENUM and hasattr(ResponseModality, "JSON"):
            mood_run_config = RunConfig(response_modalities=[ResponseModality.JSON])
        elif _HAS_ENUM and hasattr(ResponseModality, "TEXT"):
            mood_run_config = RunConfig(response_modalities=[ResponseModality.TEXT])
        else:
            mood_run_config = RunConfig(response_modalities=["TEXT"])  # fallback
        mood_request_queue = LiveRequestQueue()
        mood_session = mood_runner_local.session_service.create_session(
            app_name=f"{APP_NAME} - Mood",
            user_id=user_id,
        )
        mood_events = mood_runner_local.run_live(
            session=mood_session,
            live_request_queue=mood_request_queue,
            run_config=mood_run_config,
        )
        from google.genai.types import Content as _Content, Part as _Part
        mood_instruction = (
            "You are a service agent. Read the provided text and IDENTIFY sentiment yourself. "
            "Return ONLY a single JSON object with fields {score, emotions, intensity, emoji_path, mood_label}. "
            "No code fences or extra text. JSON only."
        )
        mood_payload = {"text": conversation}
        mood_content = _Content(role="user", parts=[
            _Part.from_text(text=mood_instruction),
            _Part.from_text(text=json.dumps(mood_payload)),
        ])
        mood_request_queue.send_content(content=mood_content)
        mood_text = ""
        try:
            async for ev in mood_events:
                evc = getattr(ev, "content", None)
                prts = getattr(evc, "parts", None) if evc else None
                if prts and len(prts) > 0:
                    p0 = prts[0]
                    txt = getattr(p0, "text", None)
                    if isinstance(txt, str) and txt:
                        mood_text = txt
                if getattr(ev, "turn_complete", False) or getattr(ev, "interrupted", False):
                    break
        finally:
            mood_request_queue.close()
        mood = _try_parse_json_object(mood_text) or {}

    # Get a dedicated runner for the journal agent
        current_runner = await get_journal_runner()

        # Prefer JSON modality if available, else text
        if _HAS_ENUM and hasattr(ResponseModality, "JSON"):
            run_config = RunConfig(response_modalities=[ResponseModality.JSON])
        elif _HAS_ENUM and hasattr(ResponseModality, "TEXT"):
            run_config = RunConfig(response_modalities=[ResponseModality.TEXT])
        else:
            run_config = RunConfig(response_modalities=["TEXT"])  # fallback

        # Start a live run to capture the final JSON
        live_request_queue = LiveRequestQueue()
        session = current_runner.session_service.create_session(
            app_name=f"{APP_NAME} - Journal",
            user_id=user_id,
        )
        live_events = current_runner.run_live(
            session=session,
            live_request_queue=live_request_queue,
            run_config=run_config,
        )

    # Build a precise instruction to the service agent to perform summarization and call save_diary
        from google.genai.types import Content, Part
        instruction = (
            "You are a service agent. Summarize the conversation YOURSELF (no helper tool). "
            "Create a short 'summary' string, a title (max 3 words), and a first-person diary-style description. "
            "Then call your tool save_diary(user_id, summary) and use its entry_id and timestamp. "
            "Build and return ONLY a single JSON object (EventDetail) with fields: {date, title, time, description, entry_id, timestamp, emoji_path?, sentiment_score?, mood_label?}. "
            "Use the provided now_iso for 'date' and time_str for 'time'. "
            "If mood is provided, include emoji_path/mood_label/sentiment_score when present. "
            "No code fences or extra text. JSON only."
        )
        # Prepare timestamp inputs for deterministic values in output
        now_iso = now_utc_z()
        time_str = datetime.now().strftime("%I:%M %p")
        # Embed inputs; mood passed as JSON for clarity
        payload = {
            "conversation": conversation,
            "user_id": user_id,
            "mood": mood,
            "now_iso": now_iso,
            "time_str": time_str,
        }
        content = Content(
            role="user",
            parts=[
                Part.from_text(text=instruction),
                Part.from_text(text=json.dumps(payload)),
            ],
        )
        live_request_queue.send_content(content=content)

        # Collect final strict JSON from the agent
        latest_text = ""
        try:
            async for event in live_events:
                evt_content = getattr(event, "content", None)
                parts = getattr(evt_content, "parts", None) if evt_content else None
                if parts and len(parts) > 0:
                    p0 = parts[0]
                    txt = getattr(p0, "text", None)
                    if isinstance(txt, str) and txt:
                        latest_text = txt
                if getattr(event, "turn_complete", False) or getattr(event, "interrupted", False):
                    break
        finally:
            live_request_queue.close()

        # Parse the strict JSON response (tolerate minor formatting deviations)
        event_detail = _try_parse_json_object(latest_text)
        if not isinstance(event_detail, dict):
            preview = (latest_text or "").strip()
            if len(preview) > 160:
                preview = preview[:160] + "..."
            raise HTTPException(status_code=502, detail=f"Invalid JSON from journal_agent. Preview: {preview}")

        return event_detail
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /journal/create: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# No analyze/test endpoints in this simplified server – root agent only

# Removed /analyze_conversation and /test for now (root agent only per request)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    try:
        await get_runner()
        print("✅ Being Agent Service started successfully")
        print(f"📡 Server running on http://localhost:8000")
        print(f"📚 API docs available at http://localhost:8000/docs")
    except Exception as e:
        print(f"❌ Failed to start Being Agent Service: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")