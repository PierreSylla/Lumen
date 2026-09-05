<script setup>
import { computed } from 'vue'
import Icon from './icons/Icon.vue'
import ToggleSwitch from './base/ToggleSwitch.vue'
import DragBar from './base/DragBar.vue'
import { useTheme } from '../composables/useTheme.js'
import { dimmed, glyphColor, readoutColor } from '../lib/colors.js'
import { lampKind } from '../lib/lampKind.js'

const props = defineProps({
  lamp: { type: Object, required: true }, // { id, name, archetype, on, bri, color }
})
const emit = defineEmits(['click-name', 'update:bri', 'change:bri', 'update:on'])

const { theme } = useTheme()

const ROW_ALPHA = { dark: 0.13, light: 0.22 }
const ROW_BASE = { dark: '#191c22', light: '#ffffff' }
const READOUT_HI = '#26282c'
const READOUT_LO = '#dfe3ea'

const rowBg = computed(() => {
  if (!props.lamp.on) return 'var(--row-off)'
  const alpha = ROW_ALPHA[theme.value]
  const [r, g, b] = hexToRgbNums(props.lamp.color)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
})

function hexToRgbNums(hex) {
  const n = parseInt(hex.replace('#', ''), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

const glyphHex = computed(() =>
  props.lamp.on ? glyphColor(props.lamp.color, props.lamp.bri, theme.value) : 'var(--ink-4)',
)

const readoutHex = computed(() => {
  if (!props.lamp.on) return 'var(--readout-off)'
  return readoutColor(props.lamp.color, ROW_ALPHA[theme.value], ROW_BASE[theme.value], READOUT_HI, READOUT_LO)
})

const sliderFill = computed(() => dimmed(props.lamp.color, props.lamp.bri))
</script>

<template>
  <div class="lamp-row" :style="{ background: rowBg }">
    <div class="name-zone" @click="emit('click-name', lamp)">
      <Icon :name="lampKind(lamp.archetype)" :size="22" :style="{ color: glyphHex }" />
      <span class="name">{{ lamp.name }}</span>
    </div>
    <DragBar
      class="slider"
      :model-value="lamp.bri"
      :fill="sliderFill"
      height="18px"
      radius="9px"
      @update:model-value="emit('update:bri', $event)"
      @change="emit('change:bri', $event)"
    />
    <span class="readout" :style="{ color: readoutHex }">{{ lamp.on ? `${lamp.bri}%` : 'off' }}</span>
    <ToggleSwitch
      :model-value="lamp.on"
      :width="38"
      :height="21"
      :knob="15"
      @update:model-value="emit('update:on', $event)"
    />
  </div>
</template>

<style scoped>
.lamp-row {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px 9px;
  border-radius: 10px;
}
.name-zone {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
}
.name {
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.slider {
  width: 100px;
  flex: 0 0 100px;
}
.readout {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  width: 30px;
  text-align: right;
  flex: none;
}
</style>
