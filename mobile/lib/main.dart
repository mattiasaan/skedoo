import 'package:flutter/material.dart';
import 'screens/login/login.dart';
import 'screens/dashboard/dashboard_screen.dart';

void main() => {
  runApp(MyApp())
};

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'skedoo',
      theme: ThemeData(
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => Login(),
        '/dashboard': (context) => DashboardScreen(),
      },
    );
  }
}