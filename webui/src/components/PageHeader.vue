<script setup>
import Icon from './icons/Icon.vue'

const HEADERS = {
  rooms: { kicker: 'Physical setup', title: 'Rooms', addLabel: 'Room' },
  zones: { kicker: 'Free grouping', title: 'Zones', addLabel: 'Zone' },
  scenes: { kicker: 'Saved states', title: 'Scenes', addLabel: 'Scene' },
  sync: { kicker: 'Entertainment API', title: 'Screen sync', addLabel: null },
  setup: { kicker: 'Bridge & app', title: 'Setup', addLabel: null },
}

defineProps({ page: { type: String, required: true } })
defineEmits(['add', 'refresh'])
</script>

<template>
  <header class="page-header">
    <div class="left">
      <div class="kicker">{{ HEADERS[page].kicker }}</div>
      <div class="title">{{ HEADERS[page].title }}</div>
    </div>
    <button v-if="HEADERS[page].addLabel" type="button" class="add-btn" @click="$emit('add')">
      <Icon name="plus" :size="12" />
      {{ HEADERS[page].addLabel }}
    </button>
    <button type="button" class="refresh-btn" @click="$emit('refresh')">
      <Icon name="refresh" :size="15" />
    </button>
  </header>
</template>

<style scoped>
.page-header {
  padding: 16px 16px 12px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  border-bottom: 1px solid var(--line);
}
.left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.kicker {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-4);
}
.title {
  font-size: 19px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ink);
}
.add-btn,
.refresh-btn {
  background: var(--pill);
  border: 1px solid var(--pill-line);
  border-radius: 8px;
  color: var(--ink-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.add-btn {
  padding: 6px 11px;
  font-size: 12px;
  font-family: inherit;
}
.refresh-btn {
  width: 34px;
  height: 30px;
  justify-content: center;
  flex: none;
}
</style>
