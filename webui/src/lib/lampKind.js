const ARCHETYPE_KIND = {
  ceiling: 'ceiling',
  pendant: 'ceiling',
  table: 'table',
  desk: 'table',
  floor: 'floor',
  strip: 'strip',
  gradient: 'strip',
  play: 'bar',
  bloom: 'bar',
  iris: 'bar',
  go: 'bar',
  signe: 'bar',
  centris: 'bar',
  bar: 'bar',
  ensis: 'bar',
  spot: 'spot',
  recessed: 'spot',
  plug: 'plug',
  candle: 'candle',
  luster: 'candle',
  flood: 'candle',
  vintage: 'candle',
}

export function lampKind(archetype) {
  return ARCHETYPE_KIND[archetype] ?? 'bulb'
}
