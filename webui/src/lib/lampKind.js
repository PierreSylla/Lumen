const RULES = [
  [/strip|gradient/, 'strip'],
  [/play|bloom|iris|go|signe|centris|bar|ensis/, 'bar'],
  [/spot|recessed/, 'spot'],
  [/ceiling|pendant/, 'ceiling'],
  [/floor/, 'floor'],
  [/table|desk/, 'table'],
  [/plug/, 'plug'],
  [/candle|luster|flood|vintage/, 'candle'],
]

export function lampKind(archetype) {
  const a = (archetype ?? '').toLowerCase()
  for (const [re, kind] of RULES) {
    if (re.test(a)) return kind
  }
  return 'bulb'
}
