import 'package:flutter/material.dart';
import '../../../palette/palette.dart';

class LastMinuteCard extends StatelessWidget {
  const LastMinuteCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Palette.background_secondary,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: Palette.primary.withOpacity(0.3),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          Icon(Icons.info_outline, color: Palette.primary),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Last Minute Changes",
                  style: TextStyle(
                    color: Palette.text_primary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 6),
                Text(
                  "Professor Rossi absent - Room 204 moved to 201.",
                  style: TextStyle(
                    color: Palette.text_secondary,
                    fontSize: 13,
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