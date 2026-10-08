"""``pyctures build``: a static folder, or one HTML file, that runs scenes in any browser.

The folder holds the scene, an ``index.html`` and a ``pyctures/`` folder
(the browser half, three.js, and the Python half as ``pyctures.py``). Python
itself is Pyodide, loaded from its official CDN, and runs in a Web Worker so
the page's own thread only draws. Every path is relative, so the folder can be
put on any static host, or inside an existing site.

When the output ends in ``.html`` (``-o scene.html``) the result is ONE file
holding all of that (three.js only when the scene uses it), which also opens
straight from disk.

Images the scene loads by a relative path (``load_image("textures/brick.png")``,
``THREE.TextureLoader().load(...)``) are found in its string literals and
included: copied beside the page in a folder, packed into a single file (where
the browser half points those loads at the packed copy). An image that is
named but not there is a warning, not an error.
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
    if out.suffix.lower() in (".html", ".htm"):
        if not target.is_file():
            raise SystemExit("pyctures: a single .html file holds one scene; "
                             "give a folder for -o to build %s" % target.name)
        return build_single(target, out, add, title, say)
    out.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        written = _build_scene(target, out, add, title, say)
    else:
        written = _build_folder(target, out, title, say)
    copy_assets(out)
    say("Built %s" % out)
    for w in written:
        say("  %s" % w)
    say("  pyctures/  (the browser half and three.js)")
    say("Serve the folder with any static web server, for example:\n"
        "  python -m http.server --directory %s" % _short(out))
    return out


def build_single(scene, out, add=(), title=None, say=print):
    """One self-contained .html file for one scene."""
    if scene.suffix != ".py":
        raise SystemExit("pyctures: %s is not a .py file" % scene.name)
    source = scene.read_text(encoding="utf-8")
    files = {}
    for rel, path in _added(scene, add):
        files[rel] = path.read_bytes()
    images = []
    for key, path in scene_images(scene, source, say):
        if key not in files:
            files[key] = path.read_bytes()
        images.append(key)
    three = pages.uses_three(source)
    page = pages.single_page(title or scene.stem.replace("_", " ").title(), scene.name, source,
                             files=files, three=three)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    say("Built %s (%d KB%s)" % (_short(out), (len(page.encode("utf-8")) + 1023) // 1024,
                                 ", with three.js" if three else ""))
    if images:
        say("  with %d image%s: %s" % (len(images), "" if len(images) == 1 else "s", ", ".join(images)))
    say("One file: open it in a browser, or put it on any website.")
    return out


def _added(scene, add):
    """(path relative to the scene, file) for every --add file, folders expanded."""
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
                yield (rel / f.relative_to(extra)).as_posix(), f
        else:
            yield rel.as_posix(), extra


def scene_images(scene, source, say=print):
    """(key, file) for each image the scene names by a relative path and that
    exists beside it. A named image that is not there is reported with ``say``."""
    found = []
    for written in pages.image_paths_in_source(source):
        key = pages.packed_key(written)
        path = (scene.parent / key).resolve()
        if path.is_file():
            if key not in (k for k, _ in found):
                found.append((key, path))
        else:
            say("Warning: %s loads the image %s, which was not found (looked for %s)."
                % (scene.name, written, _short(path)))
    return found


def _top_level(scene, add):
    """What each --add names, relative to the scene (a folder as itself)."""
    for extra in add:
        extra = Path(extra).resolve()
        try:
            yield extra.relative_to(scene.parent).as_posix()
        except ValueError:
            yield extra.name


def _build_scene(scene, out, add, title, say):
    if scene.suffix != ".py":
        raise SystemExit("pyctures: %s is not a .py file" % scene.name)
    written = []
    shutil.copyfile(scene, out / scene.name)
    written.append(scene.name)
    files = []
    for rel, f in _added(scene, add):
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, out / rel)
        files.append(rel)
    written.extend(dict.fromkeys(_top_level(scene, add)))
    for key, f in scene_images(scene, scene.read_text(encoding="utf-8"), say):
        target = (out / key).resolve()
        if out != target.parent and out not in target.parents:
            say("Warning: %s loads the image %s, which is outside the scene's folder and was "
                "not copied. Move it into the scene's folder." % (scene.name, key))
            continue
        if target != f:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, target)
        written.append(key)
    page = pages.scene_page(title or scene.stem.replace("_", " ").title(), scene.name,
                            "pyctures/pyctures.js", files=files)
    (out / "index.html").write_text(page, encoding="utf-8")
    written.append("index.html")
    return written


def _build_folder(folder, out, title, say):
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
        if f.suffix == ".py":
            # Copied with the folder already; only say which named images are missing.
            scene_images(f, f.read_text(encoding="utf-8", errors="replace"), say)
            if len(rel.parts) == 1:
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
