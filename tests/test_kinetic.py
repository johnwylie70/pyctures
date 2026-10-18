"""Kinetic text: word_slam(), count_up() and the rest (the library pykinetic, whose page half is kinetic.js, handle 17).

The Python half is thin: each call is one command with the effect, the words and the options, and Python gives every
call its time. The checks: what Python sends and the time it keeps, that its numbers (the house style, the safe area,
seeded_random) are the JavaScript library's, that a scene that names none loads none of it, and that, in a real
Chromium, the same call in Python and in JavaScript (pictures.js, when it is beside this repository) draws the same
pixels, at 1920x1080 and at 1080x1920, for every effect.
"""
import json
import shutil
import subprocess
import sys
import textwrap
import time

import pytest

import pyctures
from conftest import ROOT
from test_browser import Watched

sync_api = pytest.importorskip("playwright.sync_api")

BESIDE = ROOT.parent
WEB = ROOT / "src" / "pyctures" / "web" / "kinetic"
KINETIC_JS = WEB / "kinetic.js"
sys.path.append(str(WEB))
import pykinetic  # noqa: E402

INFO = json.dumps({"width": 400, "height": 300, "pixel_ratio": 1})
H_KINETIC = 17
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node is not here")


def node(code):
    """What the JavaScript library says: `code` is run with the module as `m`; its result is printed as JSON."""
    out = subprocess.run(["node", "--input-type=module", "-e", "import('%s').then((m) => console.log(JSON.stringify(%s)))" % (KINETIC_JS.as_uri(), code)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def kinetic_calls(reply):
    return [(c[4], c[5][0], c[5][1]) for c in reply["cmds"] if c[0] == "call" and c[3] == H_KINETIC]


# ---------------------------------------------------------------- the Python half

def test_a_call_is_one_command_with_the_effect_the_words_and_the_options_and_the_scene_s_seconds():
    reply = json.loads(pyctures.start("def draw():\n    word_slam('Hi *there*', start=0.5, size='title', y=0.3, beat=2.5, color='red')\n", INFO))
    (name, words, o), = kinetic_calls(reply)
    assert (name, words) == ("wordSlam", "Hi *there*")
    assert o == {"start": 0.5, "y": 0.3, "size": "title", "colour": "red", "beat": 2.5, "t": 0.0}, o
    assert pyctures.H_EFFECTS == 13 and H_KINETIC not in (pyctures.H_SOUND, pyctures.H_DIALS, 12, 13, 14, 15, 16)
    assert pykinetic.H_KINETIC == H_KINETIC


def test_the_scene_s_seconds_are_the_frames_dt_added_up_and_a_recorder_s_time_when_there_is_one():
    pyctures.start("def draw():\n    letter_wave('x')\n", INFO)
    seen = []
    for dt in (0.25, 0.5, 0.25):
        seen.append(kinetic_calls(json.loads(pyctures.tick(json.dumps({"dt": dt}))))[0][2]["t"])
    assert seen == [0.0, 0.25, 0.75], "a frame draws at the time before it, as pictures.js does"
    pyctures.start("def draw():\n    letter_wave('x')\n", json.dumps({"width": 400, "height": 300, "pixel_ratio": 1, "vt": 0}))
    ts = [kinetic_calls(json.loads(pyctures.tick(json.dumps({"dt": 0.02, "vt": vt}))))[0][2]["t"] for vt in (1.0, 1.5)]
    assert ts == [1.0, 1.5]


def test_kinetic_time_reads_sets_and_holds_and_an_explicit_t_wins():
    src = "kinetic_time(5, hold=True)\n\ndef draw():\n    count_up('9')\n    count_up('9', t=1.5)\n    global_t.append(kinetic_time())\n"
    reply = json.loads(pyctures.start("global_t = []\n" + src, INFO))
    assert [c[2]["t"] for c in kinetic_calls(reply)] == [5.0, 1.5]
    reply = json.loads(pyctures.tick(json.dumps({"dt": 1.0})))
    assert [c[2]["t"] for c in kinetic_calls(reply)] == [5.0, 1.5], "held: it does not move on"
    assert pyctures.S.ns["global_t"][-1] == 5.0
    pyctures.start("def draw():\n    kinetic_time(2)\n    count_up('9')\n", INFO)
    reply = json.loads(pyctures.tick(json.dumps({"dt": 1.0})))
    assert kinetic_calls(reply)[0][2]["t"] == 2.0 and pykinetic.kinetic_time() == 3.0


def test_the_other_options_are_named_and_a_wrong_one_says_so():
    reply = json.loads(pyctures.start("def draw():\n    count_up('9', from_=5)\n    mask_reveal('x', direction='up')\n    kinetic_text('pop', 'a *b*', accent='pink')\n", INFO))
    got = kinetic_calls(reply)
    assert got[0][2]["from"] == 5 and got[1][2]["direction"] == "up" and got[2][0] == "scalePop" and got[2][2]["accent"] == "pink"
    for bad, said in (("word_slam('x', speed=2)", "no option 'speed'"), ("kinetic_text('spin', 'x')", 'no kinetic effect "spin"'), ("word_slam('x', beat='fast')", "beat is a number")):
        out = json.loads(pyctures.start("def draw():\n    %s\n" % bad, INFO))
        assert said in out["error"], (bad, out)


def test_a_beat_may_be_an_object_with_a_beat_or_a_dict():
    class Music:
        beat = 7.5
    assert pykinetic._beat(Music()) == 7.5 and pykinetic._beat({"beat": 3}) == 3.0 and pykinetic._beat(None) is None


def test_every_effect_has_a_python_spelling_and_a_file_is_given_them_only_when_it_names_one():
    from pyctures import pages
    assert set(pykinetic.NAMES) >= {"word_slam", "letter_wave", "letter_bounce", "typewriter_text", "glitch_text", "mask_reveal", "scale_pop",
                                    "ticker_text", "count_up", "highlight_sweep", "kinetic_text", "kinetic_time", "kinetic_safe", "kinetic_effects", "seeded_random"}
    assert not pages.uses_library("def draw():\n    background('navy')\n    ship.word_slamming()\n", "pykinetic")
    for names in ("word_slam('x')", "x = house_style.palette.ink", "r = seeded_random(3)", "kinetic_safe()"):
        assert pages.uses_library(names, "pykinetic") and pykinetic._USES.search(names)
    pyctures.start("def draw():\n    background('navy')\n", INFO)
    assert pyctures.S.ns.get("word_slam") is None and getattr(pyctures.S, "kinetic", None) is None


# ---------------------------------------------------------------- the same numbers as JavaScript

@needs_node
def test_the_house_style_is_the_javascript_one():
    assert json.loads(json.dumps(pykinetic.house_style)) == node("m.houseStyle")
    assert pykinetic.house_style.palette.ink == "#0b1020" and pykinetic.house_style.voices.calm.weight == 500


@needs_node
def test_seeded_random_gives_javascript_s_numbers():
    for seed in (1, 7, 12345):
        roll = pykinetic.seeded_random(seed)
        assert [roll() for _ in range(5)] == node("(() => { const r = m.seededRandom(%d); return [r(), r(), r(), r(), r()] })()" % seed)


@needs_node
@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920), (1080, 1350), (800, 800)])
def test_the_safe_area_is_the_javascript_one(size):
    pyctures.start("def draw():\n    pass\n\nkinetic_effects()\n", json.dumps({"width": size[0], "height": size[1], "pixel_ratio": 1}))
    ours = dict(pykinetic.kinetic_safe(top=0.2))
    theirs = node("m.safeArea(%d, %d, { top: 0.2 })" % size)
    assert {k: round(v, 6) for k, v in ours.items()} == {k: round(v, 6) for k, v in theirs.items()}


# ---------------------------------------------------------------- in a browser

SHAPES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
# What each effect is given, as the gallery gives it: its Python name, its JavaScript one, the words and the voice.
EFFECTS = [
    ("word_slam", "wordSlam", "Learn *to code* today", "playful"),
    ("letter_wave", "letterWave", "Everything *moves*", "techy"),
    ("letter_bounce", "letterBounce", "Drop in *bounce*", "calm"),
    ("typewriter_text", "typewriterText", "print('hello, world')", "playful"),
    ("glitch_text", "glitchText", "Signal *lost*", "techy"),
    ("mask_reveal", "maskReveal", "Wipe *it* clean", "calm"),
    ("scale_pop", "scalePop", "Make it *pop* now", "playful"),
    ("ticker_text", "tickerText", "Free to try   *Python*   JavaScript", "techy"),
    ("count_up", "countUp", "12,000+", "calm"),
    ("highlight_sweep", "highlightSweep", "Mark the *important* part", "playful"),
]
STILLS = (0.9, 2.9)

PY_SCENE = """
def draw():
    background(house_style.palette.ink)
    safe = kinetic_safe()
    text("label", width / 2, safe.top + height * 0.03, house_style.palette.dim, height * 0.035, "centre")
    room = (safe.top + height * 0.08) / height
    %(py)s(%(words)r, t=%(t)s, style=%(voice)r, safe={"top": room})
"""
PY_CLOCK = """
kinetic_time(%(t)s, hold=True)

def draw():
    background(house_style.palette.ink)
    %(py)s(%(words)r, style=%(voice)r)
"""
JS_SCENE = """
function draw() {
  background(houseStyle.palette.ink)
  const safe = kineticSafe()
  text("label", width / 2, safe.top + height * 0.03, houseStyle.palette.dim, height * 0.035, "centre")
  const room = (safe.top + height * 0.08) / height
  %(js)s(%(words)s, { t: %(t)s, style: %(voice)s, safe: { top: room } })
}
"""
JS_CLOCK = """
kineticTime(%(t)s, { hold: true })
function draw() {
  background(houseStyle.palette.ink)
  %(js)s(%(words)s, { style: %(voice)s })
}
"""
PIXELS = "() => document.querySelector('[data-pyctures-src] canvas, #s canvas').toDataURL()"


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"])
        yield b
        b.close()


def js_still(browser, base, size, source):
    """pictures.js's picture of a scene: run in its own page at the size, with two frames' time to settle."""
    page = browser.new_page(viewport={"width": size[0], "height": size[1]})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base + "test.html")
    page.evaluate("""async (source) => {
      const { runScene } = await import('/pictures.js')
      window.error = null
      window.scene = runScene(document.getElementById('s'), { source, name: 'scene.js', onError: (m) => { window.error = m } })
      await window.scene.ready
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
    }""", source)
    page.wait_for_function("window.error || document.querySelector('#s canvas')")
    got = page.evaluate("() => window.error || document.querySelector('#s canvas').toDataURL()")
    page.close()
    assert not errors and got.startswith("data:image/png"), (errors, got[:200])
    return got


@pytest.fixture
def js_site(tmp_path, static_server):
    """pictures.js, as a page can load it (the file and the folder of this part), and a page to run a scene in."""
    mine = BESIDE / "pictures.js"
    if not (mine / "kinetic" / "kinetic.js").is_file():
        pytest.skip("pictures.js is not beside this repository, or has no kinetic text yet")
    site = tmp_path / "site"
    site.mkdir()
    (site / "pictures.js").symlink_to(mine / "pictures.js")
    (site / "kinetic").symlink_to(mine / "kinetic")
    (site / "test.html").write_text('<!doctype html><body style="margin:0"><div id="s" style="position:relative;width:100vw;height:100vh"></div>')
    return static_server(site)


def test_a_scene_that_names_no_kinetic_function_is_sent_none_of_it(browser, pyctures_run, tmp_path):
    file = tmp_path / "scene.py"
    file.write_text("def draw():\n    background('navy')\n    circle(100, 100, 30, 'gold')\n")
    asked = []
    w = Watched(browser, "about:blank", size=(300, 200))
    w.page.on("request", lambda r: asked.append(r.url))
    w.page.goto(pyctures_run(file).url)
    w.wait_running()
    assert not [u for u in asked if "kinetic" in u], asked
    w.page.close()


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_every_effect_draws_the_same_pixels_in_python_as_in_javascript(browser, pyctures_run, tmp_path, js_site, shape):
    size = SHAPES[shape]
    file = tmp_path / ("scene_%s.py" % shape)
    file.write_text("def draw():\n    background('navy')\n")
    server = pyctures_run(file)
    differ, same, errors = [], 0, []
    for py, js, words, voice in EFFECTS:
        for t in STILLS:
            file.write_text(textwrap.dedent(PY_SCENE) % {"py": py, "words": words, "t": t, "voice": voice})
            time.sleep(1.5)   # (the server notices a changed file, and a page open then starts again)
            w = Watched(browser, server.url, size=size)
            w.wait_running()
            w.page.wait_for_timeout(150)
            mine = w.page.evaluate(PIXELS)
            errors += ["%s %s: %s" % (py, t, e) for e in w.errors]
            w.page.close()
            theirs = js_still(browser, js_site, size, JS_SCENE % {"js": js, "words": json.dumps(words), "t": t, "voice": json.dumps(voice)})
            blank = js_still(browser, js_site, size, "function draw() { background(houseStyle.palette.ink) }")
            if mine != theirs:
                differ.append("%s at %s s" % (py, t))
            elif theirs == blank:
                differ.append("%s at %s s: blank in both" % (py, t))
            else:
                same += 1
    assert not errors, errors
    assert not differ, "%s: %s" % (shape, differ)
    assert same == len(EFFECTS) * len(STILLS)


def test_the_scene_s_own_clock_draws_the_same_pixels_in_python_as_in_javascript(browser, pyctures_run, tmp_path, js_site):
    size = SHAPES["9x16"]
    py, js, words, voice = EFFECTS[0]
    file = tmp_path / "scene_clock.py"
    file.write_text(textwrap.dedent(PY_CLOCK) % {"py": py, "words": words, "t": 1.2, "voice": voice})
    w = Watched(browser, pyctures_run(file).url, size=size)
    w.wait_running()
    w.page.wait_for_timeout(300)
    mine = w.page.evaluate(PIXELS)
    theirs = js_still(browser, js_site, size, JS_CLOCK % {"js": js, "words": json.dumps(words), "t": 1.2, "voice": json.dumps(voice)})
    assert mine == theirs and not w.errors, w.errors
    w.page.close()


def test_the_python_examples_run_and_stay_in_the_safe_area(browser, pyctures_run, tmp_path):
    """Each example, at a tall size: it draws, and nothing is drawn outside the tall frame's safe area (top 14, bottom 18, sides 6 percent)."""
    for name, wait in (("hook.py", 6500), ("kinetic_gallery.py", 1500)):
        w = Watched(browser, pyctures_run(ROOT / "examples" / name).url, size=(540, 960))
        w.wait_running()
        w.page.wait_for_timeout(wait)
        out = w.page.evaluate("""() => {
          const c = document.querySelector('[data-pyctures-src] canvas'), g = c.getContext('2d'), W = c.width, H = c.height
          const d = g.getImageData(0, 0, W, H).data
          let lit = 0, outside = 0
          for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
            const i = (y * W + x) * 4
            if (Math.abs(d[i] - 11) + Math.abs(d[i + 1] - 16) + Math.abs(d[i + 2] - 32) < 30) continue
            lit++
            if (x < W * 0.06 - 1 || x > W * 0.94 + 1 || y < H * 0.14 - 1 || y > H * 0.82 + 1) outside++
          }
          return { lit, outside }
        }""")
        assert out["lit"] > 300 and out["outside"] == 0, (name, out)
        assert not w.errors, w.errors
        w.page.close()


from test_browser import cdn_reachable  # noqa: E402

needs_cdn = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")


@needs_cdn
@pytest.mark.parametrize("html", [False, True], ids=["folder", "one file"])
def test_build_kinetic_text_with_python_in_the_browser(browser, static_server, tmp_path, html):
    """`pyctures build` carries kinetic.js and pykinetic.py for a file that names one, and the built page draws the text."""
    from pyctures.build import build as make
    scene = tmp_path / "hook.py"
    scene.write_text((ROOT / "examples" / "hook.py").read_text())
    out = tmp_path / ("scene.html" if html else "site")
    said = []
    make(scene, out, say=said.append)
    if html:
        assert "with kinetic text" in said[0]
    else:
        assert (out / "pyctures" / "kinetic" / "kinetic.js").is_file() and (out / "pyctures" / "kinetic" / "pykinetic.py").is_file()
    w = Watched(browser, static_server(tmp_path if html else out) + ("scene.html" if html else ""), size=(540, 960))
    w.wait_running(timeout=120)
    w.page.wait_for_timeout(6500)
    lit = w.page.evaluate("""() => {
      const c = document.querySelector('[data-pyctures-src] canvas'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data
      let n = 0
      for (let i = 0; i < d.length; i += 4) if (Math.abs(d[i] - 11) + Math.abs(d[i + 1] - 16) + Math.abs(d[i + 2] - 32) >= 30) n++
      return n
    }""")
    assert lit > 300 and not w.errors, (lit, w.errors)


WIPE_PY = """
def draw():
    background(house_style.palette.ink)
    mask_reveal("Press run.", t=%s, size="title")
"""
WIPE_JS = """
function draw() {
  background(houseStyle.palette.ink)
  maskReveal("Press run.", { t: %s, size: "title" })
}
"""
# The leftmost near-white pixel of a picture: where the first letter begins.
LEFTMOST = """(url) => new Promise((done) => {
  const img = new Image(); img.onload = () => {
    const c = document.createElement('canvas'); c.width = img.width; c.height = img.height
    const g = c.getContext('2d'); g.drawImage(img, 0, 0); const d = g.getImageData(0, 0, c.width, c.height).data
    let x0 = c.width
    for (let y = 0; y < c.height; y++) for (let x = 0; x < x0; x++) { const i = (y * c.width + x) * 4; if (d[i] > 200 && d[i + 1] > 200 && d[i + 2] > 200) { x0 = x; break } }
    done(x0 === c.width ? None : x0) } ; img.src = url })""".replace("None", "null")


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_mask_reveal_does_not_clip_the_first_letter_and_draws_what_javascript_draws(browser, pyctures_run, tmp_path, js_site, shape):
    """While the wipe goes, the picture is pixel for pixel pictures.js's, and the first letter is not cut: its left edge
    is where the finished text's is, less the slide the text makes as it is uncovered."""
    size = SHAPES[shape]
    file = tmp_path / ("wipe_%s.py" % shape)
    file.write_text("def draw():\n    background('navy')\n")
    server = pyctures_run(file)
    lefts = {}
    for t in (1.8, 0.36, 0.5, 0.63, 0.77):
        file.write_text(WIPE_PY % t)
        time.sleep(1.5)
        w = Watched(browser, server.url, size=size)
        w.wait_running()
        w.page.wait_for_timeout(150)
        mine = w.page.evaluate(PIXELS)
        assert not w.errors, w.errors
        theirs = js_still(browser, js_site, size, WIPE_JS % t)
        assert mine == theirs, "%s at %s s differs from pictures.js" % (shape, t)
        lefts[t] = w.page.evaluate(LEFTMOST, mine)
        w.page.close()
    done = lefts[1.8]
    assert done is not None
    # (px is the title size: 0.085 of the shorter side, raised to the minimum; it is the same 0.5 em slide as in JavaScript.)
    px = max(0.085 * min(size), 0.03 * size[1])
    for t in (0.5, 0.63, 0.77):
        u = t / 0.9
        e = 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
        assert lefts[t] is not None and abs(lefts[t] - (done - (1 - e) * px * 0.5)) <= 3, (shape, t, lefts, done, px)
