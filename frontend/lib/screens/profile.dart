// screens/profile.dart
import 'package:flutter/material.dart';
import '../main_layout.dart'; 

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0F0F),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(context),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildProfileHeader(),
                    const SizedBox(height: 28),
                    _buildSectionTitle(Icons.analytics_outlined, 'Statistiche veloci'),
                    const SizedBox(height: 12),
                    _buildQuickStats(),
                    const SizedBox(height: 28),
                    _buildSectionTitle(
                      Icons.stars_outlined, 
                      'I miei Badge', 
                      trailing: TextButton(
                        onPressed: () {}, 
                        style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: Size.zero),
                        child: const Text('Vedi tutti', style: TextStyle(color: Color(0xFF0E5434), fontWeight: FontWeight.bold)),
                      )
                    ),
                    const SizedBox(height: 16),
                    _buildBadgesRow(),
                    const SizedBox(height: 28),
                    _buildSectionTitle(Icons.chat_bubble_outline, 'I miei Post'),
                    const SizedBox(height: 16),
                    _buildPostsFeed(),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // APP BAR SUPERIORE CON BURGER MENU E NOTIFICHE
  Widget _buildAppBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.menu, color: Colors.white, size: 32),
            onPressed: () => customScaffoldKey.currentState?.openDrawer(),
          ),
          const Text(
            'Profilo',
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none, color: Colors.white, size: 28), 
            onPressed: () {
              Navigator.pushNamed(context, '/notifications');
            }
          ),
        ],
      ),
    );
  }

  // HEADER PROFILO: AVATAR, UTENTE E PULSANTE EDIT
  Widget _buildProfileHeader() {
    return Center(
      child: Column(
        children: [
          Stack(
            children: [
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFF0E5434), width: 4),
                  image: const DecorationImage(
                    image: NetworkImage('https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=200&auto=format&fit=crop'), 
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              Positioned(
                bottom: 0,
                right: 4,
                child: Container(
                  padding: const EdgeInsets.all(6),
                  decoration: const BoxDecoration(
                    color: Color(0xFF0E5434),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.edit, color: Colors.white, size: 16),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'Alex Rossi',
            style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          const Text(
            'Classe 5^A - Liceo Scientifico',
            style: TextStyle(color: Colors.white38, fontSize: 15),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: FilledButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.person_outline, size: 20),
              label: const Text('Modifica Profilo', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF0E5434),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // RIGA SEZIONI CON ICONA E TITOLO
  Widget _buildSectionTitle(IconData icon, String title, {Widget? trailing}) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFF10B981), size: 24),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
        ),
        if (trailing != null) ...[
          const Spacer(),
          trailing,
        ]
      ],
    );
  }

  // GRID/ROW STATISTICHE VELOCI
  Widget _buildQuickStats() {
    return Row(
      children: [
        _buildStatCard('94%', 'Presenze'),
        const SizedBox(width: 16),
        _buildStatCard('8.5', 'Media GPA'),
      ],
    );
  }

  Widget _buildStatCard(String value, String label) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF121818),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: const TextStyle(color: Color(0xFF10B981), fontSize: 32, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(color: Colors.white38, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }

  // ROW SCROLLABILE DEI BADGE
  Widget _buildBadgesRow() {
    final List<Map<String, dynamic>> badges = [
      {'title': 'Math King', 'icon': Icons.functions, 'color': Colors.orange},
      {'title': 'Science Pro', 'icon': Icons.science_outlined, 'color': Colors.indigo},
      {'title': 'Perfect', 'icon': Icons.calendar_today_outlined, 'color': Colors.green},
      {'title': 'Writer', 'icon': Icons.edit_note_outlined, 'color': Colors.pink},
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: badges.map((b) {
          return Padding(
            padding: const EdgeInsets.only(right: 20.0),
            child: Column(
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: b['color'].withOpacity(0.2),
                    shape: BoxShape.circle,
                    border: Border.all(color: b['color'], width: 2),
                  ),
                  child: Icon(b['icon'], color: b['color'], size: 30),
                ),
                const SizedBox(height: 8),
                Text(b['title'], style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500)),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  // FEED DEI POST (RIPRODUZIONE DELLO SCREENSHOT)
  Widget _buildPostsFeed() {
    return Column(
      children: [
        // Post 1: Solo Testo
        _buildPostCard(
          timeAndCategory: '2 ore fa • Studio di gruppo',
          content: 'Qualcuno disponibile per ripassare fisica oggi pomeriggio in biblioteca? 📚 #fisica #studio',
          likes: 12,
          comments: 4,
        ),
        const SizedBox(height: 16),
        // Post 2: Con Immagine allegata
        _buildPostCard(
          timeAndCategory: 'Ieri • Progetti',
          content: 'Finalmente finito il progetto di Informatica! Ecco uno screenshot del risultato finale. 🚀',
          likes: 45,
          comments: 8,
          imageUrl: 'https://images.unsplash.com/photo-1587620962725-abab7fe55159?q=80&w=500&auto=format&fit=crop', 
        ),
      ],
    );
  }

  Widget _buildPostCard({
    required String timeAndCategory,
    required String content,
    required int likes,
    required int comments,
    String? imageUrl,
  }) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFF121818),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(timeAndCategory, style: const TextStyle(color: Colors.white38, fontSize: 13)),
              IconButton(
                icon: const Icon(Icons.more_vert, color: Colors.white38, size: 20),
                onPressed: () {},
                constraints: const BoxConstraints(),
                padding: EdgeInsets.zero,
              )
            ],
          ),
          const SizedBox(height: 10),
          Text(
            content,
            style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.4),
          ),
          if (imageUrl != null) ...[
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
                imageUrl,
                width: double.infinity,
                height: 180,
                fit: BoxFit.cover,
              ),
            ),
          ],
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(Icons.favorite_border, color: Colors.white.withOpacity(0.3), size: 20),
              const SizedBox(width: 6),
              Text('$likes', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14)),
              const SizedBox(width: 24),
              Icon(Icons.chat_bubble_outline, color: Colors.white.withOpacity(0.3), size: 20),
              const SizedBox(width: 6),
              Text('$comments', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14)),
            ],
          )
        ],
      ),
    );
  }
}