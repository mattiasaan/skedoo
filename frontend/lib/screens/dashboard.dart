// screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/app_routes.dart';
import '../main_layout.dart';
import 'package:timeline_tile/timeline_tile.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            const SizedBox(height: 24),
            _buildNoticeCard(),
            const SizedBox(height: 28),
            _buildSectionTitle('UP NEXT'),
            const SizedBox(height: 12),
            _buildUpNextCard(),
            const SizedBox(height: 28),
            _buildScheduleHeader(context),
            const SizedBox(height: 16),
            _buildScheduleTimeline(),
          ],
        ),
      ),
    );
  }

  // 1. HEADER: Profilo, Saluto e Notifiche
  Widget _buildHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            IconButton(
              icon: const Icon(Icons.menu, color: Colors.white, size: 40),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
              onPressed: () {
                customScaffoldKey.currentState?.openDrawer();
              },
            ),
            const SizedBox(width: 16),
          ],
        ),
        Row(
          children: [
            const CircleAvatar(
              radius: 24,
              backgroundColor: Colors.grey,
              child: Icon(Icons.person, color: Colors.white),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'Hi, Alex!',
                  style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 4),
                Text(
                  'Monday, Oct 24',
                  style: TextStyle(color: Colors.grey, fontSize: 14),
                ),
              ],
            ),
          ],
        ),
        Stack(
          children: [
            IconButton(
              icon: const Icon(Icons.notifications_none_outlined, color: Colors.white, size: 28),
              onPressed: () {
                Navigator.pushNamed(context, '/notifications');
              },
            ),
            Positioned(
              right: 12,
              top: 12,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
              ),
            )
          ],
        )
      ],
    );
  }

  // 2. NOTICE CARD: Last Minute Changes
  Widget _buildNoticeCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1916), // Verde scurissimo di sfondo
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1B3D33), width: 1),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline, color: Color(0xFF10B981), size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'Last Minute Changes',
                  style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 6),
                Text(
                  'Professor Rossi absent - Room 204 moved to 201 for today\'s Physics lab.',
                  style: TextStyle(color: Colors.white70, fontSize: 14, height: 1.3),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          const Icon(Icons.close, color: Colors.white54, size: 20),
        ],
      ),
    );
  }

  // Sezioni di testo (UP NEXT)
  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(color: Colors.white60, fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 1.2),
    );
  }

  // 3. UP NEXT CARD: Linear Algebra Card Principale
  Widget _buildUpNextCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF0E5434), // Verde foresta profondo
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'MATHEMATICS • CALCULUS II',
                style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.5),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Text(
                  'ROOM\n302',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold, height: 1.1),
                ),
              )
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Linear Algebra',
            style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              const Icon(Icons.access_time, color: Colors.white70, size: 18),
              const SizedBox(width: 6),
              const Text('10:30 AM - 11:45 AM', style: TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(width: 24),
              const Icon(Icons.location_on_outlined, color: Colors.white70, size: 18),
              const SizedBox(width: 6),
              const Text('Forest Green Building', style: TextStyle(color: Colors.white70, fontSize: 13)),
            ],
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: const Color(0xFF0E5434),
              minimumSize: const Size(double.infinity, 50),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 0,
            ),
            onPressed: () {},
            child: const Text('Join Online Meeting', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          )
        ],
      ),
    );
  }

  // Header per la sezione Schedule con il tasto "View Calendar"
  Widget _buildScheduleHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          'TODAY\'S SCHEDULE',
          style: TextStyle(color: Colors.white60, fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 1.2),
        ),
        TextButton(
          onPressed: () {
            MainLayout.of(context).changeTab(1);
          },
          style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: Size.zero),
          child: const Text(
            'VIEW CALENDAR',
            style: TextStyle(color: Color(0xFF10B981), fontSize: 12, fontWeight: FontWeight.bold),
          ),
        )
      ],
    );
  }

  // 4. TIMELINE SCHEDULE: Lista dei corsi aggiornata con timeline_tile
  Widget _buildScheduleTimeline() {
    return Column(
      children: [
        _buildTimelineItem(
          time: '08:00 - 09:30',
          title: 'English Literature',
          subtitle: 'Room 104 • Dr. Bennett',
          status: 'COMPLETED',
          statusColor: Colors.white10,
          textColor: Colors.white60,
          isFirst: true,
        ),
        _buildTimelineItem(
          time: '10:30 - 11:45',
          title: 'Mathematics',
          subtitle: 'Room 302 • Prof. Schmidt',
          status: 'ONGOING',
          statusColor: const Color(0xFF10B981).withOpacity(0.15),
          textColor: Colors.white,
          isOngoing: true,
        ),
        _buildTimelineItem(
          time: '13:00 - 14:30',
          title: 'Modern History',
          subtitle: 'Room 201 • Dr. Henderson',
          status: 'Upcoming',
          statusColor: Colors.transparent,
          textColor: Colors.white60,
          isLast: true,
        ),
      ],
    );
  }

  // Elemento singolo corretto con allineamento ad aggancio sinistro e indicatorXY corretto
  Widget _buildTimelineItem({
    required String time,
    required String title,
    required String subtitle,
    required String status,
    required Color statusColor,
    required Color textColor,
    bool isFirst = false,
    bool isLast = false,
    bool isOngoing = false,
  }) {
    return TimelineTile(
      alignment: TimelineAlign.start, // Blocca la linea a sinistra eliminando i vuoti asimmetrici
      isFirst: isFirst,
      isLast: isLast,
      beforeLineStyle: const LineStyle(color: Color(0xFF1B3D33), thickness: 2),
      afterLineStyle: const LineStyle(color: Color(0xFF1B3D33), thickness: 2),
      indicatorStyle: IndicatorStyle(
        width: 20,
        height: 20,
        padding: const EdgeInsets.symmetric(horizontal: 4),
        indicatorXY: 0.2, // Riposiziona l'altezza del pallino in corrispondenza del testo
        indicator: Center(
          child: isOngoing
              ? Container(
                  width: 14,
                  height: 14,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF0B0F0F), // Uguale allo sfondo per l'effetto vuoto interno
                    border: Border.all(color: const Color(0xFF10B981), width: 2.5),
                  ),
                )
              : Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Color(0xFF10B981),
                    shape: BoxShape.circle,
                  ),
                ),
        ),
      ),
      endChild: Padding(
        padding: const EdgeInsets.only(left: 12.0, top: 6.0, bottom: 6.0), // Padding ridotto per accostarsi alla linea
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF121818),
            borderRadius: BorderRadius.circular(16),
            border: isOngoing ? Border.all(color: const Color(0xFF10B981), width: 1.5) : null,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(time, style: TextStyle(color: textColor.withOpacity(0.6), fontSize: 12)),
                  if (status.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(color: statusColor, borderRadius: BorderRadius.circular(6)),
                      child: Text(
                        status,
                        style: TextStyle(
                          color: isOngoing ? const Color(0xFF10B981) : Colors.white54,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(title, style: TextStyle(color: textColor, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(subtitle, style: TextStyle(color: textColor.withOpacity(0.6), fontSize: 13)),
            ],
          ),
        ),
      ),
    );
  }
}