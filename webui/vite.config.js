import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  // pywebview loads dist/index.html straight off disk (file://), so assets
  // must resolve with relative paths, not root-absolute ones.
  base: './',
  plugins: [vue()],
})
