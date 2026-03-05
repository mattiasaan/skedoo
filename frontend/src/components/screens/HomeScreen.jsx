import { useState } from "react";
import { COLORS } from "../../constants/colors";
import { todaySchedule, upNextClass, lastMinuteAlert } from "../../data/schedule";
import Icon from "../ui/Icon";

/* Maps a lesson status to its visual tokens */
const STATUS_STYLE = {
  completed: {
    bg:          "transparent",
    border:      COLORS.border,
    text:        COLORS.textDim,
    badge:       "#2a4a2a",
    badgeText:   COLORS.greenLight,
    dot:         COLORS.textDim,
    label:       "COMPLETED",
  },
  ongoing: {
    bg:          `${COLORS.green}15`,
    border:      COLORS.green,
    text:        COLORS.text,
    badge:       COLORS.green,
    badgeText:   "white",
    dot:         COLORS.greenAccent,
    label:       "ONGOING",
  },
  upcoming: {
    bg:          "transparent",
    border:      COLORS.border,
    text:        COLORS.textMuted,
    badge:       "transparent",
    badgeText:   COLORS.textDim,
    dot:         COLORS.textDim,
    label:       "Upcoming",
  },
};

export default function HomeScreen() {
  const [dismissed, setDismissed] = useState(false);

  return (
    <div className="anim-fadeIn" style={{ flex: 1, overflowY: "auto", padding: "24px 20px" }}>

      {/* ── Header ──────────────────────────────── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={avatarStyle}>A</div>
          <div>
            <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: "-0.3px" }}>
              Hi, Alex! 👋
            </h2>
            <p style={{ margin: 0, color: COLORS.textMuted, fontSize: 13 }}>Monday, Oct 24</p>
          </div>
        </div>

        {/* Bell with red dot */}
        <div style={{ position: "relative" }}>
          <div style={bellBtnStyle}>
            <Icon name="bell" size={20} color={COLORS.textMuted} />
          </div>
          <div style={bellDotStyle} />
        </div>
      </div>

      {/* ── Alert Banner ────────────────────────── */}
      {!dismissed && (
        <div className="anim-slideIn" style={alertStyle}>
          <Icon name="info" size={18} color={COLORS.greenLight} />
          <div style={{ flex: 1 }}>
            <p style={{ margin: "0 0 4px", fontWeight: 700, fontSize: 14 }}>{lastMinuteAlert.title}</p>
            <p style={{ margin: 0, fontSize: 13, color: COLORS.textMuted, lineHeight: 1.5 }}>{lastMinuteAlert.body}</p>
          </div>
          <button onClick={() => setDismissed(true)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}>
            <Icon name="x" size={18} color={COLORS.textDim} />
          </button>
        </div>
      )}

      {/* ── Up Next ─────────────────────────────── */}
      <SectionLabel>Up Next</SectionLabel>
      <UpNextCard lesson={upNextClass} />

      {/* ── Today's Schedule ────────────────────── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <SectionLabel inline>Today's Schedule</SectionLabel>
        <span style={{ color: COLORS.greenLight, fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
          VIEW CALENDAR
        </span>
      </div>

      <ScheduleTimeline items={todaySchedule} />
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function SectionLabel({ children, inline = false }) {
  return (
    <p style={{
      color:         COLORS.textDim,
      fontSize:      12,
      fontWeight:    700,
      letterSpacing: "1.5px",
      marginBottom:  10,
      textTransform: "uppercase",
      display:       inline ? "inline" : "block",
    }}>
      {children}
    </p>
  );
}

function UpNextCard({ lesson }) {
  return (
    <div style={upNextCardStyle}>
      {/* decorative bubble */}
      <div style={{ position: "absolute", top: -30, right: -30, width: 120, height: 120, background: `${COLORS.green}20`, borderRadius: "50%", pointerEvents: "none" }} />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div>
          <p style={{ margin: "0 0 4px", fontSize: 11, fontWeight: 700, color: COLORS.greenAccent, letterSpacing: "1px", textTransform: "uppercase" }}>
            {lesson.category}
          </p>
          <h3 style={{ margin: 0, fontSize: 28, fontWeight: 800, letterSpacing: "-0.5px" }}>
            {lesson.subject}
          </h3>
        </div>
        <div style={roomBadgeStyle}>
          <p style={{ margin: 0, fontSize: 10, fontWeight: 600, color: COLORS.textMuted, letterSpacing: "1px" }}>ROOM</p>
          <p style={{ margin: 0, fontSize: 26, fontWeight: 900, color: "white" }}>{lesson.room}</p>
        </div>
      </div>

      <div style={{ display: "flex", gap: 20, marginBottom: 16 }}>
        <MetaItem icon="clock"  text={`${lesson.timeStart} – ${lesson.timeEnd}`} />
        <MetaItem icon="mapPin" text={lesson.building} />
      </div>

      {lesson.hasMeeting && (
        <button
          style={joinBtnStyle}
          onMouseEnter={e => e.currentTarget.style.transform = "scale(1.02)"}
          onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
        >
          Join Online Meeting
        </button>
      )}
    </div>
  );
}

function MetaItem({ icon, text }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <Icon name={icon} size={15} color={COLORS.greenAccent} />
      <span style={{ fontSize: 13, color: COLORS.textMuted }}>{text}</span>
    </div>
  );
}

function ScheduleTimeline({ items }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {items.map((item) => {
        const s = STATUS_STYLE[item.status] || STATUS_STYLE.upcoming;
        return (
          <div key={item.id} style={{ display: "flex", gap: 14, alignItems: "stretch" }}>
            {/* dot + line */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 16 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: s.dot, flexShrink: 0 }} />
              <div style={{ width: 1, flex: 1, background: COLORS.border, margin: "4px 0" }} />
            </div>

            {/* card */}
            <div style={{
              flex:         1,
              background:   s.bg,
              border:       `1px solid ${s.border}`,
              borderRadius: 14,
              padding:      "14px 16px",
              marginBottom: 8,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: COLORS.textDim }}>{item.time}</span>
                {item.status !== "upcoming" ? (
                  <span style={{ background: s.badge, color: s.badgeText, fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6, letterSpacing: "0.5px", textTransform: "uppercase" }}>
                    {s.label}
                  </span>
                ) : (
                  <span style={{ color: COLORS.textDim, fontSize: 12 }}>Upcoming</span>
                )}
              </div>
              <p style={{ margin: "0 0 2px", fontWeight: 700, fontSize: 16, color: s.text }}>{item.subject}</p>
              <p style={{ margin: 0, fontSize: 13, color: COLORS.textDim }}>{item.room} · {item.teacher}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Style objects ───────────────────────────────────────────────────────── */
const avatarStyle = {
  width:          48,
  height:         48,
  borderRadius:   "50%",
  background:     `linear-gradient(135deg, ${COLORS.green}, #1a4a2a)`,
  display:        "flex",
  alignItems:     "center",
  justifyContent: "center",
  fontSize:       18,
  fontWeight:     700,
  border:         `2px solid ${COLORS.green}`,
};

const bellBtnStyle = {
  width:          42,
  height:         42,
  background:     COLORS.bgCard,
  borderRadius:   12,
  border:         `1px solid ${COLORS.border}`,
  display:        "flex",
  alignItems:     "center",
  justifyContent: "center",
  cursor:         "pointer",
};

const bellDotStyle = {
  position:   "absolute",
  top:        6,
  right:      6,
  width:      10,
  height:     10,
  background: COLORS.red,
  borderRadius: "50%",
  border:     `2px solid ${COLORS.bg}`,
};

const alertStyle = {
  background:    `${COLORS.green}20`,
  border:        `1px solid ${COLORS.green}50`,
  borderRadius:  14,
  padding:       "14px 16px",
  marginBottom:  24,
  display:       "flex",
  alignItems:    "flex-start",
  gap:           12,
};

const upNextCardStyle = {
  background:    `linear-gradient(135deg, ${COLORS.greenDark}, #163825)`,
  borderRadius:  20,
  padding:       "22px",
  marginBottom:  28,
  position:      "relative",
  overflow:      "hidden",
  boxShadow:     `0 8px 32px ${COLORS.green}30`,
};

const roomBadgeStyle = {
  background:      "rgba(0,0,0,0.3)",
  borderRadius:    12,
  padding:         "10px 14px",
  textAlign:       "center",
  backdropFilter:  "blur(8px)",
};

const joinBtnStyle = {
  width:        "100%",
  background:   "white",
  border:       "none",
  borderRadius: 12,
  padding:      "13px",
  color:        COLORS.greenDark,
  fontSize:     15,
  fontWeight:   700,
  cursor:       "pointer",
  transition:   "transform 0.15s",
};
