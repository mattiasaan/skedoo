// screens/main_layout.dart
import 'package:flutter/material.dart';
import 'package:frontend/screens/community.dart';
import 'package:frontend/screens/dashboard.dart';
import 'package:frontend/screens/calendar.dart';
import 'package:frontend/screens/grades.dart';
import 'package:frontend/screens/inbox.dart'; 
import 'package:frontend/screens/profile.dart';
import 'package:frontend/screens/settings.dart';

final GlobalKey<ScaffoldState> customScaffoldKey = GlobalKey<ScaffoldState>();

class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  // Metodo statico per permettere alle schermate figlie di cambiare scheda
  static _MainLayoutState of(BuildContext context) {
    final state = context.findAncestorStateOfType<_MainLayoutState>();
    if (state == null) {
      throw Exception("MainLayout non trovato nel contesto attuale.");
    }
    return state; // CORRETTO: Ora ritorna correttamente lo stato
  }

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  int _selectedIndex = 0;

  // Lista delle schermate principali dell'app raggiungibili dal menu
  final List<Widget> _screens = [
    const DashboardScreen(),
    const Calendar(),
    const ProfileScreen(),
    const GradesScreen(),
    const InboxScreen(),
    const CommunityScreen(),
    const SettingsScreen(),
  ];

  // Gestione centralizzata del cambio scheda e chiusura del Drawer
  void changeTab(int index) {
    setState(() {
      _selectedIndex = index;
    });
    // Se il drawer è aperto, lo chiude in automatico al cambio della scheda
    if (customScaffoldKey.currentState?.isDrawerOpen ?? false) {
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: customScaffoldKey,
      backgroundColor: const Color(0xFF0B0F0F),
      drawer: Drawer(
        child: Container(
          color: const Color(0xFF121818), // Sfondo scuro coerente
          child: ListView(
            padding: EdgeInsets.zero,
            children: [
              const DrawerHeader(
                decoration: BoxDecoration(color: Color(0xFF0E5434)),
                child: Text(
                  'Skedoo Menu',
                  style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.dashboard, color: Colors.white),
                title: const Text('Dashboard', style: TextStyle(color: Colors.white)),
                selected: _selectedIndex == 0,
                selectedColor: const Color(0xFF10B981),
                onTap: () => changeTab(0),
              ),
              ListTile(
                leading: const Icon(Icons.calendar_month, color: Colors.white),
                title: const Text('Calendar', style: TextStyle(color: Colors.white)),
                selected: _selectedIndex == 1,
                selectedColor: const Color(0xFF10B981),
                onTap: () => changeTab(1),
              ),
              ListTile(
                leading: const Icon(Icons.person, color: Colors.white),
                title: const Text('Profile', style: TextStyle(color: Colors.white)),
                selected: _selectedIndex == 2,
                selectedColor: const Color(0xFF10B981),
                onTap: () => changeTab(2),
              ),
              ListTile(
                leading: const Icon(Icons.grade, color: Colors.white),
                title: const Text('Grades', style: TextStyle(color: Colors.white)),
                selected: _selectedIndex == 3,
                selectedColor: const Color(0xFF10B981),
                onTap: () => changeTab(3),
              ),
              ListTile(
                leading: const Icon(Icons.inbox, color: Colors.white),
                title: const Text('Inbox', style: TextStyle(color: Colors.white)),
                selected: _selectedIndex == 4,
                selectedColor: const Color(0xFF10B981),
                onTap: () => changeTab(4),
              ),
              ListTile(
                leading: const Icon(Icons.comment, color: Colors.white),
                title: const Text('Community', style: TextStyle(color: Colors.white)),
                selected: _selectedIndex == 5, // CORRETTO: era 4
                selectedColor: const Color(0xFF10B981),
                onTap: () => changeTab(5),
              ),
              ListTile(
                leading: const Icon(Icons.settings, color: Colors.white),
                title: const Text('Settings', style: TextStyle(color: Colors.white)),
                selected: _selectedIndex == 6, // CORRETTO: era 5
                selectedColor: const Color(0xFF10B981),
                onTap: () => changeTab(6),
              ),
            ],
          ),
        ),
      ),
      body: _screens[_selectedIndex],
    );
  }
}