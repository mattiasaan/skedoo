# SchoolHub — Web App

> Registro elettronico moderno per studenti · React + Vite

---

## Avvio rapido

```bash
npm install
npm run dev
```

---

## Struttura del progetto

```
schoolhub/
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

---

## Come aggiungere una nuova schermata

1. Crea `src/components/screens/NuovaSchermata.jsx`
2. Aggiungi il tab in `src/components/ui/NavBar.jsx` → array `TABS`
3. Registra la schermata in `src/App.jsx` → oggetto `SCREENS`

## Come aggiungere un'icona

Apri `src/components/ui/Icon.jsx` e aggiungi una voce al dizionario `PATHS`:

```jsx
nomeIcona: (c) => <path d="..." stroke={c} ... />,
```

Poi usala ovunque: `<Icon name="nomeIcona" size={20} color="#fff" />`

## Come cambiare i colori

Modifica `src/constants/colors.js` — è l'unico file che controlla l'intera palette.

## Come collegare l'API ClasseViva

Sostituisci i file in `src/data/` con hook o servizi reali, ad esempio:

```js
// src/services/classeviva.js
export async function fetchSchedule(token) { ... }
```

---

## Stack

| Tool | Versione |
|------|----------|
| React | 18 |
| Vite  | 5  |
| CSS   | Inline styles + `index.css` per animazioni |
