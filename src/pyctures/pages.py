"""The HTML pages ``pyctures run`` serves and ``pyctures build`` writes."""
import base64
import html
import json
import os
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent / "web"
RUNTIME = Path(__file__).resolve().parent / "__init__.py"

# Published path inside the ``pyctures/`` asset folder -> file in the package.
ASSETS = {
    "pyctures.js": WEB / "pyctures.js",
    "pyctures.py": RUNTIME,
    "three/three.module.min.js": WEB / "three" / "three.module.min.js",
    "three/three.core.min.js": WEB / "three" / "three.core.min.js",
    "three/OrbitControls.js": WEB / "three" / "OrbitControls.js",
    "three/LICENSE": WEB / "three" / "LICENSE",
}


def scene_page(title, src, script, server=False, output="console", files=()):
    """A page that is one scene, filling the window."""
    attrs = ' data-pyctures-src="%s" data-pyctures-fullpage' % html.escape(src)
    if output == "panel":
        attrs += ' data-pyctures-output="panel"'
    if files:
        attrs += ' data-pyctures-files="%s"' % html.escape(",".join(files))
    meta = '<meta name="pyctures-server" content="ws">\n' if server else ""
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{meta}<title>{title}</title>
<style>
html,body{{margin:0;height:100%;overflow:hidden;background:#0b0b0f}}
#scene{{position:fixed;inset:0}}
</style>
</head>
<body>
<div id="scene"{attrs}></div>
<script type="module" src="{script}"></script>
</body>
</html>
""".format(meta=meta, title=html.escape(title), attrs=attrs, script=html.escape(script))


def _json_for_html(value):
    """JSON that is safe inside a <script> element."""
    return (json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _script_for_html(js):
    """JavaScript source that is safe inside a <script> element."""
    return js.replace("</script", "<\\/script").replace("<!--", "<\\!--")


def single_page(title, name, source, files=None, three=False):
    """One self-contained HTML file: the scene, the Python half, the browser
    half (whose worker it carries inside), and three.js only when the scene
    uses it. Python itself (Pyodide) still loads from its CDN.

    ``files``: {path: bytes} the scene opens or imports, and the images it
    loads by a relative path (the browser half points those loads at the
    packed copy).
    """
    files = files or {}
    data = {
        "runtime": RUNTIME.read_text(encoding="utf-8"),
        "sources": {name: source},
        "files": {k: base64.b64encode(v).decode("ascii") for k, v in files.items()},
    }
    if three:
        data["three"] = {
            "core": (WEB / "three" / "three.core.min.js").read_text(encoding="utf-8"),
            "module": (WEB / "three" / "three.module.min.js").read_text(encoding="utf-8"),
            "orbit": (WEB / "three" / "OrbitControls.js").read_text(encoding="utf-8"),
        }
    attrs = ' data-pyctures-src="%s" data-pyctures-fullpage' % html.escape(name)
    if files:
        attrs += ' data-pyctures-files="%s"' % html.escape(",".join(files))
    licence = ("<!-- Made with Pyctures (MIT). Includes three.js (MIT, three.js authors). "
               "Loads Pyodide (MPL 2.0) from its CDN. -->\n" if three else
               "<!-- Made with Pyctures (MIT). Loads Pyodide (MPL 2.0) from its CDN. -->\n")
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
{licence}<style>
html,body{{margin:0;height:100%;overflow:hidden;background:#0b0b0f}}
#scene{{position:fixed;inset:0}}
</style>
</head>
<body>
<div id="scene"{attrs}></div>
<script type="application/json" id="pyctures-inline">{data}</script>
<script type="module">
{script}
</script>
</body>
</html>
""".format(title=html.escape(title), licence=licence, attrs=attrs, data=_json_for_html(data),
           script=_script_for_html((WEB / "pyctures.js").read_text(encoding="utf-8")))


# A relative path to an image: no scheme, not absolute, an image extension.
# The browser half (pyctures.js, IMAGE_PATH) makes the same test.
IMAGE_PATH = re.compile(r"^(?![a-z][a-z0-9+.-]*:|/)(?:\./)?[^\s\"'<>?#]+\.(png|jpe?g|gif|webp|svg|bmp|avif)$",
                        re.I)
_LITERAL = re.compile(r"""(['"])((?:\\.|(?!\1)[^\\\n])*)\1""")


def is_relative_image_path(s):
    return len(s) < 300 and IMAGE_PATH.match(s) is not None


def image_paths_in_source(source):
    """Relative image paths named by string literals in a scene, as written
    (``"./a.png"`` stays ``./a.png``). Paths built at run time cannot be seen."""
    found = []
    for m in _LITERAL.finditer(source):
        if is_relative_image_path(m.group(2)) and m.group(2) not in found:
            found.append(m.group(2))
    return found


def packed_key(path):
    """The key an image is packed under: as written, without a leading ``./``."""
    return re.sub(r"^(\./)+", "", path)


def uses_three(source):
    """Whether a scene uses three.js (the same test the browser half makes)."""
    return re.search(r"\bTHREE\b|\baddons\b", source) is not None


def scene_list_page(title, scenes):
    """A plain list of the scenes in a folder: (link, name) pairs."""
    items = "\n".join('<li><a href="%s">%s</a></li>' % (html.escape(link), html.escape(name))
                      for link, name in scenes)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body{{font:16px/1.6 system-ui,sans-serif;margin:0;padding:24px 16px;background:#0b0b0f;color:#e5e7eb}}
main{{max-width:640px;margin:0 auto}} a{{color:#7cc4ff}}
</style>
</head>
<body><main>
<h1>{title}</h1>
<ul>
{items}
</ul>
</main></body>
</html>
""".format(title=html.escape(title), items=items or "<li>No .py files here.</li>")


def inject_server_meta(text):
    """Mark a page served by ``pyctures run`` so its scenes use your Python."""
    tag = '<meta name="pyctures-server" content="ws">'
    low = text.lower()
    i = low.find("<head>")
    if i >= 0:
        return text[:i + 6] + "\n" + tag + text[i + 6:]
    return tag + "\n" + text


SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".mypy_cache",
             ".pytest_cache", ".idea", ".vscode"}


def walk(root):
    """Every file under root, skipping hidden folders and environments."""
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if not f.startswith("."):
                yield Path(folder) / f
