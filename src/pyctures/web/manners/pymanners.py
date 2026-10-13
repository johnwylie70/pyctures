"""pymanners: Pyctures' sound button, and the card a demo asks with: sound_button(), ask_about_sound()
and sound_is_on().

sound_button() puts a small speaker in a corner of the scene that switches all
of the scene's sound off and on (so does the M key). It asks nothing.
ask_about_sound() is a line of its own, for a demo that somebody may open in a
quiet room: before anything is heard a card asks "Play with sound" or "Play
without sound", and the scene waits. It puts the button up too.

A FILE DOES NOT IMPORT THIS. Pyctures' start() calls begin_run for a file with
the word "sound" in it, and a file that names one of the three is given them.
No other file loads it.

THE PAGE draws the button and the card, holds the switch and acts on a tap at
once (manners.js beside this file; the fixed handle H_MANNERS), so they work
however slow Python is. Python writes one command, show(options) or
ask(options), and is told with the next frame, through a function it gives the
page once (listen: told is called with {"on", "asking", "box"}).
The last choice comes with the scene's saved values, so sound_is_on() is right
from the first line. While the card is up Python is not asked for a frame.

PYCTURES ITSELF is reached through `_p()`, the module `pyctures` of the scene that is running, never by a plain
import at the top of this file. What a run keeps is a `_Run`, on Pyctures' own state as `S.manners`.
"""
import re
import sys


def _p():
    return sys.modules["pyctures"]


H_MANNERS = 14   # the page's sound button and its card: show(options), ask(options), set(on), remove(), listen(callback)
SOUND_KEPT = "sound:on"   # the saved value the page keeps the last choice under

_CORNERS = ("top right", "bottom right", "top left", "bottom left")


class _Run:
    """What one run of a file keeps about its sound button, as the page last said it."""

    def __init__(self, info):
        saved = info.get("saved")
        # Recorded a frame at a time (the page gives the recorder's time, `vt`): nobody is asked, and the sound is on.
        self.recorded = info.get("vt") is not None
        self.on = self.recorded or not (isinstance(saved, dict) and saved.get(SOUND_KEPT) == "false")
        self.asking = False      # the card is up (and `on` is False until it is answered)
        self.box = None          # where the button is: [x, y, size]
        self.asked = False       # ask_about_sound() has been called in this run

    def told(self, e):
        self.on, self.asking, self.box = bool(e.get("on")), bool(e.get("asking")), e.get("box")


# The page and `pyctures build` ask the same of the same text (pyctures.js LIBRARIES, pages.USES_MANNERS).
_USES = re.compile(r"sound_button|sound_is_on|ask_about_sound")


def begin_run(ns, info, source):
    """A file is starting: if it names the sound button, give it the names, and keep what the page says."""
    if not _USES.search(source):
        return
    S = _p().S
    run = S.manners = _Run(info)
    for name in ("sound_button", "ask_about_sound", "sound_is_on"):
        ns[name] = globals()[name]
    # The page tells this run what changes through an ordinary callback, with the next frame's events.
    cb = S.next_cb
    S.next_cb += 1
    S.callbacks[cb] = run.told
    S.cmds.append(["call", 0, 0, H_MANNERS, "listen", [cb]])


def _run():
    return getattr(_p().S, "manners", None)


def _emit(name, *args):
    p = _p()
    p.S.cmds.append(["call", p._user_line(), 0, H_MANNERS, name, list(args)])


def _corner(said, call="sound_button"):
    words = str(said).lower().replace("-", " ").replace("_", " ").split()
    up = [w for w in words if w in ("top", "bottom")]
    across = [w for w in words if w in ("left", "right")]
    if len(words) != 2 or len(up) != 1 or len(across) != 1:
        raise ValueError('%s("%s"): that is not a corner. The corners are: %s'
                         % (call, said, ", ".join('"%s"' % c for c in _CORNERS)))
    return up[0] + " " + across[0]


class _SoundButton:
    """What sound_button() gives back: `on` (read it, or set it), `asking` and over(x, y)."""
    __slots__ = ()

    @property
    def on(self):
        return _run().on

    @on.setter
    def on(self, value):
        _run().on = bool(value)
        _emit("set", bool(value))

    @property
    def asking(self):
        """Is the card that asks about sound still up?"""
        return _run().asking

    def over(self, x, y):
        """Is this point of the scene on the button?"""
        box = _run().box
        return bool(box) and box[0] <= x <= box[0] + box[2] and box[1] <= y <= box[1] + box[2]

    def remove(self):
        _run().box = None
        _emit("remove")

    def __repr__(self):
        return "<the sound button: sound is %s>" % ("on" if _run().on else "off")


_sound_button = _SoundButton()


def _place(call, corner, size, inset, colour, color, key):
    """The button's options as the page names them."""
    options = {"corner": _corner(corner, call), "colour": str(color if color is not None else colour), "key": str(key) if key else ""}
    if size is not None:
        if isinstance(size, bool) or not isinstance(size, (int, float)) or size <= 0:
            raise ValueError("%s(size=%r): the size is how many points across the button is, such as 44" % (call, size))
        options["size"] = size
    if inset is not None:
        pair = list(inset) if isinstance(inset, (list, tuple)) else [inset, inset]
        if len(pair) != 2 or any(isinstance(n, bool) or not isinstance(n, (int, float)) or n < 0 for n in pair):
            raise ValueError("%s(inset=%r): inset is how far in from the corner's two edges the button is, "
                             "as a number or (across, down)" % (call, inset))
        options["inset"] = pair
    return options


def sound_button(corner="top right", *, size=None, inset=None, colour="auto", color=None, key="m"):
    """A small speaker in a corner of the scene that switches all of its sound off and on (so does the M key),
    remembered for next time. It asks nothing. The corners are "top right", "bottom right", "top left" and
    "bottom left"; inset=(across, down) moves it in from its corner's edges, beside something the scene draws there."""
    _emit("show", _place("sound_button", corner, size, inset, colour, color, key))
    return _sound_button


def ask_about_sound(title=None, *, with_sound=None, without_sound=None, remember=False, wait=True,
                    corner="top right", size=None, inset=None, colour="auto", color=None, key="m"):
    """For a demo that somebody may open in a quiet room: before anything is heard, a card over the scene says
    "This demo has sound", with "Play with sound" and "Play without sound", and the scene waits for the answer.
    It puts the sound button up too, if the scene has not. title, with_sound and without_sound are the card's
    words; remember=True asks only until there is an answer; wait=False keeps the scene running behind the card.
    The rest are sound_button's, for the button it makes."""
    options = _place("ask_about_sound", corner, size, inset, colour, color, key)
    options.update(remember=bool(remember), wait=bool(wait))
    for name, words in (("title", title), ("withSound", with_sound), ("withoutSound", without_sound)):
        if words is not None:
            options[name] = str(words)
    # The page decides whether the card comes; until it says, the sound counts as off.
    p, run = _p(), _run()
    if not (remember and SOUND_KEPT in p.S.saved) and p.S.frame_no == 0 and not run.asked and not run.recorded:
        run.asking, run.on = True, False
    run.asked = True
    _emit("ask", options)
    return _sound_button


def sound_is_on():
    """Is the scene's sound on? False once it is switched off with the sound button, the M key or mute_sound(), and
    while the card that asks first is waiting for its answer."""
    return _run().on
