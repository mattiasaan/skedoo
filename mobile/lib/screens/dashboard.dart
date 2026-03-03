import 'package:flutter/material.dart';
import './altra_opzione.dart';
import './home.dart';
import './settings.dart';

class Dashboard extends StatefulWidget {
  @override
  _DashboardState createState() => _DashboardState();
}

class _DashboardState extends State<Dashboard> {
  int _selectedIndex = 0;

  static List<Widget> _pages = <Widget>[
    Home(),
    AltraOpzione(),
    Impostazioni(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.calendar_month), label: 'Calendar'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Impostazioni'),
        ]
      ),
    );
  }
}