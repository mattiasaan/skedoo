import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../palette/palette.dart';
import '../../models/event_model.dart';

class AddEventScreen extends StatefulWidget {
  const AddEventScreen({super.key});

  @override
  State<AddEventScreen> createState() => _AddEventScreenState();
}

class _AddEventScreenState extends State<AddEventScreen> {
  final _titleController = TextEditingController();
  DateTime _selectedDate = DateTime.now();
  TimeOfDay _selectedTime = TimeOfDay.now();
  Color _selectedColor = Palette.primary;

  // Picker MD3 per la Data
  Future<void> _pickDate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 365 * 5)),
      builder: (context, child) => _buildPickerTheme(child!),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() => _selectedDate = picked);
    }
  }

  // Picker MD3 per l'Ora
  Future<void> _pickTime() async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: _selectedTime,
      builder: (context, child) => _buildPickerTheme(child!),
    );
    if (picked != null && picked != _selectedTime) {
      setState(() => _selectedTime = picked);
    }
  }

  // Applica i colori della tua Palette ai Picker MD3
  Widget _buildPickerTheme(Widget child) {
    return Theme(
      data: Theme.of(context).copyWith(
        colorScheme: const ColorScheme.dark(
          primary: Palette.primary,
          onPrimary: Colors.white,
          surface: Palette.background_secondary,
          onSurface: Palette.text_primary,
        ),
      ),
      child: child,
    );
  }

  void _saveAndClose() {
    if (_titleController.text.isEmpty) return;

    final newEvent = Event(
      id: DateTime.now().toString(),
      title: _titleController.text,
      date: _selectedDate,
      time: _selectedTime.format(context),
      color: _selectedColor,
      icon: Icons.circle,
    );

    dummyEvents.insert(0, newEvent); // Inserimento istantaneo in testa
    Navigator.pop(context, true); // Ritorna true per segnalare l'aggiunta
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Palette.text_primary),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Palette.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              ),
              onPressed: _saveAndClose,
              child: const Text("Save"),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            TextField(
              controller: _titleController,
              autofocus: true,
              style: const TextStyle(color: Palette.text_primary, fontSize: 26, fontWeight: FontWeight.w400),
              decoration: const InputDecoration(
                hintText: "Add title",
                hintStyle: TextStyle(color: Palette.text_tertiary),
                border: InputBorder.none,
              ),
            ),
            const SizedBox(height: 30),
            _buildMD3Row(Icons.access_time, DateFormat('EEEE, d MMM').format(_selectedDate), _pickDate),
            _buildMD3Row(Icons.schedule, _selectedTime.format(context), _pickTime),
            const Divider(height: 40, color: Palette.background_tertiary),
            _buildMD3Row(Icons.palette_outlined, "Color", _showColorPicker, trailing: CircleAvatar(radius: 10, backgroundColor: _selectedColor)),
            _buildMD3Row(Icons.segment, "Add description", () {}),
          ],
        ),
      ),
    );
  }

  Widget _buildMD3Row(IconData icon, String label, VoidCallback onTap, {Widget? trailing}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
        child: Row(
          children: [
            Icon(icon, color: Palette.text_tertiary, size: 24),
            const SizedBox(width: 18),
            Expanded(child: Text(label, style: const TextStyle(color: Palette.text_primary, fontSize: 16))),
            if (trailing != null) trailing,
          ],
        ),
      ),
    );
  }

  void _showColorPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Palette.background_secondary,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        height: 180,
        child: Wrap(
          spacing: 20, runSpacing: 20,
          children: [Palette.primary, Colors.blue, Colors.red, Colors.orange, Colors.purple].map((c) {
            return GestureDetector(
              onTap: () { setState(() => _selectedColor = c); Navigator.pop(context); },
              child: CircleAvatar(backgroundColor: c, radius: 25, child: _selectedColor == c ? const Icon(Icons.check, color: Colors.white) : null),
            );
          }).toList(),
        ),
      ),
    );
  }
}