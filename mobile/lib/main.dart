import 'package:flutter/material.dart';
import 'screens/dashboard/main_navigation_screen.dart'; // Assicurati che il percorso sia questo

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'University App',
      theme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
      ),
      // ✅ È qui che deve puntare: alla schermata con la barra di navigazione
      home: const MainNavigationScreen(), 
    );
  }
}