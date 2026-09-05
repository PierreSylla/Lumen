<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [String, Number], default: 18 },
})

const ICONS = {
  // Nav rail, viewBox 0 0 24 24
  rooms: { viewBox: '0 0 24 24', shapes: [{ d: 'M4 10 12 4l8 6v10H4z' }] },
  zones: { viewBox: '0 0 24 24', shapes: [{ d: 'M4 6h7v7H4zM13 11h7v7h-7z' }] },
  scenes: { viewBox: '0 0 24 24', shapes: [{ d: 'M12 3l2.4 6L21 12l-6.6 3L12 21l-2.4-6L3 12l6.6-3z' }] },
  sync: { viewBox: '0 0 24 24', shapes: [{ d: 'M4 5h16v11H4zM9 18h6v2H9z' }] },
  setup: { viewBox: '0 0 24 24', shapes: [{ d: 'M4 7h16v2H4zM4 15h16v2H4zM8 4h2v8H8zM14 12h2v8h-2z' }] },

  // Theme switch
  moon: { viewBox: '0 0 24 24', shapes: [{ d: 'M14 3a9 9 0 1 0 7 14 10.5 10.5 0 0 1-7-14z' }] },
  sun: {
    viewBox: '0 0 24 24',
    shapes: [
      {
        d: 'M12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10zM11 2h2v3h-2zM11 19h2v3h-2zM2 11h3v2H2zM19 11h3v2h-3zM4.2 5.6l1.4-1.4 2.1 2.1-1.4 1.4zM16.3 17.7l1.4-1.4 2.1 2.1-1.4 1.4zM17.7 4.2l1.4 1.4-2.1 2.1-1.4-1.4zM5.6 16.3l1.4 1.4-2.1 2.1-1.4-1.4z',
      },
    ],
  },

  // Page header, viewBox 0 0 22 22
  plus: {
    viewBox: '0 0 22 22',
    shapes: [
      { tag: 'line', attrs: { x1: 11, y1: 6, x2: 11, y2: 16 } },
      { tag: 'line', attrs: { x1: 6, y1: 11, x2: 16, y2: 11 } },
    ],
    stroke: true,
  },
  refresh: {
    viewBox: '0 0 22 22',
    shapes: [
      { tag: 'path', attrs: { d: 'M 12.71 4.63 A 6.6 6.6 0 1 0 17.57 10.42' }, stroke: true },
      { tag: 'polygon', attrs: { points: '17.57,8.0 19.99,11.39 15.15,11.39' } },
    ],
  },

  // Lamp-type glyphs, viewBox 0 0 40 40 (translated from huectl/icons.py)
  bulb: { viewBox: '0 0 40 40', shapes: [{ d: 'M19 4a10 10 0 1 1 0 20 10 10 0 0 1 0-20ZM15.2 23.2h9.6v9.6h-9.6z' }] },
  ceiling: { viewBox: '0 0 40 40', shapes: [{ d: 'M7.2 3h25.6v5.6H7.2zM11.2 6.8h17.6L24.8 32h-9.6z' }] },
  table: { viewBox: '0 0 40 40', shapes: [{ d: 'M12 18.4h16l-3.2-8.8h-9.6zM19 18.4h2v14.4h-2zM14.4 30.8h11.2v2H14.4z' }] },
  floor: { viewBox: '0 0 40 40', shapes: [{ d: 'M12 12h16l-3.2-8h-9.6zM19 12h2v22.4h-2zM14.4 32.4h11.2v2H14.4z' }] },
  strip: { viewBox: '0 0 40 40', shapes: [{ d: 'M3 16.8h34v7.2H3z' }] },
  bar: { viewBox: '0 0 40 40', shapes: [{ d: 'M16 4h8v32h-8z' }] },
  spot: { viewBox: '0 0 40 40', shapes: [{ d: 'M12 9a7 6 0 1 1 14 0 7 6 0 0 1-14 0ZM13.6 13.2h12.8L24 31.2h-8z' }] },
  plug: { viewBox: '0 0 40 40', shapes: [{ d: 'M12 12h16v17.6H12zM15.8 6.4h2v6.4h-2zM22.2 6.4h2v6.4h-2z' }] },
  candle: { viewBox: '0 0 40 40', shapes: [{ d: 'M20 4.8C28.8 13.6 26.4 24 20 24S11.2 13.6 20 4.8ZM16.8 24h6.4v9.6h-6.4z' }] },
}

const def = computed(() => ICONS[props.name] ?? ICONS.bulb)
</script>

<template>
  <svg
    :viewBox="def.viewBox"
    :width="size"
    :height="size"
    fill="currentColor"
    stroke="none"
  >
    <template v-for="(s, i) in def.shapes" :key="i">
      <line
        v-if="s.tag === 'line'"
        v-bind="s.attrs"
        stroke="currentColor"
        stroke-width="2.4"
        stroke-linecap="round"
      />
      <path
        v-else-if="s.tag === 'path' && s.stroke"
        v-bind="s.attrs"
        fill="none"
        stroke="currentColor"
        stroke-width="2.2"
        stroke-linecap="round"
      />
      <polygon v-else-if="s.tag === 'polygon'" v-bind="s.attrs" />
      <path v-else :d="s.d" />
    </template>
  </svg>
</template>
