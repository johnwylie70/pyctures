"""Copy the sound library and the on-screen controls into Pyctures, from where they are written.

    python scripts/sync_libraries.py

A scene that says ``from synths import *`` or ``from pydials import *`` needs two halves of each
library: the page's half (JavaScript, and for sound the engine and its audio worklet) and the
Python half, as one file that a browser's Python can be handed. They are written in four
repositories beside this one (``synths.js``, ``synths-py``, ``dials.js``, ``pydials``) and
are carried here as copies, under ``src/pyctures/web/synths`` and ``src/pyctures/web/dials``.
Change them there and run this again. A page loads them only for a scene that uses them.

Each file is taken as its repository last COMMITTED it, not as it stands, so work that is half
done there is not brought across. ``--working`` takes the files as they are.

The tests fail while a copy differs from what the repository beside this one last committed.
"""
import subprocess
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
    ("synths.js", "synths-midi.js"): WEB / "synths" / "synths-midi.js",
    ("synths.js", "LICENSE"): WEB / "synths" / "LICENSE",
    ("synths-py", "src/synths/__init__.py"): WEB / "synths" / "synths.py",
    ("dials.js", "dials.js"): WEB / "dials" / "dials.js",
    ("dials.js", "LICENSE"): WEB / "dials" / "LICENSE",
    ("pydials", "src/pydials/__init__.py"): WEB / "dials" / "pydials.py",
    ("notation.js", "notation.js"): WEB / "notation" / "notation.js",
    ("notation.js", "LICENSE"): WEB / "notation" / "LICENSE",
    ("notation.js", "LICENSE-GLYPHS"): WEB / "notation" / "LICENSE-GLYPHS",
    ("pynotation", "src/pynotation/__init__.py"): WEB / "notation" / "pynotation.py",
}


def committed(repo, name, working=False):
    """A file of a repository as it was last committed (or as it stands: `working`, or where there is no git). None if it is not there."""
    if not working:
        try:
            return subprocess.run(["git", "-C", str(repo), "show", "HEAD:" + name], capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            pass
    file = Path(repo) / name
    return file.read_bytes() if file.is_file() else None


def main(working=False, beside=BESIDE):
    for (repo, name), to in COPIES.items():
        data = committed(Path(beside) / repo, name, working)
        if data is None:
            raise SystemExit("%s was not found (looked for %s)" % (name, Path(beside) / repo / name))
        to.parent.mkdir(parents=True, exist_ok=True)
        to.write_bytes(data)
        print("copied %-28s %7d bytes  from %s" % (to.relative_to(WEB), len(data), repo))


if __name__ == "__main__":
    main("--working" in sys.argv)
