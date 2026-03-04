import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../palette/palette.dart';
import '../dashboard/notification_screen.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  // ✅ Inizializziamo con la data attuale del sistema
  late DateTime _focusedDay;
  late DateTime _selectedDay;
  late PageController _pageController;

  @override
  void initState() {
    super.initState();
    _focusedDay = DateTime.now();
    _selectedDay = DateTime.now();
    // Il PageController parte da 0 (il mese attuale)
    _pageController = PageController(initialPage: 0);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        automaticallyImplyLeading: false,
        title: const Text("Calendar", style: TextStyle(color: Palette.text_primary, fontWeight: FontWeight.bold)),
        centerTitle: true,
        actions: [
          IconButton(onPressed: () {}, icon: const Icon(Icons.search, color: Palette.text_primary)),
          IconButton(
            onPressed: () {
              Navigator.push(
                context, 
                MaterialPageRoute(builder: (context) => const NotificationScreen()),
              );
            }, 
            icon: const Icon(
              Icons.notifications_none, 
              color: Palette.text_primary
            )
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ✅ Header Dinamico: Mostra Mese e Anno Correnti
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  DateFormat('MMMM yyyy').format(_focusedDay),
                  style: const TextStyle(color: Palette.text_primary, fontSize: 26, fontWeight: FontWeight.bold),
                ),
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.chevron_left, color: Palette.primary),
                      onPressed: () => _pageController.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut),
                    ),
                    IconButton(
                      icon: const Icon(Icons.chevron_right, color: Palette.primary),
                      onPressed: () => _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 20),
            _buildDaysOfWeek(),
            const SizedBox(height: 12),
            
            // Container del Calendario Interattivo
            SizedBox(
              height: 280, 
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) {
                  setState(() {
                    // Calcola il nuovo mese basandosi sull'indice (0 = mese attuale)
                    DateTime now = DateTime.now();
                    _focusedDay = DateTime(now.year, now.month + index, 1);
                  });
                },
                itemBuilder: (context, index) {
                  DateTime now = DateTime.now();
                  return _buildCalendarGrid(DateTime(now.year, now.month + index, 1));
                },
              ),
            ),
            
            const SizedBox(height: 10),
            _buildLegend(),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: const [
                Text("Events", style: TextStyle(color: Palette.text_primary, fontSize: 18, fontWeight: FontWeight.bold)),
                Text("See All", style: TextStyle(color: Palette.primary, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            _buildEventCard("Math Mid-term Test", "09:00 AM - 10:30 AM • Room 302", Icons.calculate_outlined, Colors.green),
            _buildEventCard("Weekly School Assembly", "11:00 AM - 12:00 PM • Main Hall", Icons.groups_outlined, Colors.blue),
            const SizedBox(height: 100), 
          ],
        ),
      ),
    );
  }

  Widget _buildDaysOfWeek() {
    final List<String> days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: days.map((day) => Expanded(
        child: Center(
          child: Text(day, style: const TextStyle(color: Palette.text_tertiary, fontSize: 11, fontWeight: FontWeight.bold)),
        ),
      )).toList(),
    );
  }

  Widget _buildCalendarGrid(DateTime month) {
    final int daysInMonth = DateTime(month.year, month.month + 1, 0).day;
    final int firstDayOffset = DateTime(month.year, month.month, 1).weekday % 7;

    return GridView.builder(
      padding: EdgeInsets.zero,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: 42, 
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 7,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
      ),
      itemBuilder: (context, index) {
        int dayNumber = index - firstDayOffset + 1;
        bool isCurrentMonth = dayNumber > 0 && dayNumber <= daysInMonth;

        if (!isCurrentMonth) return const SizedBox();

        DateTime currentDateTime = DateTime(month.year, month.month, dayNumber);
        
        // Controllo se è il giorno selezionato
        bool isSelected = _selectedDay.year == currentDateTime.year &&
                          _selectedDay.month == currentDateTime.month &&
                          _selectedDay.day == currentDateTime.day;
        
        // Controllo se è oggi (per aggiungere un piccolo bordo o stile differente se vuoi)
        DateTime today = DateTime.now();
        bool isToday = today.year == currentDateTime.year &&
                       today.month == currentDateTime.month &&
                       today.day == currentDateTime.day;

        return GestureDetector(
          onTap: () {
            setState(() {
              _selectedDay = currentDateTime;
            });
          },
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              color: isSelected ? Palette.primary : Palette.background_secondary.withOpacity(0.3),
              borderRadius: BorderRadius.circular(12),
              border: isToday && !isSelected 
                  ? Border.all(color: Palette.primary, width: 1.5) // Bordo verde se è oggi ma non selezionato
                  : Border.all(color: Palette.background_tertiary, width: 1),
            ),
            child: Center(
              child: Text(
                "$dayNumber",
                style: TextStyle(
                  color: isSelected ? Colors.white : Palette.text_primary,
                  fontWeight: isSelected || isToday ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildLegend() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _legendItem("Tests", Colors.green),
        _legendItem("Deadlines", Colors.red),
        _legendItem("Holidays", Colors.orange),
        _legendItem("Assemblies", Colors.blue),
      ],
    );
  }

  Widget _legendItem(String label, Color color) {
    return Row(
      children: [
        Container(width: 7, height: 7, decoration: BoxDecoration(shape: BoxShape.circle, color: color)),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(color: Palette.text_tertiary, fontSize: 10)),
      ],
    );
  }

  Widget _buildEventCard(String title, String subtitle, IconData icon, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Palette.background_secondary, borderRadius: BorderRadius.circular(20)),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(14)),
            child: Icon(icon, color: color, size: 22),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Palette.text_primary, fontSize: 15, fontWeight: FontWeight.bold)),
                Text(subtitle, style: const TextStyle(color: Palette.text_tertiary, fontSize: 12)),
              ],
            ),
          ),
          const Icon(Icons.chevron_right, color: Palette.text_tertiary, size: 20),
        ],
      ),
    );
  }
}