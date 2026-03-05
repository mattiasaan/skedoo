import { COLORS } from "../../constants/colors";
import { currentUser, userStats, achievements, settingsItems } from "../../data/user";
import Icon from "../ui/Icon";

export default function ProfileScreen({ onLogout }) {
  return (
    <div className="anim-fadeIn" style={{ flex: 1, overflowY: "auto", padding: "24px 20px" }}>

      {/* ── Profile Hero ────────────────────────── */}
      <ProfileHero user={currentUser} />

      {/* ── Stats ───────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 28 }}>
        {userStats.map(s => (
          <div key={s.label} style={statCardStyle}>
            <p style={{ margin: "0 0 4px", fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</p>
            <p style={{ margin: 0, fontSize: 11, color: COLORS.textDim, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {s.label}
            </p>
          </div>
        ))}
      </div>

      {/* ── Achievements ────────────────────────── */}
      <SectionHeading>Achievements</SectionHeading>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 28 }}>
        {achievements.map(a => (
          <AchievementCard key={a.label} achievement={a} />
        ))}
      </div>

      {/* ── Settings ────────────────────────────── */}
      <SectionHeading>Settings</SectionHeading>
      <div style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 16, overflow: "hidden", marginBottom: 20 }}>
        {settingsItems.map((item, i) => (
          <SettingsRow key={item} label={item} hasBorder={i < settingsItems.length - 1} />
        ))}
      </div>

      {/* ── Logout ──────────────────────────────── */}
      <button
        onClick={onLogout}
        style={logoutBtnStyle}
        onMouseEnter={e => e.currentTarget.style.background = `${COLORS.red}25`}
        onMouseLeave={e => e.currentTarget.style.background = `${COLORS.red}15`}
      >
        Esci dall'account
      </button>

      <div style={{ height: 20 }} />
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function ProfileHero({ user }) {
  return (
    <div style={{ textAlign: "center", marginBottom: 28 }}>
      <div style={{ position: "relative", display: "inline-block", marginBottom: 16 }}>
        <div style={avatarStyle}>{user.avatarLetter}</div>
        <div style={verifiedBadgeStyle}>
          <Icon name="check" size={12} color="white" />
        </div>
      </div>
      <h2 style={{ margin: "0 0 4px", fontSize: 24, fontWeight: 800 }}>{user.name}</h2>
      <p style={{ margin: "0 0 4px", color: COLORS.textMuted, fontSize: 14 }}>@{user.nickname} · {user.class}</p>
      <p style={{ margin: 0, fontSize: 13, color: COLORS.textDim }}>ClasseViva ID: {user.classeVivaId}</p>
    </div>
  );
}

function AchievementCard({ achievement: a }) {
  return (
    <div style={{
      background:   COLORS.bgCard,
      border:       `1px solid ${a.unlocked ? a.color + "40" : COLORS.border}`,
      borderRadius: 14,
      padding:      "14px",
      display:      "flex",
      gap:          12,
      alignItems:   "center",
      opacity:      a.unlocked ? 1 : 0.5,
    }}>
      <div style={{ width: 38, height: 38, borderRadius: 10, background: `${a.color}20`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <Icon name={a.icon} size={18} color={a.color} />
      </div>
      <div>
        <p style={{ margin: "0 0 2px", fontWeight: 700, fontSize: 13 }}>{a.label}</p>
        <p style={{ margin: 0, fontSize: 11, color: COLORS.textDim, lineHeight: 1.3 }}>{a.desc}</p>
      </div>
    </div>
  );
}

function SettingsRow({ label, hasBorder }) {
  return (
    <div
      style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px", borderBottom: hasBorder ? `1px solid ${COLORS.border}` : "none", cursor: "pointer", transition: "background 0.2s" }}
      onMouseEnter={e => e.currentTarget.style.background = COLORS.bgCardHover}
      onMouseLeave={e => e.currentTarget.style.background = "transparent"}
    >
      <span style={{ fontSize: 15 }}>{label}</span>
      <Icon name="chevronRight" size={16} color={COLORS.textDim} />
    </div>
  );
}

function SectionHeading({ children }) {
  return (
    <h4 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: "1px" }}>
      {children}
    </h4>
  );
}

/* ── Style objects ───────────────────────────────────────────────────────── */
const avatarStyle = {
  width:          88,
  height:         88,
  borderRadius:   "50%",
  background:     `linear-gradient(135deg, ${COLORS.green}, #1a4a2a)`,
  display:        "flex",
  alignItems:     "center",
  justifyContent: "center",
  fontSize:       32,
  fontWeight:     800,
  border:         `3px solid ${COLORS.green}`,
  margin:         "0 auto",
};

const verifiedBadgeStyle = {
  position:       "absolute",
  bottom:         2,
  right:          2,
  width:          22,
  height:         22,
  background:     COLORS.green,
  borderRadius:   "50%",
  display:        "flex",
  alignItems:     "center",
  justifyContent: "center",
  border:         `2px solid ${COLORS.bg}`,
};

const statCardStyle = {
  background:   COLORS.bgCard,
  border:       `1px solid ${COLORS.border}`,
  borderRadius: 14,
  padding:      "14px",
  textAlign:    "center",
};

const logoutBtnStyle = {
  width:        "100%",
  background:   `${COLORS.red}15`,
  border:       `1px solid ${COLORS.red}40`,
  borderRadius: 14,
  padding:      "14px",
  color:        COLORS.red,
  fontSize:     15,
  fontWeight:   700,
  cursor:       "pointer",
  transition:   "background 0.2s",
};
