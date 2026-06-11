import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import pkg from './package.json'

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Merge shared locale/i18n code into main chunk to avoid async roundtrip
          if (id.includes('/locales/') || id.includes('/i18n/')) {
            return 'index';
          }
        }
      }
    }
  },
  server: {
    proxy: {
      '/downloads': {
        target: 'http://localhost:58888',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://localhost:58888',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:58888',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})