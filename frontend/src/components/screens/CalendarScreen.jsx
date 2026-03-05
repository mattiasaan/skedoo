import { useState } from "react";
import { COLORS } from "../../constants/colors";
import {
  calendarDays,
  calendarDots,
  calendarEvents,
  DAYS_OF_WEEK,
  EVENT_TYPE_COLORS,
  EVENT_TYPE_ICONS,
  LEGEND,
} from "../../data/calendar";
import Icon from "../ui/Icon";

export default function CalendarScreen() {
  const [selectedDay,   setSelectedDay]   = useState(5);
  const [currentMonth]                    = useState({ month: "October", year: 2023 });

  const events = calendarEvents[selectedDay] || [];

  return (
    <div className="anim-fadeIn" style={{ flex: 1, overflowY: "auto" }}>

      {/* ── Top Bar ─────────────────────────────── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 20px 0" }}>
        <button style={iconBtnStyle}><Icon name="menu"   size={22} color={COLORS.textMuted} /></button>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Calendar</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={iconBtnStyle}><Icon name="search" size={22} color={COLORS.textMuted} /></button>
          <button style={{ ...iconBtnStyle, position: "relative" }}>
            <Icon name="bell" size={22} color={COLORS.textMuted} />
            <div style={bellDotStyle} />
          </button>
        </div>
      </div>

      <div style={{ padding: "20px" }}>

        {/* ── Month Header ────────────────────────── */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ margin: 0, fontSize: 24, fontWeight: 800, letterSpacing: "-0.3px" }}>
            {currentMonth.month} {currentMonth.year}
          </h3>
          <div style={{ display: "flex", gap: 6 }}>
            <NavArrow icon="chevronLeft"  />
            <NavArrow icon="chevronRight" />
          </div>
        </div>

        {/* ── Calendar Grid ───────────────────────── */}
        <CalendarGrid
          days={calendarDays}
          dots={calendarDots}
          selectedDay={selectedDay}
          onSelectDay={setSelectedDay}
        />

        {/* ── Legend ──────────────────────────────── */}
        <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
          {LEGEND.map(l => (
            <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: l.color }} />
              <span style={{ fontSize: 12, color: COLORS.textMuted }}>{l.label}</span>
            </div>
          ))}
        </div>

        {/* ── Events ──────────────────────────────── */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <h4 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>
            {events.length > 0 ? "Today's Events" : `Events for ${selectedDay}`}
          </h4>
          <span style={{ color: COLORS.greenLight, fontSize: 13, fontWeight: 600, cursor: "pointer" }}>See All</span>
        </div>

        {events.length === 0 ? (
          <EmptyEvents />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {events.map((ev, i) => <EventCard key={i} event={ev} />)}
          </div>
        )}
      </div>

      {/* ── FAB ─────────────────────────────────── */}
      <FabButton />
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function CalendarGrid({ days, dots, selectedDay, onSelectDay }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 2, marginBottom: 16 }}>
      {/* Day-of-week headers */}
      {DAYS_OF_WEEK.map(d => (
        <div key={d} style={{ textAlign: "center", fontSize: 11, fontWeight: 700, color: COLORS.textDim, padding: "4px 0 10px", letterSpacing: "0.5px" }}>
          {d}
        </div>
      ))}

      {/* Day cells */}
      {days.map((day, i) => {
        const isSelected = day === selectedDay;
        const dotColor   = dots[day];
        const isPast     = i < 11;   // first 11 days belong to prev month week

        return (
          <div key={i} onClick={() => onSelectDay(day)} style={{ textAlign: "center", padding: "6px 2px 10px", cursor: "pointer", position: "relative", borderRadius: 10 }}>
            <div style={{
              width:          36,
              height:         36,
              borderRadius:   10,
              background:     isSelected ? COLORS.green : "transparent",
              display:        "flex",
              alignItems:     "center",
              justifyContent: "center",
              margin:         "0 auto",
              transition:     "background 0.2s",
            }}>
              <span style={{ fontSize: 15, fontWeight: isSelected ? 800 : 500, color: isSelected ? "white" : isPast ? COLORS.textDim : COLORS.text }}>
                {day}
              </span>
            </div>
            {dotColor && (
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: dotColor, margin: "3px auto 0" }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function EventCard({ event }) {
  const bg   = EVENT_TYPE_COLORS[event.type] || COLORS.bgCard;
  const icon = EVENT_TYPE_ICONS[event.type]  || "info";

  return (
    <div
      style={{ background: bg, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "16px", display: "flex", alignItems: "center", gap: 14, cursor: "pointer", transition: "transform 0.15s" }}
      onMouseEnter={e => e.currentTarget.style.transform = "translateX(4px)"}
      onMouseLeave={e => e.currentTarget.style.transform = "translateX(0)"}
    >
      <div style={{ width: 44, height: 44, borderRadius: 12, background: "rgba(0,0,0,0.3)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <Icon name={icon} size={20} color="white" />
      </div>
      <div style={{ flex: 1 }}>
        <p style={{ margin: "0 0 3px", fontWeight: 700, fontSize: 15 }}>{event.title}</p>
        <p style={{ margin: 0, fontSize: 12, color: COLORS.textMuted }}>
          {event.time}{event.place ? ` · ${event.place}` : ""}
        </p>
      </div>
      <Icon name="chevronRight" size={18} color={COLORS.textDim} />
    </div>
  );
}

function EmptyEvents() {
  return (
    <div style={{ textAlign: "center", padding: "40px 20px", color: COLORS.textDim }}>
      <Icon name="calendar" size={40} color={COLORS.textDim} />
      <p style={{ marginTop: 12, fontSize: 14 }}>No events on this day</p>
    </div>
  );
}

function NavArrow({ icon }) {
  return (
    <button style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 8, width: 32, height: 32, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <Icon name={icon} size={18} color={COLORS.greenLight} />
    </button>
  );
}

function FabButton() {
  return (
    <div style={{ position: "fixed", bottom: 72, right: 24 }}>
      <button
        style={{ width: 54, height: 54, borderRadius: "50%", background: `linear-gradient(135deg, ${COLORS.green}, ${COLORS.greenDark})`, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 4px 20px ${COLORS.green}60`, transition: "transform 0.15s" }}
        onMouseEnter={e => e.currentTarget.style.transform = "scale(1.1)"}
        onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
      >
        <Icon name="plus" size={24} color="white" />
      </button>
    </div>
  );
}

/* ── Style objects ───────────────────────────────────────────────────────── */
const iconBtnStyle = {
  background: "none",
  border:     "none",
  cursor:     "pointer",
  padding:    0,
};

const bellDotStyle = {
  position:     "absolute",
  top:          2,
  right:        2,
  width:        8,
  height:       8,
  background:   COLORS.red,
  borderRadius: "50%",
  border:       `2px solid ${COLORS.bg}`,
};
