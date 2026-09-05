<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import DragBar from '../components/base/DragBar.vue'
import { useI18n } from '../composables/useI18n.js'
import {
  apiReady,
  loadConfig,
  saveSettings,
  listEntertainmentConfigs,
  getChannelNames,
  listOutputs,
  syncStatus,
  syncPreview,
  startSync,
  stopSync,
  setSyncOutput,
  setSyncSaturation,
} from '../store/index.js'

const { t } = useI18n()

const FPS_OPTIONS = [20, 25, 30, 40, 50]
const PLACEHOLDER = 'var(--inset)'

const configId = ref(null)
const channels = ref([]) // [{ channel_id, name }]
const outputs = ref([])
const output = ref('')
const saturation = ref(1.6)
const boostPct = ref(30)
const fps = ref(30)
const running = ref(false)
const errorMsg = ref('')
const previewColors = ref([])

let previewTimer = null

onMounted(async () => {
  await apiReady()

  const cfgs = await listEntertainmentConfigs()
  if (cfgs.data?.length) {
    configId.value = cfgs.data[0].id
    channels.value = await getChannelNames(configId.value)
  }
  outputs.value = await listOutputs()

  const cfg = await loadConfig()
  output.value = cfg.sync_output || ''
  saturation.value = cfg.sync_saturation ?? 1.6
  boostPct.value = Math.round((saturation.value - 1) * 50)
  fps.value = cfg.sync_fps ?? 30

  const status = await syncStatus()
  running.value = status.running
  if (status.running) {
    fps.value = status.fps
    startPreviewPolling()
  }
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
  if (running.value) {
    await stopSync()
    running.value = false
    stopPreviewPolling()
    return
  }
  errorMsg.value = ''
  const res = await startSync(output.value, saturation.value, fps.value, configId.value)
  if (res.error) {
    errorMsg.value = res.error
    return
  }
  running.value = true
  startPreviewPolling()
}

function onOutputChange(e) {
  output.value = e.target.value
  saveSettings({ sync_output: output.value })
  if (running.value) setSyncOutput(output.value)
}

function updateBoost(pct) {
  boostPct.value = pct
  saturation.value = Math.round((1 + pct / 50) * 10) / 10
}

function commitBoost(pct) {
  updateBoost(pct)
  saveSettings({ sync_saturation: saturation.value })
  if (running.value) setSyncSaturation(saturation.value)
}

async function setFps(n) {
  fps.value = n
  saveSettings({ sync_fps: n })
  if (running.value) {
    await stopSync()
    stopPreviewPolling()
    const res = await startSync(output.value, saturation.value, n, configId.value)
    if (!res.error) {
      running.value = true
      startPreviewPolling()
    } else {
      running.value = false
      errorMsg.value = res.error
    }
  }
}
</script>

<template>
  <div class="sync-page">
    <div class="card">
      <div class="label-row"><span>{{ t('screen_channels_label') }}</span></div>
      <div class="preview" :style="{ gridTemplateColumns: `repeat(${channels.length || 1}, 1fr)` }">
        <div
          v-for="(ch, i) in channels"
          :key="ch.channel_id"
          class="preview-block"
          :style="{ background: running ? (previewColors[i] || PLACEHOLDER) : PLACEHOLDER }"
        />
      </div>
      <div class="channel-grid" :style="{ gridTemplateColumns: `repeat(${channels.length || 1}, 1fr)` }">
        <div v-for="(ch, i) in channels" :key="ch.channel_id" class="channel-cell">
          <div class="channel-bar" :style="{ background: running ? (previewColors[i] || PLACEHOLDER) : PLACEHOLDER }" />
          <div class="channel-name">{{ ch.name }}</div>
        </div>
      </div>
    </div>

    <div class="card options">
      <div class="row">
        <span class="label">{{ t('sync_monitor') }}</span>
        <select class="output-select" :value="output" @change="onOutputChange">
          <option value="">{{ t('sync_auto') }}</option>
          <option v-for="o in outputs" :key="o" :value="o">{{ o }}</option>
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
          @update:model-value="updateBoost"
          @change="commitBoost"
        />
        <span class="boost-value">{{ saturation.toFixed(1) }}</span>
      </div>

      <div class="row">
        <span class="label">{{ t('sync_fps_label') }}</span>
        <div class="fps-chips">
          <button
            v-for="n in FPS_OPTIONS"
            :key="n"
            type="button"
            class="fps-chip"
            :class="{ selected: fps === n }"
            @click="setFps(n)"
          >
            {{ n }}
          </button>
        </div>
      </div>
    </div>

    <button type="button" class="primary-action" :class="{ running }" @click="onToggle">
      {{ running ? t('sync_stop_full') : t('sync_start_full') }}
    </button>

    <div v-if="errorMsg" class="error">{{ errorMsg }}</div>
    <div class="note">{{ running ? t('sync_note_running_fmt', { fps }) : t('sync_note_idle') }}</div>
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
