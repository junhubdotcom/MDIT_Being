# Subagent Implementation Plan

## Goals
- Delegate specialized tasks to subagents while the buddy (root) agent remains the single voice to the user.
- Define clear JSON contracts for cross-agent data flow: mood analysis -> journaling -> buddy response.
- Add explicit API endpoints for deterministic usage of mood analysis and journaling.
- Align models to gemini-2.0-flash across all agents.

## Agents and Roles
- buddy_agent (root)
  - Main conversation and orchestration.
  - Delegates to subagents instead of calling raw tools.
  - Returns final JSON for specific use cases when asked (mood, journal) or chats empathetically otherwise.
- mood_agent (subagent)
  - Analyzes sentiment of text and returns JSON with sentiment score, emotions, intensity, emoji_path, mood_label.
  - No direct user chat; serves buddy_agent and journal_agent.
- journal_agent (subagent)
  - Summarizes the day’s conversation and composes final EventDetail JSON.
  - Consumes mood analysis JSON (from mood_agent) when available and includes emoji_path/mood metadata.

## Data Contracts
- MoodAnalysis JSON
  - Fields: score (float), emotions (string[]), intensity (float), emoji_path (string), mood_label ("positive"|"neutral"|"negative"), timestamp (ISO8601 Z)
- EventDetail JSON (journal)
  - Fields: date (ISO string), title (<= 3 words), time (hh:mm AM/PM), description (first-person diary), entry_id (uuid), timestamp (ISO Z), emoji_path (string), sentiment_score (float), mood_label (string)

## Delegation Flow
1) User speaks to buddy_agent.
2) For mood checks: buddy_agent delegates to mood_agent and then replies with supportive guidance plus the mood JSON.
3) For diary requests: buddy_agent delegates to journal_agent. journal_agent consults mood_agent (or receives mood from buddy) so the final EventDetail JSON includes mood fields.
4) buddy_agent returns the final JSON to the app for those use cases.

## Prompt Guidelines
- mood_agent: "Always output strict JSON only." Include the required keys; never add prose.
- journal_agent: "Use mood analysis when available. Output strict EventDetail JSON only." Titles max 3 words; description is first-person.
- buddy_agent: "You are the single voice; delegate to subagents. For diary/mood intents, return the specified JSON only. Otherwise, chat empathetically."

## API Endpoints (FastAPI)
- POST /mood/analyze
  - Input: { text: string }
  - Output: MoodAnalysis JSON + timestamp
  - Implementation: call Python tools directly (no LLM); deterministic
- POST /journal/create
  - Input: { user_id: string, conversation: string }
  - Output: EventDetail JSON (includes emoji_path + sentiment)
  - Implementation: summarize_text + analyze_sentiment + save_diary + create_event_detail_json(mood)
- POST /chat (existing)
  - Continues to use ADK for the buddy agent chat

## Error Handling
- Deterministic endpoints (/mood, /journal) return 400 for bad inputs; 500 for internal errors with message.
- /chat keeps current behavior (500 on ADK failures; no fake fallbacks).

## Testing
- Unit test Python functions (analyze_sentiment, summarize_text, create_event_detail_json).
- Integration test endpoints: /health, /mood/analyze, /journal/create.
- Validate timestamps in UTC with trailing Z and required JSON fields.

## Migration Steps
1) Refactor mood_agent prompt + model; ensure tools unchanged.
2) Refactor journal_agent prompt + create_event_detail_json to accept optional mood and include mood fields.
3) Wire sub_agents into buddy_agent; remove direct tools on buddy.
4) Implement new FastAPI endpoints and wire to Python tools.
5) Quick smoke tests and update README.
