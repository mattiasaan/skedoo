import { COLORS } from "../constants/colors";

/** Days that carry a coloured dot in the grid */
export const calendarDots = {
  5:  COLORS.greenAccent,
  10: COLORS.red,
  1:  COLORS.orange,
  6:  COLORS.blue,
};

/** @type {Record<number, CalendarEvent[]>} */
export const calendarEvents = {
  5: [
    {
      title: "Math Mid-term Test",
      time:  "09:00 AM - 10:30 AM",
      place: "Room 302",
      type:  "test",
    },
    {
      title: "Weekly School Assembly",
      time:  "11:00 AM - 12:00 PM",
      place: "Main Hall",
      type:  "assembly",
    },
    {
      title: "History Project Deadline",
      time:  "Due by 11:59 PM",
      place: "Online Submission",
      type:  "deadline",
    },
  ],
  10: [
    {
      title: "Physics Exam",
      time:  "09:00 AM - 11:00 AM",
      place: "Room 105",
      type:  "deadline",
    },
  ],
  1: [
    {
      title: "All Saints Day",
      time:  "All Day",
      place: "",
      type:  "holiday",
    },
  ],
  6: [
    {
      title: "Science Fair",
      time:  "14:00 - 17:00",
      place: "Gymnasium",
      type:  "assembly",
    },
  ],
};

export const calendarDays = [
  24, 25, 26, 27, 28, 29,  1,
   2,  3,  4,  5,  6,  7,  8,
   9, 10, 11, 12, 13, 14, 15,
  16, 17, 18, 19, 20, 21, 22,
];

export const DAYS_OF_WEEK = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

export const EVENT_TYPE_COLORS = {
  test:     COLORS.green,
  assembly: "#1a3a6a",
  deadline: "#6a1a1a",
  holiday:  "#6a4a1a",
};

export const EVENT_TYPE_ICONS = {
  test:     "tasks",
  assembly: "users",
  deadline: "flag",
  holiday:  "star",
};

export const LEGEND = [
  { label: "Tests",      color: COLORS.greenAccent },
  { label: "Deadlines",  color: COLORS.red         },
  { label: "Holidays",   color: COLORS.orange       },
  { label: "Assemblies", color: COLORS.blue         },
];
