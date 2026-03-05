## Avvio rapido

```bash
npm install
npm run dev
```

---

## Struttura del progetto

```
frontend/
├── index.html
├── vite.config.js
├── package.json
└── src/
    ├── main.jsx              # Entry point React
    ├── App.jsx               # Root: gestione auth + routing tab
    ├── index.css             # Reset, font, keyframes globali
    │
    ├── constants/
    │   └── colors.js         # Palette colori centralizzata (unico punto da modificare)
    │
    ├── data/                 # Mock data — sostituire con chiamate API reali
    │   ├── schedule.js       # Orario giornaliero + upNext + alert
    │   ├── calendar.js       # Eventi calendario, dots, leggenda
    │   ├── community.js      # Post, tag colors, leaderboard
    │   └── user.js           # Profilo, stats, achievements, settings
    │
    └── components/
        ├── ui/               # Componenti riutilizzabili / primitivi
        │   ├── Icon.jsx      # SVG icon set (aggiungere icone qui)
        │   ├── GoogleLogo.jsx
        │   └── NavBar.jsx
        │
        └── screens/          # Una schermata = un file
            ├── LoginScreen.jsx
            ├── HomeScreen.jsx
            ├── CalendarScreen.jsx
            ├── CommunityScreen.jsx
            └── ProfileScreen.jsx
```
