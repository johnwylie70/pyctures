/**
 * visualfx.js: effects for a scene. Draw some shapes, then turn one on.
 *
 *   const { kaleidoscope, glow, trails } = await use("visualfx.js")     (a pictures.js scene)
 *   import { kaleidoscope, glow, trails } from "./visualfx.js"          (any page with one canvas)
 *
 *   kaleidoscope(8)                         on, eight segments
 *   glow(0.8)                               bright things shine
 *   const trail = trails(0.5, { zoom: 1.5, spin: 20 })
 *   trail.spin = 40                         a setting is a plain property: change it any time
 *   glowing.strength = () => 0.3 + bass()   or give it a function, asked every frame
 *
 * EFFECTS APPLY IN THE ORDER THEY ARE TURNED ON, to everything the scene has drawn, 2D or 3D. Each has
 * `off()`, `on()` and `remove()`, and `amount` (0 to 1: how much of it is mixed in). `clearEffects()`
 * takes them all away. `look("dream")` is several at once.
 *
 * THE GRAPHICS CARD DOES THE WORK. The scene's canvas is handed to it as a picture once a frame, each
 * effect is a small program run over every pixel, and the result is shown on a canvas of its own laid
 * exactly over the scene's. A scene with no effect on has no such canvas and costs nothing.
 *
 * THE SAME FRAMES EVERY TIME. An effect sees only the picture, its own last frame (trails), its settings
 * and the scene's clock: never the time of day. Grain and glitches come from a seed. So a scene stepped
 * a frame at a time by a video recorder gives exactly the picture it would have given.
 *
 * MUSIC: `listenTo(soundOutput())` (or a synth, a song, the microphone: anything with `samples()`), then
 * `bass()`, `mids()`, `highs()`, `loudness()` and `pulse()` are numbers from 0 to 1 to use anywhere.
 * `react(glowing, "strength", "bass", { from: 0.3, to: 1.2 })` ties a setting to one in a line.
 *
 * YOUR OWN: `shader("vec4 effect(vec2 uv) { return texture(picture, uv).bgra; }")`. See the README.
 *
 * An effect is also something a dial can turn (dials.js): it has `set`, `get` and `describe`.
 * The Python spellings (`zoom_blur`, `clear_effects`) are understood wherever a name is looked for.
 *
 * MIT licence.
 */

const version = '0.0.0'

const LAYER = Symbol.for('effects.pipeline')
let spare = null // the last scene's context and programs, for the next
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v)
const isPlain = (v) => v != null && typeof v === 'object' && Object.getPrototypeOf(v) === Object.prototype
const camel = (name) => String(name).replace(/_([a-z])/g, (_, c) => c.toUpperCase())
/** A spec's keys in one spelling: zoom_step is zoomStep, color is colour. */
const SPELLING = { color: 'colour', colors: 'colours' }
const spelled = (spec) => {
  const out = {}
  for (const key in spec) { const k = camel(key); out[SPELLING[k] || k] = spec[key] }
  return out
}

// --- colours: anything the page understands ("gold", "#f80", "rgb(…)"), as three numbers from 0 to 1
const colours = new Map()
let swatch = null
function rgb(colour) {
  if (Array.isArray(colour) || ArrayBuffer.isView(colour)) return colour.length >= 3 && colour[0] <= 1 && colour[1] <= 1 && colour[2] <= 1 ? [colour[0], colour[1], colour[2]] : [colour[0] / 255, colour[1] / 255, colour[2] / 255]
  let found = colours.get(colour)
  if (!found) {
    swatch ||= Object.assign(document.createElement('canvas'), { width: 1, height: 1 }).getContext('2d', { willReadFrequently: true })
    swatch.fillStyle = '#000'
    swatch.fillStyle = String(colour)
    const said = swatch.fillStyle
    swatch.fillStyle = '#fff'
    swatch.fillStyle = String(colour)
    // A colour the page does not know leaves the last one in place: black one time and white the next.
    if (said !== swatch.fillStyle) throw new Error(`"${colour}" is not a colour this page knows. Try a name ("gold", "deepskyblue") or a code ("#ff8800")`)
    swatch.clearRect(0, 0, 1, 1)
    swatch.fillRect(0, 0, 1, 1)
    const [r, g, b] = swatch.getImageData(0, 0, 1, 1).data
    found = [r / 255, g / 255, b / 255]
    colours.set(colour, found)
  }
  return found
}

/** Palettes by name: a few colours a number runs through, round and round. A list of colours is one too. */
const PALETTES = {
  rainbow: ['#ff2a2a', '#ffd92a', '#3cff5a', '#2ad4ff', '#5a3cff', '#ff2ad4'],
  fire: ['#000000', '#5a0a00', '#d43a00', '#ff9a1a', '#ffe98a', '#5a0a00'],
  ocean: ['#02102a', '#0a3a7a', '#1a8ad4', '#6ae0e0', '#e8fff8', '#0a3a7a'],
  sunset: ['#1a0a3a', '#6a1a7a', '#e0407a', '#ff8a3a', '#ffd86a', '#6a1a7a'],
  neon: ['#0a001a', '#ff1ad9', '#1affea', '#f6ff1a', '#7a1aff', '#1affea'],
  candy: ['#ff8ad4', '#ffd0e8', '#8ad4ff', '#b8ffd0', '#fff0a0', '#d0a0ff'],
  forest: ['#04140a', '#0e4a22', '#3a8a2a', '#a8d44a', '#f0f0a0', '#0e4a22'],
  ice: ['#020818', '#103a6a', '#4a9ae0', '#b8e8ff', '#ffffff', '#4a9ae0'],
  lava: ['#1a0000', '#8a0a00', '#ff3a00', '#ff9a00', '#ffe27a', '#ff5a00'],
  mono: ['#000000', '#ffffff'],
  thermal: ['#000000', '#20008c', '#cc0077', '#ff3000', '#ffd000', '#ffffff'],
  aurora: ['#00ff9a', '#00b0ff', '#8a2be2', '#00ff9a'],
  gameboy: ['#0f380f', '#306230', '#8bac0f', '#9bbc0f'],
  c64: ['#000000', '#352879', '#6c5eb5', '#9a6759', '#b8c76f', '#ffffff'],
  amiga: ['#000022', '#0055aa', '#ff8800', '#ffffff'],
  pico: ['#1d2b53', '#7e2553', '#ff004d', '#ffa300', '#29adff', '#fff1e8'],
}
const palettes = new Map()
function paletteOf(value) {
  const key = Array.isArray(value) ? value.join('|') : String(value)
  let found = palettes.get(key)
  if (!found) {
    const list = Array.isArray(value) ? value : PALETTES[String(value).toLowerCase()]
    if (!list || !list.length) throw new Error(`There is no palette called "${value}". There are ${Object.keys(PALETTES).join(', ')}, or give a list of colours: ["navy", "magenta", "gold"]`)
    const data = new Float32Array(18)
    const n = Math.min(6, list.length)
    for (let i = 0; i < 6; i++) data.set(rgb(list[Math.min(i, n - 1)]), i * 3)
    found = { data, count: n }
    palettes.set(key, found)
  }
  return found
}

// --------------------------------------------------------------------------------------------
// The programs. Every effect is written as `vec4 effect(vec2 uv)`: the colour at one place of the
// picture, where uv runs from (0, 0) at the top left to (1, 1) at the bottom right. These are the
// names it can use, and they are the names a shader of your own is given (see `shader`).
const VERTEX = `#version 300 es
out vec2 uv;
uniform float flip;
void main() {
  vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
  uv = vec2(p.x, flip > 0.5 ? 1.0 - p.y : p.y);
  gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}`
const HEAD = `#version 300 es
precision highp float;
precision highp int;
in vec2 uv;
out vec4 colour_out;
uniform sampler2D picture;    // what this effect is given: the scene, after the effects before it
uniform sampler2D previous;   // what this effect made last frame (black on the first)
uniform sampler2D spectrum;   // the sound, low notes at the left: texture(spectrum, vec2(x, 0.5)).r
uniform sampler2D waveform;   // the sound's wave: texture(waveform, vec2(x, 0.5)).r, 0.5 is silence
uniform vec2 resolution;      // the picture's size in real pixels
uniform vec2 size;            // the picture's size in the scene's points (what width and height are)
uniform float time;           // seconds on the scene's clock
uniform float dt;             // seconds since the last frame
uniform float frame;          // frames so far
uniform float amount;         // this effect's amount, 0 to 1
uniform float seed;
uniform float bass, mids, highs, loudness, pulse;   // the music, 0 to 1 (0 when nothing is listened to)
uniform vec3 pal[6];
uniform float palCount;
const float TAU = 6.283185307179586;
float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
vec2 turn(vec2 p, float a) { float c = cos(a), s = sin(a); return vec2(c * p.x - s * p.y, s * p.x + c * p.y); }
// Whole-number hashing: the same on every graphics card, which a sine of a big number is not.
uint scramble(uint x) { x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16; return x; }
float hash(vec2 p) { ivec2 q = ivec2(floor(p)); return float(scramble(uint(q.x) ^ scramble(uint(q.y) + 0x9e3779b9U)) >> 8) / 16777216.0; }
float hash(vec3 p) { ivec3 q = ivec3(floor(p)); return float(scramble(uint(q.x) ^ scramble(uint(q.y) + 0x9e3779b9U ^ scramble(uint(q.z) + 0x85ebca6bU))) >> 8) / 16777216.0; }
float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { v += a * noise(p); p = p * 2.03 + 17.0; a *= 0.5; } return v; }
// A colour's hue turned by an angle: a turn about the line of greys.
vec3 hueTurn(vec3 c, float a) { const vec3 k = vec3(0.57735026919); float cs = cos(a), sn = sin(a); return c * cs + cross(k, c) * sn + k * dot(k, c) * (1.0 - cs); }
vec3 palette(float t) {
  float x = fract(t) * palCount;
  int i = int(floor(x));
  float f = x - floor(x);
  return mix(pal[i], pal[(i + 1) % int(palCount)], f * f * (3.0 - 2.0 * f));
}
// A palette from its first colour to its last, once, without coming round again.
vec3 ramp(float t) { return palette(clamp(t, 0.0, 0.999) * (palCount - 1.0) / palCount); }
// Cells, as in a honeycomb drawn by hand: xy is the nearest cell's own point, z how far this place is from the cell's edge.
vec3 cells(vec2 p) {
  vec2 i = floor(p), best = i;
  float d1 = 9.0, d2 = 9.0;
  for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
    vec2 g = i + vec2(x, y), o = g + vec2(hash(g), hash(g + vec2(37.0, 91.0)));
    float d = distance(p, o);
    if (d < d1) { d2 = d1; d1 = d; best = o; } else if (d < d2) d2 = d;
  }
  return vec3(best, d2 - d1);
}
float most(vec3 c) { return max(c.r, max(c.g, c.b)); }
// Off the edge of the picture it is seen again, mirrored: no seams and no stretched borders.
vec2 mirrored(vec2 q) { return 1.0 - abs(mod(q, 2.0) - 1.0); }
vec4 look(vec2 q) { return texture(picture, mirrored(q)); }
`
const MAIN = `
void main() {
  vec4 c = effect(uv);
  if (amount < 1.0) c = mix(texture(picture, uv), c, amount);
  colour_out = vec4(clamp(c.rgb, 0.0, 1.0), 1.0);
}`
// A backdrop is behind what the scene drew: it shows wherever the scene left the picture clear.
const MAIN_BACKDROP = `
void main() {
  vec4 s = texture(picture, uv);
  colour_out = vec4(s.rgb + clamp(backdrop(uv), 0.0, 1.0) * amount * (1.0 - s.a), 1.0);
}`

const COPY = `void main() { colour_out = vec4(texture(picture, uv).rgb, 1.0); }`
// Two pictures mixed, with a grain too fine to see that stops smooth shades showing as bands.
const BLEND = `uniform sampler2D other; uniform float add;
void main() {
  vec3 a = texture(picture, uv).rgb, b = texture(other, uv).rgb;
  vec3 c = add > 0.0 ? a + b * add * amount : mix(a, b, amount);
  colour_out = vec4(c + (hash(uv * resolution) - 0.5) / 255.0, 1.0);
}`
const GAUSS = `uniform vec2 dir; uniform float sigma;
void main() {
  vec3 sum = texture(picture, uv).rgb;
  float total = 1.0, k = 0.5 / (sigma * sigma);
  for (int i = 0; i < 5; i++) {
    float a = float(2 * i + 1), b = a + 1.0;
    float wa = exp(-a * a * k), wb = exp(-b * b * k), w = wa + wb;
    if (w < 1e-5) break;
    vec2 o = dir * ((a * wa + b * wb) / w);
    sum += (texture(picture, uv + o).rgb + texture(picture, uv - o).rgb) * w;
    total += 2.0 * w;
  }
  colour_out = vec4(sum / total, 1.0);
}`
// What is bright enough to glow, at half size. Each of the four pixels that become one is judged alone, so a
// small bright thing counts for what it is and does not flicker as it crosses pixels.
const BRIGHT = `uniform float threshold; uniform vec2 texel;
vec3 lit(vec2 q) { vec3 c = texture(picture, q).rgb; float l = max(c.r, max(c.g, c.b)); return c * smoothstep(threshold - 0.08, threshold + 0.12, l); }
void main() { colour_out = vec4((lit(uv + texel * vec2(-1, -1)) + lit(uv + texel * vec2(1, -1)) + lit(uv + texel * vec2(-1, 1)) + lit(uv + texel * vec2(1, 1))) * 0.25, 1.0); }`
const SHRINK = `uniform vec2 texel;
void main() {
  vec3 c = texture(picture, uv).rgb * 4.0;
  c += texture(picture, uv + texel * vec2(-1, -1)).rgb + texture(picture, uv + texel * vec2(1, -1)).rgb;
  c += texture(picture, uv + texel * vec2(-1, 1)).rgb + texture(picture, uv + texel * vec2(1, 1)).rgb;
  colour_out = vec4(c / 8.0, 1.0);
}`
const GROW = `uniform sampler2D other; uniform vec2 texel; uniform float weight;
void main() {
  vec3 c = texture(picture, uv + texel * vec2(-2, 0)).rgb + texture(picture, uv + texel * vec2(2, 0)).rgb;
  c += texture(picture, uv + texel * vec2(0, -2)).rgb + texture(picture, uv + texel * vec2(0, 2)).rgb;
  c += 2.0 * (texture(picture, uv + texel * vec2(-1, -1)).rgb + texture(picture, uv + texel * vec2(1, -1)).rgb);
  c += 2.0 * (texture(picture, uv + texel * vec2(-1, 1)).rgb + texture(picture, uv + texel * vec2(1, 1)).rgb);
  colour_out = vec4(c / 12.0 * weight + texture(other, uv).rgb, 1.0);
}`
// Trails: last frame's picture, moved a little and a little fainter, with this frame's on top.
const TRAIL = `uniform float keep, grow, spun, hued, cut; uniform vec2 centre, moved;
void main() {
  vec2 q = (turn(uv * size - centre, -spun) / grow + centre - moved) / size;
  vec3 old = vec3(0.0);
  if (q.x >= 0.0 && q.x <= 1.0 && q.y >= 0.0 && q.y <= 1.0) old = texture(previous, q).rgb;
  if (hued != 0.0) old = hueTurn(old, hued);
  old = max(old * keep - cut, 0.0);
  colour_out = vec4(max(texture(picture, uv).rgb, old), 1.0);
}`

// --------------------------------------------------------------------------------------------
// The effects. `order` is what the plain arguments mean: kaleidoscope(8) is { segments: 8 }.
// A setting is [default, min, max] and what kind it is. Lengths are in the scene's points and angles in
// degrees, so a scene looks the same on any screen; x and y are a place in the scene (the middle if not given).
const DEFS = {}
const num = (value, min, max, more) => ({ kind: 'float', default: value, min, max, ...more })
const whole = (value, min, max) => ({ kind: 'int', default: value, min, max, step: 1 })
const angle = (value, min = -360, max = 360) => ({ kind: 'float', default: value, min, max, unit: 'degrees' })
const place = () => ({ kind: 'float', default: null, min: 0, max: 4000, place: true })
const flag = (value) => ({ kind: 'bool', default: value, min: 0, max: 1 })
const choice = (value, choices) => ({ kind: 'choice', default: value, choices })
const colour = (value) => ({ kind: 'colour', default: value })
const pal = (value) => ({ kind: 'palette', default: value })
const AMOUNT = num(1, 0, 1)
function define(name, order, settings, glsl, more) {
  DEFS[name] = { name, order, settings: { ...settings, amount: AMOUNT }, glsl, ...more }
}
const PLACE = `vec2 c = vec2(x, y), p = uv * size - c;`

// --- shapes of the picture
define('kaleidoscope', ['segments'], { segments: whole(8, 2, 32), angle: angle(0), zoom: num(1, 0.2, 5), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float wedge = TAU / max(2.0, floor(segments + 0.5));
  float a = mod(atan(p.y, p.x) - angle, wedge);
  a = abs(a - wedge * 0.5) + angle;
  return look((c + length(p) * vec2(cos(a), sin(a)) / zoom) / size);
}`)
define('mirror', ['side'], { side: choice('left', ['left', 'right', 'top', 'bottom', 'four']) }, `
vec4 effect(vec2 uv) {
  vec2 q = uv;
  if (side < 0.5) q.x = 0.5 - abs(q.x - 0.5);
  else if (side < 1.5) q.x = 0.5 + abs(q.x - 0.5);
  else if (side < 2.5) q.y = 0.5 - abs(q.y - 0.5);
  else if (side < 3.5) q.y = 0.5 + abs(q.y - 0.5);
  else q = 0.5 - abs(q - 0.5);
  return texture(picture, q);
}`)
define('pixelate', ['size'], { size: num(10, 1, 100) }, `
vec4 effect(vec2 uv) {
  float s = max(cell, size.x / resolution.x);
  vec2 p = uv * size - size * 0.5;
  return texture(picture, ((floor(p / s) + 0.5) * s + size * 0.5) / size);
}`, { rename: { size: 'cell' } })
define('waves', ['size'], { size: num(12, 0, 100), length: num(160, 10, 1000), speed: num(0.5, -5, 5) }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size;
  vec2 d = vec2(sin(TAU * (p.y / len + time * speed)), cos(TAU * (p.x / len + time * speed * 0.8)));
  return look((p + d * big) / size);
}`, { rename: { size: 'big', length: 'len' } })
define('ripple', ['size'], { size: num(8, 0, 100), length: num(60, 10, 1000), speed: num(1, -5, 5), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float d = length(p);
  return look((c + p + normalize(p + 1e-5) * big * sin(TAU * (d / len - time * speed))) / size);
}`, { rename: { size: 'big', length: 'len' } })
define('wobble', ['size'], { size: num(14, 0, 100), scale: num(120, 10, 1000), speed: num(0.4, -5, 5) }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size, q = p / scale;
  vec2 d = vec2(noise(q + vec2(time * speed, 3.1)), noise(q + vec2(17.3, -time * speed))) - 0.5;
  return look((p + d * 2.0 * big) / size);
}`, { rename: { size: 'big' } })
define('swirl', ['angle'], { angle: angle(180, -1440, 1440), radius: num(0, 0, 2000), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float r = radius > 0.0 ? radius : min(size.x, size.y) * 0.5;
  float f = max(0.0, 1.0 - length(p) / r);
  return look((c + turn(p, angle * f * f)) / size);
}`)
define('fisheye', ['strength'], { strength: num(0.5, -1, 1), radius: num(0, 0, 2000), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float r = radius > 0.0 ? radius : length(size) * 0.5;
  float d = length(p) / r;
  if (d < 1.0) p *= 1.0 - strength * 0.75 * (1.0 - d * d);
  return look((c + p) / size);
}`)
define('tunnel', ['speed'], { speed: num(0.4, -5, 5), repeat: whole(2, 1, 12), depth: num(0.5, 0.05, 4), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float m = min(size.x, size.y) * 0.5, d = max(length(p), 0.5);
  vec2 st = vec2(atan(p.y, p.x) / TAU * repeat * 2.0, depth * m / d + time * speed);
  return look(st) * smoothstep(0.0, 0.5, d / m);
}`)
define('tile', ['across'], { across: whole(3, 1, 40), down: whole(0, 0, 40), flip: flag(false) }, `
vec4 effect(vec2 uv) {
  vec2 q = uv * vec2(across, down > 0.5 ? down : across);
  return texture(picture, flipped > 0.5 ? mirrored(q) : fract(q));
}`, { rename: { flip: 'flipped' } })

// --- blurs that are one pass
define('zoomBlur', ['strength'], { strength: num(0.25, 0, 1), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float j = hash(uv * resolution);
  vec3 sum = vec3(0.0);
  for (int i = 0; i < 14; i++) sum += look((c + p * (1.0 - strength * (float(i) + j) / 14.0)) / size).rgb;
  return vec4(sum / 14.0, 1.0);
}`)
define('spinBlur', ['angle'], { angle: angle(8, -90, 90), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float j = hash(uv * resolution);
  vec3 sum = vec3(0.0);
  for (int i = 0; i < 14; i++) sum += look((c + turn(p, angle * ((float(i) + j) / 14.0 - 0.5))) / size).rgb;
  return vec4(sum / 14.0, 1.0);
}`)
define('rgbSplit', ['size'], { size: num(4, 0, 60), angle: angle(0), spread: flag(false) }, `
vec4 effect(vec2 uv) {
  vec2 d = spread > 0.5 ? (uv - 0.5) * 2.0 * big : big * vec2(cos(angle), sin(angle));
  d /= size;
  return vec4(texture(picture, uv + d).r, texture(picture, uv).g, texture(picture, uv - d).b, 1.0);
}`, { rename: { size: 'big' } })

// --- colours
define('hue', ['shift'], { shift: angle(90), speed: num(0, -720, 720) }, `
vec4 effect(vec2 uv) { return vec4(hueTurn(texture(picture, uv).rgb, shift + radians(speed) * time), 1.0); }`)
define('saturate', ['strength'], { strength: num(1.6, 0, 4) }, `
vec4 effect(vec2 uv) { vec3 c = texture(picture, uv).rgb; return vec4(mix(vec3(luma(c)), c, strength), 1.0); }`)
define('brighten', ['strength'], { strength: num(1.3, 0, 4) }, `
vec4 effect(vec2 uv) { return vec4(texture(picture, uv).rgb * strength, 1.0); }`)
define('contrast', ['strength'], { strength: num(1.4, 0, 4) }, `
vec4 effect(vec2 uv) { return vec4((texture(picture, uv).rgb - 0.5) * strength + 0.5, 1.0); }`)
define('invert', [], {}, `
vec4 effect(vec2 uv) { return vec4(1.0 - texture(picture, uv).rgb, 1.0); }`)
define('posterize', ['levels'], { levels: whole(4, 2, 16) }, `
vec4 effect(vec2 uv) { float n = max(2.0, floor(levels + 0.5)); return vec4(min(floor(texture(picture, uv).rgb * n), n - 1.0) / (n - 1.0), 1.0); }`)
define('tint', ['colour'], { colour: colour('gold') }, `
vec4 effect(vec2 uv) { return vec4(texture(picture, uv).rgb * colour, 1.0); }`)
define('duotone', ['dark', 'light'], { dark: colour('midnightblue'), light: colour('gold') }, `
vec4 effect(vec2 uv) { return vec4(mix(dark, light, luma(texture(picture, uv).rgb)), 1.0); }`)
define('colourCycle', ['palette'], { palette: pal('rainbow'), speed: num(0.3, -5, 5), bands: num(1, 0.1, 8) }, `
vec4 effect(vec2 uv) {
  float l = luma(texture(picture, uv).rgb);
  return vec4(palette(l * bands + time * speed) * smoothstep(0.0, 0.12, l), 1.0);
}`)

// --- screens, film and print
define('scanlines', ['strength'], { strength: num(0.5, 0, 1), size: num(3, 1, 40) }, `
vec4 effect(vec2 uv) {
  float s = max(gap, 2.0 * size.y / resolution.y);
  return vec4(texture(picture, uv).rgb * (1.0 - strength * (0.5 + 0.5 * cos(TAU * uv.y * size.y / s))), 1.0);
}`, { rename: { size: 'gap' } })
define('crt', ['curve'], { curve: num(0.18, 0, 1), lines: num(0.45, 0, 1), size: num(3, 1, 40) }, `
vec4 effect(vec2 uv) {
  vec2 q = uv * 2.0 - 1.0;
  q *= 1.0 + curve * 0.5 * q.yx * q.yx;
  vec2 st = q * 0.5 + 0.5;
  // The glass ends in a soft rounded edge, and its three colours do not quite meet near it.
  vec2 e = 1.0 - smoothstep(vec2(1.0) - 6.0 / size, vec2(1.0), abs(q));
  float fringe = 0.0015 * (1.0 + 2.0 * dot(q, q));
  vec3 c = vec3(texture(picture, st + vec2(fringe, 0.0)).r, texture(picture, st).g, texture(picture, st - vec2(fringe, 0.0)).b);
  float s = max(gap, 2.0 * size.y / resolution.y);
  c *= 1.0 - lines * (0.5 + 0.5 * cos(TAU * st.y * size.y / s));
  // Thin stripes of red, green and blue, as a tube's dots are: a third of a line apart.
  float stripe = fract(st.x * size.x / s);
  c *= 1.0 + lines * 0.35 * (0.5 - smoothstep(vec3(0.0), vec3(0.34), abs(stripe - vec3(0.17, 0.5, 0.83))));
  c *= (1.0 + 0.25 * lines) * (1.0 - 0.35 * curve * dot(q, q));
  return vec4(c * e.x * e.y, 1.0);
}`, { rename: { size: 'gap' } })
define('glitch', ['strength'], { strength: num(0.5, 0, 1), speed: num(1, 0, 10), seed: whole(1, 0, 9999) }, `
vec4 effect(vec2 uv) {
  float t = floor(time * 10.0 * speed) + seed * 131.0;
  vec2 q = uv;
  // Blocks that jump sideways, a few at a time and not on every beat of the clock.
  float busy = step(1.0 - 0.6 * strength, hash(vec2(t, 5.0)));
  vec2 cell = floor(uv * vec2(3.0, 9.0 + 6.0 * hash(vec2(t, 1.0))));
  float r = hash(vec3(cell, t));
  if (r > 1.0 - 0.3 * strength * busy) q.x += (hash(vec3(cell, t + 9.0)) - 0.5) * 0.3 * strength;
  // One line where the picture tears.
  float tear = hash(vec2(t, 2.0)), band = abs(uv.y - tear);
  if (band < 0.012 * (1.0 + 3.0 * hash(vec2(t, 3.0))) && hash(vec2(t, 4.0)) < strength) q.x += (hash(vec2(t, 7.0)) - 0.5) * 0.25;
  float split = (0.002 + 0.02 * busy * hash(vec2(t, 8.0))) * strength;
  vec3 c = vec3(look(q + vec2(split, 0.0)).r, look(q).g, look(q - vec2(split, 0.0)).b);
  // A band of snow that rolls down.
  float roll = fract(uv.y - time * 0.23 * speed);
  c += strength * 0.12 * (1.0 - smoothstep(0.0, 0.06, abs(roll - 0.5))) * hash(vec3(floor(uv * resolution / 2.0), t));
  return vec4(c, 1.0);
}`)
define('grain', ['strength'], { strength: num(0.18, 0, 1), size: num(1.5, 0.5, 20), seed: whole(1, 0, 9999) }, `
vec4 effect(vec2 uv) {
  vec3 c = texture(picture, uv).rgb;
  float n = hash(vec3(floor(uv * size / max(dot_, size.x / resolution.x)), floor(time * 30.0) + seed * 57.0)) - 0.5;
  return vec4(c + n * strength * (1.0 - 0.5 * luma(c)), 1.0);
}`, { rename: { size: 'dot_' } })
define('vignette', ['strength'], { strength: num(0.6, 0, 1), size: num(0.75, 0, 2), colour: colour('black') }, `
vec4 effect(vec2 uv) {
  float d = length((uv - 0.5) * 2.0) / 1.41421;
  return vec4(mix(texture(picture, uv).rgb, colour, strength * smoothstep(wide * 0.5, wide * 0.5 + 0.55, d)), 1.0);
}`, { rename: { size: 'wide' } })
define('edges', ['strength'], { strength: num(2, 0, 10), size: num(1.5, 0.5, 20), fill: num(0, 0, 1) }, `
vec4 effect(vec2 uv) {
  vec2 o = max(thick, size.x / resolution.x) / size;
  vec3 a = texture(picture, uv + o * vec2(-1, -1)).rgb, b = texture(picture, uv + o * vec2(0, -1)).rgb, c = texture(picture, uv + o * vec2(1, -1)).rgb;
  vec3 d = texture(picture, uv + o * vec2(-1, 0)).rgb, f = texture(picture, uv + o * vec2(1, 0)).rgb;
  vec3 g = texture(picture, uv + o * vec2(-1, 1)).rgb, h = texture(picture, uv + o * vec2(0, 1)).rgb, i = texture(picture, uv + o * vec2(1, 1)).rgb;
  vec3 gx = c + 2.0 * f + i - a - 2.0 * d - g, gy = g + 2.0 * h + i - a - 2.0 * b - c;
  float e = clamp(sqrt(dot(gx, gx) + dot(gy, gy)) * 0.25 * strength, 0.0, 1.0);
  // The line takes the brightest colour beside it, at full strength.
  vec3 near = max(max(max(a, c), max(g, i)), max(max(b, h), max(d, f)));
  near /= max(max(near.r, max(near.g, near.b)), 0.001);
  return vec4(mix(texture(picture, uv).rgb * fill, near, e), 1.0);
}`, { rename: { size: 'thick' } })
define('dots', ['size'], { size: num(9, 2, 100), angle: angle(25), paper: colour('black') }, `
vec4 effect(vec2 uv) {
  vec2 p = turn(uv * size - size * 0.5, angle);
  vec2 mid = (floor(p / big) + 0.5) * big;
  vec3 s = texture(picture, (turn(mid, -angle) + size * 0.5) / size).rgb;
  float most = max(s.r, max(s.g, s.b));
  float r = sqrt(most) * big * 0.62, aa = size.x / resolution.x;
  return vec4(mix(paper, s / max(most, 0.001), (1.0 - smoothstep(r - aa, r + aa, length(p - mid))) * step(0.004, most)), 1.0);
}`, { rename: { size: 'big' } })
// Letters: each square of the picture becomes the one of ten marks that has about its brightness.
define('letters', ['size'], { size: num(10, 4, 100), colour: colour('white'), own: flag(true) }, `
const int MARKS[10] = int[10](0, 4194304, 131200, 14336, 459200, 145536, 332096, 18157905, 11512810, 33412991);
vec4 effect(vec2 uv) {
  vec2 p = uv * size;
  vec2 cell = floor(p / big);
  vec3 s = texture(picture, (cell + 0.5) * big / size).rgb;
  float l = max(s.r, max(s.g, s.b));
  int mark = MARKS[int(clamp(l * 10.0, 0.0, 9.0))];
  ivec2 at = ivec2(floor(fract(p / big) * 6.0)) - 1;
  float on = at.x >= 0 && at.x < 5 && at.y >= 0 && at.y < 5 ? float((mark >> (at.x + at.y * 5)) & 1) : 0.0;
  return vec4((own > 0.5 ? s / max(l, 0.001) : colour) * on, 1.0);
}`, { rename: { size: 'big' } })

// --- backdrops: pictures that need no drawing. They show wherever the scene has left the canvas clear.
define('plasma', ['palette'], { palette: pal('sunset'), speed: num(0.3, -5, 5), scale: num(1, 0.1, 10) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = (uv * size - size * 0.5) / min(size.x, size.y) * scale * 2.0;
  float t = time * speed * 2.0;
  float v = sin(q.x * 3.1 + t) + sin(q.y * 4.3 - t * 1.3) + sin((q.x + q.y) * 2.3 + t * 0.7);
  v += sin(length(q - vec2(sin(t * 0.37), cos(t * 0.53))) * 5.0 - t);
  return palette(v * 0.125 + 0.5 + t * 0.03);
}`, { backdrop: true })
define('starfield', ['speed'], { speed: num(0.5, -5, 5), stars: num(1, 0, 4), colour: colour('white'), x: place(), y: place() }, `
vec3 backdrop(vec2 uv) {
  ${PLACE}
  p /= min(size.x, size.y);
  float sum = 0.0;
  for (int i = 0; i < 10; i++) {
    // Ten sheets of stars, each coming nearer and starting again far away.
    float z = fract(float(i) / 10.0 + time * speed * 0.12);
    float s = mix(26.0, 0.7, z);
    vec2 g = p * s + float(i) * 23.7, cell = floor(g);
    if (hash(vec3(cell, float(i) + seed)) > 0.22 * stars) continue;
    vec2 off = vec2(hash(vec3(cell, 71.0)), hash(vec3(cell, 113.0))) - 0.5;
    float d = length(fract(g) - 0.5 - off * 0.7) / s;
    float r = 0.0012 + 0.004 * z * z;
    sum += (1.0 - smoothstep(r * 0.3, r, d)) * smoothstep(0.0, 0.25, z) * (1.0 - smoothstep(0.9, 1.0, z));
  }
  return colour * sum;
}`, { backdrop: true })
define('metaballs', ['palette'], { palette: pal('neon'), speed: num(0.5, -5, 5), count: whole(7, 1, 12), size: num(1, 0.2, 4) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = (uv * size - size * 0.5) / min(size.x, size.y);
  vec2 half_ = size / min(size.x, size.y) * 0.5;
  float t = time * speed, field = 0.0;
  for (int i = 0; i < 12; i++) {
    if (float(i) >= count) break;
    float k = float(i);
    vec2 at = half_ * 0.85 * vec2(sin(t * (0.5 + 0.13 * k) + k * 2.4), cos(t * (0.37 + 0.11 * k) + k * 4.1));
    float r = big * (0.07 + 0.035 * fract(k * 0.618));
    field += r * r / (dot(q - at, q - at) + 1e-4);
  }
  // The colour runs through the palette once from a blob's edge to its heart, and never round to the start again.
  vec3 c = palette(0.12 + 0.62 * smoothstep(0.4, 3.5, field));
  float inside = smoothstep(0.97, 1.03, field);
  return c * mix(field * field * 0.35, 1.0, inside);
}`, { backdrop: true, rename: { size: 'big' } })
define('flow', ['palette'], { palette: pal('ocean'), speed: num(0.2, -5, 5), scale: num(1, 0.1, 10) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = (uv * size - size * 0.5) / min(size.x, size.y) * scale * 2.2;
  float t = time * speed;
  // Noise looked up at a place that noise has moved: it folds like ink in water.
  vec2 w = vec2(fbm(q + vec2(t, -t * 0.7)), fbm(q + vec2(5.2 - t * 0.6, 1.3 + t)));
  float v = fbm(q + 2.5 * w + vec2(0.0, t * 0.3));
  return palette(v * 1.6 + length(w) * 0.5 + t * 0.1) * (0.35 + 1.1 * v);
}`, { backdrop: true })

// --------------------------------------------------------------------------------------------
// MORE OF THEM. The same words mean the same thing in every effect: `strength` how much, `size` how big (in
// the scene's points), `speed`, `angle`, `colour`, and x and y for a place. An effect that looks at many
// places for every pixel says so with `cost` ("some": a dozen or two; "heavy": more).
const SOBEL = `
  vec2 o = max(thick, size.x / resolution.x) / size;
  float a = luma(texture(picture, uv + o * vec2(-1, -1)).rgb), b = luma(texture(picture, uv + o * vec2(0, -1)).rgb), cc = luma(texture(picture, uv + o * vec2(1, -1)).rgb);
  float d = luma(texture(picture, uv + o * vec2(-1, 0)).rgb), f = luma(texture(picture, uv + o * vec2(1, 0)).rgb);
  float g = luma(texture(picture, uv + o * vec2(-1, 1)).rgb), h = luma(texture(picture, uv + o * vec2(0, 1)).rgb), i = luma(texture(picture, uv + o * vec2(1, 1)).rgb);
  float gx = cc + 2.0 * f + i - a - 2.0 * d - g, gy = g + 2.0 * h + i - a - 2.0 * b - cc;
  float edge = clamp(length(vec2(gx, gy)) * 0.5 * strength, 0.0, 1.0);`

// --- shapes of the picture
define('droste', ['zoom'], { zoom: num(3, 1.2, 10), twist: whole(1, 0, 4), speed: num(0.3, -5, 5), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  ${PLACE}
  float m = length(size) * 0.5, r = max(length(p), 0.001) / m, a = atan(p.y, p.x);
  // The picture inside itself, smaller each time, for ever: with a twist it winds in as a spiral.
  float k = pow(zoom, fract(log(r) / log(zoom) + a / TAU * twist - time * speed)) / zoom;
  return look((c + k * m * vec2(cos(a), sin(a))) / size);
}`)
define('rotozoom', ['speed'], { speed: num(0.5, -5, 5), zoom: num(1.5, 0.2, 8) }, `
vec4 effect(vec2 uv) {
  vec2 p = turn(uv * size - size * 0.5, time * speed) * (zoom + 0.6 * zoom * sin(time * speed * 0.7));
  return texture(picture, fract(p / size + 0.5));
}`)
define('hexagons', ['size'], { size: num(14, 3, 100) }, `
vec4 effect(vec2 uv) {
  const vec2 s = vec2(1.0, 1.7320508);
  vec2 p = uv * size / big, a = mod(p, s) - s * 0.5, b = mod(p - s * 0.5, s) - s * 0.5;
  return texture(picture, (p - (dot(a, a) < dot(b, b) ? a : b)) * big / size);
}`, { rename: { size: 'big' } })
define('glassTiles', ['size'], { size: num(40, 6, 300), strength: num(0.4, 0, 1) }, `
vec4 effect(vec2 uv) { vec2 p = uv * size; return look((p + (fract(p / big) - 0.5) * big * strength) / size); }`, { rename: { size: 'big' } })
define('frosted', ['size'], { size: num(6, 0, 60) }, `
vec4 effect(vec2 uv) {
  vec2 o = vec2(hash(uv * resolution), hash(uv * resolution + vec2(71.0, 13.0))) - 0.5;
  return look((uv * size + o * 2.0 * big) / size);
}`, { rename: { size: 'big' } })
define('heatHaze', ['size'], { size: num(5, 0, 60), scale: num(40, 5, 400), speed: num(1, -5, 5) }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size;
  p.x += big * 2.0 * (noise(vec2(p.x / scale, p.y / scale + time * speed * 3.0)) - 0.5);
  p.y += big * (noise(vec2(p.x / scale + 9.0, p.y / scale + time * speed * 3.0)) - 0.5);
  return look(p / size);
}`, { rename: { size: 'big' } })
define('caustics', ['strength'], { strength: num(0.5, 0, 2), scale: num(120, 20, 600), speed: num(0.5, -5, 5), colour: colour('#bfe8ff') }, `
vec4 effect(vec2 uv) {
  vec2 q = uv * size / scale, w = q;
  float t = time * speed;
  for (int i = 0; i < 3; i++) w += 0.6 * vec2(sin(w.y * 1.7 + t * (1.0 + 0.3 * float(i))), cos(w.x * 1.9 - t * 1.1));
  // Light gathered into a net of bright lines, as the sun is on the floor of a pool.
  float v = pow(0.5 + 0.5 * sin(w.x * 2.0) * sin(w.y * 2.0), 6.0);
  return vec4(look(uv + (w - q) * 0.004 * strength).rgb + colour * v * strength, 1.0);
}`)
define('shake', ['strength'], { strength: num(10, 0, 200), speed: num(25, 1, 100) }, `
vec4 effect(vec2 uv) {
  vec2 o = (vec2(noise(vec2(time * speed, 1.0)), noise(vec2(7.0, time * speed))) - 0.5) * 2.0 * strength;
  return look((uv * size + o) / size);
}`)
define('punch', ['strength'], { strength: num(0.15, -0.9, 4), x: place(), y: place() }, `
vec4 effect(vec2 uv) { ${PLACE} return look((c + p / (1.0 + strength)) / size); }`)

// --- blur and light
define('motionBlur', ['size'], { size: num(24, 0, 300), angle: angle(0) }, `
vec4 effect(vec2 uv) {
  vec2 d = big * vec2(cos(angle), sin(angle)) / size;
  float j = hash(uv * resolution);
  vec3 sum = vec3(0.0);
  for (int i = 0; i < 14; i++) sum += look(uv + d * ((float(i) + j) / 14.0 - 0.5)).rgb;
  return vec4(sum / 14.0, 1.0);
}`, { rename: { size: 'big' }, cost: 'some' })
define('tiltShift', ['strength'], { strength: num(8, 0, 60), size: num(70, 5, 1000), y: place() }, `
vec4 effect(vec2 uv) {
  float r = strength * smoothstep(band, band * 2.5, abs(uv.y * size.y - y));
  if (r < 0.3) return texture(picture, uv);
  // Sixteen places on a spiral out from this one: a small round blur that grows away from the band in focus.
  vec3 sum = vec3(0.0);
  float j = hash(uv * resolution) * TAU;
  for (int i = 0; i < 16; i++) sum += texture(picture, uv + sqrt((float(i) + 0.5) / 16.0) * r * vec2(cos(float(i) * 2.39996 + j), sin(float(i) * 2.39996 + j)) / size).rgb;
  return vec4(sum / 16.0, 1.0);
}`, { rename: { size: 'band' }, cost: 'some' })
define('lightRays', ['strength'], { strength: num(0.7, 0, 3), size: num(0.6, 0, 1), threshold: num(0.6, 0, 1), x: place(), y: place() }, `
vec4 effect(vec2 uv) {
  vec2 d = (uv - vec2(x, y) / size) * reach / 22.0, q = uv - d * hash(uv * resolution);
  vec3 sum = vec3(0.0);
  float w = 1.0;
  for (int i = 0; i < 22; i++) {
    q -= d;
    vec3 s = texture(picture, q).rgb;
    sum += s * smoothstep(threshold - 0.1, threshold + 0.1, most(s)) * w;
    w *= 0.93;
  }
  return vec4(texture(picture, uv).rgb + sum * strength * 0.11, 1.0);
}`, { rename: { size: 'reach' }, cost: 'some' })
define('streaks', ['strength'], { strength: num(0.6, 0, 3), size: num(120, 0, 800), threshold: num(0.6, 0, 1), colour: colour('#88aaff') }, `
vec3 lit(vec2 q) { vec3 s = texture(picture, q).rgb; return s * smoothstep(threshold - 0.1, threshold + 0.1, most(s)); }
vec4 effect(vec2 uv) {
  vec3 sum = vec3(0.0);
  float j = hash(uv * resolution);
  for (int i = 0; i < 12; i++) {
    float f = (float(i) + j) / 12.0;
    sum += (lit(uv + vec2(f * big / size.x, 0.0)) + lit(uv - vec2(f * big / size.x, 0.0))) * (1.0 - f);
  }
  return vec4(texture(picture, uv).rgb + sum * colour * strength * 0.16, 1.0);
}`, { rename: { size: 'big' }, cost: 'some' })
define('softFocus', ['strength'], { strength: num(0.6, 0, 1), size: num(6, 0, 60) }, `
vec4 effect(vec2 uv) {
  vec3 c = texture(picture, uv).rgb, b = vec3(0.0);
  for (int i = 0; i < 8; i++) b += texture(picture, uv + big * vec2(cos(float(i) * 0.7854), sin(float(i) * 0.7854)) * (0.5 + 0.5 * float(i & 1)) / size).rgb;
  return vec4(1.0 - (1.0 - c) * (1.0 - b / 8.0 * strength), 1.0);
}`, { rename: { size: 'big' } })

// --- what was drawn stays: these read their own last frame
define('smear', ['length'], { length: num(3, 0, 30), size: num(40, 0, 400), scale: num(150, 20, 1000) }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size;
  // The paint is pushed a little each frame along a slow current, and thins as it goes.
  float a = noise(p / scale + time * 0.1) * TAU * 2.0;
  vec3 old = texture(previous, (p - vec2(cos(a), sin(a)) * big * dt) / size).rgb * pow(0.1, dt / max(len, 0.01));
  return vec4(max(texture(picture, uv).rgb, max(old - 0.0015, 0.0)), 1.0);
}`, { rename: { size: 'big', length: 'len' }, feedback: true })
define('stutter', ['speed'], { speed: num(8, 0.5, 60) }, `
vec4 effect(vec2 uv) {
  // A new picture only so many times a second: between them the last one is held.
  bool fresh = floor(time * speed + 0.001) != floor((time - dt) * speed + 0.001) || frame < 1.5;
  return fresh ? texture(picture, uv) : texture(previous, uv);
}`, { feedback: true })

// --- colours
define('gradientMap', ['palette'], { palette: pal('sunset') }, `
vec4 effect(vec2 uv) { return vec4(ramp(luma(texture(picture, uv).rgb)), 1.0); }`)
define('thermal', [], { palette: pal('thermal') }, `
vec4 effect(vec2 uv) { return vec4(ramp(luma(texture(picture, uv).rgb)), 1.0); }`)
define('nightVision', ['strength'], { strength: num(1.6, 0, 6) }, `
vec4 effect(vec2 uv) {
  float l = pow(luma(texture(picture, uv).rgb) * strength, 0.8);
  l += (hash(vec3(floor(uv * resolution / 2.0), floor(time * 30.0 + 0.001))) - 0.5) * 0.14;
  l *= 0.85 + 0.15 * cos(TAU * uv.y * size.y / 3.0);
  return vec4(vec3(0.1, 1.0, 0.25) * l * (1.0 - smoothstep(0.35, 0.75, length(uv - 0.5))), 1.0);
}`)
define('sepia', ['strength'], { strength: num(1, 0, 1) }, `
vec4 effect(vec2 uv) {
  vec3 c = texture(picture, uv).rgb;
  return vec4(mix(c, vec3(dot(c, vec3(0.393, 0.769, 0.189)), dot(c, vec3(0.349, 0.686, 0.168)), dot(c, vec3(0.272, 0.534, 0.131))), strength), 1.0);
}`)
define('threshold', ['level'], { level: num(0.5, 0, 1), dark: colour('black'), light: colour('white') }, `
vec4 effect(vec2 uv) { return vec4(mix(dark, light, smoothstep(level - 0.01, level + 0.01, luma(texture(picture, uv).rgb))), 1.0); }`)
define('solarize', ['level'], { level: num(0.5, 0, 1) }, `
vec4 effect(vec2 uv) { vec3 c = texture(picture, uv).rgb; return vec4(mix(c, 1.0 - c, step(vec3(level), c)), 1.0); }`)
define('colourBleed', ['size'], { size: num(10, 0, 100) }, `
vec4 effect(vec2 uv) {
  vec3 c = texture(picture, uv).rgb, s = vec3(0.0);
  for (int i = 0; i < 6; i++) s += texture(picture, uv - vec2(float(i) * big / 6.0 / size.x, 0.0)).rgb;
  s /= 6.0;
  return vec4(luma(c) + (s - luma(s)) * 1.2, 1.0);
}`, { rename: { size: 'big' } })
define('rainbowEdges', ['strength'], { strength: num(2, 0, 10), size: num(1.5, 0.5, 20), speed: num(0.1, -5, 5) }, `
vec4 effect(vec2 uv) {${SOBEL}
  vec3 tone = 0.5 + 0.5 * cos(TAU * (atan(gy, gx) / TAU + time * speed + vec3(0.0, 0.33, 0.67)));
  return vec4(mix(texture(picture, uv).rgb, tone, edge), 1.0);
}`, { rename: { size: 'thick' } })

// --- old computers and screens
define('dither', ['palette'], { palette: pal('gameboy'), size: num(2, 1, 40), strength: num(0.35, 0, 1) }, `
const int BAYER[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
vec4 effect(vec2 uv) {
  float s = max(big, size.x / resolution.x);
  vec2 cell = floor(uv * size / s);
  vec3 c = texture(picture, (cell + 0.5) * s / size).rgb;
  // A pattern of sixteen thresholds nudges each pixel up or down, so a few colours pass for many.
  c += ((float(BAYER[int(mod(cell.x, 4.0)) + int(mod(cell.y, 4.0)) * 4]) + 0.5) / 16.0 - 0.5) * strength;
  vec3 best = pal[0];
  float closest = 9.0;
  for (int i = 0; i < 6; i++) {
    if (float(i) >= palCount) break;
    float d = distance(c, pal[i]);
    if (d < closest) { closest = d; best = pal[i]; }
  }
  return vec4(best, 1.0);
}`, { rename: { size: 'big' } })
define('interlace', ['strength'], { strength: num(0.6, 0, 1), size: num(2, 1, 20) }, `
vec4 effect(vec2 uv) {
  float row = floor(uv.y * size.y / max(gap, size.y / resolution.y)) + floor(time * 30.0 + 0.001);
  return vec4(texture(picture, uv).rgb * (1.0 - strength * mod(row, 2.0)), 1.0);
}`, { rename: { size: 'gap' } })
define('led', ['size'], { size: num(8, 3, 80) }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size, mid = (floor(p / big) + 0.5) * big;
  float aa = size.x / resolution.x;
  vec3 c = texture(picture, mid / size).rgb;
  return vec4(c * 1.25 * (1.0 - smoothstep(big * 0.36 - aa, big * 0.36 + aa, length(p - mid))) + 0.025, 1.0);
}`, { rename: { size: 'big' } })

// --- drawn, printed and painted
define('emboss', ['strength'], { strength: num(2, 0, 10), angle: angle(135), size: num(1.5, 0.5, 20) }, `
vec4 effect(vec2 uv) {
  vec2 o = max(thick, size.x / resolution.x) * vec2(cos(angle), sin(angle)) / size;
  return vec4(vec3(0.5 + (luma(texture(picture, uv + o).rgb) - luma(texture(picture, uv - o).rgb)) * strength), 1.0);
}`, { rename: { size: 'thick' } })
define('sharpen', ['strength'], { strength: num(1, 0, 5), size: num(1, 0.5, 10) }, `
vec4 effect(vec2 uv) {
  vec2 o = max(thick, size.x / resolution.x) / size;
  vec3 c = texture(picture, uv).rgb;
  vec3 round_ = texture(picture, uv + vec2(o.x, 0.0)).rgb + texture(picture, uv - vec2(o.x, 0.0)).rgb + texture(picture, uv + vec2(0.0, o.y)).rgb + texture(picture, uv - vec2(0.0, o.y)).rgb;
  return vec4(c + (c - round_ * 0.25) * strength, 1.0);
}`, { rename: { size: 'thick' } })
define('sketch', ['strength'], { strength: num(3, 0, 10), size: num(1.2, 0.5, 20), paper: colour('#f4efe2'), colour: colour('#2a2a33') }, `
vec4 effect(vec2 uv) {${SOBEL}
  vec2 p = uv * size;
  // Shading is pencil strokes on a slant, closer together where the picture is darker.
  float shade = 1.0 - luma(texture(picture, uv).rgb);
  float strokes = step(fract((p.x + p.y) / 5.0 + 0.3 * noise(p / 7.0)), shade * 0.6) * step(0.35, shade);
  return vec4(mix(paper, colour, clamp(edge + strokes * 0.45, 0.0, 1.0)), 1.0);
}`, { rename: { size: 'thick' } })
define('cartoon', ['levels'], { levels: whole(4, 2, 12), strength: num(2.5, 0, 10), size: num(1.5, 0.5, 20) }, `
vec4 effect(vec2 uv) {${SOBEL}
  vec3 c = texture(picture, uv).rgb;
  float l = max(most(c), 0.001), n = max(2.0, floor(levels + 0.5));
  return vec4(c / l * (floor(l * n + 0.5) / n) * (1.0 - smoothstep(0.25, 0.6, edge)), 1.0);
}`, { rename: { size: 'thick' } })
define('stainedGlass', ['size'], { size: num(40, 8, 400), colour: colour('#101010') }, `
vec4 effect(vec2 uv) {
  vec3 v = cells(uv * size / big);
  return vec4(mix(colour, texture(picture, v.xy * big / size).rgb * 1.1, smoothstep(0.03, 0.09, v.z)), 1.0);
}`, { rename: { size: 'big' } })
define('crosshatch', ['size'], { size: num(6, 2, 60), colour: colour('#1a1a22'), paper: colour('#f6f2e8') }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size;
  float l = luma(texture(picture, uv).rgb), a = fract((p.x + p.y) / big), b = fract((p.x - p.y) / big), ink = 0.0;
  // A darker place has more sets of lines across it.
  if (l < 0.8) ink = max(ink, step(a, 0.22));
  if (l < 0.55) ink = max(ink, step(b, 0.22));
  if (l < 0.3) ink = max(ink, step(fract(a + 0.5), 0.22));
  if (l < 0.12) ink = max(ink, step(fract(b + 0.5), 0.22));
  return vec4(mix(paper, colour, ink), 1.0);
}`, { rename: { size: 'big' } })
define('oil', ['size'], { size: num(4, 1, 30) }, `
vec4 effect(vec2 uv) {
  // Four patches round each place, and the colour of the calmest one: edges stay and everything else is smoothed like paint.
  vec2 o = max(big, size.x / resolution.x) / 2.0 / size;
  vec3 best = vec3(0.0);
  float least = 1e9;
  for (int k = 0; k < 4; k++) {
    vec2 corner = vec2(k % 2 == 0 ? -1.0 : 1.0, k < 2 ? -1.0 : 1.0);
    vec3 mean = vec3(0.0);
    float sq = 0.0;
    for (int j = 0; j < 3; j++) for (int i = 0; i < 3; i++) {
      vec3 c = texture(picture, uv + corner * vec2(i, j) * o).rgb;
      mean += c;
      sq += dot(c, c);
    }
    mean /= 9.0;
    float spread = sq / 9.0 - dot(mean, mean);
    if (spread < least) { least = spread; best = mean; }
  }
  return vec4(best, 1.0);
}`, { rename: { size: 'big' }, cost: 'heavy' })

// --- things in front of the picture
define('dust', ['strength'], { strength: num(0.5, 0, 1), seed: whole(1, 0, 9999) }, `
vec4 effect(vec2 uv) {
  vec3 c = texture(picture, uv).rgb;
  float t = floor(time * 12.0 + 0.001) + seed * 17.0;
  vec2 cell = floor(uv * vec2(8.0, 5.0));
  if (hash(vec3(cell, t)) > 1.0 - 0.1 * strength) {
    vec2 at = (cell + 0.2 + 0.6 * vec2(hash(vec3(cell, t + 3.0)), hash(vec3(cell, t + 5.0)))) / vec2(8.0, 5.0);
    c *= smoothstep(0.0, 1.0, length((uv - at) * size) / (1.0 + 2.5 * hash(vec3(cell, t + 9.0))) - 0.2);
  }
  // A scratch or two down the film, never in the same place twice.
  for (int k = 0; k < 2; k++) {
    float at = hash(vec2(t, float(k)));
    if (hash(vec2(t, float(k) + 5.0)) < 0.35 * strength) c += 0.3 * (1.0 - smoothstep(0.0, 1.2, abs(uv.x - at) * size.x)) * step(hash(vec2(floor(uv.y * 14.0), t)), 0.8);
  }
  return vec4(c, 1.0);
}`)
define('lightLeaks', ['strength'], { strength: num(0.6, 0, 2), speed: num(0.2, -5, 5), colour: colour('#ff7a2a') }, `
vec4 effect(vec2 uv) {
  float t = time * speed;
  float v = pow(noise(vec2(uv.y * 1.5 + t, t * 0.7)), 2.0) * (1.0 - smoothstep(0.0, 0.55, uv.x)) + pow(noise(vec2(uv.y * 1.2 - t * 0.8, 9.0 + t * 0.5)), 2.0) * smoothstep(0.55, 1.0, uv.x);
  return vec4(1.0 - (1.0 - texture(picture, uv).rgb) * (1.0 - clamp(colour * v * strength * 2.2, 0.0, 1.0)), 1.0);
}`)
define('rain', ['strength'], { strength: num(0.6, 0, 2), speed: num(1, 0, 5), angle: angle(12, -80, 80) }, `
vec4 effect(vec2 uv) {
  vec2 p = turn(uv * size, angle);
  float sum = 0.0;
  for (int k = 0; k < 3; k++) {
    float f = 1.0 + float(k) * 0.6, w = 9.0 / f, h = 150.0 / f, col = floor(p.x / w);
    if (hash(vec2(col, float(k))) > 0.35) continue;
    float y = fract((p.y - time * speed * 900.0 / f) / h + hash(vec2(col, float(k) + 3.0)));
    sum += smoothstep(0.75, 1.0, y) * (1.0 - smoothstep(0.1, 0.25, abs(fract(p.x / w) - 0.5))) / f;
  }
  return vec4(texture(picture, uv).rgb + vec3(0.7, 0.8, 1.0) * sum * strength * 0.5, 1.0);
}`)
define('snow', ['strength'], { strength: num(0.8, 0, 2), speed: num(1, 0, 5), size: num(3, 0.5, 20) }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size;
  float sum = 0.0;
  for (int k = 0; k < 4; k++) {
    float f = 1.0 + float(k) * 0.5, s = 70.0 / f;
    vec2 q = (p + vec2(14.0 * sin(time * 0.7 + float(k) * 2.0), -time * speed * (60.0 - 9.0 * float(k)))) / s, cell = floor(q);
    vec2 at = 0.2 + 0.6 * vec2(hash(vec3(cell, float(k))), hash(vec3(cell, float(k) + 9.0)));
    float r = big * (0.5 + 0.5 * hash(vec3(cell, 4.0))) / f / s;
    sum += (1.0 - smoothstep(r * 0.4, r, distance(fract(q), at))) / (0.6 + 0.4 * f);
  }
  return vec4(texture(picture, uv).rgb + sum * strength, 1.0);
}`, { rename: { size: 'big' } })
define('bokeh', ['strength'], { strength: num(0.5, 0, 2), size: num(30, 4, 200), speed: num(0.3, -5, 5) }, `
vec4 effect(vec2 uv) {
  vec2 p = uv * size;
  vec3 sum = vec3(0.0);
  for (int k = 0; k < 2; k++) {
    float s = big * (3.0 + float(k));
    vec2 q = (p + vec2(float(k) * 37.0, time * speed * 40.0 * (1.0 + float(k)))) / s, cell = floor(q);
    if (hash(vec3(cell, float(k))) > 0.6) continue;
    vec2 at = 0.3 + 0.4 * vec2(hash(vec3(cell, 2.0)), hash(vec3(cell, 3.0)));
    float r = (0.5 + 0.5 * hash(vec3(cell, 4.0))) * big / s, d = distance(fract(q), at);
    // A disc of light with a brighter rim, as a lamp out of focus is.
    sum += (0.5 + 0.5 * cos(TAU * (hash(vec3(cell, 5.0)) + vec3(0.0, 0.33, 0.67)))) * (1.0 - smoothstep(r * 0.9, r, d)) * (0.5 + 0.5 * smoothstep(r * 0.6, r * 0.9, d));
  }
  return vec4(texture(picture, uv).rgb + sum * strength * 0.5, 1.0);
}`, { rename: { size: 'big' } })
define('fog', ['strength'], { strength: num(0.6, 0, 1), speed: num(0.3, -5, 5), scale: num(220, 20, 2000), colour: colour('#dfe6ee') }, `
vec4 effect(vec2 uv) {
  float v = fbm(uv * size / scale + vec2(time * speed, 0.0));
  return vec4(mix(texture(picture, uv).rgb, colour, strength * smoothstep(0.2, 0.8, v) * (0.4 + 0.6 * uv.y)), 1.0);
}`)
define('lightning', ['strength'], { strength: num(1, 0, 3), speed: num(1, 0, 10), seed: whole(1, 0, 9999) }, `
vec4 effect(vec2 uv) {
  float t = time * speed * 0.7 + seed * 13.0, f = fract(t);
  float flash = step(hash(vec2(floor(t), 1.0)), 0.5) * exp(-f * 14.0) * (0.6 + 0.4 * sin(f * 90.0));
  return vec4(texture(picture, uv).rgb * (1.0 + flash * strength) + vec3(0.75, 0.82, 1.0) * flash * strength * 0.6, 1.0);
}`)

// --- more backdrops
define('warp', ['palette'], { palette: pal('neon'), speed: num(1, -10, 10), x: place(), y: place() }, `
vec3 backdrop(vec2 uv) {
  ${PLACE}
  float r = length(p) / (min(size.x, size.y) * 0.5), a = atan(p.y, p.x) / TAU;
  float z = 1.0 / max(r, 0.02) + time * speed * 2.0;
  return palette(z * 0.05 + a) * (0.3 + 0.7 * mod(floor(a * 16.0) + floor(z * 2.0), 2.0)) * smoothstep(0.0, 0.6, r);
}`, { backdrop: true })
define('voronoi', ['palette'], { palette: pal('candy'), speed: num(0.3, -5, 5), scale: num(1, 0.1, 10) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = (uv * size - size * 0.5) / min(size.x, size.y) * 5.0 * scale;
  float t = time * speed;
  q += 0.35 * vec2(sin(t + q.y * 0.9), cos(t * 0.8 + q.x * 0.9));
  vec3 v = cells(q);
  return palette(hash(v.xy * 91.0) + t * 0.05) * smoothstep(0.0, 0.1, v.z) * (0.7 + 0.3 * smoothstep(0.1, 0.5, v.z));
}`, { backdrop: true })
define('moire', ['colour'], { colour: colour('white'), speed: num(0.3, -5, 5), scale: num(1, 0.1, 10) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = (uv * size - size * 0.5) / min(size.x, size.y);
  float t = time * speed;
  float v = sin(length(q - 0.3 * vec2(sin(t), cos(t * 1.3))) * 90.0 * scale) * sin(length(q + 0.3 * vec2(cos(t * 0.7), sin(t * 1.1))) * 90.0 * scale);
  return colour * smoothstep(-0.15, 0.15, v);
}`, { backdrop: true })
define('interference', ['palette'], { palette: pal('ocean'), speed: num(0.5, -5, 5), scale: num(1, 0.1, 10) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = (uv * size - size * 0.5) / min(size.x, size.y);
  float t = time * speed, v = 0.0;
  for (int i = 0; i < 4; i++) {
    float k = float(i);
    v += sin(length(q - 0.45 * vec2(sin(t * (0.5 + 0.2 * k) + k * 2.0), cos(t * (0.4 + 0.15 * k) + k))) * 34.0 * scale - t * 4.0);
  }
  return palette(v * 0.125 + 0.5);
}`, { backdrop: true })
define('aurora', ['palette'], { palette: pal('aurora'), speed: num(0.3, -5, 5) }, `
vec3 backdrop(vec2 uv) {
  float t = time * speed;
  vec3 sum = vec3(0.004, 0.012, 0.04) * (1.0 + uv.y);
  for (int i = 0; i < 3; i++) {
    float k = float(i), y = 0.3 + 0.12 * k + 0.09 * sin(uv.x * 3.0 + t * (1.0 + 0.3 * k) + k * 2.0) + 0.04 * sin(uv.x * 9.0 - t * 1.7);
    float d = uv.y - y;
    // A curtain: sharp along its lower edge, fading upwards, with rays that shift.
    float band = (d < 0.0 ? exp(d * 9.0) : exp(-d * 60.0)) * (0.45 + 0.55 * noise(vec2(uv.x * 40.0 + k * 7.0, t * 2.0)));
    sum += palette(k / 3.0 + 0.1 * sin(t + uv.x * 2.0)) * band * 0.8;
  }
  return sum + step(0.9985, hash(floor(uv * resolution / 2.0))) * 0.6;
}`, { backdrop: true })
define('fire', ['palette'], { palette: pal('fire'), speed: num(1, -5, 5), scale: num(1, 0.1, 10) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = uv * size / min(size.x, size.y) * 3.0 * scale;
  float t = time * speed;
  float v = fbm(vec2(q.x, q.y + t * 2.2)) * 0.6 + fbm(vec2(q.x * 2.0 + 7.0, q.y * 2.0 + t * 3.5)) * 0.4;
  return ramp(clamp(v * 2.0 - (1.0 - uv.y) * 1.5 + 0.15, 0.0, 1.0));
}`, { backdrop: true })
define('clouds', ['colour'], { colour: colour('#3a8fdc'), speed: num(0.1, -5, 5), scale: num(1, 0.1, 10) }, `
vec3 backdrop(vec2 uv) {
  vec2 q = uv * size / min(size.x, size.y) * 2.5 * scale + vec2(time * speed, 0.0);
  float v = fbm(q) * 0.65 + fbm(q * 2.3 + 11.0) * 0.35;
  vec3 sky = mix(colour, colour * 0.45 + 0.5, uv.y);
  return mix(sky, vec3(1.0) - 0.25 * smoothstep(0.6, 0.9, v), smoothstep(0.42, 0.7, v));
}`, { backdrop: true })
define('matrixRain', ['colour'], { colour: colour('#3dff7a'), speed: num(1, 0, 10), size: num(14, 6, 80) }, `
vec3 backdrop(vec2 uv) {
  vec2 p = uv * size, cell = floor(p / big), sub = floor(fract(p / big) * 6.0);
  float rows = size.y / big + 24.0;
  float head = fract(time * speed * 0.12 * (0.5 + hash(vec2(cell.x, 3.0))) + hash(vec2(cell.x, 7.0))) * rows, behind = head - cell.y;
  if (behind < 0.0 || behind > 20.0 || sub.x < 1.0 || sub.y < 1.0) return vec3(0.0);
  // Each square is a mark made of dots that changes now and then.
  float on = step(0.5, hash(vec3(sub + cell * 7.0, floor(time * 5.0 * speed + 0.001 + hash(cell) * 10.0))));
  return mix(colour * (1.0 - behind / 20.0), vec3(0.85, 1.0, 0.9), step(behind, 1.0)) * on;
}`, { backdrop: true, rename: { size: 'big' } })
define('copperBars', ['palette'], { palette: pal('rainbow'), count: whole(5, 1, 8), speed: num(1, -5, 5), size: num(34, 4, 300) }, `
vec3 backdrop(vec2 uv) {
  vec3 c = vec3(0.0);
  for (int i = 0; i < 8; i++) {
    if (float(i) >= count) break;
    float d = abs(uv.y * size.y - size.y * (0.5 + 0.36 * sin(time * speed * 1.3 + float(i) * 0.55))) / big;
    // A round bar of metal: bright along its middle. A later bar is in front of an earlier one.
    if (d < 1.0) c = palette(float(i) / count) * (1.0 - d * d) + 0.5 * pow(1.0 - d, 6.0);
  }
  return c;
}`, { backdrop: true, rename: { size: 'big' } })
define('checkerFloor', ['colour'], { colour: colour('#ff2a6d'), dark: colour('#101a3a'), speed: num(1, -10, 10) }, `
vec3 backdrop(vec2 uv) {
  float h = 0.42, d = uv.y - h;
  if (d <= 0.0) return mix(vec3(0.01, 0.0, 0.05), colour * 0.55, pow(uv.y / h, 5.0));
  // Below the horizon: the further down the screen, the nearer the floor.
  float z = 1.0 / d;
  float squares = mod(floor((uv.x - 0.5) * z * 3.0 * size.x / size.y) + floor(z * 1.2 + time * speed * 3.0), 2.0);
  return mix(colour * 0.55, mix(dark, colour, squares), clamp(d * 5.0, 0.0, 1.0));
}`, { backdrop: true })
define('twister', ['palette'], { palette: pal('candy'), speed: num(1, -5, 5), size: num(0.22, 0.02, 0.5) }, `
vec3 backdrop(vec2 uv) {
  float t = time * speed, a = t + sin(uv.y * 3.0 + t * 1.3) * 2.2, x = uv.x - 0.5 - 0.08 * sin(uv.y * 2.0 + t);
  // A square bar seen from the side, twisted along its length: the faces that are towards you, each with its own colour.
  for (int i = 0; i < 4; i++) {
    float x0 = sin(a + float(i) * 1.5708) * wide, x1 = sin(a + float(i + 1) * 1.5708) * wide;
    if (x0 < x1 && x > x0 && x < x1) return palette(float(i) / 4.0) * (0.35 + 0.65 * (x1 - x0) / (wide * 1.4143));
  }
  return vec3(0.0);
}`, { backdrop: true, rename: { size: 'wide' } })

// --- the music, drawn. With nothing to listen to they are still and dark.
define('spectrumBars', ['palette'], { palette: pal('rainbow'), count: whole(32, 4, 64), size: num(0.7, 0.05, 1) }, `
vec3 backdrop(vec2 uv) {
  float n = floor(count + 0.5), i = floor(uv.x * n), v = texture(spectrum, vec2((i + 0.5) / n, 0.5)).r * tall;
  float bar = step(1.0 - uv.y, v) * step(0.12, fract(uv.x * n)) * step(fract(uv.x * n), 0.88);
  return palette(i / n * 0.85) * bar * (0.55 + 0.45 * (1.0 - uv.y) / max(v, 0.001));
}`, { backdrop: true, rename: { size: 'tall' } })
define('spectrumRing', ['palette'], { palette: pal('rainbow'), size: num(90, 10, 1000), x: place(), y: place() }, `
vec3 backdrop(vec2 uv) {
  ${PLACE}
  float s = abs(atan(p.y, p.x) / TAU * 2.0), bars = 48.0, i = floor(s * bars);
  float v = texture(spectrum, vec2((i + 0.5) / bars * 0.9, 0.5)).r, r = length(p);
  float bar = step(big, r) * step(r, big * (1.03 + 1.4 * v)) * step(0.15, fract(s * bars)) * step(fract(s * bars), 0.85);
  return palette(i / bars * 0.85) * bar;
}`, { backdrop: true, rename: { size: 'big' } })
define('waveformRing', ['colour'], { colour: colour('white'), size: num(110, 10, 1000), strength: num(3, 0.5, 40), x: place(), y: place() }, `
vec3 backdrop(vec2 uv) {
  ${PLACE}
  float s = abs(atan(p.y, p.x) / TAU * 2.0);
  float r = big * (1.0 + (texture(waveform, vec2(s, 0.5)).r - 0.5) * 1.2), aa = size.x / resolution.x;
  return colour * (1.0 - smoothstep(strength * 0.5, strength * 0.5 + aa * 1.5, abs(length(p) - r)));
}`, { backdrop: true, rename: { size: 'big' } })
define('beatFlash', ['strength'], { strength: num(0.5, 0, 2), colour: colour('white') }, `
vec4 effect(vec2 uv) { return vec4(texture(picture, uv).rgb + colour * pulse * strength, 1.0); }`)
define('bassShake', ['strength'], { strength: num(14, 0, 200), speed: num(25, 1, 100) }, `
vec4 effect(vec2 uv) {
  vec2 o = (vec2(noise(vec2(time * speed, 1.0)), noise(vec2(7.0, time * speed))) - 0.5) * 2.0 * strength * bass;
  return look((uv * size + o) / size);
}`)

/**
 * LOOKS: several effects at once, by name. Each entry is [effect, its settings].
 */
const LOOKS = {
  dream: [['glow', { strength: 1, threshold: 0.35, radius: 40 }], ['saturate', { strength: 1.3 }], ['vignette', { strength: 0.5 }]],
  arcade: [['glow', { strength: 0.7, threshold: 0.4, radius: 20 }], ['crt', { curve: 0.2, lines: 0.5 }]],
  vhs: [['saturate', { strength: 1.35 }], ['rgbSplit', { size: 3 }], ['glitch', { strength: 0.35 }], ['scanlines', { strength: 0.3, size: 4 }], ['grain', { strength: 0.2, size: 2 }], ['vignette', { strength: 0.45 }]],
  neon: [['edges', { strength: 3, fill: 0.15 }], ['glow', { strength: 1.4, threshold: 0.2, radius: 28 }]],
  comic: [['posterize', { levels: 4 }], ['dots', { size: 7 }]],
  underwater: [['wobble', { size: 10, scale: 160 }], ['tint', { colour: '#7fd4ff' }], ['glow', { strength: 0.5, threshold: 0.5 }], ['vignette', { strength: 0.6, colour: '#001830' }]],
  oldfilm: [['duotone', { dark: '#1a1208', light: '#f2e2c0' }], ['grain', { strength: 0.3, size: 2 }], ['vignette', { strength: 0.75 }]],
  disco: [['kaleidoscope', { segments: 10 }], ['hue', { shift: 0, speed: 60 }], ['glow', { strength: 0.8 }]],
  gameboy: [['dither', { palette: 'gameboy', size: 3 }]],
  c64: [['dither', { palette: 'c64', size: 3 }], ['scanlines', { strength: 0.2, size: 3 }]],
  noir: [['saturate', { strength: 0 }], ['contrast', { strength: 1.6 }], ['grain', { strength: 0.25, size: 2 }], ['vignette', { strength: 0.8 }]],
  comicbook: [['cartoon', { levels: 4 }], ['dots', { size: 5, paper: '#101018' }]],
  storm: [['rain', { strength: 0.7 }], ['lightning', {}], ['fog', { strength: 0.35, colour: '#8a94a8' }], ['vignette', { strength: 0.6 }]],
  winter: [['tint', { colour: '#cfe4ff' }], ['snow', {}], ['softFocus', { strength: 0.4 }], ['vignette', { strength: 0.4, colour: '#0a1830' }]],
  cinema: [['streaks', { strength: 0.5 }], ['tiltShift', { strength: 5 }], ['grain', { strength: 0.1 }], ['vignette', { strength: 0.5 }]],
  terminal: [['letters', { size: 9, own: false, colour: '#3dff7a' }], ['glow', { strength: 0.6, threshold: 0.2, radius: 14 }], ['scanlines', { strength: 0.25 }]],
}

// --------------------------------------------------------------------------------------------
// LISTENING: the bass, the middle, the highs, how loud, and a pulse on each beat, from anything with
// samples() (numbers from -1 to 1, the latest sound). All of it is smoothed on the scene's clock.
class Listener {
  constructor() {
    this.target = null
    this.bass = this.mids = this.highs = this.loudness = this.pulse = 0
    this.spectrum = new Uint8Array(64)
    this.waveform = new Uint8Array(256).fill(128)
    this.peak = 0.05
    this.average = 0
    this.since = 1
    this.last = null
    this.stamp = 0 // goes up when the textures need sending again
    this.used = false // nothing is asked of the sound until something here wants to know (a synth is not made to report for nothing)
    this.re = this.im = this.window = null
  }

  listen(target) {
    this.target = target || null
    this.last = null
  }

  /** The sound as it is now, or null: a list of numbers, however the target gives it. */
  heard() {
    const t = this.target
    if (!t) return null
    try {
      let s = typeof t === 'function' ? t() : typeof t.samples === 'function' ? t.samples() : null
      // Left and right as two lists: the left will do.
      if (s && s.length && typeof s[0] !== 'number' && s[0] && s[0].length !== undefined) s = s[0]
      return s && s.length ? s : null
    } catch (e) { return null }
  }

  update(dt) {
    if (!this.used) return
    const ease = (now, to, up, down) => now + (to - now) * (1 - Math.exp(-dt / (to > now ? up : down)))
    const s = this.heard()
    let bass = 0, mids = 0, highs = 0, loud = 0
    this.since += dt
    // The same list as last frame (a sound library posts about forty a second) says nothing new.
    const fresh = s && !(this.last && this.last.n === s.length && this.last.a === s[0] && this.last.b === s[s.length >> 1] && this.last.c === s[s.length - 1])
    if (s) {
      let n = 64
      while (n * 2 <= s.length && n < 1024) n *= 2
      if (!this.re || this.re.length !== n) {
        this.re = new Float32Array(n)
        this.im = new Float32Array(n)
        this.window = Float32Array.from({ length: n }, (_, i) => 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (n - 1)))
      }
      const { re, im } = this, from = s.length - n
      let energy = 0
      for (let i = 0; i < s.length; i++) energy += s[i] * s[i]
      energy /= s.length
      for (let i = 0; i < n; i++) { re[i] = (s[from + i] || 0) * this.window[i]; im[i] = 0 }
      transform(re, im)
      const rate = (this.target && this.target.sampleRate) || 48000, hz = rate / n
      const band = (low, high) => {
        const a = Math.max(1, Math.round(low / hz)), b = Math.max(a + 1, Math.min(n / 2, Math.round(high / hz)))
        let sum = 0
        for (let k = a; k < b; k++) sum += re[k] * re[k] + im[k] * im[k]
        return Math.sqrt(sum) / (n / 4)
      }
      // High notes are quieter in most music than low ones: they are turned up to be seen.
      bass = band(20, 220); mids = band(220, 2200) * 1.6; highs = band(2200, 12000) * 3
      loud = Math.sqrt(energy) * 1.6
      // Everything is measured against the loudest it has been lately, so quiet music moves as much as loud.
      this.peak = Math.max(this.peak * Math.pow(0.5, dt / 4), bass, mids, highs, loud, 0.02)
      bass /= this.peak; mids /= this.peak; highs /= this.peak; loud /= this.peak
      if (fresh) {
        // A beat: suddenly more sound than there has been over the last half second.
        if (energy > this.average * 1.8 + 1e-5 && this.since > 0.12) { this.pulse = 1; this.since = 0 }
        this.average += (energy - this.average) * 0.25
        for (let i = 0; i < 64; i++) {
          // Sixty-four steps from 30 Hz to 12 kHz, each a little wider than the one before.
          const lo = 30 * Math.pow(400, i / 64), hi = 30 * Math.pow(400, (i + 1) / 64)
          this.spectrum[i] = clamp(band(lo, Math.max(hi, lo + hz)) * (1 + i / 16) / this.peak, 0, 1) * 255
        }
        for (let i = 0; i < 256; i++) this.waveform[i] = clamp(0.5 + 0.5 * (s[from + Math.floor(i * n / 256)] || 0), 0, 1) * 255
        this.stamp++
        this.last = { n: s.length, a: s[0], b: s[s.length >> 1], c: s[s.length - 1] }
      }
    } else if (this.last) {
      this.last = null
      this.spectrum.fill(0); this.waveform.fill(128); this.stamp++
    }
    this.bass = ease(this.bass, clamp(bass, 0, 1), 0.025, 0.22)
    this.mids = ease(this.mids, clamp(mids, 0, 1), 0.025, 0.22)
    this.highs = ease(this.highs, clamp(highs, 0, 1), 0.025, 0.18)
    this.loudness = ease(this.loudness, clamp(loud, 0, 1), 0.03, 0.3)
    if (this.since > 0) this.pulse *= Math.pow(0.5, dt / 0.11)
    if (this.pulse < 0.001) this.pulse = 0
  }
}
/** A fast Fourier transform in place: how much of each pitch is in a wave. The length is a power of two. */
function transform(re, im) {
  const n = re.length
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1
    for (; j & bit; bit >>= 1) j ^= bit
    j ^= bit
    if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const step = -2 * Math.PI / len, wr = Math.cos(step), wi = Math.sin(step)
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0
      for (let k = 0; k < len / 2; k++) {
        const a = i + k, b = a + len / 2
        const xr = re[b] * cr - im[b] * ci, xi = re[b] * ci + im[b] * cr
        re[b] = re[a] - xr; im[b] = im[a] - xi
        re[a] += xr; im[a] += xi
        const t = cr * wr - ci * wi
        ci = cr * wi + ci * wr
        cr = t
      }
    }
  }
}

// --------------------------------------------------------------------------------------------
// One effect that is on a scene. What the scene holds is a Proxy of this, so `effect.segments = 12`
// sets a setting and a name that is not a setting is said plainly.
const OWN = new Set(['on', 'off', 'remove', 'set', 'get', 'describe', 'name', 'active', 'settings', 'params'])
class Effect {
  constructor(pipe, def, given) {
    this.pipe = pipe
    this.def = def
    this.name = def.name
    this.active = true
    this.values = {}
    this.history = null // two pictures it writes in turn, when it uses its own last frame
    this.flipped = 0
    for (const name in def.settings) this.values[name] = def.settings[name].default
    for (const name in given) this.set(name, given[name])
  }

  setting(name) {
    const key = SPELLING[camel(name)] || camel(name)
    const s = this.def.settings[key]
    if (!s) throw new Error(`${this.name} has no setting called "${name}". Its settings are ${Object.keys(this.def.settings).join(', ')}`)
    return [key, s]
  }

  set(name, value) {
    const [key, s] = this.setting(name)
    if (typeof value !== 'function') {
      if (s.kind === 'choice') {
        if (typeof value === 'number') value = s.choices[clamp(Math.round(value), 0, s.choices.length - 1)]
        if (!s.choices.includes(value)) throw new Error(`${this.name}'s ${key} is one of ${s.choices.map((c) => `"${c}"`).join(', ')}, not ${JSON.stringify(value)}`)
      } else if (s.kind === 'colour') rgb(value)
      else if (s.kind === 'palette') paletteOf(value)
      else if (s.kind === 'bool') value = !!value
      else if (value == null && s.place) value = null
      else if (typeof value !== 'number' || Number.isNaN(value)) throw new Error(`${this.name}'s ${key} is a number (or a function that gives one), not ${JSON.stringify(value)}`)
    }
    this.values[key] = value
  }

  /** A setting as it is now: a function is asked. */
  get(name) {
    const [key, s] = this.setting(name)
    let v = this.values[key]
    if (typeof v === 'function') {
      v = v()
      if (s.kind === 'float' || s.kind === 'int') { v = Number(v); if (Number.isNaN(v)) v = s.default }
    }
    if (v == null && s.place) {
      // The middle of the picture, which before the first frame is asked of the canvas itself.
      const p = this.pipe, c = p.canvas
      v = (key === 'y' ? (p.w ? p.H : c.clientHeight || c.height) : (p.w ? p.W : c.clientWidth || c.width)) / 2
    }
    return v
  }

  /** What a dial needs to know of a setting: its range, its kind, where it starts. */
  describe(name) {
    const [key, s] = this.setting(name)
    const d = { name: key, kind: s.kind === 'colour' || s.kind === 'palette' ? 'text' : s.kind, default: s.default }
    if (s.min !== undefined) { d.min = s.min; d.max = s.max }
    if (s.place) { const c = this.pipe.canvas; d.max = key === 'y' ? c.clientHeight || c.height : c.clientWidth || c.width; d.default = d.max / 2 }
    if (s.step) d.step = s.step
    if (s.unit) d.unit = s.unit === 'degrees' ? '°' : s.unit
    if (s.choices) d.choices = s.choices
    return d
  }

  get settings() { return Object.keys(this.def.settings) }
  get params() { return Object.keys(this.def.settings).map((n) => this.describe(n)) }
  on() { this.active = true; this.pipe.wake(); return this.proxy }
  off() { this.active = false; return this.proxy }
  remove() { this.pipe.drop(this) }
}
const EFFECT = {
  get(fx, name) {
    if (typeof name === 'symbol' || name in fx || OWN.has(name)) { const v = fx[name]; return typeof v === 'function' ? v.bind(fx) : v }
    // Asking for something it does not have is how other code finds out what an effect is (a dial asks for
    // onChange, a promise is tested for with `then`): that is answered with nothing. Setting one is a mistake, and is said.
    const key = SPELLING[camel(name)] || camel(name)
    return key in fx.def.settings ? fx.get(key) : undefined
  },
  set(fx, name, value) {
    if (name === 'active') { if (value) fx.on(); else fx.off() } else fx.set(name, value)
    return true
  },
  has(fx, name) { return name in fx || camel(name) in fx.def.settings },
}

// --------------------------------------------------------------------------------------------
// The effects of one canvas: their order, the graphics card's pictures, and the frame.
class Pipeline {
  constructor(canvas, options = {}) {
    this.canvas = canvas
    this.manual = !!options.manual
    this.sound = options.sound || null // where the music comes from when a scene has not said (a host's)
    // A host's function that gives a canvas laid over the scene's which is PART OF THE SCENE'S PICTURE (the old scene
    // going out during a transition), or nothing. The effects are given the two together, and are shown over both.
    this.under = options.under || null
    this.effects = []
    this.listener = new Listener()
    this.heard = false
    this.time = 0
    this.frames = 0
    this.dt = 1 / 60
    this.W = this.H = 1
    this.quality = 'auto'
    this.scale = 1
    this.sized = false
    this.least = 0.25
    this.handover = 0
    this.small = null // a 2D canvas the scene's picture is made smaller on, before it is handed over
    this.slow = 0
    this.best = Infinity
    this.pace = 0
    this.clock = 0
    this.gl = null
    this.layer = null
    this.failed = false
    this.lost = false
    this.closed = false
    this.raf = 0
    this.counts = { textures: 0, framebuffers: 0, programs: 0 }
    this.passes = 0
    this.told = null // a host's function for the music's numbers, called when it has answered the last (`ack`)
    this.armed = true
    this.toldLast = ''
    this.after = null // a host's function, called when a frame's picture is on the screen
    this.reset()
  }

  /** What the graphics card holds: nothing, until there is a context to hold it. */
  reset() {
    this.programs = new Map()
    this.input = null
    this.main = []
    this.pool = []
    this.inUse = []
    this.float = false
    this.sounds = null
    this.soundStamp = -1
    this.w = this.h = 0
  }

  // --- the canvas the result is shown on, and its context
  open() {
    if (this.gl || this.failed || this.closed) return !!this.gl
    const { canvas } = this
    // The context of the scene that ran before, when there is one: a page may hold only a few, making one
    // takes a moment on a tablet, and its compiled programs are as good for this scene as for the last.
    const kept = spare && !spare.gl.isContextLost() ? spare : null
    spare = null
    const layer = this.layer = kept ? kept.layer : document.createElement('canvas')
    layer.dataset.effectsLayer = ''
    layer.style.cssText = 'position:absolute;pointer-events:none;margin:0;padding:0;border:0;inset:auto;display:none'
    canvas.after(layer)
    const gl = kept ? kept.gl : layer.getContext('webgl2', { alpha: false, antialias: false, depth: false, stencil: false, powerPreference: 'high-performance' })
    if (kept) { this.programs = kept.programs; this.counts.programs = kept.programs.size }
    if (!gl) {
      this.failed = true
      layer.remove()
      this.layer = null
      console.warn('The effects need WebGL 2, which this browser or device does not have: the scene is shown without them.')
      return false
    }
    this.gl = gl
    this.onLost = (e) => { e.preventDefault(); this.lost = true; this.reset(); for (const fx of this.effects) fx.history = null }
    // The context came back: everything is made again as it is next needed. Trails start from black.
    this.onFound = () => { this.lost = false; this.counts = { textures: 0, framebuffers: 0, programs: 0 }; this.begin() }
    layer.addEventListener('webglcontextlost', this.onLost)
    layer.addEventListener('webglcontextrestored', this.onFound)
    this.begin()
    return true
  }

  begin() {
    const gl = this.gl
    this.float = !!(gl.getExtension('EXT_color_buffer_float') || gl.getExtension('EXT_color_buffer_half_float'))
    gl.disable(gl.DEPTH_TEST)
    gl.disable(gl.BLEND)
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true)
  }

  /** Frames by itself (a page that has no host to say when the scene has drawn): after the scene's own. */
  wake() {
    if (this.manual || this.raf || this.closed) return
    let last = 0
    const tick = (now) => {
      if (this.closed) return
      if (!this.canvas.isConnected || (this.layer && !this.layer.isConnected)) return this.close()
      this.raf = requestAnimationFrame(tick)
      const dt = last ? Math.min(0.1, (now - last) / 1000) : 1 / 60
      last = now
      this.frame(dt)
    }
    // Asked for from a timer, so it is behind the scene's own frame in the browser's list and stays there:
    // each frame the scene draws first, then this.
    this.raf = -1
    setTimeout(() => { if (!this.closed) this.raf = requestAnimationFrame(tick) }, 0)
  }

  close() {
    if (this.closed) return
    this.closed = true
    if (this.raf > 0) cancelAnimationFrame(this.raf)
    const gl = this.gl
    if (gl) {
      this.free()
      this.layer.removeEventListener('webglcontextlost', this.onLost)
      this.layer.removeEventListener('webglcontextrestored', this.onFound)
      // A shader a scene wrote itself goes with the scene; the library's own programs are kept with the context.
      for (const [key, p] of this.programs) if (/^shader\d/.test(key)) { gl.deleteProgram(p.program); this.programs.delete(key) }
      if (!this.lost && !gl.isContextLost()) {
        if (spare) spare.gl.getExtension('WEBGL_lose_context')?.loseContext()
        spare = { layer: this.layer, gl, programs: this.programs }
      } else gl.getExtension('WEBGL_lose_context')?.loseContext()
      this.gl = null
    }
    this.layer?.remove()
    this.layer = null
    this.effects.length = 0
    if (this.canvas[LAYER] === this) delete this.canvas[LAYER]
  }

  /** Every picture and frame buffer given back (a new size, or the end). */
  free() {
    const gl = this.gl
    const drop = (t) => {
      if (!t) return
      gl.deleteTexture(t.tex); this.counts.textures--
      if (t.fbo) { gl.deleteFramebuffer(t.fbo); this.counts.framebuffers-- }
    }
    drop(this.input)
    this.input = null
    for (const t of [...this.main, ...this.pool, ...this.inUse]) drop(t)
    this.main = []; this.pool = []; this.inUse = []
    for (const fx of this.effects) { if (fx.history) fx.history.forEach(drop); fx.history = null }
    if (this.sounds) { drop(this.sounds.spectrum); drop(this.sounds.waveform); this.sounds = null; this.soundStamp = -1 }
  }

  texture(w, h, { fbo = true, float = false, data = null, format = null } = {}) {
    const gl = this.gl
    const tex = gl.createTexture()
    this.counts.textures++
    gl.bindTexture(gl.TEXTURE_2D, tex)
    if (format === 'r8') gl.texImage2D(gl.TEXTURE_2D, 0, gl.R8, w, h, 0, gl.RED, gl.UNSIGNED_BYTE, data)
    else if (w) gl.texStorage2D(gl.TEXTURE_2D, 1, float ? gl.RGBA16F : gl.RGBA8, w, h)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    const t = { tex, w, h, fbo: null }
    if (fbo) {
      t.fbo = gl.createFramebuffer()
      this.counts.framebuffers++
      gl.bindFramebuffer(gl.FRAMEBUFFER, t.fbo)
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0)
      gl.clearColor(0, 0, 0, 1)
      gl.clear(gl.COLOR_BUFFER_BIT)
    }
    return t
  }

  /** A picture to work in for this frame, of a size: taken from those kept, or made. */
  scratch(w, h) {
    w = Math.max(1, Math.round(w)); h = Math.max(1, Math.round(h))
    const i = this.pool.findIndex((t) => t.w === w && t.h === h)
    const t = i >= 0 ? this.pool.splice(i, 1)[0] : this.texture(w, h)
    this.inUse.push(t)
    return t
  }

  /** A program by name, compiled the first time it is used. `said` is how a mistake in it is told. */
  program(key, body, said) {
    let p = this.programs.get(key)
    if (p) return p
    const gl = this.gl
    const compile = (type, source) => {
      const s = gl.createShader(type)
      gl.shaderSource(s, source)
      gl.compileShader(s)
      return s
    }
    const vs = compile(gl.VERTEX_SHADER, VERTEX), fs = compile(gl.FRAGMENT_SHADER, HEAD + body)
    const program = gl.createProgram()
    gl.attachShader(program, vs)
    gl.attachShader(program, fs)
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS) && !gl.isContextLost()) {
      const log = gl.getShaderInfoLog(fs) || gl.getProgramInfoLog(program) || ''
      gl.deleteShader(vs); gl.deleteShader(fs); gl.deleteProgram(program)
      throw new Error(said ? said(log, HEAD.split('\n').length - 1) : `visualfx.js: the ${key} effect's program did not compile on this device:\n${log}`)
    }
    gl.deleteShader(vs); gl.deleteShader(fs)
    this.counts.programs++
    const locs = {}
    const n = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS) || 0
    for (let i = 0; i < n; i++) {
      const name = gl.getActiveUniform(program, i).name.replace(/\[0\]$/, '')
      locs[name] = gl.getUniformLocation(program, name)
    }
    p = { program, locs }
    this.programs.set(key, p)
    return p
  }

  /**
   * Run a program over every pixel of `to` (a picture, or null for the screen), reading `from`.
   * `values` are its own numbers; `fx` gives the effect's amount and its last frame.
   */
  draw(p, from, to, values, fx, extra) {
    const gl = this.gl, L = p.locs
    gl.bindFramebuffer(gl.FRAMEBUFFER, to ? to.fbo : null)
    gl.viewport(0, 0, to ? to.w : this.w, to ? to.h : this.h)
    gl.useProgram(p.program)
    // The sound's pictures are made or brought up to date first: doing that leaves one of them where the scene's picture goes.
    const sounds = L.spectrum || L.waveform ? this.soundPictures() : null
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, from.tex)
    if (L.picture) gl.uniform1i(L.picture, 0)
    if (L.flip) gl.uniform1f(L.flip, to ? 0 : 1)
    if (L.resolution) gl.uniform2f(L.resolution, to ? to.w : this.w, to ? to.h : this.h)
    if (L.size) gl.uniform2f(L.size, this.W, this.H)
    if (L.time) gl.uniform1f(L.time, this.time)
    if (L.dt) gl.uniform1f(L.dt, this.dt)
    if (L.frame) gl.uniform1f(L.frame, this.frames)
    if (L.amount) gl.uniform1f(L.amount, fx ? clamp(fx.get('amount'), 0, 1) : 1)
    if (L.seed && !(values && 'seed' in values)) gl.uniform1f(L.seed, 1)
    const l = this.listener
    if (L.bass || L.mids || L.highs || L.loudness || L.pulse || L.spectrum || L.waveform) l.used = true
    if (L.bass) gl.uniform1f(L.bass, l.bass)
    if (L.mids) gl.uniform1f(L.mids, l.mids)
    if (L.highs) gl.uniform1f(L.highs, l.highs)
    if (L.loudness) gl.uniform1f(L.loudness, l.loudness)
    if (L.pulse) gl.uniform1f(L.pulse, l.pulse)
    if (sounds) {
      const s = sounds
      gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, s.spectrum.tex)
      gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, s.waveform.tex)
      if (L.spectrum) gl.uniform1i(L.spectrum, 2)
      if (L.waveform) gl.uniform1i(L.waveform, 3)
    }
    if (L.previous) {
      gl.activeTexture(gl.TEXTURE1)
      gl.bindTexture(gl.TEXTURE_2D, extra && extra.previous ? extra.previous.tex : from.tex)
      gl.uniform1i(L.previous, 1)
    }
    if (L.other && extra && extra.other) {
      gl.activeTexture(gl.TEXTURE4)
      gl.bindTexture(gl.TEXTURE_2D, extra.other.tex)
      gl.uniform1i(L.other, 4)
    }
    for (const name in values) {
      const loc = L[name], v = values[name]
      if (!loc) continue
      if (typeof v === 'number') gl.uniform1f(loc, v)
      else if (v.length === 2) gl.uniform2f(loc, v[0], v[1])
      else if (v.length === 3) gl.uniform3f(loc, v[0], v[1], v[2])
      else gl.uniform3fv(loc, v)
    }
    gl.drawArrays(gl.TRIANGLES, 0, 3)
    this.passes++
  }

  /** The sound as two thin pictures a program can read: the spectrum and the wave. */
  soundPictures() {
    const gl = this.gl, l = this.listener
    if (!this.sounds) {
      this.sounds = { spectrum: this.texture(64, 1, { fbo: false, format: 'r8', data: l.spectrum }), waveform: this.texture(256, 1, { fbo: false, format: 'r8', data: l.waveform }) }
      this.soundStamp = l.stamp
    } else if (this.soundStamp !== l.stamp) {
      this.soundStamp = l.stamp
      gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1)
      gl.bindTexture(gl.TEXTURE_2D, this.sounds.spectrum.tex)
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 64, 1, gl.RED, gl.UNSIGNED_BYTE, l.spectrum)
      gl.bindTexture(gl.TEXTURE_2D, this.sounds.waveform.tex)
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 1, gl.RED, gl.UNSIGNED_BYTE, l.waveform)
    }
    return this.sounds
  }

  // --- the size: the scene's canvas, pixel for pixel, or a part of it when that is too much for the device
  fit() {
    const { canvas, layer, gl } = this
    const W = canvas.clientWidth || canvas.width, H = canvas.clientHeight || canvas.height
    this.W = W; this.H = H
    if (this.quality === 'auto' && !this.sized) {
      // A tablet's screen has more pixels than its graphics card can fill several times a frame: it starts
      // with about as many as a 1080p picture. From there `watch` takes it down if the device is not keeping up.
      this.sized = true
      let coarse = false
      try { coarse = matchMedia('(pointer: coarse)').matches } catch (e) { /* no such question here */ }
      this.scale = Math.min(1, Math.sqrt((coarse ? 2.1e6 : 9e6) / Math.max(1, canvas.width * canvas.height)))
    }
    // Never fewer than a pixel for each of the scene's points.
    this.least = Math.min(1, Math.max(0.25, W / Math.max(1, canvas.width)))
    const scale = typeof this.quality === 'number' ? clamp(this.quality, 0.1, 1) : Math.max(this.least, this.scale)
    const w = Math.max(1, Math.round(canvas.width * scale)), h = Math.max(1, Math.round(canvas.height * scale))
    if (layer.style.left !== canvas.offsetLeft + 'px') layer.style.left = canvas.offsetLeft + 'px'
    if (layer.style.top !== canvas.offsetTop + 'px') layer.style.top = canvas.offsetTop + 'px'
    if (layer.style.width !== W + 'px') layer.style.width = W + 'px'
    if (layer.style.height !== H + 'px') layer.style.height = H + 'px'
    // Straight after the scene's canvas, under anything else laid over it (a dial is not blurred).
    const below = this.over() || canvas
    if (below.nextSibling !== layer) below.after(layer)
    if (w === this.w && h === this.h) return
    if (this.w) this.free()
    this.w = w; this.h = h
    layer.width = w
    layer.height = h
    this.main = [this.texture(w, h), this.texture(w, h)]
  }

  /** What is laid over the scene's canvas as part of its picture just now (see `under`), if anything is. */
  over() {
    if (!this.under) return null
    try { const c = this.under(); return c && c.isConnected && c.width && c.height ? c : null } catch (e) { return null }
  }

  /**
   * The scene's canvas as a picture on the graphics card. Some browsers hand it over without touching the
   * pixels; Safari's engine reads every one back first, which at a tablet's full size is most of a frame.
   * So when the effects work on fewer pixels than the canvas has, it is made that small first (a 2D
   * canvas-to-canvas copy, which the card does), and only the small one is handed over.
   */
  upload() {
    const gl = this.gl, c = this.canvas
    const t0 = performance.now()
    let from = c
    const over = this.over()
    if (over || this.w < c.width * 0.95) {
      if (!this.small) this.small = document.createElement('canvas').getContext('2d')
      const s = this.small
      if (s.canvas.width !== this.w || s.canvas.height !== this.h) { s.canvas.width = this.w; s.canvas.height = this.h }
      s.globalCompositeOperation = 'copy'
      s.drawImage(c, 0, 0, this.w, this.h)
      if (over) { s.globalCompositeOperation = 'source-over'; s.drawImage(over, 0, 0, this.w, this.h) }
      from = s.canvas
    }
    if (!this.input) this.input = this.texture(0, 0, { fbo: false })
    this.input.w = from.width; this.input.h = from.height
    gl.bindTexture(gl.TEXTURE_2D, this.input.tex)
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, from)
    // How long the hand-over held the page up (nothing, where the card does it by itself).
    const took = performance.now() - t0
    this.handover += (took - this.handover) * 0.2
  }

  /**
   * Is the device keeping up? When the hand-over takes more than a few milliseconds, or frames have been
   * late for a while, the effects work on fewer pixels. Only the wall clock is used here, and only for
   * this: under a recorder's stepped clock nothing is ever late, so a recording keeps every pixel.
   */
  watch() {
    const now = performance.now()
    const gap = now - this.clock
    this.clock = now
    if (this.quality !== 'auto' || !(gap > 0) || gap > 250 || this.scale <= this.least) { this.slow = 0; return }
    if (this.handover > 4 && this.frames > 10) {
      this.scale = Math.max(this.least, this.scale * Math.sqrt(3 / this.handover))
      this.handover = 0
      return
    }
    this.pace = this.pace ? this.pace + (gap - this.pace) * 0.1 : gap
    if (this.frames > 30) this.best = Math.min(this.best, this.pace)
    this.slow = this.pace > this.best * 1.4 ? this.slow + 1 : 0
    if (this.slow > 45) {
      this.scale = Math.max(this.least, this.scale * 0.75)
      this.slow = 0
    }
  }

  /**
   * ONE FRAME: the scene has drawn, `dt` seconds after the last. A host calls this after the scene's
   * draw (`manual`); otherwise it is called each frame the browser gives.
   */
  frame(dt = 1 / 60) {
    if (this.closed) return
    this.dt = dt
    this.time += dt
    this.frames++
    if (!this.heard && this.sound) { this.heard = true; try { this.listener.listen(typeof this.sound === 'function' ? this.sound() : this.sound) } catch (e) { /* no sound after all */ } }
    this.listener.update(dt)
    this.tell()
    const active = this.effects.filter((fx) => fx.active)
    if (!active.length || !this.canvas.width || !this.canvas.height) {
      if (this.layer && this.layer.style.display !== 'none') this.layer.style.display = 'none'
      return
    }
    if (!this.open() || this.lost) return
    this.watch()
    this.fit()
    if (this.layer.style.display !== 'block') this.layer.style.display = 'block'
    this.passes = 0
    this.upload()
    // Backdrops go behind the scene's drawing, so they are first whatever the order.
    active.sort((a, b) => (b.def.backdrop ? 1 : 0) - (a.def.backdrop ? 1 : 0))
    let from = this.input
    for (let i = 0; i < active.length; i++) {
      const fx = active[i], last = i === active.length - 1
      const to = last ? null : from === this.main[0] ? this.main[1] : this.main[0]
      from = (fx.def.run || runOne)(this, fx, from, to) || to
    }
    this.pool.push(...this.inUse.splice(0))
    if (this.after) this.after(this.api)
  }

  /** The music's numbers for a host that asked to be told (Python), when they have changed. */
  tell() {
    const l = this.listener
    if (!this.told || !this.armed) return
    const now = [l.bass, l.mids, l.highs, l.loudness, l.pulse].map((v) => Math.round(v * 1000) / 1000)
    if (now.join() === this.toldLast) return
    this.toldLast = now.join()
    this.armed = false
    // Told as an object with one list in it: that is the shape a host's callback is given (Pyctures makes an event of it).
    this.told({ b: now })
  }

  /** The picture on the screen as numbers, straight after a frame: { width, height, data } with four numbers a pixel, top row first. */
  pixels() {
    const gl = this.gl
    if (!gl || !this.w || this.layer.style.display === 'none') {
      // No effect is on: the picture is the scene's own.
      const c = this.canvas, copy = Object.assign(document.createElement('canvas'), { width: c.width, height: c.height }).getContext('2d')
      copy.drawImage(c, 0, 0)
      return { width: c.width, height: c.height, data: new Uint8Array(copy.getImageData(0, 0, c.width, c.height).data.buffer) }
    }
    const { w, h } = this, data = new Uint8Array(w * h * 4), row = w * 4
    gl.bindFramebuffer(gl.FRAMEBUFFER, null)
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, data)
    // The graphics card counts rows from the bottom.
    const line = new Uint8Array(row)
    for (let y = 0; y < h >> 1; y++) {
      const a = y * row, b = (h - 1 - y) * row
      line.set(data.subarray(a, a + row)); data.copyWithin(a, b, b + row); data.set(line, b)
    }
    return { width: w, height: h, data }
  }

  make(name, args) {
    const def = DEFS[name]
    const given = {}
    args = [...args]
    const last = args[args.length - 1]
    const options = isPlain(last) ? spelled(args.pop()) : {}
    if (args.length > def.order.length) throw new Error(`${name}() was given ${args.length} values and takes ${def.order.length ? `${def.order.length} (${def.order.join(', ')})` : 'none'}. Its other settings go in by name: ${name}(${def.order.length ? '…, ' : ''}{ ${Object.keys(def.settings).filter((n) => !def.order.includes(n)).slice(0, 2).map((n) => `${n}: …`).join(', ')} })`)
    args.forEach((v, i) => { if (v !== undefined) given[def.order[i]] = v })
    const fx = new Effect(this, def, { ...given, ...options })
    fx.proxy = new Proxy(fx, EFFECT)
    if (this.effects.length >= 16) console.warn('That is more than sixteen effects on one scene: each is a pass over every pixel, so a tablet will slow down.')
    this.effects.push(fx)
    this.wake()
    return fx.proxy
  }

  drop(fx) {
    const i = this.effects.indexOf(fx)
    if (i < 0) return
    this.effects.splice(i, 1)
    fx.active = false
    if (fx.history && this.gl) {
      for (const t of fx.history) { this.gl.deleteTexture(t.tex); this.gl.deleteFramebuffer(t.fbo); this.counts.textures--; this.counts.framebuffers-- }
      fx.history = null
    }
  }
}

// --- how an effect is run. Each is given the picture so far and where to put its own (null: the screen),
// and gives back the picture it wrote when that is one of its own.
const uniforms = {}
function valuesOf(pipe, fx) {
  const out = uniforms, def = fx.def
  for (const k in out) delete out[k]
  for (const name in def.settings) {
    if (name === 'amount') continue
    const s = def.settings[name], as = (def.rename && def.rename[name]) || name
    const v = fx.get(name)
    if (s.kind === 'colour') out[as] = rgb(v)
    else if (s.kind === 'palette') { const p = paletteOf(v); out.pal = p.data; out.palCount = p.count }
    else if (s.kind === 'choice') out[as] = s.choices.indexOf(v)
    else if (s.kind === 'bool') out[as] = v ? 1 : 0
    else out[as] = s.unit === 'degrees' ? v * Math.PI / 180 : v
  }
  return out
}
const declared = (def) => Object.keys(def.settings).filter((n) => n !== 'amount' && n !== 'seed' && def.settings[n].kind !== 'palette')
  .map((n) => `uniform ${def.settings[n].kind === 'colour' ? 'vec3' : 'float'} ${(def.rename && def.rename[n]) || n};`).join('\n')
/** Two pictures of its own that an effect writes in turn, so it can read the one it made last frame. */
function historyOf(pipe, fx) {
  if (!fx.history || fx.history[0].w !== pipe.w || fx.history[0].h !== pipe.h) {
    if (fx.history) for (const t of fx.history) { pipe.gl.deleteTexture(t.tex); pipe.gl.deleteFramebuffer(t.fbo); pipe.counts.textures--; pipe.counts.framebuffers-- }
    fx.history = [pipe.texture(pipe.w, pipe.h, { float: pipe.float }), pipe.texture(pipe.w, pipe.h, { float: pipe.float })]
    fx.flipped = 0
  }
  fx.flipped ^= 1
  return [fx.history[fx.flipped], fx.history[fx.flipped ^ 1]]
}
function runOne(pipe, fx, from, to) {
  const def = fx.def
  const p = pipe.program(def.key || def.name, `${declared(def)}\n${def.pre || ''}\n${def.glsl}\n${def.post || ''}\n${def.backdrop ? MAIN_BACKDROP : MAIN}`, def.said)
  if (!def.feedback) { pipe.draw(p, from, to, valuesOf(pipe, fx), fx); return to }
  const [now, before] = historyOf(pipe, fx)
  pipe.draw(p, from, now, valuesOf(pipe, fx), fx, { previous: before })
  if (!to) pipe.draw(pipe.program('copy', COPY), now, null)
  return now
}

DEFS.blur = {
  name: 'blur', order: ['radius'], settings: { radius: num(8, 0, 200), amount: AMOUNT },
  run(pipe, fx, from, to) {
    // The blur is as wide as asked in the scene's points. A wide one is done on a smaller picture, which is the
    // same blur for a fraction of the work: each halving is itself a little blur.
    const sigma = Math.max(0.001, fx.get('radius')) * 0.5 * pipe.w / pipe.W
    const copy = pipe.program('copy', COPY), gauss = pipe.program('gauss', GAUSS)
    let level = Math.max(0, Math.ceil(Math.log2(sigma / 2.5))), src = from, w = pipe.w, h = pipe.h
    for (let i = 0; i < level; i++) {
      w /= 2; h /= 2
      if (w < 4 || h < 4) { level = i; w *= 2; h *= 2; break }
      const small = pipe.scratch(w, h)
      pipe.draw(copy, src, small)
      src = small
    }
    const s = Math.max(0.05, sigma / 2 ** level)
    const a = pipe.scratch(w, h), b = pipe.scratch(w, h)
    pipe.draw(gauss, src, a, { dir: [1 / a.w, 0], sigma: s })
    pipe.draw(gauss, a, b, { dir: [0, 1 / a.h], sigma: s })
    pipe.draw(pipe.program('blend', BLEND), from, to, { add: 0 }, fx, { other: b })
    return to
  },
}
DEFS.glow = {
  name: 'glow', order: ['strength'], settings: { strength: num(0.8, 0, 4), threshold: num(0.5, 0, 1), radius: num(24, 2, 200), amount: AMOUNT },
  run(pipe, fx, from, to) {
    const reach = Math.max(2, fx.get('radius')) * pipe.w / pipe.W
    // Smaller and smaller pictures of what is bright, then back up, each added to the one above: a wide soft
    // glow for the price of a few small passes. The smallest fades in, so the radius can be turned smoothly.
    const depth = clamp(Math.log2(reach) - 1, 1, 7), levels = Math.ceil(depth), part = depth - (levels - 1)
    const shrink = pipe.program('shrink', SHRINK), grow = pipe.program('grow', GROW)
    const down = []
    let w = pipe.w / 2, h = pipe.h / 2, src = from
    const first = pipe.scratch(w, h)
    pipe.draw(pipe.program('bright', BRIGHT), from, first, { threshold: fx.get('threshold'), texel: [0.5 / from.w, 0.5 / from.h] })
    down.push(first)
    src = first
    for (let i = 1; i < levels && w >= 8 && h >= 8; i++) {
      w /= 2; h /= 2
      const t = pipe.scratch(w, h)
      pipe.draw(shrink, src, t, { texel: [1 / src.w, 1 / src.h] })
      down.push(t)
      src = t
    }
    let up = down[down.length - 1], weight = down.length === levels ? part : 1
    for (let i = down.length - 2; i >= 0; i--) {
      const t = pipe.scratch(down[i].w, down[i].h)
      pipe.draw(grow, up, t, { texel: [0.5 / up.w, 0.5 / up.h], weight }, null, { other: down[i] })
      up = t
      weight = 1
    }
    const total = down.length > 1 ? down.length - 1 + (down.length === levels ? part : 1) : 1
    pipe.draw(pipe.program('blend', BLEND), from, to, { add: fx.get('strength') * 2 / total }, fx, { other: up })
    return to
  },
}
DEFS.trails = {
  name: 'trails', order: ['length'],
  settings: { length: num(0.5, 0, 20, { unit: 's' }), zoom: num(1, 0.1, 10), spin: angle(0, -720, 720), hue: angle(0, -720, 720), dx: num(0, -2000, 2000), dy: num(0, -2000, 2000), x: place(), y: place(), amount: AMOUNT },
  run(pipe, fx, from, to) {
    const dt = pipe.dt, length = fx.get('length')
    const [now, before] = historyOf(pipe, fx)
    // `length` is the seconds a trail takes to fade to a tenth, whatever the frame rate. Zoom, spin and hue are
    // by the second too. Where the card cannot keep fine shades, a sliver is taken off so a trail does end.
    pipe.draw(pipe.program('trail', TRAIL), from, now, {
      keep: length > 0 ? Math.pow(0.1, dt / length) : 0, grow: Math.pow(Math.max(0.01, fx.get('zoom')), dt), spun: fx.get('spin') * Math.PI / 180 * dt, hued: fx.get('hue') * Math.PI / 180 * dt,
      cut: pipe.float ? 0 : 0.6 / 255, centre: [fx.get('x'), fx.get('y')], moved: [fx.get('dx') * dt, fx.get('dy') * dt],
    }, fx, { previous: before })
    const amount = fx.get('amount')
    if (to || amount < 1) {
      if (amount < 1) pipe.draw(pipe.program('blend', BLEND), from, to, { add: 0 }, fx, { other: now })
      else return now
      return to
    }
    pipe.draw(pipe.program('copy', COPY), now, null)
    return now
  },
}

// --------------------------------------------------------------------------------------------
// YOUR OWN EFFECT, from a program for the graphics card. See the README for what it is given.
let shaders = 0
function customDef(source, settings) {
  if (typeof source !== 'string' || !/\beffect\s*\(/.test(source)) throw new Error('shader() takes a program that has a function `vec4 effect(vec2 uv)`: the colour at one place of the picture. For example: shader("vec4 effect(vec2 uv) { return texture(picture, uv).bgra; }")')
  const defs = {}
  for (const name in settings) {
    const v = settings[name]
    if (/^(picture|previous|spectrum|waveform|resolution|size|time|dt|frame|amount|bass|mids|highs|loudness|pulse|pal|palCount)$/.test(name)) throw new Error(`A shader is already given something called ${name}: call your setting something else`)
    if (typeof v === 'number') defs[name] = num(v, Math.min(0, v * 4), Math.max(1, v * 4))
    else if (Array.isArray(v) && v.length === 3 && v.every((n) => typeof n === 'number')) defs[name] = num(v[0], v[1], v[2])
    else if (typeof v === 'boolean') defs[name] = flag(v)
    else if (typeof v === 'string') defs[name] = colour(v)
    else throw new Error(`A shader's setting is a number (speed: 2), a number with its range (speed: [2, 0, 10]), true or false, or a colour ("gold"). ${name} is ${JSON.stringify(v)}`)
  }
  const def = { name: 'shader', key: `shader${++shaders}`, order: [], settings: { ...defs, amount: AMOUNT }, glsl: `#line 1\n${source}`, feedback: /\bprevious\b/.test(source) }
  def.said = (log) => {
    // The card says "ERROR: 0:12: …" with the line of the shader as it was written.
    const lines = String(log).replace(/\0/g, '').split('\n').map((l) => l.trim()).filter(Boolean).map((l) => l.replace(/^ERROR:\s*\d+:(\d+):\s*/, 'line $1: '))
    return `Your shader has a mistake the graphics card will not accept:\n${lines.join('\n') || 'it gave no reason'}\nIt is given: picture, previous, resolution, size, time, dt, frame, amount, bass, mids, highs, loudness, pulse, spectrum, waveform${Object.keys(defs).length ? ', and your settings ' + Object.keys(defs).join(', ') : ''}. Numbers need a decimal point (2.0, not 2).`
  }
  return def
}

// --------------------------------------------------------------------------------------------
// What a scene is given for one canvas.
const NAMES = [...Object.keys(DEFS)]
function api(pipe) {
  const out = {}
  for (const name of NAMES) out[name] = (...args) => pipe.make(name, args)
  // The other spellings of the same things.
  out.bloom = out.glow
  out.colorCycle = out.colourCycle
  out.bulge = out.fisheye
  out.halftone = out.dots
  out.colorBleed = out.colourBleed
  out.godRays = out.lightRays
  const band = (name) => () => { pipe.listener.used = true; return pipe.listener[name] }
  const bands = { bass: band('bass'), mids: band('mids'), highs: band('highs'), loudness: band('loudness'), pulse: band('pulse') }
  const bandOf = (which) => {
    if (typeof which === 'function') return which
    const fn = bands[String(which).toLowerCase()] || (String(which).toLowerCase() === 'level' ? bands.loudness : null) || (String(which).toLowerCase() === 'beat' ? bands.pulse : null)
    if (!fn) throw new Error(`"${which}" is not something the music has. There are bass, mids, highs, loudness and pulse`)
    return fn
  }
  const made = new Map() // effects by a host's number (Python)
  Object.assign(out, bands, {
    /** Your own effect: shader("vec4 effect(vec2 uv) { … }", { speed: 2 }). It is compiled now, so a mistake is said here. */
    shader(source, settings = {}) {
      const def = customDef(source, settings)
      if (!pipe.open()) throw new Error('A shader needs WebGL 2, which this browser or device does not have')
      DEFS[def.key] = def
      try {
        pipe.program(def.key, `${declared(def)}\n${def.glsl}\n${MAIN}`, def.said)
        return pipe.make(def.key, [])
      } finally { delete DEFS[def.key] }
    },
    /** Several effects at once: look("dream"). It gives them back by name, with off(), on() and remove() for the lot. */
    look(name, amount = 1) {
      const key = String(name).toLowerCase().replace(/[\s_-]/g, '')
      const recipe = LOOKS[key]
      if (!recipe) throw new Error(`There is no look called "${name}". There are ${Object.keys(LOOKS).join(', ')}`)
      const parts = recipe.map(([effect, settings]) => pipe.make(effect, [{ ...settings, amount }]))
      const all = { name: key, effects: parts, on() { parts.forEach((p) => p.on()); return all }, off() { parts.forEach((p) => p.off()); return all }, remove() { parts.forEach((p) => p.remove()) } }
      recipe.forEach(([effect], i) => { all[effect] = parts[i] })
      Object.defineProperty(all, 'amount', { get: () => parts[0].amount, set: (v) => { for (const p of parts) p.amount = v } })
      return all
    },
    lookNames: () => Object.keys(LOOKS),
    effectNames: () => [...NAMES],
    paletteNames: () => Object.keys(PALETTES),
    clearEffects() { for (const fx of [...pipe.effects]) pipe.drop(fx); made.clear() },
    /** What the music is taken from: soundOutput(), a synth, a song, the microphone, or anything with samples(). */
    listenTo(target) {
      pipe.heard = true
      pipe.listener.used = true
      pipe.listener.listen(target)
      return { ...bands, level: bands.loudness, spectrum: () => pipe.listener.spectrum, waveform: () => pipe.listener.waveform, stop() { pipe.listener.listen(null) } }
    },
    /** Tie a setting to the music: react(glowing, "strength", "bass", { from: 0.3, to: 1.2 }). */
    react(effect, setting, which = 'loudness', range = {}) {
      const fx = typeof effect === 'number' ? made.get(effect) : effect
      if (!fx || typeof fx.describe !== 'function') throw new Error('react() is given an effect, the name of one of its settings and what to follow: react(glowing, "strength", "bass")')
      const d = fx.describe(setting), fn = bandOf(which)
      const now = fx.get(setting)
      const { from = typeof now === 'number' ? now : d.min ?? 0, to = d.max ?? 1 } = range || {}
      fx.set(setting, () => from + (to - from) * fn())
      return fx
    },
    /** How many of the canvas's pixels the effects work on: 1 is all, 0.5 is half each way, "auto" lets the device decide. */
    effectsQuality(value) {
      if (value === undefined) return pipe.quality === 'auto' ? pipe.scale : pipe.quality
      if (value !== 'auto' && !(typeof value === 'number' && value > 0)) throw new Error('effectsQuality() is given a number from 0.25 to 1, or "auto"')
      pipe.quality = value
      pipe.scale = 1
      pipe.sized = false
      pipe.best = Infinity
    },
    // --- for a host (pictures.js, Pyctures): the frame, the picture, and the end
    frame: (dt) => pipe.frame(dt),
    /** Called each time a frame's picture is on the screen, when `pixels()` can be read (a recorder's moment). */
    onFrame(fn) { pipe.after = fn },
    pixels: () => pipe.pixels(),
    stats: () => ({ ...pipe.counts, handover: pipe.handover, passes: pipe.passes, effects: pipe.effects.length, width: pipe.w, height: pipe.h, scale: pipe.w && pipe.canvas.width ? pipe.w / pipe.canvas.width : 1, float: pipe.float, context: !!pipe.gl, lost: pipe.lost, time: pipe.time, frames: pipe.frames }),
    close: () => pipe.close(),
    pipeline: pipe,
    // --- for a host that keeps the scene's code somewhere else (Python): effects by number, one call each
    make(kind, id, args) {
      const name = camel(kind)
      if (name === 'look') { const all = out.look(...(args || [])); made.set(id, all); return }
      if (name === 'shader') { made.set(id, out.shader(...(args || []))); return }
      if (!(name in DEFS || ['bloom', 'colorCycle', 'bulge', 'halftone', 'colorBleed', 'godRays'].includes(name))) throw new Error(`There is no effect called ${kind}`)
      made.set(id, out[name](...(args || [])))
    },
    set(id, name, value) { const fx = made.get(id); if (fx) fx[camel(name)] = value },
    call(id, name) { const fx = made.get(id); if (fx && typeof fx[name] === 'function') fx[name]() },
    listen: (target) => out.listenTo(target),
    /** The music's five numbers are told to `fn` as { b: [bass, mids, highs, loudness, pulse] } when they change, once it has answered the last with ack(). */
    report(fn) { pipe.told = fn; pipe.armed = true; pipe.listener.used = true },
    ack() { pipe.armed = true },
  })
  return out
}

/** The effects of one canvas: `const { glow, trails } = effects(canvas)`. With no canvas, the page's only one. */
function effects(canvas, options) {
  if (canvas && !(typeof canvas.getBoundingClientRect === 'function')) { options = canvas; canvas = null }
  canvas ||= onlyCanvas()
  let pipe = canvas[LAYER]
  // `fresh`: a new run of the scene on a canvas that was kept starts with no effects.
  if (pipe && options && options.fresh) { pipe.close(); pipe = null }
  if (!pipe) {
    pipe = canvas[LAYER] = new Pipeline(canvas, options || {})
    pipe.api = api(pipe)
  }
  return pipe.api
}
/**
 * WHAT EACH EFFECT IS, in a line, and the group it is shown in. The documentation (docs/effects.md, its pictures)
 * is written from this and from the settings above, so an effect added here is in the docs with no more to do.
 */
const GROUPS = {
  'Shapes of the picture': ['kaleidoscope', 'mirror', 'tile', 'pixelate', 'hexagons', 'waves', 'ripple', 'wobble', 'heatHaze', 'swirl', 'fisheye', 'tunnel', 'droste', 'rotozoom', 'glassTiles', 'frosted', 'caustics', 'shake', 'punch'],
  'Blur and light': ['blur', 'zoomBlur', 'spinBlur', 'motionBlur', 'tiltShift', 'softFocus', 'glow', 'lightRays', 'streaks'],
  'What was drawn stays': ['trails', 'smear', 'stutter'],
  'Colours': ['hue', 'saturate', 'brighten', 'contrast', 'invert', 'posterize', 'tint', 'duotone', 'colourCycle', 'gradientMap', 'thermal', 'nightVision', 'sepia', 'threshold', 'solarize', 'rgbSplit', 'colourBleed', 'rainbowEdges'],
  'Screens and old computers': ['scanlines', 'crt', 'interlace', 'glitch', 'dither', 'led', 'letters'],
  'Drawn, printed and painted': ['edges', 'dots', 'emboss', 'sharpen', 'sketch', 'cartoon', 'stainedGlass', 'crosshatch', 'oil'],
  'In front of the picture': ['vignette', 'grain', 'dust', 'lightLeaks', 'rain', 'snow', 'bokeh', 'fog', 'lightning'],
  'Backdrops that need no drawing': ['plasma', 'flow', 'metaballs', 'starfield', 'warp', 'voronoi', 'moire', 'interference', 'aurora', 'fire', 'clouds', 'matrixRain', 'copperBars', 'checkerFloor', 'twister'],
  'The music, drawn': ['spectrumBars', 'spectrumRing', 'waveformRing', 'beatFlash', 'bassShake'],
}
const ABOUT = {
  kaleidoscope: 'One slice of the picture, folded round and round. The slice starts at the middle and points right: turn it with angle.',
  mirror: 'One half of the picture shown on both sides, or one quarter in all four.',
  tile: 'The picture repeated in rows and columns.',
  pixelate: 'Big square pixels.',
  hexagons: 'Six-sided pixels, like a honeycomb.',
  waves: 'The picture ripples like a flag in the wind.',
  ripple: 'Rings spreading from a point, as from a stone dropped in water.',
  wobble: 'The picture wobbles like jelly, or something seen under water.',
  heatHaze: 'The shimmer of hot air rising.',
  swirl: 'The middle of the picture twisted round, like stirred paint.',
  fisheye: 'A bulge, as through a round lens. Below zero it pinches instead.',
  tunnel: 'The picture becomes the walls of a tunnel you are flying down.',
  droste: 'The picture inside itself, smaller each time, for ever. With a twist it winds in as a spiral.',
  rotozoom: 'The picture tiled, turning and zooming: an old demo-scene favourite.',
  glassTiles: 'Seen through a wall of glass blocks.',
  frosted: 'Seen through frosted glass.',
  caustics: 'The net of bright lines that sunlight makes on the floor of a pool.',
  shake: 'The whole picture shakes. Set strength when something hits, and let it fall away.',
  punch: 'A zoom in towards a point. Tie its strength to the beat.',
  blur: 'Out of focus.',
  zoomBlur: 'Rushing towards a point.',
  spinBlur: 'Spinning round a point.',
  motionBlur: 'Moving fast in one direction.',
  tiltShift: 'A band in focus and the rest blurred, which makes a scene look like a tiny model.',
  softFocus: 'A soft, dreamy haze over the bright parts.',
  glow: 'Bright things shine and spread light around them.',
  lightRays: 'Rays of light streaming out from a point, through whatever is bright.',
  streaks: 'Long sideways flares from bright lights, as a film camera makes.',
  trails: 'What was drawn stays and fades. With zoom, spin and hue it becomes the classic screensaver tunnel.',
  smear: 'What was drawn is carried away on a slow current, like wet paint.',
  stutter: 'Only so many new pictures a second: the last one is held between them.',
  hue: 'Every colour moved round the colour wheel. With speed, the colours keep turning.',
  saturate: 'More colour, or less: at 0 the picture is grey.',
  brighten: 'Brighter, or darker below 1.',
  contrast: 'Lights lighter and darks darker.',
  invert: 'A negative: every colour swapped for its opposite.',
  posterize: 'Only a few shades of each colour, like a poster.',
  tint: 'Seen through coloured glass.',
  duotone: 'Two colours only: one for the dark parts and one for the light.',
  colourCycle: 'Brightness becomes a colour from a palette, and the colours move round.',
  gradientMap: 'Brightness becomes a colour from a palette, dark to light.',
  thermal: 'A heat camera: cold is dark blue, hot is yellow and white.',
  nightVision: 'Green, grainy and bright in the dark, like a night-vision scope.',
  sepia: 'The warm brown of an old photograph.',
  threshold: 'Two colours and nothing between: dark or light.',
  solarize: 'The bright parts turned to their opposite, as in an over-exposed photograph.',
  rgbSplit: 'Red and blue pulled apart, like a cheap lens or a bad signal.',
  colourBleed: 'Colours smeared sideways, as on old videotape.',
  rainbowEdges: 'Every edge in the picture drawn in rainbow colours.',
  scanlines: 'Dark lines across the picture, as on an old screen.',
  crt: 'An old television: curved glass, lines, and thin stripes of red, green and blue.',
  interlace: 'Every other line dark, swapping each frame, like old video.',
  glitch: 'A broken signal: blocks that jump sideways, a line that tears, a band of snow.',
  dither: 'A few colours made to pass for many with a pattern of dots, as old computers did.',
  led: 'A wall of round lamps.',
  letters: 'The picture made of marks, as an old terminal would show it.',
  edges: 'Only the outlines, each in its own colour.',
  dots: 'Printed in dots, big where the picture is bright, as a comic or a newspaper is.',
  emboss: 'Pressed into grey metal: only the bumps and hollows show.',
  sharpen: 'Crisper edges.',
  sketch: 'A pencil drawing on paper.',
  cartoon: 'Flat colours and black outlines.',
  stainedGlass: 'Pieces of coloured glass with dark lead between them.',
  crosshatch: 'Shaded with crossing pen lines: more lines where it is darker.',
  oil: 'Smoothed into patches of colour, like oil paint. Heavy: it looks at 36 places for every pixel.',
  vignette: 'Dark corners, which draw the eye to the middle.',
  grain: 'The fine speckle of film.',
  dust: 'Specks and scratches, as on old film.',
  lightLeaks: 'Warm light creeping in from the sides, as in an old camera.',
  rain: 'Rain falling in front of the picture.',
  snow: 'Snow falling in front of the picture.',
  bokeh: 'Soft discs of coloured light drifting by: lamps out of focus.',
  fog: 'Drifting mist, thicker towards the bottom.',
  lightning: 'A flash, now and then.',
  plasma: 'Slow rolling colour.',
  flow: 'Colour that folds and curls like ink in water.',
  metaballs: 'Blobs that melt into each other when they meet: a lava lamp.',
  starfield: 'Flying through stars.',
  warp: 'A chequered tunnel rushing past.',
  voronoi: 'Soft coloured cells that slowly shift.',
  moire: 'Two sets of rings crossing, making patterns neither has alone.',
  interference: 'Waves from four moving points, crossing.',
  aurora: 'The northern lights over a night sky.',
  fire: 'Flames rising from the bottom of the picture.',
  clouds: 'A sky with drifting clouds.',
  matrixRain: 'Green marks falling in columns.',
  copperBars: 'Shining bars sliding up and down: a demo-scene classic.',
  checkerFloor: 'A chequered floor rushing towards you under a glowing horizon.',
  twister: 'A twisting four-sided bar, another demo-scene classic.',
  spectrumBars: 'The music as bars: low notes at the left, high at the right.',
  spectrumRing: 'The music as bars round a ring.',
  waveformRing: 'The sound\'s own wave, bent into a ring.',
  beatFlash: 'A flash of colour on each beat.',
  bassShake: 'The picture shakes with the bass.',
}
const LOOK_ABOUT = {
  dream: 'Soft, glowing and rich.', arcade: 'The curved glass of an old arcade machine.', vhs: 'A worn videotape.', neon: 'Glowing outlines in the dark.',
  comic: 'A few flat colours, printed in dots.', underwater: 'Blue, wobbling and dim at the edges.', oldfilm: 'Brown, grainy and dark at the corners.',
  disco: 'A kaleidoscope whose colours keep turning.', gameboy: 'Four shades of green.', c64: 'The colours of a 1980s home computer.',
  noir: 'Black and white, high contrast, grainy.', comicbook: 'Black outlines over printed dots.', storm: 'Rain, lightning and fog.',
  winter: 'Cold light and falling snow.', cinema: 'A film camera: flares, a narrow focus, grain.', terminal: 'Green marks on a dark screen.',
}
const groupOf = (name) => Object.keys(GROUPS).find((g) => GROUPS[g].includes(name)) || 'More'

/** Every effect and its settings, for a host that keeps a scene's code in another language. */
effects.definitions = () => {
  const out = {}
  for (const name of NAMES) {
    const def = DEFS[name], settings = {}
    for (const key in def.settings) { const s = def.settings[key]; settings[key] = { kind: s.kind, default: s.default, ...(s.min !== undefined ? { min: s.min, max: s.max } : {}), ...(s.choices ? { choices: s.choices } : {}), ...(s.place ? { place: true } : {}), ...(s.unit ? { unit: s.unit } : {}) } }
    out[name] = { order: def.order, settings, backdrop: !!def.backdrop, cost: def.cost || (def.run ? 'some' : 'light'), feedback: !!def.feedback || name === 'trails', group: groupOf(name), about: ABOUT[name] || '' }
  }
  return { effects: out, groups: [...Object.keys(GROUPS), 'More'], looks: Object.keys(LOOKS), recipes: LOOKS, lookAbout: LOOK_ABOUT, palettes: Object.keys(PALETTES), paletteColours: PALETTES, aliases: { bloom: 'glow', colorCycle: 'colourCycle', bulge: 'fisheye', halftone: 'dots', colorBleed: 'colourBleed', godRays: 'lightRays' } }
}
function onlyCanvas() {
  // A canvas laid over the scene's by this library, by dials.js or for a change of scene is not the scene's.
  const found = [...document.querySelectorAll('canvas')].filter((c) => c.dataset.effectsLayer === undefined && c.dataset.dialsLayer === undefined && !Object.keys(c.dataset).some((k) => /Transition$/.test(k)))
  if (found.length === 1) return found[0]
  throw new Error(found.length
    ? 'There is more than one canvas on this page, so say which one the effects are for: const { glow, trails } = effects(canvas)'
    : 'There is no canvas on this page to put effects on')
}

// --------------------------------------------------------------------------------------------
// FILM: the scene stepped a frame at a time, each frame exactly 1/fps after the last however long it took
// to draw, for a page that has no recorder of its own (Circuitry has one, and steps the page the same way).
// SOUND is stepped with it when the scene's sound is a stepped player (synths.js: createPlayer({ stepped }),
// which pictures.js makes for runScene(…, { stepped: { fps } })): before each frame is drawn the player is
// told where the clock is and makes exactly the samples up to there, so the film's sound is with its
// pictures to the sample, and what the effects hear (bass(), pulse()) is the frame they are drawn on.
/** The stepped player in what was given: the player, a scene with one as `sound`, or a function that gives either. */
function steppedOf(given) {
  try {
    let s = typeof given === 'function' ? given() : given
    if (s && !s.stepped && s.sound) s = s.sound
    if (s && !s.stepped && s.player) s = s.player
    return s && s.stepped && typeof s.stepped.advance === 'function' ? s.stepped : null
  } catch (e) { return null }
}

/**
 * The next frames of the page, one at a time: `await renderFrames({ seconds: 3, fps: 60, onFrame })`.
 * `onFrame(canvas, n, time)` is given each finished picture (the scene, its effects and anything else
 * laid over it) on one canvas that is used again for the next, and may be awaited. With no `onFrame` it
 * gives back a list of pictures (ImageBitmap), which for a long film is a great deal of memory.
 * While it runs, the page's clock is this one: requestAnimationFrame and performance.now are stepped.
 * `sound` is the scene's stepped sound (a synths.js stepped player, a pictures.js scene that has one, or a
 * function that gives either once there is one): it is moved with the frames, and `onSound(left, right,
 * sampleRate, n)` is given the samples of each frame after it, exactly sampleRate / fps of them with the
 * remainder carried, so n frames are round(n × sampleRate / fps) samples. Without `sound`, or with a
 * scene that makes none, `onSound` is never called.
 */
async function renderFrames({ seconds = 3, fps = 60, frames = Math.round(seconds * fps), onFrame = null, canvas = null, sound = null, onSound = null } = {}) {
  canvas ||= onlyCanvas()
  const real = { raf: window.requestAnimationFrame, caf: window.cancelAnimationFrame, now: performance.now }
  // The frame the browser has already promised is let through first, so everything waiting is waiting on this clock.
  await new Promise((done) => real.raf.call(window, () => setTimeout(done, 0)))
  let waiting = [], ids = 0, clock = 0
  window.requestAnimationFrame = (fn) => { waiting.push([++ids, fn]); return -ids }
  window.cancelAnimationFrame = (id) => { if (id < 0) waiting = waiting.filter(([n]) => n !== -id); else real.caf.call(window, id) }
  performance.now = () => clock || real.now.call(performance)
  const out = Object.assign(document.createElement('canvas'), { width: canvas.width, height: canvas.height })
  const g = out.getContext('2d')
  const kept = []
  // THE SOUND. `stepped` once the scene has a stepped player; `owed` the frames that went by before it had one,
  // which are silence. The player's clock is the page's, so it is told the clock, and makes the samples up to it.
  let stepped = null, owed = 0, first = 0, heardTo = 0, stop = null
  const hear = async (n) => {
    if (!sound) return
    if (!stepped) {
      stepped = steppedOf(sound)
      if (!stepped) { owed = n; return }
      // A player that has made nothing yet began with the film; one that has is joined where it is.
      if (stepped.samples) { stepped.startAt(clock / 1000); owed = n } else { stepped.startAt(first / 1000); owed = 0 }
      stepped.take()
      const lead = Math.round(owed * stepped.sampleRate / fps)
      if (lead && onSound) await onSound(new Float32Array(lead), new Float32Array(lead), stepped.sampleRate, -1)
      heardTo = lead
    }
    const made = []
    stop = stepped.onAdvance((l, r) => made.push([l, r]))
    try { await stepped.advance(clock / 1000) } finally { stop(); stop = null }
    stepped.take()
    for (const [l, r] of made) { heardTo += l.length; if (onSound) await onSound(l, r, stepped.sampleRate, n - 1) }
  }
  try {
    // One real frame lets what was already asked of the browser's own clock ask again of this one.
    // This clock starts at that frame's own time, so the first step is exactly 1/fps like every other.
    const zero = await new Promise((done) => real.raf.call(window, (now) => { clock = now; setTimeout(() => done(now), 0) }))
    first = zero + 1000 / fps
    for (let n = 0; n < frames; n++) {
      clock = zero + (n + 1) * 1000 / fps
      // The sound up to this frame is made before the frame is drawn: what the scene reads of it is this frame's.
      await hear(n)
      const due = waiting
      waiting = []
      for (const [, fn] of due) fn(clock)
      // Copied now, in the same task as the drawing: a graphics-card canvas keeps its picture no longer.
      g.fillStyle = '#000'
      g.fillRect(0, 0, out.width, out.height)
      const box = canvas.getBoundingClientRect()
      for (const c of canvas.parentElement ? canvas.parentElement.querySelectorAll('canvas') : [canvas]) {
        if (!c.width || !c.height || getComputedStyle(c).display === 'none' || getComputedStyle(c).visibility === 'hidden') continue
        const b = c.getBoundingClientRect(), k = out.width / (box.width || out.width)
        g.drawImage(c, (b.left - box.left) * k, (b.top - box.top) * k, b.width * k, b.height * k)
      }
      if (onFrame) await onFrame(out, n, (n + 1) / fps)
      else kept.push(await createImageBitmap(out))
      // What the scene awaits between frames (a promise, a timer that is due) is given its turn.
      await new Promise((done) => setTimeout(done, 0))
    }
    // The last frame lasts 1/fps too, and its sound is the film's.
    clock = zero + (frames + 1) * 1000 / fps
    await hear(frames)
  } finally {
    if (stop) stop()
    window.requestAnimationFrame = real.raf
    window.cancelAnimationFrame = real.caf
    performance.now = real.now
    for (const [, fn] of waiting) real.raf.call(window, fn)
  }
  return kept
}

/**
 * A film of the scene as a WebM file, every frame exactly 1/fps apart: `const film = await recordVideo({ seconds: 5, fps: 60 })`
 * gives a Blob (`saveVideo(film)` downloads it). It needs a browser that can encode video (WebCodecs).
 * WITH SOUND: `recordVideo({ seconds, fps, sound: scene })`, where the scene's sound is stepped (see renderFrames).
 * The sound goes into the file as Opus, beginning on the first frame's first sample and ending with the last
 * frame (`film.audio` is "opus"). A browser that cannot encode Opus gives the film without sound and the sound
 * beside it as a WAV file of the same length, `film.sound` (`film.audio` is "wav"); saveVideo saves both.
 * With no `sound`, or a scene that made none, the film has no sound track (`film.audio` is null).
 */
async function recordVideo({ seconds = 5, fps = 60, bitrate = 0, canvas = null, sound = null, audioBitrate = 160000 } = {}) {
  canvas ||= onlyCanvas()
  if (typeof VideoEncoder !== 'function' || typeof VideoFrame !== 'function') throw new Error('This browser cannot make a video file (it has no VideoEncoder). renderFrames() gives the frames one by one instead')
  // An encoder wants a picture with an even number of pixels each way.
  const w = canvas.width & ~1, h = canvas.height & ~1
  let codec = ''
  for (const c of ['vp09.00.40.08', 'vp8']) {
    try { if ((await VideoEncoder.isConfigSupported({ codec: c, width: w, height: h })).supported) { codec = c; break } } catch (e) { /* not this one */ }
  }
  if (!codec) throw new Error(`This browser cannot encode a WebM video of ${w} by ${h} pixels. renderFrames() gives the frames one by one instead`)
  const chunks = []
  let failed = null
  const encoder = new VideoEncoder({
    output: (chunk) => { const data = new Uint8Array(chunk.byteLength); chunk.copyTo(data); chunks.push({ data, key: chunk.type === 'key', time: Math.round(chunk.timestamp / 1000) }) },
    error: (e) => { failed = e },
  })
  encoder.configure({ codec, width: w, height: h, framerate: fps, bitrate: bitrate || Math.round(w * h * fps * 0.12) })
  const even = Object.assign(document.createElement('canvas'), { width: w, height: h }).getContext('2d')
  const track = soundTrack(audioBitrate)
  const total = Math.round(seconds * fps)
  await renderFrames({ seconds, fps, canvas, sound, onSound: (left, right, rate) => track.add(left, right, rate), onFrame: async (picture, n) => {
    even.drawImage(picture, 0, 0)
    const frame = new VideoFrame(even.canvas, { timestamp: Math.round(n * 1e6 / fps), duration: Math.round(1e6 / fps) })
    encoder.encode(frame, { keyFrame: n % Math.round(fps * 2) === 0 })
    frame.close()
    // The encoder is not given frames faster than it can take them.
    while (encoder.encodeQueueSize > 6) await new Promise((done) => setTimeout(done, 1))
  } })
  await encoder.flush()
  encoder.close()
  if (failed) throw new Error(`The video could not be encoded: ${failed.message}`)
  const heard = await track.end()
  const film = webm(chunks, { codec: codec === 'vp8' ? 'V_VP8' : 'V_VP9', width: w, height: h, fps, frames: total, audio: heard && heard.opus })
  film.codec = codec === 'vp8' ? 'vp8' : 'vp9'
  film.audio = heard ? (heard.opus ? 'opus' : 'wav') : null
  film.samples = heard ? heard.samples : 0
  film.sampleRate = heard ? heard.sampleRate : 0
  if (heard && heard.wav) film.sound = heard.wav
  return film
}

/**
 * A film's sound as it is made: Opus where the browser can encode it (WebCodecs' AudioEncoder, at 48000 samples
 * a second), and otherwise kept as it is, to be handed over as a WAV file. `add(left, right, sampleRate)` takes
 * each stretch; `end()` gives null (there was none), { opus: { packets, head, preSkip, samples } } or { wav }.
 */
function soundTrack(bitrate) {
  let encoder = null, failed = null, rate = 0, samples = 0, fed = 0, begun = false, head = null
  const packets = [], plain = []
  const feed = (left, right) => {
    const data = new Float32Array(left.length * 2)
    data.set(left, 0); data.set(right, left.length)
    const frame = new AudioData({ format: 'f32-planar', sampleRate: rate, numberOfFrames: left.length, numberOfChannels: 2, timestamp: Math.round(fed * 1e6 / rate), data })
    fed += left.length
    encoder.encode(frame)
    frame.close()
  }
  return {
    async add(left, right, sampleRate) {
      if (!left.length) return
      if (!begun) {
        begun = true
        rate = sampleRate
        let can = false
        try { can = rate === 48000 && typeof AudioEncoder === 'function' && typeof AudioData === 'function' && (await AudioEncoder.isConfigSupported({ codec: 'opus', sampleRate: rate, numberOfChannels: 2, bitrate })).supported } catch (e) { can = false }
        if (can) {
          encoder = new AudioEncoder({
            output: (chunk, meta) => {
              if (meta && meta.decoderConfig && meta.decoderConfig.description && !head) head = new Uint8Array(meta.decoderConfig.description.buffer || meta.decoderConfig.description).slice()
              const data = new Uint8Array(chunk.byteLength); chunk.copyTo(data)
              packets.push({ data, time: chunk.timestamp, duration: chunk.duration || 20000 })
            },
            error: (e) => { failed = e },
          })
          encoder.configure({ codec: 'opus', sampleRate: rate, numberOfChannels: 2, bitrate })
        }
      }
      samples += left.length
      // With no encoder the samples are kept as they are, for the WAV file.
      if (!encoder) plain.push([left, right])
      else if (!failed) {
        feed(left, right)
        while (encoder.encodeQueueSize > 24) await new Promise((done) => setTimeout(done, 1))
      }
    },
    async end() {
      if (!begun) return null
      if (encoder && !failed) {
        // A little silence after the end, so the encoder (which runs a few milliseconds behind) gives all of the sound.
        feed(new Float32Array(1920), new Float32Array(1920))
        try { await encoder.flush() } catch (e) { failed = failed || e }
        try { encoder.close() } catch (e) { /* already closed */ }
      }
      if (encoder && !failed && packets.length) {
        // The Opus header says how many samples at the start are the encoder's own run-in, which a player drops.
        const preSkip = head && head.length >= 12 ? head[10] | (head[11] << 8) : 312
        if (!head) { head = new Uint8Array([79, 112, 117, 115, 72, 101, 97, 100, 1, 2, preSkip & 255, preSkip >> 8, 0x80, 0xbb, 0, 0, 0, 0, 0]) }
        return { opus: { packets, head, preSkip, samples }, samples, sampleRate: rate }
      }
      if (failed) console.warn(`visualfx.js: the film's sound could not be encoded (${failed.message || failed}), so it is given beside the film as a WAV file: film.sound`)
      else console.info('visualfx.js: this browser cannot put sound into a WebM file (it has no Opus encoder), so the film\'s sound is given beside it as a WAV file: film.sound')
      // An encoder that failed part-way took the samples with it: the film is then silent, and says so above.
      if (encoder) return null
      return { wav: wav(plain, rate), samples, sampleRate: rate }
    },
  }
}

/** A WAV file (16 bits, two channels) from stretches of samples. */
function wav(parts, rate) {
  const n = parts.reduce((sum, [l]) => sum + l.length, 0)
  const out = new DataView(new ArrayBuffer(44 + n * 4))
  const text = (at, t) => { for (let i = 0; i < t.length; i++) out.setUint8(at + i, t.charCodeAt(i)) }
  text(0, 'RIFF'); out.setUint32(4, 36 + n * 4, true); text(8, 'WAVEfmt '); out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 2, true)
  out.setUint32(24, rate, true); out.setUint32(28, rate * 4, true); out.setUint16(32, 4, true); out.setUint16(34, 16, true); text(36, 'data'); out.setUint32(40, n * 4, true)
  let at = 44
  for (const [l, r] of parts) for (let i = 0; i < l.length; i++) { out.setInt16(at, Math.round(clamp(l[i], -1, 1) * 32767), true); out.setInt16(at + 2, Math.round(clamp(r[i], -1, 1) * 32767), true); at += 4 }
  return new Blob([out.buffer], { type: 'audio/wav' })
}

/**
 * A WebM file from encoded frames: the few parts a player needs, each a name, a length and what is in it.
 * `audio` is Opus packets to go with them ({ packets, head, preSkip, samples }): a second track, whose first
 * sample a player hears is the film's first (the encoder's run-in is declared, and dropped by the player) and
 * whose last is cut where the film ends.
 */
function webm(chunks, { codec, width, height, fps, frames = 0, audio = null }) {
  const bytes = (n, size) => { const out = []; for (let i = size - 1; i >= 0; i--) out.push(Math.floor(n / 2 ** (8 * i)) & 255); return out }
  const whole = (n) => bytes(n, Math.max(1, Math.ceil(Math.log2(n + 1) / 8)))
  const float = (n) => [...new Uint8Array(new Float64Array([n]).buffer).reverse()]
  const text = (t) => [...new TextEncoder().encode(t)]
  // A part: its name, how long it is (eight bytes, the first marking that there are eight) and its content.
  const part = (id, ...content) => {
    const body = content.map((c) => (c instanceof Uint8Array ? c : new Uint8Array(c)))
    const size = body.reduce((n, b) => n + b.length, 0)
    const out = new Uint8Array(id.length + 8 + size)
    out.set(id, 0)
    out.set([1, ...bytes(size, 7)], id.length)
    let at = id.length + 8
    for (const b of body) { out.set(b, at); at += b.length }
    return out
  }
  const head = part([0x1a, 0x45, 0xdf, 0xa3], part([0x42, 0x86], [1]), part([0x42, 0xf7], [1]), part([0x42, 0xf2], [4]), part([0x42, 0xf3], [8]), part([0x42, 0x82], text('webm')), part([0x42, 0x87], [4]), part([0x42, 0x85], [2]))
  const last = chunks.length ? chunks[chunks.length - 1].time : 0
  const length = frames ? frames * 1000 / fps : last + 1000 / fps
  const info = part([0x15, 0x49, 0xa9, 0x66], part([0x2a, 0xd7, 0xb1], whole(1000000)), part([0x4d, 0x80], text('visualfx.js')), part([0x57, 0x41], text('visualfx.js')), part([0x44, 0x89], float(length)))
  const picture = part([0xae], part([0xd7], [1]), part([0x73, 0xc5], [1]), part([0x83], [1]), part([0x86], text(codec)), part([0x23, 0xe3, 0x83], whole(Math.round(1e9 / fps))),
    part([0xe0], part([0xb0], whole(width)), part([0xba], whole(height))))
  // The sound's track: Opus, with its header, how much of its start is run-in (in nanoseconds) and how far back a player must begin to seek cleanly.
  const sounds = audio ? [part([0xae], part([0xd7], [2]), part([0x73, 0xc5], [2]), part([0x83], [2]), part([0x86], text('A_OPUS')), part([0x56, 0xaa], whole(Math.round(audio.preSkip * 1e9 / 48000))), part([0x56, 0xbb], whole(80000000)),
    part([0x63, 0xa2], audio.head), part([0xe1], part([0xb5], float(48000)), part([0x9f], [2])))] : []
  const tracks = part([0x16, 0x54, 0xae, 0x6b], picture, ...sounds)
  // Everything in the order of its time. A sound packet's time is where its samples begin, in milliseconds.
  const blocks = chunks.map((c) => ({ track: 1, time: c.time, key: c.key, data: c.data }))
  if (audio) {
    // Packets past the film's end are left out, and the one that crosses it is cut there.
    const end = audio.preSkip + audio.samples
    let at = 0
    for (const p of audio.packets) {
      const size = Math.round(p.duration * 48 / 1000)
      if (at >= end) break
      blocks.push({ track: 2, time: Math.round(at / 48), key: true, data: p.data, cut: Math.max(0, at + size - end) })
      at += size
    }
    blocks.sort((a, b) => a.time - b.time || a.track - b.track)
  }
  // Frames are kept in groups that each begin with a whole picture: a player can start at any group.
  const clusters = []
  let group = null
  for (const c of blocks) {
    if (!group || (c.track === 1 && c.key) || c.time - group.time > 30000) { group = { time: c.time, blocks: [] }; clusters.push(group) }
    const block = new Uint8Array(4 + c.data.length)
    block.set([0x80 | c.track, ...bytes(c.time - group.time, 2), c.key && !c.cut ? 0x80 : 0], 0)
    block.set(c.data, 4)
    // A packet that is cut short says by how much (nanoseconds), which needs the longer form of a block.
    group.blocks.push(c.cut ? part([0xa0], part([0xa1], block), part([0x75, 0xa2], bytes(Math.round(c.cut * 1e9 / 48000), 4))) : part([0xa3], block))
  }
  const body = [info, tracks, ...clusters.map((g) => part([0x1f, 0x43, 0xb6, 0x75], part([0xe7], whole(g.time)), ...g.blocks))]
  return new Blob([head, part([0x18, 0x53, 0x80, 0x67], ...body)], { type: 'video/webm' })
}

/** Save a film (or any Blob) as a file the browser downloads: saveVideo(film, "my-scene.webm"). A film whose sound is beside it (film.sound) has that saved too, as a WAV file of the same name. */
function saveVideo(film, name = 'scene.webm') {
  const put = (blob, called) => {
    const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: called })
    document.body.append(link)
    link.click()
    link.remove()
    setTimeout(() => URL.revokeObjectURL(link.href), 10000)
  }
  put(film, name)
  if (film && film.sound) put(film.sound, name.replace(/\.[^.]*$/, '') + '.wav')
}

// The same functions with no canvas named: for a page (and a pictures.js scene) with one canvas.
const on = (name) => (...args) => effects()[name](...args)
const kaleidoscope = on('kaleidoscope'), mirror = on('mirror'), pixelate = on('pixelate'), waves = on('waves'), ripple = on('ripple'), wobble = on('wobble')
const swirl = on('swirl'), fisheye = on('fisheye'), bulge = on('fisheye'), tunnel = on('tunnel'), tile = on('tile'), zoomBlur = on('zoomBlur'), spinBlur = on('spinBlur'), rgbSplit = on('rgbSplit')
const hue = on('hue'), saturate = on('saturate'), brighten = on('brighten'), contrast = on('contrast'), invert = on('invert'), posterize = on('posterize'), tint = on('tint'), duotone = on('duotone')
const colourCycle = on('colourCycle'), colorCycle = on('colourCycle'), scanlines = on('scanlines'), crt = on('crt'), glitch = on('glitch'), grain = on('grain'), vignette = on('vignette'), edges = on('edges')
const dots = on('dots'), halftone = on('dots'), letters = on('letters'), plasma = on('plasma'), starfield = on('starfield'), metaballs = on('metaballs'), flow = on('flow')
const blur = on('blur'), glow = on('glow'), bloom = on('glow'), trails = on('trails')
const droste = on('droste'), rotozoom = on('rotozoom'), hexagons = on('hexagons'), glassTiles = on('glassTiles'), frosted = on('frosted'), heatHaze = on('heatHaze'), caustics = on('caustics'), shake = on('shake'), punch = on('punch'), motionBlur = on('motionBlur'), tiltShift = on('tiltShift'), lightRays = on('lightRays'), streaks = on('streaks'), softFocus = on('softFocus'), smear = on('smear'), stutter = on('stutter'), gradientMap = on('gradientMap'), thermal = on('thermal'), nightVision = on('nightVision'), sepia = on('sepia'), threshold = on('threshold'), solarize = on('solarize'), colourBleed = on('colourBleed'), rainbowEdges = on('rainbowEdges'), dither = on('dither'), interlace = on('interlace'), led = on('led'), emboss = on('emboss'), sharpen = on('sharpen'), sketch = on('sketch'), cartoon = on('cartoon'), stainedGlass = on('stainedGlass'), crosshatch = on('crosshatch'), oil = on('oil'), dust = on('dust'), lightLeaks = on('lightLeaks'), rain = on('rain'), snow = on('snow'), bokeh = on('bokeh'), fog = on('fog'), lightning = on('lightning'), warp = on('warp'), voronoi = on('voronoi'), moire = on('moire'), interference = on('interference'), aurora = on('aurora'), fire = on('fire'), clouds = on('clouds'), matrixRain = on('matrixRain'), copperBars = on('copperBars'), checkerFloor = on('checkerFloor'), twister = on('twister'), spectrumBars = on('spectrumBars'), spectrumRing = on('spectrumRing'), waveformRing = on('waveformRing'), beatFlash = on('beatFlash'), bassShake = on('bassShake'), colorBleed = on('colourBleed'), godRays = on('lightRays')
const shader = on('shader'), look = on('look'), clearEffects = on('clearEffects'), listenTo = on('listenTo'), react = on('react'), effectsQuality = on('effectsQuality')
const bass = on('bass'), mids = on('mids'), highs = on('highs'), loudness = on('loudness'), pulse = on('pulse')
const lookNames = () => Object.keys(LOOKS), effectNames = () => [...NAMES], paletteNames = () => Object.keys(PALETTES)

export {
  effects, kaleidoscope, mirror, pixelate, waves, ripple, wobble, swirl, fisheye, bulge, tunnel, tile, zoomBlur, spinBlur, rgbSplit,
  hue, saturate, brighten, contrast, invert, posterize, tint, duotone, colourCycle, colorCycle, scanlines, crt, glitch, grain, vignette, edges,
  dots, halftone, letters, plasma, starfield, metaballs, flow, blur, glow, bloom, trails,
  droste, rotozoom, hexagons, glassTiles, frosted, heatHaze, caustics, shake, punch, motionBlur, tiltShift, lightRays, streaks, softFocus, smear, stutter, gradientMap, thermal, nightVision, sepia, threshold, solarize, colourBleed, rainbowEdges, dither, interlace, led, emboss, sharpen, sketch, cartoon, stainedGlass, crosshatch, oil, dust, lightLeaks, rain, snow, bokeh, fog, lightning, warp, voronoi, moire, interference, aurora, fire, clouds, matrixRain, copperBars, checkerFloor, twister, spectrumBars, spectrumRing, waveformRing, beatFlash, bassShake, colorBleed, godRays,
  shader, look, clearEffects, listenTo, react, effectsQuality, bass, mids, highs, loudness, pulse, lookNames, effectNames, paletteNames,
  renderFrames, recordVideo, saveVideo, version,
}
