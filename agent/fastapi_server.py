"""
Being Agent FastAPI Server
Based on Google ADK best practices for Flutter integration
"""

import os
import json
import asyncio
import warnings
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from google.genai.types import Part, Content
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.genai import types

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our Being agent
from agent import root_agent

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Load environment variables
load_dotenv()

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

class EventDetailResponse(BaseModel):
    title: str
    description: str
    emoji_path: str
    timestamp: str
    agent_response: str = ""

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str

# Global runner instance
runner = None

async def get_runner():
    """Initialize the ADK runner"""
    global runner
    if runner is None:
        runner = InMemoryRunner(
            app_name=APP_NAME,
            agent=root_agent,
        )
    return runner

async def analyze_with_agent(conversation: str, user_id: str) -> EventDetailResponse:
    """Analyze conversation using Being agent and return EventDetail structure"""
    
    try:
        # Get the runner
        current_runner = await get_runner()
        
        # Create a session for this analysis (not awaited - it's synchronous)
        session = current_runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
        )
        
        # Create analysis prompt
        analysis_prompt = f"""
        The user sent this message: "{conversation}"
        
        Please help them by:
        1. First, provide a caring, empathetic conversational response to what they shared
        2. Then use create_event_detail_json("{conversation}", "{user_id}") to generate a diary entry structure
        3. Use get_emoji_for_sentiment("{conversation}") to determine the appropriate emoji
        
        Please be warm, supportive, and genuine in your response. Show that you understand and care about what they shared.
        """
        
        # Send message to agent
        response = await current_runner.send_message(
            session=session,
            message=analysis_prompt,
        )
        
        # Parse agent response
        agent_text = response.text if hasattr(response, 'text') else str(response)
        
        # Extract structured data or create fallback response
        title = extract_title_from_response(agent_text, conversation)
        description = extract_description_from_response(agent_text, conversation)
        emoji_path = determine_emoji_from_sentiment(conversation)
        
        return EventDetailResponse(
            title=title,
            description=description,
            emoji_path=emoji_path,
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_response=agent_text
        )
        
    except Exception as e:
        print(f"Error in analyze_with_agent: {str(e)}")
        # Use fallback functions directly when agent fails
        title = extract_title_from_response("", conversation)
        description = extract_description_from_response("", conversation)
        emoji_path = determine_emoji_from_sentiment(conversation)
        
        return EventDetailResponse(
            title=title,
            description=description,
            emoji_path=emoji_path,
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_response=f"I understand you're sharing something important with me. Thank you for trusting me with your thoughts about: {conversation[:100]}..."
        )

def extract_title_from_response(response_text: str, conversation: str) -> str:
    """Extract or generate a title from the agent response"""
    response_lower = response_text.lower()
    conversation_lower = conversation.lower()
    
    # Check for common emotional keywords to generate appropriate titles
    if any(word in conversation_lower for word in ['happy', 'joy', 'excited', 'great', 'awesome']):
        return "Happy Day"
    elif any(word in conversation_lower for word in ['study', 'learn', 'class', 'homework', 'exam']):
        return "Study Day"
    elif any(word in conversation_lower for word in ['sad', 'upset', 'disappointed', 'frustrated']):
        return "Tough Day"
    elif any(word in conversation_lower for word in ['work', 'meeting', 'project', 'deadline']):
        return "Work Day"
    elif any(word in conversation_lower for word in ['tired', 'exhausted', 'busy', 'stressed']):
        return "Busy Day"
    else:
        return "Daily Reflection"

def extract_description_from_response(response_text: str, conversation: str) -> str:
    """Extract or generate a description from the agent response"""
    # Try to extract a first-person summary from the agent response
    lines = response_text.split('\n')
    
    # Look for lines that seem like diary entries (first person)
    for line in lines:
        line = line.strip()
        if line and (line.startswith('I ') or line.startswith('Today I ') or 'I felt' in line):
            return line
    
    # Fallback: create a simple summary
    if len(conversation) > 200:
        return f"I had a conversation today. {conversation[:150]}..."
    else:
        return f"I reflected on my day and shared my thoughts about: {conversation[:100]}"

def determine_emoji_from_sentiment(conversation: str) -> str:
    """Determine emoji path based on conversation sentiment"""
    conversation_lower = conversation.lower()
    
    # Expanded sentiment analysis with more words
    positive_words = [
        'happy', 'joy', 'excited', 'great', 'awesome', 'wonderful', 'amazing', 'love', 'good',
        'fantastic', 'excellent', 'perfect', 'brilliant', 'fun', 'enjoyable', 'pleasant',
        'delighted', 'thrilled', 'cheerful', 'optimistic', 'confident', 'successful',
        'accomplished', 'proud', 'satisfied', 'content', 'peaceful', 'relaxed'
    ]
    
    negative_words = [
        'sad', 'upset', 'angry', 'frustrated', 'terrible', 'awful', 'hate', 'bad', 'worried', 'anxious',
        'depressed', 'disappointed', 'stressed', 'overwhelmed', 'hopeless', 'miserable',
        'devastated', 'heartbroken', 'lonely', 'scared', 'fearful', 'nervous', 'irritated',
        'annoyed', 'embarrassed', 'ashamed', 'guilty', 'regret', 'difficult', 'tough', 'hard'
    ]
    
    # Count positive and negative words
    positive_count = sum(1 for word in positive_words if word in conversation_lower)
    negative_count = sum(1 for word in negative_words if word in conversation_lower)
    
    print(f"Sentiment analysis: positive_count={positive_count}, negative_count={negative_count}")
    print(f"Conversation: {conversation_lower}")
    
    # More sensitive detection - even 1 word can determine mood
    if positive_count > negative_count and positive_count > 0:
        return "assets/images/goodmood.png"
    elif negative_count > positive_count and negative_count > 0:
        return "assets/images/badmood.png"
    else:
        return "assets/images/moderatemode.png"

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
    return HealthResponse(
        status="healthy",
        service="Being Agent Service",
        timestamp=datetime.utcnow().isoformat()
    )

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
        
        # Create a session for this chat (not awaited - it's synchronous)
        session = current_runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=request.user_id,
        )
        
        # Create conversational prompt
        chat_prompt = f"""
        The user just shared: "{request.conversation}"
        
        Please respond to them with warmth, empathy, and understanding. 
        Show that you care about what they're going through and provide a supportive response.
        Don't use any tools for this - just provide a genuine, caring conversational response.
        """
        
        # Send message to agent
        response = await current_runner.send_message(
            session=session,
            message=chat_prompt,
        )
        
        # Get the conversational response
        agent_text = response.text if hasattr(response, 'text') else str(response)
        
        return {
            "response": agent_text,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"Error in chat_with_agent: {str(e)}")
        # Provide contextual fallback response based on conversation content
        conversation_lower = request.conversation.lower()
        
        if any(word in conversation_lower for word in ['happy', 'great', 'wonderful', 'amazing', 'excited']):
            fallback_response = f"That's wonderful to hear! It sounds like you're having a really positive experience. I'm so happy for you and I'd love to hear more about what made your day so special."
        elif any(word in conversation_lower for word in ['sad', 'upset', 'difficult', 'tough', 'stressed', 'worried']):
            fallback_response = f"I can hear that you're going through something challenging right now. It takes courage to share these feelings, and I want you to know that I'm here to listen and support you. Your feelings are completely valid."
        elif any(word in conversation_lower for word in ['study', 'exam', 'school', 'work', 'project']):
            fallback_response = f"It sounds like you're putting in a lot of effort with your responsibilities. That kind of dedication is really admirable. How are you feeling about everything you're working on?"
        else:
            fallback_response = f"Thank you for sharing that with me. I can tell this is something that's on your mind, and I appreciate you trusting me with your thoughts. I'm here to listen and support you however I can."
        
        return {
            "response": fallback_response,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

@app.post("/analyze_conversation", response_model=EventDetailResponse)
async def analyze_conversation(request: ConversationRequest):
    """
    Analyze conversation and return EventDetail-compatible JSON
    This endpoint replaces Google Gemini API calls
    """
    try:
        if not request.conversation.strip():
            raise HTTPException(status_code=400, detail="No conversation text provided")
        
        # Analyze using Being agent
        result = await analyze_with_agent(request.conversation, request.user_id)
        return result
        
    except Exception as e:
        print(f"Error in analyze_conversation: {str(e)}")
        # Return fallback response
        return EventDetailResponse(
            title="Daily Reflection",
            description="Unable to analyze conversation at this time. Please try again later.",
            emoji_path="assets/images/moderatemode.png",
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_response=f"Error: {str(e)}"
        )

@app.get("/test/{user_id}")
async def test_agent(user_id: str):
    """Test endpoint to verify agent functionality"""
    test_conversation = "I had a great day today! Everything went well and I'm feeling happy."
    
    try:
        result = await analyze_with_agent(test_conversation, user_id)
        return {
            "test_status": "success",
            "test_conversation": test_conversation,
            "result": result
        }
    except Exception as e:
        return {
            "test_status": "failed",
            "error": str(e)
        }

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