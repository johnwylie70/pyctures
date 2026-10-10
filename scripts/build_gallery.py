"""Build the online gallery: every example, running, with its code beside it.

    .venv/bin/python scripts/build_gallery.py            # -> site/gallery/
    .venv/bin/python scripts/build_gallery.py --shots    # also take the card pictures (needs Playwright)
    .venv/bin/python scripts/build_gallery.py --gif      # also record docs/images/gallery.gif (needs ffmpeg)
    .venv/bin/python scripts/build_gallery.py --readme   # also take the README's pictures of its examples

The pages are plain HTML with scenes put in inline (data-pyctures-src), so the
gallery is itself built with `pyctures build`, the way any website would be.
"""
import argparse
import re
import functools
import html
import http.server
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import pyctures  # noqa: E402
from pyctures.build import build, scene_images  # noqa: E402

EXAMPLES = ROOT / "examples"
REPO = "https://github.com/johnwylie70/pyctures"
STUDIO = "https://www.circuitry.dev"
SITE = "https://johnwylie70.github.io/pyctures/"

# (file, title, what it is, how to play with it). Shown in this order.
SCENES = [
    ("solar_system.py", "Solar System", "Planets in turning groups, a moon, a light at the sun and 2,000 stars.", "Drag to look around."),
    ("star_catcher.py", "Star Catcher", "A 2D game with emoji sprites, a score and lives.", "Arrow keys or drag. Catch the stars, dodge the rocks."),
    ("space_rocks.py", "Space Rocks", "Steer a ship and shoot the rocks, which break in two.", "Left and right turn, up flies, space shoots. Or hold to fly to your finger, and tap to shoot."),
    ("brick_breaker.py", "Brick Breaker", "A bat, a ball and a wall of bricks.", "Arrow keys or drag. Clear the wall to win."),
    ("bat_and_ball.py", "Bat and Ball", "One player against the computer. First to 5 wins.", "Up and down, or drag."),
    ("snake.py", "Snake", "A game on a grid: eat the apples and grow. Your best score is kept.", "Arrow keys, or tap the side to turn to."),
    ("high_score.py", "High Score", "Catch the star as often as you can in 10 seconds. The best score is still there next time: save() and load().", "Click or tap the star."),
    ("cube_spiral.py", "Cube Spiral", "400 cubes in a rainbow spiral, turning.", "Drag to look around."),
    ("cube_dodge.py", "Cube Dodge", "A 3D game with shadows, fog and the keyboard.", "Arrow keys or drag. Dodge the red blocks."),
    ("bouncing_balls.py", "Bouncing Balls", "A 2D animation with trails and hsl() colours.", "Click or tap to add a ball."),
    ("textured_cube.py", "Textured Cube", "A picture from a file, wrapped round a turning crate.", "Drag to turn it."),
    ("torus_knot.py", "Torus Knot", "One shape, lit, turning.", "Drag to look around it."),
    ("live_chart.py", "Live Chart", "A line chart of a made-up sensor, updating as you watch.", "Move the mouse over it to read a value."),
    ("wave_grid.py", "Wave Grid", "225 cubes rising and falling like water.", "Drag to look around."),
    ("starfield.py", "Starfield", "Fly through 300 stars.", "Hold the mouse down (or a finger) to go faster."),
    ("lit_scene.py", "Lit Scene", "Shapes on a floor, with a spotlight and shadows.", "Drag to orbit, pinch or scroll to zoom."),
    ("spiral_garden.py", "Spiral Garden", "200 dots placed on the golden angle, turning slowly.", ""),
    ("from_javascript_3d.py", "From JavaScript: 3D", "The classic three.js spinning cube, line for line in Python.", ""),
    ("from_javascript_2d.py", "From JavaScript: 2D", "A canvas example written the way JavaScript writes it.", "Click it."),
    ("type_and_measure.py", "Typing", "Type and your words appear, with a box drawn to fit them.", "Click it, then type."),
    ("night_sky.py", "Night Sky", "A whole picture from the plain drawing functions: stars, a moon, a hill and a house.", ""),
    ("hello.py", "Hello", "The smallest scene: a background and one circle.", ""),
    ("moving.py", "Moving", "A circle crossing the picture: update(dt) and one number.", "Change the 200 in the code to change its speed."),
    ("follow.py", "Follow", "A circle you move.", "Arrow keys, or hold the mouse or a finger on it."),
    ("first_game.py", "First Game", "Catch the falling stars in the basket: sprites, touches() and a score.", "Move the mouse, or drag a finger."),
    ("ring.py", "Ring", "Twelve circles in a ring.", ""),
]

# The scenes the README's animated picture shows, a few seconds each.
GIF_SCENES = ["solar_system.py", "star_catcher.py", "cube_spiral.py", "bouncing_balls.py", "wave_grid.py"]

STYLE = """
:root { --bg: #0d1117; --panel: #161b22; --line: #30363d; --text: #e6edf3; --dim: #9198a1; --accent: #3fb950; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 16px/1.6 system-ui, -apple-system, sans-serif; }
a { color: var(--accent); }
header, main, footer { max-width: 1120px; margin: 0 auto; padding: 0 16px; }
header { padding-top: 40px; }
h1 { font-size: clamp(32px, 6vw, 52px); line-height: 1.1; margin: 0 0 12px; letter-spacing: -0.02em; }
h1 small { display: block; font-size: 0.45em; color: var(--dim); font-weight: 500; letter-spacing: 0; margin-top: 8px; }
.lead { font-size: 18px; color: var(--dim); max-width: 720px; margin: 0 0 24px; }
.actions { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 40px; }
.install { font: 15px ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--panel); border: 1px solid var(--line);
           border-radius: 8px; padding: 10px 14px; display: inline-flex; gap: 12px; align-items: center; }
.install button { background: none; border: 1px solid var(--line); color: var(--dim); border-radius: 6px; padding: 2px 8px; cursor: pointer; font: inherit; font-size: 13px; }
.btn { display: inline-block; padding: 10px 16px; border-radius: 8px; border: 1px solid var(--line); color: var(--text);
       text-decoration: none; background: var(--panel); font-weight: 600; }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #04260f; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; text-decoration: none; color: var(--text);
        transition: transform .15s, border-color .15s; }
.card:hover { transform: translateY(-2px); border-color: var(--accent); }
.card img, .card .noimg { display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; background: #000; }
.card div { padding: 12px 14px 14px; }
.card h3 { margin: 0 0 4px; font-size: 17px; }
.card p { margin: 0; color: var(--dim); font-size: 14px; }
.tag { font-size: 12px; color: var(--dim); border: 1px solid var(--line); border-radius: 99px; padding: 0 8px; margin-left: 6px; font-weight: 500; vertical-align: 2px; }
footer { color: var(--dim); font-size: 14px; padding-top: 48px; padding-bottom: 48px; }
.scene { width: 100%; aspect-ratio: 16 / 9; max-height: 75vh; border-radius: 12px; overflow: hidden; background: #000; border: 1px solid var(--line); }
.crumbs { padding-top: 24px; font-size: 14px; }
.scene-head h1 { font-size: clamp(26px, 5vw, 38px); margin: 8px 0 4px; }
.scene-head p { margin: 0 0 16px; color: var(--dim); }
.cols { display: grid; grid-template-columns: 1fr; gap: 24px; margin-top: 24px; }
@media (min-width: 900px) { .cols { grid-template-columns: 2fr 1fr; } }
pre { margin: 0; background: var(--panel) !important; border: 1px solid var(--line); border-radius: 12px; padding: 16px !important;
      overflow-x: auto; font-size: 14px; line-height: 1.5; }
.cols > div { min-width: 0; }
pre code.hljs { padding: 0; background: none; }
.side h2 { font-size: 16px; margin: 0 0 8px; }
.side pre { font-size: 13px; padding: 10px 12px !important; margin-bottom: 16px; }
.side p { color: var(--dim); font-size: 14px; }
"""

HIGHLIGHT = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">\n'
             '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>\n'
             '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>\n'
             '<script>hljs.highlightAll()</script>')

COPY = """<script>
document.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => {
  navigator.clipboard.writeText(b.dataset.copy).then(() => { b.textContent = 'Copied'; setTimeout(() => b.textContent = 'Copy', 1200) })
})
</script>"""


def head(title, description):
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<title>%s</title>\n<meta name=\"description\" content=\"%s\">\n"
            "<meta property=\"og:title\" content=\"%s\">\n<meta property=\"og:description\" content=\"%s\">\n"
            "<meta property=\"og:image\" content=\"%sthumbs/solar_system.jpg\">\n"
            "<style>%s</style>\n</head>\n<body>\n"
            % (html.escape(title), html.escape(description), html.escape(title), html.escape(description), SITE, STYLE))


def is_3d(source):
    return "THREE." in source


def first_comment_block(source):
    return [l for l in source.splitlines() if l.startswith("#")]


def index_page():
    cards = []
    for name, title, what, _ in SCENES:
        stem = Path(name).stem
        kind = "3D" if is_3d((EXAMPLES / name).read_text(encoding="utf-8")) else "2D"
        cards.append('<a class="card" href="%s.html"><img src="thumbs/%s.jpg" alt="%s" loading="lazy" '
                     'onerror="this.outerHTML=\'<span class=noimg></span>\'">'
                     '<div><h3>%s<span class="tag">%s</span></h3><p>%s</p></div></a>'
                     % (stem, stem, html.escape(title), html.escape(title), kind, html.escape(what)))
    return (head("Pyctures: Python 2D and 3D graphics in your browser",
                 "Games, animations, charts and 3D scenes written in Python, running live in your browser. Click any one to see its code.")
            + '<header>\n<h1>Pyctures<small>Python 2D and 3D graphics, drawn in your web browser</small></h1>\n'
            '<p class="lead">Every scene below is a short Python program. Click one and it runs live in your browser, with its code beside it. '
            'Python gets the web\'s 2D canvas and three.js 3D, with the names JavaScript uses.</p>\n'
            '<div class="actions"><span class="install">pip install pyctures<button data-copy="pip install pyctures">Copy</button></span>'
            '<a class="btn primary" href="%s">Star on GitHub</a><a class="btn" href="%s/tree/main/docs">Docs</a></div>\n</header>\n'
            '<main><div class="grid">\n%s\n</div></main>\n' % (REPO, REPO, "\n".join(cards))
            + footer() + COPY + "\n</body>\n</html>\n")


def scene_page(name, title, what, how):
    stem = Path(name).stem
    source = (EXAMPLES / name).read_text(encoding="utf-8")
    return (head("%s · Pyctures" % title, "%s Written in Python with Pyctures, running live in your browser." % what)
            + '<main>\n<div class="crumbs"><a href="index.html">← All scenes</a></div>\n'
            '<div class="scene-head"><h1>%s</h1><p>%s %s</p></div>\n'
            '<div class="scene" data-pyctures-src="%s"></div>\n'
            '<div class="cols"><div><pre><code class="language-python">%s</code></pre></div>\n'
            '<div class="side"><h2>Run it yourself</h2>\n<pre>pip install pyctures\npyctures run %s</pre>\n'
            '<h2>Put it on your website</h2>\n<pre>pyctures build %s -o site/</pre>\n'
            '<p>Python runs in the visitor\'s browser, so any static host works. '
            '<a href="%s/blob/main/docs/website.md">How</a> · <a href="%s/blob/main/examples/%s">This file on GitHub</a></p>\n'
            '</div></div>\n</main>\n'
            % (html.escape(title), html.escape(what), html.escape(how), name, html.escape(source),
               name, name, REPO, REPO, name)
            + footer() + HIGHLIGHT + '\n<script type="module" src="pyctures/pyctures.js"></script>\n</body>\n</html>\n')


def footer():
    return ('<footer>Pyctures %s · MIT licence · <a href="%s">GitHub</a> · <a href="https://pypi.org/project/pyctures/">PyPI</a> · '
            '<a href="https://www.npmjs.com/package/pyctures">npm</a><br>'
            'Pyctures is also built into <a href="%s">Circuitry Studio</a>, where these scenes run in a code editor '
            'with a live preview beside the code.</footer>\n' % (pyctures.__version__, REPO, STUDIO))


def stage(folder):
    for name, title, what, how in SCENES:
        shutil.copyfile(EXAMPLES / name, folder / name)
        for key, image in scene_images(EXAMPLES / name, (EXAMPLES / name).read_text(encoding="utf-8")):
            (folder / key).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(image, folder / key)
        (folder / (Path(name).stem + ".html")).write_text(scene_page(name, title, what, how), encoding="utf-8")
    (folder / "index.html").write_text(index_page(), encoding="utf-8")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class Serve:
    """The built gallery on a local port, for the screenshots."""

    def __init__(self, folder):
        handler = functools.partial(Quiet, directory=str(folder))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = "http://127.0.0.1:%d/" % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


def open_scene(browser, url, size):
    page = browser.new_page(viewport={"width": size[0], "height": size[1]}, device_scale_factor=1)
    page.goto(url)
    page.wait_for_selector('[data-pyctures-status="running"]', timeout=120000)
    return page, page.locator(".scene")


def shots(out):
    from playwright.sync_api import sync_playwright
    thumbs = out / "thumbs"
    thumbs.mkdir(exist_ok=True)
    server = Serve(out)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            for name, *_ in SCENES:
                stem = Path(name).stem
                page, scene = open_scene(b, server.url + stem + ".html", (1280, 900))
                page.wait_for_timeout(3000)
                scene.screenshot(path=str(thumbs / (stem + ".jpg")), type="jpeg", quality=82)
                page.close()
                print("  thumbs/%s.jpg" % stem)
            b.close()
    finally:
        server.close()


def gif(out, target, seconds=3.0, fps=15):
    from playwright.sync_api import sync_playwright
    frames = Path(tempfile.mkdtemp(prefix="pyctures-gif-"))
    server = Serve(out)
    n = 0
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            for name in GIF_SCENES:
                page, scene = open_scene(b, server.url + Path(name).stem + ".html", (1100, 900))
                page.wait_for_timeout(1500)
                for _ in range(int(seconds * fps)):
                    scene.screenshot(path=str(frames / ("f%05d.png" % n)))
                    n += 1
                    page.wait_for_timeout(1000 / fps)
                page.close()
            b.close()
    finally:
        server.close()
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(frames / "f%05d.png"),
                    "-vf", "scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", str(target)], check=True)
    shutil.rmtree(frames)
    print("Recorded %s (%d KB)" % (target.relative_to(ROOT), target.stat().st_size // 1024))


def readme_stills():
    """A still of what each of the README's examples draws, beside its code."""
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stills = [("readme-hello", EXAMPLES / "hello.py"),
                  ("readme-first-game", EXAMPLES / "first_game.py"),
                  ("readme-textured-cube", EXAMPLES / "textured_cube.py"),
                  ("readme-from-javascript", EXAMPLES / "from_javascript_3d.py")]
        for name, scene in stills:
            build(scene, tmp / "site" / name, say=lambda *a: None)
        server = Serve(tmp / "site")
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
                for name, _ in stills:
                    page = b.new_page(viewport={"width": 640, "height": 360}, device_scale_factor=2)
                    page.goto(server.url + name + "/index.html")
                    page.wait_for_selector('[data-pyctures-status="running"]', timeout=120000)
                    page.wait_for_timeout(2500)
                    target = ROOT / "docs" / "images" / (name + ".jpg")
                    page.screenshot(path=str(target), type="jpeg", quality=85)
                    page.close()
                    print("  %s" % target.relative_to(ROOT))
                b.close()
        finally:
            server.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--out", default=str(ROOT / "site" / "gallery"))
    parser.add_argument("--shots", action="store_true", help="take the card pictures")
    parser.add_argument("--gif", action="store_true", help="record docs/images/gallery.gif")
    parser.add_argument("--readme", action="store_true", help="take the README's pictures of its examples")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists():
        keep = out / "thumbs"
        saved = Path(tempfile.mkdtemp()) / "thumbs" if keep.exists() else None
        if saved:
            shutil.copytree(keep, saved)
        shutil.rmtree(out)
    else:
        saved = None
    with tempfile.TemporaryDirectory() as tmp:
        stage(Path(tmp))
        build(Path(tmp), out, title="Pyctures", say=lambda *a: None)
    if saved:
        shutil.copytree(saved, out / "thumbs")
    (out / ".nojekyll").write_text("")   # GitHub Pages: serve the files as they are
    print("Built %s" % out)
    if args.shots:
        shots(out)
    if args.gif:
        gif(out, ROOT / "docs" / "images" / "gallery.gif")
    if args.readme:
        readme_stills()


if __name__ == "__main__":
    main()
