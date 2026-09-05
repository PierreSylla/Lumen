function toHex(r, g, b) {
  const c = (v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')
  return `#${c(r)}${c(g)}${c(b)}`
}

/** xy (+ CIE Y=1) -> sRGB, gamut-normalized before gamma (this is the step
 * that keeps saturated hues in-gamut - dropping it reintroduces the
 * Wide-RGB bug). bri (0-100) scales the gamma-corrected result, floor 0.25. */
export function xyToHex(x, y, bri = 100) {
  if (y <= 0) return '#ffffff'
  const Y = 1.0
  const X = (Y / y) * x
  const Z = (Y / y) * (1.0 - x - y)
  let r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
  let g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
  let b = 0.0557 * X - 0.204 * Y + 1.057 * Z
  r = Math.max(0, r)
  g = Math.max(0, g)
  b = Math.max(0, b)
  const m = Math.max(r, g, b) || 1.0
  r /= m
  g /= m
  b /= m

  const gm = (c) => (c > 0.0031308 ? 1.055 * c ** (1 / 2.4) - 0.055 : 12.92 * c)
  const f = Math.max(0.25, (bri || 100) / 100)
  return toHex(gm(r) * 255 * f, gm(g) * 255 * f, gm(b) * 255 * f)
}

/** Mirek (153-500) -> warm/cool blend, matching huectl/color.py exactly. */
export function mirekToHex(mirek, bri = 100) {
  const m = Math.max(153, Math.min(500, mirek || 366))
  const tt = (m - 153) / (500 - 153)
  const cool = [200, 220, 255]
  const warm = [255, 165, 70]
  const f = Math.max(0.3, (bri || 100) / 100)
  const rgb = cool.map((c, i) => Math.min(255, (c + (warm[i] - c) * tt) * f))
  return toHex(...rgb)
}

const FALLBACK_HEX = '#ffd68c' // huectl/color.py base_light_color fallback (255,214,140)

/** A light's full-hue base colour (bri=100), matching base_light_color. */
export function baseLightColor(light) {
  const xy = light.color?.xy
  const mirek = light.color_temperature?.mirek
  if (xy) return xyToHex(xy.x ?? 0.33, xy.y ?? 0.33, 100)
  if (mirek) return mirekToHex(mirek, 100)
  return FALLBACK_HEX
}

/** One scene action's display colour, dimming baked in - matches scene_colors. */
export function sceneActionColor(action) {
  const bri = action.dimming?.brightness ?? 100
  const xy = action.color?.xy
  const mirek = action.color_temperature?.mirek
  if (xy) return xyToHex(xy.x ?? 0.33, xy.y ?? 0.33, bri)
  if (mirek) return mirekToHex(mirek, bri)
  return mirekToHex(366, bri)
}
