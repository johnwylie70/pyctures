"""Every example in a real (headless) Chromium: `pyctures run`, and `pyctures build` with Pyodide.

Needs Playwright:  pip install playwright && playwright install chromium
Screenshots land in tests/screenshots/.
"""
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
        b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
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
    w.check("run-" + scene.replace(".py", ".png"))
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


# ---------------------------------------------------------------- the docs' own code

def _doc_programs():
    """Every whole Python program in the README and the JavaScript guide."""
    import re
    from conftest import ROOT
    found = []
    for doc in ("README.md", "docs/from-javascript.md", "docs/getting-started.md", "docs/website.md"):
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
    p = pyctures_run(scene)
    w = Watched(browser, p.url)
    w.check("docs-%s.png" % name, min_colours=2)
