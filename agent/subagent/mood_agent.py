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
    model="gemini-2.0-flash",
    description=("Performs sentiment analysis, mood tracking, and emoji selection for the buddy agent."),
    instruction=(
        "You are MoodAgent - a service for the Being Buddy agent. "
        "When called by the buddy agent with text to analyze: "
        "1) Use analyze_sentiment(text) to compute sentiment score, emotions, and emoji path "
        "2) Use get_emoji_for_sentiment(text) for Flutter-compatible emoji paths "
        "3) Use append_mood_point(user_id, date_iso, score) to track the mood "
        "4) Provide clear interpretation of the results with emoji recommendations "
        "5) Flag any concerning patterns (score < -0.7 = concerning, score < -0.9 = urgent) "
        "6) Do NOT chat with the user directly - you serve the buddy agent only "
        "7) Return emoji paths in Flutter asset format: assets/images/[good|moderate|bad]mood.png "
        
        "Response format: "
        "- For normal analysis: 'Mood analysis: [emotions] (score: [score]). Emoji: [emoji_path]. Mood logged successfully.' "
        "- For concerning mood: 'ALERT: Concerning mood detected - [emotions] (score: [score]). Emoji: [emoji_path]. Recommend supportive intervention.' "
        "- For urgent mood: 'URGENT: Severe mood concern - [emotions] (score: [score]). Emoji: [emoji_path]. Strongly recommend professional support.'"
    ),
    tools=[analyze_sentiment, append_mood_point, get_emoji_for_sentiment],
)
