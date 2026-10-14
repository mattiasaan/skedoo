import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// In sviluppo le chiamate a /api vanno al backend FastAPI (porta 8000): niente problemi di CORS.
// In produzione imposta VITE_API_URL (vedi .env.example).
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["apple-touch-icon.png", "favicon.svg"],
      manifest: {
        name: "Skedoo",
        short_name: "Skedoo",
        description: "Orario, voti e agenda della scuola",
        lang: "it",
        start_url: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#08100d",
        theme_color: "#08100d",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      // La app (HTML, JS, CSS, font) si salva per aprirsi anche offline.
      // Le chiamate all'API NON vengono mai salvate: sono dati personali.
      workbox: { navigateFallbackDenylist: [/^\/api\//] },
    }),
  ],
  server: {
    proxy: {
      "/api": {
        target: process.env.BACKEND_URL || "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: { environment: "node" },
});
