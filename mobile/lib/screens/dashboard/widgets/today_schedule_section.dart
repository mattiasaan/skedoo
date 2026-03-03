import 'package:flutter/material.dart';
import '../../../palette/palette.dart';
import 'schedule_card.dart';

class TodayScheduleSection extends StatelessWidget {
  const TodayScheduleSection({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        Text(
          "TODAY'S SCHEDULE",
          style: TextStyle(
            color: Palette.text_secondary,
            fontSize: 12,
            letterSpacing: 1.2,
          ),
        ),
        SizedBox(height: 16),
        ScheduleCard(
          title: "English Literature",
          subtitle: "Room 104 • Dr. Bennett",
          time: "08:00 - 09:30",
        ),
        SizedBox(height: 12),
        ScheduleCard(
          title: "Mathematics",
          subtitle: "Room 302 • Prof. Schmidt",
          time: "10:30 - 11:45",
          highlighted: true,
        ),
      ],
    );
  }
}