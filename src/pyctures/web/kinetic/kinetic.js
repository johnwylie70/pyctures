/**
 * kinetic.js: moving text for videos. Ten effects (a word slam, a wave and a bounce of letters, a typewriter,
 * a glitch, a wipe, a pop on words that matter, a ticker, a counter and a highlighter), each a plain function
 * of the text, a style and the time, that draws into the scene's 2D canvas. It is a part of its own beside
 * pictures.js, fetched only for a scene that names one of KINETIC_NAMES (pictures.js); no other scene loads it.
 *
 *   wordSlam("Learn to code", { start: 0, duration: 1.2 })
 *
 * EVERY EFFECT takes (text, options) and options are all optional:
 *   start     seconds into the scene when it begins (0)
 *   duration  seconds the movement takes; afterwards the text stays as it ended (`hold: false` takes it away)
 *   t         the time to draw at. Left out, it is the scene's own clock (`kineticTime()`), which a recorded scene
 *             steps a frame at a time; so an effect is a function of t only: no wall clock, and every "random"
 *             movement comes from a hash of the letter's place, the time step and `seed`, never from Math.random
 *   x, y      where the middle of the text goes, as a share of the frame (0 left or top, 1 right or bottom); the
 *             default is the middle. The text is then moved to sit inside the safe area
 *   size      "hook", "title", "body" or "caption" (houseStyle.scale), or a number: up to 1 a share of the frame's
 *             shorter side, above 1 pixels. Never below houseStyle.minimum of the frame's height. A text that does
 *             not fit is wrapped onto more lines, then made smaller, but not below that minimum
 *   style     "playful", "techy" or "calm" (houseStyle.voices), or an object that changes one of them
 *   colour    the text's colour (the voice's), `accent` the colour of what is emphasised
 *   beat      a number of beats, or a music object with a `.beat`: the text pulses on each beat. Without it, nothing
 *   safe      { top, bottom, side } shares of the frame, over the shape's own (houseStyle.safe)
 *   seed      changes the "random" movement (1)
 * A word between asterisks, *like this*, is the emphasised one: coloured, and what scalePop and highlightSweep
 * single out. Each effect returns { progress (0 to 1), box: {x, y, w, h}, size (pixels) }, or null before it starts.
 */
// --- THE HOUSE STYLE (a scene is given it as `houseStyle`; Python's house_style is written from it by Pyctures' scripts/sync_libraries.py)
/**
 * THE HOUSE STYLE: the look every video of ours shares, so it is not decided again for each one.
 * A scene is given it as `houseStyle` (Python: `house_style`). Its numbers are a starting point to be tuned by eye;
 * change them here and every scene that reads them follows.
 *
 *   palette  the colours: `ink` is the dark backdrop, `paper` the text on it, and four accents
 *   fonts    `display` for headlines, `mono` for code and the techy voice
 *   scale    text sizes as a share of the frame's SHORTER side (1080 in both 1920x1080 and 1080x1920), so a
 *            hook is the same size in a wide video and in a tall one and only the wrapping differs
 *   minimum  the least a text may be, as a share of the frame's HEIGHT: readable on a phone. A size below
 *            it is raised to it, and a long text is wrapped onto more lines rather than made smaller than it
 *   safe     the edges kept clear of text, as a share of the frame, by shape: the tall shape leaves room
 *            for the buttons and captions that phone apps lay over a video (top 14 percent, bottom 18)
 *   voices   three ways to set a text: playful, techy and calm
 */
export const houseStyle = {
  palette: {
    ink: '#0b1020', paper: '#f8fafc', dim: '#94a3b8',
    blue: '#3b82f6', cyan: '#22d3ee', pink: '#f472b6', yellow: '#facc15', green: '#34d399',
  },
  fonts: {
    display: '"Avenir Next", "Arial Rounded MT Bold", "Trebuchet MS", system-ui, -apple-system, sans-serif',
    mono: 'ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
  },
  scale: { hook: 0.13, title: 0.085, body: 0.05, caption: 0.04 },
  minimum: 0.03,
  safe: {
    wide: { top: 0.05, bottom: 0.05, side: 0.05 },
    tall: { top: 0.14, bottom: 0.18, side: 0.06 },
    feed: { top: 0.08, bottom: 0.10, side: 0.06 },
  },
  voices: {
    playful: { font: '"Avenir Next", "Arial Rounded MT Bold", "Trebuchet MS", system-ui, sans-serif', weight: 900, colour: '#f8fafc', accent: '#facc15', second: '#f472b6', spring: 1 },
    techy: { font: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace', weight: 700, colour: '#e0f2fe', accent: '#22d3ee', second: '#3b82f6', spring: 0.4 },
    calm: { font: 'system-ui, -apple-system, "Segoe UI", sans-serif', weight: 500, colour: '#e2e8f0', accent: '#7dd3fc', second: '#94a3b8', spring: 0 },
  },
}

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x))
const mix = (a, b, k) => a + (b - a) * k
const E = {
  out: (x) => 1 - (1 - x) ** 3,
  inOut: (x) => (x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2),
  back: (x) => { const c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2 },
  expo: (x) => (x >= 1 ? 1 : 1 - 2 ** (-10 * x)),
  bounce: (x) => {
    const n = 7.5625, d = 2.75
    if (x < 1 / d) return n * x * x
    if (x < 2 / d) return n * (x -= 1.5 / d) * x + 0.75
    if (x < 2.5 / d) return n * (x -= 2.25 / d) * x + 0.9375
    return n * (x -= 2.625 / d) * x + 0.984375
  },
}
/** A number from 0 up to 1 that is always the same for the same a and b. */
export function hash(a, b = 0) {
  let h = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263)) | 0
  h = Math.imul(h ^ (h >>> 13), 1274126177)
  h ^= h >>> 16
  return (h >>> 0) / 4294967296
}
/** A random function that gives the same numbers for the same seed (Python: seeded_random). */
export function seededRandom(seed = 1) {
  let a = seed | 0
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// --- the frame: its size, its safe area, the voice and the size of the text
function shapeOf(W, H) {
  const r = H / W
  return r >= 1.6 ? 'tall' : r >= 1.15 ? 'feed' : 'wide'
}
/** The safe area in pixels: { left, top, right, bottom, width, height }. */
export function safeArea(W, H, over = {}) {
  const m = { ...houseStyle.safe[shapeOf(W, H)], ...over }
  const left = W * m.side, right = W * (1 - m.side), top = H * m.top, bottom = H * (1 - m.bottom)
  return { left, top, right, bottom, width: right - left, height: bottom - top }
}
function voiceOf(style) {
  const voices = houseStyle.voices
  if (style && typeof style === 'object') return { ...voices[style.voice ?? 'playful'], ...style }
  const v = voices[style ?? 'playful']
  if (!v) throw new Error(`There is no style "${style}": use ${Object.keys(voices).map((n) => `"${n}"`).join(', ')}`)
  return v
}
function sizeOf(o, W, H, fallback) {
  let s = o.size ?? fallback
  const short = Math.min(W, H)
  if (typeof s === 'string') {
    if (!(s in houseStyle.scale)) throw new Error(`There is no size "${s}": use ${Object.keys(houseStyle.scale).map((n) => `"${n}"`).join(', ')} or a number`)
    s = houseStyle.scale[s]
  }
  const px = s > 1 ? s : s * short
  const min = H * houseStyle.minimum
  return { target: Math.max(px, min), min }
}
const fontOf = (v, px) => `${v.weight} ${px}px ${v.font}`

// --- the words: "a *b* c" -> a, b (emphasised), c
function parse(text) {
  const words = []
  let on = false
  for (const token of String(text).split(/\s+/).filter(Boolean)) {
    if (token.startsWith('*')) on = true
    const em = on
    if (/\*[^\w]*$/.test(token)) on = false
    const clean = token.replace(/\*/g, '')
    if (clean) words.push({ text: clean, em })
  }
  return words
}

/** The lines a text makes at a size: each word with its place from the block's top left, and its letters'. */
function layout(ctx, words, px, v, maxW, emScale) {
  const lh = px * 1.18
  ctx.font = fontOf(v, px)
  const space = ctx.measureText(' ').width
  const lines = []
  let line = null
  const made = words.map((w) => {
    const wpx = w.em ? px * emScale : px
    ctx.font = fontOf(v, wpx)
    const letters = [...w.text].map((ch, i) => ({ ch, x: ctx.measureText(w.text.slice(0, i)).width, w: ctx.measureText(ch).width }))
    const width = ctx.measureText(w.text).width
    if (!line || (line.words.length && line.w + space + width > maxW)) lines.push((line = { words: [], w: 0 }))
    const word = { ...w, px: wpx, w: width, x: line.words.length ? line.w + space : 0, line: lines.length - 1, letters }
    line.w = word.x + width
    line.words.push(word)
    return word
  })
  const w = Math.max(...lines.map((l) => l.w))
  for (const l of lines) for (const word of l.words) { word.x += (w - l.w) / 2; word.cy = word.line * lh + lh / 2 }
  return { words: made, lines, w, h: lines.length * lh, lh }
}

/** The text, laid out inside the safe area. grow: how much bigger than laid out a part of it gets; lift: room above
 *  and below for movement, and side: room at each side, both in letter heights. */
function prepare(host, text, o, { grow = 1, lift = 0, side = 0, emScale = 1, size = 'hook' } = {}) {
  const { ctx } = host
  const [W, H] = host.size()
  const safe = safeArea(W, H, o.safe)
  const v = voiceOf(o.style)
  const { target, min } = sizeOf(o, W, H, size)
  grow *= 1.06
  const upper = v.upper ? String(text).toUpperCase() : String(text)
  const key = [upper, W, H, target, JSON.stringify(v), JSON.stringify(o.safe), grow, lift, side, emScale].join('|')
  let fit = host.fits.get(key)
  if (!fit) {
    const words = parse(upper)
    let px = target
    for (;;) {
      const f = layout(ctx, words, px, v, safe.width / grow - 2 * side * px, emScale)
      fit = { px, ...f }
      if (px <= min * 1.001 || (f.w * grow + 2 * side * px <= safe.width + 0.5 && f.h * grow + 2 * lift * px <= safe.height)) break
      px = Math.max(min, px * 0.94)
    }
    if (host.fits.size > 40) host.fits.clear()
    host.fits.set(key, fit)
  }
  const padX = fit.w * grow / 2 + side * fit.px, padY = fit.h * grow / 2 + lift * fit.px
  const place = (v0, a, b) => Math.min(b, Math.max(a, v0))
  const cx = place((o.x ?? 0.5) * W, safe.left + padX, safe.right - padX)
  const cy = place((o.y ?? 0.5) * H, safe.top + padY, safe.bottom - padY)
  const colour = o.colour ?? o.color ?? v.colour
  const accent = o.accent ?? v.accent
  return { ...fit, host, ctx, W, H, safe, v, colour, accent, cx, cy, x0: cx - fit.w / 2, y0: cy - fit.h / 2 }
}
const boxOf = (L) => ({ x: L.x0, y: L.y0, w: L.w, h: L.h })

/** Where an effect is in its time. */
function timeline(host, o, duration) {
  const now = o.t ?? host.time()
  const dur = Math.max(1e-6, o.duration ?? duration)
  const local = now - (o.start ?? 0)
  return { now, local, dur, u: clamp(local / dur), live: local >= 0 && (o.hold !== false || local <= dur) }
}
/** 1 on a beat, falling to 0 before the next. 0 with no beat given. */
function pulse(o) {
  const beat = typeof o.beat === 'number' ? o.beat : o.beat?.beat
  if (!(beat >= 0)) return 0
  return (1 - (beat - Math.floor(beat))) ** 3
}
/** Run an effect's drawing on the canvas, pulsing about the text's middle when there is a beat. */
function draw(L, o, fn) {
  const { ctx } = L
  ctx.save()
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'left'
  const p = 1 + (o.pulse ?? 0.06) * pulse(o)
  if (p !== 1) { ctx.translate(L.cx, L.cy); ctx.scale(p, p); ctx.translate(-L.cx, -L.cy) }
  try { fn() } finally { ctx.restore() }
}
/** A piece of text with its left and middle at x, y, scaled and turned about (ox, oy). */
function put(L, str, x, y, px, { ox = x, oy = y, s = 1, rot = 0, a = 1, colour = L.colour } = {}) {
  if (a <= 0 || !str) return
  const { ctx } = L
  ctx.save()
  ctx.globalAlpha *= clamp(a)
  ctx.fillStyle = colour
  ctx.font = fontOf(L.v, px)
  ctx.translate(ox, oy)
  if (rot) ctx.rotate(rot)
  if (s !== 1) ctx.scale(s, s)
  ctx.fillText(str, x - ox, y - oy)
  ctx.restore()
}
const spot = (L, w) => ({ x: L.x0 + w.x, y: L.y0 + w.cy })
const hue = (L, w) => (w.em ? L.accent : L.colour)
/** All the words in place, as they end. */
function still(L, { colour, dx = 0, dy = 0, a = 1 } = {}) {
  for (const w of L.words) { const p = spot(L, w); put(L, w.text, p.x + dx, p.y + dy, w.px, { colour: colour ?? hue(L, w), a }) }
}

// --- the effects
function wordSlam(host, text, o = {}) {
  const L = prepare(host, text, o, { grow: 1 + 0.35 * voiceOf(o.style).spring, lift: 0.1, side: 0.1 })
  const T = timeline(host, o, Math.max(1.2, 0.45 * L.words.length))
  if (!T.live) return null
  const n = L.words.length, spring = voiceOf(o.style).spring
  const step = n > 1 ? (T.dur - 0.3) / (n - 1) : 0
  draw(L, o, () => {
    // The word that last landed shakes the whole text for a moment.
    const last = Math.max(0, Math.min(n - 1, Math.floor(step > 0 ? T.local / step : 0)))
    const since = T.local - last * step
    const shake = since >= 0 && since < 0.3 ? (1 - since / 0.3) ** 2 * L.px * 0.04 * spring : 0
    const tick = Math.floor(T.local * 60)
    const sx = (hash(tick, 1 + (o.seed ?? 1)) - 0.5) * 2 * shake, sy = (hash(tick, 7 + (o.seed ?? 1)) - 0.5) * 2 * shake
    L.words.forEach((w, i) => {
      const lt = (T.local - i * step) / 0.3
      if (lt < 0) return
      const k = E.out(clamp(lt))
      const p = spot(L, w)
      put(L, w.text, p.x + sx, p.y + sy, w.px, { ox: p.x + w.w / 2, oy: p.y, s: 1 + (0.9 * spring + 0.1) * (1 - k), a: clamp(lt * 4), colour: hue(L, w) })
    })
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

function letterWave(host, text, o = {}) {
  const L = prepare(host, text, o, { grow: 1.04, lift: 0.3 })
  const T = timeline(host, o, 1.2)
  if (!T.live) return null
  const total = L.words.reduce((n, w) => n + w.letters.length, 0)
  const stagger = (T.dur * 0.6) / Math.max(1, total)
  draw(L, o, () => {
    let g = 0
    for (const w of L.words) {
      const p = spot(L, w)
      w.letters.forEach((l, i) => {
        const a = clamp((T.local - g * stagger) / 0.25)
        const dy = Math.sin(T.now * 5 * (o.speed ?? 1) - g * 0.55) * L.px * 0.14 * E.out(a)
        put(L, l.ch, p.x + l.x, p.y + dy, w.px, { a, colour: hue(L, w) })
        g++
      })
    }
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

function letterBounce(host, text, o = {}) {
  const L = prepare(host, text, o, { grow: 1.02, lift: 1.1 })
  const T = timeline(host, o, 1.6)
  if (!T.live) return null
  const total = L.words.reduce((n, w) => n + w.letters.length, 0)
  const stagger = (T.dur * 0.5) / Math.max(1, total)
  const fall = 0.7
  draw(L, o, () => {
    let g = 0
    for (const w of L.words) {
      const p = spot(L, w)
      for (const l of w.letters) {
        const lt = (T.local - g * stagger) / fall
        if (lt >= 0) {
          const e = E.bounce(clamp(lt))
          put(L, l.ch, p.x + l.x, p.y - (1 - e) * L.px * 1.1, w.px, { a: clamp(lt * 8), colour: hue(L, w) })
        }
        g++
      }
    }
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

function typewriterText(host, text, o = {}) {
  const L = prepare(host, text, o, { side: 0.4 })
  const T = timeline(host, o, Math.max(1.2, 0.07 * String(text).length))
  if (!T.live) return null
  // Each letter takes a little longer or shorter than the next, and a comma or a full stop is followed by a pause.
  const seed = o.seed ?? 1
  const times = []
  let sum = 0, g = 0
  for (const w of L.words) {
    for (const l of w.letters) {
      sum += 0.6 + 0.8 * hash(g++, seed) + (/[,.;:!?]/.test(l.ch) ? 3 : 0)
      times.push(sum)
    }
    sum += 0.8
  }
  const reach = T.local / T.dur * sum
  draw(L, o, () => {
    let seen = 0, at = null
    let g2 = 0
    for (const w of L.words) {
      const p = spot(L, w)
      let shown = 0
      for (const l of w.letters) { if (times[g2++] <= reach) { shown++; seen++ } }
      if (shown) {
        put(L, w.text.slice(0, shown), p.x, p.y, w.px, { colour: hue(L, w) })
        const last = w.letters[shown - 1]
        at = { x: p.x + last.x + last.w, y: p.y, px: w.px }
      }
    }
    const first = spot(L, L.words[0])
    at ??= { x: first.x, y: first.y, px: L.px }
    // The cursor stays on while it types, then blinks twice a second.
    if (T.local < T.dur + 0.2 || Math.floor(T.now * 2) % 2 === 0) {
      L.ctx.fillStyle = L.accent
      L.ctx.fillRect(at.x + at.px * 0.06, at.y - at.px * 0.5, at.px * 0.12, at.px * 1.0)
    }
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

function glitchText(host, text, o = {}) {
  const L = prepare(host, text, o, { grow: 1.04, side: 0.35, lift: 0.1 })
  const T = timeline(host, o, 1.2)
  if (!T.live) return null
  const seed = o.seed ?? 1
  // Strong as it arrives, then a quick burst now and then, eight steps a second.
  const step = Math.floor(T.now * 8)
  const burst = hash(step, seed) > 0.82 ? 0.4 + 0.6 * hash(step, seed + 5) : 0
  const amount = clamp(((1 - T.u) ** 2 + burst) * (o.amount ?? 1))
  const { ctx } = L
  draw(L, o, () => {
    const off = L.px * 0.07 * (0.25 + amount)
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    still(L, { colour: 'rgb(255,30,90)', dx: -off, a: 0.85 })
    still(L, { colour: 'rgb(0,230,255)', dx: off, a: 0.85 })
    ctx.restore()
    if (amount < 0.08) return still(L)
    // Slices of the text jump sideways.
    const bands = 7
    for (let j = 0; j < bands; j++) {
      const jump = hash(step * 31 + j, seed + 11) < 0.55 ? (hash(step * 17 + j, seed + 3) - 0.5) * L.px * 0.7 * amount : 0
      ctx.save()
      ctx.beginPath()
      ctx.rect(0, L.y0 - L.px * 0.1 + (L.h + L.px * 0.2) * j / bands, L.W, (L.h + L.px * 0.2) / bands + 1)
      ctx.clip()
      still(L, { dx: jump })
      ctx.restore()
    }
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

function maskReveal(host, text, o = {}) {
  // The text slides half a letter as it is uncovered, so the box it is uncovered in reaches that far on the side it comes from.
  const L = prepare(host, text, o, { grow: 1.0, side: 0.6, lift: 0.6 })
  const T = timeline(host, o, 0.9)
  if (!T.live) return null
  const dir = o.direction ?? 'right'
  const e = E.inOut(T.u)
  const { ctx } = L
  const horizontal = dir === 'right' || dir === 'left'
  const forward = dir === 'right' || dir === 'down'
  // Along the wipe: from before the text's first edge (room for the slide and a letter's overhang) to past its last. Across it: a share of the size above and below.
  const from = horizontal ? L.x0 : L.y0, length = horizontal ? L.w : L.h
  const near = L.px * 0.2, far = L.px * 0.7
  const lo = from - (forward ? far : near), hi = from + length + (forward ? near : far)
  const run = (hi - lo) * e
  const across0 = (horizontal ? L.y0 : L.x0) - L.px * 0.25, acrossLen = (horizontal ? L.h : L.w) + L.px * 0.5
  const edge = forward ? lo + run : hi - run
  const slide = (1 - e) * L.px * 0.5 * (forward ? -1 : 1)
  const [rx, ry, rw, rh] = horizontal
    ? [forward ? lo : edge, across0, run, acrossLen]
    : [across0, forward ? lo : edge, acrossLen, run]
  draw(L, o, () => {
    ctx.save()
    ctx.beginPath()
    ctx.rect(rx, ry, rw, rh)
    ctx.clip()
    still(L, horizontal ? { dx: slide } : { dy: slide })
    ctx.restore()
    // A bar rides just ahead of the edge of the wipe, so it never covers the letters that are uncovered.
    if (T.u > 0 && T.u < 1) {
      ctx.fillStyle = L.accent
      const t = L.px * 0.08, at = forward ? edge : edge - t
      if (horizontal) ctx.fillRect(at, across0, t, acrossLen)
      else ctx.fillRect(across0, at, acrossLen, t)
    }
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

function scalePop(host, text, o = {}) {
  const emScale = 1.12
  const L = prepare(host, text, o, { grow: 1.22, lift: 0.15, side: 0.15, emScale })
  const T = timeline(host, o, Math.max(1.2, 0.4 * L.words.length))
  if (!T.live) return null
  const n = L.words.length
  const step = n > 1 ? (T.dur - 0.4) / (n - 1) : 0
  const spring = voiceOf(o.style).spring
  draw(L, o, () => {
    L.words.forEach((w, i) => {
      const lt = (T.local - i * step) / 0.4
      if (lt < 0) return
      const k = clamp(lt)
      const p = spot(L, w)
      // A word that matters swells past its size and settles; the others rise into place.
      const s = w.em ? 1 + (0.08 + 0.12 * spring) * Math.sin(Math.PI * E.out(k)) * (1 - 0.3 * k) : 1
      const rise = w.em ? 0 : (1 - E.out(k)) * L.px * 0.25
      put(L, w.text, p.x, p.y + rise, w.px, { ox: p.x + w.w / 2, oy: p.y, s, a: clamp(lt * 3), colour: hue(L, w) })
    })
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

function tickerText(host, text, o = {}) {
  const { ctx } = host
  const [W, H] = host.size()
  const safe = safeArea(W, H, o.safe)
  const v = voiceOf(o.style)
  const { target } = sizeOf(o, W, H, 'body')
  const colour = o.colour ?? o.color ?? v.colour, accent = o.accent ?? v.accent
  const T = timeline(host, { ...o, hold: true }, 0.4)
  if (!T.live) return null
  const L = { ctx, v, colour, accent, host }
  const cy = clamp((o.y ?? 0.5) * H, safe.top + target, safe.bottom - target)
  const unit = String(text).replace(/\*/g, '') + '     •     '
  ctx.save()
  ctx.font = fontOf(v, target)
  const cycle = ctx.measureText(unit).width
  const copies = Math.ceil(safe.width / cycle) + 1
  const run = unit.repeat(1)
  ctx.beginPath()
  ctx.rect(safe.left, cy - target, safe.width, 2 * target)
  ctx.clip()
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'left'
  // The strip the text runs along.
  ctx.globalAlpha = clamp(T.local / 0.4)
  ctx.fillStyle = accent
  ctx.globalAlpha *= 0.16 + 0.1 * pulse(o)
  ctx.fillRect(safe.left, cy - target * 0.75, safe.width, target * 1.5)
  ctx.globalAlpha = clamp(T.local / 0.4)
  ctx.fillRect(safe.left, cy - target * 0.75, safe.width, Math.max(2, target * 0.05))
  ctx.fillRect(safe.left, cy + target * 0.75 - Math.max(2, target * 0.05), safe.width, Math.max(2, target * 0.05))
  const shift = (T.local * target * 4 * (o.speed ?? 1)) % cycle
  for (let k = 0; k < copies + 1; k++) put(L, run, safe.left - shift + k * cycle, cy, target, { colour })
  ctx.restore()
  return { progress: 1, box: { x: safe.left, y: cy - target * 0.75, w: safe.width, h: target * 1.5 }, size: target }
}

function countUp(host, text, o = {}) {
  const { ctx } = host
  const [W, H] = host.size()
  const safe = safeArea(W, H, o.safe)
  const v = voiceOf(o.style)
  const { target, min } = sizeOf(o, W, H, 'hook')
  const T = timeline(host, o, 1.8)
  if (!T.live) return null
  const str = String(text)
  const m = str.match(/-?[\d,]*\.?\d+/)
  const from = o.from ?? 0
  const final = m ? Number(m[0].replace(/,/g, '')) : 0
  const decimals = m && m[0].includes('.') ? m[0].split('.')[1].length : 0
  const grouped = !!m && m[0].includes(',')
  const before = m ? str.slice(0, m.index) : str, after = m ? str.slice(m.index + m[0].length) : ''
  const show = (n) => before + (grouped ? n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : n.toFixed(decimals)) + after
  const now = mix(from, final, E.expo(T.u))
  // Digits take the width of the widest one, so the number does not shiver as it counts.
  const measure = (px, s) => {
    ctx.font = fontOf(v, px)
    const digit = ctx.measureText('0').width
    return [...s].map((c) => (/\d/.test(c) ? digit : ctx.measureText(c).width))
  }
  const total = (ws) => ws.reduce((a, b) => a + b, 0)
  const middle = (s) => s.slice(before.length, s.length - after.length)
  const sizes = (px) => [before, middle(show(final)), after].map((p) => total(measure(px, p)))
  let px = target
  let [wb, wn, wa] = sizes(px)
  while (px > min * 1.001 && (wb + wn + wa) * 1.15 > safe.width) { px = Math.max(min, px * 0.94); [wb, wn, wa] = sizes(px) }
  const width = wb + wn + wa
  const cx = clamp((o.x ?? 0.5) * W, safe.left + width * 0.575, safe.right - width * 0.575)
  const cy = clamp((o.y ?? 0.5) * H, safe.top + px, safe.bottom - px)
  const L = { ctx, v, colour: o.colour ?? o.color ?? v.colour, accent: o.accent ?? v.accent, host }
  const done = clamp((T.local - T.dur) / 0.35)
  const s = (1 + 0.1 * Math.sin(Math.PI * done)) * (1 + (o.pulse ?? 0.06) * pulse(o))
  ctx.save()
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'left'
  ctx.translate(cx, cy)
  ctx.scale(s, s)
  const colour = T.u >= 1 ? L.accent : L.colour, a = clamp(T.local / 0.15)
  const cur = middle(show(now))
  // The words before and after stay where they are; the number is held by its right-hand end.
  let x = -width / 2
  put(L, before, x, 0, px, { colour: L.colour, a })
  x += wb + (wn - total(measure(px, cur)))
  for (const c of cur) {
    put(L, c, x, 0, px, { colour, a })
    x += measure(px, c)[0]
  }
  put(L, after, -width / 2 + wb + wn, 0, px, { colour: L.colour, a })
  ctx.restore()
  return { progress: T.u, box: { x: cx - width / 2, y: cy - px * 0.6, w: width, h: px * 1.2 }, size: px, value: now }
}

function highlightSweep(host, text, o = {}) {
  const L = prepare(host, text, o, { grow: 1.0, side: 0.15, lift: 0.1 })
  const T = timeline(host, o, 1.4)
  if (!T.live) return null
  const spans = L.words.some((w) => w.em)
    ? L.words.filter((w) => w.em).map((w) => ({ x: L.x0 + w.x, y: L.y0 + w.cy, w: w.w }))
    : L.lines.map((l, i) => ({ x: L.x0 + (L.w - l.w) / 2, y: L.y0 + i * L.lh + L.lh / 2, w: l.w }))
  const lead = 0.25
  const step = spans.length > 1 ? (T.dur - lead - 0.4) / (spans.length - 1) : 0
  const { ctx } = L
  const pad = L.px * 0.12
  const bars = spans.map((s, i) => {
    const k = E.inOut(clamp((T.local - lead - i * step) / 0.4))
    return { x: s.x - pad, y: s.y - L.lh * 0.5 + L.px * 0.06, w: (s.w + 2 * pad) * k, h: L.lh * 0.9 }
  })
  draw(L, o, () => {
    ctx.fillStyle = L.accent
    for (const b of bars) if (b.w > 0) ctx.fillRect(b.x, b.y, b.w, b.h)
    const a = clamp(T.local / 0.2)
    still(L, { colour: L.colour, a })
    // Where the bar is, the text is dark.
    for (const b of bars) {
      if (b.w <= 0) continue
      ctx.save()
      ctx.beginPath()
      ctx.rect(b.x, b.y, b.w, b.h)
      ctx.clip()
      still(L, { colour: houseStyle.palette.ink })
      ctx.restore()
    }
  })
  return { progress: T.u, box: boxOf(L), size: L.px }
}

const EFFECTS = { wordSlam, letterWave, letterBounce, typewriterText, glitchText, maskReveal, scalePop, tickerText, countUp, highlightSweep }
/** The effects by the names `kineticText` takes: "slam", "wave", "bounce", "type", "glitch", "reveal", "pop", "ticker", "count" and "highlight". */
const KINDS = { slam: 'wordSlam', wave: 'letterWave', bounce: 'letterBounce', type: 'typewriterText', typewriter: 'typewriterText', glitch: 'glitchText', reveal: 'maskReveal', wipe: 'maskReveal', pop: 'scalePop', ticker: 'tickerText', count: 'countUp', counter: 'countUp', highlight: 'highlightSweep' }

/**
 * The scene's kinetic text. `host`: { ctx, size() -> [width, height], stepped? }. The scene's clock is kept here and
 * moved on by `advance(dt)` after each frame, so a scene begins at 0 and a recorded one (a frame at a time) is
 * exact. Returns the names a scene is given, and `advance` and `close` for the host.
 */
export function keep(host) {
  if (!host.ctx) throw new Error('Kinetic text is drawn on the 2D canvas: a 3D scene has none')
  let clock = 0, held = false
  const h = { ctx: host.ctx, size: host.size, fits: new Map(), time: () => clock }
  const names = {}
  for (const [name, fn] of Object.entries(EFFECTS)) names[name] = (text, o = {}) => fn(h, text, o ?? {})
  names.kineticText = (kind, text, o = {}) => {
    const name = EFFECTS[kind] ? kind : KINDS[kind]
    if (!name) throw new Error(`There is no kinetic effect "${kind}": use ${Object.keys(KINDS).map((n) => `"${n}"`).join(', ')}`)
    return names[name](text, o)
  }
  /** The scene's seconds. `kineticTime(5)` sets them, and `kineticTime(5, { hold: true })` stops them there until it is told otherwise. */
  names.kineticTime = (seconds, options = {}) => {
    if (seconds != null) { clock = Number(seconds); held = !!options.hold }
    return clock
  }
  names.kineticSafe = (options = {}) => { const [W, H] = host.size(); return safeArea(W, H, options.safe ?? options) }
  names.kineticEffects = () => Object.keys(KINDS)
  names.houseStyle = houseStyle
  names.seededRandom = seededRandom
  return {
    names,
    advance(dt) { if (!held) clock += dt },
    close() {},
  }
}
export const version = '0.1.0'
