"""A scene that a recorder gives one frame at a time: `mount(el, { stepped: { fps } })` and `await scene.step()`.

A video recorder wants every frame exactly 1/fps after the last, however long Python and the drawing took, and the
sound in step with the pictures. So the scene's time is the recorder's (`vt`), in Python and in the page, and the
sound is made a frame at a time by a player with no sound card (synths.js's stepped player).

The first tests need no browser. The others film a clapperboard in headless Chromium, with this computer's
Python behind `pyctures run`, and compare the pictures with the samples; they are skipped while the copies of
synths.js and synths.py that Pyctures keeps have no stepped player and no stepped clock.
"""
import json
import sys
import textwrap

import pytest

import pyctures
from conftest import ROOT

WEB = ROOT / "src" / "pyctures" / "web"
INFO = {"width": 320, "height": 180, "pixel_ratio": 1}


def test_a_stepped_scene_s_time_is_the_recorder_s():
    scene = textwrap.dedent('''
        print("began")
        await sleep(0.1)
        print("woke")
    ''')
    try:
        first = json.loads(pyctures.start(scene, json.dumps(dict(INFO, vt=0.0))))
        assert first["error"] is None and first["out"] == "began\n" and pyctures.S.vt == 0.0
        # Three frames at thirty a second, asked for with no wait at all between them: a tenth of a second has
        # gone by on the recorder's clock, and that is the one sleep() goes by.
        said = [json.loads(pyctures.tick(json.dumps({"dt": 1 / 30, "vt": n / 30})))["out"] for n in (1, 2, 3)]
        assert said == ["", "", "woke\n"]
    finally:
        pyctures.stop()


def test_without_a_recorder_time_is_the_computer_s():
    scene = 'await sleep(0.1)\nprint("woke")\n'
    try:
        first = json.loads(pyctures.start(scene, json.dumps(INFO)))
        assert first["error"] is None and pyctures.S.vt is None
        said = [json.loads(pyctures.tick(json.dumps({"dt": 1 / 30})))["out"] for n in (1, 2, 3)]
        assert said == ["", "", ""]
    finally:
        pyctures.stop()


# ---------------------------------------------------------------- in a browser

CLAP = '''
from synths import *

set_tempo(120)
beep = make_synth(wave="sine", filter="off", attack=0, decay=0, sustain=1, release=0, volume=1)
n = 0
seen = []

def update(dt):
    seen.append([dt, sound_time(), beat()])
    js.pySeen = seen

def draw():
    global n
    background("white" if n % 30 == 0 else "black")
    if n % 30 == 0:
        beep.play("A5", 0.01)
    n += 1
'''

PAGE = '''<!doctype html><meta charset="utf-8"><body style="margin:0;background:#000">
<div id="s" style="width:320px;height:180px"></div>
<script>window.PYCTURES_NO_AUTO = true</script>
<script type="module">
import { mount } from "/pyctures/pyctures.js"
window.film = async (fps, frames) => {
  const scene = mount(document.getElementById("s"), { src: "clap.py", stepped: { fps }, server: true })
  await scene.ready
  const g = scene.canvas.getContext("2d"), white = [], parts = []
  // Frame 0 is what the scene drew as it started; every other frame is one step.
  for (let f = 0; f < frames; f++) {
    if (f) await scene.step()
    if (window.slow) await new Promise((done) => setTimeout(done, window.slow))
    parts.push(scene.sound.take())
    if (g.getImageData(5, 5, 1, 1).data[0] > 128) white.push(f)
  }
  await scene.sound.stepTo(frames / fps)
  parts.push(scene.sound.take())
  const left = new Float32Array(parts.reduce((n, p) => n + (p ? p.length : 0), 0))
  let at = 0
  for (const p of parts) if (p) { left.set(p.left, at); at += p.length }
  const starts = []
  let quiet = 300
  for (let i = 0; i < left.length; i++) { if (Math.abs(left[i]) > 1e-4) { if (quiet >= 300) starts.push(i); quiet = 0 } else quiet++ }
  const player = scene.sound.player
  return { white, starts, total: left.length, each: parts.slice(1).map((p) => (p ? p.length : 0)), kind: player && player.kind, context: player && player.context, status: scene.status, errors: scene.errors, seen: Array.from(window.pySeen || [], (row) => Array.from(row)) }
}
</script>
'''


@pytest.fixture(scope="module")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        yield b
        b.close()


def stepped_copies():
    """Whether the copies Pyctures keeps can do it: synths.js with a stepped player, synths.py that reads the scene's stepped time."""
    if "createSteppedPlayer" not in (WEB / "synths" / "synths.js").read_text(encoding="utf-8"):
        return False
    sys.path.append(str(WEB / "synths"))
    import synths
    return hasattr(synths._Frames, "clock")


@pytest.mark.parametrize("fps", [60, 30])
def test_a_stepped_scene_s_sound_is_on_its_frames(browser, pyctures_run, tmp_path, fps):
    if not stepped_copies():
        pytest.skip("the copies of synths.js and synths.py here have no stepped player yet (scripts/sync_libraries.py brings them in)")
    (tmp_path / "clap.py").write_text(CLAP)
    (tmp_path / "film.html").write_text(PAGE)
    p = pyctures_run(tmp_path)
    page = browser.new_page(viewport={"width": 400, "height": 300})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(p.url + "film.html")
    page.wait_for_function("() => typeof window.film === 'function'")
    frames = fps * 3
    got = page.evaluate("([fps, frames]) => window.film(fps, frames)", [fps, frames])
    assert not errors and not got["errors"] and got["status"] == "running"
    # A player with no sound card, and so no tap needed first.
    assert got["kind"] == "stepped" and got["context"] is None
    # The picture is white on every thirtieth frame, and a note begins on the first sample of each of those frames.
    assert got["white"] == list(range(0, frames, 30))
    assert got["starts"] == [round(f * 48000 / fps) for f in got["white"]]
    # Every frame is the same number of samples, and the film's sound is the film's length to the sample.
    assert got["total"] == frames * 48000 // fps and set(got["each"]) == {48000 // fps}
    # Python's clocks are the video's: dt is 1/fps, and sound_time() and beat() read the frame's own time.
    seen = got["seen"]
    assert len(seen) == frames
    assert seen[0][:2] == [0, 0]
    for f, (dt, time, beat) in enumerate(seen[1:], start=1):
        assert abs(dt - 1 / fps) < 1e-9 and abs(time - f / fps) < 1e-9 and abs(beat - f / fps * 2) < 1e-6
    page.close()


CHANGE = '''
from pyscenes import *

n = 0


class Dark(Scene):
    def draw(self):
        global n
        background("black")
        n += 1
        if n == 10:
            go("Red", transition="crossfade", transition_time=0.5)


class Red(Scene):
    def draw(self):
        background("#ff0000")
'''

CHANGE_PAGE = PAGE.replace("clap.py", "change.py").replace(
    "if (g.getImageData(5, 5, 1, 1).data[0] > 128) white.push(f)",
    "{ const c = new OffscreenCanvas(8, 8).getContext('2d'); for (const layer of document.querySelectorAll('#s canvas')) if (layer.style.display !== 'none') c.drawImage(layer, 0, 0, 8, 8); white.push(c.getImageData(4, 4, 1, 1).data[0]) }")


def test_a_change_of_scene_moves_by_the_recorder_s_frames(browser, pyctures_run, tmp_path):
    """Stepped, a transition is moved by step() and by nothing else: half a second at thirty frames a second is
    fifteen frames, each a fifteenth further (eased at both ends), however long the frames really took."""
    if not (WEB / "scenes" / "pyscenes.py").exists():
        pytest.skip("this Pyctures has no scenes")
    (tmp_path / "change.py").write_text(CHANGE)
    (tmp_path / "film.html").write_text(CHANGE_PAGE)
    p = pyctures_run(tmp_path)
    runs = []
    for wait in (0, 40):
        page = browser.new_page(viewport={"width": 400, "height": 300})
        page.goto(p.url + "film.html")
        page.wait_for_function("() => typeof window.film === 'function'")
        if wait:
            # A recorder that is slow, differently: the pictures must not know.
            page.evaluate("(ms) => { window.slow = ms }", wait)
        got = page.evaluate("([fps, frames]) => window.film(fps, frames)", [30, 40])
        assert not got["errors"]
        runs.append(got["white"])
        page.close()
    red = runs[0]
    assert runs[0] == runs[1]
    start = next(i for i, v in enumerate(red) if v > 0)
    ramp = red[start - 1:start + 15]
    assert ramp[0] == 0 and ramp[-1] == 255 and red[start + 14:] == [255] * (len(red) - start - 14)
    for k in range(1, 15):
        t = k / 15
        assert abs(ramp[k] - 255 * t * t * (3 - 2 * t)) <= 2, (k, ramp)
