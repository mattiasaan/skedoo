import 'package:flutter/material.dart';
import '../../palette/palette.dart'; // Assicurati che il percorso sia corretto

class NotificationScreen extends StatelessWidget {
  const NotificationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Palette.text_primary, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "Notifications",
          style: TextStyle(
            color: Palette.text_primary,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        centerTitle: true,
      ),
      body: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        itemCount: 4, // Esempio di numero di notifiche
        itemBuilder: (context, index) {
          return _buildNotificationItem(index);
        },
      ),
    );
  }

  Widget _buildNotificationItem(int index) {
    // Dati fittizi per l'esempio
    final List<Map<String, String>> notifications = [
      {
        "title": "Room Change",
        "desc": "Physics Lab moved from Room 204 to 201.",
        "time": "Just now"
      },
      {
        "title": "New Assignment",
        "desc": "Dr. Bennett uploaded a new PDF for English Literature.",
        "time": "2h ago"
      },
      {
        "title": "Meeting Reminder",
        "desc": "Linear Algebra starts in 15 minutes.",
        "time": "3h ago"
      },
      {
        "title": "System Update",
        "desc": "The student portal will be down for maintenance tonight.",
        "time": "Yesterday"
      },
    ];

    final item = notifications[index % notifications.length];

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Palette.background_secondary,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Palette.background_tertiary,
          width: 1,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Palette.primary.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.notifications_active_outlined,
              color: Palette.primary,
              size: 20,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      item["title"]!,
                      style: const TextStyle(
                        color: Palette.text_primary,
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                    Text(
                      item["time"]!,
                      style: const TextStyle(
                        color: Palette.text_tertiary,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  item["desc"]!,
                  style: const TextStyle(
                    color: Palette.text_secondary,
                    fontSize: 13,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}