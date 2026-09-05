<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: Number, required: true },
  fill: { type: String, required: true },
  height: { type: String, default: '18px' },
  radius: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'change'])

const barEl = ref(null)

function valueFromClientX(clientX, rect) {
  return Math.min(100, Math.max(0, Math.round(((clientX - rect.left) / rect.width) * 100)))
}

function onPointerDown(e) {
  if (props.disabled) return
  const rect = barEl.value.getBoundingClientRect()
  emit('update:modelValue', valueFromClientX(e.clientX, rect))

  function onMove(ev) {
    emit('update:modelValue', valueFromClientX(ev.clientX, rect))
  }
  function onUp(ev) {
    const value = valueFromClientX(ev.clientX, rect)
    emit('update:modelValue', value)
    emit('change', value)
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}
</script>

<template>
  <div
    ref="barEl"
    class="drag-bar"
    :class="{ disabled }"
    :style="{ height, borderRadius: radius || `calc(${height} / 2)` }"
    @pointerdown="onPointerDown"
  >
    <div class="fill" :style="{ width: modelValue + '%', background: fill }" />
  </div>
</template>

<style scoped>
.drag-bar {
  position: relative;
  background: var(--inset);
  overflow: hidden;
  cursor: ew-resize;
}
.drag-bar.disabled {
  cursor: default;
}
.fill {
  position: absolute;
  inset: 0 auto 0 0;
}
</style>
