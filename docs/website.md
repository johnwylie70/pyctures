# Use It on Your Website

A Pyctures scene can live on any web page: a blog post, a course page, a portfolio. Python runs in the visitor's browser (with [Pyodide](https://pyodide.org)), so your site needs nothing but files.

There are two ways to put a scene on a page.

## 1. An iframe: the simplest

Build the scene into a folder of its own:

```bash
pyctures build orbit.py -o my-site/orbit
```

Then, in any page of your site:

```html
<iframe src="orbit/index.html" style="width: 100%; aspect-ratio: 16 / 9; border: 0"
        title="An orbit, drawn in Python"></iframe>
```

A single file works the same way: `pyctures build orbit.py -o my-site/orbit.html`, then `<iframe src="orbit.html" …>`.

The scene fills the iframe and follows its size. Nothing on your page can disturb it, and it cannot disturb your page. Each iframe runs its own copy of Python, which is fine for one or two scenes on a page.

## 2. Inline: scenes as part of the page

Put a `<div>` where each scene should go, naming its Python file, and one script tag at the end of the page:

```html
<div data-pyctures-src="balls.py"></div>
<div data-pyctures-src="knot.py" style="height: 420px"></div>

<script type="module" src="pyctures/pyctures.js"></script>
```

The scenes share one copy of Python, so a page with several stays light. It runs in a Web Worker, a background thread, so the page itself only draws and stays smooth. Each scene still has its own names and its own state: they cannot see each other.

To get the `pyctures/` folder beside your page, build the folder your page is in:

```bash
pyctures build my-page/ -o site/
```

That copies everything in `my-page/` (your HTML, your `.py` files, pictures) into `site/` and adds the `pyctures/` folder. Or load the browser half from a CDN instead, once the npm package is published (replace the version with the one you want):

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/pyctures@0.1.0/pyctures.js"></script>
```

### What a scene's box does

- **The canvas fills its box** and follows it when the box changes size, so size the `<div>` with CSS like any other element. A box with no height of its own is given a 16:9 shape.
- **A scene starts when it is scrolled into view**, and pauses while it is out of view or the tab is hidden. A long page with many scenes only runs the ones being looked at.
- **The keyboard** reaches a scene after a visitor clicks or taps it, so the arrow keys still scroll the page until then.
- **Touch** on a scene is the mouse (`mouse.down`, `mouse.x`). Scrolling a phone with a finger on a scene moves the scene, not the page, so leave some page around it to scroll by. In 3D, turn off zooming with `controls.enableZoom = False` so the mouse wheel scrolls the page.
- **Printing** goes to the browser's console.
- **Errors** are shown over the scene, with the line in the Python file, and a **Run again** button.

### Settings

Put these on the `<div>`:

| Attribute | What it does |
|---|---|
| `data-pyctures-src="game.py"` | The scene's Python file, relative to the page. Required. |
| `data-pyctures-files="words.txt,maps/level1.json"` | Files the scene opens with `open()` or imports, fetched before it starts. |
| `data-pyctures-background="#ffffff"` | The colour behind the canvas while the scene loads. |
| `data-pyctures-output="panel"` | Show printed text over the bottom of the scene, not only in the console. |
| `data-pyctures-fullpage` | The scene is the whole page: it has the keyboard from the start. |
| `data-pyctures-measure` | Show the frame rate and where each frame's time goes, in a box over the scene ([The frame rate](finding-mistakes.md#the-frame-rate)). `?measure=1` on the page's address does the same for every scene on it. |
| `data-pyctures-worker="off"` | Run Python on the page's own thread instead of a background one. Only for a browser without Web Workers. |

The div also tells you how its scene is doing: `data-pyctures-status` is `starting`, `running`, `finished` or `error`, and a `pyctures-status` event fires on it when that changes.

### From JavaScript

The module also exports what it uses, for a page that adds scenes itself:

```js
import { mount } from "./pyctures/pyctures.js"

const scene = mount(document.querySelector("#game"), { src: "game.py" })
// later
await scene.destroy()
```

Set `window.PYCTURES_NO_AUTO = true` before the script loads to stop it starting every `[data-pyctures-src]` by itself, and `window.PYCTURES_PYODIDE_URL` to load Pyodide from somewhere other than its official CDN (your own copy, for example).

## Try the example

The `examples/website` folder is a page with two scenes, a 2D one and a 3D one further down:

```bash
pyctures run examples/website          # with your own Python
pyctures build examples/website -o site/   # the static version
```

While `pyctures run` serves a folder, the pages in it run their scenes with your own Python, and saving a `.py` or `.html` file reloads them.

## Things to know

- **The first visit loads Python** (several megabytes, from Pyodide's CDN), which takes a few seconds. After that, the browser keeps it.
- **A loop that never waits** (`while True:` without `await frame()`) stops that scene, and any other scene on the page, until it is stopped: after three seconds the scene says so and offers **Stop**. The page itself keeps working. Use `draw()` and `update()`, or wait in every loop.
- **A built folder must be served** over `http://` or `https://`. Opening its `index.html` straight from disk (`file://`) does not work, because the browser will not load the scene's `.py` file that way. A single-file build (`-o scene.html`) opens from disk.
