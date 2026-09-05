<script setup>
import { reactive, watch } from 'vue'
import CardShell from '../components/CardShell.vue'
import { setLampOn, setLampBri } from '../store/index.js'

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

function onMasterToggle(group, on) {
  for (const lamp of group.lamps) setLampOn(lamp.id, on)
}

function onGroupBrightness(group, pct) {
  for (const lamp of group.lamps) setLampBri(lamp.id, pct)
}

function onRecallScene() {
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
      @master-toggle="onMasterToggle(group, $event)"
      @group-brightness="onGroupBrightness(group, $event)"
      @recall-scene="onRecallScene"
      @click-lamp="emit('click-lamp', $event)"
      @update:lamp-on="setLampOn($event.id, $event.on)"
      @update:lamp-bri="setLampBri($event.id, $event.bri)"
      @change:lamp-bri="setLampBri($event.id, $event.bri)"
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
