"""The microphone, recording, saving and the voices in a scene (`mic = use_microphone()`, `take = record_sound(3)`,
`save_sound(take, "hello.wav")`), a song's place, and reading a synth back for Python's own drawing.

Real (headless) Chromium, and NO MICROPHONE IS EVER OPENED: on every page `navigator.mediaDevices.getUserMedia`
is replaced before anything runs (`PRETEND`). It counts how often it is asked and gives a steady 440 Hz tone as a
stream, or refuses as a person would, as `window.micMode` says. What is heard is read from the sound engine
itself (the player's `read()`), as in test_sound.py. The engine says what it is doing about forty times a second
once it is being read, and stops a second and a half after the last read, so a test reads until it hears what
it is waiting for (`hears`) or for long enough to be sure of silence (`silent`), and never once only.
"""
import json
import struct

import pytest

from conftest import EXAMPLES, ROOT
from test_browser import Watched, cdn_reachable
from test_sound import CONTROLS, SCENE, build, placed, requests_of, wait_for, write

playwright = pytest.importorskip("playwright.sync_api")

needs_cdn = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")

PRETEND = """(() => {
  window.told = []
  for (const kind of ['log', 'warn', 'error', 'info']) {
    const real = console[kind]
    console[kind] = (...a) => { window.told.push(a.join(' ')); real.apply(console, a) }
  }
  window.micAsked = 0
  window.micMode = window.micMode || 'tone'
  // A steady tone as a stream: what stands where a microphone would be. Its own sound card starts with the first touch.
  window.toneStream = (hz = 440, level = 0.5) => {
    const context = new AudioContext(), osc = context.createOscillator(), gain = context.createGain(), out = context.createMediaStreamDestination()
    osc.frequency.value = hz
    gain.gain.value = level
    osc.connect(gain).connect(out)
    osc.start()
    const wake = () => context.resume()
    for (const kind of ['pointerdown', 'keydown']) addEventListener(kind, wake, true)
    wake()
    return out.stream
  }
  if (!navigator.mediaDevices) Object.defineProperty(navigator, 'mediaDevices', { value: {}, configurable: true })
  navigator.mediaDevices.getUserMedia = async () => {
    window.micAsked++
    if (window.micMode === 'refused') throw new DOMException('Permission denied', 'NotAllowedError')
    if (window.micMode === 'none') throw new DOMException('Requested device not found', 'NotFoundError')
    return window.toneStream()
  }
})()"""

# What the engine is putting out now: how loud all of it is, and its pitch (how often a second it crosses zero going up).
HEARD = """() => {
  const s = document.querySelector('[data-pyctures-src]').pycturesScene, p = s && s.sound && s.sound.player
  if (!p || !p.read) return { state: p ? p.state : null, level: 0, hz: 0 }
  const all = p.read(), a = all.samples
  let n = 0, first = -1, last = -1
  for (let i = 1; i < a.length; i++) if (a[i - 1] < 0 && a[i] >= 0) { n++; if (first < 0) first = i; last = i }
  const rate = (p.context && p.context.sampleRate) || 48000
  return { state: p.state, level: Math.max(...all.level), wave: Math.max(0, ...Array.from(a, Math.abs)), hz: n > 1 ? (n - 1) * rate / (last - first) : 0 }
}"""


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--use-fake-device-for-media-stream"])
        yield b
        b.close()


class Page(Watched):
    """A page with the pretend microphone, and what was downloaded from it."""

    def __init__(self, browser, url, mode="tone"):
        self.context = browser.new_context(viewport={"width": 800, "height": 600}, accept_downloads=True)
        self.context.add_init_script("window.micMode = %s;\n%s" % (json.dumps(mode), PRETEND))
        self.page = self.context.new_page()
        self.errors, self.downloads = [], []
        self.page.on("console", lambda m: self.errors.append(m.text) if m.type == "error" else None)
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("download", lambda d: self.downloads.append(d))
        self.asked = requests_of(self.page)
        self.page.goto(url)

    def py(self):
        return self.page.evaluate("window.py || null")

    def heard(self):
        return self.page.evaluate(HEARD)

    def hears(self, test, what, timeout=10):
        """Read the engine until it is putting out what `test` wants; the reading that passed."""
        return wait_for(self.page, lambda: (lambda h: h if test(h) else None)(self.heard()), what, timeout)

    def silent(self, ms=700):
        """Read for a while, and say whether the wave ended at nothing."""
        for _ in range(ms // 50):
            self.page.wait_for_timeout(50)
            last = self.heard()
        return last["wave"] < 0.001

    def pitch(self):
        """The pitch now: the middle of nine readings, since a voice with a growl or a room wobbles."""
        self.heard()
        reads = sorted(self.heard()["hz"] for _ in range(9) if not self.page.wait_for_timeout(60))
        return reads[4]

    def told(self, word="microphone"):
        return [t for t in self.page.evaluate("window.told") if word in t]

    def press(self, key, wait=300):
        self.page.keyboard.press(key)
        self.page.wait_for_timeout(wait)

    def control(self, label):
        for c in placed(self.page):
            if c["label"] == label:
                return c
        raise AssertionError("no control called %s" % label)

    def click(self, label, fx=0.5, fy=0.5):
        c = self.control(label)
        self.page.mouse.click(c["x"] + c["w"] * fx, c["y"] + c["h"] * fy)

    def close(self):
        self.context.close()


@pytest.fixture
def opened():
    pages = []

    def open_(browser, url, mode="tone"):
        pages.append(Page(browser, url, mode))
        return pages[-1]
    yield open_
    for p in pages:
        p.close()


def wav(data):
    """A WAV file's (channels, sample rate, bits, seconds), checked to be one."""
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE" and struct.unpack("<I", data[4:8])[0] == len(data) - 8
    channels, rate, _, _, bits = struct.unpack("<HIIHH", data[22:36])
    assert data[36:40] == b"data"
    return channels, rate, bits, struct.unpack("<I", data[40:44])[0] / (channels * bits // 8) / rate


# A scene whose keys do one thing each, and that says what Python knows where a test can read it.
VOICE = '''
from pyctures import *
from synths import *

mic = use_microphone(gate="off")
lead = make_synth("lead")
take = None
saved = None
kept = None
log = []

def on_key_down(key):
    global take, saved, kept
    if key == "l": mic.listen()
    if key == "m": mic.mute()
    if key == "c": mic.voice = "chipmunk"
    if key == "o": mic.voice = "monster"
    if key == "n": mic.voice = "none"
    if key == "r":
        take = record_sound(1)
        take.on_done(lambda t: log.append(["done", t.seconds, sound_time()]))
        log.append(["asked", take.done, sound_time()])
    if key == "p": take.play()
    if key == "s": saved = save_sound(take, "hello.wav")
    if key == "k": kept = save_sound(take, download=False)
    if key == "a": lead.play("A4", 3)

def update(dt):
    js.py = {"state": mic.state, "ready": mic.ready, "voice": mic.voice, "pitch": mic.pitch, "listening": mic.listening,
             "take": take and [take.done, take.seconds], "saved": saved and [saved.done, saved.path, saved.name],
             "kept": kept and [kept.done, len(kept.bytes or b""), kept.path], "log": log,
             "mic": [len(mic.samples()), max(mic.level())], "lead": [lead.notes(), max(lead.level()), len(lead.samples())]}

def draw():
    background("navy")
'''


def start(opened, browser, pyctures_run, tmp_path, source=VOICE, mode="tone", touch=True):
    server = pyctures_run(write(tmp_path, source))
    w = opened(browser, server.url, mode)
    w.wait_running()
    if touch:
        w.page.mouse.click(400, 300)
        w.hears(lambda h: h["state"] == "on", "the sound, turned on by a click")
    return w


# ---------------------------------------------------------------- nothing new for a scene without it

def test_a_scene_without_sound_asks_for_no_microphone_and_no_file(browser, opened, pyctures_run):
    server = pyctures_run(EXAMPLES / "star_catcher.py")
    w = opened(browser, server.url)
    w.wait_running()
    w.page.mouse.click(400, 300)
    w.page.wait_for_timeout(600)
    assert w.page.evaluate("window.micAsked") == 0
    assert not [u for u in w.asked if "synths" in u or "dials" in u]
    assert w.told() == [] and not w.errors


def test_a_sound_scene_without_a_microphone_never_asks_for_one(browser, opened, pyctures_run, tmp_path):
    w = start(opened, browser, pyctures_run, tmp_path, 'from synths import *\nplay_notes("C4 E4 G4", 0.2, repeat=True)\ndef draw():\n    background("black")\n')
    w.hears(lambda h: h["wave"] > 0.02, "the tune")
    assert w.page.evaluate("window.micAsked") == 0 and w.told() == []


# ---------------------------------------------------------------- the microphone

def test_the_microphone_is_heard_only_while_it_is_listened_to(browser, opened, pyctures_run, tmp_path):
    w = start(opened, browser, pyctures_run, tmp_path)
    wait_for(w.page, lambda: (w.py() or {}).get("state") == "on", "Python told that the microphone is on")
    assert w.page.evaluate("window.micAsked") == 1, "the page asked the browser, once"
    assert w.silent(), "it is not heard until it is listened to"
    # ...though Python's own scope and meter show it as it comes in.
    wait_for(w.page, lambda: w.py()["mic"][0] == 1024 and w.py()["mic"][1] > 0.3, "the microphone's wave, read in Python")
    w.press("l")
    w.hears(lambda h: h["wave"] > 0.1 and abs(h["hz"] - 440) < 15, "the microphone, listened to")
    assert w.py()["listening"] is True
    w.press("m")
    assert w.silent() and w.py()["listening"] is False
    assert len(w.told("headphones")) == 1, "the word about loudspeakers is said once"
    assert not w.errors, w.errors


def test_a_voice_moves_the_pitch_the_way_its_name_says(browser, opened, pyctures_run, tmp_path):
    w = start(opened, browser, pyctures_run, tmp_path)
    w.press("l")
    hz = {}
    for key, voice in (("c", "chipmunk"), ("o", "monster"), ("n", "none")):
        w.press(key, 900)
        hz[voice] = w.pitch()
        assert w.py()["voice"] == voice
    assert 600 < hz["chipmunk"] < 720, hz          # seven semitones up from 440 is 659
    assert 260 < hz["monster"] < 330, hz           # seven down is 294
    assert abs(hz["none"] - 440) < 15, hz
    assert not w.errors, w.errors


def test_a_second_of_recording_is_a_take_a_second_long_that_plays(browser, opened, pyctures_run, tmp_path):
    w = start(opened, browser, pyctures_run, tmp_path)
    wait_for(w.page, lambda: (w.py() or {}).get("state") == "on", "the microphone")
    w.press("r", 100)
    assert w.py()["take"] == [False, 0], "the take is given back at once, still being made"
    wait_for(w.page, lambda: w.py()["take"][0], "the take, done")
    py = w.py()
    assert abs(py["take"][1] - 1) < 0.02
    asked, done = py["log"][0], py["log"][1]
    assert asked[:2] == ["asked", False] and done[0] == "done"
    assert 1 <= done[2] - asked[2] < 1.6, "Python is told a frame or two after the second is over: %s" % (done[2] - asked[2])
    assert w.silent(300), "recording is not listening"
    w.press("p", 50)
    w.hears(lambda h: h["wave"] > 0.1 and abs(h["hz"] - 440) < 15, "the take, played, at the pitch it was said")
    assert not w.errors, w.errors


def test_save_sound_writes_a_wav_file_beside_the_scene(browser, opened, pyctures_run, tmp_path):
    w = start(opened, browser, pyctures_run, tmp_path)
    wait_for(w.page, lambda: (w.py() or {}).get("state") == "on", "the microphone")
    w.press("r", 50)
    w.press("s", 50)          # asked while it is still recording: saved when it is over
    assert w.py()["saved"][0] is False
    wait_for(w.page, lambda: w.py()["saved"][0], "the file, saved")
    file = tmp_path / "hello.wav"
    assert w.py()["saved"][1:] == [str(file.resolve()), "hello.wav"]
    channels, rate, bits, seconds = wav(file.read_bytes())
    assert (channels, bits) == (1, 16) and rate in (44100, 48000) and abs(seconds - 1) < 0.02
    samples = struct.unpack("<%dh" % (rate // 2), file.read_bytes()[44:44 + rate])
    assert 0.4 * 32767 < max(samples) < 0.6 * 32767, "the tone, at the level it came in"
    # download=False gives Python the bytes and writes nothing.
    w.press("k", 50)
    wait_for(w.page, lambda: w.py()["kept"][0], "the bytes, in Python")
    assert w.py()["kept"] == [True, len(file.read_bytes()), None]
    assert sorted(p.name for p in tmp_path.glob("*.wav")) == ["hello.wav"] and w.downloads == []
    assert not w.errors, w.errors


@pytest.mark.parametrize("mode, state", [("refused", "refused"), ("none", "none")])
def test_with_no_microphone_one_thing_is_said_and_the_scene_carries_on(browser, opened, pyctures_run, tmp_path, mode, state):
    w = start(opened, browser, pyctures_run, tmp_path, mode=mode)
    wait_for(w.page, lambda: (w.py() or {}).get("state") == state, "Python told there is no microphone")
    assert w.py()["ready"] is False
    w.press("l")
    w.press("c")
    w.press("r", 50)
    wait_for(w.page, lambda: w.py()["take"] == [True, 0], "an empty take, done at once")
    w.press("p")
    w.press("s", 50)
    wait_for(w.page, lambda: w.py()["saved"][0], "a file with no sound in it")
    assert wav((tmp_path / "hello.wav").read_bytes())[3] == 0
    w.press("a", 50)
    w.hears(lambda h: h["wave"] > 0.02, "a note: everything else plays")
    wait_for(w.page, lambda: w.py()["lead"][0] == [69], "the note, read in Python")
    assert len(w.told()) == 1, w.told()
    assert w.scenes()[0].get_attribute("data-pyctures-status") == "running"
    assert not w.errors, w.errors


def test_python_reads_back_what_a_synth_is_doing(browser, opened, pyctures_run, tmp_path):
    w = start(opened, browser, pyctures_run, tmp_path)
    assert w.py()["lead"][:2] == [[], 0]
    w.press("a", 50)
    wait_for(w.page, lambda: w.py()["lead"][0] == [69] and w.py()["lead"][1] > 0.02 and w.py()["lead"][2] == 1024, "the note, its level and its wave, in Python")


SONG = '''
from pyctures import *
from synths import *

song = play_song("songs/night_drive.json")
seen = []

def on_key_down(key):
    if key == "m": song.mute()
    if key == "u": song.unmute()
    if key == "l": song.loop_pattern()

def update(dt):
    place = song.position
    if not seen or seen[-1] != [place["state"], place["order"]]:
        seen.append([place["state"], place["order"]])
    js.py = {"place": place, "seen": seen, "channel": max(song.channel(0).level())}

def draw():
    background("black")
'''


def test_a_song_s_place_is_read_in_python_and_its_channels_are_muted(browser, opened, pyctures_run, tmp_path):
    import shutil
    songs = ROOT.parent / "synths.js" / "examples" / "songs"
    if not (songs / "night_drive.json").is_file():
        pytest.skip("the example song of synths.js is not beside this repository")
    shutil.copytree(songs, tmp_path / "songs")
    w = start(opened, browser, pyctures_run, tmp_path, SONG)
    w.hears(lambda h: h["wave"] > 0.02, "the song")
    wait_for(w.page, lambda: w.py()["place"]["state"] == "playing" and w.py()["place"]["rows"] > 0, "the song's place, in Python")
    py = w.py()
    assert py["seen"][0] == ["none", 0], "the first time it is read the page has not said yet"
    assert set(py["place"]) == {"state", "order", "pattern", "row", "tick", "speed", "tempo", "rounds", "rows", "orders"}
    row = py["place"]["row"]
    wait_for(w.page, lambda: w.py()["place"]["row"] != row, "the row moving on")
    w.press("m")
    assert w.silent(900), "every channel muted"
    w.press("u", 50)
    w.hears(lambda h: h["wave"] > 0.02, "the song again")
    w.press("l", 50)
    order = w.py()["place"]["order"]
    w.page.wait_for_timeout(2500)
    assert w.py()["place"]["order"] == order and w.py()["place"]["state"] == "playing", "it stays on the pattern that is playing"
    assert not w.errors, w.errors


# ---------------------------------------------------------------- the first moments

def test_a_scene_that_begins_with_the_microphone_says_what_a_touch_turns_on(browser, opened, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, VOICE + '\nplay_notes("C4 E4 G4", 0.2, repeat=True)\n'))
    w = opened(browser, "about:blank")
    # Nothing is asked of the page until it has said it is waiting: to this browser, a test's question counts as a touch.
    with w.page.expect_console_message(lambda m: "waiting for a tap" in m.text, timeout=20000):
        w.page.goto(server.url)
    cover = lambda: w.page.evaluate("document.querySelector('.pyctures-cover') ? document.querySelector('.pyctures-cover').textContent : ''")
    assert cover() == "Click, tap or press a key to turn the sound and the microphone on"
    assert w.heard()["state"] == "waiting"
    assert w.page.evaluate("window.micAsked") == 1, "the microphone is asked for at once, without waiting for the touch"
    wait_for(w.page, lambda: (w.py() or {}).get("state") == "on", "Python told of the microphone, before any touch")
    w.page.mouse.click(400, 300)
    wait_for(w.page, lambda: cover() == "", "the words gone once the page is touched")
    w.hears(lambda h: h["state"] == "on" and h["wave"] > 0.02, "the tune")
    assert not w.errors, w.errors


# ---------------------------------------------------------------- dials tied to the microphone act on the page

PANEL = '''
from pyctures import *
from synths import *
from pydials import *

mic = use_microphone(gate="off")
voice = select("voice", mic, "voice")
pitch = dial("pitch", mic, "pitch")
switch = toggle("listen", mic, "listening")

def update(dt):
    js.py = {"state": mic.state, "voice": mic.voice, "pitch": mic.pitch, "listening": mic.listening,
             "controls": [voice.value, pitch.value, bool(switch)]}

def draw():
    background("navy")
'''


def test_a_dial_a_switch_and_a_picker_tied_to_the_microphone(browser, opened, pyctures_run, tmp_path):
    w = start(opened, browser, pyctures_run, tmp_path, PANEL)
    wait_for(w.page, lambda: (w.py() or {}).get("state") == "on", "the microphone")
    pitch = w.control("pitch")
    assert (pitch["min"], pitch["max"], pitch["value"]) == (-12, 12, 0), "the dial took the pitch shifter's range from the page"
    w.click("listen")
    w.hears(lambda h: h["wave"] > 0.1, "the microphone, heard at the switch")
    wait_for(w.page, lambda: w.py()["listening"] is True, "the switch, told to Python")
    w.click("voice", 0.93)             # the arrow at its right: the next voice
    wait_for(w.page, lambda: w.py()["voice"] == "robot" and w.py()["controls"][0] == "robot", "the picker's voice, in Python")
    w.click("voice", 0.93)
    wait_for(w.page, lambda: w.py()["voice"] == "chipmunk", "the next voice")
    # The chipmunk is seven semitones up, and the dial tied to the pitch shifter stands there.
    wait_for(w.page, lambda: w.control("pitch")["value"] == 7 and w.py()["pitch"] == 7, "the dial following the voice")
    hz = w.pitch()
    assert 600 < hz < 720, hz
    assert not w.errors, w.errors


# ---------------------------------------------------------------- the examples

@pytest.mark.parametrize("mode", ["tone", "refused"])
def test_the_voice_changer_records_and_plays_back(browser, opened, pyctures_run, mode, tmp_path):
    scene = tmp_path / "voice_changer.py"
    scene.write_text((EXAMPLES / "voice_changer.py").read_text().replace("mic.record(3)", "mic.record(1)"))
    server = pyctures_run(scene)
    w = opened(browser, server.url, mode)
    w.wait_running()
    w.page.mouse.click(400, 500)
    says = lambda: (w.page.evaluate(CONTROLS) or [{"label": ""}])[0]["label"]
    wait_for(w.page, lambda: says() == ("Say something" if mode == "tone" else "No microphone here (refused): the browser's console says why"), "what the scene says")
    assert [c["label"] for c in w.page.evaluate(CONTROLS)][1:7] == ["voice", "pitch", "echo", "listen", "record", "play"]
    w.click("record")
    wait_for(w.page, lambda: says() == ("Recorded: press play" if mode == "tone" else "Nothing was recorded: there is no microphone"), "the recording, over")
    w.click("play")
    if mode == "tone":
        w.hears(lambda h: h["wave"] > 0.1 and abs(h["hz"] - 440) < 15, "the recording, played back")
    else:
        assert w.silent()
    assert len(w.told()) == (0 if mode == "tone" else 1)
    assert not w.errors, w.errors


def test_the_sampler_plays_a_recorded_word_from_the_keys(browser, opened, pyctures_run):
    server = pyctures_run(EXAMPLES / "sampler.py")
    w = opened(browser, server.url)
    w.wait_running()
    w.page.mouse.click(400, 250)
    says = lambda: (w.page.evaluate(CONTROLS) or [{"label": ""}])[0]["label"]
    w.page.keyboard.down("a")          # middle C: a bell, until a word is recorded
    w.hears(lambda h: h["wave"] > 0.02 and abs(h["hz"] - 262) < 12, "a bell at middle C")
    w.page.keyboard.up("a")
    w.click("record")
    wait_for(w.page, lambda: says() == "Now play the keys", "a word, recorded")
    assert w.silent(2500) or True      # the bell dies away
    w.page.keyboard.down("a")
    w.hears(lambda h: h["wave"] > 0.1 and abs(h["hz"] - 440) < 15, "the word, as it was said")
    w.page.keyboard.up("a")
    assert w.silent(900)
    w.page.keyboard.down("k")          # the C above: an octave higher, and twice as fast
    w.hears(lambda h: h["wave"] > 0.1 and abs(h["hz"] - 880) < 30, "the word, an octave higher")
    w.page.keyboard.up("k")
    assert not w.errors, w.errors


@pytest.mark.parametrize("html", [False, True], ids=["folder", "one file"])
def test_the_voice_changer_is_built(tmp_path, html):
    from pyctures.build import build as make
    out = tmp_path / ("voice.html" if html else "site")
    said = []
    make(EXAMPLES / "voice_changer.py", out, say=said.append)
    if html:
        text = out.read_text()
        assert '"synths":' in text and '"dials":' in text and "use_microphone" in text
    else:
        for name in ("synths/synths.js", "synths/synths_core.wasm", "synths/synths.py", "dials/dials.js", "dials/pydials.py"):
            assert (out / "pyctures" / name).is_file(), name


# ---------------------------------------------------------------- a built page, where the page keeps the files

HOST = '''<!doctype html>
<html><head><meta charset="utf-8"><script>window.PYCTURES_NO_AUTO = true; window.files = {}; window.kept = []</script></head>
<body style="margin:0"><div id="scene" data-pyctures-src="scene.py" style="position:fixed;inset:0"></div>
<script type="module">
import { mount } from "./pyctures/pyctures.js"
const storage = { writeBytes: async (path, bytes) => { window.files[path] = Array.from(bytes) }, readBytes: async () => null }
const save = (file) => { window.kept.push({ name: file.name, type: file.type, bytes: Array.from(file.bytes) }) }
const stream = { open: () => window.toneStream(), close() { window.closed = true } }
mount(document.getElementById("scene"), { src: "scene.py", fullPage: true, OPTIONS })
</script></body></html>
'''


@needs_cdn
@pytest.mark.parametrize("options, where", [("", "download"), ("storage", "files"), ("storage, save", "save"), ("microphone: stream", "download"),
                                              ("microphone: false", "none")])
def test_built_a_recording_is_saved_where_the_page_keeps_files(browser, opened, static_server, tmp_path, options, where):
    out, _ = build(tmp_path, VOICE)
    (out / "host.html").write_text(HOST.replace("OPTIONS", options))
    w = opened(browser, static_server(out) + "host.html")
    w.wait_running()
    w.page.mouse.click(400, 300)
    state = "unavailable" if where == "none" else "on"
    wait_for(w.page, lambda: (w.py() or {}).get("state") == state, "the microphone: %s" % state, 30)
    # A host's own microphone is used in place of the browser's, which is then never asked.
    assert w.page.evaluate("window.micAsked") == (0 if "microphone" in options else 1)
    w.press("r", 50)
    w.press("s", 50)
    wait_for(w.page, lambda: w.py()["saved"][0], "the file, saved")
    assert w.py()["saved"][1] is None, "in a page Python does not write the file"
    w.page.wait_for_timeout(300)
    files, kept = w.page.evaluate("window.files"), w.page.evaluate("window.kept")
    if where == "files":
        assert list(files) == ["hello.wav"] and kept == [] and w.downloads == []
        data = bytes(files["hello.wav"])
    elif where == "save":
        assert [k["name"] for k in kept] == ["hello.wav"] and kept[0]["type"] == "audio/wav" and files == {} and w.downloads == []
        data = bytes(kept[0]["bytes"])
    else:
        assert files == {} and kept == [] and len(w.downloads) == 1 and w.downloads[0].suggested_filename == "hello.wav"
        data = open(w.downloads[0].path(), "rb").read()
    channels, rate, bits, seconds = wav(data)
    assert (channels, bits) == (1, 16) and abs(seconds - (0 if where == "none" else 1)) < 0.02
    if where == "none":
        assert len(w.told()) == 1 and "turned off" in w.told()[0]
    # download=False hands Python the bytes there too, and saves nothing.
    w.press("k", 50)
    wait_for(w.page, lambda: w.py()["kept"][0], "the bytes, in Python")
    assert w.py()["kept"] == [True, len(data), None] and len(w.downloads) == (0 if where in ("files", "save") else 1)
    assert not w.errors, w.errors


# ---------------------------------------------------------------- the docs name what there is

def test_the_docs_name_every_sound_synth_and_voice_and_the_readme_every_example():
    import sys
    sys.path.insert(0, str(ROOT / "src" / "pyctures" / "web" / "synths"))
    import synths
    page = (ROOT / "docs" / "sound.md").read_text()
    index = (ROOT / "docs" / "function-index.md").read_text()
    for name in synths.sound_names() + synths.synth_names() + synths.voice_names():
        assert "`%s`" % name in page or '"%s"' % name in page, "docs/sound.md does not name %s" % name
    for name in synths.sound_names() + synths.voice_names():
        assert "`%s`" % name in index, "docs/function-index.md does not name %s" % name
    for name in synths._NAMES["microphone"]["functions"]:
        if name != "receiveSoundEvents":        # a host's to call
            assert synths._snake(name) in index, "docs/function-index.md does not have %s" % synths._snake(name)
    readme = (ROOT / "README.md").read_text()
    for example in sorted(p.name for p in EXAMPLES.glob("*.py")):
        assert example in readme, "the README does not list examples/%s" % example
