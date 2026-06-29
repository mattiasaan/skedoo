// screens/settings.dart
import 'package:flutter/material.dart';
import '../main_layout.dart'; 

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0F0F),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20.0),
                child: Column(
                  children: [
                    _buildHeaderProfile(),
                    const SizedBox(height: 32),
                    
                    // SEZIONE ACCOUNT
                    _buildSectionHeader('ACCOUNT'),
                    _buildSettingsGroup([
                      _buildSettingRow(Icons.lock_outline_rounded, 'Privacy'),
                      const Divider(color: Colors.white10, height: 1),
                      _buildSettingRow(Icons.shield_outlined, 'Security'),
                    ]),
                    
                    // SEZIONE NOTIFICATIONS
                    _buildSectionHeader('NOTIFICATIONS'),
                    _buildSettingsGroup([
                      _buildSettingRow(Icons.notifications_none_outlined, 'Push Updates'),
                      const Divider(color: Colors.white10, height: 1),
                      _buildSettingRow(Icons.mail_outline_rounded, 'Email'),
                    ]),
                    
                    // SEZIONE APPEARANCE
                    _buildSectionHeader('APPEARANCE'),
                    _buildSettingsGroup([
                      _buildSettingRow(Icons.dark_mode_outlined, 'Theme', subtitle: 'Dark Mode'),
                      const Divider(color: Colors.white10, height: 1),
                      _buildSettingRow(Icons.text_fields_rounded, 'Font Size'),
                    ]),
                    
                    // SEZIONE COMMUNITY
                    _buildSectionHeader('COMMUNITY'),
                    _buildSettingsGroup([
                      _buildSettingRow(Icons.gavel_outlined, 'Moderation'),
                      const Divider(color: Colors.white10, height: 1),
                      _buildSettingRow(Icons.block_flipped, 'Blocked Users'),
                    ]),
                    
                    // SEZIONE INFO
                    _buildSectionHeader('INFO'),
                    _buildSettingsGroup([
                      _buildSettingRow(Icons.info_outline_rounded, 'About SchoolHub'),
                      const Divider(color: Colors.white10, height: 1),
                      _buildSettingRow(Icons.help_outline_rounded, 'Support'),
                    ]),
                    
                    const SizedBox(height: 32),
                    _buildLogoutButton(),
                    const SizedBox(height: 20),
                    _buildVersionText(),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // APP BAR SUPERIORE
  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.menu, color: Colors.white, size: 28),
            onPressed: () => customScaffoldKey.currentState?.openDrawer(),
          ),
          const Text(
            'Settings',
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(width: 48), // Spacers per bilanciare l'icona del menu
        ],
      ),
    );
  }

  // BLOCCO PROFILO UTENTE SUPERIORE (Esatto da Screenshot 2026-06-29 211537.png)
  Widget _buildHeaderProfile() {
    return Column(
      children: [
        Stack(
          alignment: Alignment.bottomRight,
          children: [
            Container(
              padding: const EdgeInsets.all(3),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF0E5434), width: 1.5),
              ),
              child: const CircleAvatar(
                radius: 46,
                backgroundImage: NetworkImage('https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop'),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(6),
              decoration: const BoxDecoration(
                color: Color(0xFF10B981),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.edit, color: Color(0xFF0B0F0F), size: 14),
            ),
          ],
        ),
        const SizedBox(height: 16),
        const Text(
          'Alex Johnson',
          style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: 0.3),
        ),
        const SizedBox(height: 4),
        Text(
          'Computer Science • Year 3',
          style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 13, fontWeight: FontWeight.w500),
        ),
      ],
    );
  }

  // INTESTAZIONE DELLE SEZIONI (Testo piccolo verde)
  Widget _buildSectionHeader(String title) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.only(left: 4.0, bottom: 10.0, top: 18.0),
      child: Text(
        title,
        style: const TextStyle(
          color: Color(0xFF0E5434), 
          fontSize: 12, 
          fontWeight: FontWeight.bold, 
          letterSpacing: 1.2
        ),
      ),
    );
  }

  // CONTENITORE COMPATTO PER LE RIGHE DI IMPOSTAZIONE
  Widget _buildSettingsGroup(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF121818),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.01)),
      ),
      child: Column(children: children),
    );
  }

  // SINGOLA RIGA DI IMPOSTAZIONE
  Widget _buildSettingRow(IconData icon, String title, {String? subtitle}) {
    return InkWell(
      onTap: () {},
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 16.0),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF10B981), size: 22),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600),
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 12),
                    ),
                  ]
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: Colors.white.withOpacity(0.3), size: 22),
          ],
        ),
      ),
    );
  }

  // PULSANTE DI LOGOUT (In linea con lo screen)
  Widget _buildLogoutButton() {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: TextButton(
        onPressed: () {},
        style: TextButton.styleFrom(
          backgroundColor: const Color(0xFF1A1111), // Tonalità rossa scura/opaca di sistema
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.logout_rounded, color: Color(0xFFEF4444), size: 18),
            SizedBox(width: 8),
            Text(
              'Logout',
              style: TextStyle(color: Color(0xFFEF4444), fontSize: 15, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  // TESTO DELLA VERSIONE IN FONDO
  Widget _buildVersionText() {
    return Text(
      'VERSION 2.4.1 (STABLE)',
      style: TextStyle(
        color: Colors.white.withOpacity(0.2), 
        fontSize: 10, 
        fontWeight: FontWeight.bold, 
        letterSpacing: 1.0
      ),
    );
  }
}