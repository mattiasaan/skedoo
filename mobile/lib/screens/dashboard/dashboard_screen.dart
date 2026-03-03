import 'package:flutter/material.dart';
import '../../palette/palette.dart';
import 'widgets/header_section.dart';
import 'widgets/last_minute_card.dart';
import 'widgets/up_next_card.dart';
import 'widgets/today_schedule_section.dart';
import 'widgets/bottom_nav.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      bottomNavigationBar: const BottomNav(),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(height: 20),
              HeaderSection(),
              SizedBox(height: 24),
              LastMinuteCard(),
              SizedBox(height: 28),
              UpNextCard(),
              SizedBox(height: 28),
              TodayScheduleSection(),
              SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}