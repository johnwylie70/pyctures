"""Images a scene loads by a relative path: found and included by `pyctures build`,
and shown from a single file (from disk and over http), a built folder, a scene
embedded from a subfolder, and `pyctures run`.

The browser tests need Playwright; the built ones also need Pyodide's CDN.
"""
import struct
import time
import urllib.request
import zlib

import pytest

from conftest import WSClient
from pyctures import pages
from pyctures.build import build

COLOUR = (230, 120, 20)

SCENE_2D = '''img = load_image("textures/brick.png")

def draw():
    ctx.fill_style = "black"
    ctx.fill_rect(0, 0, width, height)
    ctx.draw_image(img, 0, 0, width, height)
'''

SCENE_3D = '''renderer = THREE.WebGLRenderer(canvas=canvas)
scene = THREE.Scene()
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.z = 3
texture = THREE.TextureLoader().load("./textures/brick.png")
texture.colorSpace = THREE.SRGBColorSpace
cube = THREE.Mesh(THREE.BoxGeometry(1.5, 1.5, 1.5), THREE.MeshBasicMaterial(map=texture))
scene.add(cube)

def draw():
    renderer.render(scene, camera)
'''


def png(rgb, size=8):
    """A small PNG of one colour."""
    row = b"\x00" + bytes(rgb) * size
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * size)) + chunk(b"IEND", b""))


def make_scene(folder, code, name="scene.py"):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "textures").mkdir(exist_ok=True)
    (folder / "textures" / "brick.png").write_bytes(png(COLOUR))
    scene = folder / name
    scene.write_text(code)
    return scene


# ---------------------------------------------------------------- build, without a browser

def test_image_paths_in_source():
    src = '''a("x.png"); b('y/z.webp'); c("not.png.txt"); d("/abs.png"); e("https://h/r.png")
f("./t/brick.JPG"); g("../up.svg"); h("x.png")'''
    assert pages.image_paths_in_source(src) == ["x.png", "y/z.webp", "./t/brick.JPG", "../up.svg"]
    assert pages.packed_key("././t/a.png") == "t/a.png"


def test_single_file_packs_the_images_the_scene_names(tmp_path):
    import base64
    import json
    import re
    scene = make_scene(tmp_path / "src", SCENE_3D)
    said = []
    out = build(scene, tmp_path / "scene.html", say=said.append)
    text = out.read_text()
    data = json.loads(re.search(r'id="pyctures-inline">(.*?)</script>', text, re.S).group(1))
    assert base64.b64decode(data["files"]["textures/brick.png"]) == png(COLOUR)
    assert 'data-pyctures-files="textures/brick.png"' in text
    assert any("1 image: textures/brick.png" in s for s in said)


def test_folder_build_copies_the_images_beside_the_page(tmp_path):
    scene = make_scene(tmp_path / "src", SCENE_2D)
    out = tmp_path / "site"
    build(scene, out, say=lambda *a: None)
    assert (out / "textures/brick.png").read_bytes() == png(COLOUR)
    assert "data-pyctures-files" not in (out / "index.html").read_text()


def test_a_missing_image_is_a_warning_not_an_error(tmp_path):
    scene = make_scene(tmp_path / "src", SCENE_2D + 'other = load_image("gone/missing.png")\n')
    for out in (tmp_path / "one.html", tmp_path / "site"):
        said = []
        build(scene, out, say=said.append)
        warnings = [s for s in said if s.startswith("Warning:")]
        assert len(warnings) == 1, said
        assert "scene.py loads the image gone/missing.png, which was not found" in warnings[0]
    assert (tmp_path / "site/textures/brick.png").is_file()
    # A folder that is a web page: its scenes are checked too.
    page = tmp_path / "page"
    make_scene(page / "scenes", 'x = load_image("nope.png")\n', name="s.py")
    (page / "index.html").write_text('<div data-pyctures-src="scenes/s.py"></div>')
    said = []
    build(page, tmp_path / "page-site", say=said.append)
    assert any("s.py loads the image nope.png" in s for s in said), said


def test_run_serves_the_images_beside_the_scene(pyctures_run, tmp_path):
    scene = make_scene(tmp_path, SCENE_2D)
    p = pyctures_run(scene)
    with urllib.request.urlopen(p.url + "textures/brick.png", timeout=10) as r:
        assert r.headers["Content-Type"] == "image/png"
        assert r.read() == png(COLOUR)
    # And the scene's commands carry the path as written, for the page to load.
    ws = WSClient(p.port, "/scene.py")
    ws.send({"id": 1, "op": "start", "info": {"width": 100, "height": 100}})
    import json
    reply = json.loads(ws.recv()["reply"])
    assert any(c[0] == "set" and c[3] == "src" and c[4] == "textures/brick.png" for c in reply["cmds"])
    ws.close()


# ---------------------------------------------------------------- in a browser

try:
    from playwright import sync_api as playwright
    from test_browser import PIXEL, Watched, cdn_reachable
    needs_cdn = pytest.mark.skipif(not cdn_reachable(), reason="Pyodide's CDN is not reachable")
except ImportError:   # the build tests above still run
    playwright = None
    needs_cdn = pytest.mark.skip(reason="needs Playwright")


@pytest.fixture(scope="module")
def browser():
    if playwright is None:
        pytest.skip("needs Playwright:  pip install playwright && playwright install chromium")
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(args=["--mute-audio", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        yield b
        b.close()


def shows_the_texture(w, index=0, timeout=60):
    """Wait until the middle of the canvas is the texture's colour."""
    end = time.time() + timeout
    colour = None
    while time.time() < end:
        el = w.scenes()[index]
        err = el.get_attribute("data-pyctures-error")
        assert err is None, err
        try:
            colour = el.evaluate(PIXEL, [0.5, 0.5])
        except Exception:
            colour = None   # no canvas yet
        if colour and all(abs(a - b) <= 6 for a, b in zip(colour, COLOUR)):
            assert not w.errors, w.errors
            return
        w.page.wait_for_timeout(300)
    raise AssertionError("the canvas shows %s, not the texture %s; errors: %s" % (colour, COLOUR, w.errors))


@needs_cdn
@pytest.mark.parametrize("code", [SCENE_2D, SCENE_3D], ids=["2d", "3d"])
def test_single_file_shows_images_from_disk_and_http(browser, static_server, tmp_path, code):
    scene = make_scene(tmp_path / "src", code)
    out = tmp_path / "out"
    out.mkdir()
    page = build(scene, out / "scene.html", say=lambda *a: None)
    assert list(out.iterdir()) == [page]   # nothing beside it to read the image from
    for url in (page.as_uri(), static_server(out) + "scene.html"):
        w = Watched(browser, url)
        shows_the_texture(w)
        w.page.close()


@needs_cdn
def test_folder_build_shows_images(browser, static_server, tmp_path):
    scene = make_scene(tmp_path / "src", SCENE_2D)
    out = tmp_path / "site"
    build(scene, out, say=lambda *a: None)
    w = Watched(browser, static_server(out))
    shows_the_texture(w)


@needs_cdn
def test_embedded_scene_in_a_subfolder_loads_images_beside_it(browser, static_server, tmp_path):
    page = tmp_path / "page"
    make_scene(page / "scenes", SCENE_2D)
    (page / "index.html").write_text(
        '<!doctype html><div data-pyctures-src="scenes/scene.py" style="width:400px;height:300px"></div>'
        '<script type="module" src="pyctures/pyctures.js"></script>')
    out = tmp_path / "site"
    build(page, out, say=lambda *a: None)
    w = Watched(browser, static_server(out))
    shows_the_texture(w)


@pytest.mark.parametrize("code", [SCENE_2D, SCENE_3D], ids=["2d", "3d"])
def test_run_shows_images(browser, pyctures_run, tmp_path, code):
    scene = make_scene(tmp_path, code)
    p = pyctures_run(scene)
    w = Watched(browser, p.url)
    shows_the_texture(w)
