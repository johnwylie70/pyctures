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
 * 2 canvas, 3 THREE, 4 the 2D context (made on first use), 5 addons,
 * 7 plain drawing, 8 saved values, 9 files and databases, 10 sound, 11 dials and other on-screen controls.
 *
 * SOUND AND DIALS are two libraries of their own (synths and dials), carried beside this file in
 * `synths/` and `dials/` and loaded only for a scene that uses them: see soundKeeper and dialsKeeper.
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

// ---------------------------------------------------------------- saved values

/**
 * SAVED VALUES: Python's save("best", 120) and load("best", 0). A value is kept as JSON text
 * in the page's localStorage, one entry for each name, under `pyctures:<the scene>:<name>`, so
 * two scenes on one site never read each other's and nothing else the page keeps is touched.
 * Python is handed all of them when a scene starts (`all`), because load() must answer at
 * once, and sends each save() as a command (`save`). Where the page has no storage (a private
 * window, a frame that is refused it) or it is full, what is saved is kept here instead, for
 * as long as the page is open.
 */
const KEPT = new Map()
function savedValues(scene) {
  const under = `pyctures:${scene}:`
  return {
    all() {
      const out = {}
      try {
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          // `file:` entries are files (see sceneFiles), not values.
          if (key && key.startsWith(under) && !key.startsWith(under + 'file:')) out[key.slice(under.length)] = localStorage.getItem(key)
        }
      } catch (e) { /* no storage */ }
      for (const [key, kept] of KEPT) if (key.startsWith(under)) out[key.slice(under.length)] = kept
      return out
    },
    save(name, kept) {
      KEPT.set(under + name, kept)
      try {
        localStorage.setItem(under + name, kept)
      } catch (e) {
        // No storage, or it is full: the scene carries on, and the value lasts while the page is open.
        if (!KEPT.warned) console.warn(`save("${name}", …): the browser would not keep it (${(e && e.message) || e}), so it will be forgotten when the page is closed`)
        KEPT.warned = true
      }
    },
  }
}

// ---------------------------------------------------------------- files and databases

/**
 * FILES AND DATABASES: Python's save_text("notes.txt", …), save_json(…) and
 * open_database("scores"). Python (Pyodide) has a file system of its own that is forgotten
 * with the page, so the page keeps the files. Python cannot ask for one and be answered at
 * once, so EVERY file a scene has stored is put into Python's file system before the scene
 * starts (`all`, into a folder of the scene's own: see storedIn), and Python sends each file it writes as a command: `text` with the path and
 * the text, `bytes` with the path and the file in base64 (a database, whole, at most once a
 * frame). With `pyctures run` none of this is used: the files are real ones beside the scene.
 *
 * WHERE THEY ARE KEPT. A host showing the scene can give `storage`, an object with any of
 *   list() -> Promise<string[]>                 the paths the scene has stored
 *   readText(path) -> Promise<string | null>    writeText(path, text) -> Promise
 *   readBytes(path) -> Promise<Uint8Array | null>   writeBytes(path, bytes) -> Promise
 * so that they are real files on the device; a database is just the file `scores.db`. What
 * the host leaves out is done here: text in localStorage, one entry for each file, under
 * `pyctures:<the scene>:file:<path>`; bytes in IndexedDB (database `pyctures`, store `files`)
 * under the same key. Where the browser will not keep one, it is kept here instead for as
 * long as the page is open. A host that writes but has no list() cannot say what it holds,
 * so the paths written through it are noted in localStorage (`pyctures:<the scene>:file:`).
 *
 * At the start each path is read as bytes first and, if there are none, as text.
 */
const KEPT_FILES = new Map()
let bytesDb = null
/** The page's IndexedDB for bytes, opened once; null where there is none. */
function openBytes() {
  if (!bytesDb) {
    bytesDb = new Promise((resolve) => {
      try {
        const req = indexedDB.open('pyctures', 1)
        req.onupgradeneeded = () => req.result.createObjectStore('files')
        req.onsuccess = () => resolve(req.result)
        req.onerror = req.onblocked = () => resolve(null)
      } catch (e) { resolve(null) }
    })
  }
  return bytesDb
}
/** One piece of work on the bytes store: resolves to its result once it is safely done. */
async function inBytes(mode, work) {
  const db = await openBytes()
  if (!db) throw new Error('no IndexedDB')
  return new Promise((resolve, reject) => {
    const tx = db.transaction('files', mode)
    const req = work(tx.objectStore('files'))
    tx.oncomplete = () => resolve(req.result)
    tx.onerror = tx.onabort = () => reject(tx.error || req.error || new Error('IndexedDB would not'))
  })
}
const cleanPath = (path) => String(path).split('/').filter((p) => p && p !== '.' && p !== '..').join('/')

/** The browser's own keeping of one scene's files: the same five calls a host can give. */
function browserFiles(under) {
  const memory = (path, data, e) => {
    KEPT_FILES.set(under + path, data)
    if (!KEPT_FILES.warned) console.warn(`${path}: the browser would not keep it (${(e && e.message) || e}), so it will be forgotten when the page is closed`)
    KEPT_FILES.warned = true
  }
  return {
    async list() {
      const paths = new Set()
      try {
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key && key.startsWith(under) && key.length > under.length) paths.add(key.slice(under.length))
        }
      } catch (e) { /* no storage */ }
      try {
        for (const key of await inBytes('readonly', (st) => st.getAllKeys(IDBKeyRange.bound(under, under + '￿')))) paths.add(key.slice(under.length))
      } catch (e) { /* no storage */ }
      for (const key of KEPT_FILES.keys()) if (key.startsWith(under)) paths.add(key.slice(under.length))
      return Array.from(paths)
    },
    async readText(path) {
      const kept = KEPT_FILES.get(under + path)
      if (typeof kept === 'string') return kept
      try { return localStorage.getItem(under + path) } catch (e) { return null }
    },
    async writeText(path, text) {
      try { localStorage.setItem(under + path, text); KEPT_FILES.delete(under + path) } catch (e) { memory(path, text, e) }
    },
    async readBytes(path) {
      const kept = KEPT_FILES.get(under + path)
      if (kept instanceof Uint8Array) return kept
      try { return (await inBytes('readonly', (st) => st.get(under + path))) || null } catch (e) { return null }
    },
    async writeBytes(path, bytes) {
      try { await inBytes('readwrite', (st) => st.put(bytes, under + path)); KEPT_FILES.delete(under + path) } catch (e) { memory(path, bytes, e) }
    },
  }
}

/** One scene's files: `all()` for the start, `text` and `bytes` for what Python writes. `storage`: a host's (see above). */
function sceneFiles(scene, storage) {
  const under = `pyctures:${scene}:file:`
  const own = browserFiles(under)
  const host = storage || {}
  const has = (name) => typeof host[name] === 'function'
  const use = (name) => (has(name) ? host[name].bind(host) : own[name])
  const noted = () => { try { return JSON.parse(localStorage.getItem(under) || '[]') } catch (e) { return [] } }
  const note = (path) => {
    try {
      const paths = noted()
      if (!paths.includes(path)) localStorage.setItem(under, JSON.stringify(paths.concat(path)))
    } catch (e) { /* no storage: it is known for this run only */ }
  }
  let warned = false
  const trouble = (path, e) => {
    if (!warned) console.warn(`${path}: the storage this scene was given failed (${(e && e.message) || e})`)
    warned = true
  }
  // Writes land in the order they were made, and a start waits for the last of them.
  let last = Promise.resolve()
  const write = (name, path, data) => {
    path = cleanPath(path)
    if (!path) return
    last = last.then(() => use(name)(path, data)).then(() => { if (has(name) && !has('list')) note(path) }, (e) => trouble(path, e))
  }
  return {
    /** Every file the scene has stored, as [{path, data}] (data: an ArrayBuffer of its own). */
    async all() {
      await last
      const paths = new Set()
      try {
        if (has('list')) for (const p of (await host.list()) || []) paths.add(cleanPath(p))
        // The browser's own, unless the host keeps everything.
        if (!has('list') || !has('writeText') || !has('writeBytes')) for (const p of (await own.list()).concat(has('list') ? [] : noted())) paths.add(p)
      } catch (e) { trouble('list()', e) }
      const out = []
      for (const path of paths) {
        if (!path) continue
        let data = null
        try { data = await use('readBytes')(path) } catch (e) { trouble(path, e) }
        if (data == null) {
          try {
            const text = await use('readText')(path)
            if (text != null) data = new TextEncoder().encode(String(text))
          } catch (e) { trouble(path, e) }
        }
        // A copy: a worker is GIVEN the buffer, and whoever kept the file must still have it.
        if (data != null) out.push({ path, data: new Uint8Array(data).slice().buffer })
      }
      return out
    },
    text(path, text) { write('writeText', path, text) },
    /** Whether a host keeps this scene's bytes as real files (its own writeBytes). */
    hostKeepsBytes: has('writeBytes'),
    /** Bytes as they are: a sound file the page's player made (save_sound). */
    raw(path, bytes) { write('writeBytes', path, bytes) },
    bytes(path, base64) {
      const bin = atob(base64)
      const bytes = new Uint8Array(bin.length)
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
      write('writeBytes', path, bytes)
    },
  }
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

// ---------------------------------------------------------------- what input a scene takes

/** The scene's Python without its comments and strings. */
const codeOf = (source) => source
  .replace(/("""|''')[\s\S]*?\1/g, '""')
  .replace(/(["'])(?:\\.|(?!\1)[^\\\n])*\1/g, '""')
  .replace(/#.*$/gm, '')

/**
 * What a scene takes from the pointer, from the names in its code. `wheel`: it
 * names the wheel (on_wheel, mouse.wheel), so the wheel is the scene's and the
 * page does not scroll under it. `pinch`: it names the pinch, so a trackpad's
 * pinch is the scene's and does not zoom the page. `pointer`: it uses the
 * pointer at all, so a drag stays the scene's when it leaves the canvas and a
 * right-click is a button, not a menu.
 */
export function inputOf(source) {
  const code = codeOf(source || '')
  const wheel = /\bon_wheel\b|\bmouse\s*\.\s*wheel\b/.test(code)
  const pinch = /(?:^|[^.\w])pinch\b|\bon_pinch\b/.test(code)
  const pointer = wheel || pinch || /\bmouse\b|\bon_mouse|(?:^|[^.\w])touches\b|\bon_touch|\badd(?:EventListener|_event_listener)\b|\bOrbitControls\b/.test(code)
  return { pointer, wheel, pinch }
}

/**
 * The renderer for one canvas. `input`: what the scene takes from the pointer (see inputOf). `images`: a function from a string in the
 * commands to the URL to use instead (see imageResolver), or null. `hooks`: onEvent(event), onSize(size),
 * onApplied({reads, errors, ms, n, timing}), onReads(reads) (a promise has
 * settled), isActive() (has the keyboard).
 */
export function createRenderer(canvas, { three = null, addons = null, images = null, input = null, saved = null, files = null, sound = null, dials = null, scenes = null, hooks }) {
  const H = new Map()
  let ctx2d = null
  let dpr = 1, cssW = 0, cssH = 0
  const reportedErrors = Object.create(null)
  // three.js objects that must follow the canvas's size: the renderer drawing
  // on this canvas, and every perspective camera.
  const glRenderers = [], cameras = []
  let timing = null
  let isGL = false
  const takes = input || { pointer: false, wheel: false, pinch: false }
  const pointersDown = new Set()

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
    if (h === 7) return 'the plain drawing functions'
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

  // INPUT IS REPORTED, NEVER ASKED FOR. Each event goes to Python with the next
  // frame, and the Python half keeps `keys`, `mouse`, `touches` and `pinch` from
  // them (pyctures/__init__.py, `_input`). `m` is the modifier keys held, as bits:
  // 1 Shift, 2 Control, 4 Alt, 8 Meta.
  const modifiers = (e) => (e.shiftKey ? 1 : 0) | (e.ctrlKey ? 2 : 0) | (e.altKey ? 4 : 0) | (e.metaKey ? 8 : 0)
  function sendInput(e) {
    const k = { type: e.type }
    if (e.type === 'keydown' || e.type === 'keyup') {
      if (!hooks.isActive()) return
      // A repeat of a held key is sent too: Python tells it from the press by the key being held (on_key_repeat).
      k.key = e.key; k.code = e.code; k.m = modifiers(e)
      if (e.repeat) k.r = 1
      if (e.key.indexOf('Arrow') === 0 || e.key === ' ') e.preventDefault()
    } else if (e.type === 'blur') {
      if (!hooks.isActive()) return
    } else if (e.type !== 'pointerleave') {
      if (e.type === 'pointerdown') {
        pointersDown.add(e.pointerId)
        canvas.focus({ preventScroll: true })
        // A drag that leaves the scene is still the scene's.
        if (takes.pointer) { try { canvas.setPointerCapture(e.pointerId) } catch (e2) { /* a pointer that has already gone */ } }
        k.m = modifiers(e)
      } else if (e.type === 'pointerup' || e.type === 'pointercancel') {
        if (!pointersDown.delete(e.pointerId)) return
      }
      const r = canvas.getBoundingClientRect()
      k.x = e.clientX - r.left; k.y = e.clientY - r.top; k.button = e.button
      k.id = e.pointerId; k.pt = e.pointerType
    }
    hooks.onEvent({ k: 'input', e: k })
  }
  // The wheel, for a scene that names it; a trackpad's pinch (the browser sends
  // it as ctrl + wheel, Safari as gesture events) for a scene that names that.
  // Under any other scene the wheel scrolls the page.
  function sendPinch(e, change) {
    const r = canvas.getBoundingClientRect()
    hooks.onEvent({ k: 'input', e: { type: 'pinch', change, x: e.clientX - r.left, y: e.clientY - r.top } })
  }
  function sendWheel(e) {
    if (e.ctrlKey && takes.pinch) {
      e.preventDefault()
      sendPinch(e, Math.exp(-Math.max(-50, Math.min(50, e.deltaY)) * 0.01))
    } else if (takes.wheel) {
      e.preventDefault()
      // In points: a wheel that counts in lines or pages is turned into them.
      const amount = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? cssH : 1)
      if (amount) hooks.onEvent({ k: 'input', e: { type: 'wheel', amount } })
    }
  }
  let gesture = 1
  function sendGesture(e) {
    e.preventDefault()
    if (e.type === 'gesturestart') { gesture = 1; return }
    if (pointersDown.size >= 2 || !(e.scale > 0)) return
    sendPinch(e, e.scale / gesture)
    gesture = e.scale
  }
  const noMenu = (e) => e.preventDefault()

  H.set(1, window); H.set(2, canvas)
  if (three) { H.set(3, three); H.set(5, addons) }
  // PLAIN DRAWING: Python's circle, rect, line, text, background and the rest. Each is ONE
  // command, done here in one go, so 2,000 circles are 2,000 commands and not 6,000. The rules
  // are those of pictures.js: what is given (a colour, a thickness, a size) is set on ctx and
  // stays. `how` is the shape's last argument, { outline, thickness } (Python's keyword
  // arguments): with a colour it is a border, without one it is the edge alone.
  function ctxFor(name) {
    const c = glRenderers.length ? null : getCtx()
    if (!c) throw new Error(name + '() draws on the 2D canvas, and this scene is 3D. Draw with THREE here')
    return c
  }
  function paint(c, colour, how) {
    if (how == null) {
      if (colour != null) c.fillStyle = colour
      c.fill()
      return
    }
    const edge = how.outline != null || how.thickness != null
    if (colour != null) c.fillStyle = colour
    if (colour != null || !edge) c.fill()
    if (edge) {
      if (how.outline != null && how.outline !== true) c.strokeStyle = how.outline
      if (how.thickness != null) c.lineWidth = how.thickness
      c.stroke()
    }
  }
  function corners(c, x, y, radius, n, inner) {
    c.beginPath()
    const step = Math.PI * 2 / n
    for (let i = 0; i < n; i++) {
      const r = inner && i % 2 ? inner : radius, a = i * step - Math.PI / 2
      c.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r)
    }
    c.closePath()
  }
  let fontSize = 0, fontOf = ''
  const stamps = new Map()
  const plainDrawing = {
    circle(x, y, radius, colour, how) {
      const c = ctxFor('circle')
      c.beginPath(); c.arc(x, y, radius, 0, Math.PI * 2)
      paint(c, colour, how)
    },
    ellipse(x, y, w, h, colour, how) {
      const c = ctxFor('ellipse')
      c.beginPath(); c.ellipse(x, y, Math.abs(w) / 2, Math.abs(h) / 2, 0, 0, Math.PI * 2)
      paint(c, colour, how)
    },
    rect(x, y, w, h, colour, how) {
      const c = ctxFor('rect')
      if (how == null) {
        if (colour != null) c.fillStyle = colour
        c.fillRect(x, y, w, h)
        return
      }
      c.beginPath()
      if (how.round) c.roundRect(x, y, w, h, how.round)
      else c.rect(x, y, w, h)
      paint(c, colour, how)
    },
    triangle(x1, y1, x2, y2, x3, y3, colour, how) {
      const c = ctxFor('triangle')
      c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.lineTo(x3, y3); c.closePath()
      paint(c, colour, how)
    },
    polygon(x, y, radius, sides, colour, how) {
      const c = ctxFor('polygon')
      corners(c, x, y, radius, Math.max(3, Math.round(sides)), 0)
      paint(c, colour, how)
    },
    star(x, y, radius, points, colour, how) {
      const c = ctxFor('star')
      corners(c, x, y, radius, Math.max(2, Math.round(points)) * 2, radius * (how && how.inner != null ? how.inner : 0.4))
      paint(c, colour, how)
    },
    line(x1, y1, x2, y2, colour, thickness) {
      const c = ctxFor('line')
      if (colour != null) c.strokeStyle = colour
      if (thickness != null) c.lineWidth = thickness
      c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke()
    },
    text(words, x, y, colour, size, align) {
      const c = ctxFor('text')
      if (colour != null) c.fillStyle = colour
      if (size != null) {
        if (size !== fontSize) { fontSize = size; fontOf = size + 'px system-ui, sans-serif' }
        c.font = fontOf
      }
      if (align != null) {
        const middle = align === 'centre' || align === 'center'
        c.textAlign = middle ? 'center' : align
        c.textBaseline = middle ? 'middle' : 'alphabetic'
      }
      c.fillText(String(words), x, y)
    },
    background(colour) {
      const c = ctxFor('background')
      if (colour == null) { c.clearRect(0, 0, cssW, cssH); return }
      const was = c.fillStyle
      c.fillStyle = colour; c.fillRect(0, 0, cssW, cssH); c.fillStyle = was
    },
    // An emoji or a word is drawn once into a small canvas and stamped from then on; an image
    // (Python sends a file's picture as the image it loaded) draws once it has arrived.
    picture(what, x, y, size) {
      const c = ctxFor('picture')
      if (typeof what === 'string') {
        const key = size + '|' + what
        let pic = stamps.get(key)
        if (!pic) {
          const px = Math.max(1, Math.round(size * 1.3 * dpr))
          pic = document.createElement('canvas')
          pic.width = pic.height = px
          const g = pic.getContext('2d')
          g.font = Math.floor(size * dpr) + 'px system-ui, sans-serif'
          g.textAlign = 'center'
          g.textBaseline = 'middle'
          g.fillText(what, px / 2, px / 2 + size * dpr * 0.06)
          stamps.set(key, pic)
        }
        const box = size * 1.3
        c.drawImage(pic, x - box / 2, y - box / 2, box, box)
        return
      }
      if (!what || what.complete === false || !what.naturalWidth) return
      const w = size * what.naturalWidth / what.naturalHeight
      c.drawImage(what, x - w / 2, y - size / 2, w, size)
    },
  }
  H.set(7, plainDrawing)
  // SAVED VALUES: Python's save(). With no keeper given, what is saved lasts for the run.
  H.set(8, { save: (name, kept) => { if (saved) saved.save(String(name), String(kept)) } })
  // FILES AND DATABASES: Python's save_text() and a database that changed. With no keeper given, they last for the run.
  H.set(9, {
    text: (path, text) => { if (files) files.text(String(path), String(text)) },
    bytes: (path, base64) => { if (files) files.bytes(String(path), String(base64)) },
  })
  // SOUND: Python's play_sound(), make_synth() and the rest (the library synths). A frame's sounds are ONE
  // command, send(batch). DIALS: Python's dial(), slider() and keyboard() (the library pydials). See soundKeeper.
  if (sound) H.set(10, sound)
  const panel = dials ? dials(canvas) : null
  if (panel) H.set(11, panel)
  // SCENES: a change of scene (see SCENES). `empty` is a scene starting with a clear canvas and the drawing settings as they start.
  if (scenes) {
    H.set(12, {
      // (A 2D canvas can be read at any time; a 3D one only straight after it is drawn on, so a slide keeps a copy then: see `applied`.)
      transition: (name, seconds, colour) => scenes.transition(name, seconds, colour, !!ctx2d && !isGL),
      show: (...args) => scenes.show(...args),
      empty() {
        if (!ctx2d || isGL) return
        if (typeof ctx2d.reset === 'function') ctx2d.reset()
        else canvas.width = canvas.width
        ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0)
      },
    })
  }
  window.addEventListener('keydown', sendInput)
  window.addEventListener('keyup', sendInput)
  window.addEventListener('blur', sendInput)
  canvas.addEventListener('pointerdown', sendInput)
  canvas.addEventListener('pointermove', sendInput)
  canvas.addEventListener('pointerleave', sendInput)
  window.addEventListener('pointerup', sendInput)
  window.addEventListener('pointercancel', sendInput)
  if (takes.wheel || takes.pinch) canvas.addEventListener('wheel', sendWheel, { passive: false })
  if (takes.pinch) {
    canvas.addEventListener('gesturestart', sendGesture)
    canvas.addEventListener('gesturechange', sendGesture)
  }
  if (takes.pointer) canvas.addEventListener('contextmenu', noMenu)

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
      // A frame's sounds are heard now, not when the frame is drawn: they are timed, and waiting for a refresh
      // (or two, in the queue) would use up the moment the player has to place them exactly.
      if (sound && cmds) {
        for (let i = 0; i < cmds.length; i++) {
          const c = cmds[i]
          if (c[3] === 10 && c[0] === 'call' && c[4] === 'send') { sound.send(c[5][0]); cmds[i] = NOTHING_TO_DO }
        }
      }
      // Not a file's own text: that is the scene's to keep as it wrote it.
      if (images && cmds) swapStrings(cmds.some((c) => c[0] === 'call' && c[3] === 9) ? cmds.filter((c) => !(c[0] === 'call' && c[3] === 9)) : cmds, images)
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
      window.removeEventListener('blur', sendInput)
      window.removeEventListener('pointerup', sendInput)
      window.removeEventListener('pointercancel', sendInput)
      for (const g of glRenderers) { try { g.dispose() } catch (e) { /* already gone */ } }
      if (panel) panel.close()
      H.clear()
    },
  }
}

// ---------------------------------------------------------------- sound and dials

/** A command that does nothing: what a frame's sounds leave in their place once they have been sent on. */
// ---------------------------------------------------------------- scenes
//
// SCENES: a Python file in several scenes (`class Title(Scene)`, `go("game")`). It is a library, loaded only
// for a file that names a scene (LIBRARIES, `pyscenes`): the page's half is scenes/scenes.js, which runs each
// transition on a layer over the canvas and shows the scrubber, as the fixed handle 12. A page with it says
// so in the start info (`scenes`), and Python sends nothing to a page without. See scenes/scenes.js.

const NOTHING_TO_DO = ['free', 0, 0]

/** Does the scene import a library (`from synths import *`, `import pydials`)? Python's pages.uses_library makes the same test. */
export function usesLibrary(source, name) {
  const lib = LIBRARIES[name]
  if (lib && lib.uses) return lib.uses.test(source || '')
  return new RegExp('^[ \\t]*(?:from|import)[ \\t]+' + name + '\\b', 'm').test(source || '')
}

/**
 * The libraries a scene asks for by importing them: the name it imports -> the folder beside this file, the
 * page's half and the Python half. Python's pages.LIBRARIES is the same table.
 */
export const LIBRARIES = {
  synths: { folder: 'synths', js: 'synths.js', py: 'synths.py' },
  pydials: { folder: 'dials', js: 'dials.js', py: 'pydials.py' },
  // Scenes are not imported: a file that names one (a class with Scene in its brackets, or a call of scene(), go(),
  // next_scene(), config() or section()) is given them. Python asks the same of the same text (_USES_SCENES), and so does `pyctures build`.
  pyscenes: { folder: 'scenes', js: 'scenes.js', py: 'pyscenes.py', uses: /(?:^|[^.\w])(?:Scene\b|(?:scene|go|next_scene|config|section)[ \t]*\()/m },
}

const libraries = {}
/**
 * The page's half of a library (`name`: what a scene imports, `synths` or `pydials`), as a module: from a host (`given`: the module itself, a
 * promise of it, or its address), from inside a single-file page, or from the folder beside this file. It is
 * loaded once, and only when a scene needs it.
 */
function loadLibrary(name, given) {
  if (given && typeof given !== 'string') return Promise.resolve(given)
  if (!libraries[name]) {
    const inl = inline(), { folder, js } = LIBRARIES[name]
    const packed = !given && inl && inl[folder] && inl[folder].js
    // A module made from text has no address of its own for the files beside it: it is given the page's
    // (the engine and the worklet are handed to it, so nothing is looked for there).
    const url = given ? new URL(given, document.baseURI).href
      : packed ? URL.createObjectURL(new Blob([packed.split("new URL('./', import.meta.url)").join("new URL('./', document.baseURI)")], { type: 'text/javascript' }))
        : new URL(`${folder}/${js}`, BASE).href
    libraries[name] = import(url)
    libraries[name].catch(() => { delete libraries[name] })
  }
  return libraries[name]
}

const libraryTexts = {}
/** The Python half of a library as text, for a browser's Python: from a single-file page, or beside this file. */
function loadLibraryPython(name) {
  if (!libraryTexts[name]) {
    const inl = inline(), { folder, py } = LIBRARIES[name]
    libraryTexts[name] = inl && inl[folder] && inl[folder].py ? Promise.resolve(inl[folder].py)
      : fetch(new URL(`${folder}/${py}`, BASE)).then((r) => {
        if (!r.ok) throw new Error(`${py} was not found beside pyctures.js (in ${folder}/)`)
        return r.text()
      })
    libraryTexts[name].catch(() => { delete libraryTexts[name] })
  }
  return libraryTexts[name]
}

/** {name: Python source} for each library the scene, or a .py file that comes with it, imports. */
async function pythonLibraries(source, files) {
  const texts = [source]
  for (const f of files || []) if (/\.py$/i.test(f.path)) texts.push(new TextDecoder().decode(f.data))
  const out = {}
  for (const name in LIBRARIES) if (texts.some((t) => usesLibrary(t, name))) out[name] = await loadLibraryPython(name)
  return out
}

// ONE PLAYER FOR THE PAGE. Every scene on a page shares one sound card and one engine, each in a scope of its
// own (its own ids, pause and stop): { player, users, made, heard: the scenes to tell of its state }.
let pagePlayer = null
let soundScopes = 0

const base64Bytes = (text) => Uint8Array.from(atob(text), (ch) => ch.charCodeAt(0))
const nameKey = (name) => String(name).toLowerCase().replace(/[_.\s-]/g, '')
const SOUND_UNITS = { hz: 'Hz', seconds: 's', semitones: 'st', cents: 'ct', octaves: 'oct' }
const NO_READING = { samples: [], level: [0, 0], notes: [] }

/**
 * SOUND: the page's end of Python's `synths` (handle 10). Python never makes a sound: it writes commands
 * in the format of synths.js (`synths/synths.js` beside this file, whose docs/commands.md is the contract)
 * and a frame's commands arrive together as one call, `send(batch)`. A player made here by synths.js carries
 * them out, on the audio thread.
 *
 * TIME. Each command carries when it was asked for on PYTHON's clock, which may be another computer's. The
 * batch's `now` is that clock when the frame was sent, so the shortest journey seen is the difference between
 * the two clocks; every command is moved onto the PAGE's clock (performance.now() / 1000) before it goes on.
 * So the player, or a host, sees one clock, whether a command came from Python or from a key on the page.
 *
 * A SCOPE. Every batch names the scene it is from (`scope`), because the scenes of a page share one player and
 * each chooses its own ids: two scenes may both have a synth "s1". A scene out of view is paused in its scope,
 * and a scene that stops closes it.
 *
 * `synth(id)` is the page's own object for one of Python's synths, with what dials.js looks for in a
 * target: set, get, describe, onChange, noteOn, noteOff, samples, level and notes. A dial or a piano key in the page
 * acts on it here, at once, and Python is only told afterwards. `output()` is the same for all the sound.
 *
 * `host` is the `sound` option of mount(), from an app that shows scenes; every part of it is optional:
 *   send(batch)       take the commands and play them somewhere else. Nothing is played or loaded here
 *   read(id, scope)   with send: what a synth is doing, { samples, level, notes }, for scopes and meters
 *   synths            synths.js itself: the module, a promise of it, or its address (a page that may not fetch)
 *   wasm, worklet     the engine's bytes and how its worklet is loaded: createPlayer's options of those names
 *   latency           seconds everything is played ahead: createPlayer's
 *   onState(state)    told 'waiting' (for a tap), 'on' or 'failed'
 *   onMidi(listener, scope)   with send: where the host's own player hands back what MIDI received (its onMidi)
 *
 * MIDI (synths.js's docs/midi.md) rides the same batches as `midi` commands, and the player's desk carries them
 * out here, where the devices are: a keyboard plays a synth (`play`) and a knob turns a setting (`map`, `learn`)
 * with Python not asked, so both are immediate however slow or far away Python is. What the desk hands back goes
 * to Python with the next frame (`midi(fn)`, which Python's synths calls once), each event's `time` moved onto
 * Python's clock; a setting a knob turned is remembered here first, so a dial tied to it turns with the knob.
 * `midi` is the `midi` option of mount(): a host's own MIDI transport for a browser that has none (an iPad),
 * or false for no MIDI. synths-midi.js is fetched by synths.js when the first `midi` command arrives.
 *
 * THE MICROPHONE, RECORDING AND SAVING (synths.js's docs/microphone.md) are `mic`, `record` and `save` commands in
 * the same batches. The player opens the microphone when the first `mic` command arrives, which is when the
 * browser asks the person; `microphone` (mount()'s option, or the host's) is a host's own stream or pushed frames
 * where the page cannot ask, or false for none. What the player says back (the microphone is on or is not, a
 * recording is over, a file is saved) goes to Python with the next frame, as MIDI does: `events(fn)`, which
 * Python's synths calls once, is handed { sound: a list of events as JSON text }.
 *   A SAVED FILE goes, in this order: to Python, as base64 in the `saved` event, when the command says
 *   `download: false` (Python run by `pyctures run` writes it beside the scene); to `save` (mount()'s option or the
 *   host's), called with { name, bytes, type }; to the scene's files, when the host's `storage` has writeBytes;
 *   and otherwise the player downloads it.
 *
 * READING BACK. Python cannot ask and be answered, so it says what it wants watched: `watch(id)` (no id: all the
 * sound) and `watchSong()`. From then on each frame's message carries what that synth is doing, { type: 'reading',
 * id, samples, level, notes }, and where the song is, { type: 'position', … }, through the same `events(fn)`,
 * until Python has not asked again for a second and a half. So Python's lead.samples() is a frame late.
 *
 * synths.js is loaded when the first sound is asked for, or before the scene starts when its source imports
 * `synths` (`module`). A scene that makes no sound loads nothing.
 */
function soundKeeper({ host = null, src = '', module = null, onState = null, midi = undefined, microphone = undefined, save = undefined, files = null }) {
  host = host || {}
  const clock = () => performance.now() / 1000
  const elsewhere = typeof host.send === 'function'
  const scope = 'scene' + ++soundScopes
  const hear = (now) => { state = now; if (onState) onState(now); if (host.onState) host.onState(now) }
  let mod = module, player = null, loading = null, closed = false, paused = false
  let offset = null, last = 0, used = false
  let held = []                // batches that came before synths.js had loaded
  const synths = new Map()     // id -> { preset, set: [[name, value]…] }: what has been asked of each synth
  const shared = []            // [[name, value]…] the settings every synth shares
  let volume = 1, table = null
  const midiHeard = new Set()  // Python's listeners for what MIDI received
  let midiLeave = null, devicesSaid = null
  const soundHeard = new Set() // Python's listeners for what the player says back, and for what is watched
  let soundLeave = null, soundKept = [], micSaid = null, micAsked = false, state = ''
  const saving = new Map()     // the number of a save -> 'python' (it is given the bytes), or a function that keeps the file
  const watched = new Map()    // what Python reads back: a synth's id ('' for all the sound, 'song' for its place) -> until when
  const mics = new Set()       // the ids that are the microphone
  const keep = save !== undefined ? save : host.save

  // What the desk says for this scene, as a list of plain objects. Python is handed it as JSON text, which
  // reaches it whole with the next frame.
  function hearMidi(events) {
    const list = []
    for (const e of Array.isArray(events) ? events : [events]) {
      if (!e || typeof e !== 'object') continue
      // A knob turned a setting here, on the page: remembered, so a dial tied to it turns too.
      if (e.type === 'set') remember({ op: 'set', id: e.id, set: { [e.setting]: e.value } })
      const m = typeof e.time === 'number' && offset !== null ? { ...e, time: e.time - offset } : e
      if (e.type === 'devices') devicesSaid = m
      list.push(m)
    }
    if (!list.length || !midiHeard.size || closed) return
    const told = { midi: JSON.stringify(list) }
    for (const fn of midiHeard) fn(told)
  }
  const joinMidi = (from) => { if (!midiLeave && from && typeof from.onMidi === 'function') midiLeave = from.onMidi(hearMidi, scope) || (() => {}) }
  if (elsewhere) joinMidi(host)

  // What the player says back for this scene. A saved file is kept where it belongs, and Python is told of it
  // without the bytes unless it asked for them.
  const base64Of = (bytes) => { let s = ''; for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000)); return btoa(s) }
  function tellSound(list) {
    if (!list.length || closed) return
    if (!soundHeard.size) { soundKept.push(...list); return }
    const told = { sound: JSON.stringify(list) }
    for (const fn of soundHeard) fn(told)
  }
  function hearSound(events) {
    const list = []
    for (const e of Array.isArray(events) ? events : [events]) {
      if (!e || typeof e !== 'object') continue
      if (e.type === 'microphone') micSaid = e
      if (e.type === 'saved') {
        const { bytes, ...rest } = e
        const to = saving.get(e.ask)
        saving.delete(e.ask)
        const data = bytes ? (bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes)) : null
        if (to === 'python' && data) rest.bytes = base64Of(data)
        else if (typeof to === 'function' && data) { try { to({ name: e.name, bytes: data, type: 'audio/wav' }) } catch (err) { console.warn(`${e.name} could not be saved (${(err && err.message) || err})`) } }
        list.push(rest)
      } else list.push(e)
    }
    tellSound(list)
  }
  const joinSound = (from) => { if (!soundLeave && from && typeof from.onSoundEvents === 'function') soundLeave = from.onSoundEvents(hearSound, scope) || (() => {}) }
  if (elsewhere) joinSound(host)
  // Where a file that save_sound made goes when Python did not ask for it: see A SAVED FILE.
  const keeper = () => (typeof keep === 'function' ? keep : files && files.hostKeepsBytes ? (file) => files.raw(file.name, file.bytes) : null)

  function load() {
    if (!loading) {
      loading = loadLibrary('synths', host.synths).then((m) => {
        mod = m
        const waited = held
        held = []
        for (const batch of waited) out(batch)
      }, (e) => { console.error('Sound could not load: ' + ((e && e.message) || e)) })
    }
    return loading
  }

  function makePlayer() {
    if (!pagePlayer || pagePlayer.player.state === 'closed' || pagePlayer.player.state === 'failed') {
      // The first scene to make a sound makes the player, with what its host gave it.
      const inl = inline()
      const packed = inl && inl.synths && inl.synths.wasm
      const mine = pagePlayer = { player: null, users: 0, heard: new Set() }
      const options = { onState: (state) => { for (const tell of mine.heard) tell(state) } }
      if (host.wasm) options.wasm = host.wasm
      else if (packed) { options.wasm = base64Bytes(packed); options.worklet = 'blob' }
      if (host.worklet) options.worklet = host.worklet
      if (host.latency != null) options.latency = host.latency
      // MIDI: a host's own transport, and for a single-file page synths-midi.js from inside it.
      const transport = midi !== undefined ? midi : host.midi
      if (transport !== undefined) options.midi = transport
      if (host.midiSysex) options.midiSysex = true
      // The microphone: a host's own stream or pushed frames, or false for none. Without it the browser is asked.
      const mic = microphone !== undefined ? microphone : host.microphone
      if (mic !== undefined) options.microphone = mic
      if (host.midiModule) options.midiModule = host.midiModule
      else if (inl && inl.synths && inl.synths.midi) options.midiModule = URL.createObjectURL(new Blob([inl.synths.midi], { type: 'text/javascript' }))
      mine.player = mod.createPlayer(options)
    }
    pagePlayer.users++
    pagePlayer.heard.add(hear)
    player = pagePlayer.player
    joinMidi(player)
    joinSound(player)
    if (player.state === 'waiting' || player.state === 'on') hear(player.state)
    if (paused) quiet(true)
  }
  // This scene alone goes quiet, or comes back, with everything kept as it is.
  const quiet = (on) => { const t = clock(); out({ synths: 1, scope, now: t, cmds: [{ op: 'master', pause: on, t }] }) }

  // A batch, on the page's clock, to whoever plays it.
  function out(batch) {
    if (closed) return
    used = true
    if (elsewhere) { host.send(batch); return }
    if (!mod) { held.push(batch); load(); return }
    if (!player) makePlayer()
    player.send(batch)
  }
  // One command from the page itself (a key, a dial), now.
  const own = (c) => { c.t = clock(); remember(c); out({ synths: 1, scope, now: c.t, cmds: [c] }) }

  function remember(c) {
    if (c.op === 'synth') {
      const had = sampled(c.id)
      synths.set(c.id, { preset: c.preset || null, set: [] })
      if (c.voice != null) wear(c.id, c.voice)
      synths.get(c.id).set.push(...Object.entries(c.set || {}))
      if (sampled(c.id) !== had) changed(c.id)
    } else if (c.op === 'set' && (c.set || c.voice != null || c.arpPattern !== undefined || c.tranceGate !== undefined)) {
      const had = sampled(c.id)
      if (!synths.has(c.id)) synths.set(c.id, { preset: 'keys', set: [] })
      if (c.voice != null) wear(c.id, c.voice)
      if (c.set) synths.get(c.id).set.push(...Object.entries(c.set))
      // Its two patterns, each kept as its text. Given a trance gate the depth is made 1 unless it has one, and
      // with the gate taken away it is 0, as the player makes it (synths.js docs/commands.md, `set`).
      for (const which of PATTERNS) {
        if (c[which] === undefined) continue
        const mine = synths.get(c.id), text = patternText(which, c[which])
        mine.patterns = { ...mine.patterns, [which]: text }
        if (which === 'tranceGate') { if (!text) mine.set.push(['gate.depth', 0]); else if (!(valueOf(listsOf(c.id), 'gate.depth') > 0)) mine.set.push(['gate.depth', 1]) }
      }
      if (sampled(c.id) !== had) changed(c.id)
    } else if (c.op === 'zones') {
      // Several recordings as one instrument (load_samples): they are the sample its wave plays.
      const had = sampled(c.id)
      if (!synths.has(c.id)) synths.set(c.id, { preset: 'keys', set: [] })
      synths.get(c.id).zones = !!c.zones
      if (sampled(c.id) !== had) changed(c.id)
    } else if (c.op === 'mic') {
      // The microphone is a synth by its id, which starts with nothing set: it comes through untouched.
      if (c.do === 'close') { mics.delete(c.id); return }
      if (!mics.has(c.id) || !synths.has(c.id)) synths.set(c.id, { preset: null, set: [], mic: true })
      mics.add(c.id)
      if (!micAsked) { micAsked = true; if (state === 'waiting') hear(state) }
      const mine = synths.get(c.id)
      if (c.voice != null) wear(c.id, c.voice)
      if (c.set) mine.set.push(...Object.entries(c.set))
      if (c.listen != null) mine.listening = !!c.listen
    } else if (c.op === 'save' && !elsewhere) {
      // A file: Python's when it asked for the bytes, else this scene's to keep, else the player's to download.
      if (c.download === false) saving.set(c.ask, 'python')
      else if (keeper()) { saving.set(c.ask, keeper()); c.download = false }
    } else if (c.op === 'save' && c.download === false) saving.set(c.ask, 'python')
    else if (c.op === 'master') {
      if (typeof c.volume === 'number') volume = c.volume
      if (c.set) shared.push(...Object.entries(c.set))
    }
  }

  // A file a sample or a song names is beside the scene, wherever the page is.
  const beside = (path) => { try { return new URL(path, new URL(src || '', document.baseURI)).href } catch (e) { return path } }

  // The settings as synths.js describes them: nameKey(any way of writing a name) -> { the engine's entry, scale }.
  function settings() {
    if (!table && mod && mod.describe) {
      const d = mod.describe(), byName = new Map()
      table = { names: new Map(), synths: d.synths || {}, plain: d.plain || {}, words: d.choiceWords || {}, voices: {}, voiced: [], mic: (d.microphone && d.microphone.names) || {},
        patterns: { arpPattern: (d.arp && d.arp.patternSteps) || {}, tranceGate: (d.tranceGate && d.tranceGate.patterns) || {} } }
      for (const name in d.voices || {}) {
        table.voices[name] = d.voices[name].values || {}
        for (const setting in table.voices[name]) if (!table.voiced.includes(setting)) table.voiced.push(setting)
      }
      for (const entry of d.settings || []) { byName.set(entry.name, entry); table.names.set(nameKey(entry.name), { entry, scale: 1 }) }
      for (const alias in d.names || {}) {
        const entry = byName.get(d.names[alias].setting)
        if (entry) table.names.set(nameKey(alias), { entry, scale: d.names[alias].scale || 1 })
      }
    }
    if (!mod) load()
    return table
  }
  // The last value given for a setting in a list of [name, value], in the engine's own measure; undefined if none was.
  function lastOf(list, entry) {
    let found
    for (const [name, value] of list) {
      const at = table.names.get(nameKey(name))
      if (!at || at.entry !== entry) continue
      if (typeof value === 'number') found = value * at.scale
      else if (typeof value === 'boolean') found = value ? 1 : 0
      else if (typeof value === 'string' && entry.choices) {
        const word = value.toLowerCase().trim()
        const i = entry.choices.indexOf(entry.choices.includes(word) ? word : table.words[word])
        if (i >= 0) found = i
      }
    }
    return found
  }
  function valueOf(lists, name) {
    const t = settings(), at = t && t.names.get(nameKey(name))
    if (!at) return undefined
    let value
    for (const list of lists) { const v = lastOf(list, at.entry); if (v !== undefined) value = v }
    if (value === undefined) value = at.entry.default
    value = Math.min(at.entry.max, Math.max(at.entry.min, value))
    return at.entry.kind === 'choice' ? at.entry.choices[value] : at.entry.kind === 'bool' ? value === 1 : value / at.scale
  }
  function describe(name, whose) {
    const t = settings(), at = t && t.names.get(nameKey(name))
    if (!at || (whose && at.entry.scope !== whose)) return null
    const { entry, scale } = at
    const d = { name: String(name), kind: entry.kind, min: entry.min / scale, max: entry.max / scale, default: entry.default / scale }
    const unit = SOUND_UNITS[scale === 12 ? 'octaves' : entry.unit]
    if (unit) d.unit = unit
    // A time from nothing to twenty seconds is turned evenly by how much longer it gets, from a thousandth of a second:
    // half the dial is then the short times that an attack or a release is nearly always set to.
    if (entry.unit === 'seconds' && entry.min === 0 && entry.max >= 1) { d.min = 0.001; d.log = true }
    if (entry.choices) {
      d.choices = [...entry.choices]; d.default = entry.default
      // Other words for a choice ("square" is "pulse"), so a control follows a wave set by either name.
      const aliases = { ...entry.aliases }
      for (const word in t.words) if (entry.choices.includes(t.words[word]) && !entry.choices.includes(word)) aliases[word] = t.words[word]
      if (Object.keys(aliases).length) d.aliases = aliases
    }
    // What the library says of how a value is shown is passed on: words for particular values (in the name's own measure), and a way to write it.
    if (entry.labels) {
      d.labels = {}
      for (const at in entry.labels) d.labels[Number(at) / scale] = entry.labels[at]
      // Where nothing is one of them (a reverb_decay of 0 is "auto"), the dial still starts from nothing.
      if (d.log && 0 in d.labels) { d.min = 0; d.logFrom = 0.001 }
    }
    if (typeof entry.format === 'function') d.format = entry.format
    return d
  }
  // "sample" is a wave only for a synth that has been given a sample to play: synths.js's rule (its makeTarget), kept
  // here because a control asks before there is a player. `wave`: the engine's name for an oscillator's wave.
  const WAVES = ['osc1.wave', 'osc2.wave']
  function hasSample(id, wave) {
    const mine = synths.get(id), holds = wave.replace('wave', 'sample')
    if (!table || !mine) return false
    if (mine.zones && wave === WAVES[0]) return true
    return mine.set.some(([name, value]) => { const at = table.names.get(nameKey(name)); return !!at && at.entry.name === holds && value != null })
  }
  const sampled = (id) => WAVES.map((wave) => hasSample(id, wave)).join()
  function describeFor(id, name) {
    const d = describe(name), at = d && d.choices && table.names.get(nameKey(name))
    if (!at || !WAVES.includes(at.entry.name) || hasSample(id, at.entry.name)) return d
    d.choices = d.choices.filter((c) => c !== 'sample')
    d.max = d.choices.length - 1
    return d
  }
  // A control tied to a synth is told when what describe says of a setting has changed (dials.js's onChange).
  const heeding = new Map()    // id -> the functions to call
  const changed = (id) => { for (const fn of heeding.get(id) || []) { try { fn() } catch (e) { console.error(e) } } }
  // A synth's two patterns (its arpeggios' and its trance gate's), by the names a set command carries them under.
  const PATTERNS = ['arpPattern', 'tranceGate']
  const patternOf = (name) => PATTERNS.find((which) => nameKey(which) === nameKey(name))
  // A pattern as its text: a built-in one by its name, a list of steps joined as the library joins them, '' for none.
  function patternText(which, given) {
    if (Array.isArray(given)) given = which === 'arpPattern' ? given.map((step) => (step === 0 || step == null ? '-' : String(step).trim())).join(' ') : given.map((v) => (v >= 1 ? 'x' : v <= 0 ? '.' : String(Math.round(v * 9)))).join('')
    const text = typeof given === 'string' ? (which === 'arpPattern' ? given.trim().replace(/\s+/g, ' ') : given.replace(/\s+/g, '').toLowerCase()) : ''
    if (['', 'off', 'none'].includes(text.toLowerCase())) return ''
    const named = table && table.patterns[which][text.toLowerCase()]
    return named || text
  }
  // What a control is told a pattern is, as synths.js's own describe says it: its text, the built-in ones, and its name if it is one.
  function describePattern(id, which) {
    const text = ((synths.get(id) || {}).patterns || {})[which] || '', all = (settings() || { patterns: {} }).patterns[which] || {}
    const named = text ? Object.keys(all).find((name) => all[name] === text) : undefined
    return { name: which, kind: 'pattern', default: '', value: text, steps: 32, patterns: { ...all }, ...(named ? { named } : {}) }
  }
  const reading = (id) => (player && player.read ? player.read(id, scope) : elsewhere && typeof host.read === 'function' ? host.read(id, scope) : null) || NO_READING

  // What has been asked of a synth, oldest first: the plain settings, its ready-made synth's, and its own.
  const listsOf = (id) => {
    const t = settings(), mine = synths.get(id)
    return !t ? [] : mine && mine.mic ? [mine.set] : [Object.entries(t.plain), Object.entries((mine && t.synths[mine.preset]) || {}), mine ? mine.set : []]
  }
  // A VOICE is put on as the player puts it on (synths.js's wearVoice; the rule is in its docs/commands.md under
  // `set`), so what a dial reads after `mic.voice = "robot"` is what the engine has: the first voice remembers what
  // its settings were, each one after puts those back before its own, and "none" forgets them.
  function wear(id, voice) {
    const t = settings(), mine = synths.get(id)
    if (!mine) return
    const last = mine.voice || 'none'
    mine.voice = voice
    if (!t) return
    const row = t.voices[voice] || {}, was = t.voices[last] || {}
    const raw = (name, lists) => { const at = t.names.get(nameKey(name)); let v; if (at) for (const list of lists) { const x = lastOf(list, at.entry); if (x !== undefined) v = x } return v }
    const whole = (name) => { const at = t.names.get(nameKey(name)); return !!at && at.entry.scope === 'all' }
    if (!mine.under) {
      mine.under = {}
      for (const name of t.voiced) { const v = raw(name, whole(name) ? [shared] : listsOf(id)); if (v !== undefined) mine.under[name] = v }
    }
    for (const name of t.voiced) {
      const at = t.names.get(nameKey(name))
      if (!at || (whole(name) && !(name in row) && !(name in was))) continue
      const value = name in row ? row[name] : name in mine.under ? mine.under[name] : at.entry.default
      ;(whole(name) ? shared : mine.set).push([name, value])
    }
    if (voice === 'none') mine.under = null
  }

  function synth(id) {
    const lists = () => listsOf(id)
    const isMic = () => mics.has(id)
    // The microphone's settings go by its own names (its `pitch` is the pitch shifter).
    const named = (name) => { const t = isMic() && settings(); const to = t && t.mic[nameKey(name)]; return to || name }
    const voices = () => { const t = settings(); return ['none', ...(t ? Object.keys(t.voices) : [])] }
    const special = (name) => { const k = nameKey(name); return k === 'voice' || (k === 'listening' && isMic()) ? k : '' }
    return {
      id,
      describe: (name) => (special(name) === 'voice' ? { name: 'voice', kind: 'choice', min: 0, max: voices().length - 1, default: 'none', choices: voices() }
        : special(name) === 'listening' ? { name: 'listening', kind: 'bool', min: 0, max: 1, default: false }
        : patternOf(name) ? describePattern(id, patternOf(name)) : describeFor(id, named(name))),
      onChange: (fn) => {
        if (typeof fn !== 'function') return null
        if (!heeding.has(id)) heeding.set(id, new Set())
        heeding.get(id).add(fn)
        return () => { const all = heeding.get(id); if (all) all.delete(fn) }
      },
      get: (name) => (special(name) === 'voice' ? (synths.get(id) || {}).voice || 'none' : special(name) === 'listening' ? !!(synths.get(id) || {}).listening
        : patternOf(name) ? ((synths.get(id) || {}).patterns || {})[patternOf(name)] || ''
        : nameKey(name) === 'arpstep' ? reading(id).arpStep ?? -1 : nameKey(name) === 'trancegatestep' ? reading(id).tranceGateStep ?? -1
        : valueOf(lists(), named(name))),
      set: (name, value) => {
        // A control gives a choice as its number in the list, and a switch as 1 or 0.
        if (special(name) === 'voice') return own({ op: 'set', id, voice: typeof value === 'number' ? voices()[value] || 'none' : String(value) })
        if (special(name) === 'listening') return own({ op: 'mic', id, listen: value === true || value === 1 || value === 'on' })
        if (patternOf(name)) return own({ op: 'set', id, [patternOf(name)]: patternText(patternOf(name), value) })
        const set = { [named(name)]: value }
        if (isMic()) {
          const k = nameKey(name)
          if (k === 'gate' && (value === false || value === 'off' || value === null)) set[named(name)] = -100
          // The microphone starts with no filter. Turning the cutoff asks for one.
          if ((k === 'cutoff' || k === 'resonance') && valueOf(lists(), 'filter') === 'off') set.filter = 'lowpass'
        }
        return own({ op: 'set', id, set })
      },
      noteOn: (note, velocity = 0.8) => own({ op: 'note', id, note: [note], len: null, vel: velocity }),
      noteOff: (note) => own({ op: 'off', id, note: [note] }),
      samples: () => reading(id).samples,
      level: () => reading(id).level,
      notes: () => reading(id).notes,
    }
  }

  return {
    /** A frame's sounds from Python: { synths: 1, now, cmds }. */
    send(batch) {
      if (closed || !batch || !Array.isArray(batch.cmds)) return
      const here = clock()
      if (typeof batch.now === 'number') {
        // The shortest journey seen is how far apart the two clocks are; it may creep up half a millisecond a second.
        const seen = here - batch.now
        offset = offset === null ? seen : Math.min(seen, offset + 0.0005 * Math.max(0, here - last))
        last = here
      }
      for (const c of batch.cmds) {
        if (!c) continue
        c.t = offset === null ? here : (typeof c.t === 'number' ? c.t : batch.now) + offset
        if (typeof c.url === 'string') c.url = beside(c.url)
        remember(c)
      }
      out({ synths: batch.synths || 1, scope, now: here, cmds: batch.cmds })
    },
    synth,
    /** Python asks for what MIDI devices send and what the desk says: fn({ midi: a list of events as JSON text }). */
    midi(fn) {
      if (typeof fn !== 'function') return
      midiHeard.add(fn)
      if (devicesSaid) fn({ midi: JSON.stringify([devicesSaid]) })
    },
    /** Python asks for what the player says back, and for what it watches: fn({ sound: a list of events as JSON text }). */
    events(fn) {
      if (typeof fn !== 'function') return
      soundHeard.add(fn)
      const kept = soundKept.length ? soundKept : micSaid ? [micSaid] : []
      soundKept = []
      if (kept.length) fn({ sound: JSON.stringify(kept) })
    },
    /** Python reads a synth back (no id: all the sound): said with every frame until it has not asked for a second and a half. */
    watch(id) { watched.set(typeof id === 'string' ? id : '', clock() + 1.5) },
    watchSong() { watched.set('song\u0001', clock() + 1.5) },
    /** Called as a frame is about to be asked of Python: what is watched goes with it. */
    frame() {
      if (!watched.size || closed) return
      const now = clock(), list = []
      for (const [id, until] of watched) {
        if (until < now) { watched.delete(id); continue }
        if (id === 'song\u0001') {
          const from = player && player.songPosition ? player : elsewhere && typeof host.songPosition === 'function' ? host : null
          if (from) list.push({ type: 'position', ...from.songPosition() })
          continue
        }
        const r = reading(id || undefined), samples = new Array(r.samples.length)
        for (let i = 0; i < samples.length; i++) samples[i] = Math.round(r.samples[i] * 1000) / 1000
        list.push({ type: 'reading', id: id || null, samples, level: [r.level[0] || 0, r.level[1] || 0], notes: Array.from(r.notes || []), arpStep: r.arpStep ?? -1, tranceGateStep: r.tranceGateStep ?? -1 })
      }
      tellSound(list)
    },
    /** Whether the scene has asked for the microphone. */
    get microphone() { return micAsked },
    /** What a synth is doing now, { samples, level: [left, right], notes }; with no id, all of this scene's sound and everyone's. */
    read: reading,
    scope,
    /** All the sound together: its volume and the shared effects to set, and what it is doing to read. */
    output: () => ({
      describe: (name) => (nameKey(name) === 'volume' ? { name: 'volume', kind: 'float', min: 0, max: 2, default: 1 } : describe(name, 'all')),
      get: (name) => (nameKey(name) === 'volume' ? volume : valueOf([shared], name)),
      set: (name, value) => own(nameKey(name) === 'volume' ? { op: 'master', volume: value } : { op: 'master', set: { [name]: value } }),
      samples: () => reading().samples,
      level: () => reading().level,
      notes: () => reading().notes,
    }),
    /** The player, once a sound has been asked for (null when a host takes the commands). */
    get player() { return player },
    /** Silence while the scene is out of view, with everything kept as it is. */
    pause() { if (!paused && used) quiet(true); paused = true },
    resume() { if (paused && used) quiet(false); paused = false },
    close() {
      if (closed) return
      // Everything of this scene is stopped and forgotten; the player goes when its last scene does.
      if (used) out({ synths: 1, scope, now: clock(), cmds: [{ op: 'close', t: clock() }] })
      closed = true
      if (midiLeave) midiLeave()
      midiHeard.clear()
      if (soundLeave) soundLeave()
      soundHeard.clear()
      if (player && pagePlayer && pagePlayer.player === player) {
        pagePlayer.heard.delete(hear)
        if (--pagePlayer.users <= 0) { player.close(); pagePlayer = null }
      }
    },
  }
}

/**
 * DIALS: the page's end of Python's `pydials` (handle 11): dials, sliders, a piano keyboard, a scope and
 * meters, drawn over the scene by `dials/dials.js` beside this file. Python makes each with one command
 * and is told with the next frame what a hand changed. `module`: dials.js when the scene's source imports
 * `pydials`, so it is there before the scene starts; otherwise it is loaded when the first control is asked
 * for, and what was asked of it meanwhile is done then. `given`: a host's copy (as for sound's `synths`).
 */
function dialsKeeper({ given = null, module = null }) {
  const made = (m, canvas) => { const api = m.dials(canvas, { fresh: true }); api.close = () => api.panel.close(); return api }
  return (canvas) => {
    if (module) return made(module, canvas)
    let api = null, closed = false
    const calls = []
    const call = (name, args) => { if (typeof api[name] === 'function') return api[name](...args) }
    const begin = () => {
      begin.done = begin.done || loadLibrary('pydials', given).then((m) => {
        if (closed) return
        api = made(m, canvas)
        for (const [name, args] of calls.splice(0)) call(name, args)
      }, (e) => { console.error('The controls could not load: ' + ((e && e.message) || e)) })
    }
    const close = () => { closed = true; if (api) api.close() }
    return new Proxy({}, {
      has: () => true,
      get: (_, name) => (name === 'close' ? close : (...args) => {
        if (api) return call(name, args)
        calls.push([name, args])
        begin()
      }),
    })
  }
}

// ---------------------------------------------------------------- a single-file page
//
// `pyctures build scene.py -o scene.html` writes one HTML file. What a folder
// would hold beside the page comes inside it instead, as JSON in
// <script type="application/json" id="pyctures-inline">:
//   {runtime, sources: {path: text}, files: {path: base64}, three: {core, module, orbit},
//    synths: {js, py, wasm: base64}, dials: {js, py}}

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
import sys, os, types, importlib
_pyctures_scenes = {}
# The libraries a scene asks for by importing them (synths, pydials): each is one file, put here for the scene that needs it.
os.makedirs('/pyctures-libraries', exist_ok=True)
sys.path.append('/pyctures-libraries')
def _pyctures_library(name, source):
    path = '/pyctures-libraries/%s.py' % name
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(source)
        importlib.invalidate_caches()
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
    if a:
        import shutil
        shutil.rmtree(a, ignore_errors=True)   # the scene's folder of stored files: the page has its own copy
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

/**
 * The folder, in Pyodide's file system, for one run's stored files. A page's scenes share
 * one Python and one file system, so each has its own (Python is told it as info.files_in)
 * and two scenes can both keep `scores.db`. It is removed when the run stops.
 */
const storedIn = (sid) => '/pyctures-stored/' + sid
const putIn = (dir, stored) => (stored || []).map((f) => ({ path: dir + '/' + f.path, data: f.data }))

/** Does the scene open a database? Python's sqlite3 is a download of its own in Pyodide, fetched only for a scene that says open_database. */
export function usesDatabase(source) { return /\bopen_database\b/.test(codeOf(source || '')) }

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
        for (const name in m.libraries || {}) py.globals.get('_pyctures_library')(name, m.libraries[name])
        await py.loadPackagesFromImports(m.source)
        if (m.sqlite) await py.loadPackage('sqlite3')
        py.globals.get('_pyctures_new')(m.sid)
        reply = call(m.sid, 'start', m.source, m.info)
      } else if (m.op === 'tick') {
        reply = call(m.sid, 'tick', m.payload)
      } else {
        reply = call(m.sid, 'stop', m.dir)
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
 * page use. `files`: extra files to put beside the scene. `stored` (to start): the files
 * the scene has written before, as [{path, data}], put there after them.
 */
export function workerTransport(src, files = []) {
  const sid = nextSceneId++
  let worker = null
  return {
    label: 'Python in a worker',
    keepsFiles: true,   // Python's files are forgotten with the page: the page hands them over and keeps what is written
    async start(source, info, stored) {
      worker = pythonWorker()
      const beside = await readFiles(src, files)
      const libraries = await pythonLibraries(source, beside)
      const data = beside.concat(putIn(storedIn(sid), stored))
      return worker.call({ op: 'start', sid, source, info: JSON.stringify({ ...info, files_in: storedIn(sid) }), files: data, libraries, sqlite: usesDatabase(source) }, data.map((d) => d.data))
    },
    tick(payload) { return worker.call({ op: 'tick', sid, payload: JSON.stringify(payload) }) },
    async stop() {
      if (worker && !worker.dead) { try { await worker.call({ op: 'stop', sid, dir: storedIn(sid) }) } catch (e) { /* not running */ } }
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
    keepsFiles: true,
    async start(source, info, stored) {
      py = await loadPyodideOnce()
      callPy = py.globals.get('_pyctures_call')
      const beside = await readFiles(src, files)
      const libraries = await pythonLibraries(source, beside)
      for (const name in libraries) py.globals.get('_pyctures_library')(name, libraries[name])
      for (const f of beside.concat(putIn(storedIn(sid), stored))) {
        const parts = f.path.split('/')
        for (let i = 1; i < parts.length; i++) {
          try { py.FS.mkdir(parts.slice(0, i).join('/')) } catch (e) { /* exists */ }
        }
        py.FS.writeFile(f.path, new Uint8Array(f.data))
      }
      await py.loadPackagesFromImports(source)
      if (usesDatabase(source)) await py.loadPackage('sqlite3')
      py.globals.get('_pyctures_new')(sid)
      return callPy(sid, 'start', source, JSON.stringify({ ...info, files_in: storedIn(sid) }))
    },
    async tick(payload) { return callPy(sid, 'tick', JSON.stringify(payload)) },
    async stop() { if (callPy) { try { callPy(sid, 'stop', storedIn(sid)) } catch (e) { /* not running */ } } },
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
 *   controls    false: no scrubber for a program of timed scenes (see scenes/scenes.js)
 *   transitions more transitions between scenes, by name (scenes/scenes.js, "MORE TRANSITIONS")
 *   scenes      the page's half of scenes, for a host that has it already: the module scenes.js, a promise of it, or its address
 * While a file with scenes runs, `scene.stage` is the page's half of them: `name`, `sections`, `duration`,
 * `time`, and `running`, the transition going on now or null (`{ name, seconds, progress, from, to, hold(progress), release() }`).
 *   storage     where the scene's files and databases are kept, from a host (see sceneFiles)
 *   sound       how the scene's sound is played, from a host (see soundKeeper)
 *   microphone  a host's own microphone (a stream, pushed frames, or false), and `save`, where save_sound's files go
 *   dials       dials.js from a host: the module, a promise of it, or its address
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
    // What this scene's saved values are kept under: its own address, so each scene on a site has its own.
    // A scene that came with the page (one file holding everything) is told apart by the page's address.
    const src = this.opt.src || this.name
    const packed = inline()
    const kept = !/^(?:https?|file):$/.test(location.protocol) ? this.name
      : packed && packed.sources && packed.sources[src] != null ? `${location.pathname}#${src}` : new URL(src, document.baseURI).pathname
    this.saved = savedValues(kept)
    this.files = sceneFiles(kept, this.opt.storage)
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
      this.hush()
      if (seen && this.status === 'idle' && this.opt.autoStart) this.start()
      else if (seen) this.resume()
    }, { rootMargin: '100px' })
    this.io.observe(el)
    this.onVisibility = () => { this.hush(); if (!document.hidden) this.resume() }
    document.addEventListener('visibilitychange', this.onVisibility)
    this.loop = this.loop.bind(this)
  }

  /** A scene that is out of view or in a hidden tab is silent, with its sound kept as it is. */
  hush() {
    if (!this.sound) return
    if (this.visible && !document.hidden) this.sound.resume()
    else this.sound.pause()
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
      // Sound and dials, for a scene that imports them: there before it starts, so a dial knows its range at once.
      const libs = {}
      const host = this.opt.sound || {}
      for (const name in LIBRARIES) {
        if (!usesLibrary(source, name)) continue
        // A host that plays the sound itself needs synths.js here only for what a dial asks of a synth.
        if (name === 'synths' && typeof host.send === 'function' && !host.synths && !usesLibrary(source, 'pydials')) continue
        try { libs[name] = await loadLibrary(name, name === 'synths' ? host.synths : name === 'pydials' ? this.opt.dials : this.opt.scenes) } catch (e) { this.log('err', `${name} could not load: ${(e && e.message) || e}`) }
      }
      // Everything the scene has stored, to put in Python's file system before it starts.
      const stored = this.transport.keepsFiles ? await this.files.all() : []
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
      // A browser keeps a page silent until it has been touched: say so over the scene, until it has been. The
      // microphone is asked for at once, without waiting for that, but is neither heard nor recorded until then.
      const waiting = ['Click, tap or press a key to turn the sound on', 'Click, tap or press a key to turn the sound and the microphone on']
      this.sound = soundKeeper({
        host: this.opt.sound, src: this.opt.src, module: libs.synths, midi: this.opt.midi,
        microphone: this.opt.microphone, save: this.opt.save, files: this.files,
        onState: (state) => { if (token === r.token && (state === 'waiting' || (this.coverEl && waiting.includes(this.coverEl.textContent)))) this.cover(state === 'waiting' ? waiting[this.sound && this.sound.microphone ? 1 : 0] : '') },
      })
      // Scenes, for a file that names one: the page's half runs the transitions and shows the scrubber.
      this.stage = libs.pyscenes ? libs.pyscenes.scenesKeeper(this.el, this.canvas, {
        more: this.opt.transitions, bar: this.opt.controls !== false,
        tell: (e) => { if (r.live && token === r.token) r.events.push({ k: 'scene', e }) },
        // The scrubber's pause is the sound's too; playing again leaves a scene that is out of view silent.
        paused: (on) => { if (!this.sound) return; if (on) this.sound.pause(); else this.hush() },
      }) : null
      this.renderer = createRenderer(this.canvas, {
        sound: this.sound,
        scenes: this.stage,
        dials: dialsKeeper({ given: this.opt.dials, module: libs.pydials }),
        three: three && three.three,
        addons: three && three.addons,
        images: imageResolver(this.opt.src, inl && inl.files),
        saved: this.saved,
        files: this.files,
        input: inputOf(source),
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
      const text = await this.transport.start(source, { ...r.size, measure: r.measuring, saved: this.saved.all(), ...(this.stage ? { scenes: { transitions: this.stage.names() } } : {}) }, stored)
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
    if (this.sound) { this.sound.close(); this.sound = null }
    if (this.stage) { this.stage.close(); this.stage = null }
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
    if (this.stage) this.stage.caught()
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
    // What Python reads back of the sound (a wave, a level, a song's place) goes with this frame.
    if (this.sound) this.sound.frame()
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
    // A transition and the scrubber move on the page's clock, whatever Python is doing.
    if (this.stage) this.stage.step(Math.min(0.1, gap / 1000))
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
 * `options.storage` (from a host, not an attribute): where the scene's files and databases
 * are kept, an object with any of list, readText, writeText, readBytes, writeBytes (see sceneFiles).
 * `options.sound` (from a host): how the scene's sound is played, an object with any of send, read,
 * synths, wasm, worklet, latency, onState (see soundKeeper). `options.dials`: dials.js from a host.
 * `options.midi` (from a host): a MIDI transport for a browser with none, an object with open, inputs, outputs,
 * send, receive and changed (synths.js's docs/midi.md), or false for no MIDI. Without it the browser's Web MIDI is used.
 * `options.microphone` (from a host): the microphone where the page cannot ask the browser for one (a frame with no
 * origin, an app that owns the audio session): a MediaStream, a function that gives one, { open(wants), close() }
 * whose open may push frames (synths.js's docs/microphone.md), or false for none. Without it the browser is asked
 * when a scene first calls use_microphone(). `options.save(file)` is given { name, bytes, type } for each file
 * save_sound() makes, in place of the scene's files (when `storage` has writeBytes) or a download.
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
    storage: options.storage,
    sound: options.sound,
    midi: options.midi,
    microphone: options.microphone,
    save: options.save,
    dials: options.dials,
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
