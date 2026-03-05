export const todaySchedule = [
  {
    id: 1,
    time: "08:00 - 09:30",
    subject: "English Literature",
    room: "Room 104",
    teacher: "Dr. Bennett",
    status: "completed",
  },
  {
    id: 2,
    time: "10:30 - 11:45",
    subject: "Mathematics",
    room: "Room 302",
    teacher: "Prof. Schmidt",
    status: "ongoing",
  },
  {
    id: 3,
    time: "13:00 - 14:30",
    subject: "Modern History",
    room: "Room 201",
    teacher: "Dr. Henderson",
    status: "upcoming",
  },
  {
    id: 4,
    time: "14:45 - 16:00",
    subject: "Physics Lab",
    room: "Room 105",
    teacher: "Prof. Rossi",
    status: "upcoming",
  },
];

export const upNextClass = {
  subject:   "Linear Algebra",
  category:  "Mathematics • Calculus II",
  room:      "302",
  timeStart: "10:30 AM",
  timeEnd:   "11:45 AM",
  building:  "Forest Green Building",
  hasMeeting: true,
};

export const lastMinuteAlert = {
  title: "Last Minute Changes",
  body:  "Professor Rossi absent — Room 204 moved to 201 for today's Physics lab.",
};
