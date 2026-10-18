"""pykinetic: moving text for videos, in Pyctures. The same ten effects as pictures.js's kinetic text.

    word_slam("Learn *to code*. From zero.")
    count_up("12,000+", start=1, duration=2, style="techy")

A FILE DOES NOT IMPORT THIS. A file that names one of the functions below is given all of them (pages.USES_KINETIC,
pyctures.js LIBRARIES and `pyctures build` ask the same of the same text); no other file loads it.

THE PAGE DRAWS THE TEXT. kinetic.js beside this file (the very file that is pictures.js's kinetic/kinetic.js, brought
here by scripts/sync_libraries.py; the fixed handle H_KINETIC) draws each effect into the scene's canvas, in the
order the scene's other drawing was sent, so it goes behind or in front of it as the file wrote it. Python writes
ONE command for each call: the effect, the words and the options. It never measures or draws a letter.

TIME IS PYTHON'S. An effect is a function of the time it is given, and Python gives it: `t=` if the call has it, else
the scene's own seconds, kept here (`kinetic_time()`): the sum of the frames' dt, or the recorder's time when a recorder
steps the scene. So a scene recorded a frame at a time is exact, and the same time draws the same picture.

NOT THE SAME AS JAVASCRIPT, in two things: a call gives back None (pictures.js gives { progress, box, size }; the
page has not drawn yet when Python goes on), and `from` is `from_`.

house_style is the palette, fonts, sizes and voices every video shares (kinetic.js beside this file, written into
this one by scripts/sync_libraries.py: do not edit the table by hand).

PYCTURES ITSELF is reached through `_p()`, the module `pyctures` of the scene that is running.
"""
import json
import re
import sys


def _p():
    return sys.modules["pyctures"]


H_KINETIC = 17   # the page's kinetic text: one call for each effect (the names are pictures.js's, in camelCase)

# The words a file names to be given this library (the page, pages.USES_KINETIC and `pyctures build` ask the same).
_USES = re.compile(r"word_slam|letter_wave|letter_bounce|typewriter_text|glitch_text|mask_reveal|scale_pop|ticker_text|count_up|highlight_sweep|kinetic_\w+|code_along\w*|house_style|seeded_random")


class _Style(dict):
    """The house style: a dict you can also read with a dot (house_style.palette.ink)."""
    __slots__ = ()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None


def _wrap(value):
    if isinstance(value, dict):
        return _Style({k: _wrap(v) for k, v in value.items()})
    return value


# STYLE:BEGIN
_STYLE = json.loads(r"""{"palette":{"ink":"#0b1020","paper":"#f8fafc","dim":"#94a3b8","blue":"#3b82f6","cyan":"#22d3ee","pink":"#f472b6","yellow":"#facc15","green":"#34d399"},"fonts":{"display":"\"Avenir Next\", \"Arial Rounded MT Bold\", \"Trebuchet MS\", system-ui, -apple-system, sans-serif","mono":"ui-monospace, \"SF Mono\", Menlo, Consolas, \"Liberation Mono\", monospace"},"scale":{"hook":0.13,"title":0.085,"body":0.05,"caption":0.04},"minimum":0.03,"safe":{"wide":{"top":0.05,"bottom":0.05,"side":0.05},"tall":{"top":0.14,"bottom":0.18,"side":0.06},"feed":{"top":0.08,"bottom":0.1,"side":0.06}},"voices":{"playful":{"font":"\"Avenir Next\", \"Arial Rounded MT Bold\", \"Trebuchet MS\", system-ui, sans-serif","weight":900,"colour":"#f8fafc","accent":"#facc15","second":"#f472b6","spring":1},"techy":{"font":"ui-monospace, \"SF Mono\", Menlo, Consolas, monospace","weight":700,"colour":"#e0f2fe","accent":"#22d3ee","second":"#3b82f6","spring":0.4},"calm":{"font":"system-ui, -apple-system, \"Segoe UI\", sans-serif","weight":500,"colour":"#e2e8f0","accent":"#7dd3fc","second":"#94a3b8","spring":0}}}""")
# STYLE:END
house_style = _wrap(_STYLE)


class _Run:
    """What one run of a file keeps: the scene's seconds."""

    def __init__(self, info):
        self.t = 0.0
        self.held = False

    def now(self):
        """The scene's seconds: the recorder's own time when it steps the scene, else the frames' dt added up (or what was set)."""
        vt = _p().S.vt
        return float(vt) if vt is not None and not self.held else self.t

    def frame(self):
        if not self.held:
            self.t += _p().S.dt or 0.0


def begin_run(ns, info, source):
    """A file is starting: if it names a kinetic text function, give it the names and keep the scene's seconds."""
    if not _USES.search(source):
        return
    S = _p().S
    run = S.kinetic = _Run(info)
    # The scene's seconds move on as each frame is sent, so a frame's draw sees the time before it.
    S.ending.append(run.frame)
    for name in NAMES:
        ns[name] = globals()[name]
    ns["house_style"] = house_style


def _run():
    return getattr(_p().S, "kinetic", None)


def _beat(beat):
    """A number of beats, or an object that has a .beat (or a dict with "beat"), as a number."""
    if beat is None:
        return None
    if isinstance(beat, dict):
        beat = beat.get("beat")
    elif not isinstance(beat, (int, float)):
        beat = getattr(beat, "beat", None)
    return float(beat) if isinstance(beat, (int, float)) and not isinstance(beat, bool) else None


def _options(call, start, duration, t, x, y, size, style, colour, color, accent, beat, safe, seed, more):
    o = {}
    for key, value in (("start", start), ("duration", duration), ("x", x), ("y", y), ("size", size), ("style", style),
                       ("colour", color if color is not None else colour), ("accent", accent), ("safe", safe), ("seed", seed)):
        if value is not None:
            o[key] = value
    if isinstance(safe, (list, tuple)):
        raise ValueError("%s(safe=%r): safe is a dict such as {'top': 0.1, 'bottom': 0.2, 'side': 0.05}" % (call, safe))
    b = _beat(beat)
    if beat is not None and b is None:
        raise ValueError("%s(beat=%r): beat is a number of beats, or something with a .beat" % (call, beat))
    if b is not None:
        o["beat"] = b
    for key, value in more.items():
        if value is not None:
            o["from" if key == "from_" else key] = value
    # The page is given the time, so it is Python's clock that every effect follows.
    if t is None:
        run = _run()
        t = run.now() if run else 0.0
    o["t"] = float(t)
    return o


def _emit(name, text, options):
    p = _p()
    p.S.cmds.append(["call", p._user_line(), 0, H_KINETIC, name, [str(text), options]])


def _make(js, doc, extra=()):
    snake = re.sub(r"[A-Z]", lambda m: "_" + m.group(0).lower(), js)

    def effect(text, *, start=None, duration=None, t=None, x=None, y=None, size=None, style=None, colour=None, color=None,
               accent=None, beat=None, safe=None, seed=None, hold=None, pulse=None, **more):
        for k in more:
            if k not in extra:
                raise TypeError("%s() has no option %r" % (snake, k))
        _emit(js, text, _options(snake, start, duration, t, x, y, size, style, colour, color, accent, beat, safe, seed,
                                 dict(more, hold=hold, pulse=pulse)))

    effect.__name__ = effect.__qualname__ = snake
    effect.__doc__ = doc
    return effect


word_slam = _make("wordSlam", "The words land one at a time, hard, and the whole text shakes a little.")
letter_wave = _make("letterWave", "The letters appear one after another, then ride a wave (speed= changes it).", ("speed",))
letter_bounce = _make("letterBounce", "The letters drop in and bounce.")
typewriter_text = _make("typewriterText", "Typed out, a little unevenly, with a cursor that blinks after.")
glitch_text = _make("glitchText", "Red and blue copies split apart and slices jump sideways (amount= is how much).", ("amount",))
mask_reveal = _make("maskReveal", 'A wipe uncovers the text; direction= is "right", "left", "up" or "down".', ("direction",))
scale_pop = _make("scalePop", "The words rise into place and each *starred* word swells and settles.")
ticker_text = _make("tickerText", "One line scrolling along a strip, for as long as it is on (speed= changes it).", ("speed",))
count_up = _make("countUp", 'A number counting up, with its commas and the words round it: count_up("12,000+"). from_= is where it starts.', ("from_",))
highlight_sweep = _make("highlightSweep", "A highlighter sweeps under the *starred* words, or under each line if there are none.")

_KINDS = {"slam": word_slam, "wave": letter_wave, "bounce": letter_bounce, "type": typewriter_text, "typewriter": typewriter_text,
          "glitch": glitch_text, "reveal": mask_reveal, "wipe": mask_reveal, "pop": scale_pop, "ticker": ticker_text,
          "count": count_up, "counter": count_up, "highlight": highlight_sweep}


def kinetic_text(kind, text, **options):
    """Any effect by a short name: "slam", "wave", "bounce", "type", "glitch", "reveal", "pop", "ticker", "count" or "highlight"."""
    effect = _KINDS.get(kind)
    if effect is None:
        raise ValueError('There is no kinetic effect "%s": use %s' % (kind, ", ".join('"%s"' % k for k in _KINDS)))
    effect(text, **options)


def kinetic_effects():
    """The short names kinetic_text() takes."""
    return list(_KINDS)


def kinetic_time(seconds=None, hold=False):
    """The scene's seconds (they start at 0 and go on by each frame's dt). kinetic_time(5) sets them,
    and kinetic_time(5, hold=True) stops them there until it is told otherwise."""
    run = _run()
    if run is None:
        return 0.0
    if seconds is not None:
        run.t, run.held = float(seconds), bool(hold)
    return run.now()


def _shape(w, h):
    r = h / w
    return "tall" if r >= 1.6 else "feed" if r >= 1.15 else "wide"


def kinetic_safe(safe=None, **over):
    """The safe area in pixels, as a dict: left, top, right, bottom, width, height. Text stays inside it."""
    ns = _p().S.ns or {}
    w, h = ns.get("width", 0), ns.get("height", 0)
    m = dict(house_style["safe"][_shape(w, h)] if w else house_style["safe"]["wide"])
    m.update(safe or {})
    m.update(over)
    left, right, top, bottom = w * m["side"], w * (1 - m["side"]), h * m["top"], h * (1 - m["bottom"])
    return _Style(left=left, top=top, right=right, bottom=bottom, width=right - left, height=bottom - top)


def seeded_random(seed=1):
    """A random function that gives the same numbers for the same seed (the same as pictures.js's seededRandom)."""
    state = [int(seed) & 0xFFFFFFFF]

    def imul(a, b):
        return (a * b) & 0xFFFFFFFF

    def roll():
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        a = state[0]
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return roll


NAMES = ("word_slam", "letter_wave", "letter_bounce", "typewriter_text", "glitch_text", "mask_reveal", "scale_pop",
         "ticker_text", "count_up", "highlight_sweep", "kinetic_text", "kinetic_time", "kinetic_safe", "kinetic_effects",
         "seeded_random")
