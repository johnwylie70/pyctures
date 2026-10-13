"""Effects: `from pyvisualfx import *` (the library pyvisualfx, whose page half is visualfx.js, handle 13).

In a real (headless) Chromium, run by `pyctures run`: a scene that imports no effects is sent nothing; one that
does has its effects on in the page, run once for each frame Python sends on the dt the scene is given; a change
of scene is seen through the effects; and what `pyctures build` writes, with its size with and without them.
The effects' own pixels are measured in their own repository (visualfx.js).
"""
import json
import textwrap

import pytest

import pyctures
from pyctures import build as builder
from test_browser import Watched

sync_api = pytest.importorskip("playwright.sync_api")

SCENE = "document.querySelector('[data-pyctures-src]').pycturesScene"
PIPE = "(document.querySelector('[data-pyctures-src] canvas') || {})[Symbol.for('effects.pipeline')]"
LAYERS = """[...document.querySelectorAll('[data-pyctures-src] canvas')].map((c, i) => i === 0 ? 'scene' : c.dataset.effectsLayer !== undefined ? 'effects'
  : c.dataset.dialsLayer !== undefined ? 'dials' : c.dataset.pycturesTransition !== undefined ? 'transition' : 'other').join()"""
# The colour in the middle of the effects' picture, read at the moment a frame's picture is there.
READ = """() => new Promise((done) => { const pipe = %s; pipe.api.onFrame((fx) => { pipe.api.onFrame(null); const p = fx.pixels(), i = (100 * p.width + 150) * 4
  done({ colour: [p.data[i], p.data[i + 1], p.data[i + 2]], layers: %s }) }) })""" % (PIPE, LAYERS)


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"])
        yield b
        b.close()


def run(browser, pyctures_run, tmp_path, source, name="scene.py"):
    file = tmp_path / name
    file.write_text(textwrap.dedent(source))
    asked = []
    w = Watched(browser, pyctures_run(file).url, size=(300, 200))
    w.page.on("request", lambda r: asked.append(r.url))
    w.wait_running()
    return w, asked


def near(a, b, by=5):
    return all(abs(x - y) <= by for x, y in zip(a, b))


# ---------------------------------------------------------------- the Python half and the handle

def test_the_frame_s_seconds_are_kept_for_a_library_and_only_for_a_frame():
    info = json.dumps({"width": 400, "height": 300, "pixel_ratio": 1})
    seen = []
    pyctures.start("def update(dt):\n    pass\n", info)
    pyctures.S.ending.append(lambda: seen.append(pyctures.S.dt))
    pyctures.tick(json.dumps({"dt": 0.04}))
    pyctures.tick(json.dumps({"dt": 0.02}))
    assert seen == [0.04, 0.02] and pyctures.S.dt is None
    assert pyctures.H_EFFECTS == 13 and pyctures.H_EFFECTS not in (pyctures.H_SOUND, pyctures.H_DIALS, 12)


# ---------------------------------------------------------------- in a browser

def test_a_scene_that_imports_no_effects_is_sent_none(browser, pyctures_run, tmp_path):
    w, asked = run(browser, pyctures_run, tmp_path, '''
        def draw():
            background("navy")
            circle(100, 100, 30, "gold")
        ''')
    w.page.wait_for_timeout(400)
    assert not [a for a in asked if "visualfx" in a]
    assert w.page.evaluate(LAYERS) == "scene"
    assert not w.errors


def test_effects_are_on_in_the_page_and_run_once_a_frame_on_pythons_clock(browser, pyctures_run, tmp_path):
    w, asked = run(browser, pyctures_run, tmp_path, '''
        from pyvisualfx import *
        t = 0
        frames = 0
        mirror("four")
        soft = blur(6)
        shine = glow(0.5, radius=20)
        shine.off()

        def update(dt):
            global t, frames
            t += dt
            frames += 1
            js.pyClock = [t, frames]
            if frames == 5:
                soft.radius = 10

        def draw():
            background("black")
            circle(120, 90, 40, "gold")
        ''')
    w.page.wait_for_function("window.pyClock && window.pyClock[1] > 12 && %s" % PIPE)
    got = w.page.evaluate("""() => new Promise((done) => { const pipe = %s; pipe.api.onFrame((fx) => { pipe.api.onFrame(null)
      done({ stats: fx.stats(), clock: window.pyClock, effects: pipe.effects.map((e) => [e.name, e.active, e.values.radius ?? null]), layers: %s }) }) })""" % (PIPE, LAYERS))
    assert got["effects"] == [["mirror", True, None], ["blur", True, 10], ["glow", False, 20]]
    assert got["layers"] == "scene,effects"
    # Once for each of Python's frames (the page may be a frame ahead of what Python last said), on Python's dt.
    assert abs(got["stats"]["frames"] - got["clock"][1]) <= 1 and abs(got["stats"]["time"] - got["clock"][0]) < 0.11 and got["clock"][0] > 0
    # The page's half is the copy Pyctures carries, asked for by the page: Python sent no library.
    assert [a for a in asked if a.endswith("/pyctures/visualfx/visualfx.js")]
    assert not w.errors


def test_a_change_of_scene_is_seen_through_the_effects(browser, pyctures_run, tmp_path):
    w, _ = run(browser, pyctures_run, tmp_path, '''
        from pyvisualfx import *
        invert()

        class Red(Scene):
            def draw(self):
                background("rgb(255,0,0)")
            def on_key_down(self, key):
                go("Blue", transition="crossfade", transition_time=60)

        class Blue(Scene):
            def draw(self):
                background("rgb(0,0,255)")
        ''')
    w.page.wait_for_function(SCENE + ".stage.name === 'Red' && " + PIPE)
    before = w.page.evaluate(READ)
    w.page.keyboard.press("a")
    w.page.wait_for_function(SCENE + ".stage.running && " + SCENE + ".stage.name === 'Blue'")
    seen = []
    for p in (0, 0.5, 1):
        w.page.evaluate("(p) => %s.stage.running.hold(p)" % SCENE, p)
        w.page.wait_for_timeout(250)
        seen.append(w.page.evaluate(READ))
    # Inverted: red is cyan, blue is yellow, and half of each is a pale green. The effects are over both pictures.
    assert near(before["colour"], [0, 255, 255]) and before["layers"] == "scene,effects"
    assert near(seen[0]["colour"], [0, 255, 255]), seen
    assert near(seen[1]["colour"], [128, 255, 128], 6), seen
    assert near(seen[2]["colour"], [255, 255, 0]), seen
    assert seen[1]["layers"] == "scene,transition,effects"
    assert not w.errors


def test_a_3d_scenes_slide_is_seen_through_the_effects(browser, pyctures_run, tmp_path):
    """A slide in 3D is all in the transition's own pixels (the page keeps a copy of each frame the new scene sends),
    so half way the old scene is on the left and the new on the right, both with the effects on them."""
    w, _ = run(browser, pyctures_run, tmp_path, '''
        from pyvisualfx import *
        invert()
        renderer = THREE.WebGLRenderer(canvas=canvas)
        camera = THREE.PerspectiveCamera()

        class Red(Scene):
            def setup(self):
                self.world = THREE.Scene()
                self.world.background = THREE.Color("rgb(255,0,0)")
            def draw(self):
                renderer.render(self.world, camera)
            def on_key_down(self, key):
                go("Blue", transition="slide_left", transition_time=60)

        class Blue(Scene):
            def setup(self):
                self.world = THREE.Scene()
                self.world.background = THREE.Color("rgb(0,0,255)")
            def draw(self):
                renderer.render(self.world, camera)
        ''')
    read = """() => new Promise((done) => { const pipe = %s; pipe.api.onFrame((fx) => { pipe.api.onFrame(null); const p = fx.pixels()
      const at = (x) => { const i = (Math.floor(p.height / 2) * p.width + Math.floor(p.width * x)) * 4; return [p.data[i], p.data[i + 1], p.data[i + 2]] }
      done({ left: at(0.25), right: at(0.75), layers: %s, moved: document.querySelector('[data-pyctures-src] canvas').style.transform }) }) })""" % (PIPE, LAYERS)
    w.page.wait_for_function(SCENE + ".stage.name === 'Red' && " + PIPE)
    w.page.wait_for_timeout(400)
    before = w.page.evaluate(read)
    w.page.keyboard.press("a")
    w.page.wait_for_function(SCENE + ".stage.running && " + SCENE + ".stage.name === 'Blue'")
    w.page.evaluate("%s.stage.running.hold(0.5)" % SCENE)
    w.page.wait_for_timeout(400)
    half = w.page.evaluate(read)
    assert near(before["left"], [0, 255, 255]), before
    assert near(half["left"], [0, 255, 255], 6) and near(half["right"], [255, 255, 0], 6), half
    assert half["layers"] == "scene,transition,effects" and not half["moved"], half
    assert not w.errors


def test_a_song_that_is_playing_moves_the_effects_music(browser, pyctures_run, tmp_path):
    """A tracker song (synths.js's own example, from the repository beside this one) is the music with nothing said:
    the page's numbers move, and Python is told them."""
    import shutil
    from conftest import ROOT
    song = ROOT.parent / "synths.js" / "examples" / "songs" / "night_drive.json"
    if not song.is_file():
        pytest.skip("no song beside this repository")
    shutil.copyfile(song, tmp_path / "night_drive.json")
    w, _ = run(browser, pyctures_run, tmp_path, '''
        from synths import *
        from pyvisualfx import *
        song = play_song("night_drive.json")
        shine = glow(0.3)
        react(shine, "strength", "bass", 0.3, 1.5)
        most = 0

        def draw():
            global most
            background("black")
            most = max(most, bass(), loudness())
            js.pyMost = most
            circle(150, 100, 20 + 60 * bass(), "gold")
        ''')
    w.page.wait_for_function(PIPE)
    w.page.mouse.click(150, 100)
    w.page.evaluate("""() => { window.most = { bass: 0, loudness: 0, strength: 0 }; const pipe = %s
      setInterval(() => { const l = pipe.listener, m = window.most; m.bass = Math.max(m.bass, l.bass); m.loudness = Math.max(m.loudness, l.loudness)
        m.strength = Math.max(m.strength, pipe.effects[0].get('strength')) }, 30) }""" % PIPE)
    w.page.wait_for_function("window.most.loudness > 0.5 && window.most.bass > 0.3 && window.pyMost > 0.3", timeout=30000)
    got = w.page.evaluate("window.most")
    # The glow's strength is tied to the bass in the page: it has been above where it starts.
    assert got["strength"] > 0.6, got
    assert not w.errors


def test_one_channel_of_a_song_cannot_be_listened_to_from_python_and_says_so(tmp_path):
    """A song's channel is a reading Python is sent, not an object in the page, so there is nothing for the page's
    effects to listen to. It is said plainly; all the sound (the default) and a synth can be listened to."""
    import sys
    import types
    sys.path.insert(0, str(next(p for p in (__import__("conftest").ROOT / "src" / "pyctures" / "web" / "visualfx",))))
    import pyvisualfx
    with pytest.raises(ValueError, match="makes sound in the page"):
        pyvisualfx.listen_to(types.SimpleNamespace(level=lambda: 0.5, samples=lambda: []))


# ---------------------------------------------------------------- built pages

def test_a_single_file_page_carries_the_effects_only_for_a_scene_that_imports_them(tmp_path):
    plain = tmp_path / "plain.py"
    plain.write_text('def draw():\n    background("navy")\n    circle(100, 100, 30, "gold")\n')
    shiny = tmp_path / "shiny.py"
    shiny.write_text('from pyvisualfx import *\nglow(1)\n\ndef draw():\n    background("navy")\n    circle(100, 100, 30, "gold")\n')
    sizes = {}
    for scene in (plain, shiny):
        out = tmp_path / (scene.stem + ".html")
        builder.build(scene, out, say=lambda *a: None)
        text = out.read_text()
        sizes[scene.stem] = len(text.encode())
        assert ('"visualfx": {"js"' in text) == (scene is shiny)
    # A page with no effects is as small as it was: under 200 kB. The effects are about 130 kB of text more.
    assert sizes["plain"] < 200_000, sizes
    assert 100_000 < sizes["shiny"] - sizes["plain"] < 220_000, sizes
    print("single-file page: %d bytes without effects, %d with" % (sizes["plain"], sizes["shiny"]))


def test_a_built_page_runs_a_scene_with_effects_in_the_browsers_own_python(browser, static_server, tmp_path):
    scene = tmp_path / "shiny.py"
    scene.write_text('from pyvisualfx import *\ninvert()\n\ndef draw():\n    background("rgb(255,0,0)")\n')
    out = tmp_path / "shiny.html"
    builder.build(scene, out, say=lambda *a: None)
    w = Watched(browser, static_server(tmp_path) + out.name, size=(300, 200))
    w.page.wait_for_function(PIPE + " && " + PIPE + ".frames > 3", timeout=90000)
    got = w.page.evaluate(READ)
    assert near(got["colour"], [0, 255, 255]) and got["layers"] == "scene,effects"
    assert not w.errors


def test_the_page_of_every_effect_is_what_the_table_of_effects_gives():
    """Fails while docs/effects-reference.md differs from the table, or a picture is missing: run scripts/effects_docs.py."""
    import subprocess
    import sys
    from conftest import ROOT
    done = subprocess.run([sys.executable, str(ROOT / "scripts" / "effects_docs.py"), "--check"], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout
