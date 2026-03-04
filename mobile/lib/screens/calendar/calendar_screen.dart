import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../palette/palette.dart';
import '../../models/event_model.dart'; // ✅ Importa la lista dummyEvents
import '../dashboard/notification_screen.dart';
import 'all_events_screen.dart';
import 'event_detail_screen.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  late DateTime _focusedDay;
  late DateTime _selectedDay;
  late PageController _pageController;
  bool _isSearching = false;
  final int _initialPage = 1200;

  @override
  void initState() {
    super.initState();
    _focusedDay = DateTime.now();
    _selectedDay = DateTime.now();
    _pageController = PageController(initialPage: _initialPage);
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
        title: _isSearching
            ? TextField(
                autofocus: true,
                style: const TextStyle(color: Palette.text_primary),
                decoration: const InputDecoration(
                    hintText: "Search events...",
                    hintStyle: TextStyle(color: Palette.text_tertiary),
                    border: InputBorder.none),
              )
            : const Text("Calendar",
                style: TextStyle(
                    color: Palette.text_primary, fontWeight: FontWeight.bold)),
        centerTitle: true,
        actions: [
          IconButton(
            onPressed: () => setState(() => _isSearching = !_isSearching),
            icon: Icon(_isSearching ? Icons.close : Icons.search, color: Palette.text_primary),
          ),
          IconButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const NotificationScreen())),
            icon: const Icon(Icons.notifications_none, color: Palette.text_primary),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Mese
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  DateFormat('MMMM yyyy').format(_focusedDay),
                  style: const TextStyle(color: Palette.text_primary, fontSize: 26, fontWeight: FontWeight.bold),
                ),
                Row(
                  children: [
                    _buildNavCircle(Icons.chevron_left, () => _pageController.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut)),
                    const SizedBox(width: 8),
                    _buildNavCircle(Icons.chevron_right, () => _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut)),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 20),
            _buildDaysOfWeek(),
            const SizedBox(height: 12),

            // Griglia Calendario (Design Originale)
            SizedBox(
              height: 280,
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) {
                  setState(() {
                    DateTime now = DateTime.now();
                    _focusedDay = DateTime(now.year, now.month + (index - _initialPage), 1);
                  });
                },
                itemBuilder: (context, index) {
                  DateTime now = DateTime.now();
                  return _buildCalendarGrid(DateTime(now.year, now.month + (index - _initialPage), 1));
                },
              ),
            ),

            const SizedBox(height: 10),
            _buildLegend(),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Events", style: TextStyle(color: Palette.text_primary, fontSize: 18, fontWeight: FontWeight.bold)),
                GestureDetector(
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const AllEventsScreen())),
                  child: const Text("See All", style: TextStyle(color: Palette.primary, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            Column(
              children: dummyEvents.isEmpty 
                ? [
                    const SizedBox(height: 20),
                    const Center(
                      child: Text("No events today", 
                        style: TextStyle(color: Palette.text_tertiary, fontSize: 14))
                    )
                  ]
                : dummyEvents.map((event) => _buildEventCard(event)).toList(),
            ),
            
            const SizedBox(height: 100),
          ],
        ),
      ),
    );
  }

  // --- WIDGETS CON IL TUO DESIGN ---

  Widget _buildNavCircle(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(color: Palette.background_secondary, shape: BoxShape.circle),
        child: Icon(icon, color: Palette.primary, size: 24),
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
        crossAxisCount: 7, mainAxisSpacing: 8, crossAxisSpacing: 8,
      ),
      itemBuilder: (context, index) {
        int dayNumber = index - firstDayOffset + 1;
        if (dayNumber < 1 || dayNumber > daysInMonth) return const SizedBox();

        DateTime currentDateTime = DateTime(month.year, month.month, dayNumber);
        bool isSelected = DateUtils.isSameDay(_selectedDay, currentDateTime);
        bool isToday = DateUtils.isSameDay(DateTime.now(), currentDateTime);

        return GestureDetector(
          onTap: () => setState(() => _selectedDay = currentDateTime),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              color: isSelected ? Palette.primary : Palette.background_secondary.withOpacity(0.3),
              borderRadius: BorderRadius.circular(12),
              border: isToday && !isSelected
                  ? Border.all(color: Palette.primary, width: 1.5)
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

  Widget _buildEventCard(Event event) {
    return GestureDetector(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => EventDetailScreen(event: event))),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Palette.background_secondary, borderRadius: BorderRadius.circular(20)),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: event.color.withOpacity(0.1), borderRadius: BorderRadius.circular(14)),
              child: Icon(event.icon, color: event.color, size: 22),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(event.title, style: const TextStyle(color: Palette.text_primary, fontSize: 15, fontWeight: FontWeight.bold)),
                  Text(event.time, style: const TextStyle(color: Palette.text_tertiary, fontSize: 12)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Palette.text_tertiary, size: 20),
          ],
        ),
      ),
    );
  }
}