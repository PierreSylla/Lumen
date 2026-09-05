<script setup>
import { onMounted, ref } from 'vue'
import Icon from '../components/icons/Icon.vue'
import FieldInput from '../components/base/FieldInput.vue'
import AppButton from '../components/base/AppButton.vue'
import ToggleSwitch from '../components/base/ToggleSwitch.vue'
import { useTheme } from '../composables/useTheme.js'
import { store, apiReady, loadConfig, saveSettings, setBridgeIp, disconnectBridge } from '../store/index.js'

const emit = defineEmits(['repair'])

const { theme } = useTheme()

const config = ref({ bridge_ip: '', has_client_key: false, columns: 2, language: 'en', start_minimized: false })
const changingIp = ref(false)
const newIp = ref('')

onMounted(async () => {
  await apiReady()
  config.value = await loadConfig()
})

async function confirmChangeIp() {
  if (!newIp.value.trim()) return
  await setBridgeIp(newIp.value.trim())
  config.value.bridge_ip = newIp.value.trim()
  changingIp.value = false
}

async function onDisconnect() {
  if (!window.confirm('Disconnect this bridge? You will need to pair again.')) return
  await disconnectBridge()
}

function setLanguage(lang) {
  config.value.language = lang
  saveSettings({ language: lang })
}

function setColumns(n) {
  config.value.columns = n
  saveSettings({ columns: n })
}

function setStartMinimized(value) {
  config.value.start_minimized = value
  saveSettings({ start_minimized: value })
}
</script>

<template>
  <div class="setup-page">
    <div class="card">
      <div class="bridge-row">
        <span class="dot" :style="{ background: store.bridgeOk ? 'var(--ok)' : 'var(--danger)' }" />
        <span class="ip">{{ config.bridge_ip }}</span>
        <span class="note">CLIP v2 &middot; {{ config.has_client_key ? 'paired' : 'no client key' }}</span>
      </div>
      <FieldInput v-if="changingIp" v-model="newIp" placeholder="192.168.x.x" />
      <div class="bridge-actions">
        <AppButton v-if="!changingIp" variant="pill" @click="changingIp = true; newIp = config.bridge_ip">Change IP</AppButton>
        <AppButton v-else variant="pill" @click="confirmChangeIp">Confirm</AppButton>
        <AppButton variant="pill" @click="emit('repair')">Re-pair</AppButton>
        <AppButton variant="danger" @click="onDisconnect">Disconnect</AppButton>
      </div>
    </div>

    <div class="card appearance">
      <div class="row">
        <span class="label">Theme</span>
        <div class="chips">
          <button type="button" class="chip" :class="{ selected: theme === 'dark' }" @click="theme = 'dark'">
            <Icon name="moon" :size="13" /> Dark
          </button>
          <button type="button" class="chip" :class="{ selected: theme === 'light' }" @click="theme = 'light'">
            <Icon name="sun" :size="13" /> Light
          </button>
        </div>
      </div>

      <div class="row">
        <span class="label">Language</span>
        <div class="chips">
          <button type="button" class="chip" :class="{ selected: config.language === 'en' }" @click="setLanguage('en')">English</button>
          <button type="button" class="chip" :class="{ selected: config.language === 'fr' }" @click="setLanguage('fr')">Francais</button>
        </div>
      </div>

      <div class="row">
        <span class="label">Tiles per row</span>
        <div class="chips">
          <button
            v-for="n in [1, 2, 3, 4]"
            :key="n"
            type="button"
            class="chip mono"
            :class="{ selected: config.columns === n }"
            @click="setColumns(n)"
          >
            {{ n }}
          </button>
        </div>
      </div>

      <div class="row">
        <span class="label">Start minimized to tray</span>
        <ToggleSwitch :model-value="config.start_minimized" :width="38" :height="21" :knob="15" @update:model-value="setStartMinimized" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.setup-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  border: 1px solid var(--panel-line);
  border-radius: 12px;
  background: var(--panel);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.bridge-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 3px;
  flex: none;
}
.ip {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 13px;
  color: var(--ink);
  flex: 1;
}
.note {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: var(--ink-4);
}
.bridge-actions {
  display: flex;
  gap: 6px;
}
.bridge-actions :deep(.btn) {
  flex: 1;
  border-radius: 8px;
  padding: 7px;
  font-size: 12px;
}
.appearance {
  gap: 12px;
}
.row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.label {
  flex: 1;
  color: var(--ink-2);
}
.chips {
  display: flex;
  gap: 6px;
}
.chip {
  padding: 5px 11px;
  border-radius: 6px;
  font-size: 12px;
  background: var(--inset);
  color: var(--ink-3);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.chip.mono {
  font-family: 'IBM Plex Mono', monospace;
  width: 26px;
  justify-content: center;
  padding: 5px 0;
}
.chip.selected {
  background: var(--accent);
  color: var(--on-accent);
}
</style>
