import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // THÊM DÒNG 1: Import Tailwind

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // THÊM DÒNG 2: Kích hoạt plugin
  ],
})