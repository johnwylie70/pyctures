"""say(): the computer talks (web/voice: pysay.py and pictures.js's say.js).

`say("Hello")` is one command to the page, which speaks it in the device's own voice or plays the recording a voice
host has of it; Python gives back how many seconds the line takes, from the host's measured length when the page
has told this run of it, else 2.5 words a second and never under 0.8. Nothing here generates a voice.

The first tests need no browser. The film tests record a scene a frame at a time in headless Chromium, with this
computer's Python behind `pyctures run`: the host is a fake whose one recording is a WAV made here (a short tone that
begins on a full-scale sample), and the browser's speech is a fake that writes down what it was asked to say. Nothing
is heard and no microphone is asked for.
"""
import json
import math
import struct
import sys
import textwrap

import pytest

import pyctures
from conftest import ROOT

WEB = ROOT / "src" / "pyctures" / "web"
INFO = {"width": 320, "height": 180, "pixel_ratio": 1}
sys.path.append(str(WEB / "voice"))
import pysay  # noqa: E402

H_SAY = 16


@pytest.fixture(autouse=True)
def stopped():
    yield
    pyctures.stop()


def start(src, **info):
    r = json.loads(pyctures.start(textwrap.dedent(src), json.dumps({**INFO, **info})))
    listens = [c for c in r["cmds"] if c[3] == H_SAY and c[4] == "listen"]
    r["cmds"] = [c for c in r["cmds"] if c not in listens]
    r["told"] = listens[0][5][0] if listens else None
    return r


def tick(**payload):
    payload.setdefault("dt", 1 / 60)
    return json.loads(pyctures.tick(json.dumps(payload)))


# ---------------------------------------------------------------- what Python writes

def test_the_estimate_is_two_and_a_half_words_a_second_and_never_under_eight_tenths():
    assert pysay.estimate("Hello") == 0.8 and pysay.estimate("") == 0.8 and pysay.estimate("  a   b  ") == 0.8
    assert pysay.estimate("one two three four five") == pytest.approx(2.0)
    assert pysay.estimate("a b c d e f g h i j") == pytest.approx(4.0)


def test_say_is_one_command_to_the_page_and_gives_back_the_estimate():
    r = start('''
        n = say("Hello")
        m = say("Half of the width is the middle.", voice="calm", lang="fr")
        print(n, m)
    ''')
    assert r["error"] is None and r["out"] == "0.8 2.8\n"
    assert r["cmds"] == [
        ["call", 2, 0, H_SAY, "say", ["Hello", None, "en", "literal", 2]],
        ["call", 3, 0, H_SAY, "say", ["Half of the width is the middle.", "calm", "fr", "literal", 3]],
    ]
    assert r["told"] and pysay.H_SAY == H_SAY


def test_a_line_made_while_it_runs_is_told_as_runtime_with_its_own_line():
    r = start('''
        name = "Sam"
        say("Hello " + name)
        say(f"Hi {name}")
        say("Hello")
    ''')
    assert [c[5] for c in r["cmds"]] == [["Hello Sam", None, "en", "runtime", 3], ["Hi Sam", None, "en", "runtime", 4], ["Hello", None, "en", "literal", 5]]


def test_the_page_tells_a_run_the_measured_length_of_a_line_and_later_ones_with_a_frame():
    # The recording is of the line with no voice named; the same words in another voice are another line.
    r = start('''
        print(say("Hello there"), say("Hello there", voice="calm"))
    ''', say=[["Hello there", None, "en", 0.5]])
    assert r["error"] is None and r["out"] == "0.5 0.8\n"
    assert pyctures.S.say.lengths == {("Hello there", None, "en"): 0.5}
    # Found only when first said: told with a later frame, exact from then on.
    r3 = start('''
        text = "Made " + "later"

        def update(dt):
            print(say(text))
    ''')
    assert r3["told"]
    first = tick()["out"]
    tick(events=[{"k": "cb", "id": r3["told"], "e": {"text": "Made later", "voice": None, "lang": "en", "seconds": 0.7}}])
    last = tick()["out"]
    assert first.strip().split("\n")[-1] == "0.8" and last.strip().split("\n")[-1] == "0.7"


def test_the_texts_in_the_file_are_found_by_python_not_by_looking_at_the_words():
    assert pysay._literals('say("a")\nsay(b)\nsay(f"c")\nx.say("d")\nsay(\'e\', voice="v")') == {"a": 1, "e": 5}


def test_say_says_what_is_wrong():
    for call, words in [('say("")', "needs the words to say"), ('say(3)', "needs the words to say"),
                        ('say("x", voice=3)', "name of a voice"), ('say("x", lang="")', "the language")]:
        r = start(call)
        assert r["error"] and words in r["error"], r["error"]


def test_a_file_that_does_not_call_it_is_given_nothing_and_keeps_its_own_say():
    r = start("print('say' in dir())\n")
    assert r["cmds"] == [] and r["told"] is None
    r = start('''
        def say(w):
            return "mine " + w

        print(say("x"))
    ''')
    assert r["out"] == "mine x\n" and not [c for c in r["cmds"] if c[3] == H_SAY and c[4] == "say"]


def test_the_voice_has_a_handle_of_its_own():
    handles = {name: value for name, value in vars(pyctures).items() if name.startswith("H_") and isinstance(value, int)}
    assert H_SAY not in handles.values()
    assert "c[3] !== 16 || c[0] !== 'call'" in (WEB / "voice" / "say.js").read_text()


def test_the_page_half_is_the_one_pictures_js_has():
    mine = (WEB / "voice" / "say.js").read_bytes()
    beside = ROOT.parent / "pictures.js" / "voice" / "say.js"
    if beside.is_file():
        assert mine == beside.read_bytes(), "web/voice/say.js differs from ../pictures.js/voice/say.js: run scripts/sync_libraries.py"


# ---------------------------------------------------------------- the talking mouth

def told_level(r, level, speaking):
    return {"k": "cb", "id": r["told"], "e": {"level": level, "speaking": speaking, "width": 0.9, "viseme": "ee"}}


def test_mouth_is_one_command_to_the_page_with_the_level_python_was_told():
    r = start('''
        mouth(10, 20)
        mouth(30, 40, size=50, style="smile", color="red")
        print(voice_level(), speaking())
    ''')
    assert r["error"] is None and r["out"] == "0.0 False\n"
    assert r["cmds"] == [
        ["call", 2, 0, H_SAY, "mouth", [10, 20, None, "oval", "black", 0.0, 0.5]],
        ["call", 3, 0, H_SAY, "mouth", [30, 40, 50, "smile", "red", 0.0, 0.5]],
    ]


def test_the_page_tells_python_the_level_with_each_frame_and_the_mouth_carries_it():
    r = start('''
        def draw():
            print(speaking(), voice_level())
            mouth(5, 6, style="robot")
    ''')
    assert r["told"]
    first = tick()
    assert first["out"].strip().split("\n")[-1] == "False 0.0"
    loud = tick(events=[told_level(r, 0.75, True)])
    assert loud["out"].strip().split("\n")[-1] == "True 0.75"
    assert [c for c in loud["cmds"] if c[3] == H_SAY] == [["call", 4, 0, H_SAY, "mouth", [5, 6, None, "robot", "black", 0.75, 0.9]]]
    # Until it is told again the level stays what it was, and a later frame can close the mouth.
    assert tick()["out"].strip().split("\n")[-1] == "True 0.75"
    assert tick(events=[told_level(r, 0, False)])["out"].strip().split("\n")[-1] == "False 0.0"


def test_voice_shape_is_what_the_page_told_python():
    r = start('''
        def draw():
            print(voice_shape())
    ''')
    assert tick()["out"].strip().split("\n")[-1] == "{'width': 0.5, 'height': 0.0, 'viseme': 'closed'}"
    loud = tick(events=[told_level(r, 0.75, True)])
    assert loud["out"].strip().split("\n")[-1] == "{'width': 0.9, 'height': 0.75, 'viseme': 'ee'}"


def test_a_file_that_calls_only_the_new_names_is_given_them_and_one_that_defines_its_own_keeps_it():
    for call in ("speaking()", "voice_level()", "voice_shape()", "mouth(1, 2)"):
        r = start("print(%r in dir())\nx = %s\n" % (call.split("(")[0], call))
        assert r["error"] is None and r["out"] == "True\n", (call, r)
    r = start('''
        def mouth(x, y):
            return "mine"

        print(mouth(1, 2))
    ''')
    assert r["out"] == "mine\n" and not [c for c in r["cmds"] if c[3] == H_SAY and c[4] == "mouth"]
    from pyctures import pages
    assert pages.uses_library("mouth(1, 2)", "pysay") and pages.uses_library("x = speaking()", "pysay") and not pages.uses_library("print(mouth)", "pysay")


def test_mouth_says_what_is_wrong():
    for call, words in [('mouth("a", 2)', "middle of the mouth"), ('mouth(1, 2, size=0)', "above 0"), ('mouth(1, 2, size="big")', "above 0"),
                        ('mouth(1, 2, style="square")', "'oval', 'smile', 'robot'"), ('mouth(1, 2, color=3)', "the colour")]:
        r = start(call)
        assert r["error"] and words in r["error"], (call, r["error"])


def test_the_styles_are_the_pages():
    js = (WEB / "voice" / "say.js").read_text()
    import re
    page = re.search(r"export const mouthStyles = \[(.*?)\]", js).group(1)
    assert tuple(x.strip().strip("'") for x in page.split(",")) == pysay.STYLES


def test_the_renderer_draws_the_mouth_in_the_order_the_frame_has_it():
    js = (WEB / "pyctures.js").read_text()
    assert "H.set(16, { mouth:" in js and "libs.pysay.drawMouth" in js
    assert "c[4] === 'mouth'" in (WEB / "voice" / "say.js").read_text()


# ---------------------------------------------------------------- voices and characters

def told_speakers(r, **speakers):
    """What the page tells with a frame: the global mouth and each speaker's own (numbers as text, as JSON keys are)."""
    return {"k": "cb", "id": r["told"], "e": {"level": 0.0, "speaking": False, "width": 0.5, "viseme": "closed", "speakers": {str(k): v for k, v in speakers.items()}}}


def test_voices_are_what_the_page_told_the_run_and_later_ones_come_with_a_frame():
    voices = [{"name": "Samantha", "lang": "en-US", "default": True, "source": "device"}]
    r = start('''
        def draw():
            print([v["name"] for v in voices()])
    ''', voices=voices)
    assert tick()["out"].strip().split("\n")[-1] == "['Samantha']"
    tick(events=[{"k": "cb", "id": r["told"], "e": {"voices": voices + [{"name": "Daniel", "lang": "en-GB", "default": False, "source": "device"}]}}])
    assert tick()["out"].strip().split("\n")[-1] == "['Samantha', 'Daniel']"
    # Nothing told yet (a device that loads late): an empty list, not an error.
    start('''
        print(voices())
    ''')
    assert pyctures.S.say.voices == []


def test_speaker_is_one_command_and_its_lines_carry_its_number():
    r = start('''
        bob = speaker(voice="deep", pitch=0.8, name="Bob")
        amy = speaker("squeaky", rate=1.2, lang="en")
        print(bob.say("Hello"), amy.say("Hi there"), bob, bob.voice, amy.pitch)
    ''')
    assert r["error"] is None and r["out"] == "0.8 0.8 <speaker Bob> deep 1\n"
    assert r["cmds"] == [
        ["call", 2, 0, H_SAY, "speaker", [1, "deep", 0.8, 1, "en", "Bob", None, None]],
        ["call", 3, 0, H_SAY, "speaker", [2, "squeaky", 1, 1.2, "en", None, None, None]],
        ["call", 4, 0, H_SAY, "say", ["Hello", "deep", "en", "runtime", 4, 1]],
        ["call", 4, 0, H_SAY, "say", ["Hi there", "squeaky", "en", "runtime", 4, 2]],
    ]


def test_the_queue_is_python_clocked_and_a_plain_say_is_not_in_it():
    r = start('''
        bob = speaker(voice="deep")
        amy = speaker(voice="high")
        out = [bob.say_at("Hello there"), amy.say_at("Hi Bob, how are you today my friend"), bob.say_at("Fine"), say_at("Plain")]
        print([round(o["start"], 1) for o in out], [round(o["end"], 1) for o in out])
    ''')
    assert r["error"] is None and r["out"] == "[0.0, 0.8, 4.0, 0.0] [0.8, 4.0, 4.8, 0.8]\n"


def test_each_speakers_mouth_is_what_the_page_told_python_about_that_speaker():
    r = start('''
        bob = speaker(voice="deep")
        amy = speaker(voice="high")

        def draw():
            print(bob.speaking(), round(bob.level(), 2), amy.speaking(), round(amy.level(), 2), voice_level(amy), speaking(bob))
            print(bob.shape(), voice_shape(amy)["viseme"])
            mouth(10, 20, speaker=bob)
            mouth(30, 40, speaker=amy, style="robot")
            mouth(50, 60)
    ''')
    assert r["told"]
    first = tick()
    assert first["out"].strip().split("\n")[-2] == "False 0.0 False 0.0 0.0 False"
    both = tick(events=[told_speakers(r, **{"1": {"level": 0.6, "width": 0.2, "viseme": "oh", "speaking": True}})])
    lines = both["out"].strip().split("\n")
    assert lines[-2] == "True 0.6 False 0.0 0.0 True"
    assert lines[-1] == "{'width': 0.2, 'height': 0.6, 'viseme': 'oh'} closed"
    cmds = [c for c in both["cmds"] if c[3] == H_SAY]
    assert [c[5] for c in cmds] == [[10, 20, None, "oval", "black", 0.6, 0.2], [30, 40, None, "robot", "black", 0.0, 0.5], [50, 60, None, "oval", "black", 0.0, 0.5]]


def test_speaker_says_what_is_wrong():
    for call, words in [('speaker(pitch=3)', "pitch is a number from 0 to 2"), ('speaker(rate=0)', "rate is a number"), ('speaker(voice=4)', "name such as"),
                        ('speaker(lang="")', "the language"), ('speaker(name=3)', "the name is text"),
                        ('say("x", speaker="bob")', "takes a speaker made with speaker()"), ('mouth(1, 2, speaker=3)', "takes a speaker made with speaker()"),
                        ('voice_level(3)', "takes a speaker made with speaker()")]:
        r = start(call)
        assert r["error"] and words in r["error"], (call, r["error"])


def test_a_file_that_calls_only_speaker_or_voices_is_given_the_voice():
    for call in ("speaker()", "voices()"):
        r = start("x = %s\nprint(%r in dir())\n" % (call, call.split("(")[0]))
        assert r["error"] is None and r["out"] == "True\n", (call, r)
    from pyctures import pages
    assert pages.uses_library("bob = speaker(voice='deep')", "pysay") and pages.uses_library("print(voices())", "pysay") and not pages.uses_library("print(bob.speaker())", "pysay")
    js = (WEB / "pyctures.js").read_text()
    assert "say|say_at|voices|speaker|speaking" in js


def test_the_names_the_page_gives_a_javascript_scene_have_python_spellings():
    js = (WEB / "voice" / "say.js").read_text()
    import re
    names = re.search(r"export const sceneNames = \[(.*?)\]", js).group(1)
    assert [n.strip().strip("'") for n in names.split(",")] == ["say", "sayAt", "voices", "speaker", "speaking", "voiceLevel", "voiceShape", "mouth"]
    assert pysay._NAMES == ("say", "say_at", "voices", "speaker", "speaking", "voice_level", "voice_shape", "mouth")


def test_the_two_faces_example_says_seven_lines_in_turn_with_each_mouth_its_own():
    src = (ROOT / "examples" / "two_faces.py").read_text()
    assert max(len(line) for line in src.splitlines()) <= 70
    r = start(src, voices=[])
    assert r["error"] is None and r["told"]
    assert tick()["error"] is None
    click = tick(events=[{"k": "input", "e": {"type": "pointerdown", "id": 1, "x": 10, "y": 10}}])
    said = [c[5] for c in click["cmds"] if c[3] == H_SAY and c[4] == "say"]
    assert click["error"] is None and [c[0][:5] for c in said] == ["Hello", "Um...", "Nope.", "Socks", "They "] + [said[5][0][:5], said[6][0][:5]]
    assert [c[5] for c in said] == [1, 2, 1, 2, 1, 2, 1] and [c[1] for c in said][:2] == ["deep", "squeaky"]
    sam, pip = pyctures.S.ns["sam"], pyctures.S.ns["pip"]
    assert (sam.voice, pip.voice) == ("deep", "squeaky")
    # The page tells each face its own mouth: only Sam's is open, and only Sam's mouth is drawn open.
    frame = tick(events=[told_speakers(r, **{"1": {"level": 0.7, "width": 0.4, "viseme": "ah", "speaking": True}})])
    mouths = [c[5] for c in frame["cmds"] if c[3] == H_SAY and c[4] == "mouth"]
    assert len(mouths) == 2 and mouths[0][5] == 0.7 and mouths[1][5] == 0.0


def test_speaker_takes_like_and_fallback_and_passes_them_to_the_page():
    r = start('''
        kid = speaker("kokoro:af_heart", like={"gender": "female", "age": "child"}, fallback=["system:Samantha", "high"], name="Kid")
    ''')
    assert r["error"] is None
    assert r["cmds"] == [["call", 2, 0, H_SAY, "speaker", [1, "kokoro:af_heart", 1, 1, "en", "Kid", {"gender": "female", "age": "child"}, ["system:Samantha", "high"]]]]
    for call, words in [('speaker(like=3)', "describes a voice"), ('speaker(like={"mood": 1})', "gender, age, pitch and rate"),
                        ('speaker(like={"pitch": -1})', "above 0"), ('speaker(fallback="high")', "list of voices")]:
        r = start(call)
        assert r["error"] and words in r["error"], (call, r["error"])


# ---------------------------------------------------------------- in a browser, a frame at a time

def wav(n, amp=0.5, rate=48000):
    """A mono 16-bit WAV: cos(i / 20), so that its first sample is full scale."""
    data = b"".join(struct.pack("<h", round(amp * 32767 * math.cos(i / 20))) for i in range(n))
    head = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) + b"data" + struct.pack("<I", len(data))
    return head + data


SCENE = '''
n = 0
said = []

def draw():
    global n
    background("black")
    if n == 37:
        said.append(say("Hello there"))
        said.append(say("Nobody made this one"))
        said.append(say("Typed " + "it"))
    n += 1
    js.pySaid = said
'''

PAGE = '''<!doctype html><meta charset="utf-8"><body style="margin:0;background:#000">
<div id="s" style="width:320px;height:180px"></div>
<script>
window.PYCTURES_NO_AUTO = true
window.spoken = []
class U { constructor(text) { this.text = text } }
window.SpeechSynthesisUtterance = U
Object.defineProperty(window, "speechSynthesis", { configurable: true, value: { speak: (u) => window.spoken.push(u.text), cancel() {}, getVoices: () => [] } })
</script>
<script type="module">
import { mount } from "/pyctures/pyctures.js"
window.film = async (fps, frames) => {
  const noted = [], warned = [], warn = console.warn
  console.warn = (...a) => { warned.push(a.join(" ")) }
  const host = {
    lookup: (r) => (r.text === "Hello there" && !r.voice ? { key: "abcdef0123456789", file: "voice/abcdef0123456789.wav", duration: 0.5, provider: "fake", voice: "calm", lang: "en" } : null),
    note: (r) => noted.push(r),
  }
  const scene = mount(document.getElementById("s"), { src: "say.py", stepped: { fps }, server: true, voice: host })
  await scene.ready
  const parts = []
  for (let f = 0; f < frames; f++) {
    if (f) await scene.step()
    parts.push(scene.sound.take())
  }
  await scene.sound.stepTo(frames / fps)
  parts.push(scene.sound.take())
  const left = new Float32Array(parts.reduce((n, p) => n + (p ? p.length : 0), 0))
  let at = 0
  for (const p of parts) if (p) { left.set(p.left, at); at += p.length }
  let first = -1, last = -1, peak = 0
  for (let i = 0; i < left.length; i++) { const a = Math.abs(left[i]); if (a > 1e-4) { if (first < 0) first = i; last = i } if (a > peak) peak = a }
  console.warn = warn
  return { first, last, peak, noted, warned, spoken: window.spoken, said: Array.from(window.pySaid || []), errors: scene.errors, status: scene.status, asked: scene.say && scene.say.asked.map((a) => a.text), unresolved: scene.say && scene.say.unresolved.map((a) => a.text) }
}
</script>
'''


# The levels of frames 36 to 45 of the face below, as pictures.js's test measures them: the line is said in frame 37.
SAME_AS_JAVASCRIPT = [0, 0, 0.6708, 0.8916, 0.9643, 0.9883, 0.9961, 0.9987, 0.9996, 0.9999]

FACE = '''
n = 0
levels = []
widths = []
spoken = []

def draw():
    global n
    background("white")
    if n == 37:
        say("Hello there")
    levels.append(voice_level())
    widths.append(voice_shape()["width"])
    spoken.append(speaking())
    mouth(100, 60, size=80)
    n += 1
    js.pyLevels = levels
    js.pyWidths = widths
    js.pySpeaking = spoken
'''

FACE_PAGE = '''<!doctype html><meta charset="utf-8"><body style="margin:0;background:#000">
<div id="s" style="width:320px;height:180px"></div>
<script>
window.PYCTURES_NO_AUTO = true
window.spoken = []
class U { constructor(text) { this.text = text } }
window.SpeechSynthesisUtterance = U
Object.defineProperty(window, "speechSynthesis", { configurable: true, value: { speak: (u) => window.spoken.push(u.text), cancel() {}, getVoices: () => [] } })
</script>
<script type="module">
import { mount } from "/pyctures/pyctures.js"
import { drawMouth } from "/pyctures/voice/say.js"
window.face = async (fps, frames) => {
  const host = { lookup: (r) => (r.text === "Hello there" ? { key: "abcdef0123456789", file: "voice/abcdef0123456789.wav", duration: 0.5, provider: "fake", voice: "calm", lang: "en" } : null), note() {} }
  const scene = mount(document.getElementById("s"), { src: "face.py", stepped: { fps }, server: true, voice: host })
  await scene.ready
  const canvas = document.querySelector("#s canvas")
  const same = [], dark = []
  for (let f = 0; f < frames; f++) {
    if (f) await scene.step()
    const levels = window.pyLevels || [], level = levels[levels.length - 1] || 0
    const widths = window.pyWidths || [], width = widths.length ? widths[widths.length - 1] : 0.5
    const mine = canvas.getContext("2d").getImageData(0, 0, 320, 180).data
    // The very same mouth, drawn by the page's own function on a white canvas.
    const other = document.createElement("canvas"); other.width = 320; other.height = 180
    const k = other.getContext("2d"); k.fillStyle = "white"; k.fillRect(0, 0, 320, 180)
    drawMouth(k, 100, 60, { size: 80, level, width, color: "black" })
    const theirs = k.getImageData(0, 0, 320, 180).data
    // (A canvas that is on show may be drawn by the graphics card and one that is not by the processor, which differ by a
    // fraction of a pixel along an edge. So: no pixel is far off, and the ink is the same to within three percent.)
    let worst = 0, inkMine = 0, inkTheirs = 0, count = 0
    for (let i = 0; i < mine.length; i += 4) { worst = Math.max(worst, Math.abs(mine[i] - theirs[i])); inkMine += 255 - mine[i]; inkTheirs += 255 - theirs[i]; if (mine[i] < 128) count++ }
    same.push(worst <= 160 && Math.abs(inkMine - inkTheirs) <= 0.03 * inkTheirs + 100); dark.push(count)
  }
  return { levels: Array.from(window.pyLevels || []), speaking: Array.from(window.pySpeaking || []), same, dark, errors: scene.errors, status: scene.status }
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


def test_a_recorded_scene_puts_the_recording_on_the_exact_sample_and_reports_the_line_with_none(browser, pyctures_run, tmp_path):
    if "createSteppedPlayer" not in (WEB / "synths" / "synths.js").read_text(encoding="utf-8"):
        pytest.skip("the copy of synths.js here has no stepped player yet (scripts/sync_libraries.py brings it in)")
    (tmp_path / "say.py").write_text(SCENE)
    (tmp_path / "film.html").write_text(PAGE)
    (tmp_path / "voice").mkdir()
    (tmp_path / "voice" / "abcdef0123456789.wav").write_bytes(wav(24000))
    p = pyctures_run(tmp_path)
    page = browser.new_page(viewport={"width": 400, "height": 300})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(p.url + "film.html")
    page.wait_for_function("() => typeof window.film === 'function'")
    got = page.evaluate("([fps, frames]) => window.film(fps, frames)", [60, 90])
    assert not errors and not got["errors"] and got["status"] == "running"
    # Python was timed from the recording (0.5) for the line written out, and by the estimate for the others.
    assert got["said"] == [0.5, 1.6, 0.8]
    # The recording begins on exactly the sample of frame 37, and is all there.
    want = round(37 * 48000 / 60)
    assert got["first"] == want and want + 24000 - 2 <= got["last"] < want + 24000 + 1500 and got["peak"] > 0.1
    # The two lines with no recording are told to the host, kept as unresolved, said once each, and not spoken.
    assert [n["text"] for n in got["noted"]] == ["Hello there", "Nobody made this one", "Typed it"]
    assert [n["source"] for n in got["noted"]] == ["literal", "literal", "runtime"]
    # The same record the JavaScript host gets for the same lines (text, voice, lang, source, line).
    assert [(n["lang"], n.get("voice"), n.get("line")) for n in got["noted"]] == [("en", None, 9), ("en", None, 10), ("en", None, 11)]
    assert got["unresolved"] == ["Nobody made this one", "Typed it"] and got["spoken"] == []
    assert len(got["warned"]) == 2 and all("cannot be recorded" in w for w in got["warned"])
    page.close()


def face(browser, pyctures_run, tmp_path, name):
    """The talking face of FACE, recorded 120 frames at 60 a second with a one-line host: what it saw and what it drew."""
    folder = tmp_path / name
    folder.mkdir()
    (folder / "face.py").write_text(FACE)
    (folder / "film.html").write_text(FACE_PAGE)
    (folder / "voice").mkdir()
    (folder / "voice" / "abcdef0123456789.wav").write_bytes(wav(24000))
    p = pyctures_run(folder)
    page = browser.new_page(viewport={"width": 400, "height": 300})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(p.url + "film.html")
    page.wait_for_function("() => typeof window.face === 'function'")
    got = page.evaluate("([fps, frames]) => window.face(fps, frames)", [60, 120])
    page.close()
    assert not errors and not got["errors"] and got["status"] == "running"
    return got


def test_a_recorded_face_follows_the_audio_and_draws_the_pages_own_mouth(browser, pyctures_run, tmp_path):
    if "createSteppedPlayer" not in (WEB / "synths" / "synths.js").read_text(encoding="utf-8"):
        pytest.skip("the copy of synths.js here has no stepped player yet (scripts/sync_libraries.py brings it in)")
    one = face(browser, pyctures_run, tmp_path, "one")
    levels = one["levels"]
    top = max(levels)
    at = levels.index(top)
    # 0 until the frame the line is said in (37), rises with the WAV's loud tone, and is 0 after it ends.
    assert len(levels) == 120 and all(v == 0 for v in levels[:38])
    assert top > 0.5 and 38 <= at < 37 + 36 and levels[-1] == 0
    assert one["speaking"][36] is False and one["speaking"][40] is True and one["speaking"][37 + 31] is False
    # Parity: the mouth Python drew in each frame is the page's own mouth at that frame's level (to within the raster's edge).
    assert all(one["same"]), [i for i, ok in enumerate(one["same"]) if not ok][:5]
    assert one["dark"][0] > 0 and one["dark"][at] > 2 * one["dark"][0] and abs(one["dark"][-1] - one["dark"][0]) <= 0.1 * one["dark"][0]
    # The very levels pictures.js gets for the same WAV, the same line and the same frame (scripts/test-say.mjs pins these too).
    assert levels[36:46] == pytest.approx(SAME_AS_JAVASCRIPT, abs=5e-4)
    # The same scene again gives the same levels, frame for frame.
    two = face(browser, pyctures_run, tmp_path, "two")
    assert two["levels"] == levels and two["dark"] == one["dark"]
