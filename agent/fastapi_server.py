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
from subagent.mood_agent import analyze_sentiment, get_emoji_for_sentiment
from subagent.journal_agent import summarize_text, save_diary, create_event_detail_json

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
    """Deterministic mood analysis using local tools (no LLM)."""
    try:
        text = (req.text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        mood = analyze_sentiment(text)
        # Enrich with label from helper for consistency
        emoji_info = get_emoji_for_sentiment(text)
        mood_label = emoji_info.get("mood_label")
        if mood_label is not None:
            mood["mood_label"] = mood_label
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
    """Create EventDetail JSON by summarizing conversation and injecting mood analysis."""
    try:
        conversation = (req.conversation or "").strip()
        user_id = (req.user_id or "").strip()
        if not conversation:
            raise HTTPException(status_code=400, detail="conversation is required")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Deterministic mood analysis
        mood = analyze_sentiment(conversation)
        emoji_info = get_emoji_for_sentiment(conversation)
        mood_label = emoji_info.get("mood_label")
        if mood_label is not None:
            mood["mood_label"] = mood_label

        # Persist diary entry and build final EventDetail JSON
        # Note: create_event_detail_json handles saving internally as well
        event_detail = create_event_detail_json(conversation, user_id, mood=mood)
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