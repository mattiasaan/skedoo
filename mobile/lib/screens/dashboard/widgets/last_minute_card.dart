import 'package:flutter/material.dart';
import '../../../palette/palette.dart';

class LastMinuteCard extends StatelessWidget {
  const LastMinuteCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Palette.background_secondary.withOpacity(0.5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Palette.primary.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: Palette.primary),
          const SizedBox(width: 12),
          Expanded(
            child: RichText(
              text: const TextSpan(
                style: TextStyle(color: Palette.text_secondary, fontSize: 13),
                children: [
                  TextSpan(
                    text: "Last Minute Changes\n",
                    style: TextStyle(color: Palette.text_primary, fontWeight: FontWeight.bold),
                  ),
                  TextSpan(text: "Professor Rossi absent - Room 204 moved to 201 for today's Physics lab."),
                ],
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, color: Palette.text_tertiary, size: 18),
            onPressed: () {},
          )
        ],
      ),
    );
  }
}