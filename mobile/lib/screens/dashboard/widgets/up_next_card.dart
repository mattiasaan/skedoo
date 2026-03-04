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
          style: TextStyle(color: Palette.text_tertiary, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            gradient: const LinearGradient(
              colors: [Palette.primary, Color(0xFF082D1B)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("MATHEMATICS • CALCULUS II", style: TextStyle(color: Palette.text_secondary, fontSize: 11, fontWeight: FontWeight.w600)),
                        SizedBox(height: 4),
                        Text("Linear Algebra", style: TextStyle(color: Palette.text_primary, fontSize: 28, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
                    child: const Column(
                      children: [
                        Text("ROOM", style: TextStyle(color: Palette.text_primary, fontSize: 10)),
                        Text("302", style: TextStyle(color: Palette.text_primary, fontSize: 18, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  )
                ],
              ),
              const SizedBox(height: 20),
              const Row(
                children: [
                  Icon(Icons.access_time, color: Palette.text_secondary, size: 18),
                  SizedBox(width: 8),
                  Text("10:30 AM - 11:45 AM", style: TextStyle(color: Palette.text_primary)),
                  SizedBox(width: 20),
                  Icon(Icons.location_on_outlined, color: Palette.text_secondary, size: 18),
                  SizedBox(width: 8),
                  Text("Forest Green", style: TextStyle(color: Palette.text_primary)),
                ],
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Palette.text_primary,
                  foregroundColor: Palette.primary,
                  minimumSize: const Size(double.infinity, 52),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () {},
                child: const Text("Join Online Meeting", style: TextStyle(fontWeight: FontWeight.bold)),
              )
            ],
          ),
        ),
      ],
    );
  }
}