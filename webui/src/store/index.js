import { reactive } from 'vue'
import { sampleRoomGroups, sampleZoneGroups, sampleSceneSections } from '../data/sample.js'
import { buildViewModel } from '../lib/snapshot.js'

export const store = reactive({
  roomGroups: sampleRoomGroups,
  zoneGroups: sampleZoneGroups,
  sceneSections: sampleSceneSections,
  bridgeOk: true,
  configured: true,
})

export async function loadSnapshot() {
  const api = window.pywebview?.api
  if (!api?.get_snapshot) return // dev-in-a-plain-browser: keep sample data

  const result = await api.get_snapshot()
  if (result.error === 'not_configured') {
    store.bridgeOk = false
    store.configured = false
    return
  }
  if (result.error) {
    store.bridgeOk = false
    return
  }

  const vm = buildViewModel(result.data)
  store.roomGroups = vm.roomGroups
  store.zoneGroups = vm.zoneGroups
  store.sceneSections = vm.sceneSections
  store.bridgeOk = true
  store.configured = true
}

export function initSnapshot() {
  const ready = () => window.pywebview?.api?.get_snapshot
  if (ready()) {
    loadSnapshot()
    return
  }
  const timer = setInterval(() => {
    if (ready()) {
      clearInterval(timer)
      loadSnapshot()
    }
  }, 100)
  setTimeout(() => clearInterval(timer), 10000)
}

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
