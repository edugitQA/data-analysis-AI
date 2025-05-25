import { fileURLToPath } from 'url';
import { dirname } from 'path';
import path from 'path-browserify';
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',
    cors: true,
    allowedHosts: [
      '5173-ig5pxrzl6nxv1q1c07urp-bc096365.manusvm.computer',
      'ig5pxrzl6nxv1q1c07urp-bc096365.manusvm.computer',
      'localhost',
      '127.0.0.1'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
