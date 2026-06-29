// screens/calendar.dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; 
import '../main_layout.dart'; 

enum CalendarViewMode { day, week, month }

class Calendar extends StatefulWidget {
  const Calendar({super.key});

  @override
  State<Calendar> createState() => _CalendarState();
}

class _CalendarState extends State<Calendar> {
  late DateTime _focusedMonth; 
  late DateTime _selectedDay; 
  CalendarViewMode _currentMode = CalendarViewMode.month; 

  @override
  void initState() {
    super.initState();
    // Imposta automaticamente la giornata odierna all'apertura
    final now = DateTime.now();
    _focusedMonth = DateTime(now.year, now.month, 1);
    _selectedDay = DateTime(now.year, now.month, now.day);
  }

  // Funzione di navigazione per le frecce < e > adattiva in base alla modalità
  void _navigatePrevious() {
    setState(() {
      if (_currentMode == CalendarViewMode.day) {
        _selectedDay = _selectedDay.subtract(const Duration(days: 1));
        _focusedMonth = DateTime(_selectedDay.year, _selectedDay.month, 1);
      } else {
        _focusedMonth = DateTime(_focusedMonth.year, _focusedMonth.month - 1, 1);
        // Nella vista week, se cambiamo mese arretriamo la settimana di partenza
        if (_currentMode == CalendarViewMode.week) {
          _selectedDay = _selectedDay.subtract(const Duration(days: 7));
        }
      }
    });
  }

  void _navigateNext() {
    setState(() {
      if (_currentMode == CalendarViewMode.day) {
        _selectedDay = _selectedDay.add(const Duration(days: 1));
        _focusedMonth = DateTime(_selectedDay.year, _selectedDay.month, 1);
      } else {
        _focusedMonth = DateTime(_focusedMonth.year, _focusedMonth.month + 1, 1);
        if (_currentMode == CalendarViewMode.week) {
          _selectedDay = _selectedDay.add(const Duration(days: 7));
        }
      }
    });
  }

  int _daysInMonth(DateTime date) {
    return DateTime(date.year, date.month + 1, 0).day;
  }

  int _firstDayOffset(DateTime date) {
    int weekday = DateTime(date.year, date.month, 1).weekday;
    if (weekday == 7) return 0;
    return weekday; 
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0F0F),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
              child: Column(
                children: [
                  _buildHeader(context),
                  const SizedBox(height: 20),
                  _buildViewSelector(), 
                  const SizedBox(height: 24),
                  _buildMonthNavigation(),
                ],
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20.0),
                child: _buildBodyContent(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBodyContent() {
    switch (_currentMode) {
      case CalendarViewMode.day:
        return _buildGoogleCalendarDayView();
      case CalendarViewMode.week:
        return _buildWeeklyView();
      case CalendarViewMode.month:
        return Column(
          children: [
            _buildWeekDaysHeader(),
            const SizedBox(height: 8),
            _buildCalendarGrid(),
            const SizedBox(height: 16),
            _buildLegend(),
            const SizedBox(height: 28),
            _buildEventsSection(),
          ],
        );
    }
  }

  // 1. TOP APP BAR
  Widget _buildHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        IconButton(
          icon: const Icon(Icons.menu, color: Colors.white, size: 32),
          onPressed: () => customScaffoldKey.currentState?.openDrawer(),
        ),
        const Text(
          'Calendar',
          style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
        ),
        Row(
          children: [
            IconButton(icon: const Icon(Icons.search, color: Colors.white, size: 28), onPressed: () {}),
            IconButton(icon: const Icon(Icons.notifications_none, color: Colors.white, size: 28), onPressed: () {Navigator.pushNamed(context, '/notifications');}),
          ],
        ),
      ],
    );
  }

  // 2. SLIDEBAR / SELETTORE VISTA
  Widget _buildViewSelector() {
    return Center(
      child: SizedBox(
        width: double.infinity,
        child: SegmentedButton<CalendarViewMode>(
          style: SegmentedButton.styleFrom(
            backgroundColor: const Color(0xFF121818),
            selectedBackgroundColor: const Color(0xFF0E5434), 
            selectedForegroundColor: Colors.white,
            foregroundColor: Colors.white60,
            side: BorderSide(color: const Color(0xFF1B3D33).withOpacity(0.5)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
          segments: const <ButtonSegment<CalendarViewMode>>[
            ButtonSegment<CalendarViewMode>(value: CalendarViewMode.day, label: Text('Day')),
            ButtonSegment<CalendarViewMode>(value: CalendarViewMode.week, label: Text('Week')),
            ButtonSegment<CalendarViewMode>(value: CalendarViewMode.month, label: Text('Month')),
          ],
          selected: <CalendarViewMode>{_currentMode},
          onSelectionChanged: (Set<CalendarViewMode> newSelection) {
            setState(() {
              _currentMode = newSelection.first;
            });
          },
        ),
      ),
    );
  }

  // 3. NAVIGAZIONE DINAMICA E TESTO VARIABILE + DATE PICKER UNIFICATO
  Widget _buildMonthNavigation() {
    // Se siamo in "Day" mostra ad esempio "October 5, 2023", altrimenti il classico "October 2023"
    String textToShow = _currentMode == CalendarViewMode.day
        ? DateFormat('MMMM d, yyyy').format(_selectedDay)
        : DateFormat('MMMM yyyy').format(_focusedMonth);

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        InkWell(
          onTap: () async {
            final DateTime? picked = await showDatePicker(
              context: context,
              initialDate: _selectedDay,
              firstDate: DateTime(2020),
              lastDate: DateTime(2030),
              builder: (context, child) {
                return Theme(
                  data: Theme.of(context).copyWith(
                    colorScheme: const ColorScheme.dark(
                      primary: Color(0xFF10B981),       
                      onPrimary: Colors.white,          
                      surface: Color(0xFF121818),       
                      onSurface: Colors.white,          
                    ),
                  ),
                  child: child!,
                );
              },
            );

            if (picked != null) {
              setState(() {
                _selectedDay = picked;
                _focusedMonth = DateTime(picked.year, picked.month, 1);
              });
            }
          },
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4.0, horizontal: 8.0),
            child: Row(
              children: [
                Text(
                  textToShow,
                  style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(width: 6),
                const Icon(Icons.arrow_drop_down, color: Colors.white70, size: 28),
              ],
            ),
          ),
        ),
        Row(
          children: [
            IconButton(
              icon: const Icon(Icons.chevron_left, color: Color(0xFF10B981), size: 30),
              onPressed: _navigatePrevious,
            ),
            IconButton(
              icon: const Icon(Icons.chevron_right, color: Color(0xFF10B981), size: 30),
              onPressed: _navigateNext,
            ),
          ],
        )
      ],
    );
  }

  // ================= VISTA SETTIMANA GENERATA DINAMICAMENTE =================
  Widget _buildWeeklyView() {
    // Genera i 6 giorni consecutivi partendo dal lunedì della settimana del giorno selezionato (o dal giorno selezionato stesso)
    List<DateTime> weekDates = [];
    DateTime startDay = _selectedDay.subtract(Duration(days: _selectedDay.weekday - 1)); // Inizia da Lunedì

    for (int i = 0; i < 6; i++) {
      weekDates.add(startDay.add(Duration(days: i)));
    }

    return Column(
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: weekDates.map((date) {
              bool isSelected = date.day == _selectedDay.day && date.month == _selectedDay.month && date.year == _selectedDay.year;
              String dayName = DateFormat('E').format(date).toUpperCase(); // MON, TUE...

              return GestureDetector(
                onTap: () {
                  setState(() {
                    _selectedDay = date;
                    _focusedMonth = DateTime(date.year, date.month, 1);
                  });
                },
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: 65,
                  height: 75,
                  decoration: BoxDecoration(
                    color: isSelected ? const Color(0xFF0E5434) : const Color(0xFF121818),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: isSelected ? const Color(0xFF10B981) : Colors.white10),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(dayName, style: TextStyle(color: isSelected ? const Color(0xFF10B981) : Colors.white38, fontSize: 12, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text('${date.day}', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 24),
        // Mostra i corsi specifici filtrati in base al giorno selezionato
        _buildWeeklyEventsForSelectedDay(),
      ],
    );
  }

  // Rende condizionale la lista degli eventi in base al giorno cliccato per testare la schedule
  Widget _buildWeeklyEventsForSelectedDay() {
    // Semplice esempio di differenziazione per vedere il cambio della schedule al click
    if (_selectedDay.weekday == DateTime.monday || _selectedDay.day % 2 == 0) {
      return Column(
        children: [
          _buildWeeklyTimelineCard('08:00', 'Advanced Mathematics', '08:00 AM - 09:30 AM', 'Room 302', 'Prof. Recla', 'CORE', null),
          _buildWeeklyTimelineCard('10:00', 'Physics II', '10:15 AM - 11:45 AM', 'Lab B (Sub)', 'Dr. Miller', null, 'NOTE: ROOM CHANGED FOR EQUIPMENT MAINTENANCE', leftBorderColor: Colors.amber),
          _buildWeeklyTimelineCard('13:00', 'Digital Arts', '01:00 PM - 02:30 PM', 'Studio 1', 'Ms. Lane', 'ELECTIVE', null),
        ],
      );
    } else {
      return Column(
        children: [
          _buildWeeklyTimelineCard('09:00', 'History Lecture', '09:00 AM - 10:30 AM', 'Room 104', 'Prof. Bianchi', 'CORE', null),
          _buildWeeklyTimelineCard('11:00', 'Sistemi e Reti Cisco', '11:00 AM - 01:00 PM', 'Lab Info', 'Prof. Recla', 'CORE', 'NOTE: REVISIONE PROGETTO IN CLASSE', leftBorderColor: Colors.green),
          _buildWeeklyTimelineCard('15:00', 'Study Hall', '03:00 PM - 04:00 PM', 'Library', 'Self-guided', null, null),
        ],
      );
    }
  }

  Widget _buildWeeklyTimelineCard(String hour, String title, String time, String location, String instructor, String? tag, String? note, {Color leftBorderColor = Colors.transparent}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 50,
            padding: const EdgeInsets.only(top: 4),
            child: Text(hour, style: const TextStyle(color: Colors.white38, fontWeight: FontWeight.bold)),
          ),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF121818),
                borderRadius: BorderRadius.circular(16),
                border: Border(left: BorderSide(color: leftBorderColor, width: leftBorderColor != Colors.transparent ? 4 : 0)),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(child: Text(title, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold))),
                      if (tag != null)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: const Color(0xFF0E5434).withOpacity(0.3), borderRadius: BorderRadius.circular(6)),
                          child: Text(tag, style: const TextStyle(color: Color(0xFF10B981), fontSize: 10, fontWeight: FontWeight.bold)),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.access_time, color: Colors.white38, size: 16),
                      const SizedBox(width: 6),
                      Text(time, style: const TextStyle(color: Colors.white60, fontSize: 13)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(children: [const Icon(Icons.meeting_room_outlined, color: Colors.white38, size: 16), const SizedBox(width: 6), Text(location, style: const TextStyle(color: Colors.white60))]),
                      Row(children: [const Icon(Icons.person_outline, color: Colors.white38, size: 16), const SizedBox(width: 6), Text(instructor, style: const TextStyle(color: Colors.white60))]),
                    ],
                  ),
                  if (note != null) ...[
                    const Divider(color: Colors.white10, height: 20),
                    Text(note, style: const TextStyle(color: Colors.orange, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.3)),
                  ]
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ================= VISTA GIORNO (Google Calendar Style) =================
  Widget _buildGoogleCalendarDayView() {
    bool hasEvents = _selectedDay.day % 2 == 0; // Alterna la visualizzazione degli slot per il test

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: List.generate(8, (index) {
        int currentHour = 8 + index; 
        String formatHour = '${currentHour.toString().padLeft(2, '0')}:00';
        
        return Container(
          height: 70,
          decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: Colors.white10, width: 0.5))),
          child: Row(
            children: [
              Container(
                width: 50,
                alignment: Alignment.topLeft,
                padding: const EdgeInsets.only(top: 8),
                child: Text(formatHour, style: const TextStyle(color: Colors.white38, fontSize: 12)),
              ),
              Expanded(
                child: hasEvents && currentHour == 9 
                    ? Container(
                        margin: const EdgeInsets.all(4),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(color: const Color(0xFF0E5434), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFF10B981))),
                        child: const Text('Math Mid-term Test', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                      )
                    : const SizedBox(),
              ),
            ],
          ),
        );
      }),
    );
  }

  // ================= METODI STRUTTURA MESE INVARIATI =================
  Widget _buildWeekDaysHeader() {
    final List<String> weekDays = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: weekDays.map((day) {
        return SizedBox(
          width: 40,
          child: Text(
            day,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Color(0xFF0E5434), fontSize: 12, fontWeight: FontWeight.bold),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildCalendarGrid() {
    int totalDays = _daysInMonth(_focusedMonth);
    int offset = _firstDayOffset(_focusedMonth);
    
    DateTime prevMonth = DateTime(_focusedMonth.year, _focusedMonth.month - 1, 1);
    int totalDaysPrevMonth = _daysInMonth(prevMonth);

    List<Widget> dayWidgets = [];

    for (int i = offset - 1; i >= 0; i--) {
      int dayNum = totalDaysPrevMonth - i;
      dayWidgets.add(_buildDayCell(dayNum, isCurrentMonth: false));
    }

    for (int i = 1; i <= totalDays; i++) {
      dayWidgets.add(_buildDayCell(i, isCurrentMonth: true));
    }

    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 7,
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      children: dayWidgets,
    );
  }

  Widget _buildDayCell(int day, {required bool isCurrentMonth}) {
    bool isSelected = isCurrentMonth && day == _selectedDay.day && _focusedMonth.month == _selectedDay.month && _focusedMonth.year == _selectedDay.year;
    
    List<Color> eventDots = [];
    if (day == 1) eventDots = [Colors.orange];
    if (day == 6) eventDots = [Colors.green, Colors.blue];
    if (day == 10) eventDots = [Colors.red];

    return GestureDetector(
      onTap: () {
        if (isCurrentMonth) {
          setState(() {
            _selectedDay = DateTime(_focusedMonth.year, _focusedMonth.month, day);
          });
        }
      },
      child: Container(
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF0E5434) : const Color(0xFF121818),
          shape: BoxShape.circle,
          border: isSelected ? Border.all(color: const Color(0xFF10B981), width: 1) : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '$day',
              style: TextStyle(
                color: isSelected ? Colors.white : (isCurrentMonth ? Colors.white : Colors.white24),
                fontSize: 16,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            if (eventDots.isNotEmpty && !isSelected) ...[
              const SizedBox(height: 2),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: eventDots.map((color) => Container(
                  margin: const EdgeInsets.symmetric(horizontal: 1),
                  width: 5,
                  height: 5,
                  decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                )).toList(),
              )
            ]
          ],
        ),
      ),
    );
  }

  Widget _buildLegend() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: [
        _buildLegendItem('Tests', Colors.green),
        _buildLegendItem('Deadlines', Colors.red),
        _buildLegendItem('Holidays', Colors.orange),
        _buildLegendItem('Assemblies', Colors.blue),
      ],
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(color: Colors.white60, fontSize: 12)),
      ],
    );
  }

  Widget _buildEventsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text("Today's Events", style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
            TextButton(onPressed: () {}, child: const Text('See All', style: TextStyle(color: Color(0xFF10B981)))),
          ],
        ),
        const SizedBox(height: 12),
        _buildEventCard('Math Mid-term Test', '09:00 AM - 10:30 AM • Room 302', Icons.calculate_outlined, Colors.green),
        const SizedBox(height: 12),
        _buildEventCard('Weekly School Assembly', '11:00 AM - 12:00 PM • Main Hall', Icons.groups_outlined, Colors.blue),
      ],
    );
  }

  Widget _buildEventCard(String title, String subtitle, IconData icon, Color color) {
    return Card.filled(
      color: const Color(0xFF121818),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
          child: Icon(icon, color: color),
        ),
        title: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4.0),
          child: Text(subtitle, style: const TextStyle(color: Colors.white60, fontSize: 13)),
        ),
        trailing: const Icon(Icons.chevron_right, color: Colors.white30),
      ),
    );
  }
}