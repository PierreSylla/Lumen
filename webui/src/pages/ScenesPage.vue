<script setup>
import SceneTile from '../components/SceneTile.vue'

defineProps({
  sections: { type: Array, required: true }, // { id, name, kind, scenes }
})
defineEmits(['new-scene', 'edit-scene', 'recall-scene'])

const BADGE = {
  room: { label: 'ROOM', color: 'var(--badge-room)' },
  zone: { label: 'ZONE', color: 'var(--badge-zone)' },
}
</script>

<template>
  <div class="scenes-page">
    <div v-for="section in sections" :key="section.id" class="section">
      <div class="head">
        <span class="name">{{ section.name }}</span>
        <span
          v-if="BADGE[section.kind]"
          class="badge"
          :style="{ color: BADGE[section.kind].color, borderColor: BADGE[section.kind].color }"
        >
          {{ BADGE[section.kind].label }}
        </span>
        <div class="rule" />
        <button type="button" class="new-action" @click="$emit('new-scene', section)">+ NEW</button>
      </div>
      <div class="tile-grid">
        <SceneTile
          v-for="scene in section.scenes"
          :key="scene.id"
          :scene="scene"
          height="78px"
          show-edit
          @recall="$emit('recall-scene', $event)"
          @edit="$emit('edit-scene', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.scenes-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}
.badge {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.1em;
  padding: 1px 5px;
  border-radius: 3px;
  border: 1px solid;
}
.rule {
  flex: 1;
  height: 1px;
  background: var(--line);
}
.new-action {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: var(--accent-text);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.tile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
</style>
