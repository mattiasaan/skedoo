import 'package:flutter/material.dart';
import '../../../palette/palette.dart';

class BottomNav extends StatelessWidget {
  const BottomNav({super.key});

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      backgroundColor: Palette.background_secondary,
      selectedItemColor: Palette.primary,
      unselectedItemColor: Palette.text_tertiary,
      type: BottomNavigationBarType.fixed,
      items: const [
        BottomNavigationBarItem(
          icon: Icon(Icons.home_outlined),
          label: "Home",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.calendar_today_outlined),
          label: "Schedule",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.groups_outlined),
          label: "Community",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline),
          label: "Profile",
        ),
      ],
    );
  }
}