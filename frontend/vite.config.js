import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig, loadEnv } from 'vite'

/** Origine dell'API in produzione (VITE_API_URL), da autorizzare nella Content Security Policy. */
function apiOrigin(url) {
  if (!url) return ''
  try {
    return new URL(url).origin
  } catch {
    return '' // percorso relativo (es. /api): è già coperto da 'self'
  }
}

/**
 * Content Security Policy solo nella build: limita da dove si caricano script, stili e font
 * e dove si può inviare dati. In sviluppo non serve (e Vite usa script inline per l'HMR).
 * Header come frame-ancestors vanno impostati dal server che pubblica il sito.
 */
function contentSecurityPolicy(env) {
  const policy = [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "img-src 'self' data:",
    `connect-src 'self' ${apiOrigin(env.VITE_API_URL)}`.trim(),
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ')
  return {
    name: 'skedoo-csp',
    apply: 'build',
    transformIndexHtml: () => [{ tag: 'meta', attrs: { 'http-equiv': 'Content-Security-Policy', content: policy }, injectTo: 'head-prepend' }],
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, fileURLToPath(new URL('.', import.meta.url)), '')
  return {
    plugins: [react(), contentSecurityPolicy(env)],
    server: {
      // /api/* -> backend FastAPI: niente CORS e funziona anche dal telefono (npm run dev -- --host)
      proxy: {
        '/api': {
          target: env.SKEDOO_API_TARGET || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
