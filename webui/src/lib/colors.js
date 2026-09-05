export function hexToRgb(hex) {
  const n = parseInt(hex.replace('#', ''), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

export function rgbToHex([r, g, b]) {
  const c = (v) => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, '0')
  return `#${c(r)}${c(g)}${c(b)}`
}

/** HSV (h: 0-360, s/v: 0-1) -> RGB (0-255 each). UI-only (the colour wheel),
 * not part of the huectl/color.py bridge-format port - see lib/huecolor.js. */
export function hsvToRgb(h, s, v) {
  const c = v * s
  const hh = h / 60
  const x = c * (1 - Math.abs((hh % 2) - 1))
  const m = v - c
  const [r, g, b] = hh < 1 ? [c, x, 0] : hh < 2 ? [x, c, 0] : hh < 3 ? [0, c, x] : hh < 4 ? [0, x, c] : hh < 5 ? [x, 0, c] : [c, 0, x]
  return [(r + m) * 255, (g + m) * 255, (b + m) * 255]
}

/** RGB (0-255 each) -> [hue 0-360, sat 0-1], ignoring value. Used only to
 * position the colour wheel's handle for the lamp's current colour. */
export function rgbToHueSat(r, g, b) {
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const d = max - min
  const s = max === 0 ? 0 : d / max
  let h = 0
  if (d !== 0) {
    if (max === r) h = ((g - b) / d) % 6
    else if (max === g) h = (b - r) / d + 2
    else h = (r - g) / d + 4
    h *= 60
    if (h < 0) h += 360
  }
  return [h, s]
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
