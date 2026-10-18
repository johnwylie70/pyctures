"""The code-along: code_along() and code_along_stage_at() (the library pycodealong, whose page half is codealong.js, handle 18).

Python works out the plan (which stage is on show and when), the layout (how big the preview's pane is) and runs a Python stage for its
preview; the page draws the code and runs a JavaScript stage. The checks: that what Python works out is what the JavaScript library works out
(the same numbers, with node), what Python sends, that a stage of Python is really run (and one that raises is shown, and the scene's
random is put back), that a scene that names none loads none of it, and that, in a real Chromium, a JavaScript stage draws the same pixels
from Python as pictures.js does, a Python stage draws its circle, and the example fits the safe area at 1920x1080 and 1080x1920.
"""
import json
import shutil
import subprocess
import sys
import time

import pytest

import pyctures
from conftest import ROOT
from test_browser import Watched

sync_api = pytest.importorskip("playwright.sync_api")

BESIDE = ROOT.parent
WEB = ROOT / "src" / "pyctures" / "web"
CODEALONG_JS = WEB / "codealong" / "codealong.js"
KINETIC_JS = WEB / "kinetic" / "kinetic.js"
sys.path.append(str(WEB / "codealong"))
sys.path.append(str(WEB / "kinetic"))
import pycodealong  # noqa: E402

INFO = json.dumps({"width": 1920, "height": 1080, "pixel_ratio": 1})
H_CODEALONG = 18
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node is not here")

STAGES = [
    {"code": 'def draw():\n    background("navy")'},
    {"code": 'def draw():\n    background("navy")\n    x = width / 2\n    circle(x, 100, 80, "gold")', "hold": 2},
    {"code": 'r = 20\n\ndef update(dt):\n    global r\n    r += 60 * dt\n\ndef draw():\n    background("navy")\n    x = width / 2\n    circle(x, 100, r, "gold")'},
]


def node(code):
    """What the JavaScript library says: `code` is run with codealong.js as `m` and kinetic.js as `k`; its result is printed as JSON."""
    script = "const [m, k] = await Promise.all([import('%s'), import('%s')]); m.useKit(k); console.log(JSON.stringify(%s))" % (
        CODEALONG_JS.as_uri(), KINETIC_JS.as_uri(), code)
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def calls(reply):
    return [(c[4], c[5]) for c in reply["cmds"] if c[0] == "call" and c[3] == H_CODEALONG]


def snake(name):
    return "".join("_" + c.lower() if c.isupper() else c for c in name)


# ---------------------------------------------------------------- the Python half

def test_a_call_is_one_command_for_a_javascript_stage_and_a_pane_with_the_drawing_between_for_a_python_one():
    src = "def draw():\n    code_along(stages=STAGES, duration=12)\n"
    pyctures.start("STAGES = %r\n%s" % (STAGES, src), json.dumps({"width": 1920, "height": 1080, "pixel_ratio": 1, "vt": 0.0}))
    seen = {}
    for vt in (0.3, 2.0, 6.0, 11.9):
        reply = json.loads(pyctures.tick(json.dumps({"dt": 0.01, "vt": vt})))
        assert not reply.get("error"), reply
        seen[vt] = [c[4] for c in reply["cmds"] if c[0] == "call"]
    assert seen[0.3] == ["codeAlong"], "nothing to run yet: the page draws the code"
    assert seen[2.0] == ["codeAlongBegin", "background", "codeAlongEnd"], "stage 1 is run here, between the page's two"
    assert seen[6.0][0] == "codeAlongBegin" and seen[6.0][-1] == "codeAlongEnd" and "circle" in seen[6.0]
    assert pycodealong.H_CODEALONG == H_CODEALONG and pyctures.H_EFFECTS == 13


def test_the_scene_s_seconds_are_the_kinetic_clock_and_t_wins():
    pyctures.start("def draw():\n    code_along(stages=['x = 1'])\n    code_along(stages=['x = 1'], t=1.5)\n", INFO)
    json.loads(pyctures.tick(json.dumps({"dt": 0.25})))
    reply = json.loads(pyctures.tick(json.dumps({"dt": 0.25})))
    ts = [args[0]["t"] for name, args in calls(reply) if name != "codeAlongEnd"]
    assert ts == [0.25, 1.5], ts


def test_a_beat_that_has_not_begun_draws_nothing_and_gives_back_none():
    pyctures.start("got = []\n\ndef draw():\n    got.append(code_along(stages=['x = 1'], start=5))\n", INFO)
    assert pyctures.S.ns["got"] == [None] and not calls(json.loads(pyctures.tick("{}")))


def test_a_python_stage_is_run_for_real_with_the_panes_own_width_and_height_and_its_update_stepped_from_zero():
    src = ('STAGES = [{"code": "r = 0\\n\\ndef update(dt):\\n    global r\\n    r += 60 * dt\\n\\ndef draw():\\n    circle(width / 2, height / 2, r, \\"gold\\")"}]\n'
           "T = [0]\ngot = []\n\ndef draw():\n    got.append(code_along(stages=STAGES, duration=6, t=T[0]))\n")
    pyctures.start(src, INFO)
    for t in (5.5, 5.7, 5.9):
        pyctures.S.ns["T"][0] = t
        reply = json.loads(pyctures.tick(json.dumps({"dt": 0.01})))
        assert not reply.get("error"), reply
        pane = pyctures.S.ns["got"][-1]
        draws = [c for c in reply["cmds"] if c[0] == "call" and c[4] == "circle"]
        assert len(draws) == 1
        x, y, radius, colour = draws[0][5]
        local = pyctures.S.ns["got"][-1]["preview_time"]
        assert abs(radius - 60 * (int(local * 60 + 1e-9) / 60)) < 1e-6, (radius, local)
        assert x > 100 and y > 100 and colour == "gold"
        assert pane["preview"] == 0


def test_a_stage_that_raises_shows_its_message_in_the_pane_and_in_warnings_and_the_scene_goes_on():
    src = "got = []\n\ndef draw():\n    got.append(code_along(stages=[{'code': 'def draw():\\n    undefined_name()'}], t=2.5))\n"
    pyctures.start(src, INFO)
    reply = json.loads(pyctures.tick("{}"))
    assert not reply.get("error")
    (name, (o,)), *_ = [c for c in calls(reply) if c[0] == "codeAlongBegin"]
    assert "NameError" in o["previewError"] and "undefined_name" in o["previewError"]
    assert any("stage 1 would not run" in w for w in pyctures.S.ns["got"][-1]["warnings"])
    # A stage that does not compile is the same.
    pyctures.start("def draw():\n    code_along(stages=['def draw(:'], t=2.5)\n", INFO)
    reply = json.loads(pyctures.tick("{}"))
    assert "SyntaxError" in [c for c in calls(reply) if c[0] == "codeAlongBegin"][0][1][0]["previewError"]


def test_a_stages_random_is_seeded_and_the_scene_s_is_put_back():
    stage = "import random\\nvalues = []\\ndef draw():\\n    circle(random.random() * 100, 5, 5)"
    src = ("import random\nrandom.seed(5)\nT = [5.5]\nafter = []\n\ndef draw():\n    code_along(stages=[{'code': '%s'}], duration=6, t=T[0])\n"
           "    after.append(random.random())\n") % stage
    pyctures.start(src, INFO)
    first = [c[5][0] for c in json.loads(pyctures.tick("{}"))["cmds"] if c[0] == "call" and c[4] == "circle"]
    pyctures.start(src, INFO)
    second = [c[5][0] for c in json.loads(pyctures.tick("{}"))["cmds"] if c[0] == "call" and c[4] == "circle"]
    assert first == second and len(first) == 1, (first, second)
    import random
    random.seed(5)
    expected = random.random()
    assert pyctures.S.ns["after"][0] == expected, "the scene's own random() goes on as it would without the stage"


def test_a_file_is_given_the_code_along_only_when_it_names_one_and_with_it_the_kinetic_text():
    from pyctures import pages
    assert pages.uses_library("def draw():\n    code_along(stages=s)\n", "pycodealong") and pages.uses_library("code_along_stage_at(s, 1)", "pycodealong")
    assert pages.uses_library("code_along(stages=s)", "pykinetic"), "its look is the kinetic text's"
    assert not pages.uses_library("def draw():\n    background('navy')\n    ship.code_along()\n", "pycodealong")
    pyctures.start("def draw():\n    background('navy')\n", INFO)
    assert pyctures.S.ns.get("code_along") is None and getattr(pyctures.S, "codealong", None) is None
    pyctures.start("def draw():\n    code_along(stages=['x'])\n", INFO)
    assert callable(pyctures.S.ns["code_along"]) and callable(pyctures.S.ns["code_along_stage_at"]) and callable(pyctures.S.ns["word_slam"])
    assert set(pycodealong.NAMES) == {"code_along", "code_along_stage_at"}


def test_a_stage_gets_a_silent_say_and_a_mouth_of_the_previews_own_size_that_talks_only_when_asked():
    stage = 'say("Hello there, my friend")\\ndef draw():\\n    mouth(width / 2, height / 2)'
    src = "T = [5.8]\n\ndef draw():\n    code_along(stages=[{'code': '%s'}], duration=6, t=T[0], demo_voice=DEMO)\n" % stage
    sizes, levels = [], []
    for demo in (False, True):
        pyctures.start("DEMO = %r\n%s" % (demo, src), INFO)
        for t in (3.7, 3.9, 4.1):
            pyctures.S.ns["T"][0] = t
            reply = json.loads(pyctures.tick("{}"))
            assert not reply.get("error"), reply
            assert not [c for c in reply["cmds"] if c[0] == "call" and c[3] == 16 and c[4] == "say"], "the preview does not speak"
            (m,) = [c[5] for c in reply["cmds"] if c[0] == "call" and c[3] == 16 and c[4] == "mouth"]
            sizes.append(m[2])
            levels.append((demo, m[5]))
    pane = pycodealong._layout({}, pycodealong.plan([{"code": stage.replace("\\n", "\n")}], 6), 1920, 1080)["inner"]
    assert all(abs(z - 0.16 * min(pane["w"], pane["h"])) < 1e-6 for z in sizes), sizes
    assert all(level == 0 for demo, level in levels if not demo) and any(level > 0 for demo, level in levels if demo), levels


def test_wrong_options_say_what_is_wrong():
    for bad, said in (("code_along(stages=[])", "needs stages"), ("code_along(stages=['x'], layout='sideways')", 'no layout "sideways"'),
                      ("code_along(stages=[{'code': 'x', 'language': 'cobol'}])", 'no tokenizer for "cobol"'), ("code_along(stages=[{}])", "stage 0 has no code")):
        out = json.loads(pyctures.start("def draw():\n    %s\n" % bad, INFO))
        assert said in out["error"], (bad, out)


# ---------------------------------------------------------------- the same numbers as JavaScript

def camel_to_python(d):
    return {snake(k): v for k, v in d.items()}


CASES = [
    (STAGES, {"duration": 12}),
    (STAGES, {"duration": 3}),
    (STAGES, {}),
    (STAGES, {"duration": 40, "typing_speed": 10}),
    ([{"code": "a = 1\nb = 2\nc = a + b"}, {"code": "a = 1\nb = 5\nc = a + b\nprint(c)", "hold": 3}, "x"], {"duration": 9, "seed": 7}),
    ([{"code": "x" * 2000}], {"duration": 2}),
    ([{"code": "a = 1"}, {"code": "a = 1\nb = 2", "at": 4, "typeTime": 1}, {"code": "a = 1\nb = 2\nc = 3", "typeAt": 0.75}], {"duration": 12}),
    ([{"code": "def draw():\n    circle(x, y, 80, 'gold')\n    background('navy')"}, {"code": "def draw():\n    background('navy', 1, 2, 3, 4, 5, 6)\n    circle(width / 2, height / 2, 80, 'gold')"}], {"duration": 9}),
]


def js_options(o):
    return json.dumps({{"typing_speed": "typingSpeed"}.get(k, k): v for k, v in o.items()})


@needs_node
@pytest.mark.parametrize("n", range(len(CASES)))
def test_the_plan_and_which_stage_is_on_show_are_the_javascript_ones(n):
    stages, options = CASES[n]
    times = [round(0.17 * i, 2) for i in range(0, 80)]
    theirs = node("%s.map((t) => ({ ...m.stageAt(%s, t, %s), t }))" % (json.dumps(times), json.dumps(stages), js_options(options)))
    keep = ("stage", "phase", "typed", "inserted", "length", "text", "cursor", "changed", "preview", "preview_time", "stage_time", "type_end",
            "hold_end", "hold_left", "total", "rate", "warnings")
    for t, js in zip(times, theirs):
        ours = pycodealong.code_along_stage_at(stages, t, **options)
        mine = {k: ours[k] for k in keep}
        want = {k: camel_to_python(js)[k] for k in keep}
        for k in keep:
            if isinstance(want[k], float) or isinstance(mine[k], float):
                assert abs(mine[k] - want[k]) < 1e-9, (t, k, mine[k], want[k])
            else:
                assert mine[k] == want[k], (t, k, mine[k], want[k])


@needs_node
@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920), (1080, 1350)])
@pytest.mark.parametrize("n", [0, 4, 5, 7])
def test_the_layout_is_the_javascript_one(size, n):
    stages, options = CASES[n]
    kinetic = pytest.importorskip("pykinetic")
    pyctures.start("def draw():\n    pass\n\nkinetic_effects()\n", json.dumps({"width": size[0], "height": size[1], "pixel_ratio": 1}))
    P = pycodealong.plan(stages, **options)
    for o in ({}, {"run": False}, {"layout": "stack"}, {"previewPad": 10}, {"fontScale": 0.3}, {"fontScale": 1.4, "x": 50, "y": 40, "w": 900, "h": 700}):
        ours = pycodealong._layout(o, P, *size)
        theirs = node("m.layout(%s, m.plan(%s, %s), %d, %d)" % (json.dumps(o), json.dumps(stages), js_options(options), *size))
        for k in ("mode", "box", "code", "preview", "inset", "inner", "px", "cw", "lh", "pad", "gap", "gutter", "cols", "visible", "warnings", "minPx"):
            a, b = ours[k], theirs[k]
            if a is None:
                assert b is None, (o, k, a, b)
            elif isinstance(a, dict):
                assert {x: round(y, 6) for x, y in a.items()} == {x: round(y, 6) for x, y in b.items()}, (o, k, a, b)
            elif isinstance(a, float):
                assert abs(a - b) < 1e-6, (o, k, a, b)
            else:
                assert a == b, (o, k, a, b)
    assert kinetic is not None


# ---------------------------------------------------------------- in a browser

SHAPES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
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
    """pictures.js, as a page can load it (the file and the folders of these parts), and a page to run a scene in."""
    mine = BESIDE / "pictures.js"
    if not (mine / "codealong" / "codealong.js").is_file():
        pytest.skip("pictures.js is not beside this repository, or has no code-along yet")
    site = tmp_path / "site"
    site.mkdir()
    (site / "pictures.js").symlink_to(mine / "pictures.js")
    for folder in ("kinetic", "codealong"):
        (site / folder).symlink_to(mine / folder)
    (site / "test.html").write_text('<!doctype html><body style="margin:0"><div id="s" style="position:relative;width:100vw;height:100vh"></div>')
    return static_server(site)


def test_a_scene_that_names_no_code_along_is_sent_none_of_it(browser, pyctures_run, tmp_path):
    from test_browser import Watched
    file = tmp_path / "scene.py"
    file.write_text("def draw():\n    background('navy')\n    circle(100, 100, 30, 'gold')\n")
    asked = []
    w = Watched(browser, "about:blank", size=(300, 200))
    w.page.on("request", lambda r: asked.append(r.url))
    w.page.goto(pyctures_run(file).url)
    w.wait_running()
    assert not [u for u in asked if "codealong" in u], asked
    w.page.close()


JS_STAGES = [
    "function draw() {\\n  background(\\\"navy\\\")\\n}",
    "function draw() {\\n  background(\\\"navy\\\")\\n  circle(width / 2, 100, 60, \\\"gold\\\")\\n}",
]


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_a_javascript_stage_draws_the_same_pixels_from_python_as_from_pictures_js(browser, pyctures_run, tmp_path, js_site, shape):
    size = SHAPES[shape]
    py_stages = [{"code": s.replace("\\n", "\n").replace('\\"', '"'), "language": "javascript"} for s in JS_STAGES]
    file = tmp_path / ("scene_%s.py" % shape)
    differ, same = [], 0
    file.write_text("def draw():\n    background('navy')\n")
    server = pyctures_run(file)
    for t in (0.9, 2.6, 5.5):
        file.write_text("def draw():\n    background(house_style.palette.ink)\n    code_along(stages=%r, duration=6, t=%s)\n" % (py_stages, t))
        time.sleep(1.5)   # (the server notices a changed file, and a page open then starts again)
        w = Watched(browser, server.url, size=size)
        w.wait_running()
        w.page.wait_for_timeout(250)
        mine = w.page.evaluate(PIXELS)
        errs = list(w.errors)
        w.page.close()
        source = ("function draw() {\n  background(houseStyle.palette.ink)\n  codeAlong({ stages: %s, duration: 6, t: %s })\n}" %
                  (json.dumps([{"code": s["code"], "language": "javascript"} for s in py_stages]), t))
        theirs = js_still(browser, js_site, size, source)
        blank = js_still(browser, js_site, size, "function draw() { background(houseStyle.palette.ink) }")
        assert not errs, errs
        if mine != theirs:
            differ.append(t)
        elif theirs == blank:
            differ.append("%s: blank in both" % t)
        else:
            same += 1
    assert not differ, "%s: %s" % (shape, differ)
    assert same == 3


GOLD = """() => {
  const c = document.querySelector('[data-pyctures-src] canvas'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data
  let gold = 0, outside = 0, lit = 0
  const W = c.width, H = c.height, tall = H > W
  const side = tall ? 0.06 : 0.05, top = tall ? 0.14 : 0.05, bottom = tall ? 0.18 : 0.05
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = (y * W + x) * 4
    if (Math.abs(d[i] - 255) <= 8 && Math.abs(d[i + 1] - 215) <= 8 && d[i + 2] <= 8) gold++
    if (Math.abs(d[i] - 11) + Math.abs(d[i + 1] - 16) + Math.abs(d[i + 2] - 32) < 30) continue
    lit++
    if (x < W * side - 1 || x > W * (1 - side) + 1 || y < H * top - 1 || y > H * (1 - bottom) + 1) outside++
  }
  return { gold, outside, lit }
}"""


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_the_python_example_runs_its_stages_and_stays_in_the_safe_area(browser, pyctures_run, tmp_path, shape):
    """The example, held at a time in each stage: no circle before stage 2 is typed, a circle after, a bigger one in stage 3."""
    size = SHAPES[shape]
    source = (ROOT / "examples" / "code_along_circle.py").read_text()
    file = tmp_path / "along.py"
    file.write_text(source)
    server = pyctures_run(file)
    seen = {}
    for t in (2.6, 6.8, 10.0, 11.9):
        file.write_text("kinetic_time(%s, hold=True)\n%s" % (t, source))
        time.sleep(1.5)
        w = Watched(browser, server.url, size=size)
        w.wait_running()
        w.page.wait_for_timeout(300)
        seen[t] = w.page.evaluate(GOLD)
        assert not w.errors, w.errors
        w.page.close()
    assert seen[2.6]["gold"] == 0 and seen[6.8]["gold"] > 3000 and seen[10.0]["gold"] > 500 and seen[11.9]["gold"] > seen[10.0]["gold"] * 3, seen
    assert all(v["outside"] == 0 and v["lit"] > 3000 for v in seen.values()), seen
