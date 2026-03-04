import 'package:flutter/material.dart';
import '../../../palette/palette.dart';

class ScheduleCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final String time;
  final String status;
  final bool isLast;

  const ScheduleCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.time,
    this.status = "UPCOMING",
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    bool isOngoing = status == "ONGOING";
    
    return IntrinsicHeight(
      child: Row(
        children: [
          Column(
            children: [
              Container(
                width: 14, height: 14,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isOngoing ? Palette.primary : Colors.transparent,
                  border: Border.all(
                    color: isOngoing ? Palette.primary : Palette.background_tertiary, 
                    width: 2
                  ),
                ),
              ),
              if (!isLast)
                Expanded(
                  child: Container(width: 2, color: Palette.background_tertiary),
                ),
            ],
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Container(
              margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Palette.background_secondary,
                borderRadius: BorderRadius.circular(16),
                border: isOngoing ? Border.all(color: Palette.primary, width: 1.5) : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(time, style: const TextStyle(color: Palette.text_tertiary, fontSize: 13)),
                      if (status != "UPCOMING")
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: isOngoing ? Palette.primary.withOpacity(0.1) : Colors.black26,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            status,
                            style: TextStyle(
                              color: isOngoing ? Palette.primary : Palette.text_tertiary,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(title, style: const TextStyle(color: Palette.text_primary, fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(subtitle, style: const TextStyle(color: Palette.text_secondary, fontSize: 13)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}