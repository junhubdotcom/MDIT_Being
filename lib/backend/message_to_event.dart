
import 'package:flutter/material.dart';
import 'package:hackathon_x_project/backend/message.dart';
import 'package:hackathon_x_project/backend/message_provider.dart';
import 'package:hackathon_x_project/backend/event_model.dart';
import 'package:hackathon_x_project/backend/being_agent_service.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';

bool isNotAnalyzing = true;

Future<void> analyzeMessagesAndCreateEvent(BuildContext context) async {
  final messages = Provider.of<MessageProvider>(context, listen: false).getAllMessages();

  if (messages.isNotEmpty && isNotAnalyzing) {
    isNotAnalyzing = false;
    
    try {
      // Use Being agent service instead of Google Gemini
      final newEvent = await BeingAgentService.createEventFromMessages(messages);
      
      if (newEvent != null) {
        // Add the new EventDetail to the sharedEvents list
        sharedEvents.add(newEvent);
        
        // Clear the messages list in the MessageProvider
        Provider.of<MessageProvider>(context, listen: false).clearMessages();
        
        print("analyzeMessagesAndCreateEvent completed successfully at ${DateTime.now()}");
      } else {
        print("Failed to create event from messages");
      }
    } catch (e) {
      print("Error in analyzeMessagesAndCreateEvent: $e");
    } finally {
      isNotAnalyzing = true;
    }
  } else {
    print("No messages to analyze or already analyzing.");
  }
}

// Legacy function replaced by BeingAgentService.analyzeMessages()
// This function is kept for reference but no longer used
/*
Future<Map<String, String?>> callGoogleGemini(List<Message> messages) async {
  // This function has been replaced by BeingAgentService.analyzeMessages()
  // to use local Being agents instead of Google Gemini API
  return {
    'title': 'Legacy Function',
    'description': 'Please use BeingAgentService instead',
    'mood': 'assets/images/moderatemode.png',
  };
}
*/