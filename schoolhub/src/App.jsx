import { useState } from "react";
import { COLORS } from "./constants/colors";
import NavBar from "./components/ui/NavBar";
import LoginScreen    from "./components/screens/LoginScreen";
import HomeScreen     from "./components/screens/HomeScreen";
import CalendarScreen from "./components/screens/CalendarScreen";
import CommunityScreen from "./components/screens/CommunityScreen";
import ProfileScreen  from "./components/screens/ProfileScreen";

/**
 * Maps a tab id → the corresponding screen component.
 * Add new tabs here without touching the render logic below.
 */
const SCREENS = {
  home:      <HomeScreen />,
  schedule:  <CalendarScreen />,
  community: <CommunityScreen />,
};

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [activeTab,     setActiveTab]     = useState("home");

  if (!authenticated) {
    return <LoginScreen onLogin={() => setAuthenticated(true)} />;
  }

  const renderScreen = () => {
    if (activeTab === "profile") {
      return <ProfileScreen onLogout={() => setAuthenticated(false)} />;
    }
    return SCREENS[activeTab] ?? <HomeScreen />;
  };

  return (
    <div style={{
      background:    COLORS.bg,
      maxWidth:      480,
      margin:        "0 auto",
      minHeight:     "100vh",
      display:       "flex",
      flexDirection: "column",
      position:      "relative",
    }}>
      {/* Main content area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflowY: "hidden", minHeight: "calc(100vh - 72px)" }}>
        {renderScreen()}
      </div>

      {/* Bottom navigation */}
      <div style={{ position: "sticky", bottom: 0 }}>
        <NavBar active={activeTab} onNavigate={setActiveTab} />
      </div>
    </div>
  );
}
