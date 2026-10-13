"""Saved values: save("best", 120) and load("best", 0). The Python half alone,
then in a browser: through `pyctures run`, and in a built page, each with a
reload, because being there the next time is the whole point."""
import json
import textwrap

import pytest

import pyctures
from conftest import SHOTS  # noqa: F401  (the browser fixtures come with conftest)

H_SAVED = 8


def start(src, **info):
    info = dict({"width": 400, "height": 300, "pixel_ratio": 1}, **info)
    return json.loads(pyctures.start(textwrap.dedent(src), json.dumps(info)))


def saves(reply):
    """What the page is told to keep: (name, the JSON text) for each save()."""
    return [tuple(c[5]) for c in reply["cmds"] if c[0] == "call" and c[3] == H_SAVED and c[4] == "save"]


@pytest.fixture(autouse=True)
def stopped():
    yield
    pyctures.stop()


# ---------------------------------------------------------------- the Python half

THINGS = {"n": 120, "half": 0.5, "words": 'héllo "you"', "yes": True, "no": False,
          "list": [1, "two", [3]], "thing": {"x": 1, "inside": {"y": [2]}}, "nothing": None}


def test_every_kind_of_value_comes_back_as_it_went_in():
    r = start("""
        things = %r
        for name in things:
            save(name, things[name])
        print(all(load(name) == things[name] for name in things), load("never saved", "the fallback"), load("never saved"))
    """ % (THINGS,))
    assert r["error"] is None, r["error"]
    assert r["out"].strip() == "True the fallback None"
    # Each save is one command to the page, the value as JSON text.
    assert saves(r) == [(name, json.dumps(value)) for name, value in THINGS.items()]


def test_what_the_page_hands_over_at_the_start_is_there_to_load_at_once():
    kept = {name: json.dumps(value) for name, value in THINGS.items()}
    r = start("""
        best = load("n", 0) + 1
        print(best, load("list"), load("thing")["inside"]["y"], load("yes"), load("nothing", "none saved"))
    """, saved=kept)
    assert r["error"] is None, r["error"]
    assert r["out"].strip() == "121 [1, 'two', [3]] [2] True None"
    assert saves(r) == []   # loading sends nothing


def test_a_new_run_has_only_what_the_page_hands_it():
    start('save("best", 5)')
    r = start('print(load("best", "nothing here"))')
    assert r["out"].strip() == "nothing here"
    r = start('print(load("best", "nothing here"))', saved={"best": "5"})
    assert r["out"].strip() == "5"


def test_changing_a_loaded_list_does_not_change_what_is_saved():
    r = start("""
        save("list", [1, 2])
        mine = load("list")
        mine.append(3)
        print(load("list"), mine)
    """)
    assert r["out"].strip() == "[1, 2] [1, 2, 3]"


def test_a_value_that_cannot_be_kept_says_what_can_be_on_its_line():
    for value in ("lambda: 1", "{1, 2}", "object()", "float('nan')"):
        r = start("x = 1\nsave('best', %s)\n" % value)
        assert "cannot keep" in r["error"] and "numbers, text, True and False, lists and dictionaries" in r["error"], value
        assert r["errorLine"] == 2, value
        assert saves(r) == []


def test_text_that_is_not_json_and_things_that_are_not_text_are_passed_over():
    r = start('print(load("broken", 0), load("number", 0), load("good", 0))', saved={"broken": "{not json", "number": 5, "good": "7"})
    assert r["error"] is None, r["error"]
    assert r["out"].strip() == "0 0 7"


def test_a_scenes_own_save_or_load_wins():
    r = start("""
        def save(name):
            return "mine " + name
        load = 5
        print(save("x"), load)
    """)
    assert r["error"] is None and r["out"].strip() == "mine x 5"
    assert saves(r) == []


def test_from_pyctures_import_star_has_them():
    r = start("""
        from pyctures import *
        save("a", 1)
        print(load("a"))
    """)
    assert r["error"] is None and r["out"].strip() == "1"


# ---------------------------------------------------------------- in a browser

playwright = pytest.importorskip("playwright.sync_api")

COUNTER = """
count = load("count", 0)
save("count", count + 1)
save("list", load("list", []) + [count])
print("count", count, load("count"), load("list"))
"""


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio"])
        yield b
        b.close()


def printed(page, logs, start, timeout=60000):
    """The next line the scene prints that starts with `start`."""
    end = page.evaluate("Date.now()") + timeout
    while page.evaluate("Date.now()") < end:
        for t in logs:
            if start in t:
                return t[t.index(start):]
        page.wait_for_timeout(100)
    raise AssertionError("nothing printed: %r" % (logs,))


def test_run_saved_values_are_there_after_a_reload(browser, pyctures_run, tmp_path):
    (tmp_path / "counter.py").write_text(COUNTER)
    (tmp_path / "other.py").write_text('print("other", load("count", "none of mine"))\n')
    p = pyctures_run(tmp_path)
    context = browser.new_context()
    page = context.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    page.add_init_script("""if (!sessionStorage.seen) { sessionStorage.seen = 1; localStorage.setItem('count', "the page's own") }""")
    for n in range(3):
        del logs[:]
        page.goto(p.url + "?scene=counter.py")
        assert printed(page, logs, "count ") == "count %d %d %s" % (n, n + 1, list(range(n + 1)))
    # Kept under the scene's own names: the page's own entry is as it was.
    keys = page.evaluate("Object.keys(localStorage).sort()")
    assert page.evaluate("localStorage.getItem('count')") == "the page's own"
    assert keys == ["count", "pyctures:/counter.py:count", "pyctures:/counter.py:list"], keys
    assert page.evaluate("localStorage.getItem('pyctures:/counter.py:list')") == "[0, 1, 2]"
    # Another scene in the same folder does not see them.
    del logs[:]
    page.goto(p.url + "?scene=other.py")
    assert printed(page, logs, "other ") == "other none of mine"
    context.close()


def test_the_high_score_example_keeps_the_best_score_over_a_reload(browser, pyctures_run, tmp_path):
    """Played with a short game: catch the star once, let the time run out, load the page again."""
    from conftest import EXAMPLES
    source = (EXAMPLES / "high_score.py").read_text().replace("left = 10", "left = 1.5")
    (tmp_path / "high_score.py").write_text(source + '\nprint("best", best)\n')
    p = pyctures_run(tmp_path)
    context = browser.new_context()
    page = context.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    page.goto(p.url + "?scene=high_score.py")
    assert printed(page, logs, "best ") == "best 0"
    box = page.locator("canvas").first.bounding_box()
    page.mouse.click(box["x"] + 200, box["y"] + 160)   # the star starts at 200, 160
    page.wait_for_function("localStorage.getItem('pyctures:/high_score.py:best') === '1'", timeout=10000)
    del logs[:]
    page.goto(p.url + "?scene=high_score.py")
    assert printed(page, logs, "best ") == "best 1"
    context.close()


def test_run_with_no_storage_still_runs_and_keeps_values_while_the_page_is_open(browser, pyctures_run, tmp_path):
    (tmp_path / "counter.py").write_text(COUNTER)
    p = pyctures_run(tmp_path)
    context = browser.new_context()
    page = context.new_page()
    logs, errors = [], []
    page.on("console", lambda m: logs.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    # A page that is refused storage, as in a private window that blocks it.
    page.add_init_script("""
      const refuse = () => { throw new DOMException('The operation is insecure.', 'SecurityError') }
      Object.defineProperty(window, 'localStorage', { configurable: true, get: refuse })
    """)
    page.goto(p.url + "?scene=counter.py")
    assert printed(page, logs, "count ") == "count 0 1 [0]"
    del logs[:]
    page.evaluate("document.querySelector('[data-pyctures-src]').pycturesScene.start()")
    assert printed(page, logs, "count ") == "count 1 2 [0, 1]"
    assert not errors, errors
    assert page.evaluate("document.querySelector('[data-pyctures-src]').dataset.pycturesError || null") is None
    context.close()


def test_built_page_saved_values_are_there_after_a_reload(browser, static_server, tmp_path):
    """Python in the browser (Pyodide in a worker), in one .html file."""
    from test_browser import cdn_reachable
    if not cdn_reachable():
        pytest.skip("Pyodide's CDN is not reachable")
    from pyctures.build import build
    scene = tmp_path / "counter.py"
    scene.write_text(COUNTER)
    build(scene, tmp_path / "out" / "counter.html", say=lambda *a: None)
    url = static_server(tmp_path / "out")
    context = browser.new_context()
    page = context.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    for n in range(2):
        del logs[:]
        page.goto(url + "counter.html")
        assert printed(page, logs, "count ", timeout=120000) == "count %d %d %s" % (n, n + 1, list(range(n + 1)))
    keys = page.evaluate("Object.keys(localStorage).filter((k) => k.startsWith('pyctures:') && k !== 'pyctures:measure').sort()")
    assert len(keys) == 2 and all(k.startswith("pyctures:/counter.html#") for k in keys), keys
    context.close()
