import uuid
import datetime
from google.adk.agents import Agent
#from google.adk.models.lite_llm import LiteLlm

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


def create_event_detail_json(conversation: str, user_id: str) -> dict:
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
    
    return {
        "date": now.isoformat(),
        "title": summary_result["title"],
        "time": now.strftime("%I:%M %p"),
        "description": summary_result["description"],
        "entry_id": diary_result["entry_id"],
        "timestamp": diary_result["timestamp"]
        # Note: emoji will be determined by mood_agent
    }


journal_agent = Agent(
    name="journal_agent",
    model="gemini-2.0-flash",
    #model=LiteLlm(model="openai/llama3.2"),  # Using OpenAI provider format for Ollama
    description=("Summarizes conversation into diary entries and creates EventDetail JSON for the buddy agent."),
    instruction=(
        "You are JournalAgent - a service for the Being Buddy agent. "
        "When called by the buddy agent with conversation content: "
        "1) Use summarize_text() to create structured diary content with title and description "
        "2) Use save_diary(user_id, summary) to persist the entry "
        "3) Use create_event_detail_json() for complete EventDetail structure "
        "4) Return structured response suitable for Flutter EventDetail model "
        "5) Do NOT chat with the user directly - you serve the buddy agent only "
        "6) Always provide clear, concise summaries suitable for diary entries "
        "7) Titles should be 3 words max (e.g., 'Happy Day', 'Study Day', 'Work Day') "
        "8) Descriptions should be first-person diary entries "
        
        "Format your response as: "
        "Diary analysis complete! Title: '[title]', Entry ID: [entry_id], Time: [timestamp]"
    ),
    tools=[summarize_text, save_diary, create_event_detail_json],
)
