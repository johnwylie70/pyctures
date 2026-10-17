"""Every example in a real (headless) Chromium: `pyctures run`, and `pyctures build` with Pyodide.

Needs Playwright:  pip install playwright && playwright install chromium
Screenshots land in tests/screenshots/.
"""
import json
import math
import shutil
import time
import urllib.request

import pytest

from conftest import EXAMPLES, SHOTS

playwright = pytest.importorskip("playwright.sync_api")

SCENES = sorted(p.name for p in EXAMPLES.glob("*.py"))

# How many different colours a 64x64 copy of the canvas has.
COLOURS = """(el) => {
  const c = el.querySelector('canvas'); if (!c) return 0
  const t = document.createElement('canvas'); t.width = 64; t.height = 64
  const g = t.getContext('2d'); g.drawImage(c, 0, 0, 64, 64)
  const d = g.getImageData(0, 0, 64, 64).data, seen = new Set()
  for (let i = 0; i < d.length; i += 4) seen.add((d[i] << 16) | (d[i + 1] << 8) | d[i + 2])
  return seen.size
}"""

PIXEL = """(el, [fx, fy]) => {
  const c = el.querySelector('canvas')
  const t = document.createElement('canvas'); t.width = c.width; t.height = c.height
  const g = t.getContext('2d'); g.drawImage(c, 0, 0)
  return Array.from(g.getImageData(Math.floor(c.width * fx), Math.floor(c.height * fy), 1, 1).data.slice(0, 3))
}"""


def cdn_reachable():
    try:
        urllib.request.urlopen("https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.mjs", timeout=5)
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        # (A scene that asks for the microphone is never given this computer's: Chromium's pretend one stands in its place.)
        b = p.chromium.launch(args=["--mute-audio", "--use-fake-ui-for-media-stream", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--use-fake-device-for-media-stream"])
        yield b
        b.close()


class Watched:
    """A page, with its console errors collected."""

    def __init__(self, browser, url, size=(800, 600)):
        self.page = browser.new_page(viewport={"width": size[0], "height": size[1]})
        self.errors = []
        self.page.on("console", lambda m: self.errors.append(m.text) if m.type == "error" else None)
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.goto(url)

    def scenes(self):
        return self.page.query_selector_all("[data-pyctures-src]")

    def wait_running(self, count=1, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            states = [s.get_attribute("data-pyctures-status") for s in self.scenes()]
            # Running, and its first frame is on screen (Python may still be
            # loading while the status already says running).
            shown = [s.evaluate("(el) => !!(el.pycturesScene && el.pycturesScene.r.shown > 0)") for s in self.scenes()]
            if len(states) == count and all(s in ("finished", "error") or (s == "running" and f)
                                            for s, f in zip(states, shown)):
                return states
            self.page.wait_for_timeout(200)
        raise AssertionError("scenes did not start: %s" % states)

    def check(self, shot, count=1, min_colours=4):
        states = self.wait_running(count)
        self.page.wait_for_timeout(1500)
        for s in self.scenes():
            err = s.get_attribute("data-pyctures-error")
            assert err is None, err
        assert "error" not in states, states
        assert not self.errors, self.errors
        for s in self.scenes():
            colours = s.evaluate(COLOURS)
            assert colours >= min_colours, "canvas looks blank (%d colours)" % colours
        SHOTS.mkdir(exist_ok=True)
        self.page.screenshot(path=str(SHOTS / shot), full_page=True)


@pytest.mark.parametrize("scene", SCENES)
def test_run_each_example(browser, pyctures_run, scene):
    p = pyctures_run(EXAMPLES / scene)
    w = Watched(browser, p.url)
    # The three smallest scenes are one circle on one colour: two colours is a whole picture there.
    plain = scene in ("hello.py", "moving.py", "follow.py")
    w.check("run-" + scene.replace(".py", ".png"), min_colours=2 if plain else 4)
    w.page.close()


def test_run_keyboard_reaches_python(browser, pyctures_run):
    p = pyctures_run(EXAMPLES / "type_and_measure.py")
    w = Watched(browser, p.url)
    w.check("run-type_and_measure-before.png")
    scene = w.scenes()[0]
    before = scene.evaluate("(el) => el.querySelector('canvas').toDataURL()")
    w.page.keyboard.type("Hello")
    w.page.wait_for_timeout(800)
    after = scene.evaluate("(el) => el.querySelector('canvas').toDataURL()")
    assert before != after
    w.page.screenshot(path=str(SHOTS / "run-type_and_measure-after.png"))


def test_run_website_page_with_two_scenes(browser, pyctures_run):
    p = pyctures_run(EXAMPLES / "website")
    w = Watched(browser, p.url, size=(900, 800))
    # The second scene is below the fold: it waits until it is scrolled to.
    w.page.wait_for_timeout(3000)
    states = [s.get_attribute("data-pyctures-status") for s in w.scenes()]
    assert states[0] == "running" and states[1] is None, states
    w.page.mouse.wheel(0, 3000)
    w.check("run-website.png", count=2)


def test_run_error_page_shows_the_line(browser, pyctures_run, tmp_path):
    scene = tmp_path / "broken.py"
    scene.write_text("x = 1\n\ndef draw():\n    ctx.fill_rect(0, 0, undefined_name, 1)\n")
    p = pyctures_run(scene)
    w = Watched(browser, p.url)
    w.page.wait_for_selector(".pyctures-error", timeout=20000)
    text = w.page.inner_text(".pyctures-error")
    assert "Error on line 4 of broken.py" in text
    assert "NameError" in text and "undefined_name" in text
    assert w.scenes()[0].get_attribute("data-pyctures-error").startswith("line 4")
    w.page.screenshot(path=str(SHOTS / "run-error.png"))


@pytest.mark.parametrize("what, source, line, says", [
    ("a stray sign", "x = 1\ny = 2\nz = = 3\n", 3, "SyntaxError"),
    ("a bracket never closed", "x = 1\ndef draw():\n    circle(1, 2, 3, 'gold'\n\ny = 2\n", 3, "'(' was never closed"),
    ("a line not indented", "x = 1\ndef draw():\ncircle(1, 2, 3)\n", 3, "IndentationError"),
    ("running, at the top", "x = 1\ny = 2\nnot_there(3)\n", 3, "not_there"),
    ("running, inside update", "x = 1\n\ndef update(dt):\n    x.move()\n", 4, "move"),
    ("running, after await frame()", "x = 1\nasync def go():\n    await frame()\n    await frame()\n    not_there(3)\nawait go()\n", 5, "not_there"),
])
def test_run_error_names_the_line(browser, pyctures_run, tmp_path, what, source, line, says):
    """A mistake in how the file is written, or one made while it runs, names its line."""
    scene = tmp_path / "broken.py"
    scene.write_text(source)
    p = pyctures_run(scene)
    w = Watched(browser, p.url)
    w.page.wait_for_selector(".pyctures-error", timeout=20000)
    text = w.page.inner_text(".pyctures-error")
    assert f"Error on line {line} of broken.py" in text, what
    assert says in text, what


def test_run_saving_reruns_the_page(browser, pyctures_run, tmp_path):
    scene = tmp_path / "colour.py"
    scene.write_text('def draw():\n    ctx.fill_style = "rgb(255, 0, 0)"\n    ctx.fill_rect(0, 0, width, height)\n')
    p = pyctures_run(scene)
    w = Watched(browser, p.url)
    w.wait_running()
    w.page.wait_for_timeout(800)
    el = w.scenes()[0]
    assert el.evaluate(PIXEL, [0.5, 0.5]) == [255, 0, 0]
    scene.write_text('def draw():\n    ctx.fill_style = "rgb(0, 0, 255)"\n    ctx.fill_rect(0, 0, width, height)\n')
    end = time.time() + 10
    colour = None
    while time.time() < end:
        try:
            el = w.scenes()[0]
            colour = el.evaluate(PIXEL, [0.5, 0.5])
            if colour == [0, 0, 255]:
                break
        except Exception:
            pass   # the page is reloading
        w.page.wait_for_timeout(300)
    assert colour == [0, 0, 255]


def test_renderer_replays_commands(browser, pyctures_run):
    """The browser half on its own: snake_case, expressions, reads and errors."""
    p = pyctures_run(EXAMPLES / "type_and_measure.py")
    w = Watched(browser, p.url)
    result = w.page.evaluate("""async () => {
      const m = await import('/pyctures/pyctures.js')
      const box = document.createElement('div')
      box.style.cssText = 'position:fixed;left:0;top:0;width:100px;height:100px'
      const canvas = document.createElement('canvas')
      canvas.style.cssText = 'width:100%;height:100%;display:block'
      box.appendChild(canvas); document.body.appendChild(box)
      let applied = null
      const r = m.createRenderer(canvas, { hooks: {
        onEvent() {}, onSize() {}, isActive: () => false, onApplied(d) { applied = d } } })
      r.push([
        ['set', 1, 4, 'fill_style', 'rgb(0, 255, 0)'],
        ['call', 2, 0, 4, 'fill_rect', [0, 0, 50, 50]],
        ['get', 3, 1100, 1, 'document'],
        ['call', 4, 1101, 1100, 'create_element', ['span']],
        ['set', 5, 1101, 'title', {$e: ['+', ['v', 2], ['*', ['v', 3], ['v', 4]]]}],
        ['read', 6, 1, {$e: ['get', ['ref', {$h: 1101}], 'title']}],
        ['read', 7, 2, {$e: ['get', ['ref', {$h: 2}], 'tagName']}],
        ['call', 8, 0, 4, 'no_such_thing', []],
        ['free', 0, 1101],
        ['read', 9, 3, {$h: 1101}],
      ])
      await new Promise((res) => { const t = () => applied ? res() : requestAnimationFrame(t); t() })
      const px = canvas.getContext('2d').getImageData(10, 10, 1, 1).data
      return { reads: applied.reads, errors: applied.errors, px: Array.from(px.slice(0, 3)) }
    }""")
    assert result["px"] == [0, 255, 0]
    assert result["reads"]["1"] == "14"
    assert result["reads"]["2"] == "CANVAS"
    assert result["reads"]["3"] is None
    lines = sorted(e["line"] for e in result["errors"])
    assert lines == [8, 9]
    assert 'ctx has no method "no_such_thing"' in result["errors"][0]["message"]


# ---------------------------------------------------------------- build (Pyodide)

needs_cdn = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")


@needs_cdn
@pytest.mark.parametrize("scene", ["star_catcher.py", "lit_scene.py"])
def test_build_runs_with_pyodide(browser, static_server, tmp_path, scene):
    from pyctures.build import build
    out = tmp_path / "site"
    build(EXAMPLES / scene, out, say=lambda *a: None)
    w = Watched(browser, static_server(out))
    w.check("build-" + scene.replace(".py", ".png"))


@needs_cdn
def test_build_website_with_two_scenes(browser, static_server, tmp_path):
    from pyctures.build import build
    out = tmp_path / "site"
    build(EXAMPLES / "website", out, say=lambda *a: None)
    w = Watched(browser, static_server(out), size=(900, 800))
    w.page.wait_for_timeout(1500)
    w.page.mouse.wheel(0, 3000)
    w.check("build-website.png", count=2)


@needs_cdn
def test_build_in_an_iframe(browser, static_server, tmp_path):
    """The iframe way of embedding: a built scene inside someone else's page."""
    from pyctures.build import build
    site = tmp_path / "www"
    build(EXAMPLES / "bouncing_balls.py", site / "balls", say=lambda *a: None)
    (site / "index.html").write_text(
        '<!doctype html><title>Host page</title><h1>My page</h1>'
        '<iframe src="balls/index.html" style="width:600px;height:400px;border:0"></iframe>')
    w = Watched(browser, static_server(site))
    frame = w.page.frame_locator("iframe")
    end = time.time() + 60
    while time.time() < end:
        status = frame.locator("[data-pyctures-src]").get_attribute("data-pyctures-status")
        drawn = frame.locator("[data-pyctures-src]").evaluate("(el) => !!(el.pycturesScene && el.pycturesScene.r.shown > 0)")
        if status == "running" and drawn:
            break
        w.page.wait_for_timeout(300)
    assert status == "running"
    w.page.wait_for_timeout(1000)
    colours = frame.locator("[data-pyctures-src]").evaluate(COLOURS)
    assert colours >= 4
    assert not w.errors, w.errors
    w.page.screenshot(path=str(SHOTS / "build-iframe.png"))


# ---------------------------------------------------------------- input: touches, mouse, wheel, pinch, keys

INPUT_PROBE = '''
import json
log = []
frames = []
def r(v): return round(v, 2)
def on_key_down(key, code): log.append(["kd", key, code])
def on_key_up(key): log.append(["ku", key])
def on_mouse_down(x, y, button): log.append(["md", r(x), r(y), button])
def on_mouse_up(x, y, button): log.append(["mu", r(x), r(y), button])
def on_touch_start(t): log.append(["ts", r(t.x), r(t.y), t.type])
def on_touch_end(t, cancelled): log.append(["te", r(t.x), r(t.y), cancelled])
def on_wheel(amount): log.append(["wheel", amount])
def on_pinch(scale, change): log.append(["pinch", r(scale)])
def update(dt):
    if mouse.dx or mouse.wheel or pressed or released or pinch.change != 1 or any(t.dx or t.dy for t in touches):
        frames.append({"dx": r(mouse.dx), "wheel": mouse.wheel, "pressed": sorted(pressed), "released": sorted(released),
                       "change": r(pinch.change), "t": [[r(t.dx), r(t.dy)] for t in touches]})
def draw():
    ctx.fill_style = "#234"
    ctx.fill_rect(0, 0, width, height)
    js.window.probe = json.dumps({
        "keys": sorted(keys), "codes": sorted(keys.codes), "mods": [keys.shift, keys.ctrl, keys.alt, keys.meta],
        "mouse": [r(mouse.x), r(mouse.y), mouse.down, mouse.button, mouse.inside],
        "touches": [[r(t.x), r(t.y), r(t.start_x), r(t.start_y), t.type] for t in touches],
        "scale": r(pinch.scale), "log": log, "frames": frames})
'''


class Driven:
    """A scene in a touch screen's page, with real input sent to it."""

    def __init__(self, browser, url, size=(800, 600)):
        self.context = browser.new_context(viewport={"width": size[0], "height": size[1]}, has_touch=True)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.goto(url)
        self.cdp = self.context.new_cdp_session(self.page)
        end = time.time() + 90
        while time.time() < end and not self.page.evaluate("typeof window.probe === 'string'"):
            self.page.wait_for_timeout(200)
        self.page.wait_for_timeout(300)

    def probe(self):
        # A few frames on, so what was just sent has been through Python and back.
        self.page.wait_for_timeout(350)
        return json.loads(self.page.evaluate("window.probe"))

    def touch(self, kind, *points):
        self.cdp.send("Input.dispatchTouchEvent", {
            "type": kind, "touchPoints": [{"id": i, "x": x, "y": y} for i, x, y in points]})


def _drive_input(d):
    page = d.page
    # mouse: movement, each button
    page.mouse.move(100, 50)
    page.mouse.move(130, 50)
    p = d.probe()
    assert p["mouse"] == [130, 50, False, None, True]
    assert sum(f["dx"] for f in p["frames"]) == 30   # the first place is not a movement
    for button in ("left", "middle", "right"):
        page.mouse.down(button=button)
        p = d.probe()
        assert p["mouse"][2:4] == [True, button] and p["touches"] == [[130, 50, 130, 50, "mouse"]]
        page.mouse.up(button=button)
        p = d.probe()
        assert p["mouse"][2:4] == [False, None] and p["touches"] == []
    assert [e[0] for e in p["log"]] == ["md", "ts", "mu", "te"] * 3
    assert [e[3] for e in p["log"] if e[0] == "md"] == ["left", "middle", "right"]
    # the wheel is the scene's
    page.mouse.wheel(0, 120)
    p = d.probe()
    assert p["log"][-1] == ["wheel", 120] and sum(f["wheel"] for f in p["frames"]) == 120
    # a trackpad's pinch arrives as ctrl + wheel
    d.cdp.send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": 130, "y": 50, "deltaX": 0, "deltaY": -10, "modifiers": 2})
    p = d.probe()
    assert p["log"][-1] == ["pinch", 1.11]
    page.wait_for_timeout(400)
    assert d.probe()["scale"] == 1
    # fingers: two, a pinch, a third, and letting go
    d.touch("touchStart", (1, 100, 100))
    d.touch("touchStart", (1, 100, 100), (2, 300, 100))
    p = d.probe()
    assert [t[:2] for t in p["touches"]] == [[100, 100], [300, 100]] and p["touches"][0][4] == "touch"
    assert p["mouse"][:4] == [100, 100, True, "left"]
    d.touch("touchMove", (1, 100, 100), (2, 400, 100))
    p = d.probe()
    assert p["scale"] == 1.5 and p["touches"][1][:4] == [400, 100, 300, 100]
    assert p["mouse"][:2] == [100, 100]   # the mouse follows the first finger only
    assert [100, 0] in [f["t"][1] for f in p["frames"] if len(f["t"]) == 2]
    d.touch("touchStart", (1, 100, 100), (2, 400, 100), (3, 200, 250))
    assert len(d.probe()["touches"]) == 3
    d.touch("touchEnd", (1, 100, 100))
    p = d.probe()
    assert len(p["touches"]) == 2 and p["mouse"][2] is False
    d.touch("touchCancel")
    p = d.probe()
    assert p["touches"] == [] and p["scale"] == 1 and p["mouse"][4] is False
    assert [e[3] for e in p["log"] if e[0] == "te"][-3:] == [False, True, True]
    # keys: pressed and released once, the modifiers, and Shift let go first
    start = len(p["frames"])
    page.keyboard.down("ShiftLeft")
    page.keyboard.down("KeyA")
    p = d.probe()
    assert p["keys"] == ["A", "Shift"] and p["codes"] == ["KeyA", "ShiftLeft"] and p["mods"] == [True, False, False, False]
    page.keyboard.up("ShiftLeft")
    p = d.probe()
    assert p["keys"] == ["A"] and p["mods"][0] is False
    page.keyboard.up("KeyA")
    p = d.probe()
    assert p["keys"] == [] and p["codes"] == []
    assert [e for e in p["log"] if e[0] in ("kd", "ku")] == [["kd", "Shift", "ShiftLeft"], ["kd", "A", "KeyA"], ["ku", "Shift"], ["ku", "A"]]
    new = p["frames"][start:]
    assert sorted(k for f in new for k in f["pressed"]) == ["A", "Shift"]
    assert sorted(k for f in new for k in f["released"]) == ["A", "Shift"]
    assert not d.errors, d.errors


def test_run_input_reaches_python(browser, pyctures_run, tmp_path):
    scene = tmp_path / "probe.py"
    scene.write_text(INPUT_PROBE)
    d = Driven(browser, pyctures_run(scene).url)
    _drive_input(d)
    d.context.close()


@needs_cdn
def test_build_input_reaches_python(browser, static_server, tmp_path):
    from pyctures.build import build
    scene = tmp_path / "probe.py"
    scene.write_text(INPUT_PROBE)
    out = tmp_path / "site"
    build(scene, out, say=lambda *a: None)
    d = Driven(browser, static_server(out))
    _drive_input(d)
    d.context.close()


# ---------------------------------------------------------------- Space Rocks, played by pointer

# Added to the end of the game: its numbers for the test, and a ship no rock can end a check on.
ROCKS_PROBE = """
import json
shots = 0
shoot_once = shoot
def shoot():
    global shots
    shots += 1
    shoot_once()
draw_game = draw
def draw():
    global safe
    safe = 1e9
    draw_game()
    js.window.probe = json.dumps({"x": ship.x, "y": ship.y, "vx": ship.vx, "vy": ship.vy, "angle": ship.angle, "shots": shots, "lives": lives})
"""


def _apart(a, b):
    """How far apart two angles are, the short way round."""
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def _speed(s):
    return math.hypot(s["vx"], s["vy"])


@pytest.mark.parametrize("how", ["mouse", "finger"])
def test_space_rocks_a_tap_shoots_and_a_hold_flies(browser, pyctures_run, tmp_path, how):
    scene = tmp_path / "space_rocks.py"
    scene.write_text((EXAMPLES / "space_rocks.py").read_text() + ROCKS_PROBE)
    # the mouse in a window, a finger on a phone-size touch screen
    d = Driven(browser, pyctures_run(scene).url, size=(1000, 700) if how == "mouse" else (390, 844))
    page = d.page
    if how == "mouse":
        def down(x, y):
            page.mouse.move(x, y)
            page.mouse.down()
        move, up = (lambda x, y: page.mouse.move(x, y, steps=4)), page.mouse.up
    else:
        down = lambda x, y: d.touch("touchStart", (1, x, y))
        move = lambda x, y: d.touch("touchMove", (1, x, y))
        up = lambda: d.touch("touchEnd")
    box = page.evaluate("(() => { const r = document.querySelector('canvas').getBoundingClientRect(); return [r.x, r.y] })()")
    at = lambda x, y: (box[0] + x, box[1] + y)
    s0 = d.probe()
    assert _speed(s0) == 0

    # a tap, down and up within 80 ms: one shot, the ship turned to it, and no engine
    down(*at(s0["x"] + 90, s0["y"] + 50))
    page.wait_for_timeout(80)
    up()
    s1 = d.probe()
    assert s1["shots"] == s0["shots"] + 1
    assert _apart(s1["angle"], math.atan2(50, 90)) < 0.02
    assert _speed(s1) == 0 and (s1["x"], s1["y"]) == (s0["x"], s0["y"])

    # taps as long as a finger's on glass: each shoots, none starts the engine (it waits 0.18 s)
    for ms in (60, 100, 130):
        down(*at(s0["x"] + 90, s0["y"] + 50))
        page.wait_for_timeout(ms)
        up()
        page.wait_for_timeout(150)
    s = d.probe()
    assert _speed(s) == 0 and s["shots"] == s1["shots"] + 3, s
    s1 = s

    # a hold of a second, up and to the left: one shot at its start, and the ship flies that way
    bx, by = s1["x"] - 150, s1["y"] - 200
    down(*at(bx, by))
    page.wait_for_timeout(1000)
    s2 = json.loads(page.evaluate("window.probe"))
    to_b = math.atan2(by - s1["y"], bx - s1["x"])
    along = (s2["x"] - s1["x"]) * math.cos(to_b) + (s2["y"] - s1["y"]) * math.sin(to_b)
    assert s2["shots"] == s1["shots"] + 1
    assert along > 30 and _speed(s2) > 100 and _apart(math.atan2(s2["vy"], s2["vx"]), to_b) < 0.1, (along, s2)

    # the pointer moves while it is held: the ship turns to follow, and does not shoot again
    cx, cy = s1["x"] + 100, s1["y"] + 250
    move(*at(cx, cy))
    page.wait_for_timeout(250)
    s3 = json.loads(page.evaluate("window.probe"))
    assert _apart(s3["angle"], math.atan2(cy - s3["y"], cx - s3["x"])) < 0.15, s3
    assert _apart(s3["angle"], s2["angle"]) > 1 and s3["shots"] == s2["shots"]

    # let go: the engine stops and the ship drifts on
    up()
    s4 = d.probe()
    s5 = d.probe()
    assert (s5["vx"], s5["vy"]) == (s4["vx"], s4["vy"]) and _speed(s5) > 0 and s5["lives"] == 3
    assert not d.errors, d.errors
    d.context.close()


def test_a_scene_that_names_no_wheel_leaves_it_to_the_page(browser, pyctures_run):
    """examples/website: two scenes in a long page, neither naming the wheel."""
    p = pyctures_run(EXAMPLES / "website")
    w = Watched(browser, p.url, size=(900, 500))
    w.page.wait_for_timeout(1000)
    box = w.scenes()[0].bounding_box()
    w.page.mouse.move(box["x"] + 50, box["y"] + 50)
    w.page.mouse.wheel(0, 300)
    w.page.wait_for_timeout(500)
    assert w.page.evaluate("scrollY") > 100
    w.page.close()


# ---------------------------------------------------------------- the docs' own code

def _doc_programs():
    """Every whole Python program in the README and the JavaScript guide."""
    import re
    from conftest import ROOT
    found = []
    for doc in ("README.md", "docs/from-javascript.md", "docs/getting-started.md", "docs/website.md",
                "docs/sound.md", "docs/dials.md", "docs/sheet-music.md", "docs/effects.md"):
        blocks = re.findall(r"```python\n(.*?)```", (ROOT / doc).read_text(), re.S)
        for i, code in enumerate(blocks):
            # A fragment that leans on names made elsewhere (the README's
            # side-by-side cube) is checked with its setup in front of it.
            if "scene.add(cube)" in code and "THREE.Scene()" not in code:
                code = ("renderer = THREE.WebGLRenderer(canvas=canvas)\nrenderer.setSize(width, height, False)\n"
                        "scene = THREE.Scene()\ncamera = THREE.PerspectiveCamera(60, width / height, 0.1, 100)\n"
                        "camera.position.z = 3\nscene.add(THREE.AmbientLight(0xffffff, 2))\n" + code)
            found.append(("%s-%d" % (doc.replace("docs/", "").replace(".md", ""), i + 1), code))
    return found


@pytest.mark.parametrize("name,code", _doc_programs(), ids=[n for n, _ in _doc_programs()])
def test_docs_python_runs(browser, pyctures_run, tmp_path, name, code):
    scene = tmp_path / "scene.py"
    scene.write_text(code)
    if "textures/" in code:   # a block that loads a picture uses the examples' own
        shutil.copytree(EXAMPLES / "textures", tmp_path / "textures")
    p = pyctures_run(scene)
    w = Watched(browser, p.url)
    # A scene that only makes controls draws nothing of its own: they are on a layer over it.
    w.check("docs-%s.png" % name, min_colours=1 if ("from pydials" in code and "def draw(" not in code) or "background()" in code else 2)
