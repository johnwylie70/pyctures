# Getting Started

Full reference: [www.circuitry.dev/docs/pyctures](https://www.circuitry.dev/docs/pyctures) (in Circuitry Studio's help)

Pyctures ("Python pictures") gives Python the full set of JavaScript graphics functions: the web's 2D canvas for 2D, and three.js for 3D. Your program draws in a web browser: shapes, text, pictures, moving sprites, games, charts and 3D scenes. The names are the ones JavaScript uses, so any JavaScript graphics example can be brought across easily (see [Bringing a JavaScript example across](from-javascript.md)).

## Install

```bash
pip install pyctures
```

Pyctures needs Python 3.9 or newer and a web browser. It installs nothing else.

## Your first scene

Save this as `hello.py`:

```python
def draw():
    ctx.fill_style = "midnightblue"
    ctx.fill_rect(0, 0, width, height)

    ctx.fill_style = "gold"
    ctx.begin_path()
    ctx.arc(width / 2, height / 2, 80, 0, 6.283)
    ctx.fill()

    ctx.fill_style = "white"
    ctx.font = "32px sans-serif"
    ctx.text_align = "center"
    ctx.fill_text("Hello!", width / 2, height / 2 + 140)
```

Then run it:

```bash
pyctures run hello.py
```

Your browser opens and shows the scene. That is a whole program. There is nothing to import and nothing to set up: `draw()` is called every frame, `ctx` is the 2D drawing surface, and `width` and `height` are the size of the canvas.

## `pyctures run`: see it as you write it

- A small web server starts on your computer (at `http://localhost:8765/`, or the next free port) and your browser opens on the scene.
- **Your program runs in your own Python**, the one Pyctures is installed in. Any library you have installed works: numpy, Pillow, your own modules. The browser only draws.
- **Save the file and the scene runs again.** Keep the browser beside your editor and save to see each change.
- Anything your program prints appears at the bottom of the page and in the terminal.
- When something goes wrong, the page shows the error with the line it happened on, and the lines around it. Fix it and save.
- Press `Ctrl+C` in the terminal to stop.

| Option | What it does |
|---|---|
| `--port 9000` | Use this port. Without it, Pyctures uses 8765, or the next free one. |
| `--no-browser` | Do not open a browser. Open the address it prints yourself. |
| `--host 0.0.0.0` | Listen on every network address, not only this computer. Only do this on a network you trust. |

The scene runs as if started from its own folder, so `open("data.csv")` finds a file beside it, and `import helper` finds `helper.py` beside it.

`pyctures run` also takes a folder. It lists the scenes in it, and any web page in the folder runs its scenes with your Python (see [Use it on your website](website.md)).

## `pyctures build`: share it

```bash
pyctures build hello.py -o site/
```

This writes a folder that runs the scene entirely in the browser, with nothing on the server but files:

```text
site/
├── index.html        the page: the scene, filling the window
├── hello.py          your scene
└── pyctures/         the browser half of Pyctures, and three.js
```

Put the folder on any static web host, or try it on your own computer:

```bash
python -m http.server --directory site
```

### One file

Give an output ending in `.html` and you get a single file instead of a folder:

```bash
pyctures build hello.py -o hello.html
```

The file holds your scene, the browser half of Pyctures and, only if the scene is 3D, three.js. A 2D scene comes to about 80 KB, a 3D one about 850 KB. Open it straight from your disk with a double-click, send it to someone, or upload it anywhere that takes a web page. Files added with `--add` go inside it too.

### Images

Images the scene loads by a relative path are included automatically: `load_image("textures/brick.png")`, `THREE.TextureLoader().load("textures/brick.png")`, or any other path to a `.png`, `.jpg`, `.gif`, `.webp`, `.svg`, `.bmp` or `.avif` file written in the scene. The path is relative to the scene's file. A folder build copies each one beside the page; a single file holds them inside it. An image that is named but not there is reported as a warning, and the build carries on. A path put together while the scene runs (`"frame%d.png" % n`) cannot be seen in advance: add those images with `--add`.

### What runs where

In a built page, Python runs inside the browser with [Pyodide](https://pyodide.org), which is loaded from its official CDN (`cdn.jsdelivr.net/pyodide`) the first time the page opens. That first load takes a few seconds; after that the browser keeps it. Libraries the scene imports, such as numpy, are loaded from the same place when the scene needs them. Every path in the folder is relative, so it works wherever you put it.

Python runs in a Web Worker, a background thread of the browser, and the page's own thread only draws. Each screen refresh shows one frame, from a queue of at most two, and the game's clock moves on by exactly one refresh per frame. So motion stays even on a phone or tablet, even when a frame of Python is slow now and then. Add `?measure=1` to the page's address to see how it is doing ([The frame rate](finding-mistakes.md#the-frame-rate)).

| Option | What it does |
|---|---|
| `-o site/` | The folder to write (default `site`). Files of the same name in it are replaced; nothing else is removed. |
| `-o game.html` | Write one self-contained `.html` file instead of a folder. |
| `--add data.csv` | Also copy a file or folder the scene opens or imports. Repeat it for more. Images the scene names are included without it. |
| `--title "My game"` | The page's title. |

`pyctures build` also takes a folder: a web page with scenes in it, or a folder of scenes. See [Use it on your website](website.md).

## Using the module

Everything is ready to use without an import. The names come from the module `pyctures`, so if your editor or your habits want an import, this works too:

```python
from pyctures import *

def draw():
    ctx.fill_style = "teal"
    ctx.fill_rect(20, 20, 200, 120)
```

## Pyctures in Circuitry Studio

Pyctures comes from [Circuitry Studio](https://www.circuitry.dev), where Python scenes run in a code editor with a live preview beside the code, on iPhone, iPad, desktop and the web, with a debugger and ready-made examples. Scenes written with this library run there unchanged, and the other way round. Its help pages are at [circuitry.dev/docs/pyctures](https://www.circuitry.dev/docs/pyctures).

## What's in these docs

- [How a program is shaped](program-shape.md): drawing once, drawing every frame, loops, input, and reading values back.
- [Drawing in 2D](drawing-2d.md): shapes, colours, text, transforms, pictures and sprites.
- [3D scenes](3d.md): renderer, camera, shapes, materials, groups, orbit controls and picking.
- [Colours](colours.md): names, hex, rgb, hsl, see-through colours, gradients and patterns.
- [2D functions](2d-functions.md) and [3D functions](3d-functions.md): everything, one line each.
- [Bringing a JavaScript example across](from-javascript.md).
- [Use it on your website](website.md).
- Tutorials: [your first drawing](tutorials/first-drawing.md), [a bouncing ball](tutorials/bouncing-ball.md), [a simple game](tutorials/game.md), [a spinning cube](tutorials/spinning-cube.md), [lighting a scene](tutorials/lighting.md), [a solar system](tutorials/solar-system.md) and [a live chart](tutorials/live-chart.md).
- [Finding mistakes](finding-mistakes.md): errors, printing, and a scene that is stuck.
- [Tips and limits](tips.md).
