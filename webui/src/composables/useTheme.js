import { ref, watchEffect } from 'vue'

const STORAGE_KEY = 'lumen.theme'

function initialTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'dark' || stored === 'light') return stored
  } catch {
    // localStorage unavailable (private browsing, etc.) - fall through
  }
  return 'dark'
}

const theme = ref(initialTheme())

watchEffect(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  try {
    localStorage.setItem(STORAGE_KEY, theme.value)
  } catch {
    // ignore - theme just won't persist across reloads
  }
})

export function useTheme() {
  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }
  return { theme, toggle }
}
