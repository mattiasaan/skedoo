import 'package:flutter/material.dart';
import '../../../palette/palette.dart';
import 'schedule_card.dart';

class TodayScheduleSection extends StatelessWidget {
  const TodayScheduleSection({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text("TODAY'S SCHEDULE", style: TextStyle(color: Palette.text_tertiary, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
            Text("VIEW CALENDAR", style: TextStyle(color: Palette.primary, fontSize: 12, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 20),
        const ScheduleCard(
          time: "08:00 - 09:30",
          title: "English Literature",
          subtitle: "Room 104 • Dr. Bennett",
          status: "COMPLETED",
        ),
        const ScheduleCard(
          time: "10:30 - 11:45",
          title: "Mathematics",
          subtitle: "Room 302 • Prof. Schmidt",
          status: "ONGOING",
        ),
        const ScheduleCard(
          time: "13:00 - 14:30",
          title: "Modern History",
          subtitle: "Room 201 • Dr. Henderson",
          status: "UPCOMING",
          isLast: true,
        ),
      ],
    );
  }
}