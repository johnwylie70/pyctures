"""A file in several scenes: `class Title(Scene)`, `scene("title", draw=...)`, go, next_scene, restart,
lengths, transitions, sections.

The first half is the Python half alone: which scene is on show, what each is called with, and the
commands the page is sent (the fixed handle 12). The second half is a real (headless) Chromium: the
pixels of each transition at its start, half way and end, measured on a screenshot (a transition is the
browser's own mixing of two layers), that a transition stays smooth while Python makes two frames a
second, and the scrubber.
"""
import json
import sys
import textwrap
import types
import zlib

import pytest

import pyctures

H_SCENES = 12


def start(src, scenes=True, **info):
    info = dict({"width": 400, "height": 300, "pixel_ratio": 1}, **info)
    if scenes:
        info["scenes"] = scenes
    return json.loads(pyctures.start(textwrap.dedent(src), json.dumps(info)))


def tick(dt=0.1, **payload):
    payload["dt"] = dt
    return json.loads(pyctures.tick(json.dumps(payload)))


def key(name):
    return {"k": "input", "e": {"type": "keydown", "key": name}}


def page(reply, name=None):
    """What the page's scenes were sent in a reply: [name, *arguments] for each command."""
    return [[c[4]] + c[5] for c in reply["cmds"] if c[0] == "call" and c[3] == H_SCENES and name in (None, c[4])]


def log():
    return pyctures.S.ns["log"]


@pytest.fixture(autouse=True)
def stopped():
    yield
    pyctures.stop()


THREE = """
    log = []
    class One(Scene):
        length = 0.25
        def setup(self): log.append("One setup")
        def on_stop(self): log.append("One stop")
    class Two(Scene):
        length = 0.25
        def setup(self): log.append("Two setup")
    def three_setup(): log.append("three setup")
    scene("three", setup=three_setup, length=0.25)
"""


# ---------------------------------------------------------------- order

def test_scenes_play_in_the_order_written_and_the_last_is_followed_by_the_first():
    r = start(THREE)
    assert r["error"] is None and r["running"]
    for i in range(9):
        tick(0.125)
    assert log() == ["One setup", "One stop", "Two setup", "three setup", "One setup", "One stop", "Two setup"]


def test_with_loop_off_the_last_scene_stays():
    start("config(loop=False)\n" + textwrap.dedent(THREE))
    for i in range(20):
        r = tick(0.1)
    assert log() == ["One setup", "One stop", "Two setup", "three setup"]
    assert pyctures.S.ns["scene_name"] == "three" and pyctures.S.ns["scene_progress"] == 1.0 and r["running"]


def test_a_sequence_keeps_time_however_the_frames_fall():
    # What a frame ran over belongs to the next scene: three scenes of 0.25 s are over at 0.75 s, not at the fourth 0.1 s frame of each.
    start(THREE)
    names = []
    for i in range(8):
        tick(0.1)
        names.append(pyctures.S.ns["scene_name"])
    # (Each beginning afresh on the frame after its time was up, they would be over at 0.9 s.)
    assert names[2] == "Two" and names[7] == "One", names


# ---------------------------------------------------------------- each starts empty

def test_each_scene_starts_empty_and_is_given_only_its_own_calls():
    r = start("""
        log = []
        shared = {"n": 0}
        class A(Scene):
            def setup(self):
                self.n = 0
            def update(self, dt):
                self.n += 1
                shared["n"] += 1
                log.append(("A", self.n, shared["n"]))
            def on_key_down(self, key):
                log.append(("A key", key))
                next_scene()
        class B(Scene):
            def update(self, dt):
                log.append(("B", hasattr(self, "n"), shared["n"]))
            def on_key_down(self, key, code):
                log.append(("B key", key))
                go(A)
        def on_key_down(key):
            log.append(("file key", key))
    """)
    assert page(r) [:2] == [["transition", "cut", 0, ""], ["empty"]]
    tick()
    r = tick(events=[key("x")])
    assert page(r, "empty") == [["empty"]]
    tick()
    tick(events=[key("y")])
    assert log() == [("A", 1, 1), ("A", 2, 2), ("file key", "x"), ("A key", "x"), ("B", False, 2), ("B", False, 2), ("file key", "y"), ("B key", "y"),
                     ("A", 1, 3)]


def test_the_drawing_settings_python_remembers_are_forgotten_with_the_scene():
    start("""
        class A(Scene):
            def draw(self):
                ctx.fill_style = "red"
            def on_key_down(self, key):
                next_scene()
        class B(Scene):
            def draw(self):
                js.console.log(ctx.fill_style)
    """)
    r = tick(events=[key("x")])
    # Not the "red" Python had remembered: the page put the settings back, so the value is asked of the page.
    assert ["call"] == [c[0] for c in r["cmds"] if c[0] == "call" and c[4] == "log"]
    assert "red" not in json.dumps(r["cmds"])


# ---------------------------------------------------------------- go, next_scene, restart, keep

GAME = """
    log = []
    score = 0
    class Menu(Scene):
        def setup(self):
            self.picks = 0
            log.append("Menu setup")
        def resume(self):
            log.append("Menu resume %d" % self.picks)
        def on_key_down(self, key):
            global score
            self.picks += 1
            score += 10
            if key == "g": go(Game)
            elif key == "n": next_scene()
            elif key == "r": restart()
            elif key == "x": go("nowhere")
    class Game(Scene):
        def setup(self):
            log.append("Game setup %d" % score)
        def on_key_down(self, key):
            if key == "k": go("menu", keep=True)
            elif key == "m": go("Menu")
"""


def test_go_next_scene_restart_and_keep():
    start(GAME)
    for press in "gknmrg":
        tick(events=[key(press)])
        tick()
    assert log() == ["Menu setup", "Game setup 10", "Menu resume 1", "Game setup 20", "Menu setup", "Menu setup", "Game setup 40"]
    assert pyctures.S.ns["scene_name"] == "Game"


def test_a_mistake_names_the_scene_and_its_line():
    start(GAME)
    r = tick(events=[key("x")])
    assert r["errorLine"] == 17
    assert r["error"].splitlines()[-1] == 'In the scene Menu: LookupError: go("nowhere"): there is no scene called "nowhere". The scenes are: Menu, Game'
    start("""
        class A(Scene):
            def draw(self):
                nothing_here()
    """)
    r = start("""
        class A(Scene):
            transition = "swirl"
        class B(Scene):
            transition = "swirl"
            def setup(self):
                pass
        go("B")
    """)
    assert r["error"].splitlines()[-1].startswith('ValueError: There is no transition "swirl". The transitions are: cut, crossfade, fade, wipe, ')


def test_a_mistake_in_a_scenes_draw_names_the_scene():
    r = start("""
        class Broken(Scene):
            def draw(self):
                nothing_here()
    """)
    assert r["errorLine"] == 4 and r["error"].splitlines()[-1] == "In the scene Broken: NameError: name 'nothing_here' is not defined"


def test_scene_options_that_do_not_exist_say_so():
    r = start('class A(Scene):\n    pass\ngo("A", fade=True)\n')
    assert 'go("A") has no option "fade". It takes transition, transition_time, transition_color and keep' in r["error"]
    r = start("config(speed=2)\nclass A(Scene):\n    pass\n")
    assert 'config() has no setting "speed". It has: loop, transition, transition_time, transition_color, beats_per_bar' in r["error"]


# ---------------------------------------------------------------- lengths

def test_scene_time_and_progress_run_through_a_length():
    start("""
        seen = []
        class A(Scene):
            length = 2
            def update(self, dt):
                seen.append((scene_name, round(scene_time, 2), round(scene_progress, 2)))
        class B(Scene):
            def update(self, dt):
                seen.append((scene_name, round(scene_time, 2), scene_progress))
    """)
    for i in range(5):
        tick(0.5)
    assert pyctures.S.ns["seen"] == [("A", 0, 0), ("A", 0.5, 0.25), ("A", 1.0, 0.5), ("A", 1.5, 0.75), ("B", 0.0, 0.0), ("B", 0.5, 0.0)]


def test_beats_and_bars_end_a_scene_on_the_sound_librarys_beat(monkeypatch):
    # The sound library's clock, held by the test: 120 beats a minute, so a beat is half a second.
    fake = types.ModuleType("synths")
    fake.now = 100.0
    fake.beat = lambda: (fake.now - 100.0) * 2
    fake.beats = lambda n=1: n * 0.5
    monkeypatch.setitem(sys.modules, "synths", fake)
    r = start("""
        import synths
        log = []
        class A(Scene):
            beats = 4
            def setup(self): log.append("A")
        class B(Scene):
            bars = 2
            def setup(self): log.append("B")
        class C(Scene):
            def setup(self): log.append("C")
    """)
    [shown] = page(r, "show")
    assert [(s["name"], s["t"]) for s in shown[1]] == [("A", 0.0), ("B", 2.0), ("C", 6.0)] and shown[2] == 0.0
    seen = []
    for now in (101.9, 102.05, 105.9, 106.1):
        fake.now = now
        tick(1 / 60)        # however short the frames are, it is the beat that ends the scene
        seen.append(("".join(log()), round(pyctures.S.ns["scene_time"], 2), round(pyctures.S.ns["scene_progress"], 3)))
    assert seen == [("A", 1.9, 0.95), ("AB", 0.05, 0.012), ("AB", 3.9, 0.975), ("ABC", 0.1, 0.0)]


# ---------------------------------------------------------------- transitions: what the page is told

def test_python_only_says_which_transition_and_the_page_runs_it():
    r = start("""
        config(transition="wipe", transition_time=2)
        drawn = []
        class A(Scene):
            def draw(self): drawn.append("A")
            def on_key_down(self, key):
                if key == "g": go("D", transition="slide_left", transition_time=0.25)
                else: next_scene()
        class B(Scene):
            transition = "none"
            def draw(self): drawn.append("B")
            def on_key_down(self, key): next_scene()
        class C(Scene):
            transition = "fade"
            transition_time = 1.5
            transition_colour = "white"
            def on_key_down(self, key): next_scene()
        class D(Scene):
            def on_key_down(self, key): go("A", transition="slide")
    """)
    assert page(r, "transition") == [["transition", "cut", 0, ""]]       # the first scene arrives with none
    sent = []
    for press in "nnnng":
        sent += page(tick(events=[key(press)]), "transition")
        tick()
    assert sent == [["transition", "cut", 0, ""], ["transition", "fade", 1.5, "white"], ["transition", "wipe", 2.0, "black"],
                    ["transition", "slide_left", 2.0, "black"], ["transition", "slide_left", 0.25, "black"]]
    # The old scene is drawn once more before a transition (a 3D picture is gone from its canvas once shown), and never again.
    drawn = pyctures.S.ns["drawn"]
    assert drawn.count("B") >= 2 and drawn[-1] == "A"


def test_the_transition_is_the_first_thing_in_the_new_scenes_batch():
    start("""
        class A(Scene):
            def draw(self): background("red")
            def on_key_down(self, key): go("B", transition="crossfade")
        class B(Scene):
            def draw(self): background("blue")
    """)
    r = tick(events=[key("x")])
    calls = [(c[3], c[4], c[5][:1]) for c in r["cmds"] if c[0] == "call"]
    # The old picture, drawn once more; then the page keeps it; then the canvas is emptied and the new scene draws.
    assert calls == [(7, "background", ["red"]), (H_SCENES, "transition", ["crossfade"]), (H_SCENES, "empty", []), (H_SCENES, "show", [[
        {"name": "A", "t": 0.0, "length": None, "scene": True}]]), (7, "background", ["blue"])]


def test_a_page_with_no_scenes_of_its_own_is_sent_nothing_and_every_change_is_a_cut():
    r = start(THREE, scenes=False)
    sent = list(r["cmds"])
    for i in range(6):
        sent += tick(0.1)["cmds"]
    assert not [c for c in sent if len(c) > 3 and c[3] == H_SCENES]
    assert log()[:4] == ["One setup", "One stop", "Two setup", "three setup"]


def test_a_page_can_add_transitions_by_name():
    r = start('class A(Scene):\n    pass\nclass B(Scene):\n    transition = "dissolve"\nnext_scene()\n', scenes={"transitions": ["dissolve"]})
    assert r["error"] is None
    assert page(r, "transition") == [["transition", "cut", 0, ""], ["transition", "dissolve", 0.5, "black"]]


# ---------------------------------------------------------------- the scrubber

TIMED = """
    log = []
    class Intro(Scene):
        length = 2
        def setup(self): log.append("Intro %.1f" % scene_time)
    class Main(Scene):
        length = 6
        def setup(self):
            log.append("Main %.1f" % scene_time)
            section("Chorus")
        def update(self, dt): log.append("update")
    class Outro(Scene):
        length = 2
        def setup(self): log.append("Outro %.1f" % scene_time)
    def on_seek(t): log.append("seek %.1f" % t)
"""


def test_sections_are_reported_and_the_scrubber_seeks_and_pauses():
    r = start(TIMED)
    [shown] = page(r, "show")
    assert shown[1:] == [[{"name": "Intro", "t": 0.0, "length": 2, "scene": True}, {"name": "Main", "t": 2.0, "length": 6, "scene": True},
                          {"name": "Outro", "t": 8.0, "length": 2, "scene": True}], 10.0, 0.0, "Intro", False]
    r = tick(0.1, events=[{"k": "scene", "e": {"seek": 5}}])
    shows = page(r, "show")
    assert shows[-1][3:] == [5.0, "Main", False] and [s["name"] for s in shows[-1][1]] == ["Intro", "Main", "Chorus", "Outro"]
    assert log()[:3] == ["Intro 0.0", "Main 3.0", "seek 5.0"]
    # Once a second the page is told the time again; in between its own clock moves the knob.
    told = sum(len(page(tick(0.1), "show")) for i in range(25))
    assert told == 2
    before = pyctures.S.ns["scene_time"]
    updates = log().count("update")
    tick(0.1, events=[{"k": "scene", "e": {"pause": True}}])
    tick(0.1)
    assert pyctures.S.ns["scene_time"] == before and log().count("update") == updates
    tick(0.1, events=[{"k": "scene", "e": {"pause": False}}])
    assert pyctures.S.ns["scene_time"] > before


# ---------------------------------------------------------------- a file with no scenes

def test_a_file_with_no_scenes_is_one_scene_as_before():
    r = start("""
        n = 0
        def restart():
            global n
            n = 0
        def update(dt):
            global n
            n += 1
        def draw():
            ctx.fill_rect(0, 0, n, n)
    """)
    assert pyctures.S.stage is None and "scene_time" not in pyctures.S.ns
    r = tick()
    assert [c[:1] + c[2:] for c in r["cmds"]] == [["call", 0, 4, "fill_rect", [0, 0, 2, 2]]]
    assert callable(pyctures.S.ns["restart"]) and pyctures.S.ns["restart"].__module__ != "pyctures"
    # A program that finishes still finishes: nothing here keeps it running.
    assert start("ctx.fill_rect(0, 0, 1, 1)")["running"] is False


# ---------------------------------------------------------------- what a file with no scenes costs

def test_scenes_are_a_library_that_only_a_file_naming_a_scene_is_given(tmp_path):
    from pyctures import build, pages
    assert not pages.uses_library("world = THREE.Scene()\nship.go(3)\ndef draw():\n    pass\n", "pyscenes")
    for names in ("class Title(Scene):\n    pass\n", 'scene("title", draw=d)\n', 'go("game")\n', "next_scene()\n"):
        assert pages.uses_library(names, "pyscenes") and pyctures._USES_SCENES.search(names)
    # The page asks the same question with the same words.
    page_words = (pages.WEB / "pyctures.js").read_text(encoding="utf-8")
    assert "uses: /%s/m" % pages.USES_SCENES.pattern in page_words
    plain = tmp_path / "plain.py"
    plain.write_text("def draw():\n    background('black')\n")
    staged = tmp_path / "staged.py"
    staged.write_text("class A(Scene):\n    def draw(self):\n        background('black')\n")
    build.build(plain, tmp_path / "plain.html", say=lambda *a: None)
    build.build(staged, tmp_path / "staged.html", say=lambda *a: None)
    without, with_scenes = (tmp_path / "plain.html").read_text(), (tmp_path / "staged.html").read_text()
    library = sum(len(pages.ASSETS[a].read_text(encoding="utf-8")) for a in ("scenes/scenes.js", "scenes/pyscenes.py"))
    assert "scenesKeeper(container" not in without and "class _Stage" not in without and "pyctures-bar" not in without
    assert "scenesKeeper(container" in with_scenes and "class _Stage" in with_scenes
    # A page with no scenes is the size it was: all of scenes but the few lines that ask for it is in the library.
    assert len(with_scenes) - len(without) > library and len(without) < 195_000
    start("def draw():\n    ctx.fill_rect(0, 0, 1, 1)\n")
    assert pyctures.S.scenes is None and "Scene" not in pyctures.S.ns


# ================================================================ in a browser

sync_api = pytest.importorskip("playwright.sync_api")
from test_browser import Watched  # noqa: E402

SCENE = "document.querySelector('[data-pyctures-src]').pycturesScene"
RED, BLUE, WHITE = [255, 0, 0], [0, 0, 255], [255, 255, 255]


def pixels(png):
    """The pixels of a screenshot: at(x, y) is [r, g, b]. (8-bit RGB or RGBA, not interlaced: what a browser writes.)"""
    at, packed, width, channels = 8, b"", 0, 0
    while at < len(png):
        n, kind = int.from_bytes(png[at:at + 4], "big"), png[at + 4:at + 8]
        body = png[at + 8:at + 8 + n]
        if kind == b"IHDR":
            width, channels = int.from_bytes(body[:4], "big"), {2: 3, 6: 4}[body[9]]
        elif kind == b"IDAT":
            packed += body
        at += 12 + n
    raw, row, out = zlib.decompress(packed), width * channels, bytearray()
    for y in range(len(raw) // (row + 1)):
        kind, line = raw[y * (row + 1)], raw[y * (row + 1) + 1:(y + 1) * (row + 1)]
        for i, v in enumerate(line):
            a = out[-channels] if i >= channels else 0
            b = out[-row] if y else 0
            c = out[-row - channels] if y and i >= channels else 0
            if kind == 1: v += a
            elif kind == 2: v += b
            elif kind == 3: v += (a + b) >> 1
            elif kind == 4:
                p = a + b - c
                v += a if abs(p - a) <= abs(p - b) and abs(p - a) <= abs(p - c) else b if abs(p - b) <= abs(p - c) else c
            out.append(v & 255)
    return lambda x, y: list(out[(y * width + x) * channels:(y * width + x) * channels + 3])


def near(a, b, by=4):
    return all(abs(x - y) <= by for x, y in zip(a, b))


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        yield b
        b.close()


# Two plain pictures to change between: red with a white stripe at 240 to 260, then blue. The page is 300 by 200.
PAIR = '''
class Red(Scene):
    def draw(self):
        background("rgb(255,0,0)")
        rect(240, 0, 20, 200, "rgb(255,255,255)")
    def on_key_down(self, key):
        go("Blue", %s)

class Blue(Scene):
    def draw(self):
        background("rgb(0,0,255)")
'''


def run(browser, pyctures_run, tmp_path, source, name="scenes.py"):
    file = tmp_path / name
    file.write_text(source)
    w = Watched(browser, pyctures_run(file).url, size=(300, 200))
    w.wait_running()
    return w


def change(browser, pyctures_run, tmp_path, how):
    """Run the pair, press a key, and take the screen with the transition held at 0, a quarter, half and the end."""
    w = run(browser, pyctures_run, tmp_path, PAIR % how)
    w.page.wait_for_function(SCENE + ".stage.name === 'Red'")
    w.page.keyboard.press("a")
    w.page.wait_for_function(SCENE + ".stage.running && " + SCENE + ".stage.name === 'Blue'")
    seen = {}
    for p in (0, 0.25, 0.5, 1):
        w.page.evaluate("(p) => %s.stage.running.hold(p)" % SCENE, p)
        w.page.wait_for_timeout(120)
        seen[p] = pixels(w.page.screenshot(clip={"x": 0, "y": 0, "width": 300, "height": 200}))
    assert not w.errors, w.errors
    w.page.close()
    return seen


def test_a_crossfade_is_the_average_of_the_two_scenes_half_way(browser, pyctures_run, tmp_path):
    seen = change(browser, pyctures_run, tmp_path, 'transition="crossfade", transition_time=60')
    assert near(seen[0](100, 100), RED, 1) and near(seen[0](250, 100), WHITE, 1)
    assert near(seen[0.5](100, 100), [128, 0, 128]) and near(seen[0.5](250, 100), [128, 128, 255])
    assert near(seen[1](100, 100), BLUE, 1) and near(seen[1](250, 100), BLUE, 1)


def test_a_wipes_edge_is_where_it_should_be(browser, pyctures_run, tmp_path):
    seen = change(browser, pyctures_run, tmp_path, 'transition="wipe", transition_time=60')
    assert [seen[0](5, 100), seen[0.25](73, 100), seen[0.25](77, 100), seen[0.5](148, 100), seen[0.5](152, 100), seen[0.5](250, 100), seen[1](295, 100)] == \
        [RED, BLUE, RED, BLUE, RED, WHITE, BLUE]


def test_a_slide_moves_both_scenes_and_a_fade_goes_through_its_colour(browser, pyctures_run, tmp_path):
    seen = change(browser, pyctures_run, tmp_path, 'transition="slide_left", transition_time=60')
    assert [seen[0](250, 100), seen[0.5](100, 100), seen[0.5](50, 100), seen[0.5](148, 100), seen[0.5](152, 100), seen[1](5, 100)] == \
        [WHITE, WHITE, RED, RED, BLUE, BLUE]
    seen = change(browser, pyctures_run, tmp_path, 'transition="fade", transition_time=60, transition_color="rgb(0,255,0)"')
    assert near(seen[0](100, 100), RED, 1) and near(seen[0.25](100, 100), [128, 128, 0]) and near(seen[0.5](100, 100), [0, 255, 0], 1) and near(seen[1](100, 100), BLUE, 1)


def test_a_recording_has_the_transition_and_a_page_with_no_scenes_asks_for_nothing_more(browser, pyctures_run, tmp_path):
    # What a recorder does: every canvas of the scene drawn one over another. No canvas has a style to miss.
    recorded = """() => {
      const out = document.createElement('canvas'); out.width = 300; out.height = 200
      const g = out.getContext('2d'), styled = []
      for (const c of document.querySelectorAll('[data-pyctures-src] canvas')) {
        g.drawImage(c, 0, 0, 300, 200)
        styled.push([c.style.opacity, c.style.clipPath, c.style.transform].join(''))
      }
      const at = (x, y) => [...g.getImageData(x, y, 1, 1).data].slice(0, 3)
      return [styled.join(''), at(100, 100), at(250, 100), at(50, 100), at(152, 100)]
    }"""
    got = {}
    for kind in ("crossfade", "slide_left"):
        w = run(browser, pyctures_run, tmp_path, PAIR % ('transition="%s", transition_time=60' % kind))
        asked = []
        w.page.on("request", lambda r: asked.append(r.url.split("/")[-1]))
        w.page.wait_for_function(SCENE + ".stage.name === 'Red'")
        w.page.keyboard.press("a")
        w.page.wait_for_function(SCENE + ".stage.running && " + SCENE + ".stage.name === 'Blue'")
        w.page.evaluate("%s.stage.running.hold(0.5)" % SCENE)
        w.page.wait_for_timeout(150)
        got[kind] = w.page.evaluate(recorded)
        w.page.close()
    styled, a, b, c, d = got["crossfade"]
    assert styled == "" and near(a, [128, 0, 128]) and near(b, [128, 128, 255])
    styled, a, b, c, d = got["slide_left"]
    assert styled == "" and [a, c, d] == [WHITE, RED, BLUE]
    # A file with no scenes is not given the library, by the page or by Python.
    asked = []
    file = tmp_path / "plain.py"
    file.write_text("def draw():\n    background('black')\n")
    page = browser.new_page()
    page.on("request", lambda r: asked.append(r.url.split("/")[-1]))
    page.goto(pyctures_run(file).url)
    page.wait_for_function("document.querySelector('[data-pyctures-status=running]')")
    assert page.evaluate(SCENE + ".stage") is None and "pyctures.js" in asked and "scenes.js" not in asked
    page.close()


def test_a_3d_files_scenes_change_with_the_same_transitions(browser, pyctures_run, tmp_path):
    w = run(browser, pyctures_run, tmp_path, '''
renderer = THREE.WebGLRenderer(canvas=canvas)
camera = THREE.PerspectiveCamera()

class Red(Scene):
    def setup(self):
        self.world = THREE.Scene()
        self.world.background = THREE.Color("rgb(255,0,0)")
    def draw(self):
        renderer.render(self.world, camera)
    def on_key_down(self, key):
        go("Blue", transition="crossfade", transition_time=60)

class Blue(Scene):
    def setup(self):
        self.world = THREE.Scene()
        self.world.background = THREE.Color("rgb(0,0,255)")
    def draw(self):
        renderer.render(self.world, camera)
''')
    w.page.wait_for_timeout(500)
    w.page.keyboard.press("a")
    w.page.wait_for_function(SCENE + ".stage.running && " + SCENE + ".stage.name === 'Blue'")
    seen = []
    for p in (0, 0.5, 1):
        w.page.evaluate("(p) => %s.stage.running.hold(p)" % SCENE, p)
        w.page.wait_for_timeout(150)
        seen.append(pixels(w.page.screenshot(clip={"x": 0, "y": 0, "width": 300, "height": 200}))(100, 100))
    assert near(seen[0], RED) and near(seen[1], [128, 0, 128], 6) and near(seen[2], BLUE), seen
    assert not w.errors, w.errors
    w.page.close()


def test_a_transition_stays_smooth_while_python_makes_two_frames_a_second(browser, pyctures_run, tmp_path):
    w = run(browser, pyctures_run, tmp_path, '''
import time

class Red(Scene):
    def draw(self):
        background("rgb(255,0,0)")
    def on_key_down(self, key):
        go("Blue", transition="crossfade", transition_time=1.5)

class Blue(Scene):
    def draw(self):
        time.sleep(0.5)             # Python throttled to two frames a second
        background("rgb(0,0,255)")
''')
    w.page.wait_for_function(SCENE + ".stage.name === 'Red'")
    w.page.keyboard.press("a")
    w.page.wait_for_function(SCENE + ".stage.running")
    got = w.page.evaluate("""() => new Promise((done) => {
      const s = %s, steps = [], from = s.r.shown
      const look = () => {
        const run = s.stage.running
        if (!run) return done({ steps, frames: s.r.shown - from, layers: document.querySelectorAll('[data-pyctures-transition]').length })
        steps.push(run.progress)
        requestAnimationFrame(look)
      }
      look()
    })""" % SCENE)
    steps = got["steps"]
    jumps = [b - a for a, b in zip(steps, steps[1:])]
    # The page moved the transition on at every refresh (about 90 of them in 1.5 s), though Python sent only a few frames in that time.
    assert len(steps) > 45 and max(jumps) < 0.08 and min(jumps) >= 0, (len(steps), max(jumps))
    assert got["frames"] <= 5 and got["layers"] == 0, got
    assert not w.errors, w.errors
    w.page.close()


def test_a_scenes_own_controls_and_picture_go_when_it_ends(browser, pyctures_run, tmp_path):
    w = run(browser, pyctures_run, tmp_path, '''
import pydials
from pydials import *

shared = dial("shared", 0, 1)
seen = []

class A(Scene):
    def setup(self):
        seen.append(["A", len(pydials._run.items)])
        self.mine = dial("mine", 0, 1)
        self.more = slider("more", 0, 1)
    def draw(self):
        background("red")
        ctx.fill_style = "lime"
    def update(self, dt):
        if scene_time > 0.3: next_scene()

class B(Scene):
    def setup(self):
        seen.append(["B", len(pydials._run.items)])
        js.pySeen = seen
    def update(self, dt):
        if scene_time > 0.3: next_scene()
''')
    w.page.wait_for_function("window.pySeen && window.pySeen.length >= 3")
    assert w.page.evaluate("window.pySeen.slice(0, 3)") == [["A", 1], ["B", 1], ["A", 1]]
    # B draws nothing: the canvas it was given is clear, with the drawing settings as they start.
    w.page.wait_for_function(SCENE + ".stage.name === 'B'")
    w.page.wait_for_timeout(100)
    got = w.page.evaluate("""() => { const c = %s.canvas, g = c.getContext('2d'); return [g.getImageData(c.width - 5, c.height - 5, 1, 1).data[3], g.fillStyle] }""" % SCENE)
    assert got == [0, "#000000"] or w.page.evaluate(SCENE + ".stage.name") != "B"
    assert not w.errors, w.errors
    w.page.close()


def test_the_scrubber_has_a_tick_for_each_scene_and_goes_where_it_is_pressed(browser, pyctures_run, tmp_path):
    w = run(browser, pyctures_run, tmp_path, '''
class Intro(Scene):
    length = 2
    def draw(self): background("red")

class Main(Scene):
    length = 6
    def draw(self): background("blue")

class Outro(Scene):
    length = 2
    def draw(self): background("green")
''')
    page = w.page
    page.wait_for_selector(".pyctures-bar", state="attached")
    assert page.evaluate("[...document.querySelectorAll('.pyctures-ticks i')].map((i) => [i.title, i.style.left])") == [["Main", "20%"], ["Outro", "80%"]]
    assert page.evaluate("document.querySelector('.pyctures-time').textContent") == "0:00 / 0:10"
    box = page.evaluate("(() => { const b = document.querySelector('.pyctures-track').getBoundingClientRect(); return [b.left, b.top + b.height / 2, b.width] })()")
    page.mouse.move(box[0] + box[2] * 0.5, box[1])
    page.mouse.down()
    page.mouse.up()
    page.wait_for_function(SCENE + ".stage.name === 'Main'")
    page.wait_for_timeout(300)
    assert 5 <= page.evaluate(SCENE + ".stage.time") < 6
    assert page.evaluate("(() => { const c = %s.canvas; return [...c.getContext('2d').getImageData(5, 5, 1, 1).data].slice(0, 3) })()" % SCENE) == BLUE
    assert not w.errors, w.errors
    page.close()
