function hexToRgb(hex) {
  const n = parseInt(hex.replace('#', ''), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function rgbToHex([r, g, b]) {
  const c = (v) => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, '0')
  return `#${c(r)}${c(g)}${c(b)}`
}

/** Multiply each channel by 0.45 + 0.55 * bri/100. bri is 0-100. */
export function dimmed(hex, bri) {
  const factor = 0.45 + 0.55 * (bri / 100)
  const [r, g, b] = hexToRgb(hex)
  return rgbToHex([r * factor, g * factor, b * factor])
}

/** Perceived luminance (0-255), used to pick a readable readout colour. */
function luminance(hex) {
  const [r, g, b] = hexToRgb(hex)
  return 0.299 * r + 0.587 * g + 0.114 * b
}

/** Composite `hex` at `alpha` over `base`, both hex colours. */
function compositeOver(hex, alpha, base) {
  const [r, g, b] = hexToRgb(hex)
  const [br, bg, bb] = hexToRgb(base)
  return [r * alpha + br * (1 - alpha), g * alpha + bg * (1 - alpha), b * alpha + bb * (1 - alpha)]
}

/**
 * Lamp row readout colour: composite the row tint over the row base at the
 * row alpha, then threshold on perceived luminance so it never disappears on
 * a bright tint.
 */
export function readoutColor(lampColorHex, alpha, baseHex, hiHex, loHex) {
  const composite = compositeOver(lampColorHex, alpha, baseHex)
  const l = 0.299 * composite[0] + 0.587 * composite[1] + 0.114 * composite[2]
  return l > 150 ? hiHex : loHex
}

/** Lamp glyph colour: light theme dims toward bri<=45, dark theme toward bri>=70. */
export function glyphColor(hex, bri, theme) {
  const b = theme === 'light' ? Math.min(bri, 45) : Math.max(bri, 70)
  return dimmed(hex, b)
}

/**
 * Group tint = dimmed(firstLitLamp.color, avgBriOfLitLamps); pillLineHex
 * when nothing is on.
 */
export function groupTint(lamps, pillLineHex) {
  const lit = lamps.filter((l) => l.on)
  if (lit.length === 0) return pillLineHex
  const avgBri = Math.round(lit.reduce((sum, l) => sum + l.bri, 0) / lit.length)
  return dimmed(lit[0].color, avgBri)
}

/** Average brightness of the lit lamps, rounded; null when none are on. */
export function groupPercent(lamps) {
  const lit = lamps.filter((l) => l.on)
  if (lit.length === 0) return null
  return Math.round(lit.reduce((sum, l) => sum + l.bri, 0) / lit.length)
}

/**
 * Scene gradient background: none -> pillLineHex, one -> flat colour,
 * many -> a linear-gradient across each action's colour. Each action's `hex`
 * already has its own brightness baked in (huectl/color.py's scene_colors
 * dims per-action, not via the generic `dimmed()` above) - see lib/huecolor.js.
 */
export function sceneGradient(actions, pillLineHex) {
  const colors = actions.filter((a) => a.on).map((a) => a.hex)
  if (colors.length === 0) return pillLineHex
  if (colors.length === 1) return colors[0]
  return `linear-gradient(105deg, ${colors.join(', ')})`
}
