"""``pyctures build``: a static folder that runs scenes in any browser.

The folder holds the scene, an ``index.html`` and a ``pyctures/`` folder
(the browser half, three.js, and the Python half as ``pyctures.py``). Python
itself is Pyodide, loaded from its official CDN. Every path is relative, so
the folder can be put on any static host, or inside an existing site.
"""
import shutil
import sys
from pathlib import Path

from . import pages


def copy_assets(out):
    """Write the ``pyctures/`` asset folder into ``out``."""
    dest = Path(out) / "pyctures"
    for published, source in pages.ASSETS.items():
        target = dest / published
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return dest


def build(target, out, add=(), title=None, say=print):
    target = Path(target).resolve()
    out = Path(out).resolve()
    if not target.exists():
        raise SystemExit("pyctures: %s does not exist" % target)
    out.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        written = _build_scene(target, out, add, title)
    else:
        written = _build_folder(target, out, title)
    copy_assets(out)
    say("Built %s" % out)
    for w in written:
        say("  %s" % w)
    say("  pyctures/  (the browser half and three.js)")
    say("Serve the folder with any static web server, for example:\n"
        "  python -m http.server --directory %s" % _short(out))
    return out


def _build_scene(scene, out, add, title):
    if scene.suffix != ".py":
        raise SystemExit("pyctures: %s is not a .py file" % scene.name)
    written = []
    shutil.copyfile(scene, out / scene.name)
    written.append(scene.name)
    files = []
    for extra in add:
        extra = Path(extra).resolve()
        if not extra.exists():
            raise SystemExit("pyctures: --add %s does not exist" % extra)
        try:
            rel = extra.relative_to(scene.parent)
        except ValueError:
            rel = Path(extra.name)
        if extra.is_dir():
            for f in pages.walk(extra):
                r = rel / f.relative_to(extra)
                (out / r).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, out / r)
                files.append(r.as_posix())
        else:
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(extra, out / rel)
            files.append(rel.as_posix())
        written.append(rel.as_posix())
    page = pages.scene_page(title or scene.stem.replace("_", " ").title(), scene.name,
                            "pyctures/pyctures.js", files=files)
    (out / "index.html").write_text(page, encoding="utf-8")
    written.append("index.html")
    return written


def _build_folder(folder, out, title):
    """Copy a folder (a web page with scenes in it, or a folder of scenes)."""
    written = []
    scenes = []
    for f in pages.walk(folder):
        rel = f.relative_to(folder)
        if out == f.resolve() or out in f.resolve().parents:
            continue   # the output folder is inside the input
        if rel.parts[0] == "pyctures":
            continue   # a previous build's assets; written fresh below
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, out / rel)
        written.append(rel.as_posix())
        if f.suffix == ".py" and len(rel.parts) == 1:
            scenes.append(rel)
    if not (folder / "index.html").exists():
        # A folder of scenes: one page each, and a list of them.
        links = []
        for rel in sorted(scenes):
            page = pages.scene_page(rel.stem.replace("_", " ").title(), rel.name, "pyctures/pyctures.js")
            (out / (rel.stem + ".html")).write_text(page, encoding="utf-8")
            written.append(rel.stem + ".html")
            links.append((rel.stem + ".html", rel.name))
        (out / "index.html").write_text(pages.scene_list_page(title or folder.name, links), encoding="utf-8")
        written.append("index.html")
    return written


def _short(p):
    try:
        return str(Path(p).relative_to(Path.cwd()))
    except ValueError:
        return str(p)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
