// screens/community.dart
import 'package:flutter/material.dart';
import '../main_layout.dart'; 

class CommunityScreen extends StatelessWidget {
  const CommunityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0F0F),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(),
            _buildSearchBar(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(vertical: 12.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildTopContributorsSection(),
                    const SizedBox(height: 16),
                    _buildPostFeed(),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        backgroundColor: const Color(0xFF0E5434),
        foregroundColor: Colors.white,
        elevation: 4,
        shape: const CircleBorder(),
        child: const Icon(Icons.edit_outlined, size: 26),
      ),
    );
  }

  // APP BAR SUPERIORE CON FUNZIONI DI NAVIGAZIONE
  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.menu, color: Colors.white, size: 28),
            onPressed: () => customScaffoldKey.currentState?.openDrawer(),
          ),
          const Text(
            'Community',
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
          IconButton(
            icon: const Icon(Icons.groups_outlined, color: Colors.white70, size: 26),
            onPressed: () {},
          ),
        ],
      ),
    );
  }

  // BARRA DI RICERCA ORIZZONTALE (Esatta dallo Screenshot 2026-06-29 211032.png)
  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
      child: Container(
        height: 46,
        padding: const EdgeInsets.symmetric(horizontal: 16.0),
        decoration: BoxDecoration(
          color: const Color(0xFF121818),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withOpacity(0.04)),
        ),
        child: Row(
          children: [
            Icon(Icons.search, color: Colors.white.withOpacity(0.3), size: 22),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                style: const TextStyle(color: Colors.white, fontSize: 14),
                decoration: InputDecoration(
                  hintText: 'Search community posts, users, or topics...',
                  hintStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 14),
                  border: InputBorder.none,
                  isDense: true,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // SEZIONE TOP CONTRIBUTORS CON SCROLL ORIZZONTALE
  Widget _buildTopContributorsSection() {
    final contributors = [
      {'name': 'Alex P.', 'url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=120&auto=format&fit=crop', 'hasBadge': true},
      {'name': 'Sarah M.', 'url': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=120&auto=format&fit=crop', 'hasBadge': false},
      {'name': 'Jason K.', 'url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=120&auto=format&fit=crop', 'hasBadge': false},
      {'name': 'Mia L.', 'url': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=120&auto=format&fit=crop', 'hasBadge': false},
      {'name': 'Chris', 'url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=120&auto=format&fit=crop', 'hasBadge': false},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'TOP CONTRIBUTORS',
                style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.0),
              ),
              TextButton(
                onPressed: () {},
                style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: Size.zero, tapTargetSize: MaterialTapTargetSize.shrinkWrap),
                child: const Text('View All', style: TextStyle(color: Color(0xFF10B981), fontSize: 13, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 100,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 14.0),
            itemCount: contributors.length,
            itemBuilder: (context, index) {
              final user = contributors[index];
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6.0),
                child: Column(
                  children: [
                    Stack(
                      alignment: Alignment.bottomRight,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(2.5),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: user['hasBadge'] as bool ? const Color(0xFF10B981) : Colors.white24, 
                              width: 2
                            ),
                          ),
                          child: CircleAvatar(
                            radius: 26,
                            backgroundColor: const Color(0xFF121818),
                            backgroundImage: NetworkImage(user['url'] as String),
                          ),
                        ),
                        if (user['hasBadge'] as bool)
                          Container(
                            padding: const EdgeInsets.all(3),
                            decoration: const BoxDecoration(color: Color(0xFF0E5434), shape: BoxShape.circle),
                            child: const Icon(Icons.star, color: Colors.amber, size: 12),
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      user['name'] as String,
                      style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  // FEED DEI POST COMPLESSIVO
  Widget _buildPostFeed() {
    return Column(
      children: [
        _buildPostCard(
          author: 'Jordan Smith',
          timeAndDept: '2 hours ago • CS Department',
          avatarUrl: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=100&auto=format&fit=crop',
          content: 'Just finished the Advanced Algorithms project! If anyone needs help with Big O analysis or dynamic programming, feel free to reach out. 🚀📚',
          imageUrl: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=600&auto=format&fit=crop', // Immagine codice laptop dello screen
          likes: '124',
          comments: '18',
          shares: '5',
        ),
        _buildPostCard(
          author: 'Sophia Chen',
          timeAndDept: '5 hours ago • Art & Design',
          avatarUrl: 'https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?q=80&w=100&auto=format&fit=crop',
          content: 'Thinking about starting a photography club for weekend photowalks around the campus. Anyone interested? We could explore the old library wing first. 📸',
          imageUrl: null,
          likes: '56',
          comments: '42',
          shares: '12',
        ),
        _buildPostCard(
          author: "Liam O'Connor",
          timeAndDept: 'Yesterday • Engineering',
          avatarUrl: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=100&auto=format&fit=crop',
          content: 'Is the central cafeteria open late tonight for the study marathon? I heard there might be a discount for students with valid IDs.',
          imageUrl: null,
          likes: '12',
          comments: '3',
          shares: '0',
        ),
      ],
    );
  }

  // CARD STRUTTURATA DEL SINGOLO POST
  Widget _buildPostCard({
    required String author,
    required String timeAndDept,
    required String avatarUrl,
    required String content,
    required String? imageUrl,
    required String likes,
    required String comments,
    required String shares,
  }) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: const Color(0xFF121818),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.02)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Riga Intestazione (Avatar, Nomi, Opzioni)
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              CircleAvatar(
                radius: 20,
                backgroundImage: NetworkImage(avatarUrl),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      author,
                      style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      timeAndDept,
                      style: TextStyle(color: Colors.white.withOpacity(0.35), fontSize: 12),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: Icon(Icons.more_horiz, color: Colors.white.withOpacity(0.5)),
                onPressed: () {},
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ],
          ),
          const SizedBox(height: 14),
          // Testo del Post
          Text(
            content,
            style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.42),
          ),
          // Allegato Immagine (se presente)
          if (imageUrl != null) ...[
            const SizedBox(height: 14),
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
          // Barra delle interazioni inferiori
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  _buildInteractionButton(Icons.favorite_border, likes),
                  const SizedBox(width: 16),
                  _buildInteractionButton(Icons.chat_bubble_outline_rounded, comments),
                  const SizedBox(width: 16),
                  _buildInteractionButton(Icons.share_outlined, shares),
                ],
              ),
              IconButton(
                icon: Icon(Icons.bookmark_border_rounded, color: Colors.white.withOpacity(0.4), size: 22),
                onPressed: () {},
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // Pulsante per icone di interazione (Like, Commenti, Condivisioni)
  Widget _buildInteractionButton(IconData icon, String count) {
    return Row(
      children: [
        Icon(icon, color: Colors.white.withOpacity(0.4), size: 20),
        const SizedBox(width: 6),
        Text(
          count,
          style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 13, fontWeight: FontWeight.w500),
        ),
      ],
    );
  }
}