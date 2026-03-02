import 'package:flutter/material.dart';
import './screens/login.dart';
import './screens/dashboard.dart';

void main() => {
  runApp(MyApp())
};

class MyApp extends StatelessWidget {
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
        '/dashboard': (context) => Dashboard(),
      },
    );
  }
}