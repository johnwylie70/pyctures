/**
 * manners.js: Pyctures' sound button and the card a demo asks with, the page's half of `sound_button()`,
 * `ask_about_sound()` and `sound_is_on()` (pymanners.py beside this file is Python's). It is a library that only
 * a file naming one of the three is given (pyctures.js LIBRARIES, `pymanners`): no other page fetches it or has
 * it packed in.
 *
 * PYTHON asks for the button with one command to the fixed handle 14, `show(options)`, for the card with
 * `ask(options)`, and switches the sound with `set(on)`. The page draws both, holds the switch and acts on a tap
 * at once, however slow or far away Python is, and Python is told with the next frame's events:
 * { on, asking, box }, to the function Python gave `listen` (`news`).
 */

/**
 * THE SOUND BUTTON, AND ASKING FIRST. Two lines a scene may write, and neither happens by itself.
 * `soundButton()` (Python's `sound_button()`) is a small speaker in a corner of the scene that switches all of the
 * scene's sound off and on. It asks nothing. `askAboutSound()` (`ask_about_sound()`) is for a demo that somebody
 * may open in a quiet room: a card over the scene before anything is heard, "This demo has sound", "Play with
 * sound", "Play without sound"; it puts the button up too if the scene has not.
 * Both are the page's own elements, laid over the scene: the scene does not draw them and nothing is done for
 * them in a frame. They sit above the controls' and the effects' layers (canvases beside the scene's, with no
 * z-index of their own) and below the frame rate and a mistake's message.
 *
 * WHAT IS KEPT, among the scene's saved values: `sound:on`, the last choice a person made (on the card, with the
 * button or with the M key; never what the scene's own code switched), and `sound:asked`, when the card was last
 * answered. THE CARD COMES BACK every time the scene is opened afresh, with the last answer ready under Enter: it
 * is there so that nobody is surprised by sound in a quiet room, and yesterday's answer is not today's. It is left
 * out when the scene is run again within SOUND_VISIT of an answer (working on a scene must not ask at every run),
 * and with `remember: true` once there is an answer. A scene that is being recorded a frame at a time shows neither
 * the card nor the button, and its sound is on (`recorded`).
 *
 * The runtime gives it `box` (the scene's element), `canvas`, `kept` ({ load(name), save(name, value) }: the saved
 * values), `ownKey` (the scene reads the M key itself), `controls()` (the
 * on-screen controls or null: the button keeps off them), `apply(on)` (switch the scene's sound), `recorded` and
 * `hold(asking, wait)` (the card went up or came down; the scene waits behind it unless `wait` is false).
 * The same text is in pictures.js and in Pyctures' page (web/pyctures.js): change one and change the other.
 */
const SOUND_ON = 'sound:on', SOUND_ASKED = 'sound:asked', SOUND_VISIT = 5 * 60 * 1000
const SOUND_CORNERS = ['top right', 'bottom right', 'top left', 'bottom left']
const SOUND_OPTIONS = { corner: 'top right', size: 0, inset: 0, colour: 'auto', key: 'm' }
// What the card that asks takes besides: its words, and when it is left out.
const SOUND_ASKING = { title: 'This demo has sound', withSound: 'Play with sound', withoutSound: 'Play without sound', remember: false, wait: true }
const SOUND_SPEAKER = '<path fill="currentColor" stroke="none" d="M3.2 9.4h3.4l4.9-4v13.2l-4.9-4H3.2z"/>'
const SOUND_ICONS = {
  on: SOUND_SPEAKER + '<path d="M14.8 9.1a4.1 4.1 0 0 1 0 5.8M17.5 6.4a7.9 7.9 0 0 1 0 11.2"/>',
  off: SOUND_SPEAKER + '<path d="M15.4 9.4l5.2 5.2m0-5.2l-5.2 5.2"/>',
}
const soundIcon = (which) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${SOUND_ICONS[which]}</svg>`
const SOUND_CSS = `
[data-sound-button]{position:absolute;z-index:2;box-sizing:border-box;margin:0;padding:0;display:grid;place-items:center;border:1px solid var(--edge);border-radius:50%;background:var(--glass);color:var(--ink);cursor:pointer;opacity:.66;outline:none;-webkit-appearance:none;appearance:none;-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);-webkit-tap-highlight-color:transparent;touch-action:manipulation;-webkit-user-select:none;user-select:none;transition:opacity .15s,transform .12s}
[data-sound-button][data-look=light]{--glass:rgba(14,16,22,.5);--ink:#fff;--edge:rgba(255,255,255,.24);--ring:#fff}
[data-sound-button][data-look=dark]{--glass:rgba(255,255,255,.66);--ink:#1b1e26;--edge:rgba(0,0,0,.16);--ring:#1b1e26}
[data-sound-button][aria-pressed=false]{opacity:.86}
[data-sound-button]:hover,[data-sound-button]:focus-visible{opacity:1}
[data-sound-button]:focus-visible{box-shadow:0 0 0 2px var(--ring)}
[data-sound-button]:active{transform:scale(.92)}
[data-sound-button] svg{width:58%;height:58%;display:block;pointer-events:none}
[data-sound-card]{position:absolute;inset:0;z-index:2;overflow:hidden;display:grid;place-items:center;container-type:size;background:rgba(6,8,14,.6);-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px);color:#fff;font:15px/1.3 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
[data-sound-card] [data-part=panel]{box-sizing:border-box;width:min(296px,calc(100% - 24px));max-height:calc(100% - 12px);padding:20px 18px 18px;display:grid;gap:10px;text-align:center;border-radius:18px;border:1px solid rgba(255,255,255,.1);background:rgba(23,26,34,.95);box-shadow:0 18px 48px rgba(0,0,0,.45);animation:sound-card-in .18s ease-out}
[data-sound-card] svg{width:30px;height:30px;margin:0 auto;display:block;color:#ffd166}
[data-sound-card] [data-part=title]{margin:0 0 6px;font-size:17px;font-weight:650;letter-spacing:-.01em;text-wrap:balance}
[data-sound-card] button{box-sizing:border-box;min-height:46px;margin:0;padding:10px 14px;border-radius:12px;border:1px solid transparent;font:inherit;font-weight:600;cursor:pointer;outline:none;-webkit-appearance:none;appearance:none;touch-action:manipulation;transition:transform .12s,background-color .12s}
[data-sound-card] button[data-answer=on]{background:#fff;color:#12141a}
[data-sound-card] button[data-answer=off]{background:rgba(255,255,255,.07);color:#fff;border-color:rgba(255,255,255,.2)}
[data-sound-card] button[data-answer=on]:hover{background:#e9edf5}
[data-sound-card] button[data-answer=off]:hover{background:rgba(255,255,255,.14)}
[data-sound-card] button:active{transform:scale(.97)}
[data-sound-card] button:focus-visible{box-shadow:0 0 0 2px rgba(23,26,34,.95),0 0 0 4px #7cc4ff}
@container (max-height:250px){
[data-sound-card] [data-part=panel]{width:min(400px,calc(100% - 16px));grid-template-columns:1fr 1fr;gap:8px;padding:12px;border-radius:14px}
[data-sound-card] svg{display:none}
[data-sound-card] [data-part=title]{grid-column:1/-1;margin:0 0 2px;font-size:14px}
[data-sound-card] button{min-height:38px;padding:6px 8px;font-size:13px;border-radius:10px}
}
@container (max-width:250px){
[data-sound-card] [data-part=panel]{padding:12px;gap:8px}
[data-sound-card] [data-part=title]{font-size:14px}
[data-sound-card] button{min-height:38px;padding:6px 8px;font-size:13px}
}
@keyframes sound-card-in{from{opacity:0;transform:translateY(6px) scale(.97)}}
@media (prefers-reduced-motion:reduce){[data-sound-card] [data-part=panel]{animation:none}[data-sound-button],[data-sound-card] button{transition:none}}
`
/** The corner as it is named, however it was written ("top-right", "right top", "topRight"); null for anything else. */
function soundCorner(said) {
  const words = String(said).replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase().split(/[\s_-]+/).filter(Boolean)
  const up = words.find((w) => w === 'top' || w === 'bottom'), across = words.find((w) => w === 'left' || w === 'right')
  return up && across && words.length === 2 ? `${up} ${across}` : null
}
/** What soundButton (or, with `asking`, askAboutSound) was given, checked: a mistake is said in plain words. `call` is how the scene wrote it. */
function soundOptions(given, call, asking = false) {
  const now = asking ? { ...SOUND_OPTIONS, ...SOUND_ASKING } : SOUND_OPTIONS
  // One thing in quotes is the corner, or for the card its title.
  if (typeof given === 'string') given = asking ? { title: given } : { corner: given }
  if (given == null) return { ...now }
  if (typeof given !== 'object') throw new Error(`${call} takes ${asking ? 'the card\'s title' : 'a corner'}, as in ${call.replace('()', asking ? '("Music and sound effects")' : '("bottom left")')}, or options in braces, not ${JSON.stringify(given)}`)
  const out = { ...now }
  const names = { color: 'colour', with_sound: 'withSound', without_sound: 'withoutSound' }
  for (const [said, value] of Object.entries(given)) {
    const name = names[said] || said
    if (!(name in now)) throw new Error(`${call} has no option called "${said}". The options are: ${Object.keys(now).join(', ')}`)
    out[name] = value
  }
  const corner = soundCorner(out.corner)
  if (!corner) throw new Error(`${call}: "${out.corner}" is not a corner. The corners are: ${SOUND_CORNERS.map((c) => `"${c}"`).join(', ')}`)
  out.corner = corner
  out.size = Number(out.size) > 0 ? Number(out.size) : 0
  // How far in from the two edges of its corner: one number, or [across, down] to sit beside something the scene draws there.
  const inset = (Array.isArray(out.inset) ? out.inset : [out.inset, out.inset]).map(Number)
  if (inset.length !== 2 || inset.some((n) => !(n >= 0))) throw new Error(`${call}: inset is how far in from the corner's two edges the button is, as a number or [across, down], not ${JSON.stringify(out.inset)}`)
  out.inset = inset[0] || inset[1] ? inset : 0
  out.key = out.key ? String(out.key).toLowerCase() : ''
  return out
}
function soundSwitch({ box, canvas, kept, ownKey, controls, apply, hold, recorded = false }) {
  // RECORDED A FRAME AT A TIME (a host making a video), there is nobody to ask and nothing to press, and the
  // recording is being made with its sound: the sound is on whatever was chosen last, and neither the card nor
  // the button is put on the page at all.
  let on = recorded || kept.load(SOUND_ON) !== false
  let options = { ...SOUND_OPTIONS }, words = { ...SOUND_ASKING }
  let shown = false, asking = false, asked = false, closed = false
  let button = null, card = null, at = null, look = 'light', sizes = null
  const timers = new Set()
  const later = (fn, ms) => { const t = setTimeout(() => { timers.delete(t); if (!closed) fn() }, ms); timers.add(t) }
  let framed = true
  try { framed = window.top !== window } catch (e) { /* another site's frame */ }

  if (!document.querySelector('style[data-sound-button-style]')) {
    const style = document.createElement('style')
    style.dataset.soundButtonStyle = ''
    style.textContent = SOUND_CSS
    document.head.append(style)
  }

  // How much of each edge the screen keeps (a notch, a home bar): left, top, right, bottom. A page inside
  // another's frame is told of the screen's edges though it may be nowhere near them: it keeps none.
  const edges = () => {
    if (framed) return [0, 0, 0, 0]
    try {
      const probe = document.createElement('div')
      probe.style.cssText = 'position:fixed;inset:0;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top, 0px) env(safe-area-inset-right, 0px) env(safe-area-inset-bottom, 0px) env(safe-area-inset-left, 0px)'
      document.documentElement.append(probe)
      const keeps = getComputedStyle(probe), r = box.getBoundingClientRect()
      const part = (name, gone) => Math.max(0, (parseFloat(keeps[name]) || 0) - Math.max(0, gone))
      const out = [part('paddingLeft', r.left), part('paddingTop', r.top), part('paddingRight', innerWidth - r.right), part('paddingBottom', innerHeight - r.bottom)]
      probe.remove()
      return out
    } catch (e) {
      return [0, 0, 0, 0]
    }
  }
  // Light or dark, from the scene under the button: read from the canvas once in a while, never in a frame.
  // A canvas that cannot be read (3D, between frames) leaves the look as it is: white on dark glass reads on both.
  const under = () => {
    if (options.colour !== 'auto') return options.colour === 'dark' ? 'dark' : 'light'
    try {
      const probe = document.createElement('canvas')
      probe.width = probe.height = 1
      const g = probe.getContext('2d', { willReadFrequently: true })
      const kx = canvas.width / (canvas.clientWidth || 1), ky = canvas.height / (canvas.clientHeight || 1)
      g.drawImage(canvas, at.x * kx, at.y * ky, at.size * kx, at.size * ky, 0, 0, 1, 1)
      const [r, gr, b, a] = g.getImageData(0, 0, 1, 1).data
      if (a < 200) return look
      return 0.2126 * r + 0.7152 * gr + 0.0722 * b > 150 ? 'dark' : 'light'
    } catch (e) {
      return look
    }
  }
  const paint = () => {
    if (!button) return
    button.innerHTML = soundIcon(on ? 'on' : 'off')
    button.setAttribute('aria-pressed', String(on))
    button.setAttribute('aria-label', on ? 'Sound is on. Turn the sound off' : 'Sound is off. Turn the sound on')
    button.title = (on ? 'Sound on' : 'Sound off') + (options.key && !ownKey ? ` (${options.key.toUpperCase()})` : '')
    button.dataset.look = look
    button.dataset.sound = on ? 'on' : 'off'
  }
  // Where the button goes: the corner asked for, of the room the controls leave; if a control is there, the next corner.
  const place = () => {
    if (!button) return
    const W = box.clientWidth, H = box.clientHeight
    let coarse = false
    try { coarse = matchMedia('(pointer: coarse)').matches } catch (e) { /* no matchMedia */ }
    const size = Math.round(Math.min(options.size || (coarse ? 44 : 34), Math.max(24, Math.min(W, H) * 0.22)))
    const gap = coarse ? 10 : 8
    const [l, t, r, b] = edges()
    let area = { x: l, y: t, w: W - l - r, h: H - t - b }
    let panel = null
    try { panel = controls() } catch (e) { /* none */ }
    try {
      const room = panel && panel.room && panel.room()
      if (room && room.width >= size + 2 * gap && room.height >= size + 2 * gap) {
        const x = Math.max(area.x, room.x), y = Math.max(area.y, room.y)
        area = { x, y, w: Math.min(area.x + area.w, room.x + room.width) - x, h: Math.min(area.y + area.h, room.y + room.height) - y }
      }
    } catch (e) { /* the controls are not laid out yet */ }
    const [gx, gy] = options.inset || [gap, gap]
    const spot = (corner) => ({
      x: corner.endsWith('left') ? area.x + gx : area.x + area.w - gx - size,
      y: corner.startsWith('top') ? area.y + gy : area.y + area.h - gy - size,
    })
    const taken = (p) => {
      try {
        if (!panel || !panel.over) return false
        for (const [fx, fy] of [[0.5, 0.5], [0, 0], [1, 0], [0, 1], [1, 1]]) if (panel.over(p.x + fx * size, p.y + fy * size) === true) return true
      } catch (e) { /* not laid out yet */ }
      return false
    }
    const tries = [options.corner, ...SOUND_CORNERS.filter((c) => c !== options.corner)].map(spot)
    const p = tries.find((q) => !taken(q)) || tries[0]
    at = { x: Math.round(p.x), y: Math.round(p.y), size }
    button.style.left = at.x + 'px'
    button.style.top = at.y + 'px'
    button.style.width = button.style.height = size + 'px'
    const now = under()
    if (now !== look) { look = now; button.dataset.look = look }
  }

  const set = (value, keep) => {
    on = !!value
    if (keep) kept.save(SOUND_ON, on)
    paint()
    apply(on)
  }
  // The scene's element may be one of several things on a page: the keyboard is taken only when nothing else has it.
  const free = () => { const a = document.activeElement; return !a || a === document.body || a === canvas || box.contains(a) }

  const answer = (yes) => {
    if (!asking) return
    asking = false
    card.remove()
    card = null
    kept.save(SOUND_ASKED, Date.now())
    if (button) button.style.display = ''
    set(yes, true)
    hold(false, true)
    place()
    try { canvas.focus({ preventScroll: true }) } catch (e) { /* it has gone */ }
  }
  const raise = () => {
    asking = asked = true
    card = document.createElement('div')
    card.dataset.soundCard = ''
    card.setAttribute('role', 'dialog')
    card.setAttribute('aria-modal', 'true')
    card.setAttribute('aria-label', String(words.title))
    card.innerHTML = `<div data-part="panel">${soundIcon('on')}<p data-part="title"></p><button type="button" data-answer="on"></button><button type="button" data-answer="off"></button></div>`
    const [yes, no] = card.querySelectorAll('button')
    card.querySelector('[data-part=title]').textContent = words.title
    yes.textContent = words.withSound
    no.textContent = words.withoutSound
    // Only the person at the screen answers: a click or a key that a program made is not theirs, and is ignored.
    yes.addEventListener('click', (e) => { if (e.isTrusted) answer(true) })
    no.addEventListener('click', (e) => { if (e.isTrusted) answer(false) })
    // Keys are the card's while it is up: none reaches the scene. Escape is "without"; Enter and Space press the
    // button that has the keyboard, which is last time's answer; Tab and the arrows go between the two.
    const keys = (e) => {
      e.stopPropagation()
      if (e.type !== 'keydown') return
      if (e.key === 'Escape') { e.preventDefault(); if (e.isTrusted) answer(false) }
      else if (e.key === 'Tab' || e.key.startsWith('Arrow')) { e.preventDefault(); (document.activeElement === yes ? no : yes).focus({ preventScroll: true }) }
    }
    card.addEventListener('keydown', keys)
    card.addEventListener('keyup', keys)
    card.addEventListener('contextmenu', (e) => e.preventDefault())
    if (button) button.style.display = 'none'
    box.append(card)
    if (free()) (kept.load(SOUND_ON) === false ? no : yes).focus({ preventScroll: true })
    hold(true, words.wait !== false)
  }

  return {
    /** Put the button on the scene (again: with other options). It asks nothing. */
    show(given) {
      if (closed || recorded) return
      options = given
      if (!button) {
        button = document.createElement('button')
        button.type = 'button'
        button.dataset.soundButton = ''
        // A press is the button's alone: the scene under it is not told, and the keyboard stays with the scene.
        button.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation() })
        button.addEventListener('mousedown', (e) => e.preventDefault())
        button.addEventListener('click', (e) => {
          set(!on, true)
          if (e.detail) { try { canvas.focus({ preventScroll: true }) } catch (e2) { /* it has gone */ } }
        })
        const own = (e) => e.stopPropagation()
        button.addEventListener('keydown', own)
        button.addEventListener('keyup', own)
        box.append(button)
        if (typeof ResizeObserver === 'function') { sizes = new ResizeObserver(place); sizes.observe(box) }
      }
      shown = true
      paint()
      place()
      // The controls lay themselves out, and the scene draws its first frames, a moment after they are asked for.
      for (const ms of [80, 400, 1500]) later(place, ms)
    },
    /** The card, for a scene whose author asks for it (a demo): once in a run. The button is put up too if there is none yet. */
    ask(given) {
      if (closed || recorded) return
      const { title, withSound, withoutSound, remember, wait, ...where } = given
      if (!shown) this.show(where)
      words = { title, withSound, withoutSound, remember, wait }
      const last = kept.load(SOUND_ON), when = Number(kept.load(SOUND_ASKED)) || 0
      const fresh = !(Date.now() - when >= 0 && Date.now() - when < SOUND_VISIT)
      if (!asked && fresh && !(remember && typeof last === 'boolean')) raise()
      asked = true
    },
    /** Is the scene's sound on? Not while the card is still waiting for its answer. */
    get on() { return on && !asking },
    get asking() { return asking },
    get shown() { return shown },
    /** Where the button is, in the scene's points: { x, y, size }, or null when there is none. */
    get place() { return shown && at ? { ...at } : null },
    /** Switch the sound: `keep` when a person chose it, so that it is remembered. */
    set,
    /** The scene's own code switched the sound (Python's mute_sound, which the page hears of): the button shows it. */
    heard(value) { on = !!value; paint() },
    toggle() { set(!on, true) },
    /** Is this point of the scene on the button? */
    over(x, y) { return shown && !!at && !asking && x >= at.x && x <= at.x + at.size && y >= at.y && y <= at.y + at.size },
    /** A key went down on the scene: true when it was the button's (M, unless the scene reads M itself). */
    key(e) {
      if (!shown || asking || ownKey || !options.key || e.repeat || e.ctrlKey || e.metaKey || e.altKey) return false
      if (String(e.key).toLowerCase() !== options.key) return false
      set(!on, true)
      return true
    },
    remove() {
      shown = false
      if (button) { button.remove(); button = null }
      if (sizes) { sizes.disconnect(); sizes = null }
    },
    close() {
      closed = true
      for (const t of timers) clearTimeout(t)
      timers.clear()
      if (card) card.remove()
      card = null
      asking = false
      this.remove()
    },
  }
}
/** Does the scene read the M key itself? Then M is the scene's, and the button leaves it alone. */
const readsM = (source) => /(["'`])[mM]\1|\bKeyM\b/.test(source)

/**
 * The sound button of one run of a scene. pyctures.js has one line for it, after the scene's sound and renderer are
 * made: `keep(scene, source, active)`, where `scene` is its Scene and `active()` says it has the keyboard.
 * EVERYTHING ELSE IS DONE HERE, by putting this run's own functions on that Scene in front of its usual ones, and
 * taking them off again when the run stops or fails:
 *   renderer.push   Python's commands to the fixed handle 14 (`show`, `ask`, `set`, `remove`, `listen`) are taken out
 *                   of a frame as it arrives, before its sounds go on: the card must be up first
 *   requestFrame    Python is not asked for a frame while the card is up and the scene waits behind it; and what has
 *                   changed (`news`) goes with the next frame, as an event for the function Python gave `listen`
 *   hush            the scene's sound is paused while the card is up
 *   sound.send      Python's own mute_sound() is heard of, so the button shows it; and a scene switched off before it
 *                   has made a sound says so with its first (nothing is loaded to switch off a scene with no sound)
 *   cover, and a host's sound.onState   while the card asks, or the sound is switched off, the words that ask for a
 *                   tap are not shown and a host is told 'asking' or 'off' in place of 'waiting'
 *   stop, showError   the button and the card go with the run
 */
function keep(scene, source, active) {
  // The scene's functions as they are now (its own, or a recorder's that were put there first): ours go in front of
  // them for the run, and they are put back as they were.
  const NAMES = ['cover', 'hush', 'requestFrame', 'stop', 'showError']
  const had = NAMES.filter((name) => Object.prototype.hasOwnProperty.call(scene, name))
  const own = Object.fromEntries(NAMES.map((name) => [name, scene[name]]))
  const sound = scene.sound, renderer = scene.renderer, host = scene.opt.sound, saved = scene.saved
  const clock = () => performance.now() / 1000
  let holding = false, said = '', took = '', listener = 0, closed = false
  let used = false, owed = false, lastNow = 0, lastAt = 0, hidden = ''

  // --- the scene's sound, switched off and on: the player's own `master` command, in the scene's batches
  const send = sound.send
  const mute = (off) => {
    if (!used) { owed = off; return }
    const t = lastNow + (clock() - lastAt)   // Python's clock now, as near as the last batch said
    send.call(sound, { synths: 1, now: t, cmds: [{ op: 'master', mute: off, t }] })
  }
  sound.send = (batch) => {
    if (batch && Array.isArray(batch.cmds)) {
      for (const c of batch.cmds) if (c && c.op === 'master' && c.mute != null) { owed = false; keeper.heard(!c.mute); changed() }
      if (!used && owed) batch.cmds.unshift({ op: 'master', mute: true })
      used = true
      if (typeof batch.now === 'number') { lastNow = batch.now; lastAt = clock() }
    }
    return send.call(sound, batch)
  }

  // --- what is said of the sound's state, over the scene and to a host
  const WAITING = /turn the sound/
  const quiet = () => (keeper.asking ? 'asking' : !keeper.on ? 'off' : null)
  scene.cover = (text) => {
    if (quiet() && WAITING.test(text || '')) { hidden = text; text = '' }
    return own.cover.call(scene, text)
  }
  const theirs = host && host.onState
  if (theirs) host.onState = (state) => theirs.call(host, quiet() || state)
  const changed = () => {
    const state = quiet() || (sound.player && sound.player.state)
    if (!state) return
    const shown = scene.coverEl ? scene.coverEl.textContent : ''
    if (quiet() && WAITING.test(shown)) scene.cover(shown)
    else if (state === 'waiting' && !shown) scene.cover(hidden || 'Click, tap or press a key to turn the sound on')
    if (theirs) theirs.call(host, state)
  }

  const keeper = soundSwitch({
    box: scene.el, canvas: scene.canvas, ownKey: readsM(source), recorded: !!scene.stepping,
    // The on-screen controls, when the scene has made some (asked this way, nothing is loaded to find out).
    controls: () => { const panel = scene.canvas[Symbol.for('dials.panel')]; return panel ? panel.api : null },
    kept: {
      load: (name) => { try { return JSON.parse(saved.all()[name]) } catch (e) { return undefined } },
      save: (name, value) => saved.save(name, JSON.stringify(value)),
    },
    apply: (on) => { mute(!on); changed() },
    // The card went up, or came down. Behind it Python is not asked for a frame: the scene waits as it was drawn.
    hold: (asking, wait) => {
      holding = asking && wait
      scene.hush()
      if (!holding) scene.resume()
      changed()
    },
  })
  if (!keeper.on) mute(true)
  scene.hush = () => { if (keeper.asking) sound.pause(); else own.hush.call(scene) }

  // --- Python's commands, and what Python is told
  const api = {
    show: (options) => keeper.show(soundOptions(options, 'sound_button()')),
    ask: (options) => keeper.ask(soundOptions(options, 'ask_about_sound()', true)),
    set: (on) => keeper.set(on),
    remove: () => keeper.remove(),
    listen: (id) => { listener = id },
  }
  const push = renderer.push
  renderer.push = (cmds, ...rest) => {
    if (cmds) {
      for (let i = 0; i < cmds.length; i++) {
        const c = cmds[i]
        if (c[3] !== 14 || c[0] !== 'call') continue
        try { api[c[4]](...c[5]) } catch (e) { console.error(e) }
        cmds[i] = ['free', 0, 0]
      }
    }
    return push.call(renderer, cmds, ...rest)
  }
  /** What Python is told, when it has changed: whether the sound is on, whether the card is up, and where the button is. */
  const news = () => {
    const at = keeper.place
    const now = { on: keeper.on, asking: keeper.asking, box: at ? [at.x, at.y, at.size] : null }
    const text = JSON.stringify(now)
    if (text === said) return null
    said = text
    return now
  }
  scene.requestFrame = (now) => {
    if (holding) return
    const r = scene.r
    if (listener && r.live && !r.busy) { const e = news(); if (e) r.events.push({ k: 'cb', id: listener, e }) }
    return own.requestFrame.call(scene, now)
  }

  // M is the button's while this scene has the keyboard (unless the scene reads M itself): Python hears neither end of it.
  const key = (e) => {
    if (e.type === 'keyup') { if (took && e.code === took) { took = ''; e.stopPropagation() } return }
    const t = e.target
    if (!active() || (t && (t.isContentEditable || /^(?:INPUT|TEXTAREA|SELECT)$/.test(t.tagName)))) return
    if (keeper.key(e)) { took = e.code; e.stopPropagation() }
  }
  window.addEventListener('keydown', key, true)
  window.addEventListener('keyup', key, true)

  const close = () => {
    if (closed) return
    closed = true
    holding = false
    keeper.close()
    window.removeEventListener('keydown', key, true)
    window.removeEventListener('keyup', key, true)
    if (theirs) host.onState = theirs
    for (const name of NAMES) { if (had.includes(name)) scene[name] = own[name]; else delete scene[name] }
    delete scene.manners
  }
  scene.stop = () => { close(); return own.stop.call(scene) }
  scene.showError = (message, line) => { close(); return own.showError.call(scene, message, line) }
  /** For a host and the tests: the switch as it is. */
  scene.manners = { get on() { return keeper.on }, get asking() { return keeper.asking }, get holding() { return holding }, get muted() { return !keeper.on || keeper.asking } }
  return scene.manners
}

export { soundOptions, soundSwitch, readsM, keep }
