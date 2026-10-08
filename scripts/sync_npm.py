"""Copy the browser half into npm/ before `npm publish`.

The files live once, in src/pyctures/web/ (and the Python half in
src/pyctures/__init__.py); this copies them into the npm package and checks
the versions agree.
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from pyctures import pages  # noqa: E402

NPM = ROOT / "npm"


def main():
    for published, source in pages.ASSETS.items():
        target = NPM / published
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for name in ("LICENSE", "THIRD-PARTY-NOTICES"):
        shutil.copyfile(ROOT / name, NPM / name)
    npm_version = json.loads((NPM / "package.json").read_text())["version"]
    py_version = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    if npm_version != py_version:
        raise SystemExit("npm/package.json is %s but pyproject.toml is %s" % (npm_version, py_version))
    print("npm/ is ready to publish as pyctures@%s" % npm_version)


if __name__ == "__main__":
    main()
