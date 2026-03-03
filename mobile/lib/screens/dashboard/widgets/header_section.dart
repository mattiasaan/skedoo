import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../palette/palette.dart';

class HeaderSection extends StatelessWidget {
  const HeaderSection({super.key});

  @override
  Widget build(BuildContext context) {

    String formattedDate = DateFormat('EEEE, MMM d').format(DateTime.now());

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
            children: [
              const Text("Hi, Alex!", 
                style: TextStyle(color: Palette.text_primary, fontSize: 22, fontWeight: FontWeight.bold)),
              Text(formattedDate, 
                style: const TextStyle(color: Palette.text_secondary, fontSize: 14)),
            ],
          ),
        ),
        IconButton(
          icon: const Badge(
            label: Text(''),
            child: Icon(Icons.notifications_none, color: Palette.text_primary, size: 28),
          ),
          onPressed: () => Navigator.push(
            context, 
            MaterialPageRoute(builder: (context) => const NotificationScreen())
          ),
        )
      ],
    );
  }
}