import 'package:flutter/material.dart';

class Event {
  String id;
  String title;
  DateTime date;
  String time;
  IconData icon;
  Color color;
  String description;

  Event({
    required this.id,
    required this.title,
    required this.date,
    required this.time,
    this.icon = Icons.event,
    this.color = Colors.green,
    this.description = "No description provided.",
  });
}

  List<Event> dummyEvents = [];