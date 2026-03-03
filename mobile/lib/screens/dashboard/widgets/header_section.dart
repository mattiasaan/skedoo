import 'package:flutter/material.dart';
import '../../../palette/palette.dart';

class HeaderSection extends StatelessWidget {
  const HeaderSection({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const CircleAvatar(
          radius: 24,
          backgroundImage: NetworkImage(
            "https://i.pravatar.cc/150?img=3",
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                "Hi, Alex!",
                style: TextStyle(
                  color: Palette.text_primary,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 4),
              Text(
                "Monday, Oct 24",
                style: TextStyle(
                  color: Palette.text_secondary,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
        Stack(
          children: const [
            Icon(Icons.notifications_none,
                color: Palette.text_primary),
            Positioned(
              right: 2,
              top: 2,
              child: CircleAvatar(
                radius: 4,
                backgroundColor: Colors.red,
              ),
            ),
          ],
        )
      ],
    );
  }
}