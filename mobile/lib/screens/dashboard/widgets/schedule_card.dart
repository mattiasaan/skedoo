import 'package:flutter/material.dart';
import '../../../palette/palette.dart';

class ScheduleCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final String time;
  final bool highlighted;

  const ScheduleCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.time,
    this.highlighted = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Palette.background_secondary,
        borderRadius: BorderRadius.circular(18),
        border: highlighted
            ? Border.all(color: Palette.primary, width: 1.5)
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(time,
              style: const TextStyle(color: Palette.text_tertiary)),
          const SizedBox(height: 6),
          Text(title,
              style: const TextStyle(
                color: Palette.text_primary,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              )),
          const SizedBox(height: 4),
          Text(subtitle,
              style: const TextStyle(color: Palette.text_secondary)),
        ],
      ),
    );
  }
}