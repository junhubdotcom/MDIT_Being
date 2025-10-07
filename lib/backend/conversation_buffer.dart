class UserChat {
  final String text;
  final DateTime time;

  UserChat({required this.text, required this.time});
}

class ConversationBuffer {
  final List<UserChat> _messages = [];

  void addUser(String text) {
    if (text.trim().isEmpty) return;
    _messages.add(UserChat(text: text.trim(), time: DateTime.now()));
  }

  void clear() => _messages.clear();

  // Build a transcript string for /journal/create using only user messages.
  String toJournalText({
    int maxMessages = 50,
    int maxChars = 8000,
  }) {
    final tail = _messages.length > maxMessages
        ? _messages.sublist(_messages.length - maxMessages)
        : List<UserChat>.from(_messages);

    final lines = <String>[];
    for (final m in tail) {
      final t = m.time.toIso8601String();
      lines.add('[USER | $t] ${m.text}');
    }

    var transcript = lines.join('\n');
    if (transcript.length > maxChars) {
      transcript = transcript.substring(transcript.length - maxChars);
    }
    return transcript.trim();
  }

  bool get isEmpty => _messages.isEmpty;
  int get length => _messages.length;
}
