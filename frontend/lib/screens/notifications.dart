// screens/notifications.dart
import 'package:flutter/material.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  // Lista simulata delle notifiche presenti nel sistema
  final List<Map<String, dynamic>> _notifications = [
    {
      'id': 1,
      'title': 'Nuovo voto inserito',
      'body': 'Il Professor Recla ha inserito la valutazione della prova scritta di Sistemi e Reti.',
      'time': '10 min fa',
      'isNew': true,
      'type': 'academic',
      'icon': Icons.assignment_turned_in_outlined,
    },
    {
      'id': 2,
      'title': 'Interazione nel post',
      'body': 'Sophia Chen e altre 3 persone hanno inserito un commento sul tuo post in CS Department.',
      'time': '2 ore fa',
      'isNew': true,
      'type': 'social',
      'icon': Icons.chat_bubble_outline_rounded,
    },
    {
      'id': 3,
      'title': 'Aggiornamento completato',
      'body': 'Il firmware della stazione meteo IoT locale (ESP32) è stato aggiornato correttamente alla v1.0.4.',
      'time': 'Ieri',
      'isNew': false,
      'type': 'system',
      'icon': Icons.dns_outlined,
    },
    {
      'id': 4,
      'title': 'Scadenza Progetto CVE',
      'body': 'Promemoria: mancano 3 giorni al caricamento finale della documentazione del dashboard vulnerabilità.',
      'time': '2 giorni fa',
      'isNew': false,
      'type': 'academic',
      'icon': Icons.lock_clock_outlined,
    },
  ];

  @override
  Widget build(BuildContext context) {
    final newNotifications = _notifications.where((n) => n['isNew'] == true).toList();
    final olderNotifications = _notifications.where((n) => n['isNew'] == false).toList();

    return Scaffold(
      backgroundColor: const Color(0xFF0B0F0F),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(),
            Expanded(
              child: _notifications.isEmpty
                  ? _buildEmptyState()
                  : ListView(
                      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
                      children: [
                        if (newNotifications.isNotEmpty) ...[
                          _buildTimeTimelineHeader('OGGI'),
                          ...newNotifications.map((n) => _buildNotificationCard(n)),
                        ],
                        if (olderNotifications.isNotEmpty) ...[
                          const SizedBox(height: 16),
                          _buildTimeTimelineHeader('IN PRECEDENZA'),
                          ...olderNotifications.map((n) => _buildNotificationCard(n)),
                        ],
                        const SizedBox(height: 24),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }

  // APP BAR SUPERIORE CON FRECCIA INDIETRO (Sostituito Hamburger Menu)
  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 12.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 22),
            onPressed: () => Navigator.maybePop(context),
          ),
          const Text(
            'Notifiche',
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
          IconButton(
            icon: const Icon(Icons.done_all_rounded, color: Color(0xFF10B981), size: 24),
            tooltip: 'Segna tutte come lette',
            onPressed: () {
              setState(() {
                for (var n in _notifications) {
                  n['isNew'] = false;
                }
              });
            },
          ),
        ],
      ),
    );
  }

  // INTESTAZIONE TEMPORALE
  Widget _buildTimeTimelineHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4.0, bottom: 12.0, top: 16.0),
      child: Text(
        title,
        style: const TextStyle(
          color: Color(0xFF0E5434),
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  // CARD DELLA NOTIFICA STRUTTURATA
  Widget _buildNotificationCard(Map<String, dynamic> item) {
    final bool isNew = item['isNew'] as bool;

    return Dismissible(
      key: Key(item['id'].toString()),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        margin: const EdgeInsets.only(bottom: 10.0),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1111),
          borderRadius: BorderRadius.circular(14),
        ),
        child: const Icon(Icons.delete_outline_rounded, color: Color(0xFFEF4444)),
      ),
      onDismissed: (direction) {
        setState(() {
          _notifications.removeWhere((n) => n['id'] == item['id']);
        });
      },
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 10.0),
        padding: const EdgeInsets.all(16.0),
        decoration: BoxDecoration(
          color: const Color(0xFF121818),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isNew ? const Color(0xFF0E5434).withOpacity(0.6) : Colors.white.withOpacity(0.01),
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF10B981).withOpacity(0.06),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                item['icon'] as IconData,
                color: isNew ? const Color(0xFF10B981) : Colors.white38,
                size: 20,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          item['title'] as String,
                          style: TextStyle(
                            color: isNew ? Colors.white : Colors.white70,
                            fontSize: 15,
                            fontWeight: isNew ? FontWeight.bold : FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        item['time'] as String,
                        style: TextStyle(
                          color: isNew ? const Color(0xFF10B981) : Colors.white24,
                          fontSize: 11,
                          fontWeight: isNew ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    item['body'] as String,
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.45),
                      fontSize: 13,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // SCHERMATA VUOTA IN CASO DI NESSUNA NOTIFICA
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              color: Color(0xFF121818),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.notifications_off_outlined,
              size: 40,
              color: Colors.white.withOpacity(0.15),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Centro notifiche vuoto',
            style: TextStyle(color: Colors.white70, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Ti avviseremo non appena ci saranno novità.',
            style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 13),
          ),
        ],
      ),
    );
  }
}