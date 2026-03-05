import { COLORS } from "../constants/colors";

export const communityPosts = [
  {
    id:       1,
    author:   "Marco T.",
    avatar:   "MT",
    time:     "2h ago",
    text:     "Anyone has notes from today's Physics lesson? Prof. Rossi changed room at the last minute 😅",
    likes:    12,
    comments: 4,
    tags:     ["Physics", "Notes"],
  },
  {
    id:       2,
    author:   "Sofia R.",
    avatar:   "SR",
    time:     "5h ago",
    text:     "The Math midterm went better than expected! The second part about linear transformations was actually pretty fair.",
    likes:    28,
    comments: 9,
    tags:     ["Math", "Midterm"],
  },
  {
    id:       3,
    author:   "Luca B.",
    avatar:   "LB",
    time:     "1d ago",
    text:     "Reminder: History project deadline is tonight at 11:59 PM. Don't forget to submit online!",
    likes:    45,
    comments: 2,
    tags:     ["History", "Deadline", "Important"],
  },
  {
    id:       4,
    author:   "Giulia M.",
    avatar:   "GM",
    time:     "1d ago",
    text:     "Study group for Physics tomorrow at 16:00 in the library. Everyone welcome! 📚",
    likes:    19,
    comments: 7,
    tags:     ["Physics", "StudyGroup"],
  },
];

/** Maps a tag name to its highlight colour */
export const TAG_COLORS = {
  Physics:    COLORS.blue,
  Math:       COLORS.green,
  History:    COLORS.orange,
  Notes:      "#5a3a8a",
  Midterm:    COLORS.red,
  Deadline:   COLORS.red,
  Important:  COLORS.red,
  StudyGroup: COLORS.green,
};

export const classLeaderboard = {
  className: "Class 3A",
  rank:      2,
  points:    720,
  progress:  0.72,   // 0–1
};
