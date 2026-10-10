"""Built pages: Python in a Web Worker, the single-file export, measure mode,
and a stuck loop that no longer freezes the page. Real (headless) Chromium.

Needs Playwright and Pyodide's CDN.
"""
import re
import time

import pytest

from conftest import EXAMPLES, SHOTS
from test_browser import COLOURS, PIXEL, Watched, cdn_reachable

playwright = pytest.importorskip("playwright.sync_api")

pytestmark = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                                    "--enable-unsafe-webgpu"])
        yield b
        b.close()


def build_one(tmp_path, source_or_example, name="scene.py", html=False, add=()):
    from pyctures.build import build
    if isinstance(source_or_example, str):
        scene = tmp_path / name
        scene.write_text(source_or_example)
    else:
        scene = source_or_example
    out = tmp_path / (scene.stem + ".html" if html else "site")
    build(scene, out, add=add, say=lambda *a: None)
    return out


def scene_info(page):
    return page.evaluate("""() => {
      const el = document.querySelector('[data-pyctures-src]'), s = el.pycturesScene
      return { status: el.dataset.pycturesStatus, error: el.dataset.pycturesError || null,
               runtime: s && s.transport ? s.transport.label : null,
               pyodideOnPage: typeof window.loadPyodide !== 'undefined' || typeof window.pyodide !== 'undefined' }
    }""")


def frames_in(page, ms):
    """How many animation frames the page's own thread ran in `ms`."""
    return page.evaluate("""(ms) => new Promise((done) => {
      let n = 0; const end = performance.now() + ms
      const f = (t) => { n++; if (t < end) requestAnimationFrame(f); else done(n) }
      requestAnimationFrame(f)
    })""", ms)


# ---------------------------------------------------------------- the worker

def test_built_page_runs_python_in_a_worker(browser, static_server, tmp_path):
    out = build_one(tmp_path, EXAMPLES / "star_catcher.py")
    w = Watched(browser, static_server(out))
    w.check("worker-star_catcher.png")
    info = scene_info(w.page)
    assert info["runtime"] == "Python in a worker"
    assert not info["pyodideOnPage"], "Pyodide was loaded on the page's own thread"
    assert any(wk.url.startswith("blob:") for wk in w.page.workers)


def test_worker_reads_events_and_promises(browser, static_server, tmp_path):
    """Await-reads, a promise's value, a promise's object, a rejected promise
    (with its line), and a callback event, all across the worker boundary."""
    code = '''
w = await ctx.measure_text("hello").width
print("width", w > 10)
n = await js.Promise.resolve(41)
print("promise", n + 1)
fonts = await js.document.fonts.ready
print("object", await fonts.status)
try:
    await js.Promise.reject(js.Error("nope"))
except RuntimeError as e:
    print("rejected", e)
clicks = 0
def clicked(e):
    global clicks
    clicks += 1
    print("clicked", clicks, e.x > 0)
canvas.add_event_listener("click", clicked)
await ctx.measure_text("x").width
print("ready")
def draw():
    ctx.fill_style = "rgb(0, 128, 255)"
    ctx.fill_rect(0, 0, width, height)
'''
    out = build_one(tmp_path, code)
    w = Watched(browser, static_server(out))
    logs = []
    w.page.on("console", lambda m: logs.append(m.text))
    w.wait_running()

    def wait_for_line(start, seconds=15):
        end = time.time() + seconds
        while time.time() < end and not any(t.startswith(start) for t in logs):
            w.page.wait_for_timeout(50)
        assert any(t.startswith(start) for t in logs), f"no {start!r} line in {seconds}s:\n" + "\n".join(logs)

    # A click sent before the page has added the listener has nothing to hear
    # it, and the awaits above take a while under load. Printing after
    # add_event_listener is not enough: output is shown at once, but drawing
    # commands (the listener is one) wait a refresh or two in the frame queue.
    # A read is answered only once the page has run everything before it, so
    # "ready" after a read means the listener is there.
    wait_for_line("ready")
    w.page.mouse.click(200, 200)
    wait_for_line("clicked")
    text = "\n".join(logs)
    assert "width True" in text
    assert "promise 42" in text
    assert "object loaded" in text
    assert re.search(r"rejected line 9: .*nope", text), text
    assert "clicked 1 True" in text
    assert w.scenes()[0].evaluate(PIXEL, [0.5, 0.5]) == [0, 128, 255]


def test_worker_error_shows_the_line(browser, static_server, tmp_path):
    out = build_one(tmp_path, "x = 1\n\ndef draw():\n    ctx.fill_rect(0, 0, undefined_name, 1)\n", name="broken.py")
    w = Watched(browser, static_server(out))
    w.page.wait_for_selector(".pyctures-error", timeout=60000)
    text = w.page.inner_text(".pyctures-error")
    assert "Error on line 4 of broken.py" in text
    assert "NameError" in text


WEBGL = '''
gl = canvas.getContext("webgl2")
VS = """#version 300 es
in vec2 pos; void main() { gl_Position = vec4(pos, 0.0, 1.0); }"""
FS = """#version 300 es
precision mediump float; out vec4 col; void main() { col = vec4(1.0, 0.5, 0.0, 1.0); }"""
def shader(kind, src):
    s = gl.createShader(kind)
    gl.shaderSource(s, src)
    gl.compileShader(s)
    return s
prog = gl.createProgram()
gl.attachShader(prog, shader(gl.VERTEX_SHADER, VS))
gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, FS))
gl.linkProgram(prog)
buf = gl.createBuffer()
gl.bindBuffer(gl.ARRAY_BUFFER, buf)
gl.bufferData(gl.ARRAY_BUFFER, js.Float32Array([0, 0.9, -0.9, -0.9, 0.9, -0.9]), gl.STATIC_DRAW)
loc = gl.getAttribLocation(prog, "pos")
gl.enableVertexAttribArray(loc)
gl.vertexAttribPointer(loc, 2, gl.FLOAT, False, 0, 0)
print("linked:", await gl.getProgramParameter(prog, gl.LINK_STATUS))
def draw():
    gl.viewport(0, 0, canvas.width, canvas.height)
    gl.clearColor(0.05, 0.05, 0.1, 1)
    gl.clear(gl.COLOR_BUFFER_BIT)
    gl.useProgram(prog)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
'''

WEBGPU = '''
gpu = js.navigator.gpu
adapter = await gpu.requestAdapter()
device = await adapter.requestDevice()
context = canvas.getContext("webgpu")
fmt = await gpu.getPreferredCanvasFormat()
context.configure(device=device, format=fmt, alphaMode="opaque")
code = """
@vertex fn vs(@builtin(vertex_index) i: u32) -> @builtin(position) vec4f {
  var p = array<vec2f, 3>(vec2f(0.0, 0.9), vec2f(-0.9, -0.9), vec2f(0.9, -0.9));
  return vec4f(p[i], 0.0, 1.0);
}
@fragment fn fs() -> @location(0) vec4f { return vec4f(1.0, 0.6, 0.2, 1.0); }
"""
module = device.createShaderModule(code=code)
pipeline = device.createRenderPipeline(layout="auto", vertex={"module": module, "entryPoint": "vs"},
    fragment={"module": module, "entryPoint": "fs", "targets": [{"format": fmt}]})
print("gpu ready")
def draw():
    encoder = device.createCommandEncoder()
    view = context.getCurrentTexture().createView()
    rp = encoder.beginRenderPass(colorAttachments=[{"view": view, "loadOp": "clear", "storeOp": "store",
                                                    "clearValue": {"r": 0.05, "g": 0.05, "b": 0.1, "a": 1}}])
    rp.setPipeline(pipeline)
    rp.draw(3)
    rp.end()
    device.queue.submit([encoder.finish()])
'''


@pytest.mark.parametrize("name,code", [("webgl", WEBGL), ("webgpu", WEBGPU)])
def test_worker_gpu_examples(browser, static_server, tmp_path, name, code):
    out = build_one(tmp_path, code, name=name + ".py")
    w = Watched(browser, static_server(out))
    if name == "webgpu" and not w.page.evaluate(
            "async () => !!(navigator.gpu && await navigator.gpu.requestAdapter())"):
        pytest.skip("no WebGPU in this browser")
    logs = []
    w.page.on("console", lambda m: logs.append(m.text))
    w.wait_running()
    end = time.time() + 20
    want = "linked: True" if name == "webgl" else "gpu ready"
    while time.time() < end and want not in logs:
        w.page.wait_for_timeout(200)
    assert want in logs, logs
    w.page.wait_for_timeout(800)
    assert scene_info(w.page)["status"] == "running"
    # The middle of the triangle is orange; a corner is the dark clear colour.
    mid = w.scenes()[0].evaluate("""(el) => new Promise((done) => requestAnimationFrame(() => {
      const c = el.querySelector('canvas'), t = document.createElement('canvas')
      t.width = c.width; t.height = c.height
      const g = t.getContext('2d'); g.drawImage(c, 0, 0)
      done(Array.from(g.getImageData(c.width >> 1, (c.height * 0.6) | 0, 1, 1).data.slice(0, 3)))
    }))""")
    assert mid[0] > 200 and mid[2] < 80, mid
    w.page.screenshot(path=str(SHOTS / ("worker-%s.png" % name)))


# ---------------------------------------------------------------- a stuck loop

def test_stuck_loop_does_not_freeze_the_page(browser, static_server, tmp_path):
    code = 'def draw():\n    while True:\n        pass\n'
    out = build_one(tmp_path, code, name="stuck.py")
    w = Watched(browser, static_server(out))
    # Python is stuck, but the page's own thread keeps drawing frames.
    w.page.wait_for_selector(".pyctures-stuck", timeout=15000)
    assert frames_in(w.page, 500) >= 20
    w.page.click(".pyctures-stuck button")
    w.page.wait_for_selector(".pyctures-error", timeout=5000)
    assert "Stopped" in w.page.inner_text(".pyctures-error")
    assert scene_info(w.page)["status"] == "error"
    # Run again: a fresh worker starts, and the page is still responsive.
    w.page.click(".pyctures-error button")
    w.page.wait_for_selector(".pyctures-stuck", timeout=60000)
    assert frames_in(w.page, 500) >= 20


def test_stuck_top_level_can_be_stopped(browser, static_server, tmp_path):
    out = build_one(tmp_path, 'n = 0\nwhile True:\n    n += 1\n', name="stuck_top.py")
    w = Watched(browser, static_server(out))
    w.page.wait_for_selector(".pyctures-stuck", timeout=60000)
    assert frames_in(w.page, 500) >= 20
    w.page.evaluate("() => document.querySelector('[data-pyctures-src]').pycturesScene.stop()")
    w.page.wait_for_timeout(300)
    assert scene_info(w.page)["status"] == "stopped"
    assert not w.page.query_selector(".pyctures-stuck")


# ---------------------------------------------------------------- one .html file

def test_single_file_2d_is_small_and_runs_from_disk_and_http(browser, static_server, tmp_path):
    page = build_one(tmp_path, EXAMPLES / "star_catcher.py", html=True)
    assert page.is_file() and page.name == "star_catcher.html"
    assert list(tmp_path.iterdir()) == [page]
    text = page.read_text()
    assert "\"three\": {\"core\"" not in text and len(text) < 200_000
    assert "<script type=\"module\">" in text
    for url in (page.as_uri(), static_server(tmp_path) + page.name):
        w = Watched(browser, url)
        w.check("single-star_catcher.png")
        assert scene_info(w.page)["runtime"] == "Python in a worker"
        w.page.close()


def test_single_file_3d_carries_three_and_runs_from_disk(browser, static_server, tmp_path):
    page = build_one(tmp_path, EXAMPLES / "solar_system.py", html=True)
    text = page.read_text()
    assert "\"three\": {\"core\"" in text and len(text) > 500_000
    for url in (page.as_uri(), static_server(tmp_path) + page.name):
        w = Watched(browser, url)
        w.check("single-solar_system.png")
        w.page.close()


def test_single_file_carries_added_files(browser, tmp_path):
    (tmp_path / "words.txt").write_text("blue")
    code = ('colour = open("words.txt").read().strip()\n'
            'def draw():\n    ctx.fill_style = colour\n    ctx.fill_rect(0, 0, width, height)\n')
    page = build_one(tmp_path, code, html=True, add=[tmp_path / "words.txt"])
    w = Watched(browser, page.as_uri())
    w.wait_running()
    w.page.wait_for_timeout(800)
    assert w.scenes()[0].evaluate(PIXEL, [0.5, 0.5]) == [0, 0, 255]


def test_single_file_cli(tmp_path):
    import subprocess
    import sys
    out = tmp_path / "game.html"
    r = subprocess.run([sys.executable, "-m", "pyctures", "build", str(EXAMPLES / "bouncing_balls.py"), "-o", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert out.is_file() and "bouncing_balls.py" in out.read_text()
    r = subprocess.run([sys.executable, "-m", "pyctures", "build", str(EXAMPLES / "website"), "-o", str(tmp_path / "x.html")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "one scene" in r.stderr


# ---------------------------------------------------------------- measure mode

def _measure_box(page):
    page.wait_for_selector(".pyctures-measure", timeout=30000)
    page.wait_for_timeout(1200)
    return page.inner_text(".pyctures-measure")


def test_measure_box_on_a_built_page(browser, static_server, tmp_path):
    out = build_one(tmp_path, EXAMPLES / "bouncing_balls.py")
    url = static_server(out)
    w = Watched(browser, url)
    w.wait_running()
    w.page.wait_for_timeout(1500)
    assert not w.page.query_selector(".pyctures-measure")      # off unless asked for
    w.page.close()
    w = Watched(browser, url + "?measure=1")
    w.wait_running()
    text = _measure_box(w.page)
    for word in ("fps", "missed", "python", "round trip", "draw", "queued", "Python in a worker"):
        assert word in text, text
    m = w.page.evaluate("() => window.__pycturesMeasure")
    assert m["fps"] > 0 and "python" in m["ms"] and "round_trip" in m["ms"] and "missedRefreshes" in m
    w.page.screenshot(path=str(SHOTS / "measure-built.png"))


def test_measure_box_on_an_embed(browser, static_server, tmp_path):
    from pyctures.build import build
    page = tmp_path / "page"
    page.mkdir()
    (page / "balls.py").write_text((EXAMPLES / "bouncing_balls.py").read_text())
    (page / "index.html").write_text(
        '<!doctype html><title>Embed</title><div data-pyctures-src="balls.py" data-pyctures-measure '
        'style="height:300px"></div><script type="module" src="pyctures/pyctures.js"></script>')
    build(page, tmp_path / "site", say=lambda *a: None)
    w = Watched(browser, static_server(tmp_path / "site"))
    w.wait_running()
    assert "fps" in _measure_box(w.page)


def test_measure_box_on_a_run_page(browser, pyctures_run):
    p = pyctures_run(EXAMPLES / "bouncing_balls.py")
    w = Watched(browser, p.url + "?measure=1")
    w.wait_running()
    text = _measure_box(w.page)
    assert "fps" in text and "your Python" in text
