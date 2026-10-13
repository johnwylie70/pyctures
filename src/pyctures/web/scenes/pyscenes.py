"""pyscenes: the part of Pyctures that makes a file several scenes.

Pyctures loads it only for a file that names a scene (`class Title(Scene)`, `scene(...)`, `go(...)`,
`next_scene()`), and gives that file its names with nothing to import. Nothing here runs for any other file.

A PROGRAM IN SEVERAL SCENES, each starting empty, played one after another or
switched by the program. The words are Pymations' own wherever the thing is
the same thing (docs/scenes.md), and pictures.js has the same in camelCase.

  class Title(Scene):                 a scene is a group of the functions a file already has
      def setup(self): ...            (setup, update, draw and the on_ functions), with its own
      def draw(self): ...             variables on self. Every Scene class in the file plays, in
      def on_mouse_down(self, x, y):  the order written, the first one first
          next_scene()
  scene("title", draw=draw_title)     the same without a class: plain functions under a name
  go("game"), go(Game), next_scene(), restart()
  length = 12, beats = 16, bars = 4   a scene that ends by itself
  transition = "crossfade"            how a scene arrives, over transition_time seconds
  scene_time, scene_progress, scene_name
  section("name"), config(loop=False)

A file that defines no scene is one unnamed scene, as it always was: `S.stage`
stays None, and each frame costs one test of it.

THE PAGE RUNS A TRANSITION, NOT PYTHON. Python may be slow, or far away, and
sends one batch a frame; so a change of scene sends the page one command,
transition(name, seconds, colour), at the head of the new scene's first batch.
The page copies the picture the old scene left to a layer over the canvas and
fades, wipes or slides that still picture away on its own clock, every
refresh, while the new scene's frames arrive underneath whenever they do.
The page's object for all this is the fixed handle H_SCENES; a page that has
none (info["scenes"] is missing) is sent nothing, and every change is a cut.

PYCTURES ITSELF is reached through `_p()`, the module `pyctures` of the scene that is running (a browser's
Python has one for each scene on a page), never by a plain import at the top of this file. What a run keeps
is a `_Run`, on Pyctures' own state as `S.scenes`; the director, once the file has defined a scene, is `S.stage`.
"""
import json
import sys
import time


def _p():
    return sys.modules["pyctures"]


H_SCENES = 12    # the page's scene changes: transition(), empty(), show() (the scrubber's ticks)

_SCENE_SETTINGS = {"loop": True, "transition": "cut", "transition_time": 0.5, "transition_color": "black", "beats_per_bar": 4}
_TRANSITIONS = ("cut", "crossfade", "fade", "wipe", "wipe_left", "wipe_up", "wipe_down",
                "slide_left", "slide_right", "slide_up", "slide_down")


class _Run:
    """What one run of a file keeps about its scenes."""

    def __init__(self, info):
        self.written = []        # (name, class, functions) for each Scene class and scene() call, in the order written
        self.settings = dict(_SCENE_SETTINGS)
        self.ask = None          # a change of scene that was asked for: (said, target, options)
        self.marks = []          # section() marks: {"name", "t"}
        # A page that runs transitions and shows the scrubber says so, with any transitions of its own by name.
        more = info.get("scenes")
        self.page = bool(more)
        self.page_transitions = tuple(more.get("transitions") or ()) if isinstance(more, dict) else ()
        self.stage = None

    def begin(self, ns):
        """The file's top level has run: if it defined scenes, the first one begins."""
        if not self.written:
            return
        stage = self.stage = _p().S.stage = _Stage(self, ns)
        # A go() at the top level says which scene is first; a next_scene() there is carried out from the first.
        ask = self.ask
        if ask and ask[1] is not None:
            self.ask = None
            stage.enter(stage.find(ask[1], ask[0]))
        else:
            stage.enter(0)


def _run():
    run = _p().S.scenes
    if run is None:
        raise RuntimeError("Scenes are for a Pyctures file that is running")
    return run


def begin_run(ns, info):
    """A file that names a scene is starting: give it the names, and keep what it says."""
    _p().S.scenes = _Run(info)
    for name in ("Scene", "scene", "go", "next_scene", "restart", "section", "config"):
        ns[name] = globals()[name]


def _transition_name(name):
    """A transition's name as it is kept: Pymations' "none" is a cut and its "slide" goes left."""
    n = "".join("_" + c.lower() if c.isupper() else c for c in str(name or "cut")).lower()
    return {"none": "cut", "slide": "slide_left", "wipe_right": "wipe"}.get(n, n)


class Scene:
    """One scene of a program: write a class with this in brackets, and give it setup(self),
    update(self, dt), draw(self) and any of the on_ functions. Its own variables go on self."""
    length = None            # seconds, then the next scene begins
    beats = None             # or so many beats of the sound library's tempo
    bars = None              # or so many bars
    transition = None        # how it arrives: "crossfade", "fade", "wipe", "slide_left", ...; else config's
    transition_time = None
    transition_color = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        run = _p().S.scenes
        if run is not None:
            run.written.append((cls.__name__, cls, None))


def scene(name, **functions):
    """A scene from plain functions, with no class: scene("title", draw=draw_title, on_mouse_down=start)."""
    if not isinstance(name, str) or not name or not functions:
        raise TypeError('scene() needs a name and the scene\'s functions, as in scene("title", draw=draw_title)')
    run = _run()
    if run.stage is not None:
        raise RuntimeError('scene("%s", ...) was called after the program began. Name every scene at the top level of the file' % name)
    if any(n == name for n, _, _ in run.written):
        raise ValueError('There are two scenes called "%s"' % name)
    run.written.append((name, None, functions))


def config(**settings):
    """Settings for every scene: loop, transition, transition_time, transition_color, beats_per_bar."""
    for key, value in settings.items():
        key = key.replace("colour", "color")
        if key not in _SCENE_SETTINGS:
            raise TypeError('config() has no setting "%s". It has: %s' % (key, ", ".join(_SCENE_SETTINGS)))
        _run().settings[key] = value


def _ask(said, target, how):
    for key in how:
        if key not in ("transition", "transition_time", "transition_color", "transition_colour", "keep"):
            raise TypeError('%s has no option "%s". It takes transition, transition_time, transition_color and keep' % (said, key))
    run = _run()
    if run.stage is not None and target is not None:
        run.stage.find(target, said)
    run.ask = (said, target, how)


def go(scene, **how):
    """Change to a scene, by its name or its class: go("game"), go(Game, transition="wipe", transition_time=0.5).
    keep=True goes back to a scene as it was left (its resume() is called in place of setup())."""
    _ask("go(%s)" % (json.dumps(scene) if isinstance(scene, str) else getattr(scene, "__name__", "...")), scene, how)


def next_scene(**how):
    """Change to the next scene written; after the last one comes the first."""
    _ask("next_scene()", None, how)


def restart(**how):
    """Begin this scene again, from empty."""
    _ask("restart()", None, how)


def section(name):
    """A mark on the scrubber at this moment, beside the one each scene has."""
    run = _run()
    stage, marks = run.stage, run.marks
    name = str(name)
    # Said again (every frame, or the next time round), a mark stays where it was first put.
    if any(m["name"] == name for m in marks):
        return
    marks.append({"name": name, "t": stage.time() if stage else 0.0})
    if stage:
        stage.show()


def _page_scenes(name, *args):
    if _run().page:
        _p().S.cmds.append(["call", 0, 0, H_SCENES, name, list(args)])


def _trimmed(fn, args):
    """Call fn with as many of args as it takes: on_key_down(key) and on_key_down(key, code) are both right."""
    code = getattr(fn, "__code__", None)
    if code is not None and not code.co_flags & 0x04:   # no *args of its own
        takes = code.co_argcount - (1 if getattr(fn, "__self__", None) is not None else 0)
        if takes < len(args):
            args = args[:takes]
    return fn(*args)


class _Stage:
    """The director of a file's scenes."""

    def __init__(self, run, ns):
        self.run = run
        self.ns = ns
        self.settings = run.settings
        self.defs = [self._define(*w) for w in run.written]
        self.now = None          # the scene on show: a dict (see enter)
        self.clock = 0.0
        self.paused = False
        self.duration = 0.0
        self.shown_at = 0.0
        # The sound library's beat, only for a program that uses it.
        lib = sys.modules.get("synths")
        used = lib is not None and any(getattr(v, "__module__", None) == lib.__name__ or v is lib for v in ns.values())
        self.sound = lib if used and callable(getattr(lib, "beat", None)) else None
        self.timeline()

    def _define(self, name, cls, functions):
        read = (lambda key: getattr(cls, key, None)) if cls else (lambda key: functions.get(key))
        beats = read("beats")
        if beats is None and read("bars") is not None:
            beats = read("bars") * self.settings["beats_per_bar"]
        colour = read("transition_color")
        return {"name": name, "cls": cls, "functions": functions, "last": None, "start": None, "seconds": None,
                "length": read("length"), "beats": beats, "transition": read("transition"),
                "transition_time": read("transition_time"),
                "transition_color": colour if colour is not None else read("transition_colour")}

    # --- time
    def beat_seconds(self):
        return self.sound.beats(1) if self.sound else 0.5

    def beat_now(self):
        return self.sound.beat() if self.sound else self.clock * 2

    def long_of(self, d):
        if d["length"] is not None:
            return d["length"]
        return d["beats"] * self.beat_seconds() if d["beats"] is not None else None

    def timeline(self):
        """Where each scene starts, for as far as the lengths are known; the whole length when they all are."""
        t = 0.0
        for d in self.defs:
            d["start"] = t
            d["seconds"] = self.long_of(d)
            t = None if t is None or d["seconds"] is None else t + d["seconds"]
        self.duration = t or 0.0

    def time(self):
        now = self.now
        if now is None:
            return 0.0
        long = now["def"]["seconds"]
        return (now["def"]["start"] or 0.0) + (min(now["t"], long) if long is not None else now["t"])

    def show(self):
        """Tell the page the sections and where the program is, for its scrubber."""
        sections = [{"name": d["name"], "t": d["start"], "length": d["seconds"], "scene": True}
                    for d in self.defs if d["start"] is not None] + self.run.marks
        sections.sort(key=lambda s: s["t"])
        self.shown_at = self.clock
        _page_scenes("show", sections, self.duration, self.time(), self.now["def"]["name"] if self.now else "", self.paused)

    # --- which scene
    def find(self, target, said):
        for i, d in enumerate(self.defs):
            if d["cls"] is target or d["name"] == target or (isinstance(target, str) and d["name"].lower() == target.lower()) \
                    or (self.now is not None and target is self.now["self"] and d is self.now["def"]):
                return i
        raise LookupError('%s: there is no scene %s. The scenes are: %s' % (
            said, 'called "%s"' % target if isinstance(target, str) else "like that", ", ".join(d["name"] for d in self.defs)))

    def after(self):
        """The scene after this one: the first again after the last, or None when the program does not loop."""
        i = self.now["i"] + 1
        return i if i < len(self.defs) else 0 if self.settings["loop"] else None

    # --- a scene's own functions
    def act(self, name, args=(), tag=None):
        now = self.now
        fn = now["acts"].get(name) if now else None
        if fn is None:
            return
        try:
            r = _trimmed(fn, args)
        except BaseException as e:
            try:
                if not hasattr(e, "pyctures_scene"):
                    e.pyctures_scene = now["def"]["name"]
            except Exception:
                pass
            raise
        if hasattr(r, "send"):
            task = [r, None] + ([tag] if tag else [])
            if _p()._drive(task):
                _p().S.tasks.append(task)

    def handle(self, name, fn, args):
        """Something happened (a key, the mouse): the file's own function first, then the current scene's."""
        if callable(fn):
            r = _trimmed(fn, args)
            if hasattr(r, "send"):
                task = [r, None]
                if _p()._drive(task):
                    _p().S.tasks.append(task)
        if not self.paused:
            self.act(name, args)

    def controls(self):
        """The on-screen controls there are now (the library pydials keeps them by id)."""
        run = getattr(sys.modules.get("pydials"), "_run", None)
        return getattr(run, "items", None) if run is not None and getattr(run, "js", None) is _p().js else None

    def leave(self):
        now = self.now
        if now is None:
            return
        try:
            self.act("on_stop")
        finally:
            items = self.controls()
            if items:
                for key in [k for k in items if k not in now["made"]]:
                    item = items.get(key)
                    if item is not None:
                        item.remove()

    def enter(self, i, how=None, offset=0.0):
        how = how or {}
        d = self.defs[i]
        get = lambda key: how[key] if how.get(key) is not None else d[key] if d[key] is not None else self.settings[key]
        name = _transition_name(get("transition"))
        seconds = float(get("transition_time"))
        if name not in _TRANSITIONS and name not in self.run.page_transitions:
            raise ValueError('There is no transition "%s". The transitions are: %s' % (name, ", ".join(_TRANSITIONS + tuple(self.run.page_transitions))))
        # The first scene of all arrives with no transition: there is nothing to come from.
        if self.now is not None and name != "cut" and seconds > 0:
            # (A 3D picture is gone from its canvas once shown: the old scene is drawn once more, for the page to keep.)
            self.act("draw")
            colour = how.get("transition_colour") if how.get("transition_colour") is not None else get("transition_color")
            _page_scenes("transition", name, seconds, colour)
        else:
            _page_scenes("transition", "cut", 0, "")
        self.leave()
        kept = d["last"] if how.get("keep") and d["last"] is not None else None
        if kept is not None:
            me = kept
        elif d["cls"] is not None:
            try:
                me = d["cls"]()
            except BaseException as e:
                e.pyctures_scene = d["name"]
                raise
        else:
            me = d["functions"]
        d["last"] = me
        find = (lambda n: getattr(me, n, None)) if d["cls"] is not None else me.get
        acts = {n: find(n) for n in _SCENE_FUNCTIONS if callable(find(n))}
        items = self.controls()
        self.now = {"def": d, "self": me, "i": i, "acts": acts, "t": 0.0, "over": False, "made": set(items or ()),
                    "began": self.clock - offset,
                    "began_beat": self.beat_now() - offset / self.beat_seconds() if d["length"] is None and d["beats"] is not None else None}
        _page_scenes("empty")
        _p().ctx._shadow.clear()      # the page put the drawing settings back as they start
        self.tell(offset)
        self.show()
        self.act("resume" if kept is not None else "setup")

    def tell(self, t):
        now = self.now
        now["t"] = t
        long = now["def"]["seconds"]
        ns = self.ns
        ns["scene_time"] = t
        ns["scene_progress"] = min(1.0, t / long) if long else 0.0
        ns["scene_name"] = now["def"]["name"]

    def step(self, dt):
        """One frame of the director: a change that was asked for happens, and a scene whose time is up ends."""
        if self.paused:
            return
        self.clock += dt
        ask, self.run.ask = self.run.ask, None
        if ask is not None:
            said, target, how = ask
            i = self.find(target, said) if target is not None else self.now["i"] if said == "restart()" else self.after()
            if i is not None:
                self.enter(i, how)
        now = self.now
        t = (self.beat_now() - now["began_beat"]) * self.beat_seconds() if now["began_beat"] is not None else self.clock - now["began"]
        long = self.long_of(now["def"])
        if long is not None and t >= long and not now["over"]:
            nxt = self.after()
            if nxt is not None:
                # What ran over belongs to the next scene, so a sequence keeps time however the frames fall.
                return self.enter(nxt, None, min(t - long, 0.1))
            now["over"] = True
        self.tell(t)
        # The page's scrubber runs on its own clock between these.
        if self.duration and self.clock - self.shown_at >= 1.0:
            self.show()

    def frame(self, dt):
        """The current scene's update and draw, after the file's own."""
        for name, args in (("update", (dt,)), ("draw", ())):
            if name == "update" and self.paused:
                continue
            tag = "scene." + name
            S = _p().S
            if any(t[2:] == [tag] for t in S.tasks):
                continue  # last frame's async draw is still waiting on a read
            t0 = time.perf_counter() if S.measuring else 0.0
            self.act(name, args, tag)
            if t0:
                S.sections[name] = S.sections.get(name, 0.0) + (time.perf_counter() - t0) * 1000

    def told(self, e):
        """What the page's scrubber asks: {"seek": seconds} or {"pause": True}."""
        if "pause" in e:
            self.paused = bool(e["pause"])
        if "seek" in e and self.duration > 0:
            t = max(0.0, min(self.duration - 0.001, float(e["seek"] or 0)))
            i = 0
            while i + 1 < len(self.defs) and self.defs[i + 1]["start"] <= t:
                i += 1
            self.run.ask = None
            self.enter(i, {"transition": "cut"}, t - self.defs[i]["start"])
            fn = self.ns.get("on_seek")
            if callable(fn):
                _trimmed(fn, (t,))
            if self.paused:
                self.act("update", (0.0,))


_SCENE_FUNCTIONS = ("setup", "resume", "update", "draw", "on_stop", "on_key_down", "on_key_up",
                    "on_mouse_down", "on_mouse_move", "on_mouse_up",
                    "on_touch_start", "on_touch_move", "on_touch_end", "on_wheel", "on_pinch", "on_key_repeat")
