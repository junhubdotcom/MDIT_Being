import uuid
import datetime
from google.adk.agents import Agent

# Simple in-memory storage for MVP (replace with database later)
DIARIES = {}

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

journal_agent = Agent(
    name="journal_agent",
    model="gemini-2.0-flash-exp",
    description=("Service agent that summarizes the conversation and produces EventDetail JSON, consuming mood analysis when available."),
    instruction=(
        "ROLE: You are JournalAgent, a service agent (not a chat bot). You only serve the caller.\n"
        "TASKS:\n"
        "1) Read the conversation text and summarize it YOURSELF (do not use any helper tool to summarize).\n"
        "   - Create: title (max 3 words) and a first-person diary-style description.\n"
        "   - Also produce a short 'summary' string to be stored.\n"
        "2) Persist the entry by calling save_diary(user_id, summary). Use the returned entry_id and timestamp.\n"
        "3) If a mood JSON is provided by the caller, include in the final output: \n"
        "   - emoji_path = mood.emoji_path (if present)\n"
        "   - sentiment_score = mood.score (if present)\n"
        "   - mood_label = mood.mood_label (if present)\n"
        "4) Return STRICT JSON only as EventDetail (no extra text).\n"
        "RETURN FORMAT (EventDetail JSON):\n"
        "{\n"
        "  \"date\": ISO-8601 datetime string for 'now',\n"
        "  \"title\": string (max 3 words),\n"
        "  \"time\": human-friendly time like '03:21 PM',\n"
        "  \"description\": first-person diary style string,\n"
        "  \"entry_id\": string (from save_diary),\n"
        "  \"timestamp\": ISO-8601 string (from save_diary),\n"
        "  \"emoji_path\"?: string,\n"
        "  \"sentiment_score\"?: number,\n"
        "  \"mood_label\"?: string\n"
        "}\n"
        "CONSTRAINTS:\n"
        "- Titles must be 3 words max. Description must be first-person diary style. STRICT JSON only.\n"
    ),
    tools=[save_diary],
)
