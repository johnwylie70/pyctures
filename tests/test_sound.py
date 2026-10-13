"""Sound (`from synths import *`) and dials and a piano keyboard (`from pydials import *`) in a scene.

Real (headless) Chromium. A browser keeps a page silent until it has been touched, so each test
clicks the scene first. What is heard is read from the sound engine itself (the player's
`read()`: the wave it is putting out and how loud it is), never from what was asked for.

Needs Playwright; the tests of built pages need Pyodide's CDN too.
"""
import json
import time

import pytest

from conftest import EXAMPLES, ROOT, SHOTS
from test_browser import Watched, cdn_reachable

playwright = pytest.importorskip("playwright.sync_api")

BESIDE = ROOT.parent
needs_cdn = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")

TUNE = '''
from synths import *
play_notes("C4 E4 G4 C5 G4 E4", 0.2, repeat=True)
'''

# The owner's demo, and what Python knows of it, put where a test can read it.
PANEL = '''
from pyctures import *
from synths import *
from pydials import *

lead = make_synth("lead")
cutoff = dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
slider("attack", lead, "attack")
scope(lead)
piano = keyboard(lead, octave=4)

def update(dt):
    js.pyState = [lead.cutoff, cutoff.value, piano.notes]
'''

SCENE = "document.querySelector('[data-pyctures-src]').pycturesScene"
# What the engine is putting out now: how loud all of it is, and the notes one synth is sounding.
HEARD = """(id) => {
  const s = document.querySelector('[data-pyctures-src]').pycturesScene, p = s && s.sound && s.sound.player
  if (!p || !p.read) return { state: p ? p.state : null, level: 0, notes: [] }
  const all = p.read(), one = s.sound.read(id)
  return { state: p.state, kind: p.kind, level: Math.max(...all.level), wave: Math.max(0, ...Array.from(all.samples, Math.abs)), notes: Array.from(one.notes) }
}"""
# The controls on the scene, from the same dials.js the page loaded.
CONTROLS = """async () => {
  const { dials } = await import(new URL('pyctures/dials/dials.js', document.baseURI).href)
  const canvas = document.querySelector('[data-pyctures-src] canvas')
  const box = canvas.getBoundingClientRect()
  return dials(canvas).all.map((c) => ({ kind: c.kind, label: c.label, value: c.v, min: c.min, max: c.max, x: box.left + c.x, y: box.top + c.y, w: c.w, h: c.h }))
}"""


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        yield b
        b.close()


def write(tmp_path, source, name="scene.py"):
    scene = tmp_path / name
    scene.write_text(source)
    return scene


def build(tmp_path, source, html=False):
    from pyctures.build import build as make
    scene = write(tmp_path, source)
    out = tmp_path / ("scene.html" if html else "site")
    said = []
    make(scene, out, say=said.append)
    return out, said


def placed(page, timeout=10):
    """The controls once they have come to rest: the panel lays itself out again as plates wrap and the keyboard
    slides in, so where a control is counts only when two looks a moment apart agree."""
    end = time.time() + timeout
    last = None
    while True:
        now = page.evaluate(CONTROLS)
        if now and last is not None and [(c["x"], c["y"], c["w"], c["h"]) for c in now] == [(c["x"], c["y"], c["w"], c["h"]) for c in last]:
            return now
        assert time.time() < end, "the controls never came to rest"
        last = now
        page.wait_for_timeout(150)


def requests_of(page):
    asked = []
    page.on("request", lambda r: asked.append(r.url))
    return asked


def heard(page, id="s1"):
    return page.evaluate(HEARD, id)


def wait_for(page, test, what, timeout=10):
    end = time.time() + timeout
    while True:
        got = test()
        if got:
            return got
        assert time.time() < end, "never happened: %s" % what
        page.wait_for_timeout(50)


def listen(w, timeout=15):
    """Click the scene (a browser is silent until then), and wait until the engine is putting sound out."""
    w.page.mouse.click(400, 80)
    return wait_for(w.page, lambda: (lambda h: h if h["state"] == "on" and h["level"] > 0.02 and h["wave"] > 0.02 else None)(heard(w.page)),
                    "sound from the engine", timeout)


# ---------------------------------------------------------------- the copies

def test_the_libraries_carried_here_are_those_beside_this_repository():
    """Fails while a copy differs: run scripts/sync_libraries.py."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("sync_libraries", ROOT / "scripts" / "sync_libraries.py")
    sync = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync)
    from pyctures import pages
    compared = 0
    for (repo, name), copy in sync.COPIES.items():
        assert copy.is_file(), "%s is missing: run scripts/sync_libraries.py" % copy.name
        assert copy in pages.ASSETS.values(), "%s is not among the files a build is given" % copy.name
        source = sync.committed(BESIDE / repo, name) if (BESIDE / repo).is_dir() else None
        if source is not None:
            compared += 1
            assert copy.read_bytes() == source, "%s differs from %s/%s as last committed: run scripts/sync_libraries.py" % (copy.name, repo, name)
    if not compared:
        pytest.skip("the libraries are not beside this repository")


def test_the_handles_are_the_ones_the_libraries_use():
    import sys
    import pyctures
    assert (pyctures.H_SOUND, pyctures.H_DIALS) == (10, 11)
    js = (ROOT / "src" / "pyctures" / "web" / "pyctures.js").read_text()
    assert "H.set(10, sound)" in js and "H.set(11, panel)" in js
    sys.path.append(str(ROOT / "src" / "pyctures" / "web" / "synths"))
    try:
        import synths
        assert synths.H_SOUND == 10
    finally:
        sys.path.pop()


# ---------------------------------------------------------------- a scene without sound

def test_run_a_scene_without_sound_loads_nothing_new(browser, pyctures_run):
    server = pyctures_run(EXAMPLES / "star_catcher.py")
    page = browser.new_page()
    asked = requests_of(page)
    page.goto(server.url)
    page.wait_for_selector('[data-pyctures-status="running"]')
    page.mouse.click(200, 200)
    page.wait_for_timeout(800)
    assert sorted(u[len(server.url):] for u in asked) == ["", "pyctures/pyctures.js", "star_catcher.py"]
    assert page.evaluate(SCENE + ".sound.player") is None, "no player, and so no AudioContext, was made"
    assert page.evaluate("document.querySelector('.pyctures-cover').textContent") == ""


@needs_cdn
def test_build_a_scene_without_sound_loads_nothing_new(browser, static_server, tmp_path):
    from pyctures.build import build as make
    out = tmp_path / "site"
    make(EXAMPLES / "star_catcher.py", out, say=lambda *a: None)
    url = static_server(out)
    page = browser.new_page()
    asked = requests_of(page)
    page.goto(url)
    page.wait_for_selector('[data-pyctures-status="running"]', timeout=60000)
    page.wait_for_timeout(800)
    ours = sorted(u[len(url):] for u in asked if u.startswith(url))
    assert ours == ["", "pyctures/pyctures.js", "pyctures/pyctures.py", "star_catcher.py"]
    assert not [u for u in asked if "synths" in u or "dials" in u]
    # ...and one .html file for it carries neither library.
    single = tmp_path / "one.html"
    make(EXAMPLES / "star_catcher.py", single, say=lambda *a: None)
    text = single.read_text()
    assert '"synths":' not in text and '"dials":' not in text


# ---------------------------------------------------------------- sound

def test_run_a_tune_is_heard(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, TUNE))
    w = Watched(browser, "about:blank")
    asked = requests_of(w.page)
    # Silent until the page is touched, and it says so over the scene. (Nothing is asked of the page until it has
    # said so: to this browser, a test's question counts as a touch.)
    with w.page.expect_console_message(lambda m: "waiting for a tap" in m.text, timeout=20000):
        w.page.goto(server.url)
    assert w.page.evaluate("document.querySelector('.pyctures-cover').textContent") == "Click, tap or press a key to turn the sound on"
    assert heard(w.page)["state"] == "waiting" and heard(w.page)["level"] == 0
    got = listen(w)
    assert got["kind"] == "worklet", "the engine runs on the audio thread"
    assert w.page.evaluate("document.querySelector('.pyctures-cover').textContent") == ""
    assert not w.errors, w.errors
    assert not [u for u in asked if "dials" in u], "a scene with sound alone does not load the dials"


@needs_cdn
@pytest.mark.parametrize("html", [False, True], ids=["folder", "one file"])
def test_build_a_tune_is_heard(browser, static_server, tmp_path, html):
    out, said = build(tmp_path, TUNE, html=html)
    if html:
        assert "with synths" in said[0] and "dials" not in said[0]
        w = Watched(browser, static_server(tmp_path) + "scene.html")
    else:
        assert (out / "pyctures" / "synths" / "synths_core.wasm").is_file()
        w = Watched(browser, static_server(out))
    asked = requests_of(w.page)
    w.wait_running()
    assert w.page.evaluate(SCENE + ".transport.label") == "Python in a worker"
    got = listen(w, timeout=30)
    assert got["kind"] == "worklet"
    assert not w.errors, w.errors
    if html:
        assert not [u for u in asked if u.startswith("http://localhost") and not u.endswith("scene.html")], "one file: nothing beside it is fetched"


def test_a_sound_effect_at_the_tap_itself_is_heard(browser, pyctures_run, tmp_path):
    """Sound asked for in an event handler goes with that call's reply, and the sound the first tap asks for is heard."""
    server = pyctures_run(write(tmp_path, '''
from synths import *
def on_mouse_down(x, y):
    play_sound("explosion")
def draw():
    background("navy")
'''))
    w = Watched(browser, server.url)
    w.wait_running()
    assert w.page.evaluate(SCENE + ".sound.player") is None, "nothing is loaded until a sound is asked for"
    listen(w)
    assert not w.errors, w.errors


def test_two_scenes_on_a_page_share_one_player_and_keep_their_own_synths(browser, pyctures_run, tmp_path):
    """Each scene chooses its own ids, so both have a synth "s1". They are one sound card, and stopping one leaves the other."""
    for name, note in (("low.py", "C3"), ("high.py", "G5")):
        write(tmp_path, 'from synths import *\nlead = make_synth("organ")\nlead.start("%s")\ndef draw():\n    background("black")\n' % note, name)
    (tmp_path / "index.html").write_text(
        '<!doctype html><html><body><div data-pyctures-src="low.py" style="height:200px"></div>'
        '<div data-pyctures-src="high.py" style="height:200px"></div>'
        '<script type="module" src="/pyctures/pyctures.js"></script></body></html>')
    server = pyctures_run(tmp_path)
    w = Watched(browser, server.url)
    w.wait_running(2)
    w.page.mouse.click(100, 100)
    notes = "() => [...document.querySelectorAll('[data-pyctures-src]')].map((el) => Array.from(el.pycturesScene.sound ? el.pycturesScene.sound.read('s1').notes : []))"
    wait_for(w.page, lambda: w.page.evaluate(notes) == [[48], [79]], "each scene's own note on its own s1")
    assert w.page.evaluate("(() => { const [a, b] = [...document.querySelectorAll('[data-pyctures-src]')].map((el) => el.pycturesScene.sound); return a.player === b.player && a.scope !== b.scope })()")
    w.page.evaluate("document.querySelector('[data-pyctures-src]').pycturesScene.stop()")
    wait_for(w.page, lambda: w.page.evaluate(notes) == [[], [79]], "the first scene's note is gone, and the second's plays on")
    assert not w.errors, w.errors


def test_run_a_song_is_heard(browser, pyctures_run, tmp_path):
    """A song in synths' own format, with the WAV files it names: Python has them, and sends them with it."""
    import shutil
    songs = BESIDE / "synths.js" / "examples" / "songs"
    if not (songs / "night_drive.json").is_file():
        pytest.skip("the example song of synths.js is not beside this repository")
    shutil.copytree(songs, tmp_path / "songs")
    server = pyctures_run(write(tmp_path, 'from synths import *\nsong = play_song("songs/night_drive.json")\ndef draw():\n    background("black")\n'))
    w = Watched(browser, server.url)
    asked = requests_of(w.page)
    w.wait_running()
    listen(w)
    assert not [u for u in asked if "/songs/" in u], "nothing of the song was fetched: Python sent it"
    assert not w.errors, w.errors


# ---------------------------------------------------------------- the synth panel

def drag_the_dial_and_play_a_key(w):
    page = w.page
    made = placed(page)
    assert [(c["kind"], c["label"]) for c in made] == [("dial", "cutoff"), ("dial", "resonance"), ("slider", "attack"),
                                                        ("scope", ""), ("keyboard", "")]
    dial, attack, piano = made[0], made[2], made[4]
    # Each control took its range and where it stands from the synth in the page.
    assert (dial["min"], dial["max"], dial["value"]) == (20, 20000, 2800)
    assert made[1]["value"] == 0.25 and attack["value"] == 0.01
    wait_for(page, lambda: page.evaluate("window.pyState") == [2800, 2800, []], "Python is told where the dial stands")

    # A drag on the dial reaches the synth in the page, and then Python.
    x, y = dial["x"] + dial["w"] / 2, dial["y"] + dial["h"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, y + 60, steps=6)
    page.mouse.up()
    now = page.evaluate(SCENE + ".sound.synth('s1').get('cutoff')")
    assert 20 <= now < 2000, "the dial turned the synth's cutoff down (it is %s)" % now
    assert page.evaluate(CONTROLS)[0]["value"] == pytest.approx(now)
    wait_for(page, lambda: page.evaluate("window.pyState")[:2] == pytest.approx([now, now]), "lead.cutoff reads what the dial says")

    # A key pressed with the mouse sounds, and stops when it is let go.
    key = (piano["x"] + 20, piano["y"] + piano["h"] - 20)
    page.mouse.move(*key)
    page.mouse.down()
    got = wait_for(page, lambda: (lambda h: h if h["notes"] == [60] and h["level"] > 0.02 else None)(heard(page)), "the key's note from the engine")
    assert got["state"] == "on"
    wait_for(page, lambda: page.evaluate("window.pyState")[2] == [60], "Python is told which key is held")
    page.mouse.up()
    wait_for(page, lambda: heard(page)["notes"] == [], "the note is let go")
    wait_for(page, lambda: page.evaluate("window.pyState")[2] == [], "Python is told the key came up")
    # The computer's keys play it too: A is the first white key.
    page.keyboard.down("a")
    wait_for(page, lambda: heard(page)["notes"] == [60], "a note from the computer's keyboard")
    page.keyboard.up("a")
    wait_for(page, lambda: heard(page)["notes"] == [], "the note is let go")
    assert not w.errors, w.errors


def test_run_the_synth_panel(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, PANEL))
    w = Watched(browser, server.url, size=(900, 600))
    w.wait_running()
    drag_the_dial_and_play_a_key(w)
    SHOTS.mkdir(exist_ok=True)
    w.page.screenshot(path=str(SHOTS / "run-synth_panel.png"))


@needs_cdn
def test_build_the_synth_panel(browser, static_server, tmp_path):
    out, _ = build(tmp_path, PANEL)
    w = Watched(browser, static_server(out), size=(900, 600))
    w.wait_running()
    drag_the_dial_and_play_a_key(w)


@needs_cdn
def test_build_the_synth_panel_as_one_file(browser, static_server, tmp_path):
    out, said = build(tmp_path, PANEL, html=True)
    assert "with synths, with pydials" in said[0]
    w = Watched(browser, static_server(tmp_path) + "scene.html", size=(900, 600))
    w.wait_running()
    w.page.mouse.move(30, 580)       # the first white key
    w.page.mouse.down()
    wait_for(w.page, lambda: heard(w.page)["notes"] == [60] and heard(w.page)["level"] > 0.02, "the key's note from the engine", 30)
    w.page.mouse.up()
    assert not w.errors, w.errors


def test_keys_and_dials_do_not_wait_for_python(browser, pyctures_run, tmp_path):
    """Python here takes half a second over every frame. A key still sounds at once: the page plays it."""
    server = pyctures_run(write(tmp_path, PANEL + '''
import time
def draw():
    time.sleep(0.5)
'''))
    w = Watched(browser, server.url, size=(900, 600))
    w.wait_running()
    page = w.page
    wait_for(page, lambda: len(page.evaluate(CONTROLS)) == 5, "the controls", 30)
    page.mouse.click(450, 300)           # the first touch turns the sound on
    page.keyboard.down("a")
    page.keyboard.up("a")
    wait_for(page, lambda: heard(page)["state"] == "on", "sound on")
    page.wait_for_timeout(700)
    took = page.evaluate("""async () => {
      const s = document.querySelector('[data-pyctures-src]').pycturesScene, p = s.sound.player
      const frames = s.r.sent
      const canvas = s.canvas, box = canvas.getBoundingClientRect()
      const at = { clientX: box.left + 30, clientY: box.bottom - 20, pointerId: 7, pointerType: 'mouse', button: 0, bubbles: true }
      const t0 = performance.now()
      canvas.dispatchEvent(new PointerEvent('pointerdown', at))
      while (!s.sound.read('s1').notes.includes(60) && performance.now() - t0 < 2000) await new Promise((r) => setTimeout(r, 5))
      const ms = performance.now() - t0
      window.dispatchEvent(new PointerEvent('pointerup', at))
      return { ms, frames: s.r.sent - frames }
    }""")
    assert took["ms"] < 250, "the note took %d ms to sound" % took["ms"]
    assert took["frames"] <= 1, "and did not wait for a frame from Python"


POLICY = "default-src 'self'; script-src 'self' blob: 'wasm-unsafe-eval'; worker-src blob:; style-src 'unsafe-inline'; connect-src 'self' ws://localhost:*"


def test_no_eval_is_needed(browser, pyctures_run, tmp_path):
    """Under a policy that allows no eval and no script from elsewhere, the panel is made and plays."""
    write(tmp_path, PANEL)
    (tmp_path / "index.html").write_text(
        '<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="%s"></head>'
        '<body style="margin:0"><div data-pyctures-src="scene.py" data-pyctures-fullpage style="position:fixed;inset:0"></div>'
        '<script src="probe.js"></script><script type="module" src="/pyctures/pyctures.js"></script></body></html>' % POLICY)
    (tmp_path / "probe.js").write_text("try { window.evalWorks = new Function('return 1')() === 1 } catch (e) { window.evalWorks = false }")
    server = pyctures_run(tmp_path)
    page = browser.new_page(viewport={"width": 900, "height": 600})
    refused = []
    page.on("console", lambda m: refused.append(m.text) if "Content Security Policy" in m.text or m.type == "error" else None)
    page.on("pageerror", lambda e: refused.append(str(e)))
    page.goto(server.url)
    page.wait_for_selector('[data-pyctures-status="running"]')
    wait_for(page, lambda: len(page.evaluate(CONTROLS)) == 5, "the controls", 30)
    assert page.evaluate("window.evalWorks") is False, "the policy is in force: the page's own eval is refused"
    refused[:] = [r for r in refused if "probe.js" not in r and "'unsafe-eval'" not in r]     # that refusal is the test's own
    page.mouse.move(30, 580)
    page.mouse.down()
    wait_for(page, lambda: heard(page)["notes"] == [60] and heard(page)["level"] > 0.02, "the key's note from the engine")
    page.mouse.up()
    assert page.evaluate(SCENE + ".sound.player.kind") == "worklet"
    assert not refused, refused


# ---------------------------------------------------------------- a host

HOST_PAGE = '''<!doctype html>
<html><head><meta charset="utf-8"><script>window.PYCTURES_NO_AUTO = true; window.got = []</script></head>
<body><div id="scene" data-pyctures-src="scene.py" style="width:600px;height:400px"></div>
<script type="module">
import { mount } from "/pyctures/pyctures.js"
mount(document.getElementById("scene"), { fullPage: true,
  sound: { send(batch) { window.got.push({ batch, at: performance.now() / 1000 }) } } })
</script></body></html>
'''

TIMED = '''
import time
from synths import *
lead = make_synth("lead", cutoff=900)
drum = load_sample("kick.wav")
stamps = []
frames = 0

def update(dt):
    global frames
    frames += 1
    if frames % 10 == 0 and len(stamps) < 18:
        for i in range(3):          # three notes in one frame, a few thousandths of a second apart
            stamps.append(sound_time())
            lead.play(60 + i, 0.05)
            time.sleep(0.004)
    js.stamps = stamps

def draw():
    background("black")
'''


def test_a_host_takes_the_commands_on_the_page_s_clock(browser, pyctures_run, tmp_path):
    """`sound: { send }`: the host is given every batch and nothing is played or loaded here. Every time in
    a batch is on the page's clock, with the spacing the calls had in Python."""
    write(tmp_path, TIMED)
    (tmp_path / "kick.wav").write_bytes(b"RIFF\x04\x00\x00\x00WAVE")
    (tmp_path / "index.html").write_text(HOST_PAGE)
    server = pyctures_run(tmp_path)
    w = Watched(browser, server.url)
    asked = requests_of(w.page)
    w.wait_running()
    wait_for(w.page, lambda: len(w.page.evaluate("window.stamps || []")) == 18, "eighteen notes")
    w.page.wait_for_timeout(200)
    got = w.page.evaluate("window.got")
    stamps = w.page.evaluate("window.stamps")
    assert not [u for u in asked if "synths" in u], "the host plays it: synths.js is not loaded"
    assert w.page.evaluate(SCENE + ".sound.player") is None

    first = got[0]["batch"]
    assert first["synths"] == 1 and first["scope"] == "scene1" and [c["op"] for c in first["cmds"]] == ["synth", "sample", "synth"]
    assert first["cmds"][0] == {"op": "synth", "id": "s1", "preset": "lead", "set": {"cutoff": 900}, "t": first["cmds"][0]["t"]}
    assert first["cmds"][1]["bytes"] == "UklGRgQAAABXQVZF", "Python had the file, so it sent it"
    notes = []
    for g in got:
        batch = g["batch"]
        assert abs(batch["now"] - g["at"]) < 0.02, "a batch's `now` is the page's clock when it was handed over"
        for c in batch["cmds"]:
            assert batch["now"] - 0.5 < c["t"] <= batch["now"] + 0.001, "a command is timed a moment before its batch was sent"
        mine = [c["t"] for c in batch["cmds"] if c["op"] == "note"]
        if mine:
            assert len(mine) == 3, "a frame's sounds are one batch"
            notes.append(mine)
    assert len(notes) == 6
    asked_at = [stamps[i:i + 3] for i in range(0, 18, 3)]
    for there, here in zip(asked_at, notes):
        for i in (1, 2):
            # Inside a frame the spacing is Python's own, whenever the frame arrived (to a tenth of a millisecond
            # here: the scene reads the clock a moment before the note does).
            assert (here[i] - here[0]) == pytest.approx(there[i] - there[0], abs=0.0001)
            assert 0.003 < here[i] - here[i - 1] < 0.02
    # From frame to frame it holds too, once the two clocks have been lined up (the shortest journey seen).
    for a in range(3, 5):
        assert (notes[a + 1][0] - notes[a][0]) == pytest.approx(asked_at[a + 1][0] - asked_at[a][0], abs=0.004)

    # Stopping the scene tells the host that the scene's sound is finished with.
    w.page.evaluate(SCENE + ".stop()")
    wait_for(w.page, lambda: w.page.evaluate("window.got[window.got.length - 1].batch.cmds[0].op") == "close", "a close for the host")
    assert w.page.evaluate("window.got[window.got.length - 1].batch.scope") == "scene1"


def beep(path, seconds=0.5, rate=22050):
    """A WAV file: a sine wave at 440 Hz."""
    import math
    import struct
    import wave
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", int(20000 * math.sin(2 * math.pi * 440 * i / rate))) for i in range(int(seconds * rate))))


SAMPLE = '''
from synths import *
beep = load_sample("sounds/beep.wav", loop=True)
beep.play()
'''


def test_run_a_sample_is_sent_by_python(browser, pyctures_run, tmp_path):
    """Your own Python has the file (it may be on another computer than the page), so it sends it."""
    (tmp_path / "sounds").mkdir()
    beep(tmp_path / "sounds" / "beep.wav")
    server = pyctures_run(write(tmp_path, SAMPLE))
    w = Watched(browser, server.url)
    asked = requests_of(w.page)
    w.wait_running()
    listen(w)
    assert not [u for u in asked if u.endswith(".wav")]
    assert not w.errors, w.errors


PIANO = '''
from pyctures import *
from synths import *
from pydials import *

piano = load_samples(["sounds/beep-C4.wav", "sounds/beep-C5.wav"], crossfade=2)
rotary("wave", piano, "wave")
piano.play_notes("C4 E4 G4 C5", 0.2, repeat=True)

def update(dt):
    js.pyState = [piano.wave, len(piano.zones())]
'''


def test_several_recordings_are_one_instrument_that_is_heard(browser, pyctures_run, tmp_path):
    """load_samples: Python sends the files and the zones, the page's player makes the map, and it sounds. A control
    on its wave offers "sample", which it is on."""
    (tmp_path / "sounds").mkdir()
    for name in ("beep-C4.wav", "beep-C5.wav"):
        beep(tmp_path / "sounds" / name)
    server = pyctures_run(write(tmp_path, PIANO))
    w = Watched(browser, server.url)
    asked = requests_of(w.page)
    w.wait_running()
    listen(w)
    page = w.page
    assert page.evaluate("window.pyState") == ["sample", 2]
    zones = page.evaluate("%s.sound.player.target('s1', %s.sound.scope).get('zones')" % (SCENE, SCENE))
    assert [(z["file"], z["note"]) for z in zones] == [("sounds/beep-C4.wav", 60), ("sounds/beep-C5.wav", 72)], zones
    assert zones[0]["to"] + 1 >= zones[1]["from"], "the keys are shared out between the two"
    made = page.evaluate(CHOSEN)
    assert made["wave"]["choices"][-1] == "sample" and made["wave"]["on"] == "sample", made
    assert not [u for u in asked if u.endswith(".wav")], "Python had the files, and sent them"
    assert not w.errors, w.errors


ARPEGGIO = '''
from synths import *
set_tempo(240)
lead = make_synth("pluck")
lead.arp("Am", 30, step="sixteenth", octaves=2, gate=0.5)
'''


def test_a_musical_arpeggio_strikes_the_notes_of_its_chord_in_time(browser, pyctures_run, tmp_path):
    """lead.arp(..., step="sixteenth") from Python is played by the engine's arpeggiator: each step a note of its
    own, so the synth is heard sounding the notes of A minor through two octaves, one after another."""
    server = pyctures_run(write(tmp_path, ARPEGGIO))
    w = Watched(browser, server.url)
    w.wait_running()
    listen(w)
    page = w.page
    seen = set()

    def enough():
        seen.update(heard(page, "s1")["notes"])
        return len(seen) >= 5
    wait_for(page, enough, "five different notes of the arpeggio", 20)
    assert seen <= {69, 72, 76, 81, 84, 88}, seen       # A4 C5 E5 and the same an octave up
    assert not w.errors, w.errors


GATED = '''
from pyctures import *
from synths import *
set_tempo(240)
pad = make_synth("pad")
pad.trance_gate = "trance"
pad.set_trance_gate("x.x.xx.x", rate="sixteenth", depth=0.9)
pad.arp_pattern = [1, 0, 3, 2]
pad.arp("Am", 60, step="sixteenth")
held = pad.start("A2", bend="scoop", vibrato=True)

def update(dt):
    js.pyState = [pad.trance_gate, pad.arp_pattern, pad.trance_gate_step(), pad.arp_step(), pad.trance_gate_depth]
'''


def test_the_trance_gate_and_a_pattern_from_python_are_the_page_s_too(browser, pyctures_run, tmp_path):
    """pad.trance_gate and pad.arp_pattern travel as text, the page's own object for the synth describes each as a
    pattern (for a control), a control's change is sent on, and Python reads the step that is sounding a frame late."""
    server = pyctures_run(write(tmp_path, GATED))
    w = Watched(browser, server.url)
    w.wait_running()
    listen(w)
    page = w.page
    target = "%s.sound.synth('s1')" % SCENE
    gate = page.evaluate("%s.describe('trance_gate')" % target)
    assert gate["kind"] == "pattern" and gate["value"] == "x.x.xx.x" and gate["patterns"]["trance"] == "x.x.xx.xx.x.xx.x" and "named" not in gate, gate
    arp = page.evaluate("%s.describe('arpPattern')" % target)
    assert arp["value"] == "1 - 3 2" and arp["patterns"]["bounce"] == "1 2 3 2", arp
    assert page.evaluate("[%s.get('trance_gate'), %s.get('arp_pattern'), %s.get('trance_gate_depth'), %s.get('trance_gate_rate')]" % ((target,) * 4)) == ["x.x.xx.x", "1 - 3 2", 0.9, 4]
    assert page.evaluate("%s.sound.player.target('s1', %s.sound.scope).get('tranceGate')" % (SCENE, SCENE)) == "x.x.xx.x", "the player has it"
    # The steps move, in the page and in Python.
    seen, told = set(), set()

    def moving():
        seen.add(page.evaluate("%s.get('tranceGateStep')" % target))
        state = page.evaluate("window.pyState") or [0, 0, -1, -1, 0]
        told.add((state[2], state[3]))
        return len(seen - {-1}) >= 3 and len({a for a, b in told} - {-1}) >= 3 and len({b for a, b in told} - {-1}) >= 2
    wait_for(page, moving, "the gate's and the arpeggio's steps to move, in the page and in Python", 20)
    assert max(seen) <= 7 and max(b for a, b in told) <= 3, (seen, told)
    assert page.evaluate("window.pyState")[:2] == ["x.x.xx.x", "1 - 3 2"] and page.evaluate("window.pyState")[4] == 0.9
    # A control sets a pattern by name, and takes the gate away: the page's object and the player follow.
    page.evaluate("%s.set('trance_gate', 'pump')" % target)
    assert page.evaluate("%s.describe('trance_gate')" % target)["named"] == "pump"
    page.evaluate("%s.set('tranceGate', 'off')" % target)
    assert page.evaluate("[%s.get('trance_gate'), %s.get('trance_gate_depth')]" % (target, target)) == ["", 0]
    wait_for(page, lambda: page.evaluate("%s.sound.player.target('s1', %s.sound.scope).get('tranceGate')" % (SCENE, SCENE)) == "", "the player to drop the gate")
    assert not w.errors, w.errors


EDITORS = '''
from pyctures import *
from synths import *
from pydials import *
set_tempo(240)
pad = make_synth("pad")
pad.trance_gate = "trance"
lead = make_synth("lead")
lead.arp_pattern = "bounce"
gate = trance_gate("gate", pad)
arp = arp_pattern("arp", lead)
pad.start(["A3", "C4", "E4"])

def update(dt):
    js.pyState = [pad.trance_gate, gate.text, arp.text]
'''

# The two pattern editors, by their labels: the text each shows and the step it has lit.
EDITED = """async () => {
  const { dials } = await import(new URL('pyctures/dials/dials.js', document.baseURI).href)
  const out = {}
  for (const c of dials(document.querySelector('[data-pyctures-src] canvas')).all) if (c.kind === 'tranceGate' || c.kind === 'arpPattern') out[c.kind === 'tranceGate' ? 'gate' : 'arp'] = { text: c.text, step: c.step }
  return out
}"""


def test_the_pattern_editors_are_tied_to_a_python_synth(browser, pyctures_run, tmp_path):
    """trance_gate("gate", pad) and arp_pattern("arp", lead) from pydials show the synth's own patterns, light the step
    that is sounding, and follow a pattern the page's synth is given."""
    server = pyctures_run(write(tmp_path, EDITORS))
    w = Watched(browser, server.url, size=(900, 700))
    w.wait_running()
    listen(w)
    page = w.page
    wait_for(page, lambda: len(page.evaluate(EDITED)) == 2, "the two editors", 30)
    made = page.evaluate(EDITED)
    assert made["gate"]["text"] == "x.x.xx.xx.x.xx.x" and made["arp"]["text"] == "1 2 3 2", made
    lit = set()

    def moving():
        lit.add(page.evaluate(EDITED)["gate"]["step"])
        return len(lit - {-1, None}) >= 3
    wait_for(page, moving, "the gate's editor to light the step that is sounding", 20)
    # A pattern set on the page's synth (as another control would) is what the editor then shows: it asks again.
    page.evaluate("%s.sound.synth('s1').set('tranceGate', 'x...x...')" % SCENE)
    wait_for(page, lambda: page.evaluate(EDITED)["gate"]["text"] == "x...x...", "the editor to show the pattern the synth now has")
    assert page.evaluate("window.pyState")[2] == "1 2 3 2"
    assert not w.errors, w.errors


BUFFER = "from pyctures import *" + TUNE + '''
set_sound_buffer("large")

def update(dt):
    now = sound_buffer()
    js.pyState = [now["thread"], now["setting"], now["frames"], now["delay"], now["underruns"]]
'''


def test_the_sound_buffer_is_set_in_python_and_read_back(browser, pyctures_run, tmp_path):
    """set_sound_buffer travels to the page's player, and what the player says comes back with a frame. On the
    audio thread (this page is localhost's) the size is how far ahead everything is scheduled: 4096 frames."""
    server = pyctures_run(write(tmp_path, BUFFER))
    w = Watched(browser, server.url)
    w.wait_running()
    listen(w)
    page = w.page
    wait_for(page, lambda: (page.evaluate("window.pyState") or [None])[0] == "audio", "Python to be told the buffer")
    thread, setting, frames, delay, underruns = page.evaluate("window.pyState")
    assert (setting, frames, underruns) == (4096, 128, 0)
    assert abs(delay - 4096 / page.evaluate("%s.sound.player.context.sampleRate" % SCENE) * 1000) < 2, delay
    assert page.evaluate("%s.sound.player.buffer().setting" % SCENE) == 4096
    assert not w.errors, w.errors


LAID_OUT = '''
from pyctures import *
from synths import *
from pydials import *

lead = make_synth("lead")
bell = make_synth(sample=load_sample("sounds/beep.wav"), note="C4")
layout(wrap=False)
with group("lead"):
    rotary("wave", lead, "wave")
    select("picked", lead, "wave")
    with column():
        dial("pwm", lead, "pwm")
        dial("rate", lead, "pwm_rate")
    wrap()
    with grid(2):
        space = rotary("space", lead, "reverb_type")
        dial("decay", lead, "reverb_decay")
    spacer()
with row():
    label("bell")
    rotary("its wave", bell, "wave")
page("more")
dial("extra", 0, 1, 0.5)
page()
keyboard(lead)
given = []

def update(dt):
    # The sample is given once a hand has chosen the plate.
    if space.value == "plate" and not given:
        given.append(1)
        lead.sample = load_sample("sounds/beep.wav")
    area = room()
    js.pyState = [lead.wave, lead.reverb_type, area.width, area.height]
'''

# The controls that choose, by their labels: what each is, its choices, and the one it is on.
CHOSEN = """async () => {
  const { dials } = await import(new URL('pyctures/dials/dials.js', document.baseURI).href)
  const out = {}
  for (const c of dials(document.querySelector('[data-pyctures-src] canvas')).all) if (c.choices) out[c.label] = { kind: c.kind, choices: [...c.choices], on: c.choices[c.i] }
  return out
}"""


def test_a_wave_offers_a_sample_only_to_a_synth_that_has_one(browser, pyctures_run, tmp_path):
    """A rotary or a select on a synth's wave takes its choices from that synth: "sample" is one only once it has a
    sample, as synths.js has it. The scene is laid out with every way pydials has (group, row, column, grid, wrap,
    spacer, page, room), and a rotary on the reverb's type has its five choices and sets it for Python to read."""
    (tmp_path / "sounds").mkdir()
    beep(tmp_path / "sounds" / "beep.wav")
    server = pyctures_run(write(tmp_path, LAID_OUT))
    w = Watched(browser, server.url, size=(900, 700))
    w.wait_running()
    page = w.page
    wait_for(page, lambda: len(page.evaluate(CHOSEN)) == 4, "the rotaries and the select", 30)
    made = page.evaluate(CHOSEN)
    plain = ["sine", "triangle", "saw", "pulse"]
    assert made["wave"]["choices"] == plain and made["picked"]["choices"] == plain, made
    assert made["its wave"]["choices"] == plain + ["sample"] and made["its wave"]["on"] == "sample", made
    assert made["space"]["choices"] == ["room", "hall", "plate", "cathedral", "spring"] and made["space"]["on"] == "room", made
    assert {made[name]["kind"] for name in ("wave", "its wave", "space")} == {"rotary"} and made["picked"]["kind"] == "select", made
    assert [c["label"] for c in page.evaluate(CONTROLS) if c["kind"] == "dial"] == ["pwm", "rate", "decay", "extra"]
    wait_for(page, lambda: (page.evaluate("window.pyState") or [0, 0, 0, 0])[2] > 0, "Python to be told the room the controls leave")
    # A hand turns the rotary to the plate: the page sets it at once, and Python reads it with the next frame.
    page.evaluate("""async () => {
      const { dials } = await import(new URL('pyctures/dials/dials.js', document.baseURI).href)
      const space = dials(document.querySelector('[data-pyctures-src] canvas')).all.find((c) => c.label === 'space')
      space.i = 2
      space.changed('plate')
    }""")
    assert page.evaluate("%s.sound.synth('s1').get('reverb_type')" % SCENE) == "plate"
    wait_for(page, lambda: page.evaluate("window.pyState")[1] == "plate", "Python to read the reverb's type")
    # Python then gives the synth a sample, and its controls gain the choice without being made again.
    wait_for(page, lambda: page.evaluate(CHOSEN)["wave"]["choices"] == plain + ["sample"], "the wave to offer the sample")
    assert page.evaluate(CHOSEN)["picked"]["choices"] == plain + ["sample"]
    assert page.evaluate("%s.sound.synth('s1').get('wave')" % SCENE) == "sample"
    # And they turn to it, since the wave was changed in code.
    wait_for(page, lambda: [page.evaluate(CHOSEN)[name]["on"] for name in ("wave", "picked")] == ["sample", "sample"], "both to turn to the sample")
    assert page.evaluate("%s.sound.synth('s1').describe('wave').aliases" % SCENE)["square"] == "pulse"
    assert not w.errors, w.errors


@needs_cdn
@pytest.mark.parametrize("html", [False, True], ids=["folder", "one file"])
def test_build_takes_a_scene_s_sound_files_along(browser, static_server, tmp_path, html):
    """A browser's Python has only the files it was given. In a folder the file is copied beside the scene and
    the page is asked to fetch it; one .html file carries it inside, and Python sends it."""
    (tmp_path / "sounds").mkdir()
    beep(tmp_path / "sounds" / "beep.wav")
    out, said = build(tmp_path, SAMPLE, html=html)
    if html:
        assert "with 1 sound file: sounds/beep.wav" in "\n".join(said)
        w = Watched(browser, static_server(tmp_path) + "scene.html")
    else:
        assert (out / "sounds" / "beep.wav").is_file()
        w = Watched(browser, static_server(out))
    asked = requests_of(w.page)
    w.wait_running()
    listen(w, timeout=30)
    assert bool([u for u in asked if u.endswith("sounds/beep.wav")]) is not html
    assert not w.errors, w.errors
