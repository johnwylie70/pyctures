"""The HTML pages ``pyctures run`` serves and ``pyctures build`` writes."""
import html
import os
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
