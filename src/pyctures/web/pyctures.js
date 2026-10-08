/**
 * Pyctures, the browser half.
 *
 * One file, used three ways:
 *   - `pyctures run`    the page talks to your own Python over a WebSocket
 *   - `pyctures build`  the page runs Python itself, with Pyodide, in a Web
 *                       Worker (a folder, or one self-contained .html file)
 *   - on any web page   `<div data-pyctures-src="scene.py"></div>` plus
 *                       `<script type="module" src=".../pyctures.js"></script>`
 *
 * THE RENDERER keeps a handle table (number -> JavaScript value), replays the
 * commands the Python half (`pyctures/__init__.py`) records, answers reads, and
 * reports input. Fixed handles (they must match the Python half): 1 window,
 * 2 canvas, 3 THREE, 4 the 2D context (made on first use), 5 addons.
 *
 * THE PAGE'S MAIN THREAD only draws: Python runs in your own Python (`run`) or
 * in a worker (`build`), so a slow frame, Python's garbage collection or a
 * stuck loop never holds up drawing or input.
 *
 * THE HOST LOOP owns requestAnimationFrame. Each refresh, if Python is free and
 * fewer than two frames are waiting to be shown, it asks Python for the next
 * frame (events and read answers in, commands out). The game's clock advances
 * by one refresh period per frame, so motion is even however unevenly the
 * frames were produced. The renderer shows one frame per refresh, from a short
 * queue.
 *
 * A scene starts when it first scrolls into view, and pauses while it is out
 * of view or the tab is hidden, so a page with several scenes stays light.
 *
 * IMAGES BY RELATIVE PATH (`load_image("textures/brick.png")`, a texture) are
 * relative to the scene's file. Before a frame is replayed, a string in its
 * commands that names one is pointed at the packed copy when the page carries
 * it (a single-file build), or at the file beside the scene otherwise.
 *
 * Author: John Wylie. MIT licence.
 */

const BASE = new URL('./', import.meta.url)
export const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.29.4/full/'
const STUCK_MS = 3000
const MEASURE_KEY = 'pyctures:measure'

// ---------------------------------------------------------------- renderer

const KEEP_STATE = ['fillStyle', 'strokeStyle', 'lineWidth', 'lineCap', 'lineJoin', 'miterLimit', 'font', 'textAlign', 'textBaseline', 'globalAlpha', 'globalCompositeOperation', 'shadowBlur', 'shadowColor', 'shadowOffsetX', 'shadowOffsetY', 'imageSmoothingEnabled']
const camelCache = Object.create(null)

// fill_rect -> fillRect, but only when the snake name is not itself real.
function prop(obj, name) {
  if (obj != null && !(name in Object(obj)) && name.indexOf('_') > 0) {
    const c = camelCache[name] || (camelCache[name] = name.replace(/_([a-z0-9])/g, (_, ch) => ch.toUpperCase()))
    if (c in Object(obj)) return c
  }
  return name
}

// ---------------------------------------------------------------- images by relative path

/** A relative path to an image: no scheme, not absolute, an image extension (pages.IMAGE_PATH). */
const IMAGE_PATH = /^(?![a-z][a-z0-9+.-]*:|\/)(?:\.\/)?[^\s"'<>?#]+\.(png|jpe?g|gif|webp|svg|bmp|avif)$/i
export function isRelativeImagePath(s) { return typeof s === 'string' && s.length < 300 && IMAGE_PATH.test(s) }
export const IMAGE_TYPES = {
  png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', gif: 'image/gif',
  webp: 'image/webp', svg: 'image/svg+xml', bmp: 'image/bmp', avif: 'image/avif',
}
/** The key an image is packed under: as written, without a leading "./". */
const packedKey = (s) => s.replace(/^(\.\/)+/, '')

/**
 * Where a scene's relative image paths point: `packed` ({path: base64}, a
 * single-file page's images) first, then the file beside the scene. Returns
 * null when nothing needs changing (no packed images, and the scene is in the
 * page's own folder), so most scenes pay nothing.
 */
export function imageResolver(src, packed) {
  const keys = packed ? Object.keys(packed).filter(isRelativeImagePath) : []
  const scene = new URL(src || '', location.href)
  const besidePage = new URL('./', scene).href === new URL('./', location.href).href
  if (!keys.length && besidePage) return null
  const done = new Map()
  return (s) => {
    if (!isRelativeImagePath(s)) return undefined
    let url = done.get(s)
    if (url === undefined) {
      const key = packedKey(s)
      if (packed && packed[key] != null) url = 'data:' + (IMAGE_TYPES[key.split('.').pop().toLowerCase()] || 'application/octet-stream') + ';base64,' + packed[key]
      else url = besidePage ? null : new URL(s, scene).href
      done.set(s, url)
    }
    return url || undefined
  }
}

/** Swap every string in a frame's commands that `resolve` maps (in place). */
function swapStrings(v, resolve) {
  for (let i = 0; i < v.length; i++) {
    const x = v[i]
    if (typeof x === 'string') { const u = resolve(x); if (u !== undefined) v[i] = u }
    else if (x && typeof x === 'object') {
      if (Array.isArray(x)) swapStrings(x, resolve)
      else for (const k in x) {
        const y = x[k]
        if (typeof y === 'string') { const u = resolve(y); if (u !== undefined) x[k] = u }
        else if (y && typeof y === 'object') swapStrings(Array.isArray(y) ? y : [y], resolve)
      }
    }
  }
}

/**
 * The renderer for one canvas. `images`: a function from a string in the
 * commands to the URL to use instead (see imageResolver), or null. `hooks`: onEvent(event), onSize(size),
 * onApplied({reads, errors, ms, n, timing}), onReads(reads) (a promise has
 * settled), isActive() (has the keyboard).
 */
export function createRenderer(canvas, { three = null, addons = null, images = null, hooks }) {
  const H = new Map()
  let ctx2d = null
  let dpr = 1, cssW = 0, cssH = 0
  const reportedErrors = Object.create(null)
  // three.js objects that must follow the canvas's size: the renderer drawing
  // on this canvas, and every perspective camera.
  const glRenderers = [], cameras = []
  let timing = null
  let isGL = false
  let pointerIsDown = false

  function size() {
    dpr = window.devicePixelRatio || 1
    const r = canvas.getBoundingClientRect()
    cssW = Math.max(1, Math.round(r.width)); cssH = Math.max(1, Math.round(r.height))
    // A WebGL renderer owns the canvas size itself (setSize); only the 2D
    // context is scaled here, so drawing is in CSS pixels and stays sharp.
    if (!isGL) {
      const w = Math.round(cssW * dpr), h = Math.round(cssH * dpr)
      if (canvas.width !== w || canvas.height !== h) {
        // Resizing a canvas wipes it and resets its drawing state. A program
        // that drew once (no draw()) would be left blank, so the picture is
        // carried across, and the state the program set is put back.
        let keep = null, state = null
        if (ctx2d && canvas.width && canvas.height) {
          keep = document.createElement('canvas')
          keep.width = canvas.width; keep.height = canvas.height
          keep.getContext('2d').drawImage(canvas, 0, 0)
          state = {}
          for (const k of KEEP_STATE) state[k] = ctx2d[k]
        }
        canvas.width = w; canvas.height = h
        if (ctx2d) {
          ctx2d.setTransform(1, 0, 0, 1, 0, 0)
          if (keep) ctx2d.drawImage(keep, 0, 0)
          ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0)
          if (state) for (const k in state) { try { ctx2d[k] = state[k] } catch (e) { /* read-only in this browser */ } }
        }
      }
    }
    fitThree()
    hooks.onSize({ width: cssW, height: cssH, pixel_ratio: dpr })
  }

  function getCtx() {
    if (!ctx2d) {
      ctx2d = canvas.getContext('2d')
      if (ctx2d) ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    return ctx2d
  }

  function lookup(h) {
    if (h === 4) return getCtx()
    if (!H.has(h)) throw new Error('that object no longer exists in the page (#' + h + ')')
    return H.get(h)
  }

  function decode(v) {
    if (v === null || typeof v !== 'object') return v
    if (Array.isArray(v)) return v.map(decode)
    if ('$h' in v) return lookup(v.$h)
    if ('$e' in v) return evalExpr(v.$e)
    if ('$cb' in v) {
      const id = v.$cb
      return (ev) => hooks.onEvent({ k: 'cb', id, e: summarize(ev) })
    }
    if ('$d' in v) {
      const o = {}; for (const k in v.$d) o[k] = decode(v.$d[k]); return o
    }
    return v
  }

  function evalExpr(t) {
    switch (t[0]) {
      case 'v': return decode(t[1])
      case 'num': return Number(t[1])
      case 'ref': return decode(t[1])
      case 'get': { const o = evalExpr(t[1]); return o[prop(o, t[2])] }
      case 'neg': return -evalExpr(t[1])
      case '+': return evalExpr(t[1]) + evalExpr(t[2])
      case '-': return evalExpr(t[1]) - evalExpr(t[2])
      case '*': return evalExpr(t[1]) * evalExpr(t[2])
      case '/': return evalExpr(t[1]) / evalExpr(t[2])
      case '%': return evalExpr(t[1]) % evalExpr(t[2])
      case '**': return Math.pow(evalExpr(t[1]), evalExpr(t[2]))
      case '//': return Math.floor(evalExpr(t[1]) / evalExpr(t[2]))
    }
    throw new Error('unknown expression ' + t[0])
  }

  // What Python gets back for a read or an event: plain data only.
  function summarize(v, depth) {
    depth = depth || 0
    if (v === null || v === undefined) return null
    const t = typeof v
    if (t === 'number' || t === 'string' || t === 'boolean') return v
    if (t === 'function') return '<function>'
    if (Array.isArray(v) || ArrayBuffer.isView(v)) {
      if (depth > 2) return null
      const a = []; for (let i = 0; i < Math.min(v.length, 100000); i++) a.push(summarize(v[i], depth + 1)); return a
    }
    if (depth > 1) return null
    const out = {}
    if (typeof Event !== 'undefined' && v instanceof Event) {
      const r = canvas.getBoundingClientRect()
      if ('clientX' in v) { out.x = v.clientX - r.left; out.y = v.clientY - r.top }
    }
    for (const k in v) {
      let x; try { x = v[k] } catch (e) { continue }
      const tx = typeof x
      if (x === null || tx === 'number' || tx === 'string' || tx === 'boolean') out[k] = x
      else if (depth === 0 && tx === 'object' && !(x instanceof Node) && !(x instanceof Window)) {
        const s = summarize(x, depth + 1); if (s !== null) out[k] = s
      }
    }
    return out
  }

  function describe(obj, h) {
    if (h === 4) return 'ctx'
    if (h === 2) return 'canvas'
    if (h === 3) return 'THREE'
    if (h === 1) return 'js'
    const n = obj && obj.constructor && obj.constructor.name
    return n || 'this object'
  }

  function apply(cmds) {
    const started = performance.now()
    const reads = {}, errors = []
    for (let i = 0; i < cmds.length; i++) {
      const c = cmds[i]
      try {
        switch (c[0]) {
          case 'get': { const o = lookup(c[3]); H.set(c[2], o[prop(o, c[4])]); break }
          case 'set': { const o = lookup(c[2]); o[prop(o, c[3])] = decode(c[4]); break }
          case 'call': {
            const o = lookup(c[3]), name = prop(o, c[4]), fn = o == null ? undefined : o[name]
            if (typeof fn !== 'function') throw new TypeError(describe(o, c[3]) + ' has no method "' + c[4] + '"')
            const res = fn.apply(o, decode(c[5]))
            if (c[2]) H.set(c[2], res)
            break
          }
          case 'new': {
            const o = lookup(c[3]), Ctor = o == null ? undefined : o[prop(o, c[4])]
            if (typeof Ctor !== 'function') throw new TypeError(describe(o, c[3]) + ' has no "' + c[4] + '"')
            const args = decode(c[5])
            // A 3D renderer keeps its drawing buffer, so a screenshot of the
            // page is the scene rather than a blank canvas.
            if (three && Ctor === three.WebGLRenderer) {
              const opts = args[0] && typeof args[0] === 'object' ? args[0] : {}
              opts.preserveDrawingBuffer = true
              args[0] = opts
            }
            const made = Reflect.construct(Ctor, args)
            if (made && made.isWebGLRenderer) markGL(made)
            if (made && made.isPerspectiveCamera) cameras.push(made)
            if (c[2]) H.set(c[2], made)
            break
          }
          case 'fcall': { const f = lookup(c[3]); const r = f.apply(null, decode(c[4])); if (c[2]) H.set(c[2], r); break }
          case 'fnew': { const F = lookup(c[3]); const m = Reflect.construct(F, decode(c[4])); if (c[2]) H.set(c[2], m); break }
          case 'free': H.delete(c[2]); break
          case 'read': {
            const val = decode(c[3])
            if (val && typeof val.then === 'function') settle(val, c[2], c[4], c[1])
            else reads[c[2]] = summarize(val)
            break
          }
        }
      } catch (e) {
        const msg = (e && e.message) || String(e)
        const key = c[1] + '|' + msg
        if (!reportedErrors[key]) { reportedErrors[key] = 1; errors.push({ line: c[1], message: (e && e.name ? e.name + ': ' : '') + msg }) }
        if (c[0] === 'read') reads[c[2]] = null
      }
    }
    hooks.onApplied({ reads, errors, ms: performance.now() - started, n: cmds.length, timing })
  }

  // A PROMISE is answered when it settles, in a later frame. An object result
  // (a GPU adapter, a device) is kept under the handle Python reserved.
  function settle(promise, rid, newH, line) {
    promise.then((res) => {
      const plain = res === null || res === undefined || typeof res !== 'object' || Array.isArray(res) ||
        ArrayBuffer.isView(res) || Object.getPrototypeOf(res) === Object.prototype
      let answer
      if (plain || !newH) answer = summarize(res)
      else { H.set(newH, res); answer = { $h: newH } }
      if (hooks.onReads) hooks.onReads({ [rid]: answer })
    }, (e) => {
      if (hooks.onReads) hooks.onReads({ [rid]: { $error: 'line ' + line + ': ' + ((e && e.message) || String(e)) } })
    })
  }

  // three.js sizes the canvas itself: stop scaling it for 2D.
  function markGL(renderer) {
    if (renderer.domElement === canvas) { isGL = true; glRenderers.push(renderer) }
  }

  // Keep the 3D view in proportion: the renderer fills the canvas and each
  // camera's aspect is the canvas's. setSize with updateStyle=false leaves
  // the CSS (100% x 100%) in charge of layout.
  function fitThree() {
    for (const g of glRenderers) { try { g.setSize(cssW, cssH, false) } catch (e) { /* disposed */ } }
    for (const cam of cameras) { try { cam.aspect = cssW / cssH; cam.updateProjectionMatrix() } catch (e) { /* not a camera any more */ } }
  }

  function sendInput(e) {
    const k = { type: e.type }
    if (e.type === 'keydown' || e.type === 'keyup') {
      if (!hooks.isActive()) return
      if (e.repeat) return
      k.key = e.key; k.code = e.code
      if (e.key.indexOf('Arrow') === 0 || e.key === ' ') e.preventDefault()
    } else {
      if (e.type === 'pointerdown') { pointerIsDown = true; canvas.focus({ preventScroll: true }) }
      else if (e.type === 'pointerup') { if (!pointerIsDown) return; pointerIsDown = false }
      const r = canvas.getBoundingClientRect()
      k.x = e.clientX - r.left; k.y = e.clientY - r.top; k.button = e.button
    }
    hooks.onEvent({ k: 'input', e: k })
  }

  H.set(1, window); H.set(2, canvas)
  if (three) { H.set(3, three); H.set(5, addons) }
  window.addEventListener('keydown', sendInput)
  window.addEventListener('keyup', sendInput)
  canvas.addEventListener('pointerdown', sendInput)
  canvas.addEventListener('pointermove', sendInput)
  window.addEventListener('pointerup', sendInput)

  // PRESENT ON THE VERTICAL BLANK. A frame's commands are held and drawn in
  // the page's own animation frame, so every frame lands on a screen refresh.
  // Batches are applied in order, all of them, because a batch can create
  // objects a later one uses.
  //
  // ONE FRAME PER REFRESH, FROM A SHORT QUEUE. The host keeps a frame or two
  // in hand, so a slow round trip to Python empties the queue instead of
  // showing as a skipped refresh. If the queue ever runs long, it is caught up
  // so latency cannot grow.
  const pending = []
  let scheduled = false
  const abs = () => performance.timeOrigin + performance.now()
  function present() {
    scheduled = false
    if (!pending.length) return
    while (pending.length > 2) applyBatch(pending.shift())
    applyBatch(pending.shift())
    if (pending.length) { scheduled = true; requestAnimationFrame(present) }
  }
  function applyBatch(b) {
    timing = b.at ? { deliver: b.recv - b.at, wait: abs() - b.recv } : null
    apply(b.cmds)
  }

  const observer = new ResizeObserver(size)
  observer.observe(canvas)
  size()

  return {
    /** Queue one frame's commands; drawn on the next refresh. */
    push(cmds, at) {
      if (images && cmds) swapStrings(cmds, images)
      pending.push({ cmds: cmds || [], at, recv: at ? abs() : 0 })
      if (!scheduled) { scheduled = true; requestAnimationFrame(present) }
    },
    get size() { return { width: cssW, height: cssH, pixel_ratio: dpr } },
    /** Frames waiting for a refresh. */
    get waiting() { return pending.length },
    destroy() {
      observer.disconnect()
      window.removeEventListener('keydown', sendInput)
      window.removeEventListener('keyup', sendInput)
      window.removeEventListener('pointerup', sendInput)
      for (const g of glRenderers) { try { g.dispose() } catch (e) { /* already gone */ } }
      H.clear()
    },
  }
}

// ---------------------------------------------------------------- a single-file page
//
// `pyctures build scene.py -o scene.html` writes one HTML file. What a folder
// would hold beside the page comes inside it instead, as JSON in
// <script type="application/json" id="pyctures-inline">:
//   {runtime, sources: {path: text}, files: {path: base64}, three: {core, module, orbit}}

let inlineData
function inline() {
  if (inlineData === undefined) {
    inlineData = null
    try {
      const el = typeof document !== 'undefined' && document.getElementById('pyctures-inline')
      if (el) inlineData = JSON.parse(el.textContent)
    } catch (e) { /* not a single-file page */ }
  }
  return inlineData
}

let threePromise = null
/** three.js and OrbitControls: from inside a single-file page, or the folder beside this file. */
function loadThree() {
  if (!threePromise) {
    const inl = inline()
    let urls
    if (inl && inl.three) {
      // Each module becomes a Blob URL, and the one it imports is pointed at it.
      const blob = (text) => URL.createObjectURL(new Blob([text], { type: 'text/javascript' }))
      const core = blob(inl.three.core)
      const mod = blob(inl.three.module.split('"./three.core.min.js"').join(JSON.stringify(core)))
      const orbit = blob(inl.three.orbit.split("'./three.module.min.js'").join(JSON.stringify(mod)))
      urls = [mod, orbit]
    } else {
      urls = [new URL('three/three.module.min.js', BASE).href, new URL('three/OrbitControls.js', BASE).href]
    }
    threePromise = Promise.all(urls.map((u) => import(u)))
      .then((m) => ({ three: m[0], addons: { OrbitControls: m[1].OrbitControls } }))
  }
  return threePromise
}

// ---------------------------------------------------------------- transports
//
// A transport runs the Python half somewhere: start(source, info) and
// tick(payload) resolve to the runtime's JSON reply text; stop() ends the run.

/** Python in your own CPython, behind `pyctures run` (one worker per scene). */
export function websocketTransport(src) {
  const url = new URL('/_pyctures/ws', location.href)
  url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  url.searchParams.set('src', new URL(src, location.href).pathname)
  const ws = new WebSocket(url)
  let nextId = 1
  const waiting = new Map()
  let closed = null
  const opened = new Promise((resolve, reject) => {
    ws.onopen = resolve
    ws.onerror = () => reject(new Error('Could not reach the pyctures server.'))
  })
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data)
    if (m.type === 'reload') { location.reload(); return }
    const w = waiting.get(m.id)
    if (!w) return
    waiting.delete(m.id)
    if (m.error) w.reject(new Error(m.error))
    else w.resolve(m.reply)
  }
  ws.onclose = () => {
    closed = new Error('The pyctures server has stopped. Start it again with  pyctures run')
    for (const w of waiting.values()) w.reject(closed)
    waiting.clear()
  }
  async function call(msg) {
    await opened
    if (closed) throw closed
    const id = nextId++
    return new Promise((resolve, reject) => {
      waiting.set(id, { resolve, reject })
      ws.send(JSON.stringify({ id, ...msg }))
    })
  }
  return {
    label: 'your Python',
    start: (_source, info) => call({ op: 'start', info }),
    tick: (payload) => call({ op: 'tick', payload }),
    stop: async () => { try { ws.close() } catch (e) { /* already closed */ } },
    log: (text) => { if (ws.readyState === 1) ws.send(JSON.stringify({ op: 'log', text })) },
  }
}

// The Python that hosts scenes in Pyodide: every scene gets its own copy of
// the module, and is made the module `pyctures` for the length of each call,
// so scenes cannot see each other.
const PY_HOST = `
import sys, types
_pyctures_scenes = {}
def _pyctures_new(sid):
    m = types.ModuleType('pyctures')
    m.__file__ = 'pyctures.py'
    exec(compile(__pyctures_source, 'pyctures.py', 'exec'), m.__dict__)
    _pyctures_scenes[sid] = m
def _pyctures_call(sid, op, a=None, b=None):
    m = _pyctures_scenes[sid]
    sys.modules['pyctures'] = m
    if op == 'start':
        return m.start(a, b)
    if op == 'tick':
        return m.tick(a)
    m.stop()
    _pyctures_scenes.pop(sid, None)
    return 'stopped'
`

function pyodideBase() {
  const url = (typeof window !== 'undefined' && window.PYCTURES_PYODIDE_URL) || PYODIDE_URL
  return new URL(url.replace(/\/?$/, '/'), location.href).href
}

let runtimePromise = null
/** The Python half's source: from a single-file page, or pyctures.py beside this file. */
function loadRuntime() {
  if (!runtimePromise) {
    const inl = inline()
    runtimePromise = inl && inl.runtime
      ? Promise.resolve(inl.runtime)
      : fetch(new URL('pyctures.py', BASE)).then((r) => {
        if (!r.ok) throw new Error('pyctures.py was not found beside pyctures.js')
        return r.text()
      })
    runtimePromise.catch(() => { runtimePromise = null })
  }
  return runtimePromise
}

/** The files a scene opens, as [{path, data}], from a single-file page or beside the scene. */
async function readFiles(src, files) {
  const inl = inline()
  const out = []
  for (const f of files) {
    const path = f.split('/').filter((p) => p && p !== '.').join('/')
    let data
    if (inl && inl.files && inl.files[f] != null) {
      const bin = atob(inl.files[f])
      const bytes = new Uint8Array(bin.length)
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
      data = bytes.buffer
    } else {
      const res = await fetch(new URL(f, new URL(src, location.href)))
      if (!res.ok) throw new Error(`Could not load ${f} (${res.status})`)
      data = await res.arrayBuffer()
    }
    out.push({ path, data })
  }
  return out
}

/**
 * THE WORKER. Python runs here, off the page's main thread, so a slow frame,
 * Python's garbage collection or a loop that never waits cannot hold up
 * drawing, scrolling or input. It only ever turns a request into a reply
 * (the same JSON the other transports give). This function is the worker's
 * whole code: it is turned into a Blob URL, so a page needs no extra file.
 */
function workerMain() {
  let py = null, booting = null, call = null
  async function boot(m) {
    importScripts(m.pyodide + 'pyodide.js')
    // eslint-disable-next-line no-undef
    py = await loadPyodide({ indexURL: m.pyodide })
    py.globals.set('__pyctures_source', m.runtime)
    py.runPython(m.host)
    call = py.globals.get('_pyctures_call')
  }
  function writeFiles(files) {
    for (const f of files || []) {
      const parts = f.path.split('/')
      for (let i = 1; i < parts.length; i++) {
        try { py.FS.mkdir(parts.slice(0, i).join('/')) } catch (e) { /* exists */ }
      }
      py.FS.writeFile(f.path, new Uint8Array(f.data))
    }
  }
  self.onmessage = async (ev) => {
    const m = ev.data
    if (m.type === 'boot') { booting = boot(m); booting.catch(() => {}); return }
    let reply = null, error = null
    try {
      try { await booting } catch (e) { throw new Error('Python could not load: ' + ((e && e.message) || e)) }
      if (m.op === 'start') {
        writeFiles(m.files)
        await py.loadPackagesFromImports(m.source)
        py.globals.get('_pyctures_new')(m.sid)
        reply = call(m.sid, 'start', m.source, m.info)
      } else if (m.op === 'tick') {
        reply = call(m.sid, 'tick', m.payload)
      } else {
        reply = call(m.sid, 'stop')
      }
    } catch (e) {
      error = String((e && e.message) || e)
    }
    self.postMessage({ id: m.id, reply, error })
  }
}

let pyWorker = null
/**
 * The page's Python worker, started on first use and shared by every scene on
 * the page (one copy of Python). terminate() ends it, for a scene stuck in a
 * loop: every call still waiting is answered with an error marked
 * `restarted`, and the next call starts a fresh worker.
 */
function pythonWorker() {
  if (pyWorker && !pyWorker.dead) return pyWorker
  const url = URL.createObjectURL(new Blob(['(' + workerMain.toString() + ')()'], { type: 'text/javascript' }))
  const w = new Worker(url)
  const waiting = new Map()
  let nextId = 1
  const me = { dead: null }
  const fail = (why) => {
    for (const p of waiting.values()) { const e = new Error(why); e.restarted = true; p.reject(e) }
    waiting.clear()
  }
  w.onmessage = (ev) => {
    const m = ev.data
    const p = waiting.get(m.id)
    if (!p) return
    waiting.delete(m.id)
    if (m.error != null) p.reject(new Error(m.error))
    else p.resolve(m.reply)
  }
  w.onerror = (ev) => {
    ev.preventDefault()
    for (const p of waiting.values()) p.reject(new Error('Python stopped: ' + (ev.message || 'the worker failed')))
    waiting.clear()
  }
  const booted = Promise.all([loadRuntime(), pyodideBase()]).then(([runtime, base]) => {
    w.postMessage({ type: 'boot', pyodide: base, runtime, host: PY_HOST })
  })
  me.call = async (msg, transfer) => {
    await booted
    if (me.dead) { const e = new Error(me.dead); e.restarted = true; throw e }
    return new Promise((resolve, reject) => {
      const id = nextId++
      waiting.set(id, { resolve, reject })
      w.postMessage({ id, ...msg }, transfer || [])
    })
  }
  me.terminate = (why) => {
    if (me.dead) return
    me.dead = why || 'Python was restarted'
    w.terminate()
    URL.revokeObjectURL(url)
    fail(me.dead)
    if (pyWorker === me) pyWorker = null
  }
  pyWorker = me
  return me
}

let nextSceneId = 1

/**
 * Python in a Web Worker, with Pyodide: what built pages and scenes on a web
 * page use. `files`: extra files to put beside the scene.
 */
export function workerTransport(src, files = []) {
  const sid = nextSceneId++
  let worker = null
  return {
    label: 'Python in a worker',
    async start(source, info) {
      worker = pythonWorker()
      const data = await readFiles(src, files)
      return worker.call({ op: 'start', sid, source, info: JSON.stringify(info), files: data }, data.map((d) => d.data))
    },
    tick(payload) { return worker.call({ op: 'tick', sid, payload: JSON.stringify(payload) }) },
    async stop() {
      if (worker && !worker.dead) { try { await worker.call({ op: 'stop', sid }) } catch (e) { /* not running */ } }
    },
    /** Stop a scene that is stuck in a loop: ends the worker, and Python with it. */
    hardStop() { if (worker) worker.terminate('Python was restarted') },
  }
}

let pyodidePromise = null
/** Pyodide on the page's own thread, loaded once and shared by every scene on it. */
function loadPyodideOnce() {
  if (!pyodidePromise) {
    const base = pyodideBase()
    pyodidePromise = (async () => {
      const [{ loadPyodide }, runtime] = await Promise.all([import(base + 'pyodide.mjs'), loadRuntime()])
      const py = await loadPyodide({ indexURL: base })
      py.globals.set('__pyctures_source', runtime)
      py.runPython(PY_HOST)
      return py
    })()
  }
  return pyodidePromise
}

/**
 * Python on the page's own thread, with Pyodide: for a browser without
 * workers, or `data-pyctures-worker="off"`. A slow frame here holds up the
 * page, so the worker is the better choice wherever it is available.
 */
export function pyodideTransport(src, files = []) {
  const sid = nextSceneId++
  let py = null, callPy = null
  return {
    label: 'Python in the page',
    async start(source, info) {
      py = await loadPyodideOnce()
      callPy = py.globals.get('_pyctures_call')
      for (const f of await readFiles(src, files)) {
        const parts = f.path.split('/')
        for (let i = 1; i < parts.length; i++) {
          try { py.FS.mkdir(parts.slice(0, i).join('/')) } catch (e) { /* exists */ }
        }
        py.FS.writeFile(f.path, new Uint8Array(f.data))
      }
      await py.loadPackagesFromImports(source)
      py.globals.get('_pyctures_new')(sid)
      return callPy(sid, 'start', source, JSON.stringify(info))
    },
    async tick(payload) { return callPy(sid, 'tick', JSON.stringify(payload)) },
    async stop() { if (callPy) { try { callPy(sid, 'stop') } catch (e) { /* not running */ } } },
  }
}

// ---------------------------------------------------------------- the page around a scene

const STYLE = `
.pyctures-scene{position:relative;overflow:hidden;color-scheme:dark}
.pyctures-scene>canvas{position:absolute;inset:0;width:100%;height:100%;display:block;outline:none;touch-action:none;-webkit-user-select:none;user-select:none}
.pyctures-cover{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:14px system-ui,sans-serif;color:#9aa3b2;pointer-events:none}
.pyctures-error{position:absolute;inset:0;overflow:auto;padding:20px;box-sizing:border-box;background:rgba(20,10,14,.94);color:#f3f4f6;font:14px system-ui,sans-serif}
.pyctures-error h2{margin:0 0 12px;font-size:17px;color:#ff8a8a}
.pyctures-error pre{margin:0 0 14px;padding:12px;background:#0b0b0f;border-radius:6px;overflow:auto;font:12.5px/1.5 ui-monospace,Menlo,Consolas,monospace;white-space:pre}
.pyctures-error .bad{background:#5a1d26;display:inline-block;min-width:100%}
.pyctures-error button,.pyctures-stuck button{font:inherit;background:#2a2f3a;color:#f3f4f6;border:1px solid #3a4150;border-radius:6px;padding:4px 12px;cursor:pointer}
.pyctures-output{position:absolute;left:0;right:0;bottom:0;max-height:35%;overflow:auto;margin:0;padding:8px 12px;background:rgba(11,11,15,.88);color:#d1d5db;font:12px/1.5 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap}
.pyctures-output .err{color:#ff8a8a}.pyctures-output .info{color:#9aa3b2}
.pyctures-stuck{position:absolute;left:50%;bottom:16px;transform:translateX(-50%);z-index:3;display:flex;gap:12px;align-items:center;max-width:calc(100% - 32px);box-sizing:border-box;padding:10px 14px;border-radius:8px;background:rgba(20,10,14,.92);color:#f3f4f6;font:13px system-ui,sans-serif}
.pyctures-measure{position:absolute;top:6px;left:6px;z-index:2;margin:0;padding:5px 8px;border-radius:6px;background:rgba(0,0,0,.66);color:#e5e7eb;font:11px/1.45 ui-monospace,Menlo,Consolas,monospace;white-space:pre;pointer-events:none}
`
let styled = false
function addStyle() {
  if (styled) return
  styled = true
  const s = document.createElement('style')
  s.textContent = STYLE
  document.head.appendChild(s)
}

function measureSwitch(el) {
  if (el && el.hasAttribute('data-pyctures-measure') && el.getAttribute('data-pyctures-measure') !== '0') return true
  try {
    if (new URLSearchParams(location.search).get('measure') === '1') return true
    return localStorage.getItem(MEASURE_KEY) === '1'
  } catch (e) { return false }
}

let activeScene = null

/**
 * One scene on the page, in `el`. Options:
 *   src         the scene's .py file (a URL, relative to the page)
 *   transport   from websocketTransport() or pyodideTransport()
 *   fullPage    the scene is the whole page: it has the keyboard from the start
 *   output      'panel' shows printed text over the scene; otherwise the console
 *   background  the colour behind the canvas
 *   autoStart   false: wait for scene.start()
 *   makeTransport  a function that makes a fresh transport for each run
 */
export class Scene {
  constructor(el, options) {
    addStyle()
    this.el = el
    this.opt = Object.assign({ output: 'console', background: '#0b0b0f', autoStart: true }, options)
    this.name = decodeURIComponent((this.opt.src || 'scene.py').split('/').pop())
    this.status = 'idle'
    this.errors = []
    this.r = {
      token: 0, live: false, busy: false, busySince: 0, warnedStuck: false, missedRefresh: false,
      sent: 0, shown: 0, clock: 0, period: 1000 / 60, lastRaf: 0, raf: 0,
      events: [], reads: {}, size: { width: 0, height: 0, pixel_ratio: 1 },
      measuring: false, measureSince: 0, lastShown: 0,
      acc: { frames: 0, shown: 0, missed: 0, worst: 0, cmds: 0, ms: {} },
    }
    this.visible = false
    el.classList.add('pyctures-scene')
    if (getComputedStyle(el).position === 'static') el.style.position = 'relative'
    if (!this.opt.fullPage && el.clientHeight === 0) el.style.aspectRatio = el.style.aspectRatio || '16 / 9'
    if (!el.style.background) el.style.background = this.opt.background
    el.pycturesScene = this
    if (this.opt.fullPage) activeScene = this

    // Start only once the scene is on screen, and pause while it is not.
    this.io = new IntersectionObserver((entries) => {
      const seen = entries[entries.length - 1].isIntersecting
      if (seen === this.visible) return
      this.visible = seen
      if (seen && this.status === 'idle' && this.opt.autoStart) this.start()
      else if (seen) this.resume()
    }, { rootMargin: '100px' })
    this.io.observe(el)
    this.onVisibility = () => { if (!document.hidden) this.resume() }
    document.addEventListener('visibilitychange', this.onVisibility)
    this.loop = this.loop.bind(this)
  }

  // -------- output
  log(kind, text, line) {
    if (!text) return
    text = String(text).replace(/\n$/, '')
    if (kind === 'err') console.error(`[${this.name}] ${text}`)
    else if (kind === 'info') console.info(`[${this.name}] ${text}`)
    else console.log(text)
    if (kind !== 'out' && this.transport && this.transport.log) this.transport.log(text)
    if (this.opt.output !== 'panel') return
    if (!this.outEl) {
      this.outEl = document.createElement('pre')
      this.outEl.className = 'pyctures-output'
      this.el.appendChild(this.outEl)
    }
    const span = document.createElement('span')
    span.className = kind
    span.textContent = text + '\n'
    this.outEl.appendChild(span)
    while (this.outEl.childNodes.length > 400) this.outEl.removeChild(this.outEl.firstChild)
    this.outEl.scrollTop = this.outEl.scrollHeight
  }

  setStatus(s) {
    this.status = s
    this.el.dataset.pycturesStatus = s
    this.el.dispatchEvent(new CustomEvent('pyctures-status', { detail: { status: s } }))
  }

  cover(text) {
    if (!this.coverEl) {
      this.coverEl = document.createElement('div')
      this.coverEl.className = 'pyctures-cover'
      this.el.appendChild(this.coverEl)
    }
    this.coverEl.textContent = text || ''
    this.coverEl.style.display = text ? '' : 'none'
  }

  showError(message, line) {
    const box = document.createElement('div')
    box.className = 'pyctures-error'
    const h = document.createElement('h2')
    h.textContent = line ? `Error on line ${line} of ${this.name}` : `Error in ${this.name}`
    box.appendChild(h)
    const pre = document.createElement('pre')
    pre.textContent = message
    box.appendChild(pre)
    const lines = (this.source || '').split('\n')
    if (line && lines[line - 1] !== undefined) {
      const code = document.createElement('pre')
      for (let n = Math.max(1, line - 3); n <= Math.min(lines.length, line + 3); n++) {
        const row = document.createElement('span')
        row.textContent = String(n).padStart(4) + '  ' + lines[n - 1]
        if (n === line) row.className = 'bad'
        code.appendChild(row)
        code.appendChild(document.createTextNode('\n'))
      }
      box.appendChild(code)
    }
    const again = document.createElement('button')
    again.textContent = 'Run again'
    again.onclick = () => this.start()
    box.appendChild(again)
    this.errorEl = box
    this.el.appendChild(box)
    this.el.dataset.pycturesError = (line ? `line ${line}: ` : '') + message.split('\n').pop()
  }

  // -------- running
  async start() {
    await this.stop()
    const r = this.r
    const token = ++r.token
    if (!this.transport) this.transport = this.opt.makeTransport ? this.opt.makeTransport() : this.opt.transport
    this.setStatus('starting')
    if (this.errorEl) { this.errorEl.remove(); this.errorEl = null }
    if (this.outEl) this.outEl.textContent = ''
    delete this.el.dataset.pycturesError
    Object.assign(r, { events: [], reads: {}, busy: false, warnedStuck: false, sent: 0, shown: 0, clock: 0, lastRaf: 0 })
    this.cover('Starting Python…')
    try {
      const inl = inline()
      if (this.source == null && inl && inl.sources && inl.sources[this.opt.src] != null) this.source = inl.sources[this.opt.src]
      if (this.source == null) {
        const res = await fetch(this.opt.src, { cache: 'no-store' })
        if (!res.ok) throw new Error(`Could not load ${this.opt.src} (${res.status})`)
        this.source = await res.text()
      }
      const source = this.source
      let three = null
      if (/\bTHREE\b|\baddons\b/.test(source)) {
        try { three = await loadThree() } catch (e) { this.log('err', `3D could not load: ${(e && e.message) || e}`) }
      }
      if (token !== r.token) return
      // A fresh canvas for every run: an empty handle table, and no context
      // left over from the last run (a canvas keeps whichever it made first).
      if (this.canvas) this.canvas.remove()
      this.canvas = document.createElement('canvas')
      this.canvas.tabIndex = 0
      this.canvas.setAttribute('aria-label', this.name)
      this.el.insertBefore(this.canvas, this.el.firstChild)
      this.canvas.addEventListener('pointerdown', () => { activeScene = this })
      this.canvas.addEventListener('focus', () => { activeScene = this })
      this.renderer = createRenderer(this.canvas, {
        three: three && three.three,
        addons: three && three.addons,
        images: imageResolver(this.opt.src, inl && inl.files),
        hooks: {
          onEvent: (e) => { if (r.live) r.events.push(e) },
          onSize: (s) => { r.size = s },
          onApplied: (d) => this.applied(d),
          onReads: (reads) => { if (r.live) Object.assign(r.reads, reads) },
          isActive: () => activeScene === this,
        },
      })
      r.measuring = measureSwitch(this.el)
      this.watch()
      r.acc = { frames: 0, shown: 0, missed: 0, worst: 0, cmds: 0, ms: {} }
      r.lastShown = 0
      r.busy = true
      r.busySince = performance.now()
      this.setStatus('running')
      const text = await this.transport.start(source, { ...r.size, measure: r.measuring })
      r.busy = false
      if (r.warnedStuck) this.unstuck()
      if (token !== r.token) return
      this.cover('')
      if (this.handleReply(JSON.parse(text), token)) {
        r.live = true
        r.measureSince = performance.now()
        r.raf = requestAnimationFrame(this.loop)
      }
    } catch (error) {
      if (token !== r.token) return
      r.busy = false
      if (error && error.restarted) { this.start(); return }   // another scene restarted Python
      this.cover('')
      const msg = String((error && error.message) || error)
      this.log('err', msg)
      this.showError(msg, 0)
      this.setStatus('error')
    }
  }

  async stop() {
    const r = this.r
    const wasBusy = r.busy
    r.token++
    r.live = false
    cancelAnimationFrame(r.raf)
    this.unwatch()
    if (this.status === 'running' || this.status === 'starting') this.setStatus('stopped')
    if (this.renderer) { this.renderer.destroy(); this.renderer = null }
    if (this.transport) {
      // Python in the middle of a frame cannot be asked to stop: a worker is
      // ended instead (and started afresh on the next run).
      if (wasBusy && this.transport.hardStop) this.transport.hardStop()
      else {
        try {
          await Promise.race([this.transport.stop(), new Promise((res) => setTimeout(res, 1000))])
        } catch (e) { /* best effort */ }
      }
      // A WebSocket transport is one run; make a new one next time.
      if (this.opt.makeTransport) this.transport = null
    }
    r.busy = false
  }

  /** Remove the scene from the page for good. */
  async destroy() {
    await this.stop()
    this.io.disconnect()
    document.removeEventListener('visibilitychange', this.onVisibility)
    if (this.canvas) this.canvas.remove()
  }

  // THE WATCHDOG. Python runs off the page's thread, so the page can still
  // notice when a frame (or the file's top level) has not come back for a
  // few seconds, say why, and offer to stop it.
  watch() {
    this.unwatch()
    this.watchdog = setInterval(() => {
      const r = this.r
      if (r.busy && !r.warnedStuck && performance.now() - r.busySince > STUCK_MS) {
        r.warnedStuck = true
        this.log('info', 'Python has not finished a frame for 3 seconds. A loop that never awaits frame() holds it.')
        this.showStuck()
      }
    }, 500)
  }

  unwatch() {
    clearInterval(this.watchdog)
    this.watchdog = 0
    this.unstuck()
  }

  showStuck() {
    if (this.stuckEl) return
    const box = document.createElement('div')
    box.className = 'pyctures-stuck'
    const text = document.createElement('span')
    text.textContent = 'Python has not finished a frame for 3 seconds. Is there a loop that never waits?'
    const btn = document.createElement('button')
    btn.textContent = 'Stop'
    btn.onclick = () => this.halt()
    box.appendChild(text)
    box.appendChild(btn)
    this.stuckEl = box
    this.el.appendChild(box)
  }

  unstuck() {
    this.r.warnedStuck = false
    if (this.stuckEl) { this.stuckEl.remove(); this.stuckEl = null }
  }

  /** Stop a scene that is stuck, and say so. */
  async halt() {
    await this.stop()
    const msg = 'Stopped: Python did not finish a frame. A loop that never waits (for example while True: without await frame()) holds it.'
    this.log('err', msg)
    this.showError(msg, 0)
    this.setStatus('error')
  }

  resume() {
    const r = this.r
    if (!r.live || !this.visible || document.hidden) return
    cancelAnimationFrame(r.raf)
    r.clock = 0          // re-anchor: no giant step after a pause
    r.lastRaf = 0
    r.raf = requestAnimationFrame(this.loop)
  }

  applied(d) {
    const r = this.r
    r.shown++
    if (r.measuring) {
      const m = r.acc.ms
      m.draw_in_page = (m.draw_in_page || 0) + (d.ms || 0)
      r.acc.shown++
      r.acc.cmds += d.n || 0
    }
    // A frame left the queue: keep one coming.
    if (r.live && !r.busy) this.requestFrame(performance.now())
    Object.assign(r.reads, d.reads)
    for (const e of d.errors || []) {
      const text = e.line ? `line ${e.line}: ${e.message}` : e.message
      this.errors.push(text)
      this.log('err', text, e.line)
    }
  }

  handleReply(reply, token) {
    const r = this.r
    if (token !== r.token) return false
    if (reply.out) this.log('out', reply.out)
    if (reply.err) this.log('err', reply.err)
    // Always, even an empty frame: the renderer counts frames to pace them.
    r.sent++
    this.renderer.push(reply.cmds || [], r.measuring ? performance.timeOrigin + performance.now() : 0)
    if (reply.error) {
      r.live = false
      this.log('err', reply.error, reply.errorLine || undefined)
      this.showError(reply.error, reply.errorLine || 0)
      this.setStatus('error')
      return false
    }
    if (!reply.running) {
      r.live = false
      this.setStatus('finished')
      return false
    }
    return true
  }

  /** Ask Python for the next frame. At most one is in flight. */
  requestFrame(now) {
    const r = this.r
    if (!r.live || r.busy || document.hidden || !this.visible) return
    // At most two frames in hand: enough to cover an uneven round trip, few
    // enough that input still feels immediate.
    if (r.sent - r.shown >= 2) return
    // THE GAME'S CLOCK ADVANCES ONE REFRESH PER FRAME. Only when Python has
    // truly fallen behind does it jump to real time, so a game never runs in
    // slow motion.
    const period = r.period
    let dt = period / 1000
    if (!r.clock) {
      r.clock = now
    } else {
      r.clock += period
      const behind = now - r.clock
      if (behind > period * 3) {
        dt = Math.min(0.1, (period + behind) / 1000)
        r.clock = now
      } else if (r.clock - now > period * 4) {
        r.clock = now
      }
    }
    r.missedRefresh = false
    const payload = { dt, events: r.events, reads: r.reads, ...r.size, measure: r.measuring }
    r.events = []
    r.reads = {}
    r.busy = true
    r.busySince = now
    const token = r.token
    const t0 = performance.now()
    this.transport.tick(payload).then((text) => {
      if (token !== r.token) return
      r.busy = false
      if (r.warnedStuck) this.unstuck()
      const done = performance.now()
      const parsed = JSON.parse(text)
      if (r.measuring) {
        const m = r.acc.ms
        const python = (parsed.t && parsed.t.python) || 0
        m.round_trip = (m.round_trip || 0) + (done - t0)
        m.bridge = (m.bridge || 0) + Math.max(0, done - t0 - python)
        for (const k in parsed.t || {}) m[k] = (m[k] || 0) + parsed.t[k]
        r.acc.frames++
      }
      if (this.handleReply(parsed, token) && r.missedRefresh) this.requestFrame(done)
    }, (error) => {
      if (token !== r.token) return
      r.busy = false
      r.live = false
      if (error && error.restarted) { this.start(); return }   // another scene restarted Python
      const msg = String((error && error.message) || error)
      this.log('err', msg)
      this.showError(msg, 0)
      this.setStatus('error')
    })
  }

  loop(now) {
    const r = this.r
    if (!r.live) return
    if (!this.visible || document.hidden) { r.raf = 0; return }   // paused; resume() restarts it
    r.raf = requestAnimationFrame(this.loop)
    // The display's refresh period (16.7 ms at 60 Hz, 8.3 at 120), learnt
    // from the animation frames themselves.
    if (r.lastRaf) {
      const delta = now - r.lastRaf
      if (delta > 4 && delta < 40) r.period = r.period * 0.9 + delta * 0.1
    }
    const gap = r.lastRaf ? now - r.lastRaf : 0
    r.lastRaf = now
    if (r.measuring) this.measureTick(now, gap)
    if (r.busy) {
      r.missedRefresh = true
      return
    }
    this.requestFrame(now)
  }

  // MEASURE MODE: add ?measure=1 to the page's address, put
  // data-pyctures-measure on the scene's div, or set
  // localStorage['pyctures:measure'] = '1'. A box over the scene shows, each
  // second, the frame rate and where the frame time goes; the same summary is
  // logged and kept in window.__pycturesMeasure (and scene.measure).
  //
  // A MISSED REFRESH is a screen refresh that showed no new frame: either an
  // animation frame came with nothing new in the queue, or the page was held
  // so long that whole refreshes went by with no animation frame at all.
  measureTick(now, gap) {
    const r = this.r, a = r.acc
    if (r.shown === r.lastShown) a.missed++
    if (gap > r.period * 1.5) a.missed += Math.round(gap / r.period) - 1
    if (gap > a.worst) a.worst = gap
    r.lastShown = r.shown
    if (now - r.measureSince < 1000) return
    const ms = {}
    for (const k in a.ms) ms[k] = +(a.ms[k] / Math.max(1, k === 'draw_in_page' ? a.shown : a.frames)).toFixed(2)
    const summary = {
      scene: this.name, runtime: (this.transport && this.transport.label) || '',
      fps: Math.round((a.shown * 1000) / (now - r.measureSince)), ms,
      commands: Math.round(a.cmds / Math.max(1, a.shown)), queued: r.sent - r.shown, missedRefreshes: a.missed,
      longestRefresh: +a.worst.toFixed(1),
    }
    this.measure = summary
    window.__pycturesMeasure = summary
    console.info('[pyctures measure]', JSON.stringify(summary))
    this.showMeasure(summary)
    r.acc = { frames: 0, shown: 0, missed: 0, worst: 0, cmds: 0, ms: {} }
    r.measureSince = now
  }

  showMeasure(m) {
    if (!this.measureEl) {
      this.measureEl = document.createElement('pre')
      this.measureEl.className = 'pyctures-measure'
      this.el.appendChild(this.measureEl)
    }
    const f = (v) => (v == null ? '–' : v.toFixed(1))
    this.measureEl.textContent =
      `${m.fps} fps   missed ${m.missedRefreshes}   longest ${m.longestRefresh.toFixed(0)} ms\n` +
      `python ${f(m.ms.python)} ms   round trip ${f(m.ms.round_trip)} ms\n` +
      `draw ${f(m.ms.draw_in_page)} ms   queued ${m.queued}\n` +
      m.runtime
  }
}

// ---------------------------------------------------------------- embedding

function serverMode() {
  const m = document.querySelector('meta[name="pyctures-server"]')
  return !!(m && m.content)
}

/**
 * Show the scene `src` in `el`. Attributes on `el` (all optional):
 *   data-pyctures-src         the .py file (required for auto-mount)
 *   data-pyctures-files       extra files the scene opens, comma-separated
 *   data-pyctures-output      "panel" to show print() over the scene
 *   data-pyctures-background  a CSS colour
 *   data-pyctures-fullpage    the scene is the whole page
 *   data-pyctures-measure     show the measure box (frame rate and timings)
 *   data-pyctures-worker      "off" runs Python on the page's own thread
 */
export function mount(el, options = {}) {
  if (el.pycturesScene) return el.pycturesScene
  const src = options.src || el.dataset.pycturesSrc
  const files = options.files || (el.dataset.pycturesFiles || '').split(',').map((s) => s.trim()).filter(Boolean)
  const server = options.server !== undefined ? options.server : serverMode()
  const worker = options.worker !== undefined ? options.worker
    : el.dataset.pycturesWorker !== 'off' && typeof Worker !== 'undefined'
  const make = () => (server ? websocketTransport(src) : worker ? workerTransport(src, files) : pyodideTransport(src, files))
  const scene = new Scene(el, {
    src,
    fullPage: options.fullPage !== undefined ? options.fullPage : el.hasAttribute('data-pyctures-fullpage'),
    output: options.output || el.dataset.pycturesOutput || 'console',
    background: options.background || el.dataset.pycturesBackground || '#0b0b0f',
    autoStart: options.autoStart !== false,
    makeTransport: make,
  })
  return scene
}

/** Mount every `[data-pyctures-src]` element on the page. */
export function mountAll(root = document) {
  return Array.from(root.querySelectorAll('[data-pyctures-src]')).map((el) => mount(el))
}

if (typeof document !== 'undefined' && !window.PYCTURES_NO_AUTO) {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => mountAll())
  else mountAll()
}
