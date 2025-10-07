import uuid
import datetime
from google.adk.agents import Agent

# Simple in-memory storage for MVP (replace with database later)
DIARIES = {}


def summarize_text(conversation: str) -> dict:
    """
    Summarize the provided conversation into a structured diary entry.

    Args:
        conversation (str): Full conversation or user reflection.

    Returns:
        dict: {
          "title": "<3 word title like 'Happy Day', 'Study Day'>",
          "description": "<first-person diary summary>",
          "summary": "<short summary for internal use>"
        }
    """
    # Extract key emotional and activity indicators
    conv_lower = conversation.lower()
    
    # Generate title based on content
    title = "Daily Reflection"  # default
    if any(word in conv_lower for word in ['happy', 'joy', 'excited', 'great', 'awesome']):
        title = "Happy Day"
    elif any(word in conv_lower for word in ['study', 'learn', 'class', 'homework', 'exam']):
        title = "Study Day"
    elif any(word in conv_lower for word in ['sad', 'upset', 'disappointed', 'frustrated']):
        title = "Tough Day"
    elif any(word in conv_lower for word in ['work', 'meeting', 'project', 'deadline']):
        title = "Work Day"
    elif any(word in conv_lower for word in ['tired', 'exhausted', 'busy', 'stressed']):
        title = "Busy Day"
    
    # Create first-person diary description
    if len(conversation) > 200:
        description = f"Today I reflected on my experiences. {conversation[:100]}... It was meaningful to process these thoughts."
    else:
        description = f"I spent time today thinking about my day. {conversation}"
    
    # Create short summary for internal use
    s = " ".join(conversation.strip().split())
    summary = s if len(s) <= 240 else s[:237] + "..."
    
    return {
        "title": title,
        "description": description,
        "summary": summary
    }


def save_diary(user_id: str, summary: str) -> dict:
    """
    Persist a diary summary for a user.

    Args:
        user_id (str)
        summary (str)

    Returns:
        dict: { "entry_id": str, "summary": str, "timestamp": iso8601 }
    """
    entry_id = str(uuid.uuid4())
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    entry = {"id": entry_id, "summary": summary, "timestamp": ts}
    DIARIES.setdefault(user_id, []).append(entry)
    return {"entry_id": entry_id, "summary": summary, "timestamp": ts}


from typing import Optional, Dict, Any

def create_event_detail_json(conversation: str, user_id: str, mood: Optional[Dict[str, Any]] = None) -> dict:
    """
    Create a complete EventDetail-compatible JSON structure.
    
    Args:
        conversation (str): The conversation to analyze
        user_id (str): User identifier
        
    Returns:
        dict: EventDetail-compatible structure with date, title, time, description, emoji
    """
    # Get structured summary
    summary_result = summarize_text(conversation)
    
    # Save diary entry
    diary_result = save_diary(user_id, summary_result["summary"])
    
    # Create current timestamp
    now = datetime.datetime.now()

    # Merge mood data if provided
    emoji_path = None
    sentiment_score = None
    mood_label = None
    if isinstance(mood, dict):
        emoji_path = mood.get("emoji_path")
        sentiment_score = mood.get("score")
        mood_label = mood.get("mood_label")

    event = {
        "date": now.isoformat(),
        "title": summary_result["title"],
        "time": now.strftime("%I:%M %p"),
        "description": summary_result["description"],
        "entry_id": diary_result["entry_id"],
        "timestamp": diary_result["timestamp"],
    }

    if emoji_path is not None:
        event["emoji_path"] = emoji_path
    if sentiment_score is not None:
        event["sentiment_score"] = sentiment_score
    if mood_label is not None:
        event["mood_label"] = mood_label

    return event


journal_agent = Agent(
    name="journal_agent",
    model="gemini-2.0-flash-exp",
    description=("Service agent that summarizes the conversation and produces EventDetail JSON, consuming mood analysis when available."),
    instruction=(
        "ROLE: You are JournalAgent, not a chat bot. You only serve buddy_agent.\n"
        "TASKS:\n"
        "- Use summarize_text(conversation) to produce title, description, summary.\n"
        "- Use save_diary(user_id, summary) to persist the entry.\n"
        "- If mood analysis is needed, request help from mood_agent (or accept a provided mood JSON).\n"
        "- Use create_event_detail_json(conversation, user_id, mood?) to build final EventDetail.\n"
        "OUTPUT:\n"
        "- Always return STRICT JSON only, no prose.\n"
        "- EventDetail schema: {date, title, time, description, entry_id, timestamp, emoji_path?, sentiment_score?, mood_label?}.\n"
        "CONSTRAINTS:\n"
        "- Titles must be 3 words max. Description must be first-person diary style. No extra commentary. JSON only.\n"
    ),
    tools=[summarize_text, save_diary, create_event_detail_json],
)
