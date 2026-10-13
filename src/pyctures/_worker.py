"""One scene's Python, in its own process, for ``pyctures run``.

The server starts one of these per open page. It reads one JSON request per
line on stdin and writes the runtime's JSON reply as one line. Replies go to a
private copy of stdout; the ordinary stdout is pointed at the terminal's
stderr, so a stray print can never break the stream. Printed text and errors
are also shown in the terminal.
"""
import io
import json
import os
import sys


def main():
    path = os.path.abspath(sys.argv[1])
    folder = os.path.dirname(path)
    name = os.path.basename(path)

    replies = io.open(os.dup(1), "w", encoding="utf-8", newline="\n")
    os.dup2(2, 1)
    sys.stdout = io.TextIOWrapper(io.FileIO(1, "w", closefd=False), encoding="utf-8",
                                  line_buffering=True)

    # The scene runs as if started from its own folder: its files open by
    # name, and its own modules import.
    os.chdir(folder)
    sys.path.insert(0, folder)
    sys.argv = [path]

    import pyctures

    # `from synths import *` and `from pydials import *` work with nothing more to install: Pyctures
    # carries a copy of each. They are looked for last, so a copy you have installed yourself is the one used.
    web = os.path.join(os.path.dirname(os.path.abspath(pyctures.__file__)), "web")
    sys.path.extend(os.path.join(web, name) for name in ("synths", "dials", "scenes"))

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        op = msg.get("op")
        if op == "start":
            reply = pyctures.start(msg["source"], json.dumps(msg.get("info") or {}))
            hint = _shadow_hint(name)
            if hint:
                d = json.loads(reply)
                d["err"] = hint + d.get("err", "")
                reply = json.dumps(d)
        elif op == "tick":
            reply = pyctures.tick(json.dumps(msg.get("payload") or {}))
        else:
            pyctures.stop()
            break
        _echo(reply, name)
        replies.write(reply + "\n")
        replies.flush()


def _shadow_hint(name):
    """A scene named like a standard module (random.py) hides that module."""
    stem = os.path.splitext(name)[0]
    names = getattr(sys, "stdlib_module_names", None) or {
        "random", "math", "time", "json", "typing", "string", "turtle", "types",
        "copy", "queue", "statistics", "colorsys", "array", "io", "os", "sys"}
    if stem in names:
        return ("Note: this file is called %s, the same as Python's own module %r. "
                "`import %s` will find this file instead. Rename it if that is not what you want.\n"
                % (name, stem, stem))
    return ""


def _echo(reply, name):
    """Show what the program printed, and any error, in the terminal too."""
    if '"out": ""' in reply and '"err": ""' in reply and '"error": null' in reply:
        return
    d = json.loads(reply)
    err = sys.__stderr__
    if d.get("out"):
        err.write(d["out"])
    if d.get("err"):
        err.write(d["err"])
    if d.get("error"):
        where = ("%s, line %d" % (name, d["errorLine"])) if d.get("errorLine") else name
        err.write("\n%s\n%s\n\n" % (where, d["error"]))
    err.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
