"""Files and databases: save_text, load_text, save_json, load_json and
open_database. The Python half alone (real files in a folder, and the commands
a page is sent), then in a browser: through `pyctures run`, where they are
files beside the scene, and in a built page, where the page keeps them, each
with a reload, because being there the next time is the whole point."""
import base64
import json
import sqlite3
import textwrap

import pytest

import pyctures
from conftest import SHOTS  # noqa: F401  (the browser fixtures come with conftest)

H_FILES = 9


def start(src, **info):
    info = dict({"width": 400, "height": 300, "pixel_ratio": 1}, **info)
    return json.loads(pyctures.start(textwrap.dedent(src), json.dumps(info)))


def tick():
    return json.loads(pyctures.tick(json.dumps({"dt": 0.016})))


def sent(reply):
    """What the page is told to keep: (kind, path, what) for each file written."""
    return [(c[4], c[5][0], c[5][1]) for c in reply["cmds"] if c[0] == "call" and c[3] == H_FILES]


@pytest.fixture(autouse=True)
def folder(tmp_path, monkeypatch):
    """Each test in an empty folder of its own, as a scene is in its own."""
    monkeypatch.chdir(tmp_path)
    yield tmp_path
    pyctures.stop()


# ---------------------------------------------------------------- the Python half: text and JSON

LEVEL = {"n": 120, "half": 0.5, "words": 'héllo "you"', "yes": True, "list": [1, "two", [3]], "thing": {"x": None}}


def test_text_and_json_come_back_as_they_went_in(folder):
    r = start("""
        save_text("notes.txt", "milk\\néggs\\r\\n")
        save_json("level.json", %r)
        print(repr(load_text("notes.txt", "")), load_json("level.json", {}) == %r)
        print(open("notes.txt", encoding="utf-8", newline="").read() == load_text("notes.txt"))
    """ % (LEVEL, LEVEL))
    assert r["error"] is None, r["error"]
    assert r["out"] == "'milk\\néggs\\r\\n' True\nTrue\n"
    # Real files, in the scene's folder, and nothing sent to a page that is not keeping them.
    assert (folder / "notes.txt").read_bytes() == "milk\néggs\r\n".encode("utf-8")
    assert json.loads((folder / "level.json").read_text(encoding="utf-8")) == LEVEL
    assert sent(r) == []


def test_a_file_that_is_not_there_gives_the_default():
    r = start("""
        print(load_text("never.txt", "the fallback"), load_text("never.txt"), load_json("never.json", {"a": 1}), load_json("never.json"))
    """)
    assert r["error"] is None, r["error"]
    assert r["out"].strip() == "the fallback None {'a': 1} None"


def test_a_file_written_by_one_run_is_there_for_the_next():
    start('save_text("notes.txt", "kept")\nsave_json("n.json", [1, 2])')
    r = start('print(load_text("notes.txt", "gone"), load_json("n.json", "gone"))')
    assert r["out"].strip() == "kept [1, 2]"


def test_saving_again_replaces_the_file():
    r = start('save_text("a.txt", "a long first go")\nsave_text("a.txt", "short")\nprint(load_text("a.txt"))')
    assert r["out"].strip() == "short"


def test_a_path_is_from_the_scenes_folder_and_cannot_leave_it(folder):
    inner = folder / "scene"
    inner.mkdir()
    (folder / "secret.txt").write_text("outside")
    import os
    os.chdir(inner)
    r = start("""
        save_text("/top.txt", "1")
        save_text("../../up.txt", "2")
        save_text("./a/./b/../deep.txt", "3")
        save_text("a\\\\back.txt", "4")
        save_json("C:/drive.json", 5)
        print(load_text("../secret.txt", "cannot see it"), load_text("/a/b/deep.txt"), load_text("a/back.txt"))
    """, page_keeps_files=True)
    assert r["error"] is None, r["error"]
    assert r["out"].strip() == "cannot see it 3 4"
    assert sorted(p.relative_to(inner).as_posix() for p in inner.rglob("*") if p.is_file()) == [
        "a/b/deep.txt", "a/back.txt", "drive.json", "top.txt", "up.txt"]
    assert sorted(p.name for p in folder.iterdir()) == ["scene", "secret.txt"]
    # The page is told the path as it was used.
    assert [path for _, path, _ in sent(r)] == ["top.txt", "up.txt", "a/b/deep.txt", "a/back.txt", "drive.json"]


@pytest.mark.parametrize("path", ["", "/", "..", "./../"])
def test_a_path_that_names_no_file_says_so_on_its_line(path):
    for call in ('save_text(%r, "x")', "save_json(%r, 1)", "load_text(%r)", "load_json(%r)", "open_database(%r)"):
        r = start("x = 1\n" + call % path)
        assert 'needs the name of a file, such as "%s"' % ("scores" if "database" in call else "notes.txt") in r["error"], (call, r["error"])
        assert call.split("(")[0] + '("' in r["error"].splitlines()[-1]
        assert r["errorLine"] == 2


def test_text_that_is_not_text_and_values_that_cannot_be_kept_say_what_can_be():
    r = start('x = 1\nsave_text("n.txt", 5)')
    assert r["error"].splitlines()[-1] == ('TypeError: save_text("n.txt", ...) was given something that is not text. '
                                           'Use save_json for numbers, lists and dictionaries, or str(...) to make text of it')
    assert r["errorLine"] == 2
    for value in ("lambda: 1", "{1, 2}", "object()", "float('nan')"):
        r = start("x = 1\nsave_json('level.json', %s)\n" % value)
        assert r["error"].splitlines()[-1] == ('TypeError: save_json("level.json", ...) was given something it cannot keep. '
                                               'It can keep numbers, text, True and False, lists and dictionaries'), value
        assert r["errorLine"] == 2 and sent(r) == []
    import os
    assert os.listdir(".") == []   # nothing was written


def test_a_json_file_that_is_broken_says_so(folder):
    (folder / "level.json").write_text("{not json")
    r = start('level = load_json("level.json", {})')
    assert 'ValueError: load_json("level.json") found the file, but what is in it is not JSON (' in r["error"]
    assert r["errorLine"] == 1


def test_a_page_that_keeps_files_is_sent_each_one_written():
    r = start("""
        save_text("notes.txt", "héllo")
        save_json("maps/level.json", {"a": [1]})
        load_text("notes.txt")
    """, page_keeps_files=True)
    assert r["error"] is None, r["error"]
    assert sent(r) == [("text", "notes.txt", "héllo"), ("text", "maps/level.json", '{"a": [1]}')]
    assert [c[1] for c in r["cmds"] if c[3] == H_FILES] == [2, 3]   # each on the line that wrote it


def test_a_scenes_own_names_win_and_import_star_has_them():
    r = start("""
        def save_text(name):
            return "mine " + name
        open_database = 5
        print(save_text("x"), open_database)
    """)
    assert r["error"] is None and r["out"].strip() == "mine x 5"
    r = start("""
        from pyctures import *
        save_text("a.txt", "1")
        save_json("a.json", 2)
        db = open_database("a")
        print(load_text("a.txt"), load_json("a.json"), db.query("select 3 as n"))
    """)
    assert r["error"] is None and r["out"].strip() == "1 2 [{'n': 3}]"


def test_save_and_load_and_open_are_as_they_were(folder):
    (folder / "data.csv").write_text("1,2")
    r = start('save("best", 5)\nprint(load("best"), open("data.csv").read(), load("notes.txt", "no such value"))')
    assert r["out"].strip() == "5 1,2 no such value"
    assert sent(r) == [] and [c[4] for c in r["cmds"]] == ["save"]


# ---------------------------------------------------------------- the Python half: databases

def test_a_database_is_opened_asked_and_changed(folder):
    r = start("""
        db = open_database("scores")
        print(db.run("create table best (name, points)"))
        print(db.run("insert into best values (?, ?)", "Ann", 12), db.run("insert into best values (?, ?)", "Bo", 3))
        print(db.query("select name, points from best where points > ?", 10))
        print(db.query("select name, points from best order by points"))
        print(db.run("update best set points = points + 1"), db.run("delete from best where name = ?", "Nobody"))
        print(db.query("select count(*) as n, sum(points) as total from best"), db.query("select * from best where points > 99"))
        db.close()
    """)
    assert r["error"] is None, r["error"]
    assert r["out"].splitlines() == [
        "0", "1 1",
        "[{'name': 'Ann', 'points': 12}]",
        "[{'name': 'Bo', 'points': 3}, {'name': 'Ann', 'points': 12}]",
        "2 0",
        "[{'n': 2, 'total': 17}] []"]
    # The real file, scores.db, as Python's own sqlite3 reads it.
    assert sorted(p.name for p in folder.iterdir()) == ["scores.db"]
    assert sqlite3.connect(str(folder / "scores.db")).execute("select * from best order by name").fetchall() == [("Ann", 13), ("Bo", 4)]
    assert sent(r) == []


def test_a_name_with_no_extension_gets_db_and_a_folder_is_made(folder):
    r = start("""
        for name in ("scores", "data/more", "kept.sqlite", "/../up"):
            db = open_database(name)
            db.run("create table t (a)")
            print(db.path)
    """)
    assert r["error"] is None, r["error"]
    assert r["out"].split() == ["scores.db", "data/more.db", "kept.sqlite", "up.db"]
    assert sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()) == [
        "data/more.db", "kept.sqlite", "scores.db", "up.db"]


def test_values_are_bound_in_order_one_by_one_or_as_one_list():
    r = start("""
        db = open_database("scores")
        db.run("create table best (name, points, note)")
        db.run("insert into best values (?, ?, ?)", "Ann", 12, None)
        db.run("insert into best values (?, ?, ?)", ["Bo", 3.5, "a 'quoted' one"])
        db.run("insert into best values (?, ?, ?)", ("Cy'; drop table best; --", True, "x"))
        db.run("insert into best values (:name, :points, :note)", {"name": "Di", "points": 7, "note": ""})
        print(db.query("select * from best where name = ? and points = ?", "Bo", 3.5))
        print(db.query("select name from best where points >= ? order by name", [7]))
        print(db.query("select name, points from best where name like ?", "Cy%"))
        print(db.query("select note from best where name = ?", "Ann"))
    """)
    assert r["error"] is None, r["error"]
    assert r["out"].splitlines() == [
        "[{'name': 'Bo', 'points': 3.5, 'note': \"a 'quoted' one\"}]",
        "[{'name': 'Ann'}, {'name': 'Di'}]",
        "[{'name': \"Cy'; drop table best; --\", 'points': 1}]",
        "[{'note': None}]"]


def test_several_databases_at_once_and_what_was_written_is_there_next_run():
    r = start("""
        a = open_database("a")
        b = open_database("b")
        a.run("create table t (n)")
        b.run("create table t (n)")
        a.run("insert into t values (1)")
        b.run("insert into t values (2)")
        print(a.query("select n from t"), b.query("select n from t"))
    """)
    assert r["out"].strip() == "[{'n': 1}] [{'n': 2}]"
    # Neither was closed: the frame's end keeps what it wrote, and a new run finds it.
    assert sqlite3.connect("a.db").execute("select n from t").fetchall() == [(1,)]
    r = start('print(open_database("a").query("select n from t"), open_database("b").query("select n from t"))')
    assert r["out"].strip() == "[{'n': 1}] [{'n': 2}]"


def test_sql_that_does_not_work_says_what_sqlite_said_on_its_line():
    r = start("""
        db = open_database("scores")
        db.run("create table best (name, points)")
        db.query("select nme from best")
    """)
    assert r["error"].splitlines()[-1] == 'ValueError: query("select nme from best") did not work. SQLite says: no such column: nme'
    assert r["errorLine"] == 4
    r = start('db = open_database("scores")\ndb.run("insert into nowhere values (?)", 1)')
    assert r["error"].splitlines()[-1] == 'ValueError: run("insert into nowhere values (?)") did not work. SQLite says: no such table: nowhere'
    assert r["errorLine"] == 2
    r = start('db = open_database("scores")\ndb.run("insert into best values (?, ?)", "only one")')
    assert 'run("insert into best values (?, ?)") did not work. SQLite says: ' in r["error"] and "binding" in r["error"]
    r = start('db = open_database("scores")\ndb.run("this is not sql")')
    assert 'run("this is not sql") did not work. SQLite says: near "this": syntax error' in r["error"]
    # A long statement is cut short in the message, and its lines run together.
    r = start('db = open_database("scores")\ndb.query("""select name,\n   points from best where name = \'a very long name to look for\' and zzz = 1""")')
    assert 'query("select name, points from best where name = \'a very long n...") did not work. SQLite says: no such column: zzz' in r["error"]


def test_using_a_database_after_close_says_to_open_it_again():
    r = start("""
        db = open_database("scores")
        db.close()
        db.close()
        db.query("select 1")
    """)
    assert r["error"].splitlines()[-1] == ('ValueError: query("select 1") was called after close(). '
                                           'Open the database again with open_database("scores.db")')
    assert r["errorLine"] == 5


def test_a_file_that_is_not_a_database_says_so(folder):
    (folder / "scores.db").write_text("these are words, not a database, and there are plenty of them to read " * 20)
    r = start('db = open_database("scores")\ndb.query("select 1 from best")')
    assert 'did not work. SQLite says: file is not a database' in r["error"], r["error"]


# ---------------------------------------------------------------- the Python half: a database and the page

def tables(b64):
    """What a database sent to the page holds, read back as SQLite would."""
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "sent.db")
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        conn = sqlite3.connect(path)
        try:
            return conn.execute("select * from best order by points").fetchall()
        finally:
            conn.close()


def test_a_page_is_sent_the_whole_database_once_a_frame_however_many_statements(folder):
    r = start("""
        db = open_database("scores")
        db.run("create table best (name, points)")
        for n in range(50):
            db.run("insert into best values (?, ?)", "p%d" % n, n)
        def update(dt):
            pass
    """, page_keeps_files=True)
    assert r["error"] is None, r["error"]
    files = sent(r)
    assert [(kind, path) for kind, path, _ in files] == [("bytes", "scores.db")]
    assert len(tables(files[0][2])) == 50
    assert base64.b64decode(files[0][2]) == (folder / "scores.db").read_bytes()
    # A frame that changes nothing sends nothing.
    assert sent(tick()) == []


def test_a_frame_that_only_asks_or_changes_nothing_sends_nothing():
    start('db = open_database("scores")\ndb.run("create table best (name, points)")\ndb.run("insert into best values (?, ?)", "Ann", 1)',
          page_keeps_files=True)
    r = start("""
        db = open_database("scores")
        db.run("create table if not exists best (name, points)")
        print(db.query("select * from best"))
        def update(dt):
            db.query("select * from best")
    """, page_keeps_files=True)
    assert r["out"].strip() == "[{'name': 'Ann', 'points': 1}]"
    assert sent(r) == [] and sent(tick()) == []


def test_each_frame_that_changes_the_database_sends_it_and_close_sends_it_too():
    r = start("""
        db = open_database("scores")
        db.run("create table best (name, points)")
        frames = 0
        def update(dt):
            global frames
            frames += 1
            if frames == 1:
                db.run("insert into best values (?, ?)", "Ann", 1)
                db.run("insert into best values (?, ?)", "Bo", 2)
            if frames == 3:
                db.run("insert into best values (?, ?)", "Cy", 3)
                db.close()
                save_text("after.txt", "written after the close")
    """, page_keeps_files=True)
    # The first frame is drawn as the scene starts: the table and both rows are one sending.
    first = sent(r)
    assert [(kind, path) for kind, path, _ in first] == [("bytes", "scores.db")]
    assert tables(first[0][2]) == [("Ann", 1), ("Bo", 2)]
    assert sent(tick()) == []
    third = tick()
    # close() sends there and then: before what the scene wrote next, and on its line.
    assert [(kind, path) for kind, path, _ in sent(third)] == [("bytes", "scores.db"), ("text", "after.txt")]
    assert tables(sent(third)[0][2]) == [("Ann", 1), ("Bo", 2), ("Cy", 3)]
    assert [c[1] for c in third["cmds"] if c[3] == H_FILES] == [13, 14]
    assert sent(tick()) == []


def test_a_frame_that_ends_in_an_error_still_keeps_what_it_wrote(folder):
    r = start("""
        db = open_database("scores")
        db.run("create table best (name, points)")
        db.run("insert into best values (?, ?)", "Ann", 1)
        oops
    """, page_keeps_files=True)
    assert "NameError" in r["error"]
    assert tables(sent(r)[0][2]) == [("Ann", 1)]
    assert sqlite3.connect(str(folder / "scores.db")).execute("select * from best").fetchall() == [("Ann", 1)]


def test_stopping_closes_the_databases_with_what_they_hold(folder):
    start("""
        db = open_database("scores")
        db.run("create table best (name, points)")
        def update(dt):
            db.run("insert into best values (?, ?)", "Ann", 1)
    """)
    tick()   # the second frame: the first is drawn as the scene starts
    state = pyctures._latest[0]
    assert len(state.databases) == 1
    pyctures.stop()
    assert state.databases == []
    assert sqlite3.connect(str(folder / "scores.db")).execute("select count(*) from best").fetchall() == [(2,)]


def test_a_page_that_gives_the_scene_a_folder_has_its_stored_files_there(folder):
    """As in a browser: stored files in a folder of the scene's own, the files that came with it beside it."""
    stored = folder / "stored" / "7"
    (folder / "level.json").write_text('{"came": "with the scene"}')
    (folder / "words.txt").write_text("came with the scene")
    conn = sqlite3.connect(str(folder / "scores.db"))
    conn.execute("create table best (name, points)")
    conn.execute("insert into best values ('Came', 1)")
    conn.commit()
    conn.close()
    src = """
        print(load_json("level.json", {}), load_text("words.txt", ""), load_text("mine.txt", "nothing yet"))
        save_json("level.json", {"saved": "by the scene"})
        save_text("maps/mine.txt", "mine")
        db = open_database("scores")
        db.run("insert into best values (?, ?)", "Ann", 2)
        print(load_json("level.json", {}), load_text("maps/mine.txt"), db.query("select * from best order by points"))
    """
    r = start(src, files_in=str(stored))
    assert r["error"] is None, r["error"]
    assert r["out"].splitlines() == [
        "{'came': 'with the scene'} came with the scene nothing yet",
        "{'saved': 'by the scene'} mine [{'name': 'Came', 'points': 1}, {'name': 'Ann', 'points': 2}]"]
    # Written in the scene's folder of stored files; what came with the scene is as it was.
    assert sorted(p.relative_to(stored).as_posix() for p in stored.rglob("*") if p.is_file()) == ["level.json", "maps/mine.txt", "scores.db"]
    assert (folder / "level.json").read_text() == '{"came": "with the scene"}'
    assert sqlite3.connect(str(folder / "scores.db")).execute("select count(*) from best").fetchall() == [(1,)]
    # The page is told each by its own path, with no folder of Python's in it.
    files = sent(r)
    assert [(kind, path) for kind, path, _ in files] == [("text", "level.json"), ("text", "maps/mine.txt"), ("bytes", "scores.db")]
    assert tables(files[2][2]) == [("Came", 1), ("Ann", 2)]
    # Another scene, given another folder, sees none of it.
    r = start('print(load_text("maps/mine.txt", "not mine"), open_database("other").query("select 1 as n"))', files_in=str(folder / "stored" / "8"))
    assert r["out"].strip() == "not mine [{'n': 1}]"


# ---------------------------------------------------------------- in a browser

playwright = pytest.importorskip("playwright.sync_api")

# Counts its runs three ways: a text file, a JSON file and a database.
COUNTER = """
count = int(load_text("count.txt", "0"))
save_text("count.txt", str(count + 1))
runs = load_json("data/runs.json", [])
save_json("data/runs.json", runs + [count])
db = open_database("scores")
db.run("create table if not exists runs (n)")
db.run("insert into runs values (?)", count)
print("count", count, load_json("data/runs.json"), [row["n"] for row in db.query("select n from runs order by n")])
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


def needs_cdn():
    from test_browser import cdn_reachable
    if not cdn_reachable():
        pytest.skip("Pyodide's CDN is not reachable")


# What the browser keeps for scenes: localStorage's entries, and the paths in IndexedDB.
KEPT = """async () => {
  const text = {}
  for (const k of Object.keys(localStorage)) if (k.startsWith('pyctures:') && k !== 'pyctures:measure') text[k] = localStorage.getItem(k)
  const bytes = await new Promise((done) => {
    const req = indexedDB.open('pyctures', 1)
    req.onupgradeneeded = () => req.result.createObjectStore('files')
    req.onsuccess = () => { const all = req.result.transaction('files').objectStore('files').getAllKeys(); all.onsuccess = () => done(all.result) }
  })
  return { text, bytes }
}"""


def test_run_files_are_real_files_beside_the_scene(browser, pyctures_run, tmp_path):
    (tmp_path / "counter.py").write_text(COUNTER)
    p = pyctures_run(tmp_path)
    context = browser.new_context()
    page = context.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    for n in range(3):
        del logs[:]
        page.goto(p.url + "?scene=counter.py")
        assert printed(page, logs, "count ") == "count %d %s %s" % (n, list(range(n + 1)), list(range(n + 1)))
    assert (tmp_path / "count.txt").read_text() == "3"
    assert json.loads((tmp_path / "data" / "runs.json").read_text()) == [0, 1, 2]
    assert sqlite3.connect(str(tmp_path / "scores.db")).execute("select n from runs order by n").fetchall() == [(0,), (1,), (2,)]
    # The page keeps none of it: the files are the keeping.
    assert page.evaluate(KEPT) == {"text": {}, "bytes": []}
    context.close()


def test_the_top_scores_example_keeps_every_game_over_a_reload(browser, pyctures_run, tmp_path):
    """Played with a short game: catch the star once, let the time run out, load the page again."""
    from conftest import EXAMPLES
    source = (EXAMPLES / "top_scores.py").read_text().replace("left = 10 ", "left = 1.5 ")
    (tmp_path / "top_scores.py").write_text(source + '\nprint("top", [game["points"] for game in top])\n')
    p = pyctures_run(tmp_path)
    context = browser.new_context()
    page = context.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    page.goto(p.url + "?scene=top_scores.py")
    assert printed(page, logs, "top ") == "top []"
    box = page.locator("canvas").first.bounding_box()
    page.mouse.click(box["x"] + 200, box["y"] + 160)   # the star starts at 200, 160
    page.wait_for_timeout(2500)
    del logs[:]
    page.goto(p.url + "?scene=top_scores.py")
    assert printed(page, logs, "top ") == "top [1]"
    context.close()


@pytest.mark.parametrize("single", [False, True])
def test_built_page_files_and_a_database_are_there_after_a_reload(browser, static_server, tmp_path, single):
    """Python in the browser (Pyodide in a worker): a folder, and one .html file."""
    needs_cdn()
    from pyctures.build import build
    scene = tmp_path / "counter.py"
    scene.write_text(COUNTER)
    build(scene, tmp_path / "out" / "counter.html" if single else tmp_path / "out", say=lambda *a: None)
    url = static_server(tmp_path / "out") + ("counter.html" if single else "index.html")
    context = browser.new_context()
    page = context.new_page()
    logs, errors, asked = [], [], []
    page.on("console", lambda m: logs.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    context.on("request", lambda req: asked.append(req.url))
    for n in range(3):
        del logs[:]
        page.goto(url)
        assert printed(page, logs, "count ", timeout=120000) == "count %d %s %s" % (n, list(range(n + 1)), list(range(n + 1)))
        # The page has kept this run's files before the next one is started.
        page.wait_for_function("(n) => Object.keys(localStorage).some((k) => k.endsWith(':file:count.txt') && localStorage.getItem(k) === String(n))", arg=n + 1)
        page.wait_for_timeout(300)
    kept = page.evaluate(KEPT)
    under = "pyctures:/counter.html#counter.py:file:" if single else "pyctures:/counter.py:file:"
    assert kept["text"] == {under + "count.txt": "3", under + "data/runs.json": "[0, 1, 2]"}, kept
    assert kept["bytes"] == [under + "scores.db"], kept
    assert [u for u in asked if "sqlite3" in u.lower()], asked   # Python's sqlite3 was fetched for this scene
    assert not errors, errors
    assert page.evaluate("document.querySelector('[data-pyctures-src]').dataset.pycturesError || null") is None
    context.close()


def test_built_page_on_the_pages_own_thread_keeps_them_too(browser, static_server, tmp_path):
    needs_cdn()
    from pyctures.build import build
    scene = tmp_path / "counter.py"
    scene.write_text(COUNTER)
    build(scene, tmp_path / "out", say=lambda *a: None)
    index = tmp_path / "out" / "index.html"
    index.write_text(index.read_text().replace("data-pyctures-fullpage", 'data-pyctures-fullpage data-pyctures-worker="off"'))
    url = static_server(tmp_path / "out")
    context = browser.new_context()
    page = context.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    for n in range(2):
        del logs[:]
        page.goto(url)
        assert printed(page, logs, "count ", timeout=120000) == "count %d %s %s" % (n, list(range(n + 1)), list(range(n + 1)))
        assert page.evaluate("document.querySelector('[data-pyctures-src]').pycturesScene.transport.label") == "Python in the page"
        page.wait_for_function("async () => (await (%s)()).bytes.length === 1" % KEPT)
        page.wait_for_timeout(300)
    context.close()


def test_a_scene_with_no_database_does_not_load_sqlite(browser, static_server, tmp_path):
    needs_cdn()
    from pyctures.build import build
    scene = tmp_path / "plain.py"
    scene.write_text('# open_database("scores") is only named in a comment, and in "open_database" as text\n'
                     'save_text("a.txt", "1")\nprint("read", load_text("a.txt"))\n')
    build(scene, tmp_path / "out", say=lambda *a: None)
    url = static_server(tmp_path / "out")
    context = browser.new_context()
    page = context.new_page()
    logs, asked = [], []
    page.on("console", lambda m: logs.append(m.text))
    context.on("request", lambda req: asked.append(req.url))
    page.goto(url)
    assert printed(page, logs, "read ", timeout=120000) == "read 1"
    assert not [u for u in asked if "sqlite" in u.lower()], asked
    context.close()


TWO_SCENES = """<!doctype html>
<div data-pyctures-src="one.py" style="width:300px;height:200px"></div>
<div data-pyctures-src="two.py" style="width:300px;height:200px"></div>
<script type="module" src="pyctures/pyctures.js"></script>
"""


def test_two_scenes_on_a_page_keep_files_of_the_same_name_apart(browser, static_server, tmp_path):
    """And a file that came with the scene is read until the scene saves its own."""
    needs_cdn()
    from pyctures.build import build
    site = tmp_path / "page"
    site.mkdir()
    for name in ("one", "two"):
        (site / (name + ".py")).write_text(
            'db = open_database("scores")\n'
            'db.run("create table if not exists runs (who)")\n'
            'db.run("insert into runs values (?)", "%s")\n'
            'level = load_json("level.json", {"from": "nowhere"})\n'
            'print("%s", load_text("note.txt", "no note"), level["from"], [row["who"] for row in db.query("select who from runs")])\n'
            'save_text("note.txt", "from %s")\n'
            'save_json("level.json", {"from": "saved by %s"})\n' % (name, name, name, name))
    (site / "level.json").write_text('{"from": "the site"}')
    (site / "index.html").write_text(TWO_SCENES.replace(" style=", ' data-pyctures-files="level.json" style='))
    build(site, tmp_path / "out", say=lambda *a: None)
    url = static_server(tmp_path / "out")
    context = browser.new_context()
    page = context.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    page.goto(url)
    assert printed(page, logs, "one ", timeout=120000) == "one no note the site ['one']"
    assert printed(page, logs, "two ", timeout=120000) == "two no note the site ['two']"
    page.wait_for_function("async () => { const k = await (%s)(); return k.bytes.length === 2 && Object.keys(k.text).length === 4 }" % KEPT)
    page.wait_for_timeout(300)
    del logs[:]
    page.goto(url)
    assert printed(page, logs, "one ", timeout=120000) == "one from one saved by one ['one', 'one']"
    assert printed(page, logs, "two ", timeout=120000) == "two from two saved by two ['two', 'two']"
    context.close()


HOST_PAGE = """<!doctype html>
<div id="scene" style="width:400px;height:300px"></div>
<script>window.PYCTURES_NO_AUTO = true</script>
<script type="module">
import { mount } from './pyctures/pyctures.js'
// A host's storage: files in a table of its own (here, one that outlives the page in sessionStorage).
const disk = JSON.parse(sessionStorage.disk || '{}')
const calls = []
const put = () => { sessionStorage.disk = JSON.stringify(disk) }
const storage = %s
window.host = { disk, calls }
mount(document.getElementById('scene'), { src: 'counter.py', storage })
</script>
"""

FULL_HOST = """{
  async list() { calls.push('list'); return Object.keys(disk) },
  async readText(path) { calls.push('readText ' + path); return path in disk && disk[path].text != null ? disk[path].text : null },
  async writeText(path, text) { calls.push('writeText ' + path); disk[path] = { text }; put() },
  async readBytes(path) { calls.push('readBytes ' + path); return path in disk && disk[path].bytes ? Uint8Array.from(disk[path].bytes) : null },
  async writeBytes(path, bytes) { calls.push('writeBytes ' + path); disk[path] = { bytes: Array.from(bytes) }; put() },
}"""

# The JavaScript sibling's contract: reads and writes, and no list().
HOST_WITH_NO_LIST = FULL_HOST.replace("  async list() { calls.push('list'); return Object.keys(disk) },\n", "")

# A host that only keeps text: databases fall back to the browser's own keeping.
TEXT_ONLY_HOST = """{
  async list() { calls.push('list'); return Object.keys(disk) },
  async readText(path) { calls.push('readText ' + path); return path in disk ? disk[path].text : null },
  async writeText(path, text) { calls.push('writeText ' + path); disk[path] = { text }; put() },
}"""


@pytest.mark.parametrize("host", ["full", "no list", "text only"])
def test_a_host_that_supplies_storage_is_given_the_files(browser, static_server, tmp_path, host):
    needs_cdn()
    from pyctures.build import build
    scene = tmp_path / "counter.py"
    scene.write_text(COUNTER)
    build(scene, tmp_path / "out", say=lambda *a: None)
    storage = {"full": FULL_HOST, "no list": HOST_WITH_NO_LIST, "text only": TEXT_ONLY_HOST}[host]
    (tmp_path / "out" / "host.html").write_text(HOST_PAGE % storage)
    url = static_server(tmp_path / "out") + "host.html"
    context = browser.new_context()
    page = context.new_page()
    logs, errors = [], []
    page.on("console", lambda m: logs.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    wrote = "writeText count.txt" if host == "text only" else "writeBytes scores.db"
    for n in range(3):
        del logs[:]
        page.goto(url)
        assert printed(page, logs, "count ", timeout=120000) == "count %d %s %s" % (n, list(range(n + 1)), list(range(n + 1)))
        page.wait_for_function("(wrote) => window.host.calls.includes(wrote) && window.host.calls.includes('writeText data/runs.json')", arg=wrote)
        page.wait_for_timeout(300)
    disk = page.evaluate("window.host.disk")
    kept = page.evaluate(KEPT)
    assert disk["count.txt"] == {"text": "3"} and disk["data/runs.json"] == {"text": "[0, 1, 2]"}
    under = "pyctures:/counter.py:file:"
    if host == "text only":
        # The database is the browser's to keep; the text is the host's alone.
        assert sorted(disk) == ["count.txt", "data/runs.json"]
        assert kept == {"text": {}, "bytes": [under + "scores.db"]}, kept
    else:
        assert sorted(disk) == ["count.txt", "data/runs.json", "scores.db"]
        assert bytes(disk["scores.db"]["bytes"][:15]) == b"SQLite format 3"
        # With no list() the paths written are noted, and that note is all the browser keeps.
        noted = {} if host == "full" else {under: json.dumps(["count.txt", "data/runs.json", "scores.db"])}
        assert kept["bytes"] == [] and {k: json.dumps(sorted(json.loads(v))) for k, v in kept["text"].items()} == noted, kept
    assert not errors, errors
    context.close()


def test_built_page_with_no_storage_still_runs_and_keeps_files_while_the_page_is_open(browser, static_server, tmp_path):
    needs_cdn()
    from pyctures.build import build
    scene = tmp_path / "counter.py"
    scene.write_text(COUNTER)
    build(scene, tmp_path / "out", say=lambda *a: None)
    url = static_server(tmp_path / "out")
    context = browser.new_context()
    page = context.new_page()
    logs, errors = [], []
    page.on("console", lambda m: logs.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    # A page that is refused storage, as in a private window that blocks it.
    page.add_init_script("""
      const refuse = () => { throw new DOMException('The operation is insecure.', 'SecurityError') }
      Object.defineProperty(window, 'localStorage', { configurable: true, get: refuse })
      Object.defineProperty(window, 'indexedDB', { configurable: true, get: refuse })
    """)
    warned = []
    page.on("console", lambda m: warned.append(m.text))
    page.goto(url)
    assert printed(page, logs, "count ", timeout=120000) == "count 0 [0] [0]"
    page.wait_for_timeout(500)
    del logs[:]
    # A hard stop ends the worker, and Python's own copy of the files with it: the page's copy is what is left.
    page.evaluate("""async () => {
      const s = document.querySelector('[data-pyctures-src]').pycturesScene
      s.transport.hardStop()
      await s.stop()
      await s.start()
    }""")
    assert printed(page, logs, "count ", timeout=120000) == "count 1 [0, 1] [0, 1]"
    assert len([t for t in warned if "would not keep it" in t]) == 1, warned   # said once, not for every file
    assert not errors, errors
    assert page.evaluate("document.querySelector('[data-pyctures-src]').dataset.pycturesError || null") is None
    context.close()
