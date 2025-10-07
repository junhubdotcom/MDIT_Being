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
        "ROLE: You are MoodAgent, not a chat bot. You only serve other agents.\n"
        "TASKS:\n"
        "- Use analyze_sentiment(text) to compute sentiment score, emotions, intensity, and emoji path.\n"
        "- Use get_emoji_for_sentiment(text) to return a Flutter-compatible emoji path when asked.\n"
        "- Use append_mood_point(user_id, date_iso, score) to log mood when a user_id and date are provided.\n"
        "OUTPUT:\n"
        "- Always return STRICT JSON only, no prose.\n"
        "- Schema: {\"score\": float, \"emotions\": string[], \"intensity\": float, \"emoji_path\": string, \"mood_label\": string}.\n"
        "- For severe cases (score < -0.9) set mood_label=\"negative\" and keep the same schema (no extra text).\n"
        "CONSTRAINTS:\n"
        "- Do NOT address the end user. Do NOT include explanations. Return JSON only.\n"
    ),
    tools=[analyze_sentiment, append_mood_point, get_emoji_for_sentiment],
)
