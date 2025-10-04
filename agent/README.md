# Being Buddy Agent 🧠💙

An empathetic AI companion built with Google's Agent Development Kit (ADK) that provides emotional support, conversation tracking, and mood analysis. Now integrated with Flutter app via Flask API.

## 🏗️ Project Structure

```
agent/
├── __init__.py                 # Main agent package exports
├── agent.py                    # Root agent definition (Being Buddy)
├── flask_server.py             # Flask API server for Flutter integration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
├── subagent/                   # Sub-agent implementations
│   ├── __init__.py            # Sub-agent exports
│   ├── journal_agent.py       # Conversation journaling & EventDetail JSON
│   └── mood_agent.py          # Sentiment analysis & emoji selection
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd agent
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env
# Add your GOOGLE_API_KEY for Gemini
```

<!-- Ollama setup removed as the project now uses Google AI Studio exclusively. -->

### 4. Start FastAPI Server
Run from the project root so Python treats `agent` as a package (prevents relative import errors):
```bash
# From the project root (folder that contains the `agent/` directory)
python -m agent.fastapi_server
# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### 5. Test Integration
```bash
curl -X POST http://localhost:8000/analyze_conversation \
  -H "Content-Type: application/json" \
  -d '{"conversation": "I had a great day today!", "user_id": "test_user"}'
```

## 📱 Flutter Integration

The FastAPI server provides these endpoints for the Flutter app:

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `POST /analyze_conversation` - Analyze chat and return EventDetail JSON
- `GET /test/{user_id}` - Test agent functionality

### EventDetail Response Format
```json
{
  "title": "Happy Day",
  "description": "I had a wonderful day reflecting on positive experiences...",
  "emoji_path": "assets/images/goodmood.png",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## 🤖 Agent Architecture

### Root Agent: Being Buddy
- **Name**: `being_buddy_agent`
- **Model**: `gemini-2.0-flash`
- **Role**: Empathetic conversational companion and task orchestrator
- **Capabilities**: 
  - Provides emotional support and validation
  - Decides when to delegate tasks to specialized sub-agents
  - Never provides medical advice or diagnosis

### Sub-Agents

#### 1. Journal Agent (`journal_agent`)
- **Model**: `gemini-2.0-flash`
- **Purpose**: Conversation summarization and diary management
- **Tools**:
  - `summarize_text()`: Creates 1-2 sentence summaries of conversations
  - `save_diary()`: Persists diary entries with timestamps and unique IDs
- **Storage**: In-memory dictionary (MVP - can be replaced with database)

#### 2. Mode Agent (`mode_agent`) 
- **Model**: `gemini-2.0-flash`
- **Purpose**: Sentiment analysis and mood timeline tracking
- **Tools**:
  - `analyze_sentiment()`: Analyzes emotional content and assigns scores (-1 to 1)
  - `append_mood_point()`: Records mood data points over time
- **Features**: 
  - Detects crisis indicators (suicide risk words)
  - Tracks emotional patterns over time
  - Returns structured sentiment analysis

## 📋 Requirements

### System Requirements
- Python 3.9+
- Google ADK (Agent Development Kit)
- **Option 1**: Google AI Studio API key (paid) OR
<!-- Ollama option removed: Project standardized on Google AI Studio. -->

<!-- Ollama setup removed. -->

### Google AI Studio Setup (Paid Option)

### Virtual Environment Setup (Recommended)

1. **Create a virtual environment**:
```bash
# Navigate to the Being project directory
cd "path/to/Being"

# Create virtual environment
python -m venv .venv
```

2. **Activate the virtual environment**:

**Windows (PowerShell)**:
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**:
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux**:
```bash
source .venv/bin/activate
```

3. **Verify activation**: Your terminal prompt should show `(.venv)` at the beginning

### Dependencies
```bash
# Install ADK and related packages (ensure virtual environment is activated)
pip install -r agent/requirements.txt
```

### Environment Setup

<!-- Ollama environment variables removed. -->

**For Google AI Studio (Paid)**:
1. Create a `.env` file in the agent directory with your API credentials:
```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_google_api_key_here
```

2. Get an API key from [Google AI Studio](https://aistudio.google.com/apikey)
3. Ensure agent models in `agent.py` and subagent files use `"gemini-2.0-flash"`

## 🚀 How to Start

### Prerequisites
Make sure your virtual environment is activated before running any commands:
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt  
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

### Method 1: Terminal Interface
```bash
# Navigate to the Being project directory
cd "path/to/Being"

# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Run the FastAPI service (module execution)
python -m agent.fastapi_server
```

<!-- ADK web UI removed for simplicity. The service is exposed via FastAPI. -->

## 🎯 Capabilities & Triggers

### 1. **Emotional Support & Conversation**
**What it does**: Provides empathetic responses, validation, and reflection
**How to trigger**: Simply start chatting naturally
```
Example:
User: "I've been feeling really overwhelmed lately..."
Buddy: "That sounds really challenging. It takes courage to share when you're feeling overwhelmed..."
```

### 2. **Journal & Conversation Logging**
**What it does**: Summarizes and saves conversation sessions as diary entries
**How to trigger**: Use keywords like:
- "save this conversation"
- "journal this session" 
- "log our chat"
- "record this"

```
Example:
User: "Please save our conversation from today"
Buddy: [Delegates to journal_agent] → Creates summary and saves with timestamp
```

### 3. **Mood Analysis & Tracking**
**What it does**: Analyzes emotional content and tracks mood patterns over time
**How to trigger**: Express emotional content naturally
**Auto-triggered by keywords**:
- Negative: "sad", "depressed", "anxious", "stressed"
- Positive: "happy", "joy", "glad", "relieved"
- Crisis: "suicidal", "kill myself", "can't go on"

```
Example:
User: "I'm feeling really anxious about tomorrow's presentation"
Buddy: [Delegates to mode_agent] → Analyzes sentiment, records mood point
```

### 4. **Crisis Detection & Support**
**What it does**: Detects potential self-harm indicators and provides supportive resources
**How to trigger**: Expressions of self-harm or suicidal ideation
**Response**: Provides empathetic support + professional resource recommendations

## 🔧 Advanced Usage

### Testing Individual Components
```bash
# Test agent loading
python -c "from agent import root_agent; print('✓ Agent loaded:', root_agent.name)"

# Test sub-agent configuration  
python -c "from agent import root_agent; print('Sub-agents:', [a.name for a in root_agent.sub_agents])"
```

### Customization Options

#### Modify Emotional Keywords
Edit `subagent/mode_agent.py` to adjust sentiment detection:
```python
# In analyze_sentiment() function
if any(w in t for w in ["your", "custom", "sad", "keywords"]):
    score = -0.6
```

#### Change Summary Length
Edit `subagent/journal_agent.py`:
```python
# In summarize_text() function  
summary = s if len(s) <= 240 else s[:237] + "..."  # Adjust character limit
```

#### Model selection
The project uses Google AI Studio with `model="gemini-2.0-flash"` across the root agent and sub-agents.

#### Update System Prompts
Modify the `instruction` field in `agent.py` to change Being Buddy's behavior.

## 🔒 Privacy & Security

- **Local Processing**: All conversations stored locally in memory
- **No External Logging**: Conversations not sent to external services (except LLM API)
- **API Security**: Uses Google's secure API endpoints
- **Data Retention**: In-memory storage cleared on restart (MVP design)

## 🛠️ Troubleshooting

### Common Issues

<!-- Ollama troubleshooting removed. -->

2. **Virtual Environment Issues**: 
   - Make sure virtual environment is activated (prompt should show `(.venv)`)
   - If packages not found, reinstall with `pip install google-adk`
   - To deactivate virtual environment: `deactivate`

3. **Import Errors**: Ensure you run the server as a module from the project root:
  - Correct: `python -m agent.fastapi_server` (run from the folder that contains `agent/`)
  - Incorrect: `python agent/fastapi_server.py` (may cause "attempted relative import" errors)

4. **API Key Issues**: Verify your `.env` file is configured correctly (only needed for Google AI Studio)

5. **Agent Not Found**: Make sure you're running `adk run agent` from the Being project root

### Debug Commands
```bash
# Check if agent loads correctly
python -c "from agent import root_agent; print('Success!')"

<!-- Ollama debug commands removed. -->

# View agent configuration
adk web --debug
```

## 🔮 Future Enhancements

- [ ] Persistent database storage (SQLite/PostgreSQL)
- [ ] Advanced NLP sentiment analysis
- [ ] Mood visualization dashboards  
- [ ] Integration with external therapy resources
- [ ] Multi-user support with privacy separation
- [ ] Voice conversation support
- [ ] Mobile app integration

## 📞 Support

For issues with:
- **ADK Framework**: [Google ADK Documentation](https://google.github.io/adk-docs/)
- **Being Agent**: Check the logs in `C:\Users\[user]\AppData\Local\Temp\agents_log\`
- **API Issues**: [Google AI Studio Support](https://aistudio.google.com/)

---

**⚠️ Important**: Being Buddy is designed for emotional support and companionship. It is not a replacement for professional mental health care. If you're experiencing serious mental health concerns, please contact a qualified healthcare provider or crisis hotline.