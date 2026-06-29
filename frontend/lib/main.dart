import 'package:flutter/material.dart';
import 'package:frontend/screens/calendar.dart';
import 'package:frontend/screens/community.dart';
import 'package:frontend/screens/dashboard.dart';
import 'package:frontend/screens/grades.dart';
import 'package:frontend/screens/inbox.dart';
import 'package:frontend/screens/notifications.dart';
import 'package:frontend/screens/profile.dart';
import 'package:frontend/screens/settings.dart';
import 'app_routes.dart';
import 'main_layout.dart';

void main() {
  runApp(const Skedoo());
}

class Skedoo extends StatelessWidget {
  const Skedoo({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Skedoo',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF10B981),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF0B0F0F),
      ),
      debugShowCheckedModeBanner: false,
      initialRoute: AppRoutes.mainLayout,
      routes: {
        AppRoutes.mainLayout: (context) => const MainLayout(),
        AppRoutes.dashboard: (context) => const DashboardScreen(),
        AppRoutes.calendar: (context) => const Calendar(),
        AppRoutes.profile:(context) => const ProfileScreen(),
        AppRoutes.grades:(context) => const GradesScreen(),
        AppRoutes.inbox:(context) => const InboxScreen(),
        AppRoutes.community:(context) => const CommunityScreen(),
        AppRoutes.settings:(context) => const SettingsScreen(),
        AppRoutes.notifications:(context) => const NotificationsScreen(),
        //qui da aggiungere rotte con AppRoutes.dashboard: (context) => const DashboardScreen()
      },
    );
  }
}