import { BookOpen, CalendarDays, GraduationCap, Home, User } from "lucide-react";
import { NavLink } from "react-router-dom";
import "./BottomNav.css";

// Per aggiungere una voce: una riga qui e la <Route> in App.jsx
const ITEMS = [
  { to: "/", label: "Home", icon: Home },
  { to: "/orario", label: "Orario", icon: CalendarDays },
  { to: "/voti", label: "Voti", icon: GraduationCap },
  { to: "/agenda", label: "Agenda", icon: BookOpen },
  { to: "/profilo", label: "Profilo", icon: User },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Navigazione principale">
      {ITEMS.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => "bottom-nav__item" + (isActive ? " is-active" : "")}>
          <Icon size={22} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
