import { useState } from "react";
import { COLORS } from "../../constants/colors";
import Icon from "../ui/Icon";
import GoogleLogo from "../ui/GoogleLogo";

export default function LoginScreen({ onLogin }) {
  const [username, setUsername]   = useState("");
  const [password, setPassword]   = useState("");
  const [showPass, setShowPass]   = useState(false);
  const [loading,  setLoading]    = useState(false);
  const [shake,    setShake]      = useState(false);

  const handleLogin = () => {
    if (!username || !password) {
      setShake(true);
      setTimeout(() => setShake(false), 500);
      return;
    }
    setLoading(true);
    setTimeout(() => { setLoading(false); onLogin(); }, 1200);
  };

  return (
    <div style={{
      minHeight:      "100vh",
      background:     COLORS.bg,
      display:        "flex",
      alignItems:     "center",
      justifyContent: "center",
      padding:        "24px",
    }}>
      <div style={{ width: "100%", maxWidth: "440px" }}>

        {/* ── Logo ────────────────────────────── */}
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <div style={{
            width:        80,
            height:       80,
            background:   `linear-gradient(135deg, ${COLORS.green}, ${COLORS.greenDark})`,
            borderRadius: 20,
            display:      "flex",
            alignItems:   "center",
            justifyContent: "center",
            margin:       "0 auto 24px",
            boxShadow:    `0 8px 32px ${COLORS.green}40`,
          }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z"
                stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M6 12v5c0 2 6 3 6 3s6-1 6-3v-5"
                stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 800, color: COLORS.text, letterSpacing: "-0.5px" }}>
            SchoolHub
          </h1>
          <p style={{ color: COLORS.textMuted, marginTop: 8, fontSize: 15 }}>
            Bentornato! Accedi al tuo registro elettronico
          </p>
        </div>

        {/* ── Form ────────────────────────────── */}
        <div className={shake ? "anim-shake" : ""}>

          {/* Username */}
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Username</label>
            <div style={{ position: "relative" }}>
              <span style={inputIconStyle}><Icon name="user" size={18} color={COLORS.textDim} /></span>
              <input
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Inserisci il tuo username"
                style={inputStyle(!!username)}
              />
            </div>
          </div>

          {/* Password */}
          <div style={{ marginBottom: 8 }}>
            <label style={labelStyle}>Password</label>
            <div style={{ position: "relative" }}>
              <span style={inputIconStyle}><Icon name="lock" size={18} color={COLORS.textDim} /></span>
              <input
                value={password}
                onChange={e => setPassword(e.target.value)}
                type={showPass ? "text" : "password"}
                placeholder="Inserisci la tua password"
                style={{ ...inputStyle(!!password), paddingRight: 46 }}
                onKeyDown={e => e.key === "Enter" && handleLogin()}
              />
              <button
                onClick={() => setShowPass(v => !v)}
                style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", padding: 4 }}
              >
                <Icon name={showPass ? "eyeOff" : "eye"} size={18} color={COLORS.textDim} />
              </button>
            </div>
          </div>

          {/* Forgot */}
          <div style={{ textAlign: "right", marginBottom: 28 }}>
            <span style={{ color: COLORS.greenLight, fontSize: 13, cursor: "pointer", fontWeight: 500 }}>
              Password dimenticata?
            </span>
          </div>

          {/* Primary CTA */}
          <button
            onClick={handleLogin}
            style={primaryBtnStyle}
            onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = `0 8px 28px ${COLORS.green}60`; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)";    e.currentTarget.style.boxShadow = `0 4px 20px ${COLORS.green}50`; }}
          >
            {loading
              ? <div className="anim-spin" style={{ width: 20, height: 20, border: "2px solid white", borderTopColor: "transparent", borderRadius: "50%" }} />
              : <><Icon name="arrowRight" size={20} color="white" /> Accedi con ClasseViva</>
            }
          </button>

          {/* Divider */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0" }}>
            <div style={{ flex: 1, height: 1, background: COLORS.border }} />
            <span style={{ color: COLORS.textDim, fontSize: 12, letterSpacing: "1px", fontWeight: 600 }}>OPPURE</span>
            <div style={{ flex: 1, height: 1, background: COLORS.border }} />
          </div>

          {/* Google */}
          <button
            style={googleBtnStyle}
            onMouseEnter={e => e.currentTarget.style.background = "#1f2e42"}
            onMouseLeave={e => e.currentTarget.style.background = "#1a2535"}
          >
            <GoogleLogo /> Continua con Google
          </button>

          <p style={{ textAlign: "center", color: COLORS.textMuted, fontSize: 14, marginTop: 28 }}>
            Non hai ancora un account?{" "}
            <span style={{ color: COLORS.greenLight, cursor: "pointer", fontWeight: 600 }}>Registrati ora</span>
          </p>
        </div>
      </div>
    </div>
  );
}

/* ── Local style helpers ─────────────────────────────────────────────────── */
const labelStyle = {
  display:       "block",
  color:         COLORS.textMuted,
  fontSize:      13,
  fontWeight:    600,
  marginBottom:  8,
  letterSpacing: "0.5px",
  textTransform: "uppercase",
};

const inputIconStyle = {
  position:  "absolute",
  left:      16,
  top:       "50%",
  transform: "translateY(-50%)",
  color:     COLORS.textDim,
};

const inputStyle = (filled) => ({
  width:        "100%",
  background:   COLORS.bgInput,
  border:       `1px solid ${filled ? COLORS.green : COLORS.border}`,
  borderRadius: 12,
  padding:      "14px 16px 14px 46px",
  color:        COLORS.text,
  fontSize:     15,
  outline:      "none",
  boxSizing:    "border-box",
  transition:   "border 0.2s",
});

const primaryBtnStyle = {
  width:          "100%",
  background:     `linear-gradient(135deg, ${COLORS.green}, ${COLORS.greenDark})`,
  border:         "none",
  borderRadius:   14,
  padding:        "16px",
  color:          "white",
  fontSize:       16,
  fontWeight:     700,
  cursor:         "pointer",
  display:        "flex",
  alignItems:     "center",
  justifyContent: "center",
  gap:            10,
  boxShadow:      `0 4px 20px ${COLORS.green}50`,
  transition:     "transform 0.15s, box-shadow 0.15s",
  marginBottom:   16,
};

const googleBtnStyle = {
  width:          "100%",
  background:     "#1a2535",
  border:         `1px solid ${COLORS.border}`,
  borderRadius:   14,
  padding:        "14px",
  color:          COLORS.text,
  fontSize:       15,
  fontWeight:     600,
  cursor:         "pointer",
  display:        "flex",
  alignItems:     "center",
  justifyContent: "center",
  gap:            12,
  transition:     "background 0.2s",
};
