import { reactive } from 'vue'
import { sampleRoomGroups, sampleZoneGroups, sampleSceneSections } from '../data/sample.js'

export const store = reactive({
  roomGroups: sampleRoomGroups,
  zoneGroups: sampleZoneGroups,
  sceneSections: sampleSceneSections,
  bridgeOk: true,
})

export function setLampOn(id, on) {
  const lamp = findLamp(id)
  if (lamp) lamp.on = on
}

export function setLampBri(id, bri) {
  const lamp = findLamp(id)
  if (lamp) {
    lamp.bri = bri
    lamp.on = bri > 0
  }
}

function findLamp(id) {
  for (const group of [...store.roomGroups, ...store.zoneGroups]) {
    const lamp = group.lamps.find((l) => l.id === id)
    if (lamp) return lamp
  }
  return null
}
