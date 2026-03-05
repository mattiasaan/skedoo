import { COLORS } from "../../constants/colors";
import Icon from "./Icon";

const TABS = [
  { id: "home",      label: "Home",      icon: "home"     },
  { id: "schedule",  label: "Schedule",  icon: "calendar" },
  { id: "community", label: "Community", icon: "users"    },
  { id: "profile",   label: "Profile",   icon: "user"     },
];

export default function NavBar({ active, onNavigate }) {
  return (
    <nav style={{
      borderTop:      `1px solid ${COLORS.border}`,
      background:     COLORS.bg,
      display:        "flex",
      justifyContent: "space-around",
      padding:        "12px 0 8px",
    }}>
      {TABS.map((tab) => {
        const isActive = active === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onNavigate(tab.id)}
            style={{
              display:        "flex",
              flexDirection:  "column",
              alignItems:     "center",
              gap:            4,
              background:     "none",
              border:         "none",
              cursor:         "pointer",
              padding:        "4px 16px",
              borderRadius:   10,
              color:          isActive ? COLORS.greenAccent : COLORS.textDim,
              transition:     "color 0.2s",
            }}
          >
            <Icon name={tab.icon} size={22} color={isActive ? COLORS.greenAccent : COLORS.textDim} />
            <span style={{
              fontSize:    11,
              fontWeight:  isActive ? 700 : 500,
              letterSpacing: "0.3px",
              textTransform: "uppercase",
            }}>
              {tab.label}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
