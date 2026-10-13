"""Pyctures: Python 2D and 3D graphics, drawn in a web browser.

This module is the Python half of Pyctures. The same source runs in your own
CPython (``pyctures run``) and in the browser with Pyodide (``pyctures build``):
the browser half loads this very file as the module ``pyctures``.

NAMESPACE MAPPING. ``js``, ``canvas``, ``ctx``, ``THREE`` and ``addons`` are
proxies for objects that live in the browser page. Using one RECORDS a command;
nothing crosses to JavaScript until the frame ends (``draw()`` returns,
``await frame()``, or ``await flush()``). So a whole frame is one message.

  - ``a.b``         a lazy reference (nothing sent until it is used)
  - ``a.b(...)``    a call with ``this = a``; the result gets a handle number at
                    once, on the Python side, so it can be used in the same frame
  - ``A.B(...)``    a capitalised name is a constructor: ``new A.B(...)``
  - ``a.b = v``     a property write; the value is also remembered here, so
                    reading it back (``a.b``) needs no round trip
  - ``a.b += 1``    maths on a value that lives in the page is DEFERRED: it is
                    sent as an expression and worked out there
  - ``await a.b``   a real read, answered at the end of the frame
  - keyword args    become one trailing options object (``antialias=True``)
  - snake_case      ``fill_rect``, ``fill_style`` reach ``fillRect``, ``fillStyle``
  - functions       passed as callbacks (addEventListener) come back as events

Command shape (the contract with ``web/pyctures.js``). Every command is
``[kind, line, ...]``, ``line`` being the user's source line that made it::

  ['get',  line, newH, objH, name]
  ['set',  line, objH, name, value]
  ['call', line, newH, objH, name, args]
  ['new',  line, newH, objH, name, args]
  ['fcall',line, newH, fnH, args]
  ['fnew', line, newH, fnH, args]
  ['free', line, h]
  ['read', line, readId, value, newH]   (newH: where a promise's object lands)

Values: plain JSON, or {"$h": h}, {"$e": expr}, {"$cb": id}, {"$d": {...}}.

SCENES. A file may be several scenes (``class Title(Scene)``, ``go("game")``). That
is a library too, ``pyscenes``, in ``web/scenes``, but one a file does not import:
a file that names a scene is given its names (see ``_USES_SCENES``), and no other
file loads it. Its page half is the fixed handle H_SCENES.

SOUND AND DIALS are libraries of their own, ``synths`` and ``pydials``, which a
scene imports. Each records its commands here as drawing does, against a fixed
handle (H_SOUND, H_DIALS), so they ride the frame's message: a frame's sounds
are ONE command, ``send(batch)``, timed on Python's clock (see ``_State.ending``).

The host calls ``start(source, info_json)`` once, then ``tick(payload_json)``
once per frame, and ``stop()``. Each returns a JSON reply:
``{"cmds", "out", "err", "running", "error", "errorLine"}``.
"""
import sys, io, os, re, json, time, math, traceback, threading, types, linecache

__version__ = "0.2.0"

VERSION = "10"
USER_FILE = "main.py"

# Fixed handles the frame defines before anything runs.
H_WINDOW, H_CANVAS, H_THREE, H_CTX, H_ADDONS = 1, 2, 3, 4, 5
H_DRAW = 7   # the page's plain drawing functions (6 is taken where Pyctures is built into an editor)
H_SAVED = 8  # the page's keeper of saved values
H_FILES = 9  # the page's keeper of files and databases
H_SOUND = 10     # the page's sound: `from synths import *` sends it a frame's sounds as one command, send(batch)
H_DIALS = 11     # the page's dials, sliders and piano keys: `from pydials import *` makes each with one command
H_EFFECTS = 13   # pyvisualfx
H_NOTATION = 15  # the page's sheet music: `from pynotation import *`



class _State:
    def __init__(self):
        self.cmds = []
        self.next_read = 1
        self.reads = {}          # read id -> result once answered
        self.callbacks = {}      # callback id -> Python function
        self.next_cb = 1
        self.tasks = []          # live coroutines: [coro, waiting]
        self.ns = None           # the user's namespace
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.started = 0.0
        self.frame_no = 0
        self.thread = None
        self.busy = False
        self.stopped = False
        self.pictures = {}       # (text, size) -> a canvas with the text drawn once
        self.measuring = False   # measure mode: time each part of a frame
        self.sections = {}       # name -> ms this frame (measure mode)
        self.saved = {}          # name -> JSON text: what save() has kept
        self.page_files = False  # files live in the page's storage: each one written is sent to it
        self.files_dir = ""      # where the page put this scene's stored files (a browser); "" is the scene's folder
        self.databases = []      # every database that is open
        self.ending = []         # functions called as a frame is sent (a library that sends once a frame, as synths does)
        self.vt = None           # the scene's time while a recorder steps it (each frame says it), else None
        self.dt = None           # this frame's seconds, or None
        self.scenes = None       # what the library pyscenes keeps for this run, for a file that names a scene
        self.stage = None        # its director, once the file has defined a scene: each frame tests this and no more


# WHICH RUN A THREAD IS WORKING FOR. A host may run every frame as its own
# request on its own thread, and a frame from a run the user has just stopped
# can still be finishing while the next run starts. If both shared one state,
# the old frame's commands landed in the new run (objects the new preview never
# made). So each start()/tick() pins its run's state to its thread, and `S`
# reads through that pin; with no pin, it is the latest run.
_tls = threading.local()
_latest = [_State()]


class _Current:
    __slots__ = ()

    def __getattr__(self, name):
        return getattr(getattr(_tls, "state", None) or _latest[0], name)

    def __setattr__(self, name, value):
        setattr(getattr(_tls, "state", None) or _latest[0], name, value)


S = _Current()

# Never reset between runs: a reference from the LAST run that is collected
# during this one sends a 'free' for its number, and that number must not
# belong to anything new.
_next_handle = [1000]


def _user_line():
    f = sys._getframe(1)
    while f is not None:
        if f.f_code.co_filename == USER_FILE:
            return f.f_lineno
        f = f.f_back
    return 0


def _emit(*cmd):
    S.cmds.append([cmd[0], _user_line(), *cmd[1:]])


def _new_handle():
    _next_handle[0] += 1
    return _next_handle[0]


class PreviewValueError(TypeError):
    pass


_READ_HINT = ("this value lives in the preview, not in Python — "
              "read it with  value = await <expression>")


class _Read:
    """An awaitable for one value the frame has to send back.

    A PROMISE is awaited in the page: what it resolves to comes back as data,
    or, when it is an object (a GPU adapter, a device, a loaded font), as a
    reference that can be used like any other. Its handle number is reserved
    here, with the read, so the two sides never disagree on it.
    """
    __slots__ = ("rid",)

    def __init__(self, encoded):
        self.rid = S.next_read
        S.next_read += 1
        _emit("read", self.rid, encoded, _new_handle())

    def __await__(self):
        result = yield self
        if isinstance(result, dict) and len(result) == 1:
            if "$h" in result:
                return JsRef(result["$h"], owned=True)
            if "$error" in result:
                raise RuntimeError(result["$error"])
        return result


def _clock():
    return time.monotonic() if S.vt is None else S.vt


class _Frame:
    """'await frame()' — park until the next frame (also sends this one)."""
    __slots__ = ("until",)

    def __init__(self, seconds=0.0):
        self.until = _clock() + seconds

    def __await__(self):
        yield self


def frame():
    return _Frame()


# Another name for frame: 'await vsync()' waits for the screen's next refresh.
vsync = frame


def flush():
    """Send what has been drawn so far, now, and carry on next frame."""
    return _Frame()


def sleep(seconds):
    return _Frame(seconds)


# ---------------------------------------------------------------- expressions

class _Expr:
    __slots__ = ("tree",)

    def __init__(self, tree):
        object.__setattr__(self, "tree", tree)

    def _enc(self):
        return {"$e": self.tree}

    def __await__(self):
        return _Read(self._enc()).__await__()

    def __bool__(self):
        raise PreviewValueError(_READ_HINT)

    def __repr__(self):
        return "<preview expression>"


def _expr_of(v):
    if isinstance(v, _Expr):
        return v.tree
    if isinstance(v, JsRef):
        return ["ref", v._enc()]
    return ["v", _encode(v)]


def _binop(op):
    def fwd(self, other):
        return _Expr([op, _expr_of(self), _expr_of(other)])

    def rev(self, other):
        return _Expr([op, _expr_of(other), _expr_of(self)])
    return fwd, rev


for _name, _op in (("add", "+"), ("sub", "-"), ("mul", "*"), ("truediv", "/"),
                   ("mod", "%"), ("pow", "**"), ("floordiv", "//")):
    _f, _r = _binop(_op)
    setattr(_Expr, "__%s__" % _name, _f)
    setattr(_Expr, "__r%s__" % _name, _r)
_Expr.__neg__ = lambda self: _Expr(["neg", _expr_of(self)])


# ---------------------------------------------------------------- references

class JsRef:
    """A JavaScript object in the preview frame, seen from Python."""
    __slots__ = ("_h", "_parent", "_name", "_shadow", "_kids", "_owned", "_cmd", "__weakref__")

    def __init__(self, handle=None, parent=None, name=None, owned=False, cmd=None):
        object.__setattr__(self, "_h", handle)
        object.__setattr__(self, "_parent", parent)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_shadow", {})
        object.__setattr__(self, "_kids", {})
        object.__setattr__(self, "_owned", owned)
        # The unsent command that made this value. While it is still unsent and
        # the value is unused, a discarded result needs no handle at all.
        object.__setattr__(self, "_cmd", cmd)

    def _use(self):
        object.__setattr__(self, "_cmd", None)

    # A lazy member becomes a real handle the first time it is used as one.
    def _handle(self):
        self._use()
        if self._h is None:
            h = _new_handle()
            _emit("get", h, self._parent._handle(), self._name)
            object.__setattr__(self, "_h", h)
            object.__setattr__(self, "_owned", True)
        return self._h

    def _enc(self):
        return {"$h": self._handle()}

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        self._use()
        shadow = self._shadow
        if name in shadow:
            return shadow[name]
        kid = self._kids.get(name)
        if kid is None:
            kid = JsRef(parent=self, name=name)
            self._kids[name] = kid
        return kid

    def __setattr__(self, name, value):
        self._use()
        _emit("set", self._handle(), name, _encode(value))
        if isinstance(value, (int, float, str, bool)) or value is None:
            self._shadow[name] = value
        else:
            self._shadow.pop(name, None)
        self._kids.pop(name, None)

    def __getitem__(self, key):
        return self.__getattr__(str(key))

    def __setitem__(self, key, value):
        self.__setattr__(str(key), value)

    def __call__(self, *args, **kwargs):
        enc = [_encode(a) for a in args]
        if kwargs:
            enc.append({"$d": {k: _encode(v) for k, v in kwargs.items()}})
        self._use()
        h = _new_handle()
        if self._parent is not None and self._h is None:
            kind = "new" if self._name[:1].isupper() else "call"
            _emit(kind, h, self._parent._handle(), self._name, enc)
        else:
            _emit("fcall", h, self._handle(), enc)
        return JsRef(h, owned=True, cmd=S.cmds[-1])

    def new(self, *args, **kwargs):
        enc = [_encode(a) for a in args]
        if kwargs:
            enc.append({"$d": {k: _encode(v) for k, v in kwargs.items()}})
        h = _new_handle()
        if self._parent is not None and self._h is None:
            _emit("new", h, self._parent._handle(), self._name, enc)
        else:
            _emit("fnew", h, self._handle(), enc)
        return JsRef(h, owned=True)

    def __await__(self):
        if self._h is None and self._parent is not None:
            enc = {"$e": ["get", _expr_of(self._parent), self._name]}
        else:
            enc = self._enc()
        return _Read(enc).__await__()

    def __bool__(self):
        return True

    def __del__(self):
        try:
            cmd = self._cmd
            if cmd is not None and S.cmds and any(c is cmd for c in S.cmds[-64:]):
                cmd[2] = 0   # never used and not sent yet: do not keep it
            elif self._owned and self._h is not None and not S.stopped:
                S.cmds.append(["free", 0, self._h])
        except Exception:
            pass

    def __repr__(self):
        if self._parent is not None and self._h is None:
            return "<preview %s>" % self._name
        return "<preview object #%s>" % self._h


# Arithmetic on a reference to a value in the frame is deferred.
def _ref_expr(op, rev=False):
    def f(self, other):
        lhs = ["get", _expr_of(self._parent), self._name] if (self._h is None and self._parent is not None) else _expr_of(self)
        rhs = _expr_of(other)
        return _Expr([op, rhs, lhs] if rev else [op, lhs, rhs])
    return f


for _name, _op in (("add", "+"), ("sub", "-"), ("mul", "*"), ("truediv", "/"),
                   ("mod", "%"), ("pow", "**"), ("floordiv", "//")):
    setattr(JsRef, "__%s__" % _name, _ref_expr(_op))
    setattr(JsRef, "__r%s__" % _name, _ref_expr(_op, rev=True))


def _cmp_error(self, other):
    raise PreviewValueError(_READ_HINT)


for _name in ("lt", "le", "gt", "ge"):
    setattr(JsRef, "__%s__" % _name, _cmp_error)
    setattr(_Expr, "__%s__" % _name, _cmp_error)


# ---------------------------------------------------------------- values

def _encode(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            return {"$e": ["num", "NaN" if v != v else ("Infinity" if v > 0 else "-Infinity")]}
        return v
    if isinstance(v, JsRef):
        return v._enc()
    if isinstance(v, _Expr):
        return v._enc()
    if isinstance(v, (list, tuple)):
        return [_encode(x) for x in v]
    if isinstance(v, dict):
        return {"$d": {str(k): _encode(x) for k, x in v.items()}}
    if callable(v):
        cid = S.next_cb
        S.next_cb += 1
        S.callbacks[cid] = v
        return {"$cb": cid}
    tolist = getattr(v, "tolist", None)   # numpy arrays and scalars
    if tolist is not None:
        return _encode(tolist())
    return str(v)


class Event(dict):
    """An event from the preview: event.key, event.x … (also event["key"])."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


# ---------------------------------------------------------------- input state

#
# The page reports what happens (keys, pointers, the wheel) as events with the
# next frame; nothing is read back from the page. ``_input`` turns each event
# into the names below and calls the scene's on_... functions, before update.
#
# WHAT HAPPENED SINCE THE LAST FRAME (mouse.dx, mouse.dy, mouse.wheel,
# pinch.change, a touch's dx and dy, pressed, released) is set from the events
# that arrive with a frame and cleared at the top of the next, so it reads the
# same all through that frame: in update, in draw and after an ``await frame()``.

class _Keys(set):
    """The names of the keys held: ``"ArrowLeft" in keys``.

    Also ``keys.shift``, ``keys.ctrl``, ``keys.alt`` and ``keys.meta`` (True
    while that key is held), and ``keys.codes``: the same keys by where they
    are on the keyboard (``"KeyW"``), whatever the layout prints on them.
    """
    shift = ctrl = alt = meta = False

    def __init__(self, *args):
        super().__init__(*args)
        self.codes = set()

    def __repr__(self):
        held = [m for m in ("shift", "ctrl", "alt", "meta") if getattr(self, m)]
        names = "{%s}" % ", ".join(repr(k) for k in sorted(self, key=str)) if self else ""
        return "keys(%s)" % ", ".join([names] * bool(names) + ["%s=True" % m for m in held])


class _Mouse:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.down = False
        self.button = None    # "left", "middle" or "right" while one is down
        self.inside = False   # the pointer is over the scene
        self.dx = 0.0         # movement since the last frame
        self.dy = 0.0
        self.wheel = 0.0      # how far the wheel turned since the last frame

    def __repr__(self):
        return "mouse(x=%g, y=%g, down=%s, button=%r, inside=%s, dx=%g, dy=%g, wheel=%g)" % (
            self.x, self.y, self.down, self.button, self.inside, self.dx, self.dy, self.wheel)


class _Touch:
    """A finger, or a mouse button, that is down. The same object from start to end."""
    def __init__(self, id, x, y, type):
        self.id = id
        self.x = self.start_x = x
        self.y = self.start_y = y
        self.dx = 0.0
        self.dy = 0.0
        self.type = type      # "touch", "mouse" or "pen"

    def __repr__(self):
        return "touch(id=%r, x=%g, y=%g, start_x=%g, start_y=%g, dx=%g, dy=%g, type=%r)" % (
            self.id, self.x, self.y, self.start_x, self.start_y, self.dx, self.dy, self.type)


class _Pinch:
    def __init__(self):
        self.scale = 1.0      # 1 when the pinch starts
        self.change = 1.0     # how much it changed since the last frame
        self.x = 0.0          # the middle of the pinch
        self.y = 0.0

    def __repr__(self):
        return "pinch(scale=%g, change=%g, x=%g, y=%g)" % (self.scale, self.change, self.x, self.y)


keys = _Keys()
pressed = set()       # the keys that went down since the last frame
released = set()      # the keys that came up since the last frame
mouse = _Mouse()
touches = []          # every finger or mouse button down right now
pinch = _Pinch()


class _Input:
    """What the names above do not show."""
    def __init__(self):
        self.held = {}          # physical key -> the name it went down with
        self.fingers = {}       # pointer id -> its touch
        self.first = None       # the pointer `mouse` follows while it is down
        self.placed = False     # the mouse has been somewhere
        self.pinch_base = 1.0
        self.pinched_at = 0.0   # the trackpad's last pinch step: it has no end of its own
        self.stirred = False    # this frame has something to clear


_in = _Input()
_BUTTONS = ("left", "middle", "right")


def _reset_input():
    global _in
    _in = _Input()
    keys.clear()
    keys.codes.clear()
    keys.shift = keys.ctrl = keys.alt = keys.meta = False
    pressed.clear()
    released.clear()
    del touches[:]
    mouse.__init__()
    pinch.__init__()


def _new_frame():
    """Clear what the last frame was told had happened."""
    i = _in
    if i.stirred:
        i.stirred = False
        mouse.dx = mouse.dy = mouse.wheel = 0.0
        pinch.change = 1.0
        pressed.clear()
        released.clear()
        for touch in touches:
            touch.dx = touch.dy = 0.0
    if i.pinched_at:
        if time.monotonic() - i.pinched_at > 0.25:
            i.pinched_at = 0.0
            if len(touches) < 2:
                pinch.scale = 1.0


def _handle(name, *args):
    """Call the scene's function `name`, if it has one, with as many of `args` as it takes:
    on_key_down(key) and on_key_down(key, code) are both right."""
    fn = S.ns.get(name)
    if S.stage is not None:
        return S.stage.handle(name, fn, args)   # a file with scenes: its own function, then the current scene's
    if not callable(fn):
        return
    code = getattr(fn, "__code__", None)
    if code is not None and not code.co_flags & 0x04:   # no *args of its own
        takes = code.co_argcount - (1 if getattr(fn, "__self__", None) is not None else 0)
        if takes < len(args):
            args = args[:takes]
    r = fn(*args)
    if hasattr(r, "send"):
        task = [r, None]
        if _drive(task):
            S.tasks.append(task)


def _modifiers(e):
    m = e.get("m")
    if m is not None:
        keys.shift, keys.ctrl, keys.alt, keys.meta = bool(m & 1), bool(m & 2), bool(m & 4), bool(m & 8)


def _place(x, y, moved):
    """Put the mouse there. `moved`: it travelled (a finger going down somewhere new did not)."""
    i = _in
    if moved and i.placed:
        mouse.dx += x - mouse.x
        mouse.dy += y - mouse.y
    i.placed = True
    mouse.x, mouse.y = x, y
    ns = S.ns
    mouse.inside = 0 <= x <= ns.get("width", 0) and 0 <= y <= ns.get("height", 0)


def _spread():
    a, b = touches[0], touches[1]
    return max(1.0, math.hypot(b.x - a.x, b.y - a.y))


def _squeeze(change, x, y):
    pinch.scale *= change
    pinch.change *= change
    pinch.x, pinch.y = x, y
    _handle("on_pinch", pinch.scale, change)


def _regrip():
    """The fingers changed: two or more carry the pinch on from where it is, fewer end it."""
    if len(touches) >= 2:
        _in.pinch_base = _spread() / pinch.scale
    elif not _in.pinched_at:
        pinch.scale = 1.0


def _lift(e, cancelled):
    i = _in
    pid = e.get("id")
    touch = i.fingers.pop(pid, None)
    if touch is None:
        return
    x, y = e.get("x", touch.x), e.get("y", touch.y)
    touch.x, touch.y = x, y
    touches.remove(touch)
    _regrip()
    if pid == i.first:
        button = mouse.button
        i.first = None
        _place(x, y, True)
        mouse.down = False
        mouse.button = None
        _handle("on_mouse_up", x, y, button)
    _handle("on_touch_end", touch, cancelled)


def _input(e):
    """One event from the page: keep the input names true, and call the scene's function for it."""
    i = _in
    t = e.get("type")
    i.stirred = True
    if t == "pointermove":
        pid = e.get("id")
        touch = i.fingers.get(pid)
        x, y = e.get("x", mouse.x), e.get("y", mouse.y)
        if touch is not None:
            touch.dx += x - touch.x
            touch.dy += y - touch.y
            touch.x, touch.y = x, y
        # `mouse` follows the first pointer down, or whichever is moving while none is.
        if (pid == i.first) if touch is not None else (i.first is None):
            _place(x, y, True)
            _handle("on_mouse_move", x, y)
        if touch is not None:
            if len(touches) >= 2 and (touch is touches[0] or touch is touches[1]):
                a, b = touches[0], touches[1]
                _squeeze(_spread() / i.pinch_base / pinch.scale, (a.x + b.x) / 2, (a.y + b.y) / 2)
            _handle("on_touch_move", touch)
    elif t == "keydown":
        _modifiers(e)
        key, code = e.get("key"), e.get("code") or e.get("key")
        if e.get("r") and code in i.held:
            # A key held down repeats on the keyboard: it went down once.
            _handle("on_key_repeat", key, code)
            return
        i.held[code] = key
        keys.add(key)
        keys.codes.add(code)
        pressed.add(key)
        _handle("on_key_down", key, code)
    elif t == "keyup":
        _modifiers(e)
        code = e.get("code") or e.get("key")
        # By physical key: Shift let go first turns the name from "A" to "a",
        # and the name that went down is the one that must come out.
        key = i.held.pop(code, e.get("key"))
        keys.codes.discard(code)
        if key not in i.held.values():   # the two Shifts share a name
            keys.discard(key)
        released.add(key)
        _handle("on_key_up", key, code)
    elif t == "pointerdown":
        _modifiers(e)
        pid = e.get("id")
        if pid in i.fingers:
            _lift(e, True)   # its lift was never heard
        x, y = e.get("x", mouse.x), e.get("y", mouse.y)
        kind = e.get("pt") or "mouse"
        touch = _Touch(pid, x, y, kind)
        i.fingers[pid] = touch
        touches.append(touch)
        if len(touches) == 2:
            pinch.scale, i.pinched_at = 1.0, 0.0   # a pinch starts here, at 1
        _regrip()
        if i.first is None:
            i.first = pid
            _place(x, y, kind == "mouse")
            mouse.down = True
            b = e.get("button", 0)
            mouse.button = _BUTTONS[b] if b in (0, 1, 2) else "left"
            _handle("on_mouse_down", x, y, mouse.button)
        _handle("on_touch_start", touch)
    elif t == "pointerup":
        _lift(e, False)
    elif t == "pointercancel":
        _lift(e, True)
    elif t == "pointerleave":
        mouse.inside = False
    elif t == "wheel":
        amount = e.get("amount", 0)
        mouse.wheel += amount
        _handle("on_wheel", amount)
    elif t == "pinch":
        # A trackpad's pinch, worked out by the page.
        if len(touches) < 2:
            i.pinched_at = time.monotonic()
            _squeeze(e.get("change", 1.0), e.get("x", mouse.x), e.get("y", mouse.y))
    elif t == "blur":
        keys.clear()
        keys.codes.clear()
        i.held.clear()
        keys.shift = keys.ctrl = keys.alt = keys.meta = False


# ---------------------------------------------------------------- plain drawing
#
# circle, rect, line, text, background and the rest: one call each, for a first
# scene. Each is ONE command, done by the page in one go (handle H_DRAW), so
# 2,000 circles are 2,000 commands. What is given (a colour, a thickness, a
# size) is set on ctx and so stays for what is drawn next; what is left out is
# whatever ctx has. So ctx forgets what Python remembered of those values.
#
# EVERY SHAPE takes the same two keywords: outline="white", thickness=3. With a
# colour as well it is a filled shape with a border; without one it is the edge
# alone. They travel as one last argument, and only when they are given.

_FILL = ("fillStyle", "fill_style")
_STROKE = ("strokeStyle", "stroke_style", "lineWidth", "line_width")
_TEXT = _FILL + ("font", "textAlign", "text_align", "textBaseline", "text_baseline")


def _draw(name, args, how=None, forgets=_FILL):
    args = [_encode(a) for a in args]
    if how:
        args.append({"$d": {k: _encode(v) for k, v in how.items() if v is not None}})
        forgets = forgets + _STROKE
    S.cmds.append(["call", _user_line(), 0, H_DRAW, name, args])
    shadow = ctx._shadow
    if shadow:
        for key in forgets:
            shadow.pop(key, None)


def _how(outline, thickness, **more):
    if outline is None and thickness is None and not any(v is not None for v in more.values()):
        return None
    more["outline"], more["thickness"] = outline, thickness
    return more


def circle(x, y, radius, colour=None, outline=None, thickness=None):
    """A filled circle, centred on x, y."""
    _draw("circle", (x, y, radius, colour), _how(outline, thickness))


def ellipse(x, y, width, height, colour=None, outline=None, thickness=None):
    """An oval, centred on x, y, `width` across and `height` down."""
    _draw("ellipse", (x, y, width, height, colour), _how(outline, thickness))


def rect(x, y, width, height, colour=None, outline=None, thickness=None, round=None):
    """A filled box. x, y is its top left corner. round=12 rounds its corners."""
    _draw("rect", (x, y, width, height, colour), _how(outline, thickness, round=round))


def triangle(x1, y1, x2, y2, x3, y3, colour=None, outline=None, thickness=None):
    """Three corners."""
    _draw("triangle", (x1, y1, x2, y2, x3, y3, colour), _how(outline, thickness))


def polygon(x, y, radius, sides, colour=None, outline=None, thickness=None):
    """A shape with `sides` equal sides, centred on x, y, one corner straight up."""
    _draw("polygon", (x, y, radius, sides, colour), _how(outline, thickness))


def star(x, y, radius, points, colour=None, outline=None, thickness=None, inner=None):
    """A star with that many points, one straight up. Its inner corners are 0.4 of the radius out (inner=0.6 changes that)."""
    _draw("star", (x, y, radius, points, colour), _how(outline, thickness, inner=inner))


def line(x1, y1, x2, y2, colour=None, thickness=None):
    """A straight line from x1, y1 to x2, y2."""
    _draw("line", (x1, y1, x2, y2, colour, thickness), forgets=_STROKE)


def text(words, x, y, colour=None, size=None, align=None):
    """Words. x, y is their left end, on the line the letters sit on; with "centre", x, y is their middle."""
    _draw("text", (words, x, y, colour, size, align), forgets=_TEXT)


def background(colour=None):
    """Paint the whole picture one colour (or, with no colour, wipe it clear). It leaves ctx's own colour alone."""
    _draw("background", (colour,), forgets=())


_IMAGE_FILE = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif")


def picture(what, x, y, size=48):
    """An emoji or a word, or a picture from a file, centred on x, y and `size` high:
    picture("🌙", 300, 80, 60), picture("cat.png", 100, 100, 80), or an image from load_image.
    A file is loaded the first time it is asked for and draws nothing until it has arrived."""
    if isinstance(what, str) and (what.lower().endswith(_IMAGE_FILE) or what.startswith("data:image/")):
        key = ("file", what)
        img = S.pictures.get(key)
        if img is None:
            img = S.pictures[key] = ((S.ns or {}).get("load_image") or load_image)(what)
        what = img
    _draw("picture", (what, x, y, size), forgets=())


# ---------------------------------------------------------------- chance
#
# random(1, 6) is a whole number from 1 to 6, either end included; random(6) is
# from 0 to 6. If an end has a fraction (random(0, 0.5)) so may the answer.
# random() is a fraction from 0 up to 1.
#
# `random` is also the name of Python's own module, and every Python tutorial
# says `import random`. So the name a scene is given IS that module, made so it
# can be called as well: random.randint(1, 6) and random(1, 6) both work, with
# or without the import. A scene's own `import random` (or `from random import
# random`) is answered with the same object, by the import function its file is
# given; nothing in Python's real module, or in anyone else's imports, changes.

import builtins as _builtins
import random as _py_random


def _roll(a=None, b=None):
    if a is None:
        return _py_random.random()
    if b is None:
        a, b = 0, a
    if float(a).is_integer() and float(b).is_integer():
        return _py_random.randint(int(a), int(b))
    return _py_random.uniform(a, b)


class _Random(types.ModuleType):
    def __call__(self, a=None, b=None):
        return _roll(a, b)


random = _Random("random", _py_random.__doc__)
random.__dict__.update({k: v for k, v in vars(_py_random).items() if k not in ("__name__", "__doc__", "__spec__", "__loader__")})
random.random = _roll      # so `from random import random` can be called either way


def pick(things):
    """One thing from a list, picked by chance."""
    return _py_random.choice(things)


def _scene_import(name, globals=None, locals=None, fromlist=(), level=0):
    """The scene's `import random` gets the module that can also be called."""
    if name == "random" and level == 0 and globals is not None and globals is S.ns:
        return random
    return _builtins.__import__(name, globals, locals, fromlist, level)


def _scene_builtins():
    scope = dict(vars(_builtins))
    scope["__import__"] = _scene_import
    return scope


def degrees(n):
    """An angle said in degrees: every angle here (ctx.rotate, ctx.arc, a sprite's angle and spin) is in radians.
    (Python's own math.degrees goes the other way; math.radians is this.)"""
    return n * (math.pi / 180)


# ---------------------------------------------------------------- saved values
#
# save("best", 120) and load("best", 0): values that are still there the next
# time the program runs. The PAGE keeps them (the browser's storage, for this
# program alone), each as JSON text under its name. A page cannot be asked for
# a value and answer at once, and load() must, so the page hands over
# everything the program has saved when it starts (info["saved"]) and each
# save() is one command to it (handle H_SAVED). Where the page has no storage,
# or no page hands anything over, values last for the run and nothing fails.

def save(name, value):
    """Keep a value under a name, to load() the next time the program runs:
    save("best", 120). Numbers, text, True and False, lists and dictionaries."""
    name = str(name)
    try:
        kept = json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        raise TypeError('save("%s", ...) was given something it cannot keep. '
                        'It can keep numbers, text, True and False, lists and dictionaries' % name) from None
    S.saved[name] = kept
    S.cmds.append(["call", _user_line(), 0, H_SAVED, "save", [name, kept]])


def load(name, default=None):
    """The value saved under a name, or the default if nothing was: load("best", 0)."""
    kept = S.saved.get(str(name))
    if kept is None:
        return default
    try:
        # A fresh copy each time: changing a list that was loaded does not change what is saved.
        return json.loads(kept)
    except ValueError:
        return default


# ---------------------------------------------------------------- files and databases
#
# save_text("notes.txt", text), load_json("level.json", {}) and
# open_database("scores"): files the program writes, there the next time it
# runs. A path is from the scene's own folder and cannot leave it. A database is
# SQLite, Python's own sqlite3, in one file: "scores" is the file scores.db.
#
# WHERE THE FILES ARE. Run by your own Python (`pyctures run`), they are real
# files beside the scene and nothing more is needed. In a browser Python has a
# file system of its own that is forgotten with the page, so the PAGE keeps the
# files (the browser's storage, or what the app showing the scene gives it). As
# with saved values, the page cannot be asked for a file and answer at once, so
# before a scene starts it puts EVERY file the scene has stored into Python's
# file system, and each file written is one command to it (handle H_FILES):
# "text" with the path and the text, "bytes" with the path and the file in
# base64. That is why load_text() can answer at once.
#
# A FOLDER FOR EACH SCENE. A page's scenes share one Python, and one file
# system, so the page gives each scene a folder of its own for what it has
# stored (info["files_in"]): two scenes can both keep scores.db. Reading looks
# there first and then beside the scene, where the files that came with the
# scene are, so a level.json that came with it is read until one is saved.
#
# A DATABASE IS SENT WHOLE, so not on every statement: what a frame changes is
# finished (committed) and sent once, when the frame ends, and only if the file
# is not what was last sent. close() sends it there and then.

_sqlite = None  # Python's sqlite3, brought in by the first open_database()


def _file_path(path, call, such_as="notes.txt"):
    """A path as it is used: from the scene's folder, and never out of it."""
    parts = [p for p in str(path).replace("\\", "/").split("/")
             if p not in ("", ".", "..") and not p.endswith(":")]
    if not parts:
        raise ValueError('%s needs the name of a file, such as "%s"' % (call, such_as)) from None
    return "/".join(parts)


def _stored(path):
    """Where a stored file really is: in the folder the page gave this scene, or else as the path says."""
    return os.path.join(S.files_dir, path) if S.files_dir else path


def _write_file(path, text, call):
    try:
        file = _stored(path)
        folder = os.path.dirname(file)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(file, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    except (OSError, UnicodeError) as e:
        raise OSError("%s could not write the file (%s)" % (call, getattr(e, "strerror", None) or e)) from None
    if S.page_files:
        S.cmds.append(["call", _user_line(), 0, H_FILES, "text", [path, text]])


def save_text(path, text):
    """Write a text file: save_text("notes.txt", "milk, eggs"). It replaces the file if it is there."""
    call = 'save_text("%s", ...)' % (path,)
    path = _file_path(path, call)
    if not isinstance(text, str):
        raise TypeError("%s was given something that is not text. Use save_json for numbers, lists "
                        "and dictionaries, or str(...) to make text of it" % call) from None
    _write_file(path, text, call)


def load_text(path, default=None):
    """What a text file holds, or the default if there is no such file: load_text("notes.txt", "")."""
    return _read_file(path, 'load_text("%s")' % (path,), default)


def _read_file(path, call, default):
    path = _file_path(path, call)
    # What the scene stored, then (in a browser) the file that came with the scene.
    for file in ((_stored(path), path) if S.files_dir else (path,)):
        try:
            with open(file, encoding="utf-8", newline="") as f:
                return f.read()
        except (OSError, UnicodeError):
            pass
    return default


def save_json(path, value):
    """Write a value as a JSON file: save_json("level.json", {"walls": [[1, 2], [3, 4]]}).
    Numbers, text, True and False, lists and dictionaries."""
    call = 'save_json("%s", ...)' % (path,)
    path = _file_path(path, call)
    try:
        text = json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        raise TypeError("%s was given something it cannot keep. "
                        "It can keep numbers, text, True and False, lists and dictionaries" % call) from None
    _write_file(path, text, call)


def load_json(path, default=None):
    """The value in a JSON file, or the default if there is no such file: load_json("level.json", {})."""
    text = _read_file(path, 'load_json("%s")' % (path,), None)
    if text is None:
        return default
    try:
        return json.loads(text)
    except ValueError as e:
        raise ValueError('load_json("%s") found the file, but what is in it is not JSON (%s)' % (path, e)) from None


def _short(sql):
    sql = " ".join(str(sql).split())
    return sql if len(sql) <= 60 else sql[:57] + "..."


class Database:
    """A SQLite database in a file, from open_database("scores")."""

    def __init__(self, path, conn, file):
        self.path = path
        self._file = file       # where the file really is (see _stored)
        self._conn = conn
        self._changed = False   # something may have been written since the file was last kept
        self._sent = None       # the file as the page last had it (in a browser)

    def _do(self, call, sql, values):
        if self._conn is None:
            raise ValueError('%s("%s") was called after close(). Open the database again with '
                             'open_database("%s")' % (call, _short(sql), self.path)) from None
        if len(values) == 1 and isinstance(values[0], (list, tuple, dict)):
            values = values[0]
        try:
            return self._conn.execute(sql, values)
        except (_sqlite.Error, _sqlite.Warning, TypeError, ValueError, OverflowError) as e:
            raise ValueError('%s("%s") did not work. SQLite says: %s' % (call, _short(sql), e)) from None

    def query(self, sql, *values):
        """Ask a question: a list of rows, each a dictionary by column name.
        db.query("select name, points from best where points > ?", 10)"""
        cur = self._do("query", sql, values)
        try:
            names = [d[0] for d in cur.description or ()]
            rows = [dict(zip(names, row)) for row in cur.fetchall()]
        except (_sqlite.Error, _sqlite.Warning) as e:
            raise ValueError('query("%s") did not work. SQLite says: %s' % (_short(sql), e)) from None
        if self._conn.in_transaction:
            self._changed = True
        return rows

    def run(self, sql, *values):
        """Make a change, and say how many rows it changed:
        db.run("insert into best values (?, ?)", "Ann", 12)"""
        cur = self._do("run", sql, values)
        self._changed = True
        return max(0, cur.rowcount)

    def close(self):
        """Finish with the database. What it holds is kept."""
        if self._conn is None:
            return
        _keep_database(self, _user_line())
        _shut_database(self)
        if self in S.databases:
            S.databases.remove(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _keep_database(db, line=0):
    """Make what was changed last: finish the writes and, in a browser, send the page the file."""
    if db._conn is None or not db._changed:
        return
    db._changed = False
    try:
        if db._conn.in_transaction:
            db._conn.commit()
        if S.page_files:
            with open(db._file, "rb") as f:
                data = f.read()
            if data != db._sent:
                import base64
                db._sent = data
                S.cmds.append(["call", line, 0, H_FILES, "bytes", [db.path, base64.b64encode(data).decode("ascii")]])
    except Exception as e:  # noqa: BLE001 — a frame still has to be answered
        S.err.write("The database %s could not be kept (%s)\n" % (db.path, e))


def _shut_database(db):
    conn, db._conn = db._conn, None
    try:
        if conn.in_transaction:
            conn.commit()
        conn.close()
    except Exception:  # noqa: BLE001
        pass


def _close_databases(state):
    """A run has ended: its databases are finished with."""
    for db in state.databases:
        if db._conn is not None:
            _shut_database(db)
    state.databases = []


def open_database(name):
    """Open a SQLite database, making it if it is new: db = open_database("scores").
    Then rows = db.query("select ..."), db.run("insert ...") and db.close()."""
    global _sqlite
    call = 'open_database("%s")' % (name,)
    path = _file_path(name, call, "scores")
    if "." not in path.rsplit("/", 1)[-1]:
        path += ".db"
    if _sqlite is None:
        try:
            import sqlite3
        except ImportError:
            raise RuntimeError("%s could not load SQLite. In a browser it is loaded for a scene whose own "
                               "file says open_database, so call it from there" % call) from None
        _sqlite = sqlite3
    file = _stored(path)
    try:
        folder = os.path.dirname(file)
        if folder:
            os.makedirs(folder, exist_ok=True)
        if file != path and not os.path.exists(file) and os.path.isfile(path):
            # A database that came with the scene: the scene's own copy starts as that one.
            import shutil
            shutil.copyfile(path, file)
        # A host may run each frame on a thread of its own, so the connection is not tied to one.
        conn = _sqlite.connect(file, check_same_thread=False)
    except (OSError, _sqlite.Error) as e:
        raise ValueError("%s could not open the file %s. SQLite says: %s" % (call, path, e)) from None
    db = Database(path, conn, file)
    if S.page_files:
        try:
            with open(file, "rb") as f:
                db._sent = f.read()
        except OSError:
            pass
    S.databases.append(db)
    return db


# ---------------------------------------------------------------- hit-testing
#
# Numbers in, yes or no out. Nothing here knows what a sprite is, so a game
# engine can call these as they are, or put its own in their place. A circle is
# its centre and radius. A box is its centre, width and height; ``turn`` is the
# angle it is turned by, in radians (two boxes are tested upright). Shapes that
# only just meet at an edge do not touch; a point on an edge is inside.

def circles_touch(ax, ay, ar, bx, by, br):
    r = ar + br
    return (ax - bx) ** 2 + (ay - by) ** 2 < r * r


def boxes_touch(ax, ay, aw, ah, bx, by, bw, bh):
    return abs(ax - bx) * 2 < aw + bw and abs(ay - by) * 2 < ah + bh


def circle_touches_box(cx, cy, cr, bx, by, bw, bh, turn=0):
    dx, dy = cx - bx, cy - by
    if turn:
        # Seen from the box: turn the circle's centre back by the box's angle.
        c, s = math.cos(turn), math.sin(turn)
        dx, dy = dx * c + dy * s, dy * c - dx * s
    # How far the centre is outside the box, across and down (0 when it is level with it).
    dx = max(abs(dx) - bw / 2, 0)
    dy = max(abs(dy) - bh / 2, 0)
    return dx * dx + dy * dy < cr * cr


def point_in_circle(px, py, cx, cy, cr):
    return (px - cx) ** 2 + (py - cy) ** 2 <= cr * cr


def point_in_box(px, py, bx, by, bw, bh, turn=0):
    dx, dy = px - bx, py - by
    if turn:
        c, s = math.cos(turn), math.sin(turn)
        dx, dy = dx * c + dy * s, dy * c - dx * s
    return abs(dx) * 2 <= bw and abs(dy) * 2 <= bh


def _sprites_touch(a, b):
    """Two sprites, by their shapes."""
    if a._box:
        if b._box:
            return boxes_touch(a.x, a.y, a.width, a.height, b.x, b.y, b.width, b.height)
        return circle_touches_box(b.x, b.y, b.size * b._fit, a.x, a.y, a.width, a.height, a.angle)
    if b._box:
        return circle_touches_box(a.x, a.y, a.size * a._fit, b.x, b.y, b.width, b.height, b.angle)
    return circles_touch(a.x, a.y, a.size * a._fit, b.x, b.y, b.size * b._fit)


def remove(things, thing):
    """Take a thing out of a list (nothing happens if it is not there)."""
    try:
        things.remove(thing)
    except ValueError:
        return False
    return True


def _scene_size():
    ns = S.ns or {}
    return ns.get("width", 0), ns.get("height", 0)


# ---------------------------------------------------------------- sprites

def _takes_size(fn):
    """A sprite's picture function is given (ctx, size), as it always was.
    One that takes a single thing (def draw_ship(size)) is given the size
    alone. No picture function that worked before is called any differently:
    one with a single parameter could not be called with two at all."""
    code = getattr(fn, "__code__", None)
    if code is None or code.co_flags & 0x04:  # no code to read, or it takes *args
        return False
    takes = code.co_argcount
    if getattr(fn, "__self__", None) is not None:
        takes -= 1  # a method: self is already given
    return takes == 1


class Sprite:
    """A picture that moves. The picture is an emoji or text, an image, or a
    function that draws it: ``def draw_ship(size)``, or ``(ctx, size)``. Draws itself with ctx."""

    def __init__(self, picture, x=0, y=0, size=48):
        self.picture = picture
        self._drawn = None  # the picture function last drawn, and whether it takes the size alone
        self._size_only = False
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.angle = 0.0
        self.spin = 0.0
        self.size = size
        self.visible = True
        self.colour = "white"
        self._box = False
        # The hit circle's radius as a part of the size. 0.4, because an emoji has space round it.
        self._fit = 0.4
        # A box, or a circle with a radius of its own (see touches).
        self._special = False
        self._w = self._h = None

    @classmethod
    def box(cls, x, y, width, height=None, colour="white"):
        """A plain coloured box, ``width`` across and ``height`` down. It is hit-tested as a box."""
        if height is None:
            height = width
        s = cls(None, x, y, max(width, height))
        s.shape = "box"
        s.width, s.height = width, height
        s.colour = colour
        return s

    @classmethod
    def circle(cls, x, y, size, colour="white"):
        """A plain coloured circle, ``size`` across. Its hit circle is the circle you see."""
        s = cls(None, x, y, size)
        s.radius = size / 2
        s.colour = colour
        return s

    # "circle" or "box": the shape it is hit-tested as.
    @property
    def shape(self):
        return "box" if self._box else "circle"

    @shape.setter
    def shape(self, name):
        self._box = name == "box"
        self._special = self._box or self._fit != 0.4

    # A sprite is as wide and as tall as its size until it is told otherwise.
    @property
    def width(self):
        return self.size if self._w is None else self._w

    @width.setter
    def width(self, w):
        self._w = w

    @property
    def height(self):
        return self.size if self._h is None else self._h

    @height.setter
    def height(self, h):
        self._h = h

    @property
    def radius(self):
        return self.size * self._fit

    @radius.setter
    def radius(self, r):
        self._fit = r / self.size if self.size else 0.0
        self._special = self._box or self._fit != 0.4

    @property
    def color(self):
        return self.colour

    @color.setter
    def color(self, c):
        self.colour = c

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.spin:
            self.angle += self.spin * dt

    def draw(self):
        if not self.visible:
            return
        c = ctx
        c.save()
        c.translate(self.x, self.y)
        if self.angle:
            c.rotate(self.angle)
        s = self.size
        pic = self.picture
        if isinstance(pic, str):
            # Emoji/text is drawn ONCE into a small canvas and stamped from then
            # on: redrawing text every frame is the slow path on phones.
            box = s * 1.3
            c.drawImage(_picture(pic, s), -box / 2, -box / 2, box, box)
        elif pic is None:
            # No picture: its own shape, in its colour.
            c.fillStyle = self.colour
            if self._box:
                w, h = self.width, self.height
                c.fillRect(-w / 2, -h / 2, w, h)
            else:
                c.beginPath()
                c.arc(0, 0, s * self._fit, 0, math.pi * 2)
                c.fill()
        elif isinstance(pic, JsRef):
            w, h = self.width, self.height
            c.drawImage(pic, -w / 2, -h / 2, w, h)
        else:
            # A picture you draw yourself: 0, 0 is the sprite's middle, and it faces right.
            # It is given (ctx, size), or the size alone if that is all it asks for (see _takes_size).
            if pic is not self._drawn:
                self._drawn = pic
                self._size_only = _takes_size(pic)
            if self._size_only:
                pic(s)
            else:
                pic(c, s)
        c.restore()

    # --- touching. Whether a sprite can be seen makes no difference: a hidden one still touches.

    def touches(self, other):
        # Two plain round sprites are tested right here; a box, or a circle
        # with a radius of its own, goes the longer way.
        if self._special or other._special:
            return _sprites_touch(self, other)
        r = (self.size + other.size) * 0.4
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2 < r * r

    def hit(self, sprites):
        """The first sprite in the list that this one touches, or None."""
        for other in sprites:
            if other is not self and self.touches(other):
                return other
        return None

    def contains(self, x, y=None):
        """Is this point on the sprite? ``contains(x, y)``, or anything with an x and y: ``contains(mouse)``."""
        if y is None:
            x, y = x.x, x.y
        if self._box:
            return point_in_box(x, y, self.x, self.y, self.width, self.height, self.angle)
        return point_in_circle(x, y, self.x, self.y, self.size * self._fit)

    # --- the edges of the picture

    def wrap(self):
        """Gone off one edge? Come back on the opposite one."""
        width, height = _scene_size()
        w, h = self.width / 2, self.height / 2
        if self.x < -w:
            self.x = width + w
        elif self.x > width + w:
            self.x = -w
        if self.y < -h:
            self.y = height + h
        elif self.y > height + h:
            self.y = -h

    def bounce(self, *edges):
        """Bounce off the edges: all four, or the ones named, ``bounce("top", "bottom")``.
        Gives the edge it bounced off, or None."""
        width, height = _scene_size()
        if self._box:
            w, h = self.width / 2, self.height / 2
        else:
            w = h = self.size * self._fit
        edge = None
        if self.x < w and (not edges or "left" in edges):
            self.x, self.vx, edge = w, abs(self.vx), "left"
        elif self.x > width - w and (not edges or "right" in edges):
            self.x, self.vx, edge = width - w, -abs(self.vx), "right"
        if self.y < h and (not edges or "top" in edges):
            self.y, self.vy, edge = h, abs(self.vy), "top"
        elif self.y > height - h and (not edges or "bottom" in edges):
            self.y, self.vy, edge = height - h, -abs(self.vy), "bottom"
        return edge

    def offscreen(self):
        """Is all of it outside the picture?"""
        width, height = _scene_size()
        w, h = self.width / 2, self.height / 2
        return self.x < -w or self.x > width + w or self.y < -h or self.y > height + h

    # --- moving the way it faces (angle 0 is to the right, and it grows clockwise)

    def push(self, amount):
        """Speed up the way it faces."""
        self.vx += math.cos(self.angle) * amount
        self.vy += math.sin(self.angle) * amount

    def forward(self, distance):
        """Step the way it faces, without changing its speed."""
        self.x += math.cos(self.angle) * distance
        self.y += math.sin(self.angle) * distance

    def limit(self, speed):
        """Never faster than this."""
        now = math.hypot(self.vx, self.vy)
        if now > speed:
            self.vx *= speed / now
            self.vy *= speed / now

    def angle_to(self, other, y=None):
        """The angle from here to another sprite, to anything with an x and y, or to ``angle_to(x, y)``."""
        if y is None:
            return math.atan2(other.y - self.y, other.x - self.x)
        return math.atan2(y - self.y, other - self.x)

    def distance_to(self, other, y=None):
        """How far it is to another sprite, to anything with an x and y, or to ``distance_to(x, y)``."""
        if y is None:
            return math.hypot(other.x - self.x, other.y - self.y)
        return math.hypot(other - self.x, y - self.y)


def _picture(text, size):
    key = (text, size)
    pic = S.pictures.get(key)
    if pic is None:
        ratio = (S.ns or {}).get("pixel_ratio", 1) or 1
        px = max(1, int(size * 1.3 * ratio + 0.5))
        pic = js.document.createElement("canvas")
        pic.width = px
        pic.height = px
        g = pic.getContext("2d")
        g.font = "%dpx system-ui, sans-serif" % int(size * ratio)
        g.textAlign = "center"
        g.textBaseline = "middle"
        g.fillText(text, px / 2, px / 2 + size * ratio * 0.06)
        S.pictures[key] = pic
    return pic


def load_image(src):
    """An image for drawImage or a Sprite. Draws once it has loaded."""
    img = js.Image()
    img.src = src
    return img


# ---------------------------------------------------------------- the namespace

js = JsRef(H_WINDOW)
canvas = JsRef(H_CANVAS)
THREE = JsRef(H_THREE)
ctx = JsRef(H_CTX)
addons = JsRef(H_ADDONS)

class measure:
    """Time a section of your frame: `with measure("physics"): ...`. Shown in measure mode."""
    __slots__ = ("name", "t0")

    def __init__(self, name):
        self.name = str(name)

    def __enter__(self):
        self.t0 = time.perf_counter() if S.measuring else 0.0
        return self

    def __exit__(self, *exc):
        if self.t0:
            sec = S.sections
            sec[self.name] = sec.get(self.name, 0.0) + (time.perf_counter() - self.t0) * 1000
        return False


EXPORTS = ("js", "canvas", "ctx", "THREE", "addons", "frame", "vsync", "flush", "sleep",
           "keys", "mouse", "pressed", "released", "touches", "pinch",
           "circle", "rect", "line", "text", "background", "triangle", "ellipse", "polygon", "star",
           "picture", "random", "pick", "degrees", "save", "load",
           "save_text", "load_text", "save_json", "load_json", "open_database",
           "Sprite", "remove", "load_image", "Event", "measure")


# ---------------------------------------------------------------- breakpoints
#
# A pause HOLDS the thread running the frame, so only a host that answers
# other requests meanwhile (one thread per request) can pause. The
# ``pyctures`` command line does not use breakpoints; they are kept so the
# module stays the same everywhere it runs. The host asks debug_state() and answers with debug_resume()
# from those other requests. Only the user's file is traced.

class _Debug:
    def __init__(self):
        self.on = False
        self.bps = set()
        self.mode = None      # 'over' | 'into' | 'out' after a step
        self.depth = 0
        self.paused = False
        self.line = 0
        self.vars = {}
        self.action = None
        self.seq = 0          # one number per pause, so the host answers each once


DBG = _Debug()
_STEP = {"stepOver": "over", "stepInto": "into", "stepOut": "out"}


def _user_depth(frame):
    d = 0
    while frame is not None:
        if frame.f_code.co_filename == USER_FILE:
            d += 1
        frame = frame.f_back
    return d


def _vars(frame):
    out = {}
    names = dict(frame.f_globals) if frame.f_globals is not None else {}
    names.update(frame.f_locals)
    for name, value in names.items():
        if name.startswith("_") or (name in EXPORTS and value is globals().get(name)):
            continue   # ours, unless the file made its own thing of that name
        if isinstance(value, types.ModuleType) or (callable(value) and not isinstance(value, type)):
            continue
        try:
            if isinstance(value, (int, float, str, bool, type(None))):
                out[name] = {"value": value, "type": type(value).__name__}
            elif isinstance(value, (list, tuple, dict, set)):
                out[name] = {"value": repr(value)[:200], "type": type(value).__name__, "length": len(value)}
            else:
                out[name] = {"value": repr(value)[:200], "type": type(value).__name__}
        except Exception:
            out[name] = {"value": "<unreadable>", "type": type(value).__name__}
    return out


def _local_trace(frame, event, arg):
    if event == "line" and DBG.on and not S.stopped:
        line = frame.f_lineno
        mode = DBG.mode
        d = _user_depth(frame) if mode else 0
        if (line in DBG.bps or mode == "into"
                or (mode == "over" and d <= DBG.depth)
                or (mode == "out" and d < DBG.depth)):
            _pause(frame, line)
    return _local_trace


def _global_trace(frame, event, arg):
    if frame.f_code.co_filename != USER_FILE:
        return None
    return _local_trace


def _pause(frame, line):
    # This run's state, not whatever run is latest: a new run (or a reloaded
    # page) must still release a pause left behind.
    state = getattr(_tls, "state", None) or _latest[0]
    DBG.mode = None
    DBG.line = line
    DBG.vars = _vars(frame)
    DBG.action = None
    DBG.seq += 1
    DBG.paused = True
    try:
        while DBG.action is None and not state.stopped:
            time.sleep(0.02)
    finally:
        DBG.paused = False
    action = DBG.action
    if action == "stop" or state.stopped:
        raise KeyboardInterrupt("Stopped")
    DBG.mode = _STEP.get(action)
    DBG.depth = _user_depth(frame)


def debug_set(lines_json, on):
    DBG.on = bool(on)
    DBG.bps = set(json.loads(lines_json))
    DBG.mode = None
    return "ok"


def debug_state():
    return json.dumps({"paused": DBG.paused, "seq": DBG.seq, "line": DBG.line,
                       "vars": DBG.vars if DBG.paused else {}}, default=str)


def debug_resume(action):
    DBG.action = action
    return "ok"


class _Traced:
    """Trace the user's file for the length of one start() or tick()."""
    def __enter__(self):
        if DBG.on:
            sys.settrace(_global_trace)

    def __exit__(self, *exc):
        if DBG.on:
            sys.settrace(None)
        return False


# ---------------------------------------------------------------- running

def _drive(task, value=None):
    """Step one coroutine until it waits; returns False when it has finished."""
    coro = task[0]
    try:
        waiting = coro.send(value)
    except StopIteration:
        return False
    task[1] = waiting
    return True


def _format_error(e):
    tb = traceback.extract_tb(e.__traceback__)
    user = [fr for fr in tb if fr.filename == USER_FILE]
    lines = ["Traceback (most recent call last):"]
    for fr in user:
        lines.append('  line %d, in %s' % (fr.lineno, fr.name))
        if fr.line:
            lines.append("    " + fr.line.strip())
    line = user[-1].lineno if user else 0
    if isinstance(e, SyntaxError) and e.filename == USER_FILE and e.lineno:
        # A mistake in how the file is written: it never ran, so there is no
        # traceback into it, only the line the parser stopped at.
        line = e.lineno
        lines.append("  line %d" % line)
        if e.text:
            lines.append("    " + e.text.strip())
        lines.append("%s: %s" % (type(e).__name__, e.msg))
        return "\n".join(lines), line
    where = getattr(e, "pyctures_scene", None)
    lines.append("%s%s: %s" % ("In the scene %s: " % where if where else "", type(e).__name__, e))
    return "\n".join(lines), line


def _reply(error=None, error_line=0):
    for db in S.databases:
        _keep_database(db)   # once a frame, however many statements it ran
    for end in S.ending:
        end()
    S.dt = None
    cmds, S.cmds = S.cmds, []
    out = S.out.getvalue()
    err = S.err.getvalue()
    S.out = io.StringIO()
    S.err = io.StringIO()
    running = S.ns is not None and not error and (
        bool(S.tasks) or bool(S.callbacks) or S.stage is not None
        or any(callable(S.ns.get(n)) for n in _LIVE_NAMES))
    reply = {
        "cmds": cmds, "out": out, "err": err, "running": running,
        "error": error, "errorLine": error_line,
    }
    if S.measuring:
        reply["t"] = S.sections
        S.sections = {}
    return json.dumps(reply, default=str)


_LIVE_NAMES = ("draw", "update", "on_key_down", "on_key_up",
               "on_mouse_down", "on_mouse_move", "on_mouse_up",
               "on_touch_start", "on_touch_move", "on_touch_end", "on_wheel", "on_pinch",
               "on_key_repeat")


def _apply_info(p):
    ns = S.ns
    if ns is None:
        return
    for k in ("width", "height", "pixel_ratio"):
        if k in p:
            ns[k] = p[k]


def _apply_events(p):
    for ev in p.get("events", ()):
        e = Event(ev.get("e") or {})
        kind = ev.get("k")
        if kind == "cb":
            fn = S.callbacks.get(ev.get("id"))
            if fn is not None:
                r = fn(e)
                if hasattr(r, "send"):
                    # Kept only while it is still waiting: a callback that
                    # finishes without awaiting must not be driven again.
                    task = [r, None]
                    if _drive(task):
                        S.tasks.append(task)
            continue
        if kind == "scene":
            if S.stage is not None:
                S.stage.told(e)
            continue
        _input(e)


def _step_tasks(answers):
    now = _clock()
    alive = []
    for task in S.tasks:
        waiting = task[1]
        if isinstance(waiting, _Read):
            if waiting.rid not in answers:
                alive.append(task)
                continue
            keep = _drive(task, answers[waiting.rid])
        elif isinstance(waiting, _Frame):
            if waiting.until > now:
                alive.append(task)
                continue
            keep = _drive(task)
        else:
            keep = _drive(task)
        if keep:
            alive.append(task)
    S.tasks = alive


def _call_frame_functions(dt):
    ns = S.ns
    stage = S.stage
    if stage is not None:
        stage.step(dt)
    for name, args in (("update", (dt,)), ("draw", ())):
        fn = ns.get(name)
        if not callable(fn):
            continue
        if any(t[2:] == [name] for t in S.tasks):
            continue  # last frame's async draw is still waiting on a read
        takes = getattr(getattr(fn, "__code__", None), "co_argcount", 1)
        t0 = time.perf_counter() if S.measuring else 0.0
        r = fn(*args) if (name != "update" or takes) else fn()
        if t0:
            S.sections[name] = S.sections.get(name, 0.0) + (time.perf_counter() - t0) * 1000
        if hasattr(r, "send"):
            task = [r, None, name]
            if _drive(task):
                S.tasks.append(task)
    if stage is not None:
        stage.frame(dt)


# SCENES are the library pyscenes (web/scenes/pyscenes.py), brought in only for a file that names one: a class
# with Scene in its brackets, or a call of scene(), go(), next_scene(), config() or section() (the last two because they are written at the top of a
# file, before its first scene is). The page and `pyctures build` ask the
# same question of the same text with the same words (pyctures.js LIBRARIES, pages.uses_library).
_USES_SCENES = re.compile(r"(?:^|[^.\w])(?:Scene\b|(?:scene|go|next_scene|config|section)[ \t]*\()", re.M)


def _scenes_library():
    try:
        import pyscenes
    except ImportError:
        # Beside this file, where nothing has put it on the path (the tests, a host of its own).
        folder = os.path.join(os.path.dirname(os.path.abspath(globals().get("__file__") or "")), "web", "scenes")
        if not os.path.isfile(os.path.join(folder, "pyscenes.py")):
            raise
        sys.path.append(folder)
        import pyscenes
    return pyscenes


_MIDI_NAMES = ("on_midi", "on_midi_note", "on_midi_note_off", "on_midi_control", "on_midi_devices")


def _midi_hooks(ns):
    """A scene's own on_midi_note, on_midi_note_off, on_midi_control, on_midi and on_midi_devices are called by
    the sound library (`synths`), which the page hands what MIDI received with each frame. A scene that has
    none of them asks nothing of the page. (`from synths import *` gives a scene functions of the same names,
    for handing a function over; those are the library's own, and are not the scene's.)"""
    lib = sys.modules.get("synths")
    use = getattr(lib, "use_midi_hooks", None)
    if callable(use) and any(callable(ns.get(n)) and getattr(ns[n], "__module__", None) != lib.__name__ for n in _MIDI_NAMES):
        use(ns)


def start(source, info_json):
    """Run the file's top level. Returns the first frame's reply (JSON)."""
    _latest[0].stopped = True
    _close_databases(_latest[0])
    _latest[0] = _State()
    _tls.state = _latest[0]
    # FRESH ROOT NAMES EVERY RUN. A name like `js` remembers what was looked
    # up through it (js.document, THREE.DoubleSide) as handles in the preview
    # page; a new run has a new page, so reused names pointed at objects that
    # no longer exist ("that object no longer exists in the preview").
    global js, canvas, THREE, ctx, addons
    js, canvas, THREE = JsRef(H_WINDOW), JsRef(H_CANVAS), JsRef(H_THREE)
    ctx, addons = JsRef(H_CTX), JsRef(H_ADDONS)
    _reset_input()
    S.thread = threading.get_ident()
    S.busy = True
    S.started = time.monotonic()
    info = json.loads(info_json)
    S.vt = info.get("vt")
    S.measuring = bool(info.get("measure"))
    saved = info.get("saved")
    if isinstance(saved, dict):
        S.saved = {str(k): v for k, v in saved.items() if isinstance(v, str)}
    # In a browser the page keeps the files; a host that keeps them for another Python says so.
    S.files_dir = str(info.get("files_in") or "")
    S.page_files = bool(S.files_dir) or sys.platform == "emscripten" or bool(info.get("page_keeps_files"))
    ns = {"__name__": "__main__", "__builtins__": _scene_builtins()}
    for name in EXPORTS:
        ns[name] = globals()[name]
    S.ns = ns
    _apply_info(info)
    if _USES_SCENES.search(source):
        try:
            _scenes_library().begin_run(ns, info)
        except ImportError:
            pass   # a page that did not bring the library: the file's own mention of a scene is then a name that is not there
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = S.out, S.err
    tracer = _Traced()
    try:
        tracer.__enter__()
        import ast
        flags = getattr(ast, "PyCF_ALLOW_TOP_LEVEL_AWAIT", 0)
        # Tracebacks quote the line that failed: let them find the source.
        linecache.cache[USER_FILE] = (len(source), None, source.splitlines(True), USER_FILE)
        code = compile(source, USER_FILE, "exec", flags=flags)
        result = eval(code, ns)
        if hasattr(result, "send"):
            task = [result, None]
            if _drive(task):
                S.tasks.append(task)
        if callable(ns.get("setup")):
            r = ns["setup"]()
            if hasattr(r, "send"):
                task = [r, None]
                if _drive(task):
                    S.tasks.append(task)
        _midi_hooks(ns)
        if S.scenes is not None:
            S.scenes.begin(ns)
        _call_frame_functions(0.0)
    except BaseException as e:  # noqa: BLE001 — every failure is the user's to read
        msg, line = _format_error(e)
        S.ns = None
        return _reply(msg, line)
    finally:
        tracer.__exit__()
        sys.stdout, sys.stderr = old_out, old_err
        S.busy = False
    return _reply()


def tick(payload_json):
    """One frame: events and read answers in, this frame's commands out (JSON)."""
    _tls.state = _latest[0]
    if S.ns is None:
        return _reply("Nothing is running", 0)
    S.thread = threading.get_ident()
    S.busy = True
    p = json.loads(payload_json)
    S.frame_no += 1
    S.vt = p.get("vt", S.vt)
    S.measuring = bool(p.get("measure"))
    t_tick = time.perf_counter() if S.measuring else 0.0
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = S.out, S.err
    tracer = _Traced()
    try:
        tracer.__enter__()
        if "bps" in p:
            DBG.bps = set(p["bps"])
        _apply_info(p)
        answers = {int(k): v for k, v in (p.get("reads") or {}).items()}
        _new_frame()
        _apply_events(p)
        _step_tasks(answers)
        S.dt = float(p.get("dt", 0.0))
        _call_frame_functions(S.dt)
    except BaseException as e:  # noqa: BLE001
        msg, line = _format_error(e)
        S.ns = None
        return _reply(msg, line)
    finally:
        tracer.__exit__()
        sys.stdout, sys.stderr = old_out, old_err
        S.busy = False
    if t_tick:
        S.sections["python"] = (time.perf_counter() - t_tick) * 1000
    return _reply()


def stop():
    """Stop: drop the program, and interrupt it if it is stuck in a loop."""
    _tls.state = _latest[0]
    S.stopped = True
    S.ns = None
    S.tasks = []
    _close_databases(_latest[0])
    DBG.action = "stop"
    tid = S.thread
    # Only while a frame is actually running: a finished frame's thread id may
    # already belong to another request.
    if S.busy and tid is not None and tid != threading.get_ident():
        try:
            import ctypes
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid), ctypes.py_object(KeyboardInterrupt))
        except Exception:
            pass
    return "stopped"


