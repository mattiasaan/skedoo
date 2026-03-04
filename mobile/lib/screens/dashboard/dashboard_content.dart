import 'package:flutter/material.dart';
import '../../palette/palette.dart';
import 'widgets/header_section.dart';
import 'widgets/last_minute_card.dart';
import 'widgets/up_next_card.dart';
import 'widgets/today_schedule_section.dart';

class DashboardContent extends StatelessWidget {
  const DashboardContent({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
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
    );
  }
}