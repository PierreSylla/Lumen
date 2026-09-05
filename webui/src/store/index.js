import { reactive } from 'vue'
import { sampleRoomGroups, sampleZoneGroups, sampleSceneSections } from '../data/sample.js'
import { buildViewModel } from '../lib/snapshot.js'
import { xyToHex, mirekToHex } from '../lib/huecolor.js'

export const store = reactive({
  roomGroups: sampleRoomGroups,
  zoneGroups: sampleZoneGroups,
  sceneSections: sampleSceneSections,
  bridgeOk: true,
  configured: true,
})

function api() {
  return window.pywebview?.api ?? null
}

export async function loadSnapshot() {
  const a = api()
  if (!a?.get_snapshot) return // dev-in-a-plain-browser: keep sample data

  const result = await a.get_snapshot()
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

function findLamp(id) {
  for (const group of [...store.roomGroups, ...store.zoneGroups]) {
    const lamp = group.lamps.find((l) => l.id === id)
    if (lamp) return lamp
  }
  return null
}

let reloadTimer = null
function scheduleReload() {
  clearTimeout(reloadTimer)
  reloadTimer = setTimeout(loadSnapshot, 700)
}

function patchLampFromSSE(fragment) {
  const lamp = findLamp(fragment.id)
  if (!lamp) return
  if (fragment.on) lamp.on = !!fragment.on.on
  if (fragment.dimming) lamp.bri = Math.round(fragment.dimming.brightness)
  if (fragment.color?.xy) lamp.color = xyToHex(fragment.color.xy.x, fragment.color.xy.y, 100)
  else if (fragment.color_temperature?.mirek) lamp.color = mirekToHex(fragment.color_temperature.mirek, 100)
}

/** Call once on app start, alongside initSnapshot(). */
export function initSSE() {
  window.__lumenSSE = (payload) => {
    if (payload.type === 'update') {
      for (const light of payload.lights) patchLampFromSSE(light)
    } else if (payload.type === 'change') {
      scheduleReload()
    }
  }
}

export function updateLampBriLocal(id, bri) {
  const lamp = findLamp(id)
  if (lamp) {
    lamp.bri = bri
    lamp.on = bri > 0
  }
}

export function writeLampOn(id, on) {
  const lamp = findLamp(id)
  if (lamp) lamp.on = on
  api()?.put_light(id, { on: { on } })
}

export function writeLampBri(id, bri) {
  updateLampBriLocal(id, bri)
  const payload = bri > 0 ? { on: { on: true }, dimming: { brightness: bri } } : { on: { on: false } }
  api()?.put_light(id, payload)
}

export function writeLampColor(id, hex, xy) {
  const lamp = findLamp(id)
  if (lamp) {
    lamp.color = hex
    lamp.on = true
  }
  api()?.put_light(id, { on: { on: true }, color: { xy: { x: xy[0], y: xy[1] } } })
}

export function writeLampMirek(id, mirek) {
  const lamp = findLamp(id)
  if (lamp) {
    lamp.color = mirekToHex(mirek, 100)
    lamp.on = true
  }
  api()?.put_light(id, { on: { on: true }, color_temperature: { mirek } })
}

function writeToGroupOrLamps(group, payload) {
  if (group.groupedLightId) {
    api()?.put_grouped_light(group.groupedLightId, payload)
  } else {
    for (const l of group.lamps) api()?.put_light(l.id, payload)
  }
}

export function writeGroupOn(group, on) {
  for (const l of group.lamps) l.on = on
  writeToGroupOrLamps(group, { on: { on } })
}

export function updateGroupBriLocal(group, pct) {
  for (const l of group.lamps) {
    l.bri = pct
    l.on = pct > 0
  }
}

export function writeGroupBri(group, pct) {
  updateGroupBriLocal(group, pct)
  writeToGroupOrLamps(group, pct > 0 ? { on: { on: true }, dimming: { brightness: pct } } : { on: { on: false } })
}

export async function recallScene(sceneId) {
  await api()?.recall_scene(sceneId)
  setTimeout(loadSnapshot, 600)
}
