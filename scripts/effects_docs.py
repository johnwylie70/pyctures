"""docs/effects-reference.md: every effect and look, in Python's spelling, written from the table inside the copy of
the effects library here (src/pyctures/web/visualfx/pyvisualfx.py), so the page cannot say anything the library
does not do.

    python scripts/effects_docs.py            write the page, and bring the pictures (docs/images/effects/) from
                                              ../visualfx.js/docs/images/effects when that folder is beside this one
    python scripts/effects_docs.py --check    change nothing; code 1 if the page is not what the table gives, or a
                                              picture is missing

Run it after scripts/sync_libraries.py has brought a newer pyvisualfx. The pictures are made in the effects' own
repository (visualfx.js: scripts/docs.mjs), from the effects themselves.
"""
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "effects-reference.md"
PICTURES = ROOT / "docs" / "images" / "effects"


def table():
    spec = importlib.util.spec_from_file_location("pyvisualfx_table", ROOT / "src" / "pyctures" / "web" / "visualfx" / "pyvisualfx.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._TABLE


def snake(name):
    return re.sub(r"[A-Z]", lambda m: "_" + m.group(0).lower(), name)


def value(v):
    return "None" if v is None else "True" if v is True else "False" if v is False else json.dumps(v)


def rows(d):
    for name, s in d["settings"].items():
        kind = s["kind"]
        if kind == "choice":
            can = ", ".join('`"%s"`' % c for c in s["choices"])
        elif kind == "colour":
            can = "any colour"
        elif kind == "palette":
            can = "a palette's name, or a list of colours"
        elif kind == "bool":
            can = "True or False"
        elif s.get("place"):
            can = "a place in the scene"
        else:
            can = "%s to %s%s%s" % (value(s["min"]), value(s["max"]), {"degrees": " degrees", "s": " seconds"}.get(s.get("unit"), ""),
                                    ", a whole number" if kind == "int" else "")
        yield "| `%s` | %s | %s |" % (snake(name), "the middle" if s.get("place") else "`%s`" % value(s["default"]), can)


def page(t):
    fx = t["effects"]
    names = lambda group: [n for n in fx if fx[n]["group"] == group]
    out = ["# Every effect", "",
           "<!-- Written by scripts/effects_docs.py from the table in src/pyctures/web/visualfx/pyvisualfx.py. Do not edit it by hand. -->", "",
           "This is the list. [Effects](effects.md) is how to use them. There are %d effects and %d looks, all from `from pyvisualfx import *`." % (len(fx), len(t["looks"])), "",
           "The value in the brackets is the one a plain number (or name) sets; every other setting goes in by name, `glow(0.8, radius=40)`, and can be changed at any time, `shine.radius = 60`. Every effect also has `amount`, from 0 to 1. Lengths are in the scene's points and angles in degrees; a place (`x`, `y`) is the middle unless you say.", "",
           "The palettes: %s, or your own list of colours." % ", ".join("`%s`" % p for p in t["palettes"]), "", "## Contents", ""]
    for group in t["groups"]:
        if names(group):
            out.append("- **%s**: %s" % (group, ", ".join("[%s](#%s)" % (snake(n), snake(n)) for n in names(group))))
    out += ["- **Looks**: %s" % ", ".join("[%s](#look-%s)" % (l, l) for l in t["looks"]), ""]
    for group in t["groups"]:
        if not names(group):
            continue
        out += ["## %s" % group, ""]
        if "Backdrops" in group:
            out += ["A backdrop is a picture the graphics card makes by itself. It is behind whatever you draw, and shows wherever the canvas is clear: wipe the picture each frame with `background()` (no colour) rather than painting over it.", ""]
        if "music" in group:
            out += ["These follow the scene's sound. With no sound they are still and dark.", ""]
        for name in names(group):
            d = fx[name]
            alias = ["`%s`" % snake(a) for a, to in t["aliases"].items() if to == name]
            out += ["### %s" % snake(name), "", '<img src="images/effects/%s.jpg" width="320" height="200" alt="%s">' % (name, snake(name)), "", d["about"], "",
                    "```py", "%s(%s)" % (snake(name), ", ".join(value(d["settings"][o]["default"]) for o in d["order"])), "```", ""]
            if alias:
                out += ["Also called %s." % " and ".join(alias), ""]
            if d["cost"] == "heavy":
                out += ["**Heavy.** It looks at dozens of places for every pixel: use it alone, or with `effects_quality(0.5)`.", ""]
            elif d["cost"] == "some":
                out += ["It looks at a dozen or more places for every pixel, so it costs a little more than most.", ""]
            if d["feedback"]:
                out += ["It keeps its own last frame, so it wants a scene that moves.", ""]
            out += ["| Setting | Starts at | Can be |", "|---|---|---|"] + list(rows(d)) + [""]
    out += ["## Looks", "", 'A look is several effects at once: `look("dream")`. It has `amount`, `off()`, `on()` and `remove()` for the lot.', ""]
    for name in t["looks"]:
        parts = ["`%s(%s)`" % (snake(effect), ", ".join("%s=%s" % (snake(k), value(v)) for k, v in settings.items())) for effect, settings in t["recipes"][name]]
        out += ["### look: %s" % name, "", '<a id="look-%s"></a>' % name, "", '<img src="images/effects/look-%s.jpg" width="320" height="200" alt="look %s">' % (name, name), "",
                t["lookAbout"].get(name, ""), "", '`look("%s")` is %s.' % (name, ", then ".join(parts)), ""]
    return "\n".join(out)


def main():
    t = table()
    text = page(t)
    wanted = ["%s.jpg" % n for n in t["effects"]] + ["look-%s.jpg" % l for l in t["looks"]]
    if "--check" in sys.argv:
        problems = []
        if not PAGE.exists() or PAGE.read_text(encoding="utf-8") != text:
            problems.append("docs/effects-reference.md is not what the table of effects gives: run python scripts/effects_docs.py")
        problems += ["docs/images/effects/%s is missing" % f for f in wanted if not (PICTURES / f).exists()]
        print("\n".join(problems), end="\n" if problems else "")
        sys.exit(1 if problems else 0)
    PAGE.write_text(text, encoding="utf-8")
    theirs = ROOT.parent / "visualfx.js" / "docs" / "images" / "effects"
    PICTURES.mkdir(parents=True, exist_ok=True)
    copied = 0
    for f in wanted:
        if (theirs / f).exists() and not ((PICTURES / f).exists() and (PICTURES / f).read_bytes() == (theirs / f).read_bytes()):
            shutil.copyfile(theirs / f, PICTURES / f)
            copied += 1
    sheet = theirs.parent / "effects.jpg"
    if sheet.exists():
        shutil.copyfile(sheet, ROOT / "docs" / "images" / "effects.jpg")
    print("docs/effects-reference.md written; %d pictures brought from %s" % (copied, theirs))


if __name__ == "__main__":
    main()
