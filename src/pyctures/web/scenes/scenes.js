/**
 * scenes.js: the page's half of a Pyctures file in several scenes. pyctures.js loads it only for a file that
 * names a scene (LIBRARIES, `pyscenes`); its Python half is pyscenes.py, beside it.
 *
 * SCENES: a Python file in several scenes (`class Title(Scene)`, `go("game")`; see the Python half). Which scene
 * is on show is Python's business alone. The page does the two things that must not wait for Python:
 *
 *   A TRANSITION. Python may be slow or far away, and sends one batch a frame. When a scene ends it sends one
 *   command at the head of the new scene's first batch: transition(name, seconds, colour). The canvas still
 *   holds the old scene's last picture then, so it is copied once to a layer over the canvas, and that still
 *   picture is faded, clipped or slid away by the browser on the page's own clock, every refresh, while the new
 *   scene's frames arrive underneath whenever they do. It never draws on the scene's canvas.
 *
 *   THE SCRUBBER, for a program whose scenes all have a length: Python sends show(sections, duration, time, name,
 *   paused) when a scene begins and once a second; between those the page's clock moves the knob. A press on it
 *   goes back to Python as an event, { k: 'scene', e: { seek: seconds } } or { pause: true }.
 *
 * Both are the fixed handle 12 (H_SCENES). A page says it has them in the start info (`scenes`), and Python
 * sends nothing to a page that does not. `transitionLayer` and `timelineBar` are the same two functions
 * pictures.js has (its scenes/scenes.js), and `scenesKeeper` is what an app with a renderer of its own needs to make handle 12.
 *
 * MORE TRANSITIONS (a dissolve, a ripple: an effects library's) are given by name in the scene's `transitions`
 * option: `{ dissolve: { start({ from, to, container, seconds }), frame(progress), end() } }`. `from` is a
 * canvas holding the old scene's last picture (not on the page), `to` the scene's own canvas.
 */

const TRANSITIONS = ['cut', 'crossfade', 'fade', 'wipe', 'wipe_left', 'wipe_up', 'wipe_down', 'slide_left', 'slide_right', 'slide_up', 'slide_down']
const SLIDES = { slide_left: [-1, 0], slide_right: [1, 0], slide_up: [0, -1], slide_down: [0, 1] }
/**
 * The layer a transition is shown on (see the top of this file). `begin` copies the canvas as it is now (`from`, kept off
 * the page) and lays one more canvas over the scene's; `step(dt)` moves the transition on and `paint()`
 * draws it into that canvas, and the layer is taken away when the transition is over.
 *
 * IT IS DRAWN, NOT STYLED. The layer has no opacity, clip or transform of its own: what it shows is in its
 * pixels (the old picture at an alpha, the part of it a wipe has not reached, both pictures of a slide), so
 * a recorder that draws the canvases of the scene one over another gets exactly what the screen shows. And
 * the transition moves only by the `dt` it is stepped with, which is the scene's own frame time: a page
 * that is stepped a frame at a time steps the transition with it.
 *
 * `real` says the scene's canvas can be read whenever `paint` is called (a 2D canvas; a 3D one only straight
 * after the scene has drawn on it). A slide draws the new scene too, moved, and covers the canvas whole; where
 * the canvas cannot be read at any time, `caught()` is called straight after each time the scene has drawn, and
 * keeps a copy for the slide to draw from until the next.
 *
 * `running` is the transition now, or null: `{ name, seconds, progress, from, to, layer, draw(ctx),
 * hold(progress), release() }`. `draw(ctx)` paints the layer as it is now over the whole of another canvas's
 * context; `hold` stops the transition at a point (a test) and `release` lets it carry on from there.
 * `data` names the layer for the page: it is `<canvas data-${data}-transition="crossfade">`.
 */
export function transitionLayer(container, canvas, more = {}, data = 'pyctures') {
  let run = null
  const finish = () => {
    if (!run) return
    const was = run
    run = null
    try { was.own?.end?.() } catch (e) { console.error(e) }
    was.layer.remove()
  }
  const paint = () => {
    if (!run || run.own) return
    const { name, from, layer, g, shown: p } = run, w = layer.width, h = layer.height
    g.globalAlpha = 1
    g.clearRect(0, 0, w, h)
    if (name === 'crossfade') {
      g.globalAlpha = 1 - p
      g.drawImage(from, 0, 0)
    } else if (name === 'fade') {
      // Through a colour: the old picture goes under it, then the new one comes out from under it.
      if (p < 0.5) g.drawImage(from, 0, 0)
      g.globalAlpha = p < 0.5 ? p * 2 : (1 - p) * 2
      g.fillStyle = run.colour
      g.fillRect(0, 0, w, h)
    } else if (SLIDES[name]) {
      const [x, y] = SLIDES[name], dx = Math.round(x * p * w), dy = Math.round(y * p * h)
      try { g.drawImage(run.real ? canvas : run.kept, dx - x * w, dy - y * h, w, h) } catch (e) { /* a canvas with no size */ }
      g.drawImage(from, dx, dy)
    } else {
      // A wipe: the part of the old picture the edge has not reached.
      const across = Math.round(p * w), down = Math.round(p * h)
      if (name === 'wipe') g.drawImage(from, across, 0, w - across, h, across, 0, w - across, h)
      else if (name === 'wipe_left') g.drawImage(from, 0, 0, w - across, h, 0, 0, w - across, h)
      else if (name === 'wipe_down') g.drawImage(from, 0, down, w, h - down, 0, down, w, h - down)
      else g.drawImage(from, 0, 0, w, h - down, 0, 0, w, h - down)
    }
    g.globalAlpha = 1
  }
  const show = (p) => {
    run.shown = p
    if (run.own) run.own.frame?.(p)
  }
  return {
    names: () => [...TRANSITIONS, ...Object.keys(more)],
    knows: (name) => TRANSITIONS.includes(name) || !!more[name],
    get running() { return run },
    begin(name, seconds, colour = 'black', real = true) {
      finish()
      const copy = () => {
        const c = document.createElement('canvas')
        c.width = canvas.width
        c.height = canvas.height
        return c
      }
      const from = copy(), layer = copy()
      try { from.getContext('2d').drawImage(canvas, 0, 0) } catch (e) { /* a canvas with no size yet: the picture is blank */ }
      layer.dataset[`${data}Transition`] = name
      layer.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none'
      const mine = run = { name, seconds, colour, real, kept: !real && SLIDES[name] ? copy() : null, from, to: canvas, layer, g: layer.getContext('2d'), progress: 0, shown: 0, held: false, at: 0, own: more[name] || null,
        draw(ctx) { ctx.drawImage(layer, 0, 0, ctx.canvas.width, ctx.canvas.height) },
        hold(p) { mine.held = true; mine.progress = p; if (run === mine) { show(p); paint() } },
        release() { mine.held = false; mine.at = mine.progress * seconds } }
      if (run.own) run.own.start?.({ from, to: canvas, container, seconds })
      else canvas.after(layer)
      show(0)
      paint()
    },
    step(dt) {
      if (!run || run.held) return
      run.at += dt
      const p = run.progress = Math.min(1, run.at / run.seconds)
      // Eased at both ends, as Pymations' are.
      show(p * p * (3 - 2 * p))
      if (p >= 1) finish()
    },
    paint,
    /** The scene has just drawn on its canvas: keep the picture, for a slide over a canvas that cannot be read later. */
    caught() {
      if (!run || !run.kept) return
      const g = run.kept.getContext('2d')
      g.clearRect(0, 0, run.kept.width, run.kept.height)
      try { g.drawImage(canvas, 0, 0, run.kept.width, run.kept.height) } catch (e) { /* a canvas with no size */ }
    },
    finish,
  }
}

/**
 * THE SCRUBBER, for a program whose scenes all have a length (a sequence): play and pause, a track with a
 * tick where each scene and section starts, and the time. It is pictures.js's own, and looks and behaves as Pymations' does: shown
 * while paused, and on a move of the pointer while playing. `stage` is what it shows and moves:
 * `{ time(), duration(), sections(), paused(), pause(on), seek(seconds) }`.
 */
const BAR_STYLE = `.pyctures-bar{position:absolute;left:8px;right:8px;bottom:8px;z-index:2;display:flex;align-items:center;gap:10px;padding:4px 10px 4px 4px;border-radius:8px;background:rgba(11,11,15,.8);color:#e5e7eb;font:12px ui-monospace,Menlo,Consolas,monospace;transition:opacity .2s}
.pyctures-bar.hide{opacity:0;pointer-events:none}
.pyctures-bar button{width:26px;height:26px;padding:0;border:0;border-radius:6px;background:none;color:inherit;font:14px/1 system-ui,sans-serif;cursor:pointer}
.pyctures-bar button:hover{background:rgba(255,255,255,.14)}
.pyctures-track{position:relative;flex:1;height:18px;cursor:pointer;touch-action:none}
.pyctures-track::before{content:"";position:absolute;left:0;right:0;top:8px;height:2px;border-radius:1px;background:rgba(255,255,255,.25)}
.pyctures-fill{position:absolute;left:0;top:8px;height:2px;border-radius:1px;background:#e5e7eb}
.pyctures-ticks i{position:absolute;top:4px;width:2px;height:10px;margin-left:-1px;border-radius:1px;background:rgba(255,255,255,.65)}
.pyctures-knob{position:absolute;top:4px;width:10px;height:10px;margin-left:-5px;border-radius:50%;background:#fff}`
const minutes = (t) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`
export function timelineBar(container, stage) {
  if (!document.getElementById('pyctures-bar-style')) {
    const style = document.createElement('style')
    style.id = 'pyctures-bar-style'
    style.textContent = BAR_STYLE
    document.head.append(style)
  }
  const bar = document.createElement('div')
  bar.className = 'pyctures-bar hide'
  bar.innerHTML = '<button type="button" class="pyctures-play" aria-label="Pause"></button><div class="pyctures-track" role="slider" aria-label="Time" tabindex="-1">' +
    '<div class="pyctures-fill"></div><div class="pyctures-ticks"></div><div class="pyctures-knob"></div></div><span class="pyctures-time"></span>'
  container.append(bar)
  const [play, track, fill, ticks, knob, time] = ['play', 'track', 'fill', 'ticks', 'knob', 'time'].map((part) => bar.querySelector(`.pyctures-${part}`))
  let over = false, dragging = false, wasPaused = false, hiding = 0, drawn = '', icon = ''
  const show = () => {
    bar.classList.remove('hide')
    clearTimeout(hiding)
    const hide = () => {
      if (stage.paused() || over || dragging) { hiding = setTimeout(hide, 800); return }
      bar.classList.add('hide')
    }
    hiding = setTimeout(hide, 2500)
  }
  const update = () => {
    const long = stage.duration(), t = stage.time(), part = long > 0 ? Math.min(1, t / long) : 0
    fill.style.width = knob.style.left = `${part * 100}%`
    time.textContent = `${minutes(t)} / ${minutes(long)}`
    const now = stage.paused() ? '▶' : '❚❚'
    if (now !== icon) { icon = play.textContent = now; play.setAttribute('aria-label', stage.paused() ? 'Play' : 'Pause') }
    const sections = stage.sections(), key = long + '|' + sections.map((s) => `${s.name}@${s.t}`).join(',')
    if (key === drawn) return
    drawn = key
    ticks.textContent = ''
    for (const s of sections) {
      if (!(long > 0) || !(s.t > 0) || s.t >= long) continue
      const tick = document.createElement('i')
      tick.style.left = `${s.t / long * 100}%`
      tick.title = s.name
      ticks.append(tick)
    }
  }
  const seekTo = (x) => {
    const box = track.getBoundingClientRect()
    stage.seek(box.width ? (x - box.left) / box.width * stage.duration() : 0)
    update()
  }
  // The scrubber's own presses are not the program's.
  const own = (e) => e.stopPropagation()
  bar.addEventListener('pointerdown', own)
  bar.addEventListener('pointerup', own)
  bar.addEventListener('pointerenter', () => { over = true })
  bar.addEventListener('pointerleave', () => { over = false })
  play.addEventListener('click', (e) => { e.stopPropagation(); stage.pause(!stage.paused()); update(); show() })
  track.addEventListener('pointerdown', (e) => {
    e.stopPropagation()
    dragging = true
    wasPaused = stage.paused()
    stage.pause(true)
    try { track.setPointerCapture(e.pointerId) } catch (e2) { /* a pointer that has already gone */ }
    seekTo(e.clientX)
  })
  track.addEventListener('pointermove', (e) => { if (dragging) seekTo(e.clientX) })
  const end = (e) => {
    if (!dragging) return
    e.stopPropagation()
    dragging = false
    stage.pause(wasPaused)
    update()
    show()
  }
  track.addEventListener('pointerup', end)
  track.addEventListener('pointercancel', end)
  const stir = () => show()
  container.addEventListener('pointermove', stir)
  container.addEventListener('pointerdown', stir)
  update()
  return {
    update,
    remove() {
      clearTimeout(hiding)
      container.removeEventListener('pointermove', stir)
      container.removeEventListener('pointerdown', stir)
      bar.remove()
    },
  }
}

/**
 * The page's half of a file's scenes, for one canvas in `container`. `tell(event)` is handed what the scrubber
 * asks of Python; `more` is transitions by name beside the ones built in; `bar: false` leaves the scrubber out;
 * `paused(on)` is told when the scrubber pauses and plays, for the sound.
 * What it gives back: `transition`, `show` (Python's commands), `step(dt)` once a refresh, `close()`, and
 * `running`, `sections`, `duration`, `time`, `name` to read.
 */
export function scenesKeeper(container, canvas, { tell = () => {}, more = {}, bar: wantsBar = true, paused: onPause = () => {} } = {}) {
  const layer = transitionLayer(container, canvas, more || {})
  const state = { sections: [], duration: 0, time: 0, name: '', paused: false }
  let bar = null
  const stage = {
    time: () => state.time, duration: () => state.duration, sections: () => state.sections, paused: () => state.paused,
    pause(on) { state.paused = !!on; tell({ pause: state.paused }); onPause(state.paused) },
    seek(seconds) { state.time = Math.max(0, Math.min(state.duration, seconds)); tell({ seek: state.time }) },
  }
  return {
    names: () => Object.keys(more || {}),
    transition(name, seconds, colour, real = true) {
      if (name === 'cut' || !(seconds > 0)) return layer.finish()
      layer.begin(name, seconds, colour || 'black', real)
    },
    show(sections, duration, time, name, paused) {
      Object.assign(state, { sections: sections || [], duration: duration || 0, time: time || 0, name: name || '', paused: !!paused })
      container.dataset.pycturesScene = state.name
      container.dispatchEvent(new CustomEvent('pyctures-sections', { detail: { sections: state.sections, duration: state.duration, name: state.name } }))
      if (state.duration > 0 && wantsBar && !bar) bar = timelineBar(container, stage)
      if (bar) bar.update()
    },
    /** A batch of the scene's drawing has just been done (in this same turn of the page, so a 3D canvas can still be read). */
    caught() { layer.caught(); layer.paint() },
    step(dt) {
      layer.step(dt)
      layer.paint()
      if (!bar || state.paused) return
      state.time = Math.min(state.duration, state.time + dt)
      bar.update()
    },
    close() {
      layer.finish()
      if (bar) bar.remove()
      bar = null
      delete container.dataset.pycturesScene
    },
    get running() { return layer.running },
    get sections() { return state.sections },
    get duration() { return state.duration },
    get time() { return state.time },
    get name() { return state.name },
    stage,
  }
}

