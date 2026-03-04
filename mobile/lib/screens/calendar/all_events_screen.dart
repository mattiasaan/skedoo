import 'package:flutter/material.dart';
import '../../palette/palette.dart';
import '../../models/event_model.dart';
import 'event_detail_screen.dart';

class AllEventsScreen extends StatelessWidget {
  const AllEventsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      appBar: AppBar(title: const Text("All Events"), backgroundColor: Colors.transparent),
      body: ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: dummyEvents.length,
        itemBuilder: (context, index) {
          final event = dummyEvents[index];
          return ListTile(
            title: Text(event.title, style: const TextStyle(color: Colors.white)),
            subtitle: Text(event.time, style: const TextStyle(color: Colors.grey)),
            trailing: const Icon(Icons.chevron_right, color: Colors.grey),
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => EventDetailScreen(event: event))),
          );
        },
      ),
    );
  }
}