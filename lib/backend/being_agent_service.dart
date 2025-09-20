import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:hackathon_x_project/backend/message.dart';
import 'package:hackathon_x_project/backend/event_model.dart';
import 'package:intl/intl.dart';
import 'package:image_picker/image_picker.dart';

/// Service to communicate with the local Being agent system
/// Replaces Google Gemini API calls with local agent integration
class BeingAgentService {
  // For Android emulator, use 10.0.2.2 instead of localhost
  // For iOS simulator or physical device, use your computer's IP address
  static const String _baseUrl = 'http://10.0.2.2:8000'; // FastAPI server URL for Android emulator
  static const Duration _timeout = Duration(seconds: 30);

  /// Analyze messages and create EventDetail using Being agents
  /// This replaces the callGoogleGemini function
  /// Returns both analysis and agent response
  static Future<Map<String, String?>> analyzeMessages(List<Message> messages) async {
    try {
      // Convert messages to string format for analysis
      final String userInput = Message.convertMessagesToString(messages);
      
      // Call the Being agent for analysis
      final response = await http.post(
        Uri.parse('$_baseUrl/analyze_conversation'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'conversation': userInput,
          'user_id': 'flutter_user_${DateTime.now().millisecondsSinceEpoch}',
        }),
      ).timeout(_timeout);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        
        // Extract the analysis results - map FastAPI response to Flutter format
        return {
          'title': data['title'] as String?,
          'description': data['description'] as String?,
          'mood': data['emoji_path'] as String?,
          'agent_response': data['agent_response'] as String?, // Add agent response for debugging
        };
      } else {
        print('Being Agent Service Error: ${response.statusCode} - ${response.body}');
        return _getDefaultResponse();
      }
    } catch (e) {
      print('Being Agent Service Exception: $e');
      return _getDefaultResponse();
    }
  }

  /// Get conversational response from Being agent
  /// This provides the agent's reply to the user's message
  static Future<String?> getAgentResponse(List<Message> messages) async {
    try {
      // Convert messages to string format for analysis
      final String userInput = Message.convertMessagesToString(messages);
      
      // Call the Being agent for conversational response
      final response = await http.post(
        Uri.parse('$_baseUrl/chat'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'conversation': userInput,
          'user_id': 'flutter_user_${DateTime.now().millisecondsSinceEpoch}',
        }),
      ).timeout(_timeout);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        return data['response'] as String?;
      } else {
        print('Being Agent Service Error: ${response.statusCode} - ${response.body}');
        return 'I\'m here to help with your emotional tracking. Please try again.';
      }
    } catch (e) {
      print('Being Agent Service Exception: $e');
      return 'I\'m having trouble connecting right now. Please try again later.';
    }
  }

  /// Create EventDetail from messages using Being agent analysis
  /// This is a complete replacement for analyzeMessagesAndCreateEvent
  static Future<EventDetail?> createEventFromMessages(List<Message> messages) async {
    if (messages.isEmpty) {
      return null;
    }

    try {
      // Get analysis from Being agents
      final analysisResult = await analyzeMessages(messages);
      
      // Find the last image in the messages
      XFile? lastImage;
      for (var message in messages) {
        if (message.image != null) {
          lastImage = message.image;
        }
      }

      // Create time string
      DateTime now = DateTime.now();
      String time = DateFormat.jm().format(now);

      // Create EventDetail with agent analysis
      return EventDetail(
        date: now,
        title: analysisResult['title'] ?? 'Daily Reflection',
        time: time,
        description: analysisResult['description'] ?? 'Conversation summary not available',
        emoji: analysisResult['mood'] ?? 'assets/images/moderatemode.png',
        imageFile: lastImage,
      );
    } catch (e) {
      print('Error creating event from messages: $e');
      return null;
    }
  }

  /// Test connection to Being agent service
  static Future<bool> testConnection() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/health'),
      ).timeout(_timeout);
      
      return response.statusCode == 200;
    } catch (e) {
      print('Being Agent Service health check failed: $e');
      return false;
    }
  }

  /// Get default response when agent service is unavailable
  static Map<String, String?> _getDefaultResponse() {
    return {
      'title': 'Daily Reflection',
      'description': 'Unable to analyze conversation at this time. Please try again later.',
      'mood': 'assets/images/moderatemode.png',
    };
  }

  /// Initialize the Being agent service
  /// Call this when the app starts to ensure the service is ready
  static Future<bool> initialize() async {
    print('Initializing Being Agent Service...');
    
    // Test if the service is available
    bool isAvailable = await testConnection();
    
    if (isAvailable) {
      print('Being Agent Service is ready');
    } else {
      print('Being Agent Service is not available. Please ensure the agent server is running.');
    }
    
    return isAvailable;
  }
}