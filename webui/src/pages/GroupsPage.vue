<script setup>
import { reactive, watch } from 'vue'
import CardShell from '../components/CardShell.vue'
import {
  writeLampOn,
  updateLampBriLocal,
  writeLampBri,
  writeGroupOn,
  updateGroupBriLocal,
  writeGroupBri,
  recallScene,
} from '../store/index.js'

const props = defineProps({
  groups: { type: Array, required: true },
})
const emit = defineEmits(['edit-group', 'click-lamp'])

const expanded = reactive({})
watch(
  () => props.groups,
  (groups) => {
    if (groups.length && !groups.some((g) => expanded[g.id])) {
      expanded[groups[0].id] = true
    }
  },
  { immediate: true },
)

function toggleExpanded(id, value) {
  expanded[id] = value
}

function onRecallScene(scene) {
  recallScene(scene.id)
}
</script>

<template>
  <div class="groups-page">
    <CardShell
      v-for="group in groups"
      :key="group.id"
      :group="group"
      :expanded="!!expanded[group.id]"
      @update:expanded="toggleExpanded(group.id, $event)"
      @edit="emit('edit-group', group)"
      @master-toggle="writeGroupOn(group, $event)"
      @group-brightness="updateGroupBriLocal(group, $event)"
      @change:group-brightness="writeGroupBri(group, $event)"
      @recall-scene="onRecallScene"
      @click-lamp="emit('click-lamp', $event)"
      @update:lamp-on="writeLampOn($event.id, $event.on)"
      @update:lamp-bri="updateLampBriLocal($event.id, $event.bri)"
      @change:lamp-bri="writeLampBri($event.id, $event.bri)"
    />
  </div>
</template>

<style scoped>
.groups-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
