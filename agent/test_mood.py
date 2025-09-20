import requests
import json

def test_mood_analysis():
    base_url = 'http://localhost:8000'
    
    # Test different mood scenarios
    test_cases = [
        {
            'conversation': 'I am so happy and excited! Today was absolutely wonderful!',
            'expected_mood': 'positive',
            'expected_emoji': 'assets/images/goodmood.png'
        },
        {
            'conversation': 'I feel really sad and depressed today. Everything seems hopeless.',
            'expected_mood': 'negative', 
            'expected_emoji': 'assets/images/badmood.png'
        },
        {
            'conversation': 'Just finished studying for my exam. Feeling okay about it.',
            'expected_mood': 'neutral',
            'expected_emoji': 'assets/images/moderatemode.png'
        },
        {
            'conversation': 'I am stressed and anxious about my presentation tomorrow.',
            'expected_mood': 'negative',
            'expected_emoji': 'assets/images/badmood.png'
        },
        {
            'conversation': 'Had an amazing day at the beach with friends! So much fun!',
            'expected_mood': 'positive',
            'expected_emoji': 'assets/images/goodmood.png'
        }
    ]
    
    print('🎭 Testing Mood Analysis and Emoji Selection')
    print('=' * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f'\n--- Test {i}/5 ---')
        print(f'Input: {test_case["conversation"][:60]}...')
        
        try:
            # Test analyze_conversation endpoint
            response = requests.post(f'{base_url}/analyze_conversation', 
                                   json={
                                       'conversation': test_case['conversation'],
                                       'user_id': f'mood_test_{i}'
                                   }, 
                                   timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                emoji = result.get('emoji_path')
                title = result.get('title')
                
                print(f'✅ Analysis successful!')
                print(f'   Title: {title}')
                print(f'   Emoji: {emoji}')
                print(f'   Expected: {test_case["expected_emoji"]}')
                
                if emoji == test_case['expected_emoji']:
                    print(f'   ✅ Emoji matches expected!')
                else:
                    print(f'   ⚠️  Emoji differs from expected')
                    
                # Test chat response too
                chat_response = requests.post(f'{base_url}/chat', 
                                            json={
                                                'conversation': test_case['conversation'],
                                                'user_id': f'mood_test_{i}'
                                            }, 
                                            timeout=15)
                
                if chat_response.status_code == 200:
                    chat_result = chat_response.json()
                    print(f'   💬 Chat response: {chat_result["response"][:80]}...')
                    
            else:
                print(f'   ❌ Analysis failed: {response.status_code}')
                print(f'   Error: {response.text}')
                
        except Exception as e:
            print(f'   ❌ Request failed: {e}')
    
    print('\n' + '=' * 50)
    print('🎭 Mood analysis testing complete!')

if __name__ == "__main__":
    test_mood_analysis()