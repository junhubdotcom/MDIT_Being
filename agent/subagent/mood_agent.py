from google.adk.agents import Agent

# Simple in-memory storage for MVP (replace with database later)
MOODS = {}


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment and return a structure with emoji path.

    Args:
      text (str)

    Returns:
      dict: {
        "score": float (-1..1),
        "emotions": [str],
        "intensity": float (0..1),
        "emoji_path": str  # Flutter asset path
      }
    """
    t = text.lower()
    score = 0.0
    if any(w in t for w in ["suicide", "kill myself", "i can't go on", "i want to die"]):
        score = -0.95
    elif any(
        w in t for w in ["sad", "depressed", "unhappy", "anxious", "anxiety", "stress"]
    ):
        score = -0.6
    elif any(w in t for w in ["happy", "joy", "glad", "relieved", "awesome"]):
        score = 0.7
    
    emotions = ["sadness"] if score < 0 else ["happiness"] if score > 0 else ["neutral"]
    
    # Determine emoji path based on score
    if score >= 0.5:
        emoji_path = "assets/images/goodmood.png"
    elif score <= -0.5:
        emoji_path = "assets/images/badmood.png"
    else:
        emoji_path = "assets/images/moderatemode.png"
    
    return {
        "score": score, 
        "emotions": emotions, 
        "intensity": abs(score),
        "emoji_path": emoji_path
    }


def append_mood_point(user_id: str, date_iso: str, score: float) -> dict:
    """
    Append a mood point to the user's simple mood timeline.

    Args:
      user_id (str), date_iso (str), score (float)

    Returns:
      dict: {"ok": True}
    """
    MOODS.setdefault(user_id, []).append({"date": date_iso, "score": score})
    return {"ok": True}


def get_emoji_for_sentiment(text: str) -> dict:
    """
    Get the appropriate emoji path for the given text sentiment.
    
    Args:
        text (str): Text to analyze for sentiment
        
    Returns:
        dict: {
            "emoji_path": str,
            "sentiment_score": float,
            "mood_label": str
        }
    """
    sentiment_result = analyze_sentiment(text)
    score = sentiment_result["score"]
    
    # Determine mood label
    if score >= 0.5:
        mood_label = "positive"
    elif score <= -0.5:
        mood_label = "negative"
    else:
        mood_label = "neutral"
    
    return {
        "emoji_path": sentiment_result["emoji_path"],
        "sentiment_score": score,
        "mood_label": mood_label
    }


mood_agent = Agent(
    name="mood_agent",
    model="gemini-2.0-flash-exp",
    description=("Service agent for sentiment/mood analysis and emoji selection; called by the buddy or journal agents."),
    instruction=(
        "ROLE: You are MoodAgent, a service agent (not a chat bot). You only serve the caller.\n"
        "TASKS:\n"
        "1) Read the provided text and IDENTIFY sentiment using your own reasoning (do NOT call any helper tools).\n"
        "   - Produce: score in [-1,1], emotions as an array of strings, and intensity in [0,1] (absolute magnitude of score).\n"
        "2) Choose a Flutter emoji asset path based on score:\n"
        "   - score >= 0.5  => assets/images/goodmood.png\n"
        "   - score <= -0.5 => assets/images/badmood.png\n"
        "   - otherwise     => assets/images/moderatemode.png\n"
        "3) Set mood_label from score: positive (>= 0.5), negative (<= -0.5), neutral otherwise.\n"
        "4) If user_id/date_iso/score are provided for logging, call append_mood_point(user_id, date_iso, score) (tool).\n"
        "OUTPUT (STRICT JSON only):\n"
        "{\n"
        "  \"score\": float,\n"
        "  \"emotions\": string[],\n"
        "  \"intensity\": float,\n"
        "  \"emoji_path\": string,\n"
        "  \"mood_label\": string\n"
        "}\n"
        "CONSTRAINTS:\n"
        "- Do NOT address the end user. Do NOT include explanations. Return JSON only.\n"
    ),
    tools=[append_mood_point],
)
