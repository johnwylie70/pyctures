/**
 * codealong.js: the code-along scene for videos. Code typed on one side, syntax coloured, with line numbers, a cursor and
 * the lines that just changed lit; on the other side, what that code really draws, for each stage of the typing. It is a
 * part of its own beside pictures.js, fetched only for a scene that names one of CODEALONG_NAMES (pictures.js), and it
 * borrows the look (houseStyle) and the safe area from kinetic/kinetic.js (the host gives it as `kit`), so it sits in the same videos as the moving text.
 *
 *   codeAlong({
 *     stages: [
 *       { code: "function draw() {\n  background('navy')\n}" },
 *       { code: "function draw() {\n  background('navy')\n  circle(width / 2, height / 2, 80, 'gold')\n}", hold: 2 },
 *     ],
 *     start: 0, duration: 12,
 *   })
 *
 * IT IS A FUNCTION OF TIME like the kinetic kit: the scene's own clock (`kineticTime()`), or the `t` it is given. No wall
 * clock, no Math.random (the preview's random() and pick() are seeded). Stills at explicit times are exact.
 *
 * OPTIONS (all but stages are optional)
 *   stages        [{ code, language: "javascript" | "python", hold, at, typeAt, typeTime, preview }]. A string is a stage of its own. Stage 0 is typed
 *                 from an empty editor, every next stage types only what changed (the text that was already right stays), then
 *                 holds `hold` seconds (1.5). To sync the typing to a voice-over, a stage may say when it begins: `at` seconds into the
 *                 beat, or `typeAt` a share (0 to 1) of `duration`, and how long it takes: `typeTime` seconds
 *   language      the language of a stage that does not say (javascript)
 *   start         seconds into the scene when the beat begins (0)
 *   duration      the seconds the whole beat takes. The typing is made faster (or the holds shorter) to fit, and the holds
 *                 longer when there is time to spare. Left out, it is the natural time
 *   typingSpeed   characters a second (22), before it is fitted to `duration`
 *   layout        "auto" (code beside the preview in a wide frame, above it in a tall one), "side" or "stack"
 *   x, y, w, h    the box, in pixels (the safe area of the frame)
 *   style         a voice of houseStyle ("techy"), or an object that changes one: its accent lights the changed lines and the cursor
 *   run           true (the default): the preview runs each stage. false: only the code, in the whole box
 *   live          false (the default): the preview changes when a stage is fully typed. true: it runs the typed text each
 *                 time that parses, for a live-coding feel
 *   fontScale     1. The text is never smaller than houseStyle.minimum of the frame's height: a scale below that is raised to it
 *   callouts      [{ at, line, text, duration }]: a label with an arrow at a line of the code, `at` seconds into the beat
 *   demoVoice     false. A stage's say() never speaks in the preview (the voice-over owns the sound) and gives back the line's length; its mouth() is
 *                 drawn at a size of the preview's own. `demoVoice: true` makes that mouth talk from a made-up level for the stage's last say()
 *   previews      [image | canvas | (ctx, w, h, t) => void] a preview for each stage, for stages that are not JavaScript (or to
 *                 draw something else). Without one a Python stage says its output is pending
 *   start, t, hold as the kinetic effects have them: `t` wins over the scene's clock, `hold: false` takes the beat away at its end
 *
 * THE PREVIEW is the stage's own code run in a box of its own (`width` and `height` are the box's), clipped to it. The code
 * is a scene as pictures.js runs it, with setup(), update(dt) and draw(); update(dt) is called with a fixed 1/60 s from 0 to
 * the stage's time, so what it draws is the same every time. A stage that does not compile or throws shows its message in the
 * preview and in `warnings`.
 *
 * RETURNS { progress (0 to 1), stage, phase ("lead", "type", "hold" or "done"), typed, warnings }, or null before it starts.
 * `warnings` says what could not be shown as asked: a line longer than the budget (wrapped), more lines than fit (it scrolls),
 * a text that was made larger to reach the minimum, a Python stage with no preview, a typing speed too fast to follow.
 *
 *   codeAlongStageAt(stages, t, options)   which stage, and how many characters of it are typed, at t seconds into the beat
 *   codeAlongBegin(options) ... codeAlongEnd()   the same, but the scene draws the preview itself between the two (`previewError: "text"` shows a message in the pane instead)
 */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x))
/** A number from 0 up to 1 that is always the same for the same a and b (the same as kinetic.js's hash). */
function hash(a, b = 0) {
  let h = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263)) | 0
  h = Math.imul(h ^ (h >>> 13), 1274126177)
  h ^= h >>> 16
  return (h >>> 0) / 4294967296
}

// --- THE LOOK: the kit's palette (houseStyle, from kinetic.js: the host hands it over in `kit`, so this file stands alone), with the editor's own panels
let houseStyle, safeArea, seededRandom, PALETTE, LOOK
function adopt(kit) {
  if (!kit?.houseStyle) throw new Error('The code-along takes its look from the moving text: keep({ kit }) needs kinetic.js (houseStyle, safeArea, seededRandom)')
  ;({ houseStyle, safeArea, seededRandom } = kit)
  PALETTE = houseStyle.palette
  LOOK = {
    panel: '#111936', edge: '#223058', gutter: '#64748b', stage: '#0d1330',
    plain: '#e5e7eb', punct: '#a5b4cb',
    keyword: PALETTE.pink, string: PALETTE.green, number: PALETTE.yellow, comment: '#7a8aa6', fn: PALETTE.cyan, constant: '#8ab4ff',
  }
}
/** The characters a line is at most (wide frame, tall frame): the line-length budget of the video notes. */
const BUDGET = { side: 60, stack: 34 }
const LEAD = 0.4
const MAX_SPEED = 90

// --- THE TOKENIZER: JavaScript and Python, a few rules each. Keywords, strings, numbers, comments, function names.
const WORDS = (s) => new Set(s.split(' '))
const LANGUAGES = {
  javascript: {
    keywords: WORDS('const let var function return if else for while do break continue new class extends import export from default async await of in typeof instanceof switch case throw try catch finally delete void yield static get set'),
    constants: WORDS('true false null undefined NaN Infinity this super'),
    defines: WORDS('function class'),
    comment: '//', block: ['/*', '*/'], triple: false, template: true,
  },
  python: {
    keywords: WORDS('def return if elif else for while in not and or is import from as class pass break continue lambda with try except finally raise yield global nonlocal assert del async await'),
    constants: WORDS('True False None self cls'),
    defines: WORDS('def class'),
    comment: '#', block: null, triple: true, template: false,
  },
}
const ALIASES = { js: 'javascript', ts: 'javascript', typescript: 'javascript', javascript: 'javascript', py: 'python', python: 'python', python3: 'python' }
const languageOf = (name) => {
  const lang = ALIASES[String(name ?? 'javascript').toLowerCase()]
  if (!lang) throw new Error(`There is no tokenizer for "${name}": use "javascript" or "python"`)
  return lang
}
const isWordStart = (c) => /[A-Za-z_$]/.test(c)
const isWordChar = (c) => /[\w$]/.test(c)

/** The kind of each character of `code`: "plain", "punct", "keyword", "string", "number", "comment", "fn" or "constant". */
export function tokenKinds(code, language = 'javascript') {
  const L = LANGUAGES[languageOf(language)]
  const n = code.length
  const kinds = new Array(n).fill('plain')
  const paint = (a, b, kind) => { for (let i = a; i < b; i++) kinds[i] = kind }
  let i = 0, lastWord = ''
  while (i < n) {
    const c = code[i]
    if (c === '\n' || c === ' ' || c === '\t') { i++; continue }
    // comments
    if (code.startsWith(L.comment, i)) {
      let j = code.indexOf('\n', i); if (j < 0) j = n
      paint(i, j, 'comment'); i = j; continue
    }
    if (L.block && code.startsWith(L.block[0], i)) {
      let j = code.indexOf(L.block[1], i + 2); j = j < 0 ? n : j + L.block[1].length
      paint(i, j, 'comment'); i = j; continue
    }
    // strings (a prefix such as f, r or b in Python is part of the string)
    let q = i
    if (L.triple && /[rRbBfFuU]/.test(c) && /["']/.test(code[i + 1] ?? '') && (i === 0 || !isWordChar(code[i - 1]))) q = i + 1
    else if (L.triple && /[rRbBfFuU]/.test(c) && /[rRbBfF]/.test(code[i + 1] ?? '') && /["']/.test(code[i + 2] ?? '') && (i === 0 || !isWordChar(code[i - 1]))) q = i + 2
    const quote = code[q]
    if (quote === '"' || quote === "'" || (L.template && quote === '`')) {
      let j
      const triple = L.triple && code.startsWith(quote.repeat(3), q)
      if (triple) {
        j = code.indexOf(quote.repeat(3), q + 3); j = j < 0 ? n : j + 3
      } else {
        j = q + 1
        while (j < n && code[j] !== quote && (quote === '`' || code[j] !== '\n')) j += code[j] === '\\' ? 2 : 1
        j = Math.min(n, j < n && code[j] === quote ? j + 1 : j)
      }
      paint(i, j, 'string'); i = j; lastWord = ''; continue
    }
    // numbers
    if (/[0-9]/.test(c) || (c === '.' && /[0-9]/.test(code[i + 1] ?? '') && !isWordChar(code[i - 1] ?? ' '))) {
      const m = /^(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|(?:\d[\d_]*)?\.?\d[\d_]*(?:[eE][+-]?\d+)?)/.exec(code.slice(i, i + 40))
      const j = i + Math.max(1, m ? m[0].length : 1)
      paint(i, j, 'number'); i = j; lastWord = ''; continue
    }
    // words
    if (isWordStart(c)) {
      let j = i + 1
      while (j < n && isWordChar(code[j])) j++
      const word = code.slice(i, j)
      let k = j
      while (k < n && (code[k] === ' ' || code[k] === '\t')) k++
      if (L.keywords.has(word)) paint(i, j, 'keyword')
      else if (L.constants.has(word)) paint(i, j, 'constant')
      else if (code[k] === '(' || L.defines.has(lastWord)) paint(i, j, 'fn')
      lastWord = word; i = j; continue
    }
    kinds[i] = 'punct'; lastWord = ''; i++
  }
  return kinds
}
/** The tokens of each line: [[{ text, kind }]]. */
export function tokenize(code, language = 'javascript') {
  const kinds = tokenKinds(code, language)
  const lines = [[]]
  let at = 0
  for (const line of code.split('\n')) {
    const row = lines[lines.length - 1]
    for (let i = 0; i < line.length; i++) {
      const last = row[row.length - 1]
      if (last && last.kind === kinds[at + i]) last.text += line[i]
      else row.push({ text: line[i], kind: kinds[at + i] })
    }
    at += line.length + 1
    lines.push([])
  }
  lines.pop()
  return lines
}

// --- THE TYPING: which stage, how many characters, at what time. Pure.
function normalise(stages, o = {}) {
  if (!Array.isArray(stages) || !stages.length) throw new Error('codeAlong needs stages: a list of { code } (a string is a stage of code)')
  return stages.map((s, i) => {
    const stage = typeof s === 'string' ? { code: s } : s
    if (typeof stage?.code !== 'string') throw new Error(`codeAlong: stage ${i} has no code (a stage is { code: "…" } or a string)`)
    return { ...stage, code: stage.code.replace(/\r\n?/g, '\n').replace(/\t/g, '  ').replace(/\n+$/, ''), language: languageOf(stage.language ?? o.language) }
  })
}
/**
 * What changed from `before` to `after`, as the editing that does it: the lines both keep stay as they are, and each run of lines
 * that differ is a hunk, typed from where its old and new text differ (the start and the end they share are not retyped).
 * A hunk is { old, head, typed, tail } (the lines it replaces, joined; the text kept in front; the text typed; the text kept after).
 */
function diff(before, after) {
  const a = before === '' ? [] : before.split('\n'), b = after === '' ? [] : after.split('\n')
  const lcs = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0))
  for (let i = a.length - 1; i >= 0; i--) for (let j = b.length - 1; j >= 0; j--) lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
  const parts = []
  let i = 0, j = 0, drop = [], add = []
  const flush = () => {
    if (!drop.length && !add.length) return
    const old = drop.join('\n'), now = add.join('\n')
    let h = 0
    const limit = Math.min(old.length, now.length)
    while (h < limit && old[h] === now[h]) h++
    let t = 0
    while (t < limit - h && old[old.length - 1 - t] === now[now.length - 1 - t]) t++
    // Whole lines are added or removed (no text kept on either side): there is no head or tail to keep.
    const lines = !drop.length || !add.length
    const flags = { hunk: true, old, hadOld: drop.length > 0, hasNew: add.length > 0 }
    parts.push(lines ? { ...flags, head: '', typed: now, tail: '' } : { ...flags, head: now.slice(0, h), typed: now.slice(h, now.length - t), tail: now.slice(now.length - t) })
    drop = []; add = []
  }
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) {
      flush()
      const last = parts[parts.length - 1]
      if (last && !last.hunk) last.lines.push(a[i]); else parts.push({ hunk: false, lines: [a[i]] })
      i++; j++
    } else if (j < b.length && (i === a.length || lcs[i][j + 1] >= lcs[i + 1][j])) add.push(b[j++])
    else drop.push(a[i++])
  }
  flush()
  return parts
}
/** The text and cursor of an edit when `n` of its typed characters are in, and the stretches of the text that were typed. */
function compose(parts, n) {
  const pieces = []
  const spans = []
  let cursor = null, start = 0, offset = 0
  const put = (text) => { pieces.push(text); offset += text.length + 1 }
  for (const part of parts) {
    if (!part.hunk) { put(part.lines.join('\n')); continue }
    const len = part.typed.length, local = n - start
    // The old text stays until the cursor gets to it (the first character typed in a hunk, or at once for one with nothing to type).
    const reached = len ? local > 0 : local >= 0
    const typed = Math.max(0, Math.min(len, local))
    const text = reached ? part.head + part.typed.slice(0, typed) + part.tail : part.old
    if (cursor === null) cursor = offset + (part.hadOld ? part.head.length : 0)
    if (reached) {
      if (typed > 0) spans.push([offset + part.head.length, offset + part.head.length + typed])
      cursor = offset + part.head.length + typed
    }
    if (reached ? part.hasNew : part.hadOld) put(text)
    start += len
  }
  return { text: pieces.join('\n'), cursor: cursor ?? 0, spans }
}
/** How long each typed character takes, relative to the others: uneven, deterministic, a pause at the end of a line. */
function weights(text, stage, seed) {
  const w = new Array(text.length)
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    w[i] = ch === '\n' ? 2.2 : ch === ' ' ? 0.6 : 0.7 + 0.6 * hash(i * 31 + stage, seed)
  }
  return w
}

/**
 * The timeline of a beat: for each stage when its typing starts and ends and when its hold ends, in seconds from the beat's start.
 * `duration` fits it (holds stretch to fill spare time; short of time, the holds shrink first and then the typing speeds up).
 */
export function plan(stagesIn, o = {}) {
  const stages = normalise(stagesIn, o)
  const speed = Math.max(1, o.typingSpeed ?? 22)
  const seed = o.seed ?? 1
  let before = ''
  const items = stages.map((s, i) => {
    const parts = diff(before, s.code)
    before = s.code
    const typed = parts.filter((p) => p.hunk).map((p) => p.typed).join('')
    const w = weights(typed, i, seed)
    return { parts, index: i, stage: s, typed, w, total: w.reduce((a, b) => a + b, 0), hold: Math.max(0, s.hold ?? 1.5) }
  })
  const typing = items.reduce((a, it) => a + it.total, 0)
  const holds = items.reduce((a, it) => a + it.hold, 0)
  const natural = LEAD + typing / speed + holds
  let rate = speed, holdOf = (it) => it.hold, lead = LEAD
  const want = o.duration
  if (want != null && want > 0) {
    if (natural <= want) {
      const extra = (want - natural) / items.length
      holdOf = (it) => it.hold + extra
    } else {
      const floor = (it) => Math.min(it.hold, Math.max(0.3, it.hold * 0.35))
      const holdMin = items.reduce((a, it) => a + floor(it), 0)
      if (LEAD + typing / speed + holdMin <= want) {
        const f = (natural - want) / Math.max(1e-9, holds - holdMin)
        holdOf = (it) => it.hold - (it.hold - floor(it)) * f
      } else {
        holdOf = floor
        const room = want - LEAD - holdMin
        if (room >= want * 0.2) rate = typing / room
        else { const k = want / (LEAD + typing / speed + holdMin); rate = speed / k; holdOf = (it) => floor(it) * k; lead = LEAD * k }
      }
    }
  }
  const warnings = []
  if (rate > MAX_SPEED) warnings.push(`the code is typed at ${Math.round(rate)} characters a second to fit ${want} seconds, which is too fast to follow: give it more time or shorten the code`)
  // A stage may say when its typing begins: `at` in seconds into the beat, or `typeAt` as a share (0 to 1) of `duration`. Those stages start then,
  // the others follow the stage before; a stage that has a next one at a set time is typed to be done 0.3 s before it (`typeTime` is how many seconds
  // its typing takes, else the typing speed's) and is held until then.
  const startOf = (it) => (it.stage.at != null ? Number(it.stage.at) : it.stage.typeAt != null && want > 0 ? Number(it.stage.typeAt) * want : null)
  let t = lead
  let segments
  if (items.some((it) => startOf(it) != null)) {
    warnings.length = 0
    segments = []
    let free = lead
    items.forEach((it, i) => {
      const typeStart = Math.max(0, startOf(it) ?? free)
      const next = items[i + 1] ? startOf(items[i + 1]) : null
      let take = it.stage.typeTime != null ? Number(it.stage.typeTime) : it.total / speed
      if (next != null && typeStart + take > next - 0.3) take = Math.max(0.05, next - 0.3 - typeStart)
      const typeEnd = typeStart + take
      const holdEnd = next != null ? Math.max(typeEnd, next) : Math.max(typeEnd + it.hold, i === items.length - 1 && want > 0 ? want : 0)
      if (it.total / take > MAX_SPEED && it.total > 0) warnings.push(`stage ${i + 1} is typed at ${Math.round(it.total / take)} characters a second to fit the time before the next: give it more time or shorten the code`)
      segments.push({ ...it, typeStart, typeEnd, holdEnd })
      free = holdEnd
    })
    t = segments[segments.length - 1].holdEnd
    return { segments, lead: segments[0].typeStart, rate: speed, total: t, warnings, stages }
  }
  segments = items.map((it) => {
    const typeStart = t
    t += it.total / rate
    const typeEnd = t
    t += holdOf(it)
    return { ...it, typeStart, typeEnd, holdEnd: t }
  })
  return { segments, lead, rate, total: t, warnings, stages }
}

/** The lines (1 to n) of `text` that hold characters from a to b. */
function linesOf(text, a, b) {
  const out = []
  if (b <= a) return out
  let line = 1
  for (let i = 0; i < Math.min(b, text.length); i++) {
    if (i >= a) out.push(line)
    if (text[i] === '\n') line++
  }
  return [...new Set(out)]
}
/** The state at `t` seconds into a plan. */
function at(P, t) {
  const segs = P.segments
  let k = segs.findIndex((s) => t < s.holdEnd)
  const done = k < 0
  if (done) k = segs.length - 1
  const s = segs[k]
  const previous = k > 0 ? segs[k - 1] : null
  const before = previous ? previous.stage.code : ''
  let phase, typed
  if (done) { phase = 'done'; typed = s.typed.length }
  else if (t < s.typeStart) { phase = 'lead'; typed = 0 }
  else if (t < s.typeEnd) {
    phase = 'type'
    const target = ((t - s.typeStart) / Math.max(1e-9, s.typeEnd - s.typeStart)) * s.total
    typed = 0
    let sum = 0
    while (typed < s.w.length && sum + s.w[typed] <= target) sum += s.w[typed++]
  } else { phase = 'hold'; typed = s.typed.length }
  const made = compose(s.parts, typed)
  const text = made.text, cursor = made.cursor
  // The preview shows the last stage whose typing is over; its own seconds begin when that typing ended.
  const finished = phase === 'type' || phase === 'lead' ? k - 1 : k
  const preview = finished < 0 ? -1 : finished
  return {
    stage: k, phase, typed, inserted: s.typed.length, length: text.length, text, cursor, before,
    changed: k > 0 ? [...new Set(made.spans.flatMap(([a, b]) => linesOf(text, a, b)))] : [],
    preview, previewTime: preview < 0 ? 0 : t - segs[preview].typeEnd, stageTime: t - s.typeStart,
    typeEnd: s.typeEnd, holdEnd: s.holdEnd, holdLeft: s.holdEnd - t,
  }
}
/** Which stage is being typed at `t` seconds into the beat, and how many characters of it are typed. A pure helper. */
export function stageAt(stages, t, options = {}) {
  const P = plan(stages, options)
  return { ...at(P, t), total: P.total, rate: P.rate, warnings: P.warnings }
}

// --- THE PICTURE
function roundRect(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2)
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}
function voiceOf(style) {
  const voices = houseStyle.voices
  if (style && typeof style === 'object') return { ...voices[style.voice ?? 'techy'], ...style }
  const v = voices[style ?? 'techy']
  if (!v) throw new Error(`There is no style "${style}": use ${Object.keys(voices).map((n) => `"${n}"`).join(', ')}`)
  return v
}
/** The seeded versions of the two functions of chance that a scene is given. */
function chance(seed) {
  const next = seededRandom(seed)
  const random = (a, b) => {
    if (a === undefined) return next()
    if (b === undefined) { b = a; a = 0 }
    if (Number.isInteger(a) && Number.isInteger(b)) return a + Math.floor(next() * (b - a + 1))
    return a + next() * (b - a)
  }
  return { random, pick: (list) => list[Math.floor(next() * list.length)] }
}

/** Rows of text on screen (exported as `wrap`, for tests and for a host that lays code out itself): each source line cut into pieces of at most `cols` characters (a cut keeps the line's indent, and two more). */
function rowsOf(text, cols) {
  const rows = []
  let at = 0
  text.split('\n').forEach((line, n) => {
    const indent = Math.min(Math.floor(cols / 2), line.length - line.trimStart().length + 2)
    let from = 0
    do {
      const room = from === 0 ? cols : cols - indent
      let to = from + room >= line.length ? line.length : from + room
      // A line that has to be cut is cut where it reads best: after the last comma, or after the last opening bracket (so the argument
      // starts the next row), or after the last space that fits; with something worth a row before the cut and not a lone bracket after it.
      if (to < line.length) {
        let best = -1
        for (let i = from + 1; i <= to; i++) {
          const c = line[i - 1]
          const cut = c === ',' ? (line[i] === ' ' ? i + 1 : i) : c === '(' || c === '[' || c === '{' ? i : c === ' ' && line.slice(from, i).trim() ? i : -1
          if (cut > best && cut <= to + 1 && cut > from + room / 4 && line.length - cut > 1) best = cut
        }
        if (best > from) to = Math.min(best, line.length)
      }
      rows.push({ line: n, first: from === 0, from, to, at: at + from, indent: from === 0 ? 0 : indent })
      from = to
    } while (from < line.length)
    at += line.length + 1
  })
  return rows
}

/**
 * The box, the two panes and the text size for these options, in a frame W by H. Fixed for the whole beat (the stages together decide it) and
 * a pure function of the numbers, so a Python half can work it out too: a letter of the code is 0.6 of its size across.
 */
export function layout(o, P, W, H) {
  const warnings = []
  const safe = safeArea(W, H, o.safe)
  const box = { x: o.x ?? safe.left, y: o.y ?? safe.top, w: o.w ?? safe.width, h: o.h ?? safe.height }
  const run = o.run !== false
  let mode = o.layout ?? 'auto'
  if (mode === 'auto') mode = box.h / box.w >= 1 ? 'stack' : 'side'
  if (mode !== 'side' && mode !== 'stack') throw new Error(`There is no layout "${o.layout}": use "auto", "side" or "stack"`)
  const minPx = H * houseStyle.minimum
  const wanted = (mode === 'stack' ? minPx : minPx * 1.15) * (o.fontScale ?? 1)
  const px = Math.max(minPx, wanted)
  if (wanted < minPx - 0.01) warnings.push(`the text is raised to ${Math.round(minPx)} px, the least that is readable (3 percent of the frame's height): fontScale ${o.fontScale} was too small`)
  const font = `600 ${px}px ${houseStyle.fonts.mono}`
  const cw = px * 0.6
  const lh = px * (mode === 'stack' ? 1.28 : 1.32)
  const pad = px * (mode === 'stack' ? 0.4 : 0.45)
  const gap = px * (mode === 'stack' ? 0.5 : 0.7)
  const lines = Math.max(...P.stages.map((s) => s.code.split('\n').length))
  const gutter = cw * (String(lines).length + 1.1)
  const longest = Math.max(...P.stages.flatMap((s) => s.code.split('\n').map((l) => l.length)))
  // Lines longer than the budget are for the author to shorten; they are wrapped here.
  const budget = BUDGET[mode]
  P.stages.forEach((s, i) => s.code.split('\n').forEach((l, n) => {
    if (l.length > budget) warnings.push(`line ${n + 1} of stage ${i + 1} is ${l.length} characters, over the budget of ${budget} for this shape: it is wrapped, shorten it`)
  }))
  let code, preview
  if (!run) {
    code = { ...box }
    preview = null
  } else if (mode === 'side') {
    const want = gutter + 2 * pad + cw * (Math.min(longest, budget) + 2)
    const w = clamp(want, box.w * 0.42, box.w * 0.62)
    code = { x: box.x, y: box.y, w, h: box.h }
    preview = { x: box.x + w + gap, y: box.y, w: box.w - w - gap, h: box.h }
  } else {
    const cols0 = Math.max(8, Math.floor((box.w - gutter - 2 * pad) / cw))
    const rows = Math.max(...P.stages.map((s) => rowsOf(s.code, cols0).length))
    const h = clamp(rows * lh + 2 * pad, box.h * 0.2, box.h * 0.66)
    code = { x: box.x, y: box.y, w: box.w, h }
    preview = { x: box.x, y: box.y + h + gap, w: box.w, h: box.h - h - gap }
  }
  // Inside the preview's pane, the stage's own box is set in from the edges, so what it draws near its edge (a ball at x = 40) is not cut off.
  const inset = preview ? o.previewPad ?? 0.04 * Math.min(preview.w, preview.h) : 0
  const inner = preview ? { w: preview.w - 2 * inset, h: preview.h - 2 * inset } : null
  const cols = Math.max(8, Math.floor((code.w - gutter - 2 * pad) / cw))
  const visible = Math.max(1, Math.floor((code.h - 2 * pad) / lh))
  const wrapped = new Set()
  P.stages.forEach((s, i) => {
    s.code.split('\n').forEach((l, n) => { if (l.length > cols && l.length <= budget) wrapped.add(`line ${n + 1} of stage ${i + 1}`) })
    const rows = rowsOf(s.code, cols).length
    if (rows > visible) warnings.push(`stage ${i + 1} is ${rows} rows and ${visible} fit: the code scrolls to keep the cursor in view`)
  })
  if (wrapped.size) warnings.push(`${[...wrapped].join(', ')} does not fit ${cols} columns at ${Math.round(px)} px: it is wrapped`)
  return { mode, box, code, preview, inset, inner, px, font, cw, lh, pad, gap, gutter, cols, visible, warnings, minPx }
}

/**
 * The code-along for one scene. `host`: { ctx, kit, voice (say.js, for a preview's mouth), size() -> [width, height], time() -> the scene's seconds, stage(code, w, h, seed, chance, extras) ->
 * { setup, update, draw } (compiles a stage as a scene; throws what is wrong with it) }.
 */
export function keep(host) {
  if (!host.ctx) throw new Error('The code-along is drawn on the 2D canvas: a 3D scene has none')
  adopt(host.kit)
  const { ctx } = host
  const plans = new Map()
  const runners = new Map()
  let begun = null

  const planOf = (o) => {
    const key = JSON.stringify([o.stages, o.language, o.duration, o.typingSpeed, o.seed])
    let P = plans.get(key)
    if (!P) { P = plan(o.stages, o); if (plans.size > 20) plans.clear(); plans.set(key, P) }
    return P
  }

  /**
   * What a stage is given in place of the scene's say() and mouth(): the preview is silent (the beat's own voice-over owns the sound, so a say() in
   * a stage never speaks), say() gives back how long the line would take, and mouth() is drawn at a size of the preview's own (a sixth of its smaller
   * side). `demoVoice: true` makes the mouth talk from a made-up level for the last say() of the stage (the same as the draft voice's, from the text),
   * `demoVoice: { delay: 0.3 }` after that many seconds; without it the mouth stays shut.
   */
  function voiceFor(r, o) {
    const V = host.voice
    if (!V?.drawMouth) return undefined
    const demo = o.demoVoice ?? o.fakeVoice
    const said = { text: null, at: 0, profile: null, seconds: 0 }
    const now = () => {
      if (!demo || said.text == null) return { open: 0, width: 0.5, on: false }
      const pos = r.time - said.at - (typeof demo === 'object' ? demo.delay ?? 0 : 0)
      return pos >= 0 && pos < said.seconds ? { ...V.mouthAt(said.profile, pos), on: true } : { open: 0, width: 0.5, on: false }
    }
    const say = (text) => {
      text = String(text ?? '')
      if (text !== said.text) { said.text = text; said.at = r.time; said.seconds = V.estimate(text); said.profile = V.mouthProfile(text, said.seconds) }
      return said.seconds
    }
    const mouth = (x, y, m = {}) => {
      const k = now()
      V.drawMouth(ctx, x, y, { size: m.size ?? 0.16 * Math.min(r.w, r.h), style: m.style, color: m.color, level: k.open, width: k.width })
      return k.open
    }
    const level = () => now().open
    return { say, mouth, speaking: () => now().on, voiceLevel: level, voice_level: level }
  }
  function makeStage(r, seed, o) { return host.stage(r.code, r.w, r.h, seed, chance(seed), voiceFor(r, o ?? {})) }

  /** The preview of a stage: its code run in a box of its own, kept between frames and stepped to the time wanted. */
  function runnerFor(key, code, w, h, seed, t, o) {
    let r = runners.get(key)
    if (r && (r.code !== code || r.w !== w || r.h !== h || t < r.time - 1e-9)) r = null
    if (!r) {
      r = { code, w, h, time: 0, hooks: null, error: null, every: false }
      if (runners.size > 12) runners.clear()
      runners.set(key, r)
      try {
        if (!host.stage) throw new Error('there is no scene to run it in')
        r.hooks = makeStage(r, seed, o)
      } catch (e) { r.error = String(e?.message ?? e) }
    }
    return r
  }
  function runStage(r, t, seed, problems) {
    if (r.error) return
    try {
      const h = r.hooks
      if (!r.began) {
        r.began = true
        r.every = !h.draw && !h.update
        h.setup?.()
      }
      if (h.update) {
        let steps = 0
        while (r.time + 1 / 60 <= t + 1e-9 && steps++ < 4000) { h.update(1 / 60); r.time += 1 / 60 }
      } else r.time = t
      h.draw?.()
    } catch (e) { r.error = String(e?.message ?? e) }
  }

  function wrapText(text, maxWidth, font) {
    ctx.font = font
    const out = []
    for (const para of String(text).split('\n')) {
      let line = ''
      for (const word of para.split(' ')) {
        const next = line ? `${line} ${word}` : word
        if (line && ctx.measureText(next).width > maxWidth) { out.push(line); line = word } else line = next
      }
      out.push(line)
    }
    return out
  }

  function paintCode(o, L, S, v, local) {
    const { code, px, cw, lh, pad, gutter, cols, visible } = L
    ctx.save()
    ctx.fillStyle = LOOK.panel
    roundRect(ctx, code.x, code.y, code.w, code.h, px * 0.4)
    ctx.fill()
    ctx.clip()
    ctx.strokeStyle = LOOK.edge
    ctx.lineWidth = 4
    ctx.stroke()
    ctx.font = L.font
    ctx.textBaseline = 'middle'
    ctx.textAlign = 'left'
    const rows = rowsOf(S.text, cols)
    const kinds = tokenKinds(S.text, S.language)
    // The row the cursor is on, and the first row shown (the code scrolls to keep the cursor in view, two rows from the bottom).
    let cursorRow = rows.length - 1
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i]
      const last = i + 1 >= rows.length || rows[i + 1].line !== r.line
      if (S.cursor >= r.at && (S.cursor < r.at + (r.to - r.from) || (last && S.cursor <= r.at + (r.to - r.from)))) { cursorRow = i; break }
    }
    const top = Math.max(0, Math.min(rows.length - visible, cursorRow - visible + 2))
    const x0 = code.x + pad + gutter, y0 = code.y + pad
    const changed = new Set(S.changed)
    const shown = Math.min(rows.length - top, visible)
    for (let i = 0; i < shown; i++) {
      const r = rows[top + i], y = y0 + i * lh + lh / 2
      if (changed.has(r.line + 1)) {
        ctx.fillStyle = v.accent
        ctx.globalAlpha = 0.16
        ctx.fillRect(code.x, y - lh / 2, code.w, lh)
        ctx.globalAlpha = 1
        if (r.first) ctx.fillRect(code.x, y - lh / 2, Math.max(3, px * 0.12), lh)
      }
      if (r.first) {
        ctx.fillStyle = LOOK.gutter
        ctx.textAlign = 'right'
        ctx.fillText(String(r.line + 1), code.x + pad + gutter - cw * 0.9, y)
        ctx.textAlign = 'left'
      }
      let k = r.at, col = r.indent
      while (k < r.at + (r.to - r.from)) {
        const kind = kinds[k]
        let j = k
        while (j < r.at + (r.to - r.from) && kinds[j] === kind) j++
        ctx.fillStyle = LOOK[kind] ?? LOOK.plain
        const chunk = S.text.slice(k, j)
        if (chunk.trim()) ctx.fillText(chunk, x0 + col * cw, y)
        col += j - k
        k = j
      }
    }
    // The cursor: solid while typing, blinking once it stops.
    const row = cursorRow - top
    if (row >= 0 && row < visible) {
      const r = rows[cursorRow]
      const on = S.phase === 'type' || Math.floor(local * 2.2) % 2 === 0
      if (on) {
        ctx.fillStyle = v.accent
        ctx.fillRect(x0 + (r.indent + S.cursor - r.at) * cw, y0 + row * lh + lh * 0.12, Math.max(3, px * 0.1), lh * 0.76)
      }
    }
    ctx.restore()
    return { rows, top, y0, x0 }
  }

  function paintCallouts(o, L, v, local, grid, S) {
    if (!o.callouts?.length) return
    const { px, cw, lh, code } = L
    const size = Math.max(L.minPx, px * 0.8)
    const font = `700 ${size}px ${houseStyle.fonts.mono}`
    const endOf = (row) => (row ? grid.x0 + (row.indent + S.text.slice(row.at, row.at + row.to - row.from).trimEnd().length) * cw : grid.x0)
    for (const c of o.callouts) {
      const length = c.duration ?? 2.5
      const u = local - (c.at ?? 0)
      if (u < 0 || u > length) continue
      const a = clamp(u / 0.25) * clamp((length - u) / 0.25)
      const i = grid.rows.findIndex((r, n) => r.line + 1 === c.line && grid.rows[n + 1]?.line !== r.line)
      if (i < grid.top || i >= grid.top + L.visible) continue
      const y = grid.y0 + (i - grid.top) * lh + lh / 2
      ctx.save()
      ctx.globalAlpha = a
      ctx.font = font
      const lines = wrapText(c.text ?? '', code.w * 0.62, font)
      const tw = Math.max(...lines.map((l) => ctx.measureText(l).width))
      const bw = tw + size, bh = lines.length * size * 1.2 + size * 0.1
      const span = Math.ceil(bh / lh - 0.05)
      const right = code.x + code.w - L.pad * 0.5
      const bx = right - bw
      // The label goes where it covers no code: at the end of the line, or on the nearest rows where the text stops short of it.
      let cy = null
      for (const d of [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6, 7, -7, 8, -8]) {
        const first = i + d
        if (first < grid.top || first + span > grid.top + L.visible) continue
        let clear = true
        for (let k = 0; k < span; k++) if (endOf(grid.rows[first + k]) + cw * 2 > bx) clear = false
        if (clear) { cy = grid.y0 + (first - grid.top) * lh + (span * lh) / 2; break }
      }
      // No clear place: it sits on the lower edge of the pane.
      if (cy === null) cy = code.y + code.h - bh / 2 - 3
      const by = cy - bh / 2
      ctx.fillStyle = v.accent
      roundRect(ctx, bx, by, bw, bh, size * 0.35)
      ctx.fill()
      ctx.fillStyle = PALETTE.ink
      ctx.textBaseline = 'middle'
      lines.forEach((l, n) => ctx.fillText(l, bx + size * 0.5, by + size * 0.15 + (n + 0.5) * size * 1.2))
      // The arrow: from the label to the end of the line.
      ctx.strokeStyle = ctx.fillStyle = v.accent
      ctx.lineWidth = Math.max(3, px * 0.1)
      ctx.lineCap = 'round'
      const level = Math.abs(cy - y) < lh * 0.6
      const ex = level ? Math.min(endOf(grid.rows[i]) + cw * 0.6, bx - cw * 0.3) : endOf(grid.rows[i]) + cw * 0.6, ey = y
      const sx = level ? bx : Math.max(bx, Math.min(bx + bw, ex)), sy = level ? cy : cy > y ? by : by + bh
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke()
      const ang = Math.atan2(ey - sy, ex - sx), head = size * 0.5
      ctx.beginPath()
      ctx.moveTo(ex, ey)
      ctx.lineTo(ex - head * Math.cos(ang - 0.45), ey - head * Math.sin(ang - 0.45))
      ctx.lineTo(ex - head * Math.cos(ang + 0.45), ey - head * Math.sin(ang + 0.45))
      ctx.closePath(); ctx.fill()
      ctx.restore()
    }
  }

  /** The frame around the preview, and the pane's own backdrop; leaves the context clipped to the pane and moved to its corner. */
  function openPreview(L, v, flash) {
    const p = L.preview
    ctx.save()
    roundRect(ctx, p.x, p.y, p.w, p.h, L.px * 0.4)
    ctx.clip()
    ctx.fillStyle = LOOK.stage
    ctx.fillRect(p.x, p.y, p.w, p.h)
    ctx.translate(p.x + L.inset, p.y + L.inset)
    ctx.beginPath(); ctx.rect(-L.inset, -L.inset, p.w, p.h); ctx.clip()
    return () => {
      ctx.restore()
      ctx.save()
      ctx.strokeStyle = flash > 0 ? v.accent : LOOK.edge
      const edge = 2 + 5 * flash
      ctx.lineWidth = edge
      // The line is drawn inside the pane's edge, so that none of it is outside the box.
      roundRect(ctx, p.x + edge / 2, p.y + edge / 2, p.w - edge, p.h - edge, L.px * 0.4)
      ctx.stroke()
      ctx.restore()
    }
  }
  function message(L, text, colour) {
    const p = L.inner
    const size = Math.max(L.minPx, L.px * 0.8)
    const font = `600 ${size}px ${houseStyle.fonts.mono}`
    ctx.save()
    ctx.font = font
    ctx.fillStyle = colour
    ctx.textBaseline = 'middle'
    ctx.textAlign = 'center'
    const lines = wrapText(text, p.w, font)
    const h = lines.length * size * 1.3
    lines.forEach((l, i) => ctx.fillText(l, p.w / 2, p.h / 2 - h / 2 + (i + 0.5) * size * 1.3))
    ctx.restore()
  }

  function codeAlong(o = {}, mode = 'whole') {
    const [W, H] = host.size()
    const P = planOf(o)
    const now = o.t ?? host.time()
    const local = now - (o.start ?? 0)
    if (local < 0) return null
    if (o.hold === false && local > P.total) return null
    const v = voiceOf(o.style)
    const L = layout(o, P, W, H)
    const S = at(P, local)
    S.language = P.stages[S.stage].language
    const warnings = [...P.warnings, ...L.warnings]

    const grid = paintCode(o, L, S, v, local)
    paintCallouts(o, L, v, local, grid, S)

    let close = null
    if (L.preview) {
      // 0.5 s of flash on the frame as a stage is swapped in.
      const flash = S.preview >= 0 ? clamp(1 - S.previewTime / 0.5) : 0
      close = openPreview(L, v, flash)
      if (mode === 'whole') {
        // Draws a stage into the open pane; gives back what is wrong with it, if anything.
        const drawStage = (index, code, when) => {
          const stage = P.stages[index]
          const given = o.previews?.[index] ?? stage.preview
          const p = L.inner
          if (given && (typeof given === 'function' || given.width || given.naturalWidth)) {
            if (typeof given === 'function') given(ctx, p.w, p.h, Math.max(0, when))
            else {
              const gw = given.naturalWidth || given.width, gh = given.naturalHeight || given.height, k = Math.min(p.w / gw, p.h / gh)
              ctx.drawImage(given, (p.w - gw * k) / 2, (p.h - gh * k) / 2, gw * k, gh * k)
            }
            return null
          }
          if (stage.language === 'python') {
            message(L, 'Python output pending', LOOK.gutter)
            return `stage ${index + 1} is Python and has no preview: pass previews: [...] or run it in Pyctures`
          }
          const seed = (o.seed ?? 1) * 1000 + index
          const r = runnerFor(`${index}${code === stage.code ? '' : 'l'}`, code, p.w, p.h, seed, Math.max(0, when), o)
          // A stage with nothing but top-level code draws it all again each frame.
          if (r.every && r.began && !r.error) {
            r.began = false
            try { r.hooks = makeStage(r, seed, o) } catch (e) { r.error = String(e?.message ?? e) }
          }
          runStage(r, Math.max(0, when))
          return r.error ? `stage ${index + 1} would not run: ${r.error}` : null
        }
        try {
          let problem = null
          if (S.preview >= 0 || (o.live && S.phase === 'type')) {
            if (o.live && S.phase === 'type') {
              const seg = P.segments[S.stage]
              problem = drawStage(S.stage, S.text, S.stageTime - (seg.typeEnd - seg.typeStart))
              // Not yet a program: the last whole stage stays on show.
              if (problem && S.preview >= 0) { ctx.fillStyle = LOOK.stage; ctx.fillRect(-L.inset, -L.inset, L.preview.w, L.preview.h); problem = drawStage(S.preview, P.stages[S.preview].code, S.previewTime); if (problem) warnings.push(problem) } else if (problem) problem = null
            } else {
              problem = drawStage(S.preview, P.stages[S.preview].code, S.previewTime)
              if (problem && P.stages[S.preview].language !== 'python') message(L, runners.get(`${S.preview}`)?.error ?? problem, '#fca5a5')
              if (problem) warnings.push(problem)
            }
          }
        } catch (e) { warnings.push(`the preview failed: ${e?.message ?? e}`) }
        close()
        close = null
      }
    }
    if (mode === 'begin') {
      if (close && o.previewError) message(L, String(o.previewError), '#fca5a5')
      begun = { close }
    }
    return {
      progress: clamp(local / P.total), stage: S.stage, phase: S.phase, typed: S.typed, previewStage: S.preview, previewTime: S.previewTime,
      warnings, box: L.box, code: L.code, preview: L.preview, inner: L.inner, size: L.px, layout: L.mode,
    }
  }

  const names = {
    codeAlong: (o) => codeAlong(o ?? {}),
    /** Draws the code, opens the preview (clipped, moved to its corner, `width` and `height` of the pane are `preview.w`, `.h`) and returns; the scene draws, then calls codeAlongEnd(). */
    codeAlongBegin: (o) => codeAlong(o ?? {}, 'begin'),
    codeAlongEnd: () => { if (begun) { begun.close?.(); begun = null } },
    codeAlongStageAt: (stages, t, o) => { const r = stageAt(stages, t, o ?? {}); delete r.before; return r },
  }
  return {
    names,
    close() { runners.clear(); plans.clear() },
  }
}
export { adopt as useKit, rowsOf as wrap }
export const version = '0.1.0'
