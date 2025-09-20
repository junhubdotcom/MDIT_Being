import 'package:flutter/material.dart';
import 'package:hackathon_x_project/backend/being_agent_service.dart';
import 'package:hackathon_x_project/backend/message.dart';
import 'package:hackathon_x_project/backend/event_model.dart';

/// Test widget to verify Being Agent integration
/// Add this to your app to test the agent service
class AgentTestScreen extends StatefulWidget {
  const AgentTestScreen({super.key});

  @override
  State<AgentTestScreen> createState() => _AgentTestScreenState();
}

class _AgentTestScreenState extends State<AgentTestScreen> {
  bool _isLoading = false;
  String _status = 'Ready to test';
  EventDetail? _lastEvent;
  String? _agentResponse; // Add agent response field
  final TextEditingController _messageController = TextEditingController();

  // Test scenarios
  final List<Map<String, String>> _testScenarios = [
    {
      'name': 'Happy Day Test',
      'message': 'I had such a wonderful day today! I aced my exam and got to spend time with friends. Everything just felt perfect!',
      'expectedEmoji': 'assets/images/goodmood.png'
    },
    {
      'name': 'Tough Day Test', 
      'message': 'Today was really tough. I failed my presentation and felt so embarrassed. I just want to hide from everyone.',
      'expectedEmoji': 'assets/images/badmood.png'
    },
    {
      'name': 'Study Day Test',
      'message': 'I spent most of the day studying for my upcoming exams. Had to review a lot of material but made good progress.',
      'expectedEmoji': 'assets/images/moderatemode.png'
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Being Agent Test'),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Status Card
            Card(
              color: _getStatusColor(),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Text(
                      'Agent Service Status',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _status,
                      style: const TextStyle(color: Colors.white),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Service Test Button
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _testServiceConnection,
              icon: _isLoading 
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.health_and_safety),
              label: const Text('Test Service Connection'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Quick Test Scenarios
            const Text(
              'Quick Test Scenarios:',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            
            SizedBox(
              height: 200, // Fixed height for scenario list
              child: ListView.builder(
                itemCount: _testScenarios.length,
                itemBuilder: (context, index) {
                  final scenario = _testScenarios[index];
                  return Card(
                    child: ListTile(
                      title: Text(scenario['name']!),
                      subtitle: Text(
                        scenario['message']!,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: ElevatedButton(
                        onPressed: _isLoading ? null : () => _testScenario(scenario),
                        child: const Text('Test'),
                      ),
                    ),
                  );
                },
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Custom Message Test
            const Text(
              'Custom Message Test:',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            
            TextField(
              controller: _messageController,
              decoration: const InputDecoration(
                hintText: 'Enter your message to test...',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            
            const SizedBox(height: 8),
            
            ElevatedButton(
              onPressed: _isLoading ? null : _testCustomMessage,
              child: const Text('Test Custom Message'),
            ),
            
            const SizedBox(height: 16),
            
            // Last Result
            if (_lastEvent != null) ...[
              const Text(
                'Last Test Result:',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              
              // Agent Response Section
              if (_agentResponse != null && _agentResponse!.isNotEmpty) ...[
                Card(
                  color: Colors.blue[50],
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.smart_toy, color: Colors.blue),
                            SizedBox(width: 8),
                            Text('Agent Response:', 
                                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue[800])),
                          ],
                        ),
                        SizedBox(height: 8),
                        Text(_agentResponse!, style: TextStyle(fontSize: 14)),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 8),
              ],
              
              // EventDetail Section
              Container(
                height: 250, // Fixed height for diary entry
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.event_note, color: Colors.green),
                            SizedBox(width: 8),
                            Text('Generated Diary Entry:', 
                                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green[800])),
                          ],
                        ),
                        SizedBox(height: 8),
                        Text('Title: ${_lastEvent!.title}', style: const TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text('Time: ${_lastEvent!.time}'),
                        const SizedBox(height: 4),
                        Text('Emoji: ${_lastEvent!.emoji}'),
                        const SizedBox(height: 8),
                        Text('Description:', style: const TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Expanded(
                          child: SingleChildScrollView(
                            child: Text(_lastEvent!.description),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getStatusColor() {
    if (_status.contains('✅') || _status.contains('ready')) {
      return Colors.green;
    } else if (_status.contains('❌') || _status.contains('failed')) {
      return Colors.red;
    } else {
      return Colors.orange;
    }
  }

  Future<void> _testServiceConnection() async {
    setState(() {
      _isLoading = true;
      _status = 'Testing service connection...';
    });

    try {
      bool isConnected = await BeingAgentService.testConnection();
      setState(() {
        _status = isConnected 
          ? '✅ Agent service is running and ready!'
          : '❌ Agent service is not available. Please start the FastAPI server.';
      });
    } catch (e) {
      setState(() {
        _status = '❌ Connection test failed: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _testScenario(Map<String, String> scenario) async {
    setState(() {
      _isLoading = true;
      _status = 'Testing scenario: ${scenario['name']}...';
    });

    try {
      // Create a test message
      final message = Message(
        text: scenario['message']!,
        isUser: true,
        image: null,
      );

      // Get both the event and agent response
      final event = await BeingAgentService.createEventFromMessages([message]);
      final agentResponse = await BeingAgentService.getAgentResponse([message]);
      
      if (event != null) {
        setState(() {
          _lastEvent = event;
          _agentResponse = agentResponse;
          _status = '✅ Scenario test completed! Check result below.';
        });
        
        // Validate expected emoji
        if (event.emoji == scenario['expectedEmoji']) {
          _showSnackBar('✅ Emoji matches expected result!', Colors.green);
        } else {
          _showSnackBar('⚠️ Emoji differs from expected. Got: ${event.emoji}', Colors.orange);
        }
      } else {
        setState(() {
          _status = '❌ Failed to create event from scenario';
        });
      }
    } catch (e) {
      setState(() {
        _status = '❌ Scenario test failed: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _testCustomMessage() async {
    if (_messageController.text.trim().isEmpty) {
      _showSnackBar('Please enter a message to test', Colors.red);
      return;
    }

    setState(() {
      _isLoading = true;
      _status = 'Testing custom message...';
    });

    try {
      // Create a test message
      final message = Message(
        text: _messageController.text,
        isUser: true,
        image: null,
      );

      // Get both the event and agent response
      final event = await BeingAgentService.createEventFromMessages([message]);
      final agentResponse = await BeingAgentService.getAgentResponse([message]);
      
      if (event != null) {
        setState(() {
          _lastEvent = event;
          _agentResponse = agentResponse;
          _status = '✅ Custom message test completed!';
        });
        _messageController.clear();
      } else {
        setState(() {
          _status = '❌ Failed to create event from custom message';
        });
      }
    } catch (e) {
      setState(() {
        _status = '❌ Custom message test failed: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
        duration: const Duration(seconds: 3),
      ),
    );
  }
}