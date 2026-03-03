import 'package:flutter/material.dart';
import '../../../palette/palette.dart';

class UpNextCard extends StatelessWidget {
  const UpNextCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "UP NEXT",
          style: TextStyle(
            color: Palette.text_secondary,
            fontSize: 12,
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Palette.primary,
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Linear Algebra",
                style: TextStyle(
                  color: Palette.text_primary,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                "10:30 AM - 11:45 AM",
                style: TextStyle(color: Palette.text_primary),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                height: 45,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Palette.text_primary,
                    foregroundColor: Palette.primary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  onPressed: () {},
                  child: const Text("Join Online Meeting"),
                ),
              )
            ],
          ),
        ),
      ],
    );
  }
}