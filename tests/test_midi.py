"""MIDI in a scene (`lead.play_from_midi()`, `def on_midi_note(note, velocity, channel):`, `send_midi_note("C4")`).

Real (headless) Chromium, and NO REAL DEVICE IS EVER SENT TO: every page that sends is given a pretend MIDI
transport (the `midi` option of mount(), which is what an app gives where the browser has no MIDI), with a
pretend keyboard to press and a list of what was sent. The browser's own Web MIDI is only ever asked and
listened to. What is heard is read from the sound engine itself, as in test_sound.py.
"""
import json

import pytest

from conftest import ROOT
from test_browser import Watched, cdn_reachable
from test_sound import CONTROLS, SCENE, build, heard, requests_of, wait_for, write

playwright = pytest.importorskip("playwright.sync_api")

needs_cdn = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        yield b
        b.close()


# A page whose scene is given a pretend transport: window.keys(bytes) is a device sending, window.sent what was
# sent to one. `OPEN` is the body of its open().
PRETEND = '''<!doctype html>
<html><head><meta charset="utf-8"><script>window.PYCTURES_NO_AUTO = true; window.sent = []; window.opened = 0</script></head>
<body style="margin:0"><div id="scene" data-pyctures-src="scene.py" style="position:fixed;inset:0"></div>
<script type="module">
import { mount } from "/pyctures/pyctures.js"
const midi = {
  open() { window.opened++; OPEN },
  inputs: () => ["Pretend Keys"],
  outputs: () => ["Pretend Box", "Other Box"],
  send(bytes, time, output) { window.sent.push({ bytes: Array.from(bytes), time, output: output || null, at: performance.now() }) },
  receive(listener) { window.keys = (bytes) => listener(bytes, performance.now(), "Pretend Keys") },
  changed() {},
}
mount(document.getElementById("scene"), { fullPage: true, midi: THE_OPTION })
</script></body></html>
'''


def pretend(tmp_path, source, open_body="", midi="midi"):
    write(tmp_path, source)
    (tmp_path / "index.html").write_text(PRETEND.replace("OPEN", open_body).replace("THE_OPTION", midi))
    return tmp_path


def warnings_of(page):
    said = []
    page.on("console", lambda m: said.append(m.text) if "MIDI" in m.text else None)
    return said


HOOKS = '''
from pyctures import *
from synths import *

got = []

def on_midi_note(note, velocity, channel):
    got.append(["note", note, round(velocity, 3), channel])

def on_midi_control(number, value):                 # fewer arguments is right too
    got.append(["control", number, round(value, 3)])

def on_midi(message):
    if message.type in ("noteOn", "bend"):
        got.append([message.type, message.device, message.data, round(sound_time() - message.time, 3), message.bend])

def on_midi_devices(devices):
    got.append(["devices", devices["inputs"], devices["outputs"], devices["available"]])

def update(dt):
    js.got = got
    js.known = midi_devices()
'''


def test_a_scene_s_own_functions_are_called_with_decoded_values(browser, pyctures_run, tmp_path):
    server = pyctures_run(pretend(tmp_path, HOOKS))
    w = Watched(browser, server.url)
    asked = requests_of(w.page)
    w.wait_running()
    page = w.page
    wait_for(page, lambda: page.evaluate("window.got || []"), "the devices, told to Python")
    assert page.evaluate("window.got[0]") == ["devices", ["Pretend Keys"], ["Pretend Box", "Other Box"], True]
    assert page.evaluate("window.known") == {"inputs": ["Pretend Keys"], "outputs": ["Pretend Box", "Other Box"], "available": True}
    page.evaluate("""() => {
      window.keys([0x91, 60, 64])            // a key down on channel 2
      window.keys([0x91, 60, 0])             // and up: a note-on with no velocity
      window.keys([0xB0, 74, 127])           // a knob, all the way
      window.keys([0xE0, 0, 0])              // the pitch wheel, all the way down
    }""")
    wait_for(page, lambda: len(page.evaluate("window.got")) >= 6, "what the keyboard sent, in Python")
    got = page.evaluate("window.got")[1:]
    assert got[0] == ["note", 60, 0.504, 2]
    assert got[1][:3] == ["noteOn", "Pretend Keys", [0x91, 60, 64]]
    assert 0 <= got[1][3] < 1, "message.time is on the clock sound_time() reads: it was %s seconds ago" % got[1][3]
    assert got[2] == ["note", 60, 0, 2], "with no on_midi_note_off, a key coming up is velocity 0"
    assert got[3] == ["control", 74, 1]
    assert got[4][0] == "bend" and got[4][4] == -1
    assert page.evaluate("window.sent") == [], "listening sends nothing"
    assert len([u for u in asked if u.endswith("synths-midi.js")]) == 1, "MIDI's file is fetched, once, by a scene that uses MIDI"
    assert not w.errors, w.errors


def test_a_sound_scene_without_midi_fetches_nothing_for_it(browser, pyctures_run, tmp_path):
    server = pyctures_run(pretend(tmp_path, 'from synths import *\nplay_notes("C4 E4 G4", 0.2, repeat=True)\ndef draw():\n    background("black")\n'))
    w = Watched(browser, server.url)
    asked = requests_of(w.page)
    w.wait_running()
    w.page.mouse.click(300, 200)
    wait_for(w.page, lambda: heard(w.page)["level"] > 0.02, "the tune")
    assert not [u for u in asked if "midi" in u], "no MIDI in the scene: its file is not fetched"
    assert w.page.evaluate("window.opened") == 0, "and the devices are not asked for"
    assert not w.errors, w.errors


KEYS = '''
from pyctures import *
from synths import *
from pydials import *
import time

lead = make_synth("lead")
cutoff = dial("cutoff", lead, "cutoff")
lead.play_from_midi()
lead.learn("cutoff")
heard = []
on_midi_note(lambda note, velocity: heard.append(note))

def update(dt):
    js.pyState = [lead.cutoff, heard]

def draw():
    background("black")
    time.sleep(SLEEP)
'''


def test_a_keyboard_plays_the_synth_without_waiting_for_python(browser, pyctures_run, tmp_path):
    """Python here takes half a second over every frame. A key of the pretend keyboard still sounds at once: the
    page plays the synth itself, and Python hears of the note afterwards."""
    server = pyctures_run(pretend(tmp_path, KEYS.replace("SLEEP", "0.5")))
    w = Watched(browser, server.url, size=(900, 600))
    w.wait_running()
    page = w.page
    page.mouse.click(450, 300)           # the first touch turns the sound on
    wait_for(page, lambda: heard(page)["state"] == "on", "sound on")
    wait_for(page, lambda: page.evaluate("window.opened") == 1 and page.evaluate("typeof window.keys") == "function", "the pretend keyboard")
    page.wait_for_timeout(700)
    took = page.evaluate("""async () => {
      const s = document.querySelector('[data-pyctures-src]').pycturesScene
      const frames = s.r.sent
      const t0 = performance.now()
      window.keys([0x90, 64, 100])
      while (!s.sound.read('s1').notes.includes(64) && performance.now() - t0 < 2000) await new Promise((r) => setTimeout(r, 5))
      return { ms: performance.now() - t0, frames: s.r.sent - frames }
    }""")
    assert took["ms"] < 250, "the note took %d ms to sound" % took["ms"]
    assert took["frames"] <= 1, "and did not wait for a frame from Python"
    got = wait_for(page, lambda: (lambda h: h if h["level"] > 0.02 and h["wave"] > 0.02 else None)(heard(page)), "the note, from the engine")
    assert got["notes"] == [64]
    wait_for(page, lambda: (page.evaluate("window.pyState") or [0, []])[1] == [64], "Python hears of the note, a frame or two later")
    page.evaluate("window.keys([0x80, 64, 0])")
    wait_for(page, lambda: heard(page)["notes"] == [], "the key came up and the note is let go")
    assert page.evaluate("window.sent") == [], "a keyboard playing a synth sends nothing"
    assert not w.errors, w.errors


def test_a_learnt_knob_turns_the_setting_and_its_dial(browser, pyctures_run, tmp_path):
    server = pyctures_run(pretend(tmp_path, KEYS.replace("SLEEP", "0")))
    w = Watched(browser, server.url, size=(900, 600))
    w.wait_running()
    page = w.page
    wait_for(page, lambda: page.evaluate("typeof window.keys") == "function", "the pretend controller")
    wait_for(page, lambda: len(page.evaluate(CONTROLS)) == 1, "the dial")
    assert page.evaluate(CONTROLS)[0]["value"] == 2800 and page.evaluate("window.pyState")[0] == 2800
    page.wait_for_timeout(300)
    # The next knob that is moved is the cutoff from then on: knob 21, to half way and then to a quarter.
    page.evaluate("window.keys([0xB0, 21, 64])")
    half = 20 * (20000 / 20) ** (64 / 127)          # a pitch in Hz is turned evenly by ratio
    wait_for(page, lambda: page.evaluate(SCENE + ".sound.synth('s1').get('cutoff')") == pytest.approx(half), "the synth's cutoff, on the page")
    wait_for(page, lambda: page.evaluate(CONTROLS)[0]["value"] == pytest.approx(half), "the dial on the screen turns with the knob")
    wait_for(page, lambda: page.evaluate("window.pyState")[0] == pytest.approx(half), "lead.cutoff reads what the knob set")
    page.evaluate("window.keys([0xB0, 21, 32])")
    quarter = 20 * (20000 / 20) ** (32 / 127)
    wait_for(page, lambda: page.evaluate("window.pyState")[0] == pytest.approx(quarter), "and again")
    assert page.evaluate(CONTROLS)[0]["value"] == pytest.approx(quarter)
    # Another knob is not the cutoff.
    page.evaluate("window.keys([0xB0, 22, 127])")
    page.wait_for_timeout(300)
    assert page.evaluate(SCENE + ".sound.synth('s1').get('cutoff')") == pytest.approx(quarter)
    assert not w.errors, w.errors


SENDS = '''
from pyctures import *
from synths import *

t = sound_time() + 0.5
send_midi_note("C4", 0.8, length=0.5, at=t)
send_midi_note(["E4", "G4"], 1, "quarter", channel=10, output="Other Box", at=t + 0.1)
send_midi_control(74, 0.5, at=t + 0.2)
send_midi_bend(-1, at=t + 0.3)
send_midi_program(5, at=t + 0.4)
send_midi([0xB0, 123, 0], at=t + 0.45)
js.asked = sound_time()

def draw():
    background("black")
'''


def test_what_is_sent_has_the_right_bytes_at_the_right_times(browser, pyctures_run, tmp_path):
    server = pyctures_run(pretend(tmp_path, SENDS))
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    wait_for(page, lambda: len(page.evaluate("window.sent")) == 10, "ten messages at the pretend device")
    sent = sorted(page.evaluate("window.sent"), key=lambda m: (m["time"], m["bytes"]))
    assert [m["bytes"] for m in sent] == [
        [0x90, 60, 102],                              # C4 at 0.8
        [0x99, 64, 127], [0x99, 67, 127],             # a chord on channel 10
        [0xB0, 74, 64], [0xE0, 0, 0], [0xC0, 5], [0xB0, 123, 0],
        [0x80, 60, 0],                                # C4 let go, half a second after it began
        [0x89, 64, 0], [0x89, 67, 0]]                 # the chord let go, a quarter note (half a second at 120) after
    first = sent[0]["time"]
    assert [round(m["time"] - first, 1) for m in sent] == pytest.approx([0, 100, 100, 200, 300, 400, 450, 500, 600, 600], abs=0.2), \
        "each leaves at the time asked for, in milliseconds on the page's clock, with Python's spacing"
    assert [m["output"] for m in sent] == [None, "Other Box", "Other Box", None, None, None, None, None, "Other Box", "Other Box"]
    assert all(m["time"] - m["at"] < 200 for m in sent), "a message is handed over a moment before it is due, not long before"
    assert not w.errors, w.errors


NOWHERE = '''
from pyctures import *
from synths import *

lead = make_synth("lead")
lead.play_from_midi()
lead.learn("cutoff")
SENDS
frames = 0

def update(dt):
    global frames
    frames += 1
    js.known = [midi_devices(), frames]

def draw():
    background("black")
'''


@pytest.mark.parametrize("why, open_body, midi, says", [
    ("a transport that cannot start", "throw new Error('no MIDI on this device')", "midi", "MIDI could not be started here (no MIDI on this device)"),
    ("MIDI switched off by the host", "", "false", "MIDI is switched off for this page"),
    ("the browser's own, not allowed", "", "undefined", "MIDI"),
], ids=lambda v: v if " " in str(v) and len(str(v)) < 40 else None)
def test_where_there_is_no_midi_it_is_said_once_and_the_scene_carries_on(browser, pyctures_run, tmp_path, why, open_body, midi, says):
    """The last of these asks Chromium's own Web MIDI, which a test's browser does not allow. Its scene sends
    nothing at all (it listens, and asks what there is), so no real device can be sent to whatever the browser says."""
    sends = "" if midi == "undefined" else 'send_midi_note("C4")\nuse_midi_output("Minilogue")\nsend_midi_control(74, 0.5, after=0.2)'
    server = pyctures_run(pretend(tmp_path, NOWHERE.replace("SENDS", sends), open_body, midi))
    page = browser.new_page(viewport={"width": 800, "height": 600})
    said = warnings_of(page)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(server.url)
    page.wait_for_selector('[data-pyctures-status="running"]')
    known = wait_for(page, lambda: (lambda k: k if k and k[0]["available"] is not None else None)(page.evaluate("window.known")), "the page's answer about MIDI")
    if midi == "undefined" and known[0]["available"]:
        page.close()
        pytest.skip("this browser allows Web MIDI, so there is no refusal to hear of")
    assert known[0] == {"inputs": [], "outputs": [], "available": False}
    page.wait_for_timeout(600)
    assert page.evaluate("window.known")[1] > known[1], "the scene carries on"
    assert page.get_attribute("[data-pyctures-src]", "data-pyctures-status") == "running"
    assert page.get_attribute("[data-pyctures-src]", "data-pyctures-error") is None
    assert len(said) == 1 and says in said[0] and "carries on" in said[0], said
    assert page.evaluate("window.sent") == [] and not errors, errors
    page.close()


HOST = '''<!doctype html>
<html><head><meta charset="utf-8"><script>window.PYCTURES_NO_AUTO = true; window.batches = []</script></head>
<body><div id="scene" data-pyctures-src="scene.py" style="width:600px;height:400px"></div>
<script type="module">
import { mount } from "/pyctures/pyctures.js"
mount(document.getElementById("scene"), { fullPage: true, sound: {
  send(batch) { window.batches.push(batch) },
  onMidi(listener, scope) { window.tell = (events) => listener(events); window.scope = scope; return () => { window.left = true } },
} })
</script></body></html>
'''


def test_a_host_that_takes_the_commands_takes_midi_too(browser, pyctures_run, tmp_path):
    """`sound: { send, onMidi }`: the `midi` commands are in the host's batches, and what the host's own player
    received reaches the scene's functions. Nothing is loaded here."""
    write(tmp_path, HOOKS + 'lead = make_synth("lead")\nlead.play_from_midi(channel=2)\n')
    (tmp_path / "index.html").write_text(HOST)
    server = pyctures_run(tmp_path)
    w = Watched(browser, server.url)
    asked = requests_of(w.page)
    w.wait_running()
    page = w.page
    wait_for(page, lambda: page.evaluate("window.batches.length"), "a batch for the host")
    cmds = [c for b in page.evaluate("window.batches") for c in b["cmds"] if c["op"] == "midi"]
    assert sorted(c["do"] for c in cmds) == ["devices", "listen", "play"], cmds
    play = [c for c in cmds if c["do"] == "play"][0]
    assert play["id"] == "s1" and play["channel"] == 2
    assert page.evaluate("window.scope") == page.evaluate("window.batches[0].scope")
    page.evaluate("() => window.tell([{ type: 'noteOn', note: 72, velocity: 1, channel: 1, time: performance.now() / 1000, device: 'Theirs', data: [144, 72, 127] }])")
    got = wait_for(page, lambda: [g for g in page.evaluate("window.got || []") if g[0] in ("note", "noteOn")], "the host's note, in Python")
    assert got[0] == ["note", 72, 1, 1] and got[1][:3] == ["noteOn", "Theirs", [144, 72, 127]] and 0 <= got[1][3] < 1
    assert not [u for u in asked if "synths" in u], "the host plays it: nothing of synths.js is loaded"
    page.evaluate(SCENE + ".stop()")
    assert page.evaluate("window.left") is True, "a scene that stops no longer listens"
    assert not w.errors, w.errors


# ---------------------------------------------------------------- built pages

MIDI_SCENE = 'from synths import *\nlead = make_synth("keys")\nlead.play_from_midi()\ndef draw():\n    background("black")\n'


def test_build_takes_midi_s_file_along_for_a_scene_that_uses_it(tmp_path):
    out, _ = build(tmp_path, MIDI_SCENE)
    assert (out / "pyctures" / "synths" / "synths-midi.js").is_file(), "a folder has it beside synths.js, to be fetched on first use"
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    one, _ = build(tmp_path / "a", MIDI_SCENE, html=True)
    packed = json.loads(one.read_text().split('id="pyctures-inline">', 1)[1].split("</script>", 1)[0])
    assert "makeMidiDesk" in packed["synths"]["midi"], "one file carries it inside"
    plain, _ = build(tmp_path / "b", 'from synths import *\nplay_note("C4")\n', html=True)
    packed = json.loads(plain.read_text().split('id="pyctures-inline">', 1)[1].split("</script>", 1)[0])
    assert "midi" not in packed["synths"], "and a sound scene with no MIDI in it does not"


@needs_cdn
def test_a_single_file_page_has_midi_inside_it(browser, static_server, tmp_path):
    """Web MIDI itself is asked here (there is no option to give a built page): asked and listened to, never sent to."""
    out, _ = build(tmp_path, 'from synths import *\nlead = make_synth("keys")\nlead.play_from_midi()\nseen = []\non_midi_devices(seen.append)\ndef update(dt):\n    js.seen = seen\n', html=True)
    w = Watched(browser, "about:blank")
    said = warnings_of(w.page)
    asked = requests_of(w.page)
    w.page.goto(static_server(tmp_path) + "scene.html")
    w.wait_running()
    seen = wait_for(w.page, lambda: w.page.evaluate("window.seen || []"), "the page's answer about MIDI, in Python", 30)
    assert set(seen[0]) == {"inputs", "outputs", "available"}
    assert not [u for u in asked if u.startswith("http://localhost") and not u.endswith("scene.html")], "one file: nothing beside it is fetched"
    assert not [s for s in said if "could not be loaded" in s], said
    assert not w.errors, w.errors


# ---------------------------------------------------------------- the examples, with nothing plugged in

def test_midi_lights_rings_and_draws_for_a_pretend_key(browser, pyctures_run):
    """The browser's own Web MIDI is asked here and is not allowed, or has nothing: the example sends nothing."""
    from conftest import EXAMPLES
    server = pyctures_run(EXAMPLES / "midi_lights.py")
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    page.mouse.click(400, 300)          # the first touch turns the sound on
    page.mouse.click(500, 200)          # and a click pretends to be a key
    wait_for(page, lambda: heard(page)["level"] > 0.02, "the bell, from the engine")
    assert not w.errors, w.errors
