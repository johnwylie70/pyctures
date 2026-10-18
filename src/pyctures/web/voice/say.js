/**
 * say(): a scene that talks. Part of pictures.js, in a folder of its own and fetched only by a scene that calls `say`.
 *
 *   say("Hello")                                  the computer says it; gives back how many seconds the line takes
 *   say("Half of the width is the middle.", { voice: "calm", lang: "en" })
 *   await sleep(say("Hello") + 0.25)              (or time the next picture from it)
 *
 * With nothing set up it is the DRAFT VOICE: the browser's speech (speechSynthesis), free, on this device, no
 * network and no account. It is heard live. It cannot be recorded into a video file: the speech goes straight to
 * the speaker, so a scene that is recorded a frame at a time says so for every line that has no generated audio.
 *
 * A VOICE HOST is what makes a better voice possible. The library never talks to a provider and never generates
 * anything, on run or at any other time: it asks the host (`runScene(el, { voice: host })`, else
 * `window.pictureHost.voice`), which has this shape (docs-internal/notes/video-production-contracts.md, section 1):
 *
 *   lookup(req)     what is known about the line right now: { key, file, duration, words?, provider, voice, lang } or null
 *   note(req)       the line was asked for (so an editor can list the lines that have no audio yet)
 *   speakDraft(req) optional: speak it on this device now, in the host's own way (else the browser's speech is used)
 *
 * where `req` is { text, voice?, lang } (`note` also gets source: "literal" | "runtime" and line when it is known).
 *
 * WHEN THE HOST HAS THE LINE its audio file plays on the scene's clock, and `say` gives back the file's measured
 * duration. When the scene is recorded a frame at a time (`stepped`), the file goes through the stepped sound
 * (synths.js's loadSample and play at the clock's exact sample), so it lands on the exact sample.
 * WHEN IT DOES NOT, the draft voice speaks it (live only) and `say` gives back an estimate: 2.5 words a second,
 * never less than 0.8. A scene is a function of its time and of that number, so it does not change between runs.
 *
 * A TALKING FACE needs nothing more than say():
 *
 *   speaking()          true while a line is being said
 *   voiceLevel()        how loud the voice is right now, 0 (quiet) to 1 (loud); voice_level() in Python
 *   voiceShape()        the mouth now: { width: 0 round (oo) to 1 spread (ee), height: the level, viseme }; voice_shape()
 *   mouth(x, y)         draws a mouth: a line when it is quiet, opening with the voice when it talks
 *   mouth(x, y, { size: 60, style: "smile", color: "red" })     style is "oval" (the default), "smile" or "robot"
 *
 * WHERE THE LEVEL COMES FROM. A line a voice host has recorded is a real sound: voiceLevel() is the loudness of its
 * audio at this moment of the scene (the root mean square of the last 512 samples, about a hundredth of a second, the line's sound has made, times 12,
 * at most 1), so a recorded scene is exact for each frame. The draft voice is the browser's speech and gives no
 * samples at all, so its level is MADE UP from the words: each syllable of the line (seeded by the text, so two runs
 * and two recordings are the same) opens and closes the mouth, with a pause at a comma or a full stop. It starts when
 * the browser says the speech started (else when say() was called), is moved on to each word as the browser says it
 * reached it, and ends when the browser says it ended (else after the line's estimated time). THAT IS NOT TRUE
 * LIP-SYNC: the mouth moves as a talking mouth would, not with the sounds. Both are smoothed, so the mouth does not flicker.
 *
 * VOICES AND CHARACTERS. Two faces can talk to each other, each with a voice of its own:
 *
 *   voices()                  the voices on offer: [{ name, lang, default, source: "device" | "host" }], English first. A device
 *                             may load its voices late: until then the list is empty, so ask again a moment later.
 *   const bob = speaker({ voice: "deep", pitch: 1, rate: 1, lang: "en", name: "Bob" })
 *   bob.say("Hello")          like say(): gives back the line's seconds. bob.sayAt("Hello") gives { start, duration, end }
 *   bob.level()  bob.shape()  bob.speaking()      the same as voiceLevel(), voiceShape() and speaking(), for this speaker only
 *   mouth(x, y, { speaker: bob })                 opens only while bob's line is played (voiceLevel(bob), voiceShape(bob) too)
 *   sayAt("Hi", { speaker: bob })                 say(), giving { start, duration, end } in seconds from now
 *
 * `voice` is an exact voice name, a provider-qualified id (`system:Samantha`, `kokoro:af_heart`, `hq:nova`, `draft:`; a bare
 * name is read as `system:` first, then by name anywhere), a PRESET WORD ("robot", "high", "deep", "squeaky", "slow", "fast": each sets a pitch and
 * a rate and looks for an installed voice that suits it, and works on any device because it falls back to the device's
 * default voice) or a host's voice id. A speaker is a role, not one provider's voice: `like: { gender, age, pitch, rate }`
 * describes it in words every provider can match, and `fallback: ["system:Samantha", "high"]` lists voices to try in turn.
 * The draft voice picks the best device match for the voice, then each fallback, then `like`, then the default. A host may
 * have `resolveVoice(spec) -> { voice, exact, note }` to cast the speaker in its own set; `lookup` then gets that voice,
 * and `note` gets `resolved` and `exact` (false when a stand-in was chosen). The draft voice honours `pitch` (0 to 2) and `rate` (0.1 to 4) as the browser does;
 * a generated line is the host's: its entry is the chosen provider's voice and pitch and rate are the host's to apply.
 *
 * TURN-TAKING. Lines said by speakers go through ONE QUEUE: a second line waits for the first to finish, so a
 * conversation does not overlap, and each line starts when the one before it ends. say() gives back the duration as it
 * always did; sayAt() also says when the line starts (seconds from the call, 0 when nothing is queued), so
 * `sleep(bob.sayAt("Hi").end)` waits for the line to end. A line said with plain say() (no speaker) is not queued.
 *
 * `createSay(options)` is what pictures.js calls for a scene; it is exported for a host or a test that wants the
 * same without a page. options:
 *   host()      the voice host now, or nothing
 *   sound()     the scene's sound library functions ({ loadSample, soundTime }), or nothing
 *   recorded    true when the scene is recorded a frame at a time
 *   code        the scene's text, so that a literal line can be told from one made while it runs
 *   speech()    the browser's speechSynthesis (else the global one); Utterance, the SpeechSynthesisUtterance class
 *   warn(text)  where a warning goes (console.warn)
 *   live()      false once the scene has stopped
 *   clock()     the scene's time in seconds (performance.now() / 1000; a recorder steps it), for the level
 *   ctx()       the 2D context mouth() draws on, and size() its [width, height] (a mouth's size starts from the smaller)
 * It gives { say, sayAt, voices, speaker, speaking, voiceLevel, voiceShape, mouth, onVoices, names, asked, plays, unresolved, close };
 * `names` is what a scene is given (say, sayAt, voices, speaker, speaking, voiceLevel, voice_level, voiceShape, voice_shape, mouth).
 * The host may also have voices(): the voices it can make, each a name or { id, name, lang, provider } (a proposal).
 */
export const version = '0.1.0'

/** The names a scene is given. */
export const sceneNames = ['say', 'sayAt', 'voices', 'speaker', 'speaking', 'voiceLevel', 'voiceShape', 'mouth']

/** How many seconds a line takes when nothing has measured it: 2.5 words a second, at least 0.8. */
export function estimate(text) {
  const words = String(text ?? '').split(/\s+/).filter(Boolean).length
  return Math.max(0.8, words / 2.5)
}

// --- voices and characters -----------------------------------------------------------------------------------------------

/** The preset words of a speaker's voice: a pitch and a rate, and the names of the installed voices that suit it. */
const HIGH = /\b(?:female|samantha|karen|victoria|zira|fiona|moira|tessa|susan|kate|serena|allison)\b/i
export const voicePresets = {
  robot: { pitch: 0.6, rate: 0.9, like: /zarvox|trinoids|cellos|bad news|bahh|boing|robot/i },
  high: { pitch: 1.6, rate: 1, like: HIGH },
  deep: { pitch: 0.4, rate: 0.9, like: /\b(?:male|daniel|alex|fred|thomas|oliver|arthur|david|mark|george|rishi)\b/i },
  squeaky: { pitch: 2, rate: 1.15, like: HIGH },
  slow: { pitch: 1, rate: 0.6 },
  fast: { pitch: 1, rate: 1.6 },
}
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n))
const baseLang = (l) => String(l || '').toLowerCase().replace('_', '-').split('-')[0]

/** The settings of a speaker, or what is wrong with them. */
function checkSpeaker(o) {
  if (o == null) o = {}
  if (typeof o === 'string') o = { voice: o }
  if (typeof o !== 'object') throw new Error('speaker() takes its settings in braces, as in speaker({ voice: "deep", pitch: 1, rate: 1 })')
  const known = ['voice', 'pitch', 'rate', 'lang', 'name', 'like', 'fallback']
  for (const k of Object.keys(o)) if (!known.includes(k)) throw new Error(`speaker(): ${JSON.stringify(k)} is not a setting; the settings are ${known.join(', ')}`)
  if (o.voice != null && o.voice !== '' && typeof o.voice !== 'string') throw new Error(`speaker(): the voice is a name such as "deep" or "robot", not ${JSON.stringify(o.voice)}`)
  const number = (name, lo, hi) => {
    const v = o[name] ?? 1
    if (typeof v !== 'number' || !isFinite(v) || v < lo || v > hi) throw new Error(`speaker(): ${name} is a number from ${lo} to ${hi} (1 is normal), not ${JSON.stringify(v)}`)
    return v
  }
  if (o.lang != null && (typeof o.lang !== 'string' || !o.lang.trim())) throw new Error(`speaker(): the language is such as "en" or "fr", not ${JSON.stringify(o.lang)}`)
  if (o.name != null && typeof o.name !== 'string') throw new Error(`speaker(): the name is text, not ${JSON.stringify(o.name)}`)
  let like
  if (o.like != null) {
    const l = o.like
    if (typeof l !== 'object' || Array.isArray(l)) throw new Error('speaker(): like describes a voice, as in like: { gender: "female", age: "child", pitch: 1.3, rate: 1 }')
    for (const k of Object.keys(l)) if (!['gender', 'age', 'pitch', 'rate'].includes(k)) throw new Error(`speaker(): like has gender, age, pitch and rate, not ${JSON.stringify(k)}`)
    for (const k of ['gender', 'age']) if (l[k] != null && typeof l[k] !== 'string') throw new Error(`speaker(): like.${k} is a word such as ${k === 'gender' ? '"female"' : '"child"'}, not ${JSON.stringify(l[k])}`)
    for (const k of ['pitch', 'rate']) if (l[k] != null && (typeof l[k] !== 'number' || !(l[k] > 0))) throw new Error(`speaker(): like.${k} is a number above 0, not ${JSON.stringify(l[k])}`)
    like = { ...l }
  }
  if (o.fallback != null && (!Array.isArray(o.fallback) || o.fallback.some((f) => typeof f !== 'string'))) throw new Error('speaker(): fallback is a list of voices to try in turn, as in fallback: ["system:Samantha", "high"]')
  return { voice: o.voice || undefined, pitch: number('pitch', 0, 2), rate: number('rate', 0.1, 4), lang: o.lang ? String(o.lang) : 'en', name: o.name || undefined, ...(like ? { like } : {}), fallback: o.fallback ? [...o.fallback] : [] }
}

/**
 * The installed voice for a speaker's `voice`, and the pitch and rate that go with it: an exact name (or uri) first, then
 * a preset word (its pitch and rate, with the first installed voice for the language that suits it, else the device's
 * default), then a part of a name. { voice: the device's voice or undefined, pitch, rate } with the preset's own numbers.
 */
export function pickVoice(want, lang, voices) {
  const same = (v) => baseLang(v.lang) === baseLang(lang)
  const w = want ? String(want).toLowerCase() : ''
  const exact = w && voices.find((v) => String(v.name).toLowerCase() === w || v.voiceURI === want)
  if (exact) return { voice: exact, pitch: 1, rate: 1 }
  const preset = w && Object.hasOwn(voicePresets, w) ? voicePresets[w] : null
  if (preset) return { voice: (preset.like && voices.find((v) => same(v) && preset.like.test(v.name))) || undefined, pitch: preset.pitch, rate: preset.rate }
  return { voice: (w && voices.find((v) => String(v.name).toLowerCase().includes(w) && same(v))) || undefined, pitch: 1, rate: 1 }
}

const FEMALE = /\b(?:female|woman|samantha|karen|victoria|zira|fiona|moira|tessa|susan|kate|serena|allison|amelie|alice|ava|nicky|sara|joanna)\b/i
const MALE = /\b(?:male|man|daniel|alex|fred|thomas|oliver|arthur|david|mark|george|rishi|ralph|bruce|junior)\b/i
const AGE = { child: 1.3, kid: 1.3, young: 1.1, adult: 1, old: 0.9, elderly: 0.85 }

/**
 * Cast a speaker on the voices a device has: the speaker's voice (`system:Samantha`, a bare name, a preset word, `draft:`,
 * a provider this device does not have is skipped), then each of its fallbacks, then the best match for `like` (gender
 * and the language), then the language's default. Gives { voice (the device's or undefined), id (what was chosen),
 * pitch, rate (the preset's and `like`'s, not the speaker's own), exact (the speaker's own voice was found, or it named none) }.
 */
export function castVoice(sp, voices) {
  const lang = sp.lang || 'en'
  const same = (v) => baseLang(v.lang) === baseLang(lang)
  const like = sp.like || {}
  const shape = (pitch, rate) => ({ pitch: pitch * (like.pitch ?? AGE[String(like.age || '').toLowerCase()] ?? 1), rate: rate * (like.rate ?? 1) })
  const candidates = [sp.voice, ...(sp.fallback || [])].filter(Boolean).map(String)
  for (let i = 0; i < candidates.length; i++) {
    const m = /^([a-z][\w-]*):(.*)$/i.exec(candidates[i])
    const provider = m ? m[1].toLowerCase() : '', name = m ? m[2] : candidates[i]
    let found = null
    if (provider === 'draft') found = { voice: voices.find((v) => v.default && same(v)) || voices.find(same), pitch: 1, rate: 1, any: true }
    else if (provider === 'preset' || !provider || provider === 'system') {
      const p = pickVoice(name, lang, voices)
      const preset = (provider === 'preset' || !provider) && Object.hasOwn(voicePresets, name.toLowerCase())
      if (p.voice || preset) found = { ...p, any: preset }
      else if (!provider) { const any = voices.find((v) => String(v.name).toLowerCase() === name.toLowerCase()); if (any) found = { voice: any, pitch: 1, rate: 1 } }
    }
    if (found && (found.voice || found.any)) return { voice: found.voice, id: found.voice ? found.voice.name : candidates[i], ...shape(found.pitch, found.rate), exact: i === 0 }
  }
  // Nothing named is here: the best match for the description, else the language's default.
  const gender = String(like.gender || '').toLowerCase()
  const want = gender.startsWith('f') ? FEMALE : gender.startsWith('m') ? MALE : null
  const score = (v) => (same(v) ? 4 : 0) + (want && want.test(v.name) && !(want === MALE && FEMALE.test(v.name)) ? 2 : 0) + (v.default ? 1 : 0)
  const best = [...voices].sort((a, b) => score(b) - score(a))[0]
  return { voice: best && same(best) ? best : voices.find(same), id: best ? best.name : 'draft:', ...shape(1, 1), exact: !candidates.length }
}

// --- the draft voice's made-up level, and the mouth ----------------------------------------------------------------------

/** The loudness of a recorded line is its samples' root mean square times this, at most 1. */
const LEVEL_GAIN = 12
/** How fast the level follows a rise and a fall, in seconds: quick to open, slower to close, so the mouth does not flicker. */
const ATTACK = 0.015, RELEASE = 0.05

/** A number from the text (FNV-1a), so the same words always give the same mouth. */
function seedOf(text) {
  let h = 0x811c9dc5
  for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 0x01000193) }
  return h >>> 0
}
/** A small seeded random stream (mulberry32): the same seed gives the same numbers. */
function seeded(seed) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return (((t ^ (t >>> 14)) >>> 0) / 4294967296)
  }
}

/** How a vowel shapes the mouth: how far it opens (amp) and how wide it is (width, 0 round like "oo", 1 spread like "ee"). */
const VOWELS = { a: [1, 0.4], o: [0.9, 0.12], u: [0.6, 0.02], e: [0.7, 0.8], i: [0.5, 0.95], y: [0.5, 0.9] }
const VOWEL = /[aeiouyàáâäãåæèéêëìíîïòóôöõøùúûüœ]+/gi

/**
 * The made-up mouth of a line of the draft voice, syllable by syllable. Each word is split at its runs of vowels. A
 * syllable opens the mouth for its vowel (a tall and a little wide, o tall and round, u small and round, e wide and
 * half open, i wide and nearly shut), closes between syllables, opens late after m, b and p (the lips meet first),
 * and a word ends in a short gap, a comma in a longer one and a full stop in a pause. The size and length of each
 * are varied by a stream seeded from the text, so the same words always give the same mouth. Gives
 * { syllables: [{ from, to, amp, width }] in seconds, words: [{ at, char }], seconds }, spread over `seconds` (the
 * line's estimated length).
 */
export function mouthProfile(text, seconds = estimate(text)) {
  text = String(text ?? '')
  const random = seeded(seedOf(text))
  const syllables = [], words = []
  let cursor = 0
  for (const m of text.matchAll(/\S+/g)) {
    const word = m[0]
    words.push({ at: cursor, char: m.index })
    const groups = [...word.matchAll(VOWEL)].slice(0, 6)
    // A word with no vowel (hm, shh) is one small sound.
    const list = groups.length ? groups : [{ 0: 'm', index: 0 }]
    let before = 0
    for (const g of list) {
      const onset = word.slice(before, g.index).toLowerCase()
      before = g.index + g[0].length
      const base = g[0][0].normalize('NFD')[0].toLowerCase()
      const [open, wide] = groups.length ? VOWELS[base] || [0.7, 0.5] : [0.35, 0.5]
      const length = 0.8 + 0.4 * random()
      const lips = /[mbp]/.test(onset) ? 0.2 : 0
      syllables.push({ from: cursor + length * lips, to: cursor + length * 0.85, amp: Math.min(1, open * (0.75 + 0.25 * random())), width: Math.min(1, Math.max(0, wide + (random() - 0.5) * 0.16)) })
      cursor += length
    }
    cursor += 0.35 + (/[.!?…]["')\]]*$/.test(word) ? 1 : /[,;:]["')\]]*$/.test(word) ? 0.5 : 0)
  }
  const scale = cursor > 0 ? seconds / cursor : 1
  return { syllables: syllables.map((s) => ({ from: s.from * scale, to: s.to * scale, amp: s.amp, width: s.width })), words: words.map((w) => ({ at: w.at * scale, char: w.char })), seconds }
}

/** The made-up mouth `pos` seconds into the line: { open: 0 to 1, width: 0 to 1 }, a half sine for each syllable. */
export function mouthAt(profile, pos) {
  const list = profile.syllables
  let lo = 0, hi = list.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1, s = list[mid]
    if (pos < s.from) hi = mid - 1
    else if (pos >= s.to) lo = mid + 1
    else return { open: s.amp * Math.sin(Math.PI * (pos - s.from) / (s.to - s.from)) ** 0.7, width: s.width }
  }
  return { open: 0, width: 0.5 }
}

/** The styles of mouth, and the size one has when nothing is said: a sixth of the scene's smaller side, across. */
export const mouthStyles = ['oval', 'smile', 'robot']
export const defaultMouthSize = (width, height) => 0.16 * Math.min(width, height)

/** The style and size of a mouth from its settings, or what is wrong with them. */
function checkMouth(o) {
  const style = o.style ?? 'oval'
  if (!mouthStyles.includes(style)) throw new Error(`mouth(): the style is one of ${mouthStyles.map((s) => JSON.stringify(s)).join(', ')}, not ${JSON.stringify(style)}`)
  const size = o.size ?? defaultMouthSize(...(o.area || [320, 180]))
  if (typeof size !== 'number' || !(size > 0)) throw new Error(`mouth(): the size is a number of pixels above 0, as in mouth(x, y, { size: 60 }), not ${JSON.stringify(size)}`)
  return { style, size }
}

/**
 * Draw a mouth at (x, y), its middle, on a 2D context. `level` is 0 (a closed line) to 1 (wide open).
 * o: { size (its width, in pixels; else by area), style, color, level, width (0 round like "oo" to 1 spread like "ee", 0.5 when not said), area: [width, height] }.
 * The context's own settings are put back after.
 */
export function drawMouth(ctx, x, y, o = {}) {
  const { style, size } = checkMouth(o)
  const l = Math.min(1, Math.max(0, +o.level || 0)), t = Math.max(2, size * 0.09)
  const w = Math.min(1, Math.max(0, o.width ?? 0.5))
  ctx.save()
  ctx.fillStyle = ctx.strokeStyle = o.color ?? 'black'
  ctx.lineWidth = t
  ctx.lineCap = ctx.lineJoin = 'round'
  ctx.beginPath()
  if (style === 'oval') {
    // Hangs from the line it closes to, like a jaw.
    // Wide spreads it sideways and flattens it; round makes it taller and narrower.
    const rx = size * (0.32 + 0.16 * l) * (0.7 + 0.6 * w), ry = Math.max(t / 2, size * 0.5 * l * (1.3 - 0.6 * w))
    ctx.ellipse(x, y - t / 2 + ry, rx, ry, 0, 0, Math.PI * 2)
    ctx.fill()
  } else if (style === 'smile') {
    // The top edge is a smile; the bottom edge drops away from it as the voice gets louder.
    const top = size * 0.22, bottom = top + size * 1.1 * l
    const half = size / 2 * (0.8 + 0.4 * w)
    ctx.moveTo(x - half, y)
    ctx.quadraticCurveTo(x, y + top, x + half, y)
    ctx.quadraticCurveTo(x, y + bottom, x - half, y)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  } else {
    // Five bars, level with each other's middles, each taller than a line by its share of the voice.
    const shape = [0.6, 0.9, 1, 0.85, 0.7], gap = size * 0.06, wide = (size - gap * 4) / 5
    for (let i = 0; i < 5; i++) {
      const high = t + size * 0.55 * l * shape[i]
      ctx.rect(x - size / 2 + i * (wide + gap), y - high / 2, wide, high)
    }
    ctx.fill()
  }
  ctx.restore()
}

const ESCAPES = { n: '\n', t: '\t', r: '\r', b: '\b', f: '\f', v: '\v', 0: '\0' }
/** The text of a string literal written in a scene (quotes included), or null when it holds something made while it runs. */
function unquote(literal) {
  const q = literal[0]
  const body = literal.slice(1, -1)
  if (q === '`' && body.includes('${')) return null
  let out = ''
  for (let i = 0; i < body.length; i++) {
    const c = body[i]
    if (c !== '\\') { out += c; continue }
    const n = body[++i]
    if (n === 'u' && /^[0-9a-fA-F]{4}$/.test(body.slice(i + 1, i + 5))) { out += String.fromCharCode(parseInt(body.slice(i + 1, i + 5), 16)); i += 4 }
    else if (n === 'x' && /^[0-9a-fA-F]{2}$/.test(body.slice(i + 1, i + 3))) { out += String.fromCharCode(parseInt(body.slice(i + 1, i + 3), 16)); i += 2 }
    else out += ESCAPES[n] ?? n
  }
  return out
}

/** One string literal written in code. (A template with `${` in it is not text that is known beforehand: unquote() gives null.) */
const STRING = new RegExp(String.raw`"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|` + '`(?:[^`\\\\]|\\\\.)*`', 'g')

/**
 * The lines a scene says with text written out in the call, as [{ text, line, voice?, lang? }]: `say("Hello")`, but
 * not `say(name)` or `say("Hi " + name)`. The voice and the language are read when they are written out too, in
 * either spelling: `{ voice: "calm", lang: "fr" }`, `voice="calm", lang="fr"`, or Python's `"calm", "fr"` in place.
 */
export function literalsIn(code) {
  const found = []
  code = String(code ?? '')
  const call = new RegExp(String.raw`(?:^|[^.\w$])say\s*\(\s*(${STRING.source})\s*([,)])`, 'g')
  for (const m of code.matchAll(call)) {
    const text = unquote(m[1])
    if (text === null) continue
    const at = m.index + m[0].indexOf('say')
    const entry = { text, line: code.slice(0, at).split('\n').length }
    if (m[2] === ',') {
      // The rest of the call, to the bracket that closes it.
      let i = m.index + m[0].length, depth = 1
      for (; i < code.length && depth; i++) depth += code[i] === '(' ? 1 : code[i] === ')' ? -1 : 0
      const rest = code.slice(m.index + m[0].length, i - 1)
      const word = (name) => { const w = rest.match(new RegExp(String.raw`\b${name}\s*[:=]\s*(${STRING.source})`)); return w ? unquote(w[1]) : null }
      const strings = rest.match(new RegExp(String.raw`^\s*(${STRING.source})\s*(?:,\s*(${STRING.source}))?\s*$`))
      const voice = word('voice') ?? (strings ? unquote(strings[1]) : null)
      const lang = word('lang') ?? (strings && strings[2] ? unquote(strings[2]) : null)
      if (voice) entry.voice = voice
      if (lang) entry.lang = lang
    }
    found.push(entry)
  }
  return found
}

export function createSay(options = {}) {
  const warn = options.warn || ((text) => console.warn(text))
  const live = options.live || (() => true)
  const recorded = !!options.recorded
  const literal = new Map()
  for (const l of literalsIn(options.code)) if (!literal.has(l.text)) literal.set(l.text, l.line)
  const asked = []          // every distinct line the scene asked for, as the host is told: { text, voice?, lang, source, line? }
  const plays = []          // every recorded-file play: { key, file, at, duration }
  const unresolved = []     // lines with no audio that a recording could not have
  const told = new Set()
  const samples = new Map() // entry key -> the sample loaded for it
  const once = new Set()
  let spoke = false
  const now = options.clock || (() => globalThis.performance.now() / 1000)
  const lines = []          // the lines being said: { audio: the sample } or { profile, ... } for the draft voice
  const speakers = new Set()  // the speakers made here
  let tail = 0              // when the speakers' queue is free again, on the scene's clock
  let queued = null         // the draft line last put in the queue
  const tellOnce = (key, text) => { if (once.has(key)) return; once.add(key); warn(text) }
  const shown = (text) => JSON.stringify(text.length > 40 ? text.slice(0, 37) + '...' : text)

  function speech() {
    const s = options.speech ? options.speech() : globalThis.speechSynthesis
    return s && typeof s.speak === 'function' ? s : null
  }
  /** The draft voice: the browser's speech. Live only; it has no samples to record. */
  function speakDraft(req, line, sp) {
    const synth = speech()
    const Utterance = options.Utterance || globalThis.SpeechSynthesisUtterance
    if (!synth || typeof Utterance !== 'function') {
      tellOnce('nospeech', 'say(): this browser has no speech, so the lines are not spoken. The text of each is still timed.')
      return false
    }
    try {
      const u = new Utterance(req.text)
      u.lang = req.lang
      const voices = typeof synth.getVoices === 'function' ? synth.getVoices() || [] : []
      const want = req.voice ? String(req.voice).toLowerCase() : ''
      const same = (v) => String(v.lang || '').toLowerCase().replace('_', '-').split('-')[0] === req.lang.toLowerCase().split('-')[0]
      const picked = sp ? castVoice(sp, voices) : null
      const chosen = (picked ? picked.voice : (want && voices.find((v) => String(v.name).toLowerCase() === want || v.voiceURI === req.voice))
        || (want && voices.find((v) => String(v.name).toLowerCase().includes(want) && same(v))))
        || voices.find((v) => String(v.lang || '').toLowerCase().replace('_', '-') === req.lang.toLowerCase())
        || voices.find((v) => v.default && same(v))
        || voices.find(same)
      if (chosen) u.voice = chosen
      // A speaker's pitch and rate: the preset word's own, times the speaker's.
      if (sp) { u.pitch = clamp((picked.pitch ?? 1) * sp.pitch, 0, 2); u.rate = clamp((picked.rate ?? 1) * sp.rate, 0.1, 10) }
      // The browser says when the speech starts, which word it has reached and when it ends, if it does: the mouth follows.
      if (line) {
        u.onstart = () => { line.begun = true; line.start = now(); line.anchor = null; if (queued === line) tail = line.start + line.seconds }
        u.onboundary = (e) => {
          if (!e || (e.name && e.name !== 'word') || !(e.charIndex >= 0)) return
          let word = 0
          while (word + 1 < line.profile.words.length && line.profile.words[word + 1].char <= e.charIndex) word++
          line.begun = true
          line.anchor = { time: now(), pos: line.profile.words[word]?.at ?? 0 }
        }
        u.onend = u.onerror = () => { line.ended = true; if (queued === line) tail = now() }
      }
      synth.speak(u)
      spoke = true
      return true
    } catch (e) {
      tellOnce('speakfailed', `say(): the draft voice could not speak (${(e && e.message) || e}).`)
      return false
    }
  }

  /** Play a generated line: on the scene's clock, which is the stepped sound's exact sample when it is recorded. */
  function play(entry, host, text, begin, sp) {
    const sound = options.sound ? options.sound() : null
    if (!sound || typeof sound.loadSample !== 'function') {
      tellOnce('nosound', 'say(): the line has its audio, but this scene has no sound to play it through.')
      return
    }
    try {
      let sample = samples.get(entry.key)
      if (!sample) {
        sample = sound.loadSample(entry.url || entry.file, { note: 60 })
        samples.set(entry.key, sample)
      }
      const at = typeof sound.soundTime === 'function' ? sound.soundTime() : undefined
      // The whole file, at its own pitch (a sample plays to its end, whatever the note's length).
      const wait = begin - now()
      sample.play(60, wait > 1e-6 ? { volume: 1, after: wait } : { volume: 1 })
      plays.push({ key: entry.key, file: entry.file, at: at === undefined ? at : at + Math.max(0, wait), duration: entry.duration })
      lines.push({ sample, start: begin, end: begin + entry.duration, speaker: sp, profile: mouthProfile(text, entry.duration) })
    } catch (e) {
      tellOnce('playfailed:' + entry.key, `say(): the audio of ${shown(String(entry.file))} could not be played (${(e && e.message) || e}).`)
    }
  }

  /** Say a line. Gives { duration, start: seconds from now until it begins (a speaker's line waits its turn) }. */
  function sayLine(text, opts) {
    if (typeof text !== 'string' || !text.trim()) throw new Error(`say(${text === undefined ? '' : JSON.stringify(text)}) needs the words to say, as in say("Hello")`)
    if (typeof opts === 'string') opts = { voice: opts }
    if (opts == null) opts = {}
    if (typeof opts !== 'object') throw new Error(`say(${shown(text)}, ...) takes its settings in braces, as in say("Hello", { voice: "calm", lang: "en" })`)
    const sp = opts.speaker ?? null
    if (sp && !speakers.has(sp)) throw new Error(`say(${shown(text)}, { speaker }) takes a speaker made with speaker(), as in const bob = speaker({ voice: "deep" })`)
    const req = { text, lang: sp ? sp.lang : opts.lang ? String(opts.lang) : 'en' }
    const voice = sp ? sp.voice : opts.voice
    if (voice !== undefined && voice !== null && voice !== '') req.voice = String(voice)
    // What a speaker adds for the host: its pitch and rate, when they are not the normal ones.
    if (sp && sp.pitch !== 1) req.pitch = sp.pitch
    if (sp && sp.rate !== 1) req.rate = sp.rate
    const host = options.host ? options.host() : undefined
    const line = opts.line ?? literal.get(text)
    // Casting: a host that can (resolveVoice) says which voice the speaker is in its set and whether it is the speaker's own;
    // else the device's best match, as the draft voice will use.
    let cast = null
    if (sp) {
      if (typeof host?.resolveVoice === 'function') {
        try {
          const r = host.resolveVoice({ name: sp.name, voice: sp.voice, like: sp.like, fallback: [...sp.fallback], pitch: sp.pitch, rate: sp.rate, lang: sp.lang })
          if (r && r.voice) { cast = { voice: String(r.voice), exact: !!r.exact, ...(r.note ? { castNote: String(r.note) } : {}) }; req.voice = cast.voice }
        } catch (e) { tellOnce('resolvefailed', `say(): the voice host's resolveVoice() failed (${(e && e.message) || e}).`) }
      }
      if (!cast) {
        const dev = castVoice(sp, voices().filter((v) => v.source === 'device').map((v) => ({ ...v, voiceURI: v.name })))
        cast = { voice: dev.id, exact: dev.exact }
      }
    }
    const note = { ...req, source: opts.source || (literal.has(text) ? 'literal' : 'runtime'), ...(line ? { line } : {}), ...(sp && sp.name ? { speaker: sp.name } : {}), ...(cast ? { resolved: cast.voice, exact: cast.exact, ...(cast.castNote ? { castNote: cast.castNote } : {}) } : {}) }

    // Tell the host once for each distinct line in a run: a scene that says it again each time round a loop is one entry.
    const id = JSON.stringify([text, req.voice ?? null, req.lang, ...(req.pitch || req.rate ? [req.pitch ?? 1, req.rate ?? 1] : [])])
    if (!told.has(id)) {
      told.add(id)
      asked.push(note)
      try { host?.note?.({ ...note }) } catch (e) { tellOnce('notefailed', `say(): the voice host's note() failed (${(e && e.message) || e}).`) }
    }
    if (!live()) return { duration: estimate(text), start: 0 }

    // A speaker's line waits for the line before it; any other begins at once.
    const t0 = now()
    const begin = sp ? Math.max(t0, tail) : t0
    const done = (duration) => {
      if (sp) { tail = begin + duration; queued = null }
      return { duration, start: begin - t0 }
    }

    let entry = null
    try { entry = host?.lookup?.({ ...req }) || null } catch (e) { tellOnce('lookupfailed', `say(): the voice host's lookup() failed (${(e && e.message) || e}), so the draft voice is used.`) }
    if (entry && (entry.file || entry.url) && entry.duration > 0) {
      play(entry, host, text, begin, sp)
      return done(entry.duration)
    }
    if (recorded) {
      // The draft voice is speech the platform sends to the speaker; there is nothing to put in a video.
      if (!unresolved.some((u) => u.text === text && u.voice === req.voice && u.lang === req.lang)) unresolved.push({ ...note })
      tellOnce('unresolved:' + id, `say(${shown(text)}): this line has no generated voice, and the draft voice cannot be recorded, so it is silent in this recording. Generate the voice for it first (it is on the host's list of asked lines).`)
      return done(estimate(text))
    }
    // The mouth of the draft voice: made up from the words, from its turn.
    const seconds = estimate(text)
    const talk = { profile: mouthProfile(text, seconds), start: begin, seconds, begun: false, ended: false, anchor: null, speaker: sp }
    lines.push(talk)
    let spoken = true
    if (host && typeof host.speakDraft === 'function') {
      try { host.speakDraft({ ...req }) } catch (e) { spoken = false; tellOnce('draftfailed', `say(): the voice host's speakDraft() failed (${(e && e.message) || e}).`) }
    } else spoken = speakDraft(req, talk, sp)
    if (!spoken) lines.splice(lines.indexOf(talk), 1)
    const result = done(seconds)
    if (sp && spoken) queued = talk
    return result
  }
  const say = (text, opts) => sayLine(text, opts).duration
  /** Like say(), giving { start, duration, end } in seconds from now: when the line begins (after the lines before it), how long, and when it ends. */
  const sayAt = (text, opts) => { const r = sayLine(text, opts); return { start: r.start, duration: r.duration, end: r.start + r.duration } }

  /** The voices on offer: the host's, then the device's, English first. Empty until the device has loaded its own. */
  function voices() {
    const out = []
    try {
      const h = options.host ? options.host() : undefined
      for (const v of (typeof h?.voices === 'function' && h.voices()) || []) {
        if (typeof v === 'string') out.push({ name: v, lang: 'en', default: false, source: 'host' })
        else if (v && (v.name || v.id)) out.push({ name: String(v.name ?? v.id), lang: v.lang || 'en', default: false, source: 'host', ...(v.id !== undefined ? { id: String(v.id) } : {}), ...(v.provider ? { provider: String(v.provider) } : {}) })
      }
    } catch (e) { tellOnce('voicesfailed', `voices(): the voice host's voices() failed (${(e && e.message) || e}).`) }
    const synth = speech()
    try {
      for (const v of (synth && typeof synth.getVoices === 'function' && synth.getVoices()) || []) out.push({ name: String(v.name), lang: String(v.lang || ''), default: !!v.default, source: 'device' })
    } catch (e) { /* the device has none yet */ }
    const english = (v) => baseLang(v.lang) === 'en'
    return [...out.filter(english), ...out.filter((v) => !english(v))]
  }
  /** Call back when the device has loaded its voices (or they changed). Gives a function that stops it. */
  function onVoices(callback) {
    const synth = speech()
    if (!synth || typeof synth.addEventListener !== 'function') return () => {}
    const listener = () => callback(voices())
    synth.addEventListener('voiceschanged', listener)
    return () => { try { synth.removeEventListener('voiceschanged', listener) } catch (e) { /* gone */ } }
  }

  /** A character: its own voice, pitch and rate, its own turn in the queue and its own mouth. */
  function speaker(o) {
    const set = checkSpeaker(o)
    const sp = { ...set }
    sp.say = (text) => say(text, { speaker: sp })
    sp.sayAt = (text) => sayAt(text, { speaker: sp })
    sp.level = () => step(sp).v
    sp.shape = () => shapeOf(sp)
    sp.speaking = () => speakingOf(sp)
    speakers.add(sp)
    return sp
  }
  const speakerOf = (sp, where) => {
    if (sp == null) return null
    if (!speakers.has(sp)) throw new Error(`${where} takes a speaker made with speaker(), as in const bob = speaker({ voice: "deep" })`)
    return sp
  }

  // --- speaking(), voiceLevel() and mouth() ---
  /** The sound of a recorded line right now: { open, width } from the samples its sound has made; null when the sound gives none. */
  function heard(line) {
    let samples
    try { samples = line.sample.samples && line.sample.samples() } catch (e) { return null }
    if (!samples || !samples.length) return null
    // The last 512 samples (about 10 ms): loud is how far the mouth opens; how often the wave crosses zero says low, round
    // sounds (oh, ah) from high, spread ones (ee, s), which is how wide it is.
    const n = Math.min(512, samples.length)
    let sum = 0, crossings = 0
    for (let i = samples.length - n; i < samples.length; i++) {
      sum += samples[i] * samples[i]
      if (i > samples.length - n && (samples[i] >= 0) !== (samples[i - 1] >= 0)) crossings++
    }
    return { open: Math.min(1, Math.sqrt(sum / n) * LEVEL_GAIN), width: Math.min(1, Math.max(0, (crossings / n - 0.015) / 0.05)) }
  }
  /** Is the line being said at time t? A draft line the browser has told us began is said until the browser says it ended. */
  function active(line, t) {
    if (line.sample) return t >= line.start && t < line.end
    if (line.ended) return false
    return t >= line.start && t < line.start + (line.begun ? line.seconds * 4 + 5 : line.seconds)
  }
  /** How open and how wide the loudest line's mouth is at time t, before smoothing. */
  function rawShape(t, sp) {
    let best = { open: 0, width: 0.5 }
    for (const line of lines) {
      if (sp && line.speaker !== sp) continue
      if (!active(line, t)) continue
      let v = line.sample ? heard(line) : null
      if (v === null) {
        // Made up from the words (also for a recorded line whose sound gives no samples, such as one that has not started).
        const length = line.profile.seconds
        let pos = (line.anchor ? line.anchor.pos + (t - line.anchor.time) : t - line.start)
        if (pos > length) pos = line.begun ? pos % length : -1
        v = pos < 0 ? { open: 0, width: 0.5 } : mouthAt(line.profile, pos)
      }
      if (v.open > best.open) best = v
    }
    return best
  }
  const smooth = new Map()   // a speaker (or null, for all the lines) -> { t, v, w }
  /** Is the speaker (or, with none, anyone) speaking? */
  function speakingOf(sp) {
    const t = now()
    let yes = false
    for (let i = lines.length - 1; i >= 0; i--) {
      if (active(lines[i], t) && (!sp || lines[i].speaker === sp)) yes = true
      else if (!active(lines[i], t)) {
        // A line that is over is forgotten once its level has had time to close the mouth.
        const gone = lines[i].sample ? lines[i].end : lines[i].ended ? lines[i].start : lines[i].start + lines[i].seconds * (lines[i].begun ? 4 : 1) + 5
        if (t > gone + 1) lines.splice(i, 1)
      }
    }
    return yes
  }
  const speaking = (sp) => speakingOf(speakerOf(sp, 'speaking(speaker)'))
  /** The mouth now, smoothed: quick to open and a little slower to close. The same time gives the same numbers however often it is asked. */
  function step(sp = null) {
    const t = now()
    const was = smooth.get(sp) || { t: null, v: 0, w: 0.5 }
    if (was.t === t) return was
    const target = rawShape(t, sp)
    const dt = was.t === null ? Infinity : Math.max(0, t - was.t)
    let v = was.v + (target.open - was.v) * (1 - Math.exp(-dt / (target.open > was.v ? ATTACK : RELEASE)))
    if (target.open === 0 && v < 0.01) v = 0
    const w = was.w + (target.width - was.w) * (1 - Math.exp(-dt / 0.03))
    const next = { t, v, w }
    smooth.set(sp, next)
    return next
  }
  /** How loud the voice is right now, 0 to 1 (one speaker's, or all). */
  const voiceLevel = (sp) => step(speakerOf(sp, 'voiceLevel(speaker)')).v
  function shapeOf(sp) {
    const { v, w } = step(sp)
    const viseme = v < 0.08 ? 'closed' : w > 0.65 ? 'ee' : w < 0.3 ? (v > 0.5 ? 'oh' : 'oo') : v > 0.6 ? 'ah' : 'mid'
    return { width: w, height: v, viseme }
  }
  /** The shape of the mouth now: { width: 0 round to 1 spread, height: the level, viseme: closed, oo, oh, ah, mid or ee }. */
  const voiceShape = (sp) => shapeOf(speakerOf(sp, 'voiceShape(speaker)'))
  function mouth(x, y, o) {
    if (typeof x !== 'number' || typeof y !== 'number' || !isFinite(x) || !isFinite(y)) throw new Error(`mouth(${x === undefined ? '' : JSON.stringify(x)}, ...) needs the middle of the mouth, as in mouth(width / 2, height / 2)`)
    if (o == null) o = {}
    if (typeof o !== 'object') throw new Error('mouth(x, y, ...) takes its settings in braces, as in mouth(x, y, { size: 60, style: "smile", color: "red" })')
    const { v: level, w: width } = step(speakerOf(o.speaker, 'mouth(x, y, { speaker })'))
    const ctx = options.ctx ? options.ctx() : null
    const area = options.size ? options.size() : undefined
    checkMouth({ ...o, area })
    if (ctx) drawMouth(ctx, x, y, { size: o.size, style: o.style, color: o.color, level, width, area })
    return level
  }

  return {
    say, sayAt, voices, speaker, speaking, voiceLevel, voiceShape, mouth, onVoices, asked, plays, unresolved,
    names: { say, sayAt, say_at: sayAt, voices, speaker, speaking, voiceLevel, voice_level: voiceLevel, voiceShape, voice_shape: voiceShape, mouth },
    close() {
      lines.length = 0
      if (!spoke) return
      try { speech()?.cancel?.() } catch (e) { /* nothing was speaking */ }
    },
  }
}

/**
 * PYCTURES' HALF. Pyctures (Python) runs its scene somewhere else and talks to the page by commands, so `say` there
 * is a Python function (pysay.py, beside this file in Pyctures' `voice` folder) that writes one command to the fixed
 * handle 16, and the page does the rest with the code above. pyctures.js has one line for it, after the scene's
 * sound and renderer are made: `keep(scene, source)`.
 *
 * Python cannot be answered at once, so it is TOLD the lengths that are known before it starts: for every line written
 * out in the scene (and every line an earlier run of this scene made while it ran) the page asks the host's `lookup`
 * and puts the measured durations in the run's start information (`info.say`: a list of [text, voice, lang, seconds]).
 * A line the host had no entry for then is timed by the same estimate in Python. A line that is found only when it is
 * first said (one made while the scene runs, the first time) is told to Python with the next frame, and is exact from
 * then on and in the next run. The audio itself needs none of this: it is placed by the page the moment the command
 * arrives, on the scene's clock (Python's own clock in a live scene; the recorder's exact one when stepped).
 */
export function keep(scene, source) {
  const renderer = scene.renderer, r = scene.r
  const memo = (scene.sayHeard ??= new Map())    // text | voice | lang -> seconds, from the host's entries
  const key = (text, voice, lang) => JSON.stringify([text, voice || null, lang || 'en'])
  const host = () => scene.opt.voice ?? globalThis.pictureHost?.voice
  let closed = false, listener = 0

  // The sound: the commands of a loaded sample go to the scene's sound as Python's own would, timed on Python's clock.
  let ids = 0
  const at = () => { const t = scene.sound && scene.sound.soundTime && scene.sound.soundTime(); return typeof t === 'number' ? t : undefined }
  const sound = {
    soundTime: at,
    loadSample(file) {
      const id = 'say' + ++ids
      scene.sound.send({ synths: 1, cmds: [{ op: 'sample', id: id + 'w', name: file, url: file }, { op: 'synth', id, preset: 'sample', set: { sample: id + 'w' }, t: at() }] })
      return {
        // A speaker's line waits its turn: { after } seconds from now (on Python's clock when the sound has one).
        play: (note, o) => {
          const t = at()
          scene.sound.send({ synths: 1, cmds: [{ op: 'note', id, note: 60, len: null, vel: 1, t: o && o.after > 0 && t !== undefined ? t + o.after : t }] })
        },
        // What the line's sound is making now, for the mouth (the scene's sound reads it back by the synth's id).
        samples: () => scene.sound.synth(id).samples(),
      }
    },
  }
  // The scene's time: the recorder's when it steps the scene (the sound keeper's clock), else the page's.
  const clock = () => (scene.opt.sound && typeof scene.opt.sound.clock === 'function' ? scene.opt.sound.clock() : performance.now() / 1000)
  const talk = createSay({ host, sound: () => (scene.sound ? sound : null), recorded: !!scene.stepping, code: source, live: () => !closed, clock })

  // What Python is told at the start: the measured length of every line that is known beforehand.
  const lines = new Map()
  for (const l of literalsIn(source)) lines.set(key(l.text, l.voice, l.lang), { text: l.text, voice: l.voice, lang: l.lang || 'en' })
  for (const k of memo.keys()) { const [text, voice, lang] = JSON.parse(k); lines.set(k, { text, voice: voice || undefined, lang }) }
  const known = []
  const lookup = (l) => { try { return host()?.lookup?.({ ...l }) || null } catch (e) { return null } }
  for (const [k, l] of lines) {
    const entry = lookup(l)
    if (entry && entry.duration > 0) { memo.set(k, entry.duration); known.push([l.text, l.voice || null, l.lang, entry.duration]) } else memo.delete(k)
  }
  const transport = scene.transport
  if (transport && typeof transport.start === 'function') {
    const start = transport.start
    transport.start = function (src, info, stored) {
      transport.start = start
      return start.call(this, src, { ...info, say: known, voices: talk.voices() }, stored)
    }
  }

  // Python's commands to handle 16 are taken out of a frame as it arrives.
  const speakers = new Map()   // Python's speaker numbers -> the speakers made here
  const api = {
    speaker(id, voice, pitch, rate, lang, name, like, fallback) {
      speakers.set(id, talk.speaker({ voice: voice || undefined, pitch, rate, lang, name: name || undefined, like: like || undefined, fallback: fallback || undefined }))
    },
    say(text, voice, lang, source, line, speaker) {
      const d = talk.say(text, { voice: voice || undefined, lang: lang || 'en', source, line, speaker: speaker ? speakers.get(speaker) : undefined })
      const k = key(text, voice, lang)
      // Found now and not before: Python is told with the next frame.
      if (d !== estimate(text) && memo.get(k) !== d) {
        memo.set(k, d)
        if (listener && r.live) r.events.push({ k: 'cb', id: listener, e: { text, voice: voice || null, lang: lang || 'en', seconds: d } })
      }
    },
    listen(id) { listener = id },
  }
  const push = renderer.push
  renderer.push = (cmds, ...rest) => {
    if (cmds) {
      for (let i = 0; i < cmds.length; i++) {
        const c = cmds[i]
        if (c[3] !== 16 || c[0] !== 'call') continue
        if (c[4] === 'mouth') continue   // drawn by the renderer, in the order the frame has it
        try { api[c[4]](...c[5]) } catch (e) { console.error(e) }
        cmds[i] = ['free', 0, 0]
      }
    }
    return push.call(renderer, cmds, ...rest)
  }

  // Python is told how loud the voice is, with each frame (it cannot ask): when it has changed since the last was told.
  let told = ''
  const tellLevel = () => {
    if (closed || !listener || !r.live) return
    const shape = talk.voiceShape()
    const e = { level: shape.height, width: shape.width, viseme: shape.viseme, speaking: talk.speaking() }
    // Each speaker's own mouth, with the same four numbers.
    if (speakers.size) {
      e.speakers = {}
      for (const [id, sp] of speakers) { const h = sp.shape(); e.speakers[id] = { level: h.height, width: h.width, viseme: h.viseme, speaking: sp.speaking() } }
    }
    const now = JSON.stringify(e)
    if (now === told) return
    told = now
    r.events.push({ k: 'cb', id: listener, e })
  }
  // The device may load its voices late: Python is told the list again when it has.
  const stopVoices = talk.onVoices((list) => { if (!closed && listener && r.live) r.events.push({ k: 'cb', id: listener, e: { voices: list } }) })
  // Both the screen's frames and a recorder's ask the sound for what Python reads back just before the frame is asked for.
  const frame = scene.sound && scene.sound.frame
  if (typeof frame === 'function') scene.sound.frame = function (...a) { tellLevel(); return frame.apply(this, a) }

  // It goes with the run.
  const own = { stop: scene.stop, showError: scene.showError }
  const close = () => {
    if (closed) return
    closed = true
    stopVoices()
    talk.close()
    renderer.push = push
    scene.stop = own.stop
    scene.showError = own.showError
    delete scene.say
  }
  scene.stop = function (...a) { close(); return own.stop.apply(this, a) }
  scene.showError = function (...a) { close(); return own.showError.apply(this, a) }
  /** For a host and the tests: what the scene has asked for and could not have recorded. */
  scene.say = { asked: talk.asked, unresolved: talk.unresolved, plays: talk.plays }
  return scene.say
}
