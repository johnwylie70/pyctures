# Pyctures

[![PyPI](https://img.shields.io/pypi/v/pyctures)](https://pypi.org/project/pyctures/) [![npm](https://img.shields.io/npm/v/pyctures)](https://www.npmjs.com/package/pyctures) [![Python 3.9+](https://img.shields.io/pypi/pyversions/pyctures)](https://pypi.org/project/pyctures/) [![MIT licence](https://img.shields.io/badge/licence-MIT-green)](LICENSE)

[![Pyctures scenes: a solar system, a 2D game, a spiral of 400 cubes, bouncing balls and a wave of cubes, each a short Python program](docs/images/gallery.gif)](https://johnwylie70.github.io/pyctures/)

**[See them running in your browser, with their code →](https://johnwylie70.github.io/pyctures/)** Nothing to install.

Pyctures ("Python pictures") gives Python the full set of JavaScript graphics functions: the web's 2D canvas for 2D, and three.js for 3D. Write a short Python program and it draws in your web browser: shapes, text, moving sprites, games, animations, live charts and lit 3D scenes. The names are the ones JavaScript uses, so any JavaScript graphics example can be brought across easily. Run a scene with your own Python while you write it, then build it into a folder that runs in any browser, on any website.

## Install

```bash
pip install pyctures
```

Python 3.9 or newer. Nothing else is installed.

## A first scene

Save this as `hello.py`:

```python
import math

def draw():
    ctx.fill_style = "midnightblue"
    ctx.fill_rect(0, 0, width, height)
    for i in range(12):
        ctx.fill_style = f"hsl({i * 30}, 80%, 60%)"
        ctx.begin_path()
        ctx.arc(width / 2 + 120 * math.cos(i / 1.91), height / 2 + 120 * math.sin(i / 1.91), 20, 0, math.tau)
        ctx.fill()
```

![What hello.py draws: twelve circles in a ring of rainbow colours on dark blue](docs/images/readme-hello.jpg)

`draw()` is called every frame, `ctx` is the 2D drawing surface, and `width` and `height` are the size of the canvas. There is nothing to import.

## Run it

```bash
pyctures run hello.py
```

Your browser opens on the scene. The program runs in your own Python, so numpy and anything else you have installed works. Save the file and the scene runs again. Errors are shown on the page with the line they happened on.

Options: `--port 9000`, `--no-browser`.

## A 3D scene, with a picture from a file

Put a picture beside your scene, here `textures/crate.png`, and wrap it round a cube:

```python
renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color(0x1b2430)
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(0, 1.2, 4)
controls = addons.OrbitControls(camera, canvas)

texture = THREE.TextureLoader().load("textures/crate.png")
texture.colorSpace = THREE.SRGBColorSpace
crate = THREE.Mesh(THREE.BoxGeometry(1.6, 1.6, 1.6), THREE.MeshStandardMaterial(map=texture))
scene.add(crate)

light = THREE.DirectionalLight(0xffffff, 2.5)
light.position.set(3, 4, 5)
scene.add(light)
scene.add(THREE.AmbientLight(0xffffff, 0.6))

def draw():
    crate.rotation.y += 0.008
    crate.rotation.x = 0.35
    controls.update()
    renderer.render(scene, camera)
```

![What textured_cube.py draws: a wooden crate, lit from above, turning](docs/images/readme-textured-cube.jpg)

`THREE` is three.js, ready to use, and `addons.OrbitControls` lets you drag to turn the scene. The picture is loaded by its path from the scene, and `pyctures build` takes it along. This is [`examples/textured_cube.py`](examples/textured_cube.py).

## Share it

```bash
pyctures build hello.py -o site/
```

`site/` is a folder of plain files that runs the scene entirely in the browser, with [Pyodide](https://pyodide.org) loaded from its official CDN. Put it on any static host. Every path in it is relative.

Or make one file:

```bash
pyctures build hello.py -o hello.html
```

`hello.html` holds the scene and everything it needs (three.js too, if the scene is 3D), so you can email it, put it on any website, or open it straight from your disk. Python still loads from Pyodide's CDN.

Either way, images the scene loads by a relative path, such as `load_image("textures/brick.png")` or `THREE.TextureLoader().load("textures/brick.png")`, are included automatically: copied into the folder, or packed into the one file. A named image that is missing is reported as a warning.

Python runs in a background thread of the browser (a Web Worker), and the page only draws. A slow frame or a stuck loop cannot hold up the page, so scenes play smoothly on phones and tablets too. Add `?measure=1` to the address to see the frame rate and where each frame's time goes.

## Use it on your website

Either put a built scene in an iframe:

```html
<iframe src="hello/index.html" style="width: 100%; aspect-ratio: 16 / 9; border: 0"></iframe>
```

or put scenes straight into your page, as many as you like:

```html
<div data-pyctures-src="balls.py"></div>
<div data-pyctures-src="knot.py" style="height: 420px"></div>
<script type="module" src="pyctures/pyctures.js"></script>
```

Each canvas fills its box, starts when it scrolls into view, and pauses when it is out of view or the tab is hidden. All the scenes on a page share one copy of Python, in a background thread. `pyctures build my-page/ -o site/` copies your page and adds the `pyctures/` folder. See [Use it on your website](docs/website.md), and the two-scene page in [`examples/website`](examples/website).

## Bringing a JavaScript example across

The calls are the same; a few things are written the Python way.

| JavaScript | Python |
|---|---|
| `new THREE.Mesh(g, m)` | `THREE.Mesh(g, m)` |
| `{ color: 0x44aaff, roughness: 0.4 }` | `color=0x44aaff, roughness=0.4` |
| `const x = 1;` `let y = 2;` | `x = 1` `y = 2` |
| `ctx.fillStyle = "red"` | the same, or `ctx.fill_style = "red"` |
| a `requestAnimationFrame` loop | `def draw():` and `def update(dt):` |
| `canvas.addEventListener("click", (e) => …)` | `canvas.add_event_listener("click", clicked)` with `def clicked(e):` |
| `const w = ctx.measureText("Hi").width` | `w = await ctx.measure_text("Hi").width` |
| `Math.PI` | `math.pi` |

```js
// JavaScript
const cube = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1),
                            new THREE.MeshStandardMaterial({ color: 0x44aaff }));
scene.add(cube);
function animate() {
  cube.rotation.y += 0.01;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
```

```python
# Python
cube = THREE.Mesh(THREE.BoxGeometry(1, 1, 1),
                  THREE.MeshStandardMaterial(color=0x44aaff))
scene.add(cube)

def draw():
    cube.rotation.y += 0.01
    renderer.render(scene, camera)
```

![What the whole example draws: a blue cube, lit, turning](docs/images/readme-from-javascript.jpg)

That is the heart of [`examples/from_javascript_3d.py`](examples/from_javascript_3d.py), which draws the cube above. The full guide, with a 2D and a 3D example side by side: [Bringing a JavaScript example across](docs/from-javascript.md).

## Examples

In [`examples/`](examples), each with a comment at the top saying what it shows. All of them run in the [online gallery](https://johnwylie70.github.io/pyctures/).

| File | What it is |
|---|---|
| `star_catcher.py` | A 2D game with sprites, a score and lives |
| `cube_dodge.py` | A 3D game: dodge the oncoming blocks |
| `lit_scene.py` | Shapes on a floor with a spotlight and shadows |
| `bouncing_balls.py` | A 2D animation with trails; click to add balls |
| `solar_system.py` | Planets, a moon and 2,000 stars in 3D |
| `live_chart.py` | A live line chart with a readout under the mouse |
| `textured_cube.py` | A picture from a file, wrapped round a cube |
| `cube_spiral.py`, `wave_grid.py`, `torus_knot.py` | 3D: a rainbow spiral of 400 cubes, a wave of 225 cubes, a lit knot |
| `starfield.py`, `spiral_garden.py` | 2D: fly through stars, dots on the golden angle |
| `type_and_measure.py` | Keyboard input, and reading a value back with `await` |
| `from_javascript_2d.py`, `from_javascript_3d.py` | JavaScript examples brought across |
| `website/` | A web page with two scenes on it |

```bash
pyctures run examples/star_catcher.py
pyctures run examples            # a list of them all
```

## Docs

Start with [Getting started](docs/getting-started.md), then [how a program is shaped](docs/program-shape.md), [drawing in 2D](docs/drawing-2d.md), [3D scenes](docs/3d.md), [colours](docs/colours.md), and [tips](docs/tips.md). The [2D functions](docs/2d-functions.md) and [3D functions](docs/3d-functions.md) pages list everything, one line each. Seven tutorials are in [docs/tutorials](docs/tutorials).


## Pyctures in Circuitry Studio

Pyctures comes from [Circuitry Studio](https://www.circuitry.dev), where Python scenes run in a code editor with a live preview beside the code, with a debugger and ready-made examples. It runs on phones, iPad, the web and desktop, and no subscription is needed to use it. Scenes written with this library run there unchanged, and the other way round.

![A 3D Pyctures scene running in Circuitry Studio on iPad, with the Python code beside its live preview](docs/images/circuitry-studio-ipad.jpg)

Its help pages: [Pyctures help](https://www.circuitry.dev/docs/pyctures) · [2D functions](https://www.circuitry.dev/docs/pyctures/2d-functions) · [3D functions](https://www.circuitry.dev/docs/pyctures/3d-functions) · [Colours](https://www.circuitry.dev/docs/pyctures/colours) · [Bringing a JavaScript example across](https://www.circuitry.dev/docs/pyctures/from-javascript)

## Licence

MIT. See [LICENSE](LICENSE). Pyctures includes three.js (MIT) and loads Pyodide (MPL 2.0) from its CDN; see [THIRD-PARTY-NOTICES](THIRD-PARTY-NOTICES).

Author: John Wylie
