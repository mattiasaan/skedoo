// Elenco delle pagine dell'app. Per aggiungerne una: crea il file in pages/ e aggiungi una <Route> qui.
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import BottomNav from "./components/BottomNav";
import Agenda from "./pages/Agenda";
import ClassPicker from "./pages/ClassPicker";
import Grades from "./pages/Grades";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Schedule from "./pages/Schedule";

// Le pagine dentro questa route richiedono il login; senza si va a /login
function RequireLogin() {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? <Outlet /> : <Navigate to="/login" replace />;
}

// Pagine con la barra di navigazione in basso
function WithNav() {
  return (
    <div className="app">
      <Outlet />
      <BottomNav />
    </div>
  );
}

export default function App() {
  const { isLoggedIn } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={isLoggedIn ? <Navigate to="/" replace /> : <Login />} />

      <Route element={<RequireLogin />}>
        <Route path="/classe" element={<ClassPicker />} />
        <Route element={<WithNav />}>
          <Route path="/" element={<Home />} />
          <Route path="/orario" element={<Schedule />} />
          <Route path="/voti" element={<Grades />} />
          <Route path="/agenda" element={<Agenda />} />
          <Route path="/profilo" element={<Profile />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
