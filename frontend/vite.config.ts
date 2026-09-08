import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // Port 8010 avoids a common Windows reservation/conflict on 8000.
        // Docker uses its own Nginx proxy and is unaffected by this value.
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
    },
  },
})
