// screens/inbox.dart
import 'package:flutter/material.dart';
import '../main_layout.dart'; 

class InboxScreen extends StatefulWidget {
  const InboxScreen({super.key});

  @override
  State<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends State<InboxScreen> {
  String _selectedCategory = 'All';

  final List<Map<String, dynamic>> _categories = [
    {'id': 'All', 'label': 'Tutti', 'icon': Icons.grid_view_rounded},
    {'id': 'Updates', 'label': 'Aggiornamenti', 'icon': Icons.update_outlined}, // Sostituito con un'icona neutra di sistema
    {'id': 'Social', 'label': 'Social', 'icon': Icons.hub_outlined},
    {'id': 'Promo', 'label': 'Promozioni', 'icon': Icons.add_business_outlined},
  ];

  void _showFilterBottomSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF121818),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 20.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
                  child: Text(
                    'Seleziona Canale Feed',
                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
                const Divider(color: Colors.white10),
                ..._categories.map((cat) {
                  final isSelected = _selectedCategory == cat['id'];
                  return ListTile(
                    leading: Icon(
                      cat['icon'] as IconData, 
                      color: isSelected ? const Color(0xFF10B981) : Colors.white60
                    ),
                    title: Text(
                      cat['label'] as String,
                      style: TextStyle(
                        color: isSelected ? Colors.white : Colors.white,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                    trailing: isSelected 
                        ? const Icon(Icons.check_circle_outline, color: Color(0xFF10B981)) 
                        : null,
                    onTap: () {
                      setState(() {
                        _selectedCategory = cat['id'] as String;
                      });
                      Navigator.pop(context);
                    },
                  );
                }),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0F0F),
      body: SafeArea(
        child: Column(
          children: [
            _buildCustomHeader(),
            _buildFilterBar(),
            const SizedBox(height: 14),
            Expanded(
              child: _buildNotificationFeed(),
            ),
          ],
        ),
      ),
    );
  }

  // HEADER PERSONALIZZATO (Sostituisce la barra Gmail)
  Widget _buildCustomHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.menu, color: Colors.white, size: 28),
            onPressed: () => customScaffoldKey.currentState?.openDrawer(),
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Inbox Feed',
              style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.search, color: Colors.white70, size: 26),
            onPressed: () {},
          ),
        ],
      ),
    );
  }

  // BARRA FILTRI INTEGRATA CON LO STILE DELL'APP
  Widget _buildFilterBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Row(
        children: [
          Expanded(
            child: Container(
              height: 40,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF121818),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white.withOpacity(0.04)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Filtro: ${_categories.firstWhere((c) => c['id'] == _selectedCategory)['label']}',
                    style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500),
                  ),
                  const Icon(Icons.tune_rounded, color: Color(0xFF10B981), size: 18),
                ],
              ),
            ),
          ),
          const SizedBox(width: 10),
          ElevatedButton.icon(
            onPressed: _showFilterBottomSheet,
            icon: const Icon(Icons.filter_list, size: 16),
            label: const Text('Filtra per'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0E5434),
              foregroundColor: Colors.white,
              elevation: 0,
              textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
          ),
        ],
      ),
    );
  }

  // FEED NOTIFICHE / EMAIL IN CARD GEOMETRICHE
  Widget _buildNotificationFeed() {
    final List<Map<String, dynamic>> messages = [
      {
        'category': 'Updates',
        'sender': 'LinkedIn Network',
        'subject': 'Nuove visite al tuo profilo professionale',
        'snippet': 'Il tuo profilo è apparso in ricerche recenti. Scopri quali aziende stanno cercando le tue competenze.',
        'time': '20:31',
        'isUnread': true,
        'icon': Icons.star_purple500_outlined,
        'iconColor': Colors.blue,
      },
      {
        'category': 'Updates',
        'sender': 'Fintech Services',
        'subject': 'Aggiornamento Termini e Condizioni',
        'snippet': 'Ti informiamo che i dettagli contrattuali relativi ai servizi digitali sono stati aggiornati nei moduli allegati.',
        'time': '14:12',
        'isUnread': false,
        'icon': Icons.gavel_rounded,
        'iconColor': Colors.amber,
      },
      {
        'category': 'Promo',
        'sender': 'Tech Store',
        'subject': 'Offerte Flash del fine settimana',
        'snippet': 'Sconti esclusivi su hardware e accessori per lo sviluppo. Promo valida fino a esaurimento scorte.',
        'time': '12:18',
        'isUnread': true,
        'icon': Icons.local_mall_outlined,
        'iconColor': Colors.red,
      },
      {
        'category': 'Social',
        'sender': 'Developer Community',
        'subject': 'Nuovo trend rilevato nel feed locale',
        'snippet': 'Contenuti consigliati in base ai tuoi interessi tecnologici e ai gruppi di sviluppo della tua zona.',
        'time': 'Ieri',
        'isUnread': true,
        'icon': Icons.forum_outlined,
        'iconColor': Colors.purple,
      }
    ];

    final filteredMessages = _selectedCategory == 'All'
        ? messages
        : messages.where((msg) => msg['category'] == _selectedCategory).toList();

    if (filteredMessages.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.space_dashboard_outlined, size: 48, color: Colors.white.withOpacity(0.1)),
            const SizedBox(height: 12),
            const Text('Nessun avviso in questo canale', style: TextStyle(color: Colors.white24, fontSize: 14)),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: filteredMessages.length,
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      itemBuilder: (context, index) {
        final item = filteredMessages[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 12.0),
          child: _buildStructuredMessageCard(item),
        );
      },
    );
  }

  // CARD DELLA NOTIFICA (Coerente con il design delle materie)
  Widget _buildStructuredMessageCard(Map<String, dynamic> item) {
    final bool isUnread = item['isUnread'] as bool;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF121818),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isUnread ? const Color(0xFF0E5434) : Colors.white.withOpacity(0.02),
          width: isUnread ? 1.2 : 1.0,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Icona geometrica con sfondo sfumato/opaco
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: (item['iconColor'] as Color).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(item['icon'] as IconData, color: item['iconColor'] as Color, size: 20),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item['sender'] as String,
                      style: TextStyle(
                        color: isUnread ? const Color(0xFF10B981) : Colors.white70,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      item['subject'] as String,
                      style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Text(
                item['time'] as String,
                style: TextStyle(
                  color: isUnread ? const Color(0xFF10B981) : Colors.white24,
                  fontSize: 12,
                  fontWeight: isUnread ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            item['snippet'] as String,
            style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 13, height: 1.3),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (isUnread) ...[
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0E5434).withOpacity(0.3),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    'NEW',
                    style: TextStyle(color: Color(0xFF10B981), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                  ),
                ),
              ],
            ),
          ]
        ],
      ),
    );
  }
}