import 'package:flutter/material.dart';
import '../../palette/palette.dart';
import 'dashboard_content.dart'; 
import '../calendar/calendar_screen.dart';

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
    const Center(child: Text("Community", style: TextStyle(color: Colors.white))),
    const Center(child: Text("Profile", style: TextStyle(color: Colors.white))),
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
      // Usiamo IndexedStack per non perdere lo stato delle pagine (scroll, etc)
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      
      // ✅ Pulsante "+" centrale
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Azione per aggiungere
        },
        backgroundColor: Palette.primary,
        shape: const CircleBorder(),
        child: const Icon(Icons.add, color: Colors.white, size: 30),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      
      // ✅ La barra personalizzata definita sotto
      bottomNavigationBar: CustomBottomAppBar(
        selectedIndex: _selectedIndex,
        onTap: _onItemTapped,
      ),
    );
  }
}

// --- CLASSE DELLA BARRA (Assicurati che sia fuori dalla classe precedente) ---

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
      shape: const CircularNotchedRectangle(), // Crea l'incavo per il tasto +
      notchMargin: 8,
      child: SizedBox(
        height: 60,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildNavItem(Icons.home_outlined, "HOME", 0),
            _buildNavItem(Icons.calendar_month_outlined, "SCHEDULE", 1),
            const SizedBox(width: 40), // Spazio vuoto per il FAB
            _buildNavItem(Icons.groups_outlined, "COMMUNITY", 2),
            _buildNavItem(Icons.person_outline, "PROFILE", 3),
          ],
        ),
      ),
    );
  }

  Widget _buildNavItem(IconData icon, String label, int index) {
    bool isActive = selectedIndex == index;
    return GestureDetector(
      onTap: () => onTap(index),
      behavior: HitTestBehavior.opaque,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: isActive ? Palette.primary : Palette.text_tertiary,
          ),
          const SizedBox(height: 4),
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