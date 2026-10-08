"""`pyctures run` (HTTP + WebSocket + worker) and `pyctures build`, without a browser."""
import json
import socket
import time
import urllib.request

import pytest

from conftest import EXAMPLES, ROOT, WSClient
from pyctures import build as build_mod
from pyctures import pages


def get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.read().decode("utf-8", "replace")


def raw_get(port, path):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(("GET %s HTTP/1.1\r\nHost: localhost\r\n\r\n" % path).encode())
        data = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    return int(data.split(b" ")[1])


def test_run_serves_the_scene_page_and_assets(pyctures_run):
    p = pyctures_run(EXAMPLES / "star_catcher.py")
    status, page = get(p.url)
    assert status == 200
    assert 'data-pyctures-src="star_catcher.py"' in page
    assert 'name="pyctures-server"' in page
    assert get(p.url + "pyctures/pyctures.js")[0] == 200
    assert get(p.url + "pyctures/pyctures.py")[1] == (ROOT / "src/pyctures/__init__.py").read_text()
    assert get(p.url + "pyctures/three/three.module.min.js")[0] == 200
    assert get(p.url + "star_catcher.py")[1].startswith("# Star Catcher")
    # nothing outside the scene's folder
    assert raw_get(p.port, "/../pyproject.toml") == 404
    assert raw_get(p.port, "/%2e%2e/pyproject.toml") == 404


def test_run_a_folder_lists_scenes_and_injects_into_html(pyctures_run):
    p = pyctures_run(EXAMPLES)
    status, page = get(p.url)
    assert "star_catcher.py" in page and "cube_dodge.py" in page
    status, page = get(p.url + "website/index.html")
    assert 'name="pyctures-server"' in page and "data-pyctures-src" in page
    status, page = get(p.url + "?scene=type_and_measure.py")
    assert 'data-pyctures-src="type_and_measure.py"' in page


def test_websocket_runs_frames_in_a_python_process(pyctures_run):
    p = pyctures_run(EXAMPLES / "bouncing_balls.py")
    ws = WSClient(p.port, "/bouncing_balls.py")
    assert ws.status == 101
    ws.send({"id": 1, "op": "start", "info": {"width": 400, "height": 300, "pixel_ratio": 1}})
    m = ws.recv()
    assert m["id"] == 1
    reply = json.loads(m["reply"])
    assert reply["error"] is None and reply["running"] is True
    assert any(c[0] == "call" and c[4] == "fill_rect" for c in reply["cmds"])
    for i in range(2, 12):
        ws.send({"id": i, "op": "tick", "payload": {"dt": 1 / 60, "events": [], "reads": {}}})
        m = ws.recv()
        assert m["id"] == i and json.loads(m["reply"])["running"]
    ws.close()


def test_websocket_reports_errors_with_line_numbers(pyctures_run, tmp_path):
    scene = tmp_path / "broken.py"
    scene.write_text("x = 1\n\ndef draw():\n    ctx.fill_rect(0, 0, undefined_name, 1)\n")
    p = pyctures_run(scene)
    ws = WSClient(p.port, "/broken.py")
    ws.send({"id": 1, "op": "start", "info": {"width": 100, "height": 100}})
    reply = json.loads(ws.recv()["reply"])
    assert reply["errorLine"] == 4
    assert "NameError" in reply["error"]
    ws.close()
    out = p.stop()
    assert "broken.py, line 4" in out and "NameError" in out   # also in the terminal


def test_websocket_refuses_other_sites_and_other_files(pyctures_run):
    p = pyctures_run(EXAMPLES / "star_catcher.py")
    assert WSClient(p.port, "/star_catcher.py", origin="https://example.com").status == 403
    assert WSClient(p.port, "/../pyproject.toml").status == 404
    assert WSClient(p.port, "/star_catcher.py", origin=p.url.rstrip("/")).status == 101


def test_numpy_like_imports_run_in_your_own_python(pyctures_run, tmp_path):
    # The scene's folder is importable, and files open by name.
    (tmp_path / "helper.py").write_text("SIZE = 7\n")
    (tmp_path / "data.txt").write_text("hello")
    (tmp_path / "scene.py").write_text("import helper\nprint(helper.SIZE, open('data.txt').read())\n")
    p = pyctures_run(tmp_path / "scene.py")
    ws = WSClient(p.port, "/scene.py")
    ws.send({"id": 1, "op": "start", "info": {}})
    reply = json.loads(ws.recv()["reply"])
    assert reply["out"] == "7 hello\n"
    ws.close()


def test_saving_the_file_reloads_open_pages(pyctures_run, tmp_path):
    scene = tmp_path / "scene.py"
    scene.write_text("def draw(): pass\n")
    p = pyctures_run(scene)
    ws = WSClient(p.port, "/scene.py")
    ws.send({"id": 1, "op": "start", "info": {}})
    ws.recv()
    time.sleep(0.5)
    scene.write_text("def draw(): ctx.fill_rect(0, 0, 1, 1)\n")
    ws.sock.settimeout(5)
    assert ws.recv() == {"type": "reload"}
    ws.close()


# ---------------------------------------------------------------- build

def test_build_a_scene_is_relative_and_self_contained(tmp_path):
    data = tmp_path / "src"
    data.mkdir()
    scene = data / "scene.py"
    scene.write_text("print(open('words.txt').read())\n")
    (data / "words.txt").write_text("hi")
    out = tmp_path / "site"
    build_mod.build(scene, out, add=[data / "words.txt"], say=lambda *a: None)
    index = (out / "index.html").read_text()
    assert 'data-pyctures-src="scene.py"' in index
    assert 'src="pyctures/pyctures.js"' in index
    assert 'data-pyctures-files="words.txt"' in index
    assert "localhost" not in index and 'src="/' not in index and "pyctures-server" not in index
    for published in pages.ASSETS:
        assert (out / "pyctures" / published).is_file(), published
    assert (out / "pyctures/pyctures.py").read_text() == (ROOT / "src/pyctures/__init__.py").read_text()
    assert (out / "words.txt").read_text() == "hi"
    js = (out / "pyctures/three/OrbitControls.js").read_text()
    assert "from './three.module.min.js'" in js


def test_build_a_folder_keeps_the_page_and_adds_assets(tmp_path):
    out = tmp_path / "site"
    build_mod.build(EXAMPLES / "website", out, say=lambda *a: None)
    assert (out / "index.html").read_text() == (EXAMPLES / "website/index.html").read_text()
    assert (out / "balls.py").is_file() and (out / "knot.py").is_file()
    assert (out / "pyctures/pyctures.js").is_file()


def test_build_a_folder_of_scenes_makes_a_page_for_each(tmp_path):
    src = tmp_path / "scenes"
    src.mkdir()
    (src / "one.py").write_text("ctx.fill_rect(0,0,1,1)\n")
    (src / "two.py").write_text("ctx.fill_rect(0,0,1,1)\n")
    out = tmp_path / "site"
    build_mod.build(src, out, say=lambda *a: None)
    assert 'href="one.html"' in (out / "index.html").read_text()
    assert 'data-pyctures-src="two.py"' in (out / "two.html").read_text()


def test_cli_build(tmp_path):
    import subprocess
    import sys
    out = tmp_path / "site"
    r = subprocess.run([sys.executable, "-m", "pyctures", "build", str(EXAMPLES / "type_and_measure.py"), "-o", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (out / "type_and_measure.py").is_file() and (out / "index.html").is_file()


def test_a_scene_named_like_a_standard_module_still_starts(pyctures_run, tmp_path):
    # Python itself must start even though the folder has a typing.py in it,
    # and the scene is told why `import random` finds itself.
    (tmp_path / "typing.py").write_text("x = 1\n")
    (tmp_path / "random.py").write_text("print('hello')\n")
    p = pyctures_run(tmp_path / "random.py")
    ws = WSClient(p.port, "/random.py")
    ws.send({"id": 1, "op": "start", "info": {}})
    reply = json.loads(ws.recv()["reply"])
    assert reply["error"] is None and reply["out"] == "hello\n"
    assert "same as Python's own module 'random'" in reply["err"]
    ws.close()


def test_versions_agree():
    import re
    import pyctures
    py = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    npm = json.loads((ROOT / "npm/package.json").read_text())["version"]
    assert py == pyctures.__version__ == npm
