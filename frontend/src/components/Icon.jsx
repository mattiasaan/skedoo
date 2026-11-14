// Icone a tratto 24x24 (stile lucide), colore = currentColor.
const paths = {
	alert: <><path d="M12 3 2.8 19a1.5 1.5 0 0 0 1.3 2.2h15.8a1.5 1.5 0 0 0 1.3-2.2L12 3Z" /><path d="M12 9v4m0 4h.01" /></>,
	arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
	arrowLeft: <path d="M19 12H5m6 6-6-6 6-6" />,
	bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21a2 2 0 0 0 4 0" /></>,
	bolt: <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />,
	book: <><path d="M2 4h7a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H2V4Z" /><path d="M22 4h-7a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h8V4Z" /></>,
	bookmark: <path d="M6 4.8A1.8 1.8 0 0 1 7.8 3h8.4A1.8 1.8 0 0 1 18 4.8V21l-6-4-6 4V4.8Z" />,
	bulb: <><path d="M9 18h6m-5 3h4" /><path d="M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3Z" /></>,
	building: <><rect x="4" y="3" width="16" height="18" rx="2" /><path d="M9 21v-4h6v4M9 7h.01M15 7h.01M9 11h.01M15 11h.01" /></>,
	calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></>,
	cap: <><path d="m2 9 10-5 10 5-10 5L2 9Z" /><path d="M6 11v5c3.5 2.7 8.5 2.7 12 0v-5M22 9v6" /></>,
	chart: <path d="M5 20V12m7 8V4m7 16v-9" />,
	check: <path d="m5 12 4 4L19 6" />,
	checkCircle: <><circle cx="12" cy="12" r="9" /><path d="m8.5 12 2.5 2.5 4.5-5" /></>,
	chevron: <path d="m9 18 6-6-6-6" />,
	chevronDown: <path d="m6 9 6 6 6-6" />,
	chevronLeft: <path d="m15 18-6-6 6-6" />,
	clipboard: <><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4.5V3h6v1.5M9 11h6M9 15h4" /></>,
	clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
	close: <path d="m18 6-12 12M6 6l12 12" />,
	code: <path d="m8 7-5 5 5 5m8-10 5 5-5 5" />,
	download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5m-5 5V3" /></>,
	eye: <><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></>,
	eyeOff: <><path d="m3 3 18 18M10.6 10.6a2 2 0 0 0 2.8 2.8" /><path d="M9.9 5.2A10.8 10.8 0 0 1 12 5c6.4 0 10 7 10 7a16 16 0 0 1-3.1 3.8M6.2 6.2C3.5 8 2 12 2 12s3.6 7 10 7a10.8 10.8 0 0 0 4.1-.8" /></>,
	file: <><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></>,
	flag: <path d="M5 21V4m0 0c5-3 9 3 14 0v10c-5 3-9-3-14 0" />,
	flask: <><path d="M9 3h6M10 3v6L4.5 18.5A1.7 1.7 0 0 0 6 21h12a1.7 1.7 0 0 0 1.5-2.5L14 9V3" /><path d="M7 15h10" /></>,
	gear: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" /></>,
	globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></>,
	grid: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></>,
	landmark: <path d="M3 21h18M5 21V10m4 11V10m6 11V10m4 11V10M2 10l10-6 10 6H2Z" />,
	link: <><path d="M10 14a4.5 4.5 0 0 0 6.4 0l3-3a4.5 4.5 0 0 0-6.4-6.4l-1 1" /><path d="M14 10a4.5 4.5 0 0 0-6.4 0l-3 3a4.5 4.5 0 0 0 6.4 6.4l1-1" /></>,
	lock: <><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 7.8-1.2M12 14v3" /></>,
	logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5M21 12H9" /></>,
	megaphone: <><path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1Z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13" /></>,
	palette: <><path d="M12 3a9 9 0 1 0 0 18c1.1 0 1.7-.9 1.4-1.9-.4-1.1.4-2.1 1.5-2.1H17a4 4 0 0 0 4-4c0-5.5-4-10-9-10Z" /><circle cx="7.5" cy="11.5" r="1" /><circle cx="10.5" cy="7.5" r="1" /><circle cx="15.5" cy="8.5" r="1" /></>,
	person: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-1a7 7 0 0 1 14 0v1" /></>,
	pulse: <><circle cx="12" cy="12" r="9" /><path d="M7 12h2.5l1.5-3 2 6 1.5-3H17" /></>,
	refresh: <><path d="M20 11a8 8 0 0 0-14.8-3.5M4 4v4h4" /><path d="M4 13a8 8 0 0 0 14.8 3.5M20 20v-4h-4" /></>,
	run: <><circle cx="14" cy="4.5" r="1.5" /><path d="m7 21 3-6 3 2v5M6 12l3-4h5l2 4 3 1M10 15l2-5" /></>,
	school: <><path d="m3 10 9-6 9 6-9 5-9-5Z" /><path d="M6 12v5l6 3 6-3v-5" /></>,
	search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
	shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></>,
	sigma: <path d="M18 7V4H6l6 8-6 8h12v-3" />,
	square: <rect x="4" y="4" width="16" height="16" rx="4" />,
	swap: <path d="M4 8h14m-4-4 4 4-4 4M20 16H6m4-4-4 4 4 4" />,
	trend: <path d="m3 17 6-6 4 4 8-9m-6 0h6v6" />,
	users: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20v-1a6.5 6.5 0 0 1 13 0v1" /><path d="M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20v-1a6.5 6.5 0 0 0-4-6" /></>,
}

export function Icon({ name, size = 18, className, strokeWidth = 1.8 }) {
	return (
		<svg
			aria-hidden="true"
			className={className}
			fill="none"
			height={size}
			stroke="currentColor"
			strokeLinecap="round"
			strokeLinejoin="round"
			strokeWidth={strokeWidth}
			viewBox="0 0 24 24"
			width={size}
		>
			{paths[name] ?? paths.book}
		</svg>
	)
}

export default Icon
