import { baseLightColor, sceneActionColor } from './huecolor.js'

function nameOf(res) {
  return res.metadata?.name ?? '?'
}

function byName(a, b) {
  return a.name.localeCompare(b.name)
}

function findGroupedLightId(res) {
  return res.services?.find((s) => s.rtype === 'grouped_light')?.rid ?? null
}

function toLampViewModel(light) {
  return {
    id: light.id,
    name: nameOf(light),
    archetype: light.metadata?.archetype ?? '',
    on: !!light.on?.on,
    bri: Math.round(light.dimming?.brightness ?? 100),
    color: baseLightColor(light),
  }
}

function toSceneViewModel(scene) {
  return {
    id: scene.id,
    name: nameOf(scene),
    // Raw CLIP v2 group ref, kept even for an orphan scene (unknown group) -
    // the Scene Editor's re-capture needs it regardless of whether the group
    // resolved to a room/zone card.
    groupId: scene.group?.rid ?? null,
    groupKind: scene.group?.rtype ?? null,
    actions: (scene.actions ?? []).map((a) => ({
      on: a.action?.on?.on !== false,
      hex: sceneActionColor(a.action ?? {}),
    })),
  }
}

// A room's children are devices (rid = device id, resolved via each light's
// own owner.rid); a zone's children are lights directly (rid = light id).
function lightsOfGroup(group, lightsById, lightsByOwner) {
  const out = []
  for (const child of group.children ?? []) {
    if (child.rtype === 'light' && lightsById.has(child.rid)) {
      out.push(lightsById.get(child.rid))
    } else if (child.rtype === 'device') {
      out.push(...(lightsByOwner.get(child.rid) ?? []))
    }
  }
  return out
}

function scenesFor(groupId, scenes) {
  return scenes.filter((s) => s.group?.rid === groupId)
}

export function buildViewModel(raw) {
  const lights = raw.light ?? []
  const rooms = raw.room ?? []
  const zones = raw.zone ?? []
  const scenes = raw.scene ?? []

  const lightsById = new Map(lights.map((l) => [l.id, l]))
  const lightsByOwner = new Map()
  for (const l of lights) {
    const ownerId = l.owner?.rid
    if (!lightsByOwner.has(ownerId)) lightsByOwner.set(ownerId, [])
    lightsByOwner.get(ownerId).push(l)
  }

  function buildGroup(res, kind) {
    return {
      id: res.id,
      name: nameOf(res),
      kind,
      groupedLightId: findGroupedLightId(res),
      lamps: lightsOfGroup(res, lightsById, lightsByOwner).map(toLampViewModel).sort(byName),
      scenes: scenesFor(res.id, scenes).map(toSceneViewModel).sort(byName),
    }
  }

  const roomGroups = rooms.map((r) => buildGroup(r, 'room')).sort(byName)
  const zoneGroups = zones.map((z) => buildGroup(z, 'zone')).sort(byName)

  // Lights in neither any room nor any zone -> synthetic "Others" room card.
  const assigned = new Set()
  for (const g of [...roomGroups, ...zoneGroups]) for (const l of g.lamps) assigned.add(l.id)
  const orphanLamps = lights
    .filter((l) => !assigned.has(l.id))
    .map(toLampViewModel)
    .sort(byName)
  if (orphanLamps.length) {
    roomGroups.push({ id: 'others', name: 'Others', kind: 'ungrouped', groupedLightId: null, lamps: orphanLamps, scenes: [] })
  }

  // One scenes-page section per room/zone (even with zero scenes, so "+ NEW"
  // stays reachable), plus "Other scenes" for scenes with an unknown group.
  const sceneSections = [...roomGroups, ...zoneGroups]
    .filter((g) => g.id !== 'others')
    .map((g) => ({ id: g.id, name: g.name, kind: g.kind, scenes: g.scenes }))

  const knownGroupIds = new Set([...rooms, ...zones].map((g) => g.id))
  const orphanScenes = scenes
    .filter((s) => !knownGroupIds.has(s.group?.rid))
    .map(toSceneViewModel)
    .sort(byName)
  if (orphanScenes.length) {
    sceneSections.push({ id: 'other-scenes', name: 'Other scenes', kind: null, scenes: orphanScenes })
  }

  return { roomGroups, zoneGroups, sceneSections }
}
