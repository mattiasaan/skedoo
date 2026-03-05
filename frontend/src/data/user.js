import { COLORS } from "../constants/colors";

export const currentUser = {
  name:        "Alex Marchetti",
  nickname:    "alex.m",
  class:       "Class 3A",
  classeVivaId: "2024-3A-012",
  avatarLetter: "A",
};

export const userStats = [
  { label: "Attendance", value: "96%",   color: COLORS.greenAccent },
  { label: "Points",     value: "1,240", color: COLORS.orange      },
  { label: "Streak",     value: "14d",   color: COLORS.blue        },
];

export const achievements = [
  {
    icon:     "zap",
    label:    "Early Bird",
    desc:     "Logged in 7 days in a row",
    color:    COLORS.orange,
    unlocked: true,
  },
  {
    icon:     "star",
    label:    "Top Student",
    desc:     "Highest attendance this month",
    color:    COLORS.greenAccent,
    unlocked: true,
  },
  {
    icon:     "shield",
    label:    "Streak Master",
    desc:     "30-day login streak",
    color:    COLORS.blue,
    unlocked: false,
  },
  {
    icon:     "trophy",
    label:    "Class Champion",
    desc:     "#1 in class leaderboard",
    color:    COLORS.orange,
    unlocked: false,
  },
];

export const settingsItems = [
  "Notifiche Push",
  "Tema Scuro",
  "Lingua: Italiano",
  "Privacy",
];
