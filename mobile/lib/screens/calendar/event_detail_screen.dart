import 'package:flutter/material.dart';
import '../../palette/palette.dart';
import '../../models/event_model.dart';

class EventDetailScreen extends StatelessWidget {
  final Event event;
  const EventDetailScreen({super.key, required this.event});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.red),
            onPressed: () {
              dummyEvents.removeWhere((e) => e.id == event.id);
              Navigator.pop(context);
            },
          ),
        ],
      ),
      body: Center(
        child: Column(
          children: [
            Icon(event.icon, size: 100, color: event.color),
            const SizedBox(height: 20),
            Text(event.title, style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
            Text(event.time, style: const TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}