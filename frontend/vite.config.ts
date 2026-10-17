import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'
import { defineConfig } from 'vite'

// SPMS_HTTPS=1 proxies to the HTTPS dev backend (npm run dev:be:https), which uses a self-signed cert.
const https = process.env.SPMS_HTTPS === '1'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': https
        ? { target: 'https://localhost:8443', secure: false }
        : 'http://localhost:8000',
    },
  },
})
