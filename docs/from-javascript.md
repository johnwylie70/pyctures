# Bringing a JavaScript Example Across

Full reference: [www.circuitry.dev/docs/pyctures/from-javascript](https://www.circuitry.dev/docs/pyctures/from-javascript) (in Circuitry Studio's help)

Python drawing has the full set of JavaScript graphics functions: the web's 2D canvas for 2D, and three.js for 3D. The names are the same, so almost any JavaScript canvas or three.js example can be ported to Python by changing a handful of things. This page lists those changes and shows two examples ported side by side, first in JavaScript, then in Python.

## The changes to make

| In JavaScript | In Python |
|---|---|
| `new THREE.Mesh(g, m)` | `THREE.Mesh(g, m)`: drop `new`. A capitalised name makes something new. |
| `{ color: 0xff0000, roughness: 0.5 }` options | `color=0xff0000, roughness=0.5` keyword arguments |
| `const x = 1;`, `let y = 2;` | `x = 1`, `y = 2`: drop `const`, `let`, `var` and the semicolons |
| `ctx.fillStyle = "red"` | Stays as it is, or becomes `ctx.fill_style = "red"`; both work |
| `const ctx = canvas.getContext("2d")` | Not needed: `ctx` and `canvas` are ready |
| `function animate() { …; requestAnimationFrame(animate) }` | `def draw():` (and `def update(dt):` for movement): called every frame for you |
| `canvas.addEventListener("click", (e) => { … })` | `def clicked(e): …` then `canvas.add_event_listener("click", clicked)` |
| `const w = ctx.measureText("hi").width` (a value the page works out) | `w = await ctx.measure_text("hi").width` ([reading a value back](program-shape.md#reading-a-value-back-with-await)) |
| `Math.PI`, `Math.sin(a)`, `Math.random()` | `math.pi`, `math.sin(a)`, `random.random()`, after `import math, random` |
| `for (let i = 0; i < 10; i++)` | `for i in range(10):` |
| `true`, `false`, `null` | `True`, `False`, `None` |
| `a && b`, `a || b`, `!a` | `a and b`, `a or b`, `not a` |
| `{ … }` around blocks | Indentation, after a `:` |
| `window.innerWidth`, `canvas.width` | `width`, `height` (the canvas's size in points) |
| `renderer.setSize(window.innerWidth, window.innerHeight)` and a resize listener | `renderer.setSize(width, height, False)`; resizing is handled for you |
| `import * as THREE from "three"`, `import { OrbitControls } …` | Not needed: `THREE` is ready, and `addons.OrbitControls` |
| `document`, `Image`, `Path2D`, anything else on the page | `js.document`, `js.Image`, `js.Path2D` |

## A 2D canvas example

In JavaScript:

```js
const canvas = document.getElementById("c");
const ctx = canvas.getContext("2d");
let angle = 0;

function animate() {
  ctx.fillStyle = "#102030";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < 12; i++) {
    const a = angle + i * Math.PI / 6;
    ctx.fillStyle = "hsl(" + i * 30 + ", 80%, 60%)";
    ctx.beginPath();
    ctx.arc(200 + Math.cos(a) * 100, 150 + Math.sin(a) * 100, 15, 0, Math.PI * 2);
    ctx.fill();
  }
  angle += 0.02;
  requestAnimationFrame(animate);
}
animate();
```

In Python:

```python
import math

angle = 0

def draw():
    global angle
    ctx.fill_style = "#102030"
    ctx.fill_rect(0, 0, width, height)
    for i in range(12):
        a = angle + i * math.pi / 6
        ctx.fill_style = f"hsl({i * 30}, 80%, 60%)"
        ctx.begin_path()
        ctx.arc(200 + math.cos(a) * 100, 150 + math.sin(a) * 100, 15, 0, math.pi * 2)
        ctx.fill()
    angle += 0.02
```

What changed: no `getContext`, the `animate` loop became `draw()`, `let` and the semicolons went, the `for` became `range`, `Math` became `math`, and `global angle` lets `draw()` change `angle`. The calls themselves are the same, here in their snake_case spelling.

## A three.js example

In JavaScript:

```js
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(2, 2, 4);
const controls = new OrbitControls(camera, renderer.domElement);

const cube = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshStandardMaterial({ color: 0x44aaff, roughness: 0.4 })
);
scene.add(cube);
scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const light = new THREE.DirectionalLight(0xffffff, 2);
light.position.set(3, 4, 5);
scene.add(light);

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

renderer.setAnimationLoop(() => {
  cube.rotation.y += 0.01;
  controls.update();
  renderer.render(scene, camera);
});
```

In Python:

```python
renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)

scene = THREE.Scene()
camera = THREE.PerspectiveCamera(60, width / height, 0.1, 100)
camera.position.set(2, 2, 4)
controls = addons.OrbitControls(camera, canvas)

cube = THREE.Mesh(
    THREE.BoxGeometry(1, 1, 1),
    THREE.MeshStandardMaterial(color=0x44aaff, roughness=0.4),
)
scene.add(cube)
scene.add(THREE.AmbientLight(0xffffff, 0.4))
light = THREE.DirectionalLight(0xffffff, 2)
light.position.set(3, 4, 5)
scene.add(light)

def draw():
    cube.rotation.y += 0.01
    controls.update()
    renderer.render(scene, camera)
```

What changed: no imports, no `new`, the options object became keyword arguments, the renderer draws on the scene's `canvas` instead of adding a new one to the page, the resize listener is gone (Pyctures refits the renderer and camera itself), and the animation loop became `draw()`.

Both Python halves are in the `examples` folder to run as they are: `from_javascript_2d.py` and `from_javascript_3d.py` show the same changes on two more small programs, including a click handler and a value read back with `await`.

## Things that work differently

- **Values the page works out** need `await` to read in Python, and each read waits a frame. Keep your own numbers in Python where you can. A value you set from Python can be read back straight away.
- **Callbacks run a moment later.** A Python function passed to the page (an event listener) is called on the next frame, not inside the page's own code. That suits events. It does not suit functions three.js expects an answer from straight away, such as `traverse` or a custom sort; keep your objects in a Python list instead.
- **Libraries outside three.js and its orbit controls** are not loaded. Everything in the core of three.js is there.

## Related

- [2D functions](2d-functions.md)
- [3D functions](3d-functions.md)
- [How a program is shaped](program-shape.md)
