import 'package:flutter/material.dart';
import '../../../palette/palette.dart';
// Assicurati che questi percorsi siano corretti nel tuo progetto
import '../dashboard_content.dart'; 
import '../../calendar/calendar_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _selectedIndex = 0;

  // Lista delle schermate
  final List<Widget> _pages = [
    const DashboardContent(), 
    const CalendarScreen(),
    const Center(child: Text("Tasks", style: TextStyle(color: Colors.white))),
    const Center(child: Text("Community", style: TextStyle(color: Colors.white))),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      // Usiamo un IndexedStack per mantenere lo stato delle pagine quando cambi tab
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Azione per aggiungere un nuovo task/evento
        },
        backgroundColor: Palette.primary,
        shape: const CircleBorder(),
        child: const Icon(Icons.add, color: Colors.white, size: 30),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      
      bottomNavigationBar: CustomBottomAppBar(
        selectedIndex: _selectedIndex,
        onTap: _onItemTapped,
      ),
    );
  }
}

// ✅ Devi definire la classe CustomBottomAppBar qui sotto o importarla
class CustomBottomAppBar extends StatelessWidget {
  final int selectedIndex;
  final Function(int) onTap;

  const CustomBottomAppBar({
    super.key,
    required this.selectedIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return BottomAppBar(
      color: Palette.background_secondary,
      shape: const CircularNotchedRectangle(),
      notchMargin: 8,
      child: SizedBox(
        height: 60,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _navItem(Icons.home_outlined, "HOME", 0),
            _navItem(Icons.calendar_month_outlined, "CALENDAR", 1),
            const SizedBox(width: 40), // Spazio vitale per il tasto +
            _navItem(Icons.groups_outlined, "COMMUNITY", 2),
            _navItem(Icons.person_outline, "PROFILE", 3),
          ],
        ),
      ),
    );
  }

  Widget _navItem(IconData icon, String label, int index) {
    bool isActive = selectedIndex == index;
    return GestureDetector(
      onTap: () => onTap(index),
      behavior: HitTestBehavior.opaque, // Rende cliccabile tutta l'area
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: isActive ? Palette.primary : Palette.text_tertiary,
          ),
          Text(
            label,
            style: TextStyle(
              color: isActive ? Palette.primary : Palette.text_tertiary,
              fontSize: 10,
              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}