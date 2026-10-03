import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // In development, requests to /api go through Vite to the Next.js server.
    // The browser only talks to localhost:5173 (same origin), so there is no CORS.
    proxy: {
      '/api': 'http://localhost:3000',
    },
  },
})
