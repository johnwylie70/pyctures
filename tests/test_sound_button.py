"""The sound button, `sound_button()` and `sound_is_on()`, and the card a demo asks with, `ask_about_sound()`.

They are a library of Pyctures' own (web/manners: manners.js and pymanners.py) that only a file naming one of
them is given. The page draws both, holds the switch and acts on a tap at once; Python writes one command and
is told with the next frame. Real (headless) Chromium, started muted. What is heard is read from the sound
engine itself, as in test_sound.py.

Needs Playwright; the test of a built page needs Pyodide's CDN too.
"""
import json
import re
import sys
import textwrap

import pytest

import pyctures
from conftest import ROOT, SHOTS
from test_browser import Watched, cdn_reachable
from test_sound import CONTROLS, HEARD, SCENE, heard, placed, requests_of, wait_for, write

playwright = pytest.importorskip("playwright.sync_api")

BESIDE = ROOT.parent
needs_cdn = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")
INFO = {"width": 400, "height": 300, "pixel_ratio": 2}
MANNERS_JS = ROOT / "src" / "pyctures" / "web" / "manners" / "manners.js"
# The library is beside Pyctures; `pyctures run` and a page put it where Python finds it, and so does this.
sys.path.append(str(MANNERS_JS.parent))
import pymanners  # noqa: E402
H_MANNERS = 14

# A game with a tune: what Python knows goes where a test can read it.
GAME = '''
from synths import *
play_notes("C4 E4 G4 C5 G4 E4", 0.2, repeat=True)
sound = %s
frames = 0
downs = 0

def update(dt):
    global frames
    frames += 1
    js.pyState = [frames, downs, sound_is_on(), sound.on, sound.asking]

def on_mouse_down(x, y):
    global downs
    downs += 1

def draw():
    background("#0b1020")
    circle(width / 2, height / 2, 40, "gold")
'''
PLAIN = '''
sound = sound_button()

def update(dt):
    js.pyState = [sound_is_on(), sound.over(width - 20, 20), sound.over(100, 100)]

def draw():
    background("#f4f1e8")
    circle(width / 2, height / 2, 40, "tomato")
'''

BUTTON = """() => {
  const el = document.querySelector('[data-pyctures-src]'), b = el.querySelector('[data-sound-button]')
  if (!b || getComputedStyle(b).display === 'none') return null
  const box = el.getBoundingClientRect(), r = b.getBoundingClientRect()
  return { x: r.left + r.width / 2, y: r.top + r.height / 2, left: Math.round(r.left - box.left), top: Math.round(r.top - box.top), right: Math.round(box.right - r.right), bottom: Math.round(box.bottom - r.bottom), size: Math.round(r.width), sound: b.dataset.sound, look: b.dataset.look, label: b.getAttribute('aria-label') }
}"""
CARD = """() => {
  const c = document.querySelector('[data-pyctures-src] [data-sound-card]')
  if (!c) return null
  const a = document.activeElement
  return { title: c.querySelector('[data-part=title]').textContent, buttons: [...c.querySelectorAll('button')].map((b) => b.textContent), focus: a && a.dataset ? a.dataset.answer || null : null }
}"""
KEPT = "Object.fromEntries(Object.keys(localStorage).filter((k) => /sound:on$/.test(k)).map((k) => ['on', localStorage.getItem(k)]))"
FORGET_ASKED = "for (const k of Object.keys(localStorage)) if (/sound:asked$/.test(k)) localStorage.removeItem(k)"
COVER = "(document.querySelector('.pyctures-cover') || { textContent: '' }).textContent"


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        yield b
        b.close()


@pytest.fixture(autouse=True)
def stopped():
    yield
    pyctures.stop()


def start(src, **info):
    """The first frame's reply. The command that gives the page a function to tell (`listen`) is taken out of
    `cmds` and kept as `told`, the callback's number."""
    r = json.loads(pyctures.start(textwrap.dedent(src), json.dumps({**INFO, **info})))
    listens = [c for c in r["cmds"] if c[3] == H_MANNERS and c[4] == "listen"]
    r["cmds"] = [c for c in r["cmds"] if c not in listens]
    r["told"] = listens[0][5][0] if listens else None
    return r


def tick(**payload):
    payload.setdefault("dt", 1 / 60)
    return json.loads(pyctures.tick(json.dumps(payload)))


def state(page):
    return page.evaluate("window.pyState")


def silent(page, timeout=8):
    """Switched off, nothing new sounds: what is left is the echo dying away, and then nothing."""
    return wait_for(page, lambda: heard(page)["level"] < 0.001, "silence", timeout)


def sounding(page, timeout=8):
    return wait_for(page, lambda: (lambda h: h if h["state"] == "on" and h["level"] > 0.02 else None)(heard(page)), "sound", timeout)


# ---------------------------------------------------------------- what Python writes

def test_sound_button_is_one_command_to_the_page():
    r = start("""
        b = sound_button()
        print(sound_is_on(), b.on, b.asking, b.over(10, 10))
    """)
    assert r["error"] is None
    assert r["cmds"] == [["call", 2, 0, H_MANNERS, "show", [{"corner": "top right", "colour": "auto", "key": "m"}]]]
    assert r["out"] == "True True False False\n"
    assert pymanners.H_MANNERS == H_MANNERS and r["told"]
    assert "c[3] !== 14 || c[0] !== 'call'" in MANNERS_JS.read_text()


def test_no_two_fixed_handles_are_the_same():
    """Every library's page half has a fixed handle of its own: 10 sound, 11 dials, 12 scenes, 13 effects, 14 the sound button."""
    handles = {name: value for name, value in vars(pyctures).items() if name.startswith("H_") and isinstance(value, int)}
    web = ROOT / "src" / "pyctures" / "web"
    for path in sorted(web.glob("*/*.py")):
        text = path.read_text(encoding="utf-8")
        for name, value in re.findall(r"^(H_[A-Z_]+) = (\d+)\b", text, re.M):
            # A library may name Pyctures' own handle again (synths has H_SOUND): the same name must be the same number.
            assert handles.setdefault(name, int(value)) == int(value), "%s is %s in %s" % (name, value, path.name)
    assert handles["H_MANNERS"] == 14 and handles.get("H_EFFECTS", 13) == 13
    by_number = {}
    for name, value in handles.items():
        by_number.setdefault(value, []).append(name)
    assert not {v: n for v, n in by_number.items() if len(n) > 1}, "two handles are the same"
    assert 6 not in by_number, "6 is taken where Pyctures is built into an editor"


def test_a_file_that_names_neither_is_given_neither_and_keeps_nothing():
    r = start("print([n for n in globals() if n.startswith('sound')])")
    assert r["out"] == "[]\n" and getattr(pyctures.S, "manners", None) is None and r["told"] is None
    from pyctures import pages
    assert not pages.uses_library("def draw():\n    background('navy')\n", "pymanners")
    for names in ("sound_button()\n", "if sound_is_on(): pass\n", "ask_about_sound()\n"):
        assert pages.uses_library(names, "pymanners") and pymanners._USES.search(names)
    assert "uses: /%s/ }" % pages.USES_MANNERS.pattern in (pages.WEB / "pyctures.js").read_text(encoding="utf-8")


def test_its_options_go_as_the_page_names_them():
    r = start("sound_button(inset=(16, 84))\nsound_button(inset=20)")
    assert [c[5][0]["inset"] for c in r["cmds"]] == [[16, 84], [20, 20]]
    assert "inset is how far in from the corner's two edges" in start("sound_button(inset=-1)")["error"]
    r = start('sound_button("bottom-left", size=50, color="dark", key=None)')
    assert r["cmds"][0][4:] == ["show", [{"corner": "bottom left", "colour": "dark", "key": "", "size": 50}]]
    # The card's words are not the button's: sound_button() never asks.
    assert "unexpected keyword argument 'title'" in start('sound_button(title="Music")')["error"]


def test_ask_about_sound_is_one_command_of_its_own():
    r = start("""
        b = ask_about_sound()
        print(sound_is_on(), b.asking)
    """)
    assert r["cmds"] == [["call", 2, 0, H_MANNERS, "ask", [{"corner": "top right", "colour": "auto", "key": "m", "remember": False, "wait": True}]]]
    # Until the page says, the card counts as up and the sound as off.
    assert r["out"] == "False True\n"
    r = start("""
        ask_about_sound("Music and sound effects", with_sound="Sound on", without_sound="Quiet", remember=True, wait=False,
                        corner="bottom-left", size=50)
    """)
    assert r["cmds"][0][4:] == ["ask", [{"corner": "bottom left", "colour": "auto", "key": "m", "size": 50, "remember": True, "wait": False,
                                         "title": "Music and sound effects", "withSound": "Sound on", "withoutSound": "Quiet"}]]
    assert 'ask_about_sound("middle"): that is not a corner' in start('ask_about_sound(corner="middle")')["error"]


def test_a_corner_that_is_not_one_is_said_in_plain_words():
    r = start("""
        x = 1
        sound_button("middle")
    """)
    assert r["errorLine"] == 3
    assert 'sound_button("middle"): that is not a corner. The corners are: "top right", "bottom right", "top left", "bottom left"' in r["error"]
    r = start("sound_button(size=-4)")
    assert "the size is how many points across the button is" in r["error"]


def test_the_last_choice_is_known_from_the_first_line_and_the_page_says_the_rest():
    r = start("print(sound_is_on())", saved={"sound:on": "false"})
    assert r["out"] == "False\n"
    r = start("""
        b = sound_button()
        def update(dt):
            print(sound_is_on(), b.asking, b.over(370, 20), b.over(100, 100))
    """)
    told = r["told"]
    r = tick(events=[{"k": "cb", "id": told, "e": {"on": False, "asking": True, "box": None}}])
    assert r["out"] == "False True False False\n"
    r = tick(events=[{"k": "cb", "id": told, "e": {"on": True, "asking": False, "box": [358, 8, 34]}}])
    assert r["out"] == "True False True False\n"
    assert tick()["out"] == "True False True False\n"


def test_setting_on_is_one_command_and_is_known_at_once():
    r = start("""
        b = sound_button()
        b.on = False
        print(sound_is_on())
    """)
    assert r["out"] == "False\n"
    assert r["cmds"][1] == ["call", 3, 0, H_MANNERS, "set", [False]]


def test_a_button_alone_never_counts_as_asking_even_with_sound():
    sys.path.append(str(ROOT / "src" / "pyctures" / "web" / "synths"))
    try:
        r = start("""
            from synths import *
            b = sound_button()
            print(sound_is_on(), b.asking)
        """)
        assert r["out"] == "True False\n" and [c[4] for c in r["cmds"] if c[3] == H_MANNERS] == ["show"]
    finally:
        sys.path.pop()


def test_the_button_s_code_is_the_same_as_pictures_js_s():
    """The page's half is the same text in both libraries. Compared when pictures.js is beside this repository and has it."""
    def code(text):
        found = re.search(r"\nconst SOUND_ON = .*?\nconst readsM = [^\n]*\n", text, re.S)
        return found.group(0) if found else None
    ours = code(MANNERS_JS.read_text())
    assert ours
    compared = 0
    for sibling in ("pictures.js-manners", "pictures.js"):
        path = BESIDE / sibling / "manners" / "manners.js"
        theirs = code(path.read_text()) if path.is_file() else None
        if theirs is None:
            continue
        compared += 1
        assert ours == theirs, "the sound button differs from %s: change one and change the other" % path
    if not compared:
        pytest.skip("pictures.js is not beside this repository, or has no sound button yet")


# ---------------------------------------------------------------- the button

def test_run_a_button_and_no_sound_loads_its_own_file_and_no_sound_library(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, PLAIN))
    w = Watched(browser, "about:blank")
    asked = requests_of(w.page)
    w.page.goto(server.url)
    w.wait_running()
    wait_for(w.page, lambda: state(w.page), "Python's first frame")
    b = w.page.evaluate(BUTTON)
    assert (b["size"], b["right"], b["top"], b["sound"]) == (34, 8, 8, "on") and "Sound is on" in b["label"]
    w.page.wait_for_timeout(700)
    assert w.page.evaluate(BUTTON)["look"] == "dark", "on a light scene the button is dark"
    assert w.page.evaluate(CARD) is None, "the button alone asks nothing"
    assert sorted(u[len(server.url):] for u in asked) == ["", "pyctures/manners/manners.js", "pyctures/pyctures.js", "scene.py"]
    assert w.page.evaluate(SCENE + ".sound.player") is None, "no player, and so no AudioContext, was made"
    # Python knows where it is, and that the sound is on; a tap on it is told to Python with the next frame.
    wait_for(w.page, lambda: state(w.page) == [True, True, False], "Python told where the button is")
    w.page.mouse.click(b["x"], b["y"])
    wait_for(w.page, lambda: state(w.page) == [False, True, False], "Python told the sound is off")
    assert w.page.evaluate(BUTTON)["sound"] == "off" and w.page.evaluate(KEPT) == {"on": "false"}
    assert w.page.evaluate(SCENE + ".sound.player") is None, "and switching it loads nothing"
    assert not [u for u in asked if "synths" in u]
    # Kept: the scene opened again is still off, and Python knows from its first line.
    w.page.reload()
    w.wait_running()
    wait_for(w.page, lambda: state(w.page) == [False, True, False], "still off")
    assert w.page.evaluate(BUTTON)["sound"] == "off"
    assert not w.errors, w.errors


def test_a_tap_on_the_button_silences_the_scene_and_is_not_a_tap_on_the_game(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, GAME % "sound_button()"))
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    assert page.evaluate(CARD) is None
    page.mouse.click(400, 300)          # the first touch turns the sound on
    sounding(page)
    b = page.evaluate(BUTTON)
    page.mouse.click(b["x"], b["y"])
    assert page.evaluate(BUTTON)["sound"] == "off"
    silent(page)
    wait_for(page, lambda: state(page)[2:] == [False, False, False], "Python told the sound is off")
    assert state(page)[1] == 1, "the tap on the button was not a tap on the game"
    assert page.evaluate("document.activeElement === %s.canvas" % SCENE), "and the game keeps the keyboard"
    page.mouse.click(b["x"], b["y"])
    sounding(page)
    wait_for(page, lambda: state(page)[2:] == [True, True, False], "Python told the sound is on")
    # M is the same switch, and Python is not handed the key.
    page.keyboard.press("m")
    assert page.evaluate(BUTTON)["sound"] == "off"
    silent(page)
    page.keyboard.press("M")
    sounding(page)
    assert page.evaluate(KEPT) == {"on": "true"}
    assert not w.errors, w.errors


def test_mute_sound_in_python_is_the_same_switch(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, GAME % "sound_button()" + '''
def on_key_down(key):
    if key == "q": mute_sound()
    if key == "w": unmute_sound()
    if key == "e": sound.on = False
'''))
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    page.mouse.click(400, 300)
    sounding(page)
    page.keyboard.press("q")
    wait_for(page, lambda: page.evaluate(BUTTON)["sound"] == "off", "the button shows what mute_sound() did")
    wait_for(page, lambda: state(page)[2] is False, "sound_is_on() says so a frame later")
    silent(page)
    assert page.evaluate(KEPT) == {}, "what the code switched is not kept as a person's choice"
    page.keyboard.press("w")
    wait_for(page, lambda: page.evaluate(BUTTON)["sound"] == "on", "and unmute_sound()")
    sounding(page)
    page.keyboard.press("e")
    wait_for(page, lambda: page.evaluate(BUTTON)["sound"] == "off", "sound.on = False")
    silent(page)
    assert not w.errors, w.errors


def test_the_button_does_not_wait_for_python(browser, pyctures_run, tmp_path):
    """Python here takes half a second over every frame. The button still switches at once: the page does it."""
    server = pyctures_run(write(tmp_path, GAME % "sound_button()" + '''
import time
def draw():
    time.sleep(0.5)
    background("#0b1020")
'''))
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    page.mouse.click(400, 300)
    sounding(page, 20)
    b = page.evaluate(BUTTON)
    took = page.evaluate("""async ([x, y]) => {
      const s = document.querySelector('[data-pyctures-src]').pycturesScene
      const frames = s.r.sent, t0 = performance.now()
      const el = document.elementFromPoint(x, y)
      el.click()
      while (!s.manners.muted && performance.now() - t0 < 2000) await new Promise((r) => setTimeout(r, 5))
      return { ms: performance.now() - t0, frames: s.r.sent - frames, sound: el.dataset.sound }
    }""", [b["x"], b["y"]])
    assert took["sound"] == "off" and took["ms"] < 100, "the switch took %d ms" % took["ms"]
    assert took["frames"] <= 1, "and did not wait for a frame from Python"
    silent(page)
    wait_for(page, lambda: state(page)[2] is False, "Python is told with a later frame")


def test_the_button_keeps_off_the_controls(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, '''
from pyctures import *
from synths import *
from pydials import *

lead = make_synth("lead")
dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
scope(lead)
keyboard(lead, octave=4)
sound_button()

def draw():
    background("midnightblue")
'''))
    for size in ((390, 780), (820, 1100), (1280, 800)):
        w = Watched(browser, server.url, size=size)
        w.wait_running()
        controls = placed(w.page)
        w.page.wait_for_timeout(1700)
        b = w.page.evaluate(BUTTON)
        r = (b["x"] - b["size"] / 2, b["y"] - b["size"] / 2, b["x"] + b["size"] / 2, b["y"] + b["size"] / 2)
        hit = [c["kind"] for c in controls if c["w"] and c["h"] and r[0] < c["x"] + c["w"] and r[2] > c["x"] and r[1] < c["y"] + c["h"] and r[3] > c["y"]]
        assert len(controls) == 4 and not hit, "at %s the button is on %s" % (size, hit)
        assert r[0] >= 0 and r[1] >= 0 and r[2] <= size[0] and r[3] <= size[1]
        SHOTS.mkdir(exist_ok=True)
        w.page.screenshot(path=str(SHOTS / ("sound-button-panel-%d.png" % size[0])))
        assert not w.errors, w.errors
        w.page.close()


# ---------------------------------------------------------------- the card

def test_the_card_holds_the_sound_and_the_game_until_it_is_answered(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, GAME % "ask_about_sound()"))
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    wait_for(page, lambda: page.evaluate(CARD), "the card")
    card = page.evaluate(CARD)
    assert card == {"title": "This demo has sound", "buttons": ["Play with sound", "Play without sound"], "focus": "on"}
    assert page.evaluate(BUTTON) is None, "the button waits behind the card"
    page.wait_for_timeout(900)
    SHOTS.mkdir(exist_ok=True)
    page.screenshot(path=str(SHOTS / "sound-card.png"))
    sent = page.evaluate(SCENE + ".r.sent")
    assert sent <= 3, "Python is asked for no more frames behind the card"
    # A tap beside the card is not a tap on the game, and turns nothing on: no words ask for a tap either.
    page.mouse.click(400, 60)
    page.keyboard.press("x")
    page.wait_for_timeout(500)
    assert page.evaluate(SCENE + ".r.sent") == sent
    assert page.evaluate(COVER) == "", "the page does not also ask for a tap"
    got = heard(page)
    assert got["level"] == 0 and got["state"] != "on"
    # Only the person answers: a click or a key that a program makes (an agent's scripted tap) is ignored.
    page.evaluate("""() => {
      for (const b of document.querySelectorAll('[data-sound-card] button')) { b.click(); b.dispatchEvent(new MouseEvent('click', { bubbles: true })) }
      document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    }""")
    page.wait_for_timeout(300)
    assert page.evaluate(CARD) and page.evaluate(SCENE + ".r.sent") == sent and page.evaluate(KEPT) == {}
    page.click("[data-sound-card] button[data-answer=on]")
    sounding(page)
    wait_for(page, lambda: state(page) and state(page)[0] > 5, "the game starts")
    wait_for(page, lambda: state(page)[2:] == [True, True, False], "Python told the sound is on")
    assert state(page)[1] == 0, "none of the taps reached the game"
    assert page.evaluate(CARD) is None and page.evaluate(BUTTON)["sound"] == "on"
    assert page.evaluate(KEPT) == {"on": "true"}
    assert page.evaluate("document.activeElement === %s.canvas" % SCENE)
    # Run again within a few minutes: it does not ask again.
    page.reload()
    w.wait_running()
    page.wait_for_timeout(500)
    assert page.evaluate(CARD) is None and page.evaluate(BUTTON)["sound"] == "on"
    assert not w.errors, w.errors


def test_play_without_sound_and_escape(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, GAME % "ask_about_sound()"))
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    wait_for(page, lambda: page.evaluate(CARD), "the card")
    page.click("[data-sound-card] button[data-answer=off]")
    wait_for(page, lambda: state(page) and state(page)[0] > 5, "the game starts")
    assert state(page)[2:] == [False, False, False]
    assert page.evaluate(CARD) is None and page.evaluate(BUTTON)["sound"] == "off" and page.evaluate(KEPT) == {"on": "false"}
    page.wait_for_timeout(600)
    assert heard(page)["level"] < 0.001 and page.evaluate(COVER) == "", "nothing is heard, and no words ask for a tap"
    # The button later turns it on.
    b = page.evaluate(BUTTON)
    page.mouse.click(b["x"], b["y"])
    sounding(page)
    page.mouse.click(b["x"], b["y"])
    # Opened afresh it asks again, with last time's answer under Enter; Escape is "without".
    page.evaluate(FORGET_ASKED)
    page.reload()
    w.wait_running()
    wait_for(page, lambda: page.evaluate(CARD), "the card again")
    assert page.evaluate(CARD)["focus"] == "off"
    page.keyboard.press("Escape")
    wait_for(page, lambda: state(page) and state(page)[0] > 5, "the game starts")
    assert page.evaluate(CARD) is None and page.evaluate(BUTTON)["sound"] == "off"
    assert not w.errors, w.errors


def test_remember_wait_and_the_card_s_own_words(browser, pyctures_run, tmp_path):
    scene = write(tmp_path, GAME % 'ask_about_sound("Music and sound effects", remember=True, wait=False, with_sound="Sound on", without_sound="Quiet")')
    server = pyctures_run(scene)
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    wait_for(page, lambda: page.evaluate(CARD), "the card")
    assert page.evaluate(CARD) == {"title": "Music and sound effects", "buttons": ["Sound on", "Quiet"], "focus": "on"}
    # wait=False: the scene runs behind the card, still silent, and Python knows it is asking.
    wait_for(page, lambda: state(page) and state(page)[0] > 5, "frames behind the card")
    assert state(page)[2:] == [False, False, True] and heard(page)["level"] == 0
    page.click("[data-sound-card] button[data-answer=off]")
    wait_for(page, lambda: state(page)[2:] == [False, False, False], "answered")
    # remember=True: there is an answer, so it is not asked again, however long ago that was.
    page.evaluate(FORGET_ASKED)
    page.reload()
    w.wait_running()
    wait_for(page, lambda: state(page) and state(page)[0] > 5, "running")
    assert page.evaluate(CARD) is None and page.evaluate(BUTTON)["sound"] == "off"
    assert not w.errors, w.errors


def test_a_host_is_told_asking_and_off_and_never_to_wait_for_a_tap(browser, pyctures_run, tmp_path):
    server = pyctures_run(write(tmp_path, GAME % "ask_about_sound()"))
    w = Watched(browser, server.url)
    w.wait_running()
    page = w.page
    # The same scene again, with a host listening to the sound's state.
    page.evaluate("""async () => {
      localStorage.clear()
      window.states = []
      const s = document.querySelector('[data-pyctures-src]').pycturesScene
      s.opt.sound = { onState: (state) => window.states.push(state) }
      await s.start()
    }""")
    wait_for(page, lambda: page.evaluate(CARD), "the card")
    page.wait_for_timeout(900)
    states = page.evaluate("window.states")
    assert "asking" in states and "waiting" not in states and "on" not in states, states
    page.click("[data-sound-card] button[data-answer=off]")
    page.wait_for_timeout(500)
    states = page.evaluate("window.states")
    assert states[-1] == "off" and "waiting" not in states, states
    b = page.evaluate(BUTTON)
    page.mouse.click(b["x"], b["y"])
    wait_for(page, lambda: page.evaluate("window.states").pop() == "on", "the host told the sound is on")
    assert not w.errors, w.errors


@needs_cdn
@pytest.mark.parametrize("html", [False, True], ids=["folder", "one file"])
def test_build_the_card_and_the_button_with_python_in_the_browser(browser, static_server, tmp_path, html):
    from pyctures.build import build as make
    out = tmp_path / ("scene.html" if html else "site")
    said = []
    make(write(tmp_path, GAME % "ask_about_sound()"), out, say=said.append)
    if html:
        assert "with the sound button" in said[0]
    else:
        assert (out / "pyctures" / "manners" / "manners.js").is_file() and (out / "pyctures" / "manners" / "pymanners.py").is_file()
    w = Watched(browser, static_server(tmp_path if html else out) + ("scene.html" if html else ""))
    w.wait_running(timeout=120)
    page = w.page
    wait_for(page, lambda: page.evaluate(CARD), "the card")
    page.click("[data-sound-card] button[data-answer=on]")
    sounding(page, 20)
    wait_for(page, lambda: state(page) and state(page)[2:] == [True, True, False], "Python told the sound is on")
    b = page.evaluate(BUTTON)
    page.mouse.click(b["x"], b["y"])
    silent(page)
    wait_for(page, lambda: state(page)[2:] == [False, False, False], "Python told the sound is off")
    assert not w.errors, w.errors


# ---------------------------------------------------------------- recorded a frame at a time

def test_python_knows_it_is_being_recorded_and_counts_the_sound_as_on():
    r = start("""
        b = ask_about_sound()
        print(sound_is_on(), b.asking)
    """, vt=0.0, saved={"sound:on": "false"})
    assert r["out"] == "True False\n"


def test_a_recorded_scene_shows_no_card_and_no_button_and_its_sound_starts_on_sample_0(browser, pyctures_run, tmp_path):
    """A recording has nobody to ask and is made with its sound: the clapperboard of test_stepped.py, with
    ask_about_sound() as its first line and "sound off" kept from last time, filmed twice."""
    import test_stepped
    if not test_stepped.stepped_copies():
        pytest.skip("the copies of synths.js and synths.py here have no stepped player yet")
    clap = test_stepped.CLAP.replace("set_tempo(120)", "sound = ask_about_sound()\nset_tempo(120)").replace(
        "    js.pySeen = seen", "    js.pySeen = seen\n    js.pyOn = [sound_is_on(), sound.asking]")
    assert "ask_about_sound()" in clap and "js.pyOn" in clap
    (tmp_path / "clap.py").write_text(clap)
    (tmp_path / "film.html").write_text(test_stepped.PAGE.replace(
        "window.film = async (fps, frames) => {",
        "window.film = async (fps, frames) => {\n  for (const k of Object.keys(localStorage)) localStorage.removeItem(k)\n  localStorage.setItem('pyctures:/clap.py:sound:on', 'false')\n  window.laid = 0\n  new MutationObserver(() => { window.laid += document.querySelectorAll('[data-sound-card], [data-sound-button]').length }).observe(document.body, { childList: true, subtree: true })"))
    p = pyctures_run(tmp_path)
    films = []
    for _ in range(2):
        page = browser.new_page(viewport={"width": 400, "height": 300})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(p.url + "film.html")
        page.wait_for_function("() => typeof window.film === 'function'")
        got = page.evaluate("() => window.film(30, 60)")
        assert not errors and not got["errors"] and got["status"] == "running"
        assert page.evaluate("[window.laid, document.querySelectorAll('[data-sound-card], [data-sound-button]').length]") == [0, 0], "no card and no button was ever on the page"
        assert page.evaluate("window.pyOn") == [True, False]
        assert got["white"] == [0, 30] and got["starts"] == [0, 48000], "the first note is on sample 0, and the next on its own frame"
        assert got["total"] == 60 * 1600 and len(got["seen"]) == 60, "every frame was made: nothing waited for an answer"
        films.append([got["white"], got["starts"], got["total"]])
        page.close()
    assert films[0] == films[1]
