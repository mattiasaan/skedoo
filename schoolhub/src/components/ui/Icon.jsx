/**
 * Icon — lightweight inline SVG icon set.
 * Add new icons to the `icons` map as needed.
 */

const PATHS = {
  home: (c) => (
    <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H14v-5h-4v5H4a1 1 0 01-1-1V9.5z"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  calendar: (c) => (<>
    <rect x="3" y="4" width="18" height="18" rx="2" fill="none" stroke={c} strokeWidth="1.8" />
    <path d="M16 2v4M8 2v4M3 10h18" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  users: (c) => (<>
    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
    <circle cx="9" cy="7" r="4" fill="none" stroke={c} strokeWidth="1.8" />
    <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  user: (c) => (<>
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
    <circle cx="12" cy="7" r="4" fill="none" stroke={c} strokeWidth="1.8" />
  </>),
  bell: (c) => (<>
    <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  eye: (c) => (<>
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" fill="none" stroke={c} strokeWidth="1.8" />
    <circle cx="12" cy="12" r="3" fill="none" stroke={c} strokeWidth="1.8" />
  </>),
  eyeOff: (c) => (<>
    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19M1 1l22 22"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  lock: (c) => (<>
    <rect x="3" y="11" width="18" height="11" rx="2" fill="none" stroke={c} strokeWidth="1.8" />
    <path d="M7 11V7a5 5 0 0110 0v4" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  arrowRight: (c) => (
    <path d="M5 12h14M12 5l7 7-7 7" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  chevronLeft: (c) => (
    <path d="M15 18l-6-6 6-6" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  chevronRight: (c) => (
    <path d="M9 18l6-6-6-6" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  clock: (c) => (<>
    <circle cx="12" cy="12" r="10" fill="none" stroke={c} strokeWidth="1.8" />
    <path d="M12 6v6l4 2" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  mapPin: (c) => (<>
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" fill="none" stroke={c} strokeWidth="1.8" />
    <circle cx="12" cy="10" r="3" fill="none" stroke={c} strokeWidth="1.8" />
  </>),
  info: (c) => (<>
    <circle cx="12" cy="12" r="10" fill="none" stroke={c} strokeWidth="1.8" />
    <path d="M12 16v-4M12 8h.01" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  x: (c) => (
    <path d="M18 6L6 18M6 6l12 12" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  ),
  check: (c) => (
    <path d="M20 6L9 17l-5-5" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  ),
  plus: (c) => (
    <path d="M12 5v14M5 12h14" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" />
  ),
  menu: (c) => (
    <path d="M3 12h18M3 6h18M3 18h18" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  ),
  search: (c) => (<>
    <circle cx="11" cy="11" r="8" fill="none" stroke={c} strokeWidth="1.8" />
    <path d="M21 21l-4.35-4.35" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  tasks: (c) => (<>
    <path d="M9 11l3 3L22 4" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  star: (c) => (
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  trophy: (c) => (<>
    <path d="M6 9H4.5a2.5 2.5 0 010-5H6M18 9h1.5a2.5 2.5 0 000-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22M18 2H6v7a6 6 0 0012 0V2z"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </>),
  shield: (c) => (
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  zap: (c) => (
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  hash: (c) => (<>
    <path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
  heart: (c) => (
    <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  ),
  flag: (c) => (<>
    <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"
      fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    <line x1="4" y1="22" x2="4" y2="15" stroke={c} strokeWidth="1.8" strokeLinecap="round" />
  </>),
};

export default function Icon({ name, size = 20, color = "currentColor" }) {
  const renderPath = PATHS[name];
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
      {renderPath ? renderPath(color) : null}
    </svg>
  );
}
