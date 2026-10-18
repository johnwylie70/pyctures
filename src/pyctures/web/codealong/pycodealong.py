"""pycodealong: the code-along scene for videos, in Pyctures. Code typed on one side, syntax coloured, with line numbers, a cursor
and the changed lines lit; on the other, what that code really draws, for each stage of the typing. The same scene as pictures.js's
codeAlong().

    code_along(stages=[
        {"code": "def draw():\\n    background('navy')"},
        {"code": "def draw():\\n    background('navy')\\n    circle(width / 2, height / 2, 80, 'gold')"},
    ], duration=12)

A FILE DOES NOT IMPORT THIS. A file that names code_along or code_along_stage_at is given them (pages.USES_CODEALONG, pyctures.js
LIBRARIES and `pyctures build` ask the same of the same text), and with them the kinetic text, whose house style it takes its
look from; no other file loads either.

THE PAGE DRAWS THE CODE (codealong.js beside this file, the very file that is pictures.js's codealong/codealong.js, brought here by
scripts/sync_libraries.py; the fixed handle H_CODEALONG): the panels, the coloured text, the cursor, the lit lines, the callouts.
Python writes ONE command for the call, with the time it is at.

THE PREVIEW is the stage's code run for real, and where depends on its language:
  * a PYTHON stage (language "python", the default here) is run HERE, by Python, in a namespace of its own (the scene's names, its own
    `width` and `height`, which are the preview's), with its setup(), update(dt) (called with a fixed 1/60 s from 0 to the stage's time)
    and draw(). What it draws is sent between two page commands that clip and move the drawing to the preview's pane;
  * a JAVASCRIPT stage (language "javascript") is run by the page, which has the plain drawing functions (background, circle, rect,
    ellipse, triangle, polygon, star, line, text, picture, random, pick, degrees) and not the rest of a scene: no sound, no controls.
A stage that raises shows its message in the pane (and is in `warnings`). Randomness in a stage is seeded, from the stage and the step.

IT IS A FUNCTION OF TIME like the kinetic kit: `t=` if the call has it, else kinetic_time().

THE TYPING IS WORKED OUT TWICE, here and in codealong.js (plan, _layout and which stage is on show), by the same steps, so that Python knows which
stage to run and how big its pane is. tests/test_codealong.py compares the two with node.

NOT THE SAME AS JAVASCRIPT: code_along() gives back a dict of what Python knows (progress, stage, phase, typed, warnings, preview, box)
and not what the page worked out; the page's own warnings for a stage that raised in JavaScript are not seen here.
Python names are snake_case: typing_speed, font_scale, and in a stage hold=.
"""
import contextlib
import math
import random as _random
import re
import sys


def _p():
    return sys.modules["pyctures"]


H_CODEALONG = 18   # the page's code-along: codeAlong(options), codeAlongBegin(options), codeAlongEnd(), one call for each

# The words a file names to be given this library (the page, pages.USES_CODEALONG and `pyctures build` ask the same).
_USES = re.compile(r"code_along\w*")

BUDGET = {"side": 60, "stack": 34}
LEAD = 0.4
MAX_SPEED = 90
_M = 0xFFFFFFFF
_ALIASES = {"js": "javascript", "ts": "javascript", "typescript": "javascript", "javascript": "javascript",
            "py": "python", "python": "python", "python3": "python"}
_RENAME = {"typing_speed": "typingSpeed", "font_scale": "fontScale", "preview_error": "previewError"}


# ------------------------------------------------------------------ the typing: which stage, how many characters, at what time
def _imul(a, b):
    return ((a & _M) * (b & _M)) & _M


def _hash(a, b=0):
    """A number from 0 up to 1 that is always the same for the same a and b (the same as kinetic.js's hash)."""
    h = (_imul(a, 374761393) + _imul(b, 668265263)) & _M
    h = _imul(h ^ (h >> 13), 1274126177)
    h ^= h >> 16
    return (h & _M) / 4294967296


def _language(name):
    lang = _ALIASES.get(str("python" if name is None else name).lower())
    if not lang:
        raise ValueError('There is no tokenizer for "%s": use "javascript" or "python"' % name)
    return lang


def _normalise(stages, language=None):
    if not isinstance(stages, (list, tuple)) or not stages:
        raise ValueError("code_along needs stages: a list of {'code': ...} (a string is a stage of code)")
    out = []
    for i, s in enumerate(stages):
        stage = {"code": s} if isinstance(s, str) else dict(s)
        for py_key, js_key in (("type_at", "typeAt"), ("type_time", "typeTime")):
            if py_key in stage:
                stage[js_key] = stage.pop(py_key)
        if not isinstance(stage.get("code"), str):
            raise ValueError("code_along: stage %d has no code (a stage is {'code': '...'} or a string)" % i)
        code = re.sub(r"\n+$", "", stage["code"].replace("\r\n", "\n").replace("\r", "\n").replace("\t", "  "))
        out.append({**stage, "code": code, "language": _language(stage.get("language", language))})
    return out


def _diff(before, after):
    """What changed from before to after, as the editing that does it: the lines both keep stay, and each run of lines that differ is a hunk."""
    a = [] if before == "" else before.split("\n")
    b = [] if after == "" else after.split("\n")
    lcs = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            lcs[i][j] = lcs[i + 1][j + 1] + 1 if a[i] == b[j] else max(lcs[i + 1][j], lcs[i][j + 1])
    parts = []
    st = {"drop": [], "add": []}

    def flush():
        drop, add = st["drop"], st["add"]
        if not drop and not add:
            return
        old, now = "\n".join(drop), "\n".join(add)
        h = 0
        limit = min(len(old), len(now))
        while h < limit and old[h] == now[h]:
            h += 1
        t = 0
        while t < limit - h and old[len(old) - 1 - t] == now[len(now) - 1 - t]:
            t += 1
        hunk = {"hunk": True, "old": old, "hadOld": len(drop) > 0, "hasNew": len(add) > 0}
        if not drop or not add:
            hunk.update(head="", typed=now, tail="")
        else:
            hunk.update(head=now[:h], typed=now[h:len(now) - t], tail=now[len(now) - t:])
        parts.append(hunk)
        st["drop"], st["add"] = [], []

    i = j = 0
    while i < len(a) or j < len(b):
        if i < len(a) and j < len(b) and a[i] == b[j]:
            flush()
            if parts and not parts[-1]["hunk"]:
                parts[-1]["lines"].append(a[i])
            else:
                parts.append({"hunk": False, "lines": [a[i]]})
            i += 1
            j += 1
        elif j < len(b) and (i == len(a) or lcs[i][j + 1] >= lcs[i + 1][j]):
            st["add"].append(b[j])
            j += 1
        else:
            st["drop"].append(a[i])
            i += 1
    flush()
    return parts


def _compose(parts, n):
    pieces, spans = [], []
    cursor, start, offset = None, 0, 0
    for part in parts:
        if not part["hunk"]:
            text = "\n".join(part["lines"])
            pieces.append(text)
            offset += len(text) + 1
            continue
        length = len(part["typed"])
        local = n - start
        reached = local > 0 if length else local >= 0
        typed = max(0, min(length, local))
        text = part["head"] + part["typed"][:typed] + part["tail"] if reached else part["old"]
        if cursor is None:
            cursor = offset + (len(part["head"]) if part["hadOld"] else 0)
        if reached:
            if typed > 0:
                spans.append((offset + len(part["head"]), offset + len(part["head"]) + typed))
            cursor = offset + len(part["head"]) + typed
        if (part["hasNew"] if reached else part["hadOld"]):
            pieces.append(text)
            offset += len(text) + 1
        start += length
    return {"text": "\n".join(pieces), "cursor": 0 if cursor is None else cursor, "spans": spans}


def _weights(text, stage, seed):
    out = []
    for i, ch in enumerate(text):
        out.append(2.2 if ch == "\n" else 0.6 if ch == " " else 0.7 + 0.6 * _hash(i * 31 + stage, seed))
    return out


def _sum(values):
    total = 0.0
    for v in values:
        total += v
    return total


def plan(stages, duration=None, typing_speed=None, language=None, seed=None):
    """The timeline of a beat: for each stage when its typing starts and ends and when its hold ends, in seconds from the beat's start."""
    stages = _normalise(stages, language)
    speed = max(1, 22 if typing_speed is None else typing_speed)
    seed = 1 if seed is None else seed
    before = ""
    items = []
    for i, s in enumerate(stages):
        parts = _diff(before, s["code"])
        before = s["code"]
        typed = "".join(p["typed"] for p in parts if p["hunk"])
        w = _weights(typed, i, seed)
        hold = s.get("hold")
        items.append({"parts": parts, "index": i, "stage": s, "typed": typed, "w": w, "total": _sum(w),
                      "hold": max(0, 1.5 if hold is None else hold)})
    typing = _sum(it["total"] for it in items)
    holds = _sum(it["hold"] for it in items)
    natural = LEAD + typing / speed + holds
    rate, lead = speed, LEAD
    hold_of = lambda it: it["hold"]  # noqa: E731
    if duration is not None and duration > 0:
        want = duration
        if natural <= want:
            extra = (want - natural) / len(items)
            hold_of = lambda it: it["hold"] + extra  # noqa: E731
        else:
            def floor(it):
                return min(it["hold"], max(0.3, it["hold"] * 0.35))
            hold_min = _sum(floor(it) for it in items)
            if LEAD + typing / speed + hold_min <= want:
                f = (natural - want) / max(1e-9, holds - hold_min)
                hold_of = lambda it: it["hold"] - (it["hold"] - floor(it)) * f  # noqa: E731
            else:
                hold_of = floor
                room = want - LEAD - hold_min
                if room >= want * 0.2:
                    rate = typing / room
                else:
                    k = want / (LEAD + typing / speed + hold_min)
                    rate = speed / k
                    hold_of = lambda it: floor(it) * k  # noqa: E731
                    lead = LEAD * k
    warnings = []
    if rate > MAX_SPEED:
        warnings.append("the code is typed at %d characters a second to fit %s seconds, which is too fast to follow: give it more time or shorten the code" % (_round(rate), _js(duration)))
    def start_of(it):
        st = it["stage"]
        if st.get("at") is not None:
            return float(st["at"])
        if st.get("typeAt") is not None and duration is not None and duration > 0:
            return float(st["typeAt"]) * duration
        return None

    if any(start_of(it) is not None for it in items):
        warnings.clear()
        segments = []
        free = lead
        for i, it in enumerate(items):
            type_start = max(0, free if start_of(it) is None else start_of(it))
            nxt = start_of(items[i + 1]) if i + 1 < len(items) else None
            take = float(it["stage"]["typeTime"]) if it["stage"].get("typeTime") is not None else it["total"] / speed
            if nxt is not None and type_start + take > nxt - 0.3:
                take = max(0.05, nxt - 0.3 - type_start)
            type_end = type_start + take
            if nxt is not None:
                hold_end = max(type_end, nxt)
            else:
                hold_end = max(type_end + it["hold"], duration if i == len(items) - 1 and duration is not None and duration > 0 else 0)
            if it["total"] > 0 and it["total"] / take > MAX_SPEED:
                warnings.append("stage %d is typed at %d characters a second to fit the time before the next: give it more time or shorten the code" % (i + 1, _round(it["total"] / take)))
            segments.append({**it, "typeStart": type_start, "typeEnd": type_end, "holdEnd": hold_end})
            free = hold_end
        return {"segments": segments, "lead": segments[0]["typeStart"], "rate": speed, "total": segments[-1]["holdEnd"], "warnings": warnings, "stages": stages}
    t = lead
    segments = []
    for it in items:
        type_start = t
        t += it["total"] / rate
        type_end = t
        t += hold_of(it)
        segments.append({**it, "typeStart": type_start, "typeEnd": type_end, "holdEnd": t})
    return {"segments": segments, "lead": lead, "rate": rate, "total": t, "warnings": warnings, "stages": stages}


def _round(x):
    return int(math.floor(x + 0.5))


def _js(x):
    """A number as JavaScript writes it in a message."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def _lines_of(text, a, b):
    out = []
    if b <= a:
        return out
    line = 1
    for i in range(min(b, len(text))):
        if i >= a and line not in out:
            out.append(line)
        if text[i] == "\n":
            line += 1
    return out


def _at(P, t):
    segs = P["segments"]
    k = next((i for i, s in enumerate(segs) if t < s["holdEnd"]), -1)
    done = k < 0
    if done:
        k = len(segs) - 1
    s = segs[k]
    if done:
        phase, typed = "done", len(s["typed"])
    elif t < s["typeStart"]:
        phase, typed = "lead", 0
    elif t < s["typeEnd"]:
        phase = "type"
        target = ((t - s["typeStart"]) / max(1e-9, s["typeEnd"] - s["typeStart"])) * s["total"]
        typed = 0
        total = 0.0
        while typed < len(s["w"]) and total + s["w"][typed] <= target:
            total += s["w"][typed]
            typed += 1
    else:
        phase, typed = "hold", len(s["typed"])
    made = _compose(s["parts"], typed)
    text = made["text"]
    finished = k - 1 if phase in ("type", "lead") else k
    preview = -1 if finished < 0 else finished
    changed = []
    if k > 0:
        for a, b in made["spans"]:
            for line in _lines_of(text, a, b):
                if line not in changed:
                    changed.append(line)
    return {
        "stage": k, "phase": phase, "typed": typed, "inserted": len(s["typed"]), "length": len(text), "text": text, "cursor": made["cursor"],
        "changed": changed, "preview": preview, "previewTime": 0 if preview < 0 else t - segs[preview]["typeEnd"], "stageTime": t - s["typeStart"],
        "typeEnd": s["typeEnd"], "holdEnd": s["holdEnd"], "holdLeft": s["holdEnd"] - t,
    }


def _snake(name):
    return re.sub(r"[A-Z]", lambda m: "_" + m.group(0).lower(), name)


def code_along_stage_at(stages, t, duration=None, typing_speed=None, language=None, seed=None):
    """Which stage is being typed `t` seconds into the beat, and how many characters of it are typed: a dict with stage, phase, typed,
    inserted, length, text, cursor, changed (the lines lit), preview (the stage whose output is on show, -1 for none), preview_time,
    stage_time, type_end, hold_end, hold_left, total, rate and warnings."""
    P = plan(stages, duration, typing_speed, language, seed)
    out = _at(P, t)
    out.update(total=P["total"], rate=P["rate"], warnings=P["warnings"])
    return {_snake(k): v for k, v in out.items()}


# ------------------------------------------------------------------ the layout: the two panes and the size of the text
def _rows_of(text, cols):
    rows, at = [], 0
    for n, line in enumerate(text.split("\n")):
        indent = min(cols // 2, len(line) - len(line.lstrip(" ")) + 2)
        start = 0
        while True:
            room = cols if start == 0 else cols - indent
            to = len(line) if start + room >= len(line) else start + room
            if to < len(line):
                best = -1
                for i in range(start + 1, to + 1):
                    c = line[i - 1]
                    if c == ",":
                        cut = i + 1 if line[i:i + 1] == " " else i
                    elif c in "([{":
                        cut = i
                    elif c == " " and line[start:i].strip():
                        cut = i
                    else:
                        cut = -1
                    if cut > best and cut <= to + 1 and cut > start + room / 4 and len(line) - cut > 1:
                        best = cut
                if best > start:
                    to = min(best, len(line))
            rows.append({"line": n, "first": start == 0, "from": start, "to": to, "at": at + start, "indent": 0 if start == 0 else indent})
            start = to
            if start >= len(line):
                break
        at += len(line) + 1
    return rows


def _shape(w, h):
    r = h / w
    return "tall" if r >= 1.6 else "feed" if r >= 1.15 else "wide"


def _safe(W, H, over=None):
    style = _kinetic().house_style
    m = dict(style["safe"][_shape(W, H)])
    m.update(over or {})
    left, right, top, bottom = W * m["side"], W * (1 - m["side"]), H * m["top"], H * (1 - m["bottom"])
    return {"left": left, "top": top, "right": right, "bottom": bottom, "width": right - left, "height": bottom - top}


def _kinetic():
    return sys.modules["pykinetic"] if "pykinetic" in sys.modules else __import__("pykinetic")


def _clamp(x, a, b):
    return min(b, max(a, x))


def _layout(o, P, W, H):
    """The box, the two panes and the text size for these options in a frame W by H, as codealong.js works them out. `o` has the options in
    the page's spelling (layout, x, y, w, h, run, fontScale, safe). Returns a dict with mode, box, code, preview (None without one), px,
    cw, lh, pad, gap, gutter, cols, visible, warnings, minPx."""
    style = _kinetic().house_style
    warnings = []
    safe = _safe(W, H, o.get("safe"))
    box = {"x": safe["left"] if o.get("x") is None else o["x"], "y": safe["top"] if o.get("y") is None else o["y"],
           "w": safe["width"] if o.get("w") is None else o["w"], "h": safe["height"] if o.get("h") is None else o["h"]}
    run = o.get("run") is not False
    mode = o.get("layout") or "auto"
    if mode == "auto":
        mode = "stack" if box["h"] / box["w"] >= 1 else "side"
    if mode not in ("side", "stack"):
        raise ValueError('There is no layout "%s": use "auto", "side" or "stack"' % o.get("layout"))
    min_px = H * style["minimum"]
    scale = o.get("fontScale")
    wanted = (min_px if mode == "stack" else min_px * 1.15) * (1 if scale is None else scale)
    px = max(min_px, wanted)
    if wanted < min_px - 0.01:
        warnings.append("the text is raised to %d px, the least that is readable (3 percent of the frame's height): fontScale %s was too small" % (_round(min_px), _js(scale)))
    cw = px * 0.6
    lh = px * (1.28 if mode == "stack" else 1.32)
    pad = px * (0.4 if mode == "stack" else 0.45)
    gap = px * (0.5 if mode == "stack" else 0.7)
    lines = max(len(s["code"].split("\n")) for s in P["stages"])
    gutter = cw * (len(str(lines)) + 1.1)
    longest = max(len(l) for s in P["stages"] for l in s["code"].split("\n"))
    budget = BUDGET[mode]
    for i, s in enumerate(P["stages"]):
        for n, l in enumerate(s["code"].split("\n")):
            if len(l) > budget:
                warnings.append("line %d of stage %d is %d characters, over the budget of %d for this shape: it is wrapped, shorten it" % (n + 1, i + 1, len(l), budget))
    if not run:
        code, preview = dict(box), None
    elif mode == "side":
        want = gutter + 2 * pad + cw * (min(longest, budget) + 2)
        w = _clamp(want, box["w"] * 0.42, box["w"] * 0.62)
        code = {"x": box["x"], "y": box["y"], "w": w, "h": box["h"]}
        preview = {"x": box["x"] + w + gap, "y": box["y"], "w": box["w"] - w - gap, "h": box["h"]}
    else:
        cols0 = max(8, math.floor((box["w"] - gutter - 2 * pad) / cw))
        rows = max(len(_rows_of(s["code"], cols0)) for s in P["stages"])
        h = _clamp(rows * lh + 2 * pad, box["h"] * 0.2, box["h"] * 0.66)
        code = {"x": box["x"], "y": box["y"], "w": box["w"], "h": h}
        preview = {"x": box["x"], "y": box["y"] + h + gap, "w": box["w"], "h": box["h"] - h - gap}
    if preview:
        inset = o.get("previewPad") if o.get("previewPad") is not None else 0.04 * min(preview["w"], preview["h"])
        inner = {"w": preview["w"] - 2 * inset, "h": preview["h"] - 2 * inset}
    else:
        inset, inner = 0, None
    cols = max(8, math.floor((code["w"] - gutter - 2 * pad) / cw))
    visible = max(1, math.floor((code["h"] - 2 * pad) / lh))
    wrapped = []
    for i, s in enumerate(P["stages"]):
        for n, l in enumerate(s["code"].split("\n")):
            if len(l) > cols and len(l) <= budget and "line %d of stage %d" % (n + 1, i + 1) not in wrapped:
                wrapped.append("line %d of stage %d" % (n + 1, i + 1))
        rows = len(_rows_of(s["code"], cols))
        if rows > visible:
            warnings.append("stage %d is %d rows and %d fit: the code scrolls to keep the cursor in view" % (i + 1, rows, visible))
    if wrapped:
        warnings.append("%s does not fit %d columns at %d px: it is wrapped" % (", ".join(wrapped), cols, _round(px)))
    return {"mode": mode, "box": box, "code": code, "preview": preview, "inset": inset, "inner": inner, "px": px, "cw": cw, "lh": lh, "pad": pad, "gap": gap,
            "gutter": gutter, "cols": cols, "visible": visible, "warnings": warnings, "minPx": min_px}


# ------------------------------------------------------------------ the run: stages run here, and the scene's clock
class _Run:
    """What one run of a file keeps: the namespace a stage is given, and the stages that have begun."""

    def __init__(self, base):
        self.base = base
        self.runners = {}


def begin_run(ns, info, source):
    """A file is starting: if it names a code-along function, give it the names and keep the scene's names for the stages' namespaces."""
    if not _USES.search(source):
        return
    S = _p().S
    S.codealong = _Run({k: v for k, v in ns.items() if k not in ("setup", "update", "draw")})
    for name in NAMES:
        ns[name] = globals()[name]


def _run():
    return getattr(_p().S, "codealong", None)


def _seeding(seed, step):
    """The `random` module's own state is the scene's: a stage is given a seeded one, and the scene's is put back."""
    @contextlib.contextmanager
    def seeded():
        state = _random.getstate()
        _random.seed(seed * 100003 + step)
        try:
            yield
        finally:
            _random.setstate(state)
    return seeded()


class _Stage:
    def __init__(self, code, index, w, h, seed, base, demo=False):
        self.code, self.w, self.h, self.seed = code, w, h, seed
        self.time, self.began, self.error = 0.0, False, None
        self.ns = dict(base)
        self.ns.update(width=w, height=h, pixel_ratio=1, __name__="__code_along__")
        self.ns.update(_voice(self, demo))
        self.every = False
        self.hooks = {}
        self.run_top(index)

    def run_top(self, index):
        self.error = None
        try:
            with _seeding(self.seed, 0):
                exec(compile(self.code, "<code-along stage %d>" % (index + 1), "exec"), self.ns)
            self.hooks = {n: self.ns[n] for n in ("setup", "update", "draw") if callable(self.ns.get(n))}
        except Exception as e:  # noqa: BLE001 — a stage's mistakes are the stage's, shown in its pane
            self.error = _message(e)

    def step(self, t, index):
        if self.error:
            return
        h = self.hooks
        try:
            if not self.began:
                self.began = True
                self.every = "draw" not in h and "update" not in h
                if "setup" in h:
                    with _seeding(self.seed, 0):
                        h["setup"]()
            if "update" in h:
                steps = 0
                takes = getattr(getattr(h["update"], "__code__", None), "co_argcount", 1)
                while self.time + 1 / 60 <= t + 1e-9 and steps < 4000:
                    with _seeding(self.seed, steps + 1):
                        h["update"](1 / 60) if takes else h["update"]()
                    self.time += 1 / 60
                    steps += 1
            else:
                self.time = t
            if "draw" in h:
                with _seeding(self.seed, int(round(t * 60)) + 100000):
                    h["draw"]()
        except Exception as e:  # noqa: BLE001
            self.error = _message(e)


def _voice(stage, demo):
    """What a stage is given in place of say() and mouth(): the preview is silent (the beat's own voice-over owns the sound), say() gives back how
    long the line would take, and mouth() is drawn at a size of the preview's own (a sixth of its smaller side). `demo_voice=True` makes the mouth
    talk from a made-up level for the stage's last say() (not the draft voice's exact one: pictures.js has that); without it the mouth stays shut."""
    said = {"text": None, "at": 0.0, "seconds": 0.0}
    delay = demo.get("delay", 0) if isinstance(demo, dict) else 0

    def level():
        if not demo or said["text"] is None:
            return 0.0, False
        pos = stage.time - said["at"] - delay
        if pos < 0 or pos >= said["seconds"]:
            return 0.0, False
        beat = pos * 4.4
        return abs(math.sin(math.pi * beat)) ** 0.7 * (0.45 + 0.55 * _hash(int(beat), 3)), True

    def say(text, voice=None, lang="en", speaker=None):
        text = str(text)
        if text != said["text"]:
            said.update(text=text, at=stage.time, seconds=sys.modules["pysay"].estimate(text) if "pysay" in sys.modules else 0.075 * len(text) + 0.5)
        return said["seconds"]

    def mouth(x, y, size=None, style="oval", color="black", speaker=None):
        p = _p()
        open_ = level()[0]
        p.S.cmds.append(["call", p._user_line(), 0, 16, "mouth", [x, y, 0.16 * min(stage.w, stage.h) if size is None else size, style, color, open_, 0.5]])

    return {"say": say, "mouth": mouth, "speaking": lambda speaker=None: level()[1], "voice_level": lambda speaker=None: level()[0]}


def _message(e):
    return "%s: %s" % (type(e).__name__, e)


def _run_stage(run, key, index, code, w, h, seed, t, demo=False):
    """The cmds of a stage at time t of its own, and its mistake if it has one. The cmds are taken out of the frame, to be put between the page's two."""
    S = _p().S
    ctx = _p().ctx
    mark = len(S.cmds)
    ctx._shadow.clear()
    r = run.runners.get(key)
    if r is not None and (r.code != code or r.w != w or r.h != h or t < r.time - 1e-9):
        r = None
    if r is None:
        r = run.runners[key] = _Stage(code, index, w, h, seed, run.base, demo)
    elif r.every and r.began and not r.error:
        r.began = False
        r.hooks = {}
        r.run_top(index)
    r.step(max(0.0, t), index)
    cmds = S.cmds[mark:]
    del S.cmds[mark:]
    ctx._shadow.clear()
    if r.error:
        return [], r.error
    return cmds, None


def code_along(stages, start=0, duration=None, layout=None, x=None, y=None, w=None, h=None, typing_speed=None, style=None, run=None,
               live=None, font_scale=None, callouts=None, t=None, hold=None, language=None, seed=None, safe=None, preview_pad=None, demo_voice=None):
    """Code typed on one side, and what it draws on the other, for each stage of the typing. `stages` is a list of {"code": ..., "language":
    "python" or "javascript", "hold": seconds} (a string is a stage of code). Gives back a dict of what Python knows: progress, stage, phase,
    typed, preview (the stage on show, -1 for none), box, warnings; or None before `start`, and after the beat with hold=False."""
    p = _p()
    kit = _kinetic()
    state = _run()
    if state is None:
        raise RuntimeError("code_along() was not set up: name it in the file's own text (it is found by its name)")
    opts = {}
    for key, value in (("start", start), ("duration", duration), ("layout", layout), ("x", x), ("y", y), ("w", w), ("h", h),
                       ("typingSpeed", typing_speed), ("style", style), ("run", run), ("live", live), ("fontScale", font_scale),
                       ("callouts", callouts), ("hold", hold), ("previewPad", preview_pad), ("demoVoice", demo_voice), ("language", language), ("seed", seed), ("safe", safe)):
        if value is not None:
            opts[key] = value
    P = plan(stages, duration, typing_speed, language, seed)
    now = float(t) if t is not None else kit.kinetic_time()
    local = now - (start or 0)
    if local < 0 or (hold is False and local > P["total"]):
        return None
    ns = p.S.ns or {}
    W, H = ns.get("width", 0), ns.get("height", 0)
    L = _layout(opts, P, W, H)
    S = _at(P, local)
    shown, text, when = S["preview"], (P["stages"][S["preview"]]["code"] if S["preview"] >= 0 else ""), S["previewTime"]
    if live and S["phase"] == "type" and P["stages"][S["stage"]]["language"] == "python":
        seg = P["segments"][S["stage"]]
        shown, text, when = S["stage"], S["text"], S["stageTime"] - (seg["typeEnd"] - seg["typeStart"])
    out_opts = dict(opts)
    out_opts["stages"] = [{k: v for k, v in s.items() if k in ("code", "language", "hold", "at", "typeAt", "typeTime")} for s in P["stages"]]
    out_opts["t"] = now
    warnings = list(P["warnings"]) + list(L["warnings"])
    python_preview = L["preview"] is not None and shown >= 0 and P["stages"][shown]["language"] == "python"
    if not python_preview:
        p.S.cmds.append(["call", p._user_line(), 0, H_CODEALONG, "codeAlong", [out_opts]])
    else:
        pane = L["inner"]
        seed_ = (1 if seed is None else seed) * 1000 + shown
        live_now = text != P["stages"][shown]["code"]
        cmds, error = _run_stage(state, "%d%s" % (shown, "l" if live_now else ""), shown, text, pane["w"], pane["h"], seed_, when, demo_voice)
        if error and live_now and S["preview"] >= 0:
            # Not yet a program: the last whole stage stays on show.
            cmds, error = _run_stage(state, "%d" % S["preview"], S["preview"], P["stages"][S["preview"]]["code"], pane["w"], pane["h"],
                                     (1 if seed is None else seed) * 1000 + S["preview"], S["previewTime"], demo_voice)
            shown = S["preview"]
        if error and not live_now:
            out_opts["previewError"] = error
            warnings.append("stage %d would not run: %s" % (shown + 1, error))
        elif error:
            error = None
        p.S.cmds.append(["call", p._user_line(), 0, H_CODEALONG, "codeAlongBegin", [out_opts]])
        p.S.cmds.extend(cmds)
        p.S.cmds.append(["call", p._user_line(), 0, H_CODEALONG, "codeAlongEnd", []])
    return {"progress": min(1.0, max(0.0, local / P["total"])), "stage": S["stage"], "phase": S["phase"], "typed": S["typed"],
            "preview": S["preview"], "preview_time": S["previewTime"], "warnings": warnings, "box": L["box"], "layout": L["mode"], "size": L["px"]}


NAMES = ("code_along", "code_along_stage_at")
