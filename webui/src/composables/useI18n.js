import { reactive, ref } from 'vue'
import { apiReady } from '../store/index.js'

const STORAGE_KEY = 'lumen.lang'

function initialLang() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'en' || stored === 'fr') return stored
  } catch {
    // localStorage unavailable - fall through
  }
  return 'en'
}

const lang = ref(initialLang())
// Both full dictionaries (huectl/i18n.py's STRINGS), loaded once - switching
// lang afterwards is instant, no round trip.
const strings = reactive({ en: {}, fr: {} })
let loaded = null

/** Call once on app start - fetches both dictionaries from the bridge process. */
export function initI18n() {
  if (!loaded) {
    loaded = apiReady().then(async () => {
      const api = window.pywebview?.api
      if (!api?.get_strings) return
      const result = await api.get_strings()
      Object.assign(strings.en, result.en)
      Object.assign(strings.fr, result.fr)
    })
  }
  return loaded
}

/** t('key', {param: value}) - same {placeholder} format as huectl/i18n.py's t(). */
export function t(key, params) {
  const s = strings[lang.value]?.[key] ?? strings.en[key] ?? key
  return params ? s.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? '') : s
}

export function useI18n() {
  function setLang(code) {
    lang.value = code
    try {
      localStorage.setItem(STORAGE_KEY, code)
    } catch {
      // ignore - language just won't persist across reloads
    }
  }
  return { lang, t, setLang }
}
