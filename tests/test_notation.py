"""Sheet music: `from pynotation import *` (the library pynotation, whose page half is notation.js, handle 15).

In a real (headless) Chromium, run by `pyctures run`: a scene that imports no sheet music is sent nothing; one
that does has its music written out in the page over the scene and under its controls, and the sound with it; a
tune is begun when the sound is on and Python is told each note as it sounds; a song is followed in the page
from its own place; a keyboard plays a page; and what `pyctures build` writes, with its size with and without.
How music is written out and laid out is measured in the library's own repository (notation.js). Nothing is heard.
"""
import json
import textwrap

import pytest

import pyctures
from pyctures import build as builder
from pyctures import pages
from test_browser import Watched

sync_api = pytest.importorskip("playwright.sync_api")

STAGE = "(document.querySelector('[data-pyctures-src] canvas') || {})[Symbol.for('notation.stage')]"
PAGE = STAGE + ".pages[0]"
# The first page of music is written out and laid out.
READY = "(%s && %s && %s.plan)" % (STAGE, PAGE, PAGE)
LAYERS = """[...document.querySelector('[data-pyctures-src] canvas').parentElement.children].filter((c) => c.tagName === 'CANVAS' || c.dataset.notationLayer !== undefined)
  .map((c, i) => i === 0 ? 'scene' : c.dataset.notationLayer !== undefined ? 'notation' : c.dataset.dialsLayer !== undefined ? 'dials' : 'other').join()"""

# A small song in the sound's own format, version 2: a tune with a chord, an arpeggio and a glide, and a bass.
SONG = {"format": "synths-song", "version": 2, "title": "Test Tune", "speed": 6, "tempo": 150, "channels": 2, "order": [0, 0], "patterns": [{"rows": 32, "events": [
    {"row": 0, "ch": 0, "note": "C-5", "ins": 1}, {"row": 4, "ch": 0, "note": "E-5", "ins": 1}, {"row": 8, "ch": 0, "note": "G-5", "ins": 1, "chord": "maj"},
    {"row": 12, "ch": 0, "note": "A-5", "ins": 1, "glide": "1/16"}, {"row": 16, "ch": 0, "note": "C-5", "ins": 1, "arp": {"chord": "min", "rate": "1/16"}},
    {"row": 24, "ch": 0, "note": "D-5", "ins": 1}, {"row": 28, "ch": 0, "note": "off"},
    {"row": 0, "ch": 1, "note": "C-3", "ins": 2}, {"row": 8, "ch": 1, "note": "G-2", "ins": 2}, {"row": 16, "ch": 1, "note": "A-2", "ins": 2}, {"row": 24, "ch": 1, "note": "F-2", "ins": 2},
]}], "instruments": [{"name": "tune", "patch": "keys"}, {"name": "bass", "patch": "bass"}]}


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio"])
        yield b
        b.close()


def run(browser, pyctures_run, tmp_path, source, name="scene.py", size=(700, 560)):
    file = tmp_path / name
    file.write_text(textwrap.dedent(source))
    asked = []
    w = Watched(browser, pyctures_run(file).url, size=size)
    w.page.on("request", lambda r: asked.append(r.url))
    w.wait_running()
    return w, asked


# ---------------------------------------------------------------- the Python half and the handle

def test_no_two_fixed_handles_are_the_same_and_sheet_music_is_15():
    handles = {name: value for name, value in vars(pyctures).items() if name.startswith("H_") and isinstance(value, int)}
    assert handles["H_NOTATION"] == 15
    assert len(set(handles.values())) == len(handles), handles
    # 6 is taken where Pyctures is built into an editor, 12 is the page's scenes, 13 its effects and 14 its sound button.
    assert not set(handles.values()) & {6} and handles["H_NOTATION"] not in (12, 13, 14)
    js = (pages.WEB / "pyctures.js").read_text()
    assert "H.set(15, sheets)" in js
    import sys
    sys.path.append(str(pages.WEB / "notation"))
    try:
        import pynotation
        assert "H_NOTATION" in (pages.WEB / "notation" / "pynotation.py").read_text() and pynotation.__all__ == ["show_notes", "make_sheet", "theme"]
    finally:
        sys.path.pop()


def test_a_scene_with_sheet_music_has_the_sound_too_and_a_plain_scene_has_neither():
    with_music = "from pyctures import *\nfrom pynotation import *\nshow_notes('C4 E4')\n"
    assert pages.uses_library(with_music, "pynotation") and pages.uses_library(with_music, "synths")
    for plain in ("def draw():\n    background('navy')\n", "notes = [1, 2]\n# from pynotation import *\n", "from synths import *\nplay_notes('C4')\n"):
        assert not pages.uses_library(plain, "pynotation")
    assert not pages.uses_library("def draw():\n    pass\n", "synths") and pages.uses_library("from synths import *\n", "synths")


def test_python_sends_one_command_to_handle_15_for_a_page_of_music():
    info = json.dumps({"width": 400, "height": 300, "pixel_ratio": 1})
    import sys
    sys.path.append(str(pages.WEB / "notation"))
    try:
        reply = json.loads(pyctures.start('from pynotation import *\npage = show_notes("C4 E4 G4", "quarter", title="Up")\n', info))
    finally:
        sys.path.pop()
        pyctures.stop()
    assert reply["error"] is None, reply["error"]
    made = [c for c in reply["cmds"] if c[0] == "call" and c[4] == "make"]
    assert len(made) == 1 and made[0][3] == 15 and made[0][5][:3] == [1, "C4 E4 G4", "quarter"]
    # The page has the library: Python sends no copy of it.
    assert not [c for c in reply["cmds"] if c[0] == "new"]


# ---------------------------------------------------------------- in a browser

def test_a_scene_that_imports_no_sheet_music_is_sent_none(browser, pyctures_run, tmp_path):
    w, asked = run(browser, pyctures_run, tmp_path, '''
        def draw():
            background("navy")
            circle(100, 100, 30, "gold")
        ''')
    w.page.wait_for_timeout(400)
    assert not [a for a in asked if "notation" in a or "synths" in a]
    assert w.page.evaluate(LAYERS) == "scene"
    assert not w.errors


def test_music_is_written_out_in_the_page_over_the_scene_and_under_its_controls(browser, pyctures_run, tmp_path):
    w, asked = run(browser, pyctures_run, tmp_path, '''
        from pyctures import *
        from pydials import *
        from pynotation import *
        page = show_notes("C4 E4 G4 - C5:2", "quarter", title="Up")
        sheet = make_sheet(key="G")
        sheet.add("G4", "quarter")
        second = show_notes(sheet, at="bottom")
        speed = dial("speed", 0, 10)

        def draw():
            background("navy")
        ''')
    w.page.wait_for_function("%s && %s.pages.length === 2 && %s.pages.every((p) => p.plan && p.plan.hits.length)" % (STAGE, STAGE, STAGE))
    w.page.wait_for_function("document.querySelector('[data-pyctures-src] canvas[data-dials-layer]')")
    got = w.page.evaluate("""() => { const pages = %s.pages, box = pages[0].wrap.getBoundingClientRect()
      return { layers: %s, notes: pages[0].plan.hits.length, key: pages[1].score.key, inside: box.left >= 0 && box.top >= 0 && box.right <= innerWidth, below: pages[1].box.y > pages[0].box.y + pages[0].box.h } }""" % (STAGE, LAYERS))
    assert got == {"layers": "scene,notation,notation,dials", "notes": 4, "key": 1, "inside": True, "below": True}
    # The page's half is the copy Pyctures carries, asked for by the page, and the sound came with it.
    assert [a for a in asked if a.endswith("/pyctures/notation/notation.js")] and [a for a in asked if a.endswith("/pyctures/synths/synths.js")]
    w.page.screenshot(path=str(tmp_path / "sheet-music.png"))
    assert not w.errors


def test_a_tune_begins_when_the_sound_is_on_and_python_is_told_each_note_as_it_sounds(browser, pyctures_run, tmp_path):
    w, _ = run(browser, pyctures_run, tmp_path, '''
        from pyctures import *
        from pynotation import *
        from synths import sound_time
        page = show_notes("C4 E4 G4 C5 E5 G5 C6 G5", "quarter", tempo=160)
        began = []
        page.on_note = lambda note: began.append((note.name, sound_time()))
        page.play()

        def draw():
            background("navy")
            js.pyBegan = len(began)
            if len(began) >= 5:
                js.pyGaps = [round((began[i + 1][1] - began[i][1]) * 1000) for i in range(4)]
                js.pyNames = [b[0] for b in began[:5]]
        ''')
    w.page.wait_for_function(READY)
    w.page.wait_for_timeout(700)
    before = w.page.evaluate("() => ({ began: window.pyBegan, lit: %s.sounding, state: document.querySelector('[data-pyctures-src]').pycturesScene.sound.state() })" % PAGE)
    # Until the page is touched the sound is not on (a browser's rule), though its clock runs: nothing has lit.
    if before["state"] != "on":
        assert before["began"] == 0 and before["lit"] == [], before
    w.page.mouse.click(350, 450)
    w.page.wait_for_function("window.pyNames", timeout=20000)
    got = w.page.evaluate("() => ({ names: window.pyNames, gaps: window.pyGaps, lit: %s.sounding })" % PAGE)
    assert got["names"] == ["C4", "E4", "G4", "C5", "E5"]
    # A quarter note at 160 is 375 ms: each note is told to Python that long after the last, to a few frames.
    assert all(abs(g - 375) < 90 for g in got["gaps"]), got
    assert len(got["lit"]) == 1
    assert not w.errors


def test_a_song_in_format_version_2_is_written_out_and_followed_in_the_page(browser, pyctures_run, tmp_path):
    (tmp_path / "tune.json").write_text(json.dumps(SONG))
    w, _ = run(browser, pyctures_run, tmp_path, '''
        from pyctures import *
        from synths import *
        from pynotation import *
        song = play_song("tune.json", patches={"tune": "keys", "bass": "bass"})
        page = show_notes("tune.json", follow=song)

        def draw():
            background("navy")
            js.pyBar = page.bar
        ''')
    w.page.wait_for_function(READY)
    w.page.mouse.click(350, 450)
    w.page.evaluate("""() => { window.seen = []; const page = %s, sound = document.querySelector('[data-pyctures-src]').pycturesScene.sound
      const look = () => { const p = sound.player && sound.player.songPosition(); if (p && p.state === 'playing') window.seen.push({ row: p.order * 32 + p.row + p.tick / p.speed, beat: page.beat, bass: page.active.filter((e) => e.staff === 1).map((e) => e.sounds[0])[0] }); requestAnimationFrame(look) }
      requestAnimationFrame(look) }""" % PAGE)
    w.page.wait_for_function("window.seen.length > 90", timeout=30000)
    got = w.page.evaluate("""() => { const page = %s
      const want = (row) => [[0, 48], [8, 43], [16, 45], [24, 41]].filter(([r]) => r <= row %% 32).pop()[1]
      const edge = (row) => Math.min(...[0, 8, 16, 24, 32].map((r) => Math.abs(r - (row %% 32))))
      const wrong = window.seen.filter((s) => s.bass !== want(s.row))
      return { direct: !!page.direct, worst: Math.max(0, ...wrong.map((s) => edge(s.row))), off: Math.max(0, ...window.seen.map((s) => Math.abs(s.beat - s.row / 4))), bar: window.pyBar,
        staves: page.score.staves.map((s) => s.name + ':' + s.clef), first: page.score.staves[0].events.slice(0, 5).map((e) => [e.start / 8, e.sounds, e.arp]) } }""" % PAGE)
    # A chord is written together, an arpeggio as its chord with a wavy line, and the note glided to is not a new note.
    assert got["staves"] == ["tune:treble", "bass:bass"]
    assert got["first"] == [[0, [72], False], [1, [76], False], [2, [79, 83, 86], False], [4, [72, 75, 79], True], [6, [74], False]]
    # The page follows its own sound (Python hands nothing on), and the bass note lit is the one the song's rows give, to within a row.
    assert got["direct"] is True and got["worst"] <= 1 and got["off"] < 0.3, got
    assert got["bar"] >= 1
    assert not w.errors


def test_a_pydials_keyboard_plays_a_page_that_waits_for_a_learner(browser, pyctures_run, tmp_path):
    w, _ = run(browser, pyctures_run, tmp_path, '''
        from pyctures import *
        from synths import *
        from pydials import *
        from pynotation import *
        lead = make_synth("keys")
        page = show_notes("C4 E4 G4", "quarter")
        page.play_along("wait", synth=lead)
        keyboard(page, octave=4, octaves=1)

        def draw():
            background("navy")
            js.pyTally = [page.result.right, page.result.wrong, page.result.done]
        ''')
    w.page.wait_for_function(READY + " && %s.along && %s.along.groups.length === 3" % (PAGE, PAGE))
    w.page.wait_for_function("(document.querySelector('[data-pyctures-src] canvas')[Symbol.for('dials.panel')] || { items: [] }).items.some((c) => c.kind === 'keyboard' && c.w > 0)")
    for key in (0, 2, 1, 4):           # C, E, then D (wrong), then G
        x, y = w.page.evaluate("""(i) => { const canvas = document.querySelector('[data-pyctures-src] canvas'), k = canvas[Symbol.for('dials.panel')].items.find((c) => c.kind === 'keyboard'), b = canvas.getBoundingClientRect()
          return [b.left + k.x + k.w / 8 * (i + 0.5), b.top + k.y + k.h * 0.85] }""", key)
        w.page.mouse.move(x, y)
        w.page.mouse.down()
        w.page.wait_for_timeout(100)
        w.page.mouse.up()
        w.page.wait_for_timeout(200)
    w.page.wait_for_function("window.pyTally && window.pyTally[2] === true", timeout=10000)
    assert w.page.evaluate("window.pyTally") == [3, 1, True]
    assert not w.errors


def test_a_scene_that_is_stopped_takes_its_sheet_music_with_it(browser, pyctures_run, tmp_path):
    w, _ = run(browser, pyctures_run, tmp_path, '''
        from pyctures import *
        from pynotation import *
        show_notes("C4 E4", "quarter")

        def draw():
            background("navy")
        ''')
    w.page.wait_for_function(READY)
    w.page.evaluate("document.querySelector('[data-pyctures-src]').pycturesScene.stop()")
    w.page.wait_for_timeout(300)
    assert w.page.evaluate("document.querySelectorAll('[data-notation-layer]').length") == 0


# ---------------------------------------------------------------- built pages

def test_a_single_file_page_carries_sheet_music_only_for_a_scene_that_imports_it(tmp_path):
    plain = tmp_path / "plain.py"
    plain.write_text('def draw():\n    background("navy")\n    circle(100, 100, 30, "gold")\n')
    tune = tmp_path / "tune.py"
    tune.write_text('from pyctures import *\nfrom pynotation import *\nshow_notes("C4 E4 G4", "quarter")\n\ndef draw():\n    background("navy")\n')
    sizes = {}
    for scene in (plain, tune):
        out = tmp_path / (scene.stem + ".html")
        builder.build(scene, out, say=lambda *a: None)
        text = out.read_text()
        sizes[scene.stem] = len(text.encode())
        assert ('"notation": {"js"' in text) == (scene is tune)
        assert ('"synths": {"js"' in text) == (scene is tune)
    # A page with no sheet music is as small as it was: under 200 kB.
    assert sizes["plain"] < 200_000, sizes
    print("single-file page: %d bytes without sheet music, %d with it and the sound" % (sizes["plain"], sizes["tune"]))


def test_a_built_folder_carries_sheet_music_with_the_licence_of_its_symbols(tmp_path):
    """A folder has every library beside the page, as it has the sound and the dials: a page asks for one only when its scene imports it
    (test_a_scene_that_imports_no_sheet_music_is_sent_none)."""
    scene = tmp_path / "tune.py"
    scene.write_text('from pynotation import *\nshow_notes("C4 E4")\n')
    out = tmp_path / "out"
    builder.build(scene, out, say=lambda *a: None)
    for name in ("notation.js", "pynotation.py", "LICENSE", "LICENSE-GLYPHS"):
        assert (out / "pyctures" / "notation" / name).is_file(), name
    assert (out / "pyctures" / "synths" / "synths.js").is_file()


def test_a_built_page_shows_sheet_music_in_the_browsers_own_python(browser, static_server, tmp_path):
    scene = tmp_path / "tune.py"
    scene.write_text('from pyctures import *\nfrom pynotation import *\npage = show_notes("C4 E4 G4 C5", "quarter", title="Built")\n\ndef draw():\n    background("navy")\n')
    out = tmp_path / "tune.html"
    builder.build(scene, out, say=lambda *a: None)
    w = Watched(browser, static_server(tmp_path) + out.name, size=(700, 500))
    w.page.wait_for_function(READY + " && %s.plan.hits.length === 4" % PAGE, timeout=120000)
    assert w.page.evaluate(LAYERS) == "scene,notation"
    assert not w.errors
