function lamp(id, name, archetype, on, bri, color) {
  return { id, name, archetype, on, bri, color }
}

function scene(id, name, actions) {
  return { id, name, actions }
}

const livingCeiling = lamp('l1', 'Living room ceiling', 'ceiling', true, 80, '#ffb347')
const livingFloor = lamp('l2', 'Floor lamp', 'floor', true, 45, '#7ec0ee')
const livingStrip = lamp('l3', 'TV backlight strip', 'strip', false, 60, '#bb9af7')
const kitchenSpot1 = lamp('l4', 'Kitchen spot 1', 'spot', true, 100, '#fff4e0')
const kitchenSpot2 = lamp('l5', 'Kitchen spot 2', 'spot', true, 100, '#fff4e0')
const bedroomTable = lamp('l6', 'Bedside lamp', 'table', false, 30, '#ffa546')
const officeDesk = lamp('l7', 'Desk lamp', 'desk', true, 55, '#f0b429')
const hallwayPlug = lamp('l8', 'Hallway plug', 'plug', false, 0, '#ffffff')
const orphanCandle = lamp('l9', 'Old candle bulb', 'candle', true, 70, '#ffcf9e')

export const sampleRoomGroups = [
  {
    id: 'r-living',
    name: 'Living room',
    kind: 'room',
    lamps: [livingCeiling, livingFloor, livingStrip],
    scenes: [
      scene('s1', 'Movie night', [
        { color: '#ff8a3d', bri: 25, on: true },
        { color: '#3d6bff', bri: 40, on: true },
        { color: '#bb9af7', bri: 20, on: false },
      ]),
      scene('s2', 'Bright', [
        { color: '#ffe9c7', bri: 100, on: true },
        { color: '#ffe9c7', bri: 100, on: true },
      ]),
    ],
  },
  {
    id: 'r-kitchen',
    name: 'Kitchen',
    kind: 'room',
    lamps: [kitchenSpot1, kitchenSpot2],
    scenes: [scene('s3', 'Cooking', [{ color: '#fff4e0', bri: 100, on: true }])],
  },
  {
    id: 'r-bedroom',
    name: 'Bedroom',
    kind: 'room',
    lamps: [bedroomTable],
    scenes: [],
  },
  {
    id: 'r-office',
    name: 'Office',
    kind: 'room',
    lamps: [officeDesk],
    scenes: [],
  },
  {
    id: 'r-hallway',
    name: 'Hallway',
    kind: 'room',
    lamps: [hallwayPlug],
    scenes: [],
  },
  {
    id: 'others',
    name: 'Others',
    kind: 'ungrouped',
    lamps: [orphanCandle],
    scenes: [],
  },
]

export const sampleZoneGroups = [
  {
    id: 'z-downstairs',
    name: 'Downstairs',
    kind: 'zone',
    lamps: [livingCeiling, livingFloor, kitchenSpot1, kitchenSpot2],
    scenes: [
      scene('s4', 'Evening', [
        { color: '#ffb347', bri: 60, on: true },
        { color: '#fff4e0', bri: 80, on: true },
      ]),
    ],
  },
  {
    id: 'z-reading',
    name: 'Reading',
    kind: 'zone',
    lamps: [livingFloor, officeDesk],
    scenes: [],
  },
]

export const sampleSceneSections = [
  { id: 'r-living', name: 'Living room', kind: 'room', scenes: sampleRoomGroups[0].scenes },
  { id: 'r-kitchen', name: 'Kitchen', kind: 'room', scenes: sampleRoomGroups[1].scenes },
  { id: 'z-downstairs', name: 'Downstairs', kind: 'zone', scenes: sampleZoneGroups[0].scenes },
]
