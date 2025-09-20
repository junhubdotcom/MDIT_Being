from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
import datetime
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from agent import root_agent

app = Flask(__name__)
CORS(app)

# Initialize ADK runner
APP_NAME = "being_app"
session_service = InMemorySessionService()

async def get_runner():
    return Runner(
        app_name=APP_NAME,
        session_service=session_service,
        agents=[root_agent]
    )

# Global runner instance
runner = None

def initialize_runner():
    global runner
    if runner is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        runner = loop.run_until_complete(get_runner())
    return runner

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Flutter service testing"""
    return jsonify({
        "status": "healthy",
        "service": "Being Agent Service",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

@app.route('/analyze_conversation', methods=['POST'])
def analyze_conversation():
    """
    Analyze conversation and return EventDetail-compatible JSON
    This endpoint replaces Google Gemini API calls
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        conversation = data.get('conversation', '')
        user_id = data.get('user_id', 'default_user')
        
        if not conversation:
            return jsonify({"error": "No conversation text provided"}), 400
        
        # Use the agent to analyze the conversation
        session_id = f"session_{user_id}_{datetime.datetime.utcnow().timestamp()}"
        
        # Create analysis prompt for the agent
        analysis_prompt = f"""
        Please analyze this conversation for a diary entry:
        
        Conversation: {conversation}
        
        I need you to create a complete EventDetail structure. Please:
        1. Use create_event_detail_json(conversation, user_id) to generate the diary structure
        2. Use get_emoji_for_sentiment(conversation) to determine the appropriate emoji
        3. Provide a complete analysis with title, description, and emoji path
        
        Conversation text: {conversation}
        User ID: {user_id}
        """
        
        # Execute the analysis asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_analysis():
            # Initialize runner if needed
            initialize_runner()
            
            response = await runner.send_message(
                session_id=session_id,
                message=analysis_prompt
            )
            return response
        
        agent_response = loop.run_until_complete(run_analysis())
        
        # Parse the agent response and extract key information
        response_text = agent_response.text if hasattr(agent_response, 'text') else str(agent_response)
        
        # Create a simple title extraction (can be improved with more sophisticated parsing)
        title = extract_title_from_response(response_text, conversation)
        description = extract_description_from_response(response_text, conversation)
        emoji_path = determine_emoji_from_sentiment(conversation)
        
        return jsonify({
            "title": title,
            "description": description,
            "emoji_path": emoji_path,
            "agent_response": response_text,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in analyze_conversation: {str(e)}")
        return jsonify({
            "error": "Analysis failed",
            "message": str(e),
            "title": "Daily Reflection",
            "description": "Unable to analyze conversation at this time.",
            "emoji_path": "assets/images/moderatemode.png"
        }), 500

def extract_title_from_response(response_text: str, conversation: str) -> str:
    """Extract or generate a title from the agent response"""
    # Simple extraction logic - can be improved
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
        return f"I reflected on my day and shared my thoughts."

def determine_emoji_from_sentiment(conversation: str) -> str:
    """Determine emoji path based on conversation sentiment"""
    conversation_lower = conversation.lower()
    
    # Simple sentiment analysis
    positive_words = ['happy', 'joy', 'excited', 'great', 'awesome', 'wonderful', 'amazing', 'love', 'good']
    negative_words = ['sad', 'upset', 'angry', 'frustrated', 'terrible', 'awful', 'hate', 'bad', 'worried', 'anxious']
    
    positive_count = sum(1 for word in positive_words if word in conversation_lower)
    negative_count = sum(1 for word in negative_words if word in conversation_lower)
    
    if positive_count > negative_count and positive_count > 0:
        return "assets/images/goodmood.png"
    elif negative_count > positive_count and negative_count > 0:
        return "assets/images/badmood.png"
    else:
        return "assets/images/moderatemode.png"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)