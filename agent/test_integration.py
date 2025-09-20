#!/usr/bin/env python3
"""
Test script for Being Agent Integration
Tests the complete workflow: Flutter messages → Being agents → EventDetail creation
"""

import asyncio
import json
import requests
import time
from datetime import datetime

# Test configuration
FASTAPI_URL = "http://localhost:8000"
TEST_CONVERSATIONS = [
    {
        "conversation": "I had such a wonderful day today! I aced my exam and got to spend time with friends. Everything just felt perfect!",
        "expected_title": "Happy Day",
        "expected_emoji": "assets/images/goodmood.png"
    },
    {
        "conversation": "Today was really tough. I failed my presentation and felt so embarrassed. I just want to hide from everyone.",
        "expected_title": "Tough Day", 
        "expected_emoji": "assets/images/badmood.png"
    },
    {
        "conversation": "I spent most of the day studying for my upcoming exams. Had to review a lot of material but made good progress.",
        "expected_title": "Study Day",
        "expected_emoji": "assets/images/moderatemode.png"
    },
    {
        "conversation": "Work was incredibly busy today. Back-to-back meetings and deadlines. Barely had time for lunch.",
        "expected_title": "Work Day",
        "expected_emoji": "assets/images/moderatemode.png"
    }
]

def test_health_check():
    """Test if the FastAPI server is running"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_conversation_analysis(conversation_data):
    """Test conversation analysis endpoint"""
    print(f"\n🔍 Testing conversation: '{conversation_data['conversation'][:50]}...'")
    
    payload = {
        "conversation": conversation_data["conversation"],
        "user_id": f"test_user_{int(time.time())}"
    }
    
    try:
        response = requests.post(
            f"{FASTAPI_URL}/analyze_conversation",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Analysis successful!")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Description: {data.get('description', 'N/A')[:100]}...")
            print(f"   Emoji: {data.get('emoji_path', 'N/A')}")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            
            # Validate expected results
            title_match = data.get('title') == conversation_data['expected_title']
            emoji_match = data.get('emoji_path') == conversation_data['expected_emoji']
            
            if title_match and emoji_match:
                print("✅ Expected results match!")
            else:
                print(f"⚠️  Results differ from expected:")
                print(f"   Expected title: {conversation_data['expected_title']}, got: {data.get('title')}")
                print(f"   Expected emoji: {conversation_data['expected_emoji']}, got: {data.get('emoji_path')}")
            
            return True
        else:
            print(f"❌ Analysis failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

def test_flutter_compatibility():
    """Test that the response format is compatible with Flutter EventDetail model"""
    print("\n🔍 Testing Flutter EventDetail compatibility...")
    
    test_payload = {
        "conversation": "This is a test to verify EventDetail structure compatibility.",
        "user_id": "flutter_compatibility_test"
    }
    
    try:
        response = requests.post(
            f"{FASTAPI_URL}/analyze_conversation",
            headers={"Content-Type": "application/json"},
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required EventDetail fields
            required_fields = ['title', 'description', 'emoji_path', 'timestamp']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("✅ All required EventDetail fields present!")
                
                # Validate field types and formats
                validations = [
                    (isinstance(data['title'], str) and len(data['title']) > 0, "Title is non-empty string"),
                    (isinstance(data['description'], str) and len(data['description']) > 0, "Description is non-empty string"),
                    (data['emoji_path'].startswith('assets/images/') and data['emoji_path'].endswith('.png'), "Emoji path has correct format"),
                    (data['timestamp'], "Timestamp is present")
                ]
                
                for is_valid, description in validations:
                    if is_valid:
                        print(f"   ✅ {description}")
                    else:
                        print(f"   ❌ {description}")
                
                return True
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
        else:
            print(f"❌ Compatibility test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Compatibility test error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🤖 Being Agent Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ FastAPI server is not running. Please start it with:")
        print("   python fastapi_server.py")
        print("   Or use the startup script: start_agent.bat (Windows) or start_agent.sh (Linux/Mac)")
        return
    
    # Test 2: Flutter compatibility
    if not test_flutter_compatibility():
        print("\n❌ Flutter compatibility test failed")
        return
    
    # Test 3: Conversation analysis
    print(f"\n🔍 Testing {len(TEST_CONVERSATIONS)} conversation scenarios...")
    successful_tests = 0
    
    for i, conversation_data in enumerate(TEST_CONVERSATIONS, 1):
        print(f"\n--- Test {i}/{len(TEST_CONVERSATIONS)} ---")
        if test_conversation_analysis(conversation_data):
            successful_tests += 1
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {successful_tests}/{len(TEST_CONVERSATIONS)} conversation tests passed")
    
    if successful_tests == len(TEST_CONVERSATIONS):
        print("🎉 All tests passed! Integration is working correctly.")
        print("\n📱 Ready for Flutter integration:")
        print("   1. Ensure Flutter app has http dependency")
        print("   2. Import BeingAgentService in your Dart code")
        print("   3. Replace Google Gemini calls with BeingAgentService.analyzeMessages()")
    else:
        print("⚠️  Some tests failed. Check the agent configuration and try again.")

if __name__ == "__main__":
    main()