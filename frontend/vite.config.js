import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In dev, forward /api to a locally running backend (uvicorn on :8000).
// In Docker/K8s, nginx does the same proxying.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
