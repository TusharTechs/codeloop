import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development the UI runs on :5173 and proxies the API and WebSocket to the backend on :8000.
// In production the backend serves the built UI from frontend/dist on the same origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true },
    },
  },
})
