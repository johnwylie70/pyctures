"""Copy the sound library and the on-screen controls into Pyctures, from where they are written.

    python scripts/sync_libraries.py

A scene that says ``from synths import *`` or ``from pydials import *`` needs two halves of each
library: the page's half (JavaScript, and for sound the engine and its audio worklet) and the
Python half, as one file that a browser's Python can be handed. They are written in four
repositories beside this one (``synths.js``, ``synths-py``, ``dials.js``, ``pydials``) and
are carried here as copies, under ``src/pyctures/web/synths`` and ``src/pyctures/web/dials``.
Change them there and run this again. A page loads them only for a scene that uses them.

The tests fail while a copy differs from the repository beside this one.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "src" / "pyctures" / "web"
BESIDE = ROOT.parent

# (repository beside this one, file in it) -> the copy here.
COPIES = {
    ("synths.js", "synths.js"): WEB / "synths" / "synths.js",
    ("synths.js", "synths_core.wasm"): WEB / "synths" / "synths_core.wasm",
    ("synths.js", "synths-worklet.js"): WEB / "synths" / "synths-worklet.js",
    ("synths.js", "LICENSE"): WEB / "synths" / "LICENSE",
    ("synths-py", "src/synths/__init__.py"): WEB / "synths" / "synths.py",
    ("dials.js", "dials.js"): WEB / "dials" / "dials.js",
    ("dials.js", "LICENSE"): WEB / "dials" / "LICENSE",
    ("pydials", "src/pydials/__init__.py"): WEB / "dials" / "pydials.py",
}


def main(beside=BESIDE):
    for (repo, name), to in COPIES.items():
        source = Path(beside) / repo / name
        if not source.is_file():
            raise SystemExit("%s was not found (looked for %s)" % (name, source))
        to.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, to)
        print("copied %-28s %7d bytes  from %s" % (to.relative_to(WEB), to.stat().st_size, repo))


if __name__ == "__main__":
    main(*sys.argv[1:2])
