<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import DragBar from '../components/base/DragBar.vue'
import { useI18n } from '../composables/useI18n.js'
import {
  apiReady,
  store,
  initSync,
  syncPreview,
  startSync,
  stopSync,
  setSyncOutput,
  setSyncSaturation,
  setSyncFps,
} from '../store/index.js'

const { t } = useI18n()

const FPS_OPTIONS = [20, 25, 30, 40, 50]
const PLACEHOLDER = 'var(--inset)'

const errorMsg = ref('')
const previewColors = ref([])
const boostPct = computed(() => Math.round((store.sync.saturation - 1) * 50))

let previewTimer = null

onMounted(async () => {
  await apiReady()
  await initSync()
  if (store.sync.running) startPreviewPolling()
})

onUnmounted(() => clearInterval(previewTimer))

function startPreviewPolling() {
  clearInterval(previewTimer)
  previewTimer = setInterval(async () => {
    previewColors.value = await syncPreview()
  }, 200)
}

function stopPreviewPolling() {
  clearInterval(previewTimer)
  previewColors.value = []
}

async function onToggle() {
  if (store.sync.running) {
    await stopSync()
    stopPreviewPolling()
    return
  }
  errorMsg.value = ''
  const res = await startSync()
  if (res.error) {
    errorMsg.value = res.error
    return
  }
  startPreviewPolling()
}

function onOutputChange(e) {
  setSyncOutput(e.target.value)
}

function commitBoost(pct) {
  setSyncSaturation(Math.round((1 + pct / 50) * 10) / 10)
}

async function setFps(n) {
  const wasRunning = store.sync.running
  if (wasRunning) stopPreviewPolling()
  const res = await setSyncFps(n)
  if (res.error) {
    errorMsg.value = res.error
  } else if (wasRunning) {
    startPreviewPolling()
  }
}
</script>

<template>
  <div class="sync-page">
    <div class="card">
      <div class="label-row"><span>{{ t('screen_channels_label') }}</span></div>
      <div class="preview" :style="{ gridTemplateColumns: `repeat(${store.sync.channels.length || 1}, 1fr)` }">
        <div
          v-for="(ch, i) in store.sync.channels"
          :key="ch.channel_id"
          class="preview-block"
          :style="{ background: store.sync.running ? (previewColors[i] || PLACEHOLDER) : PLACEHOLDER }"
        />
      </div>
      <div class="channel-grid" :style="{ gridTemplateColumns: `repeat(${store.sync.channels.length || 1}, 1fr)` }">
        <div v-for="(ch, i) in store.sync.channels" :key="ch.channel_id" class="channel-cell">
          <div class="channel-bar" :style="{ background: store.sync.running ? (previewColors[i] || PLACEHOLDER) : PLACEHOLDER }" />
          <div class="channel-name">{{ ch.name }}</div>
        </div>
      </div>
    </div>

    <div class="card options">
      <div class="row">
        <span class="label">{{ t('sync_monitor') }}</span>
        <select class="output-select" :value="store.sync.output" @change="onOutputChange">
          <option value="">{{ t('sync_auto') }}</option>
          <option v-for="o in store.sync.outputs" :key="o" :value="o">{{ o }}</option>
        </select>
      </div>

      <div class="row">
        <span class="label">{{ t('sync_saturation') }}</span>
        <DragBar
          class="boost-slider"
          :model-value="boostPct"
          fill="var(--accent)"
          height="8px"
          radius="4px"
          @update:model-value="setSyncSaturation(Math.round((1 + $event / 50) * 10) / 10)"
          @change="commitBoost"
        />
        <span class="boost-value">{{ store.sync.saturation.toFixed(1) }}</span>
      </div>

      <div class="row">
        <span class="label">{{ t('sync_fps_label') }}</span>
        <div class="fps-chips">
          <button
            v-for="n in FPS_OPTIONS"
            :key="n"
            type="button"
            class="fps-chip"
            :class="{ selected: store.sync.fps === n }"
            @click="setFps(n)"
          >
            {{ n }}
          </button>
        </div>
      </div>
    </div>

    <button type="button" class="primary-action" :class="{ running: store.sync.running }" @click="onToggle">
      {{ store.sync.running ? t('sync_stop_full') : t('sync_start_full') }}
    </button>

    <div v-if="errorMsg" class="error">{{ errorMsg }}</div>
    <div class="note">{{ store.sync.running ? t('sync_note_running_fmt', { fps: store.sync.fps }) : t('sync_note_idle') }}</div>
  </div>
</template>

<style scoped>
.sync-page {
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
.label-row {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  color: var(--ink-4);
}
.preview {
  height: 104px;
  border-radius: 9px;
  display: grid;
  overflow: hidden;
}
.preview-block {
  transition: background 0.15s linear;
}
.channel-grid {
  display: grid;
  gap: 6px;
}
.channel-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.channel-bar {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  transition: background 0.15s linear;
}
.channel-name {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 9px;
  color: var(--ink-4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.options {
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
.output-select {
  background: var(--inset);
  border: 1px solid var(--panel-line);
  border-radius: 8px;
  padding: 5px 10px;
  font-size: 12px;
  font-family: inherit;
  color: var(--ink-2);
}
.boost-slider {
  width: 150px;
  flex: none;
}
.boost-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  width: 30px;
  text-align: right;
  color: var(--ink-2);
}
.fps-chips {
  display: flex;
  gap: 6px;
}
.fps-chip {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
  background: var(--inset);
  color: var(--ink-3);
  border: none;
  cursor: pointer;
}
.fps-chip.selected {
  background: var(--accent);
  color: var(--on-accent);
}
.primary-action {
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  font-weight: 600;
  border: none;
  cursor: pointer;
  background: var(--accent);
  color: var(--on-accent);
}
.primary-action.running {
  background: var(--danger-bg);
  color: var(--danger);
}
.error {
  font-size: 12px;
  color: var(--danger);
}
.note {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: var(--ink-4);
}
</style>
