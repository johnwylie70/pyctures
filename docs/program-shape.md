# How a Program Is Shaped

Full reference: [www.circuitry.dev/docs/pyctures/program-shape](https://www.circuitry.dev/docs/pyctures/program-shape) (in Circuitry Studio's help)

A program for the canvas can take one of four shapes: draw once, draw every frame, loop, or draw step by step. This page shows each one, then how to read the keyboard, mouse and touch, and how to read a value back from the canvas.

## The names you can use

These are ready in every file, with no import:

| Name | What it is |
|---|---|
| `ctx` | The 2D drawing surface. See [Drawing in 2D](drawing-2d.md). |
| `canvas` | The canvas itself, for 3D and for event listeners. |
| `THREE` | The 3D toolkit. See [3D scenes](3d.md). |
| `addons` | Extra 3D tools: `addons.OrbitControls`. |
| `width`, `height` | The size of the canvas, in screen points. They update when the canvas is resized. |
| `pixel_ratio` | How many real pixels make one screen point (2 or 3 on most phones). |
| `frame`, `flush`, `sleep` | Used with `await` to wait for the next frame, send the drawing now, or pause. |
| `keys`, `mouse` | What is pressed right now. |
| `Sprite`, `load_image` | Moving pictures, and loading an image. |
| `Event` | The type of the event a callback receives. |
| `js` | Everything else the page has, for when you need it. |

## 1. Draw once

Write your drawing at the top level, with no functions. It runs once, top to bottom, and the program finishes.

```python
ctx.fill_style = "white"
ctx.fill_rect(0, 0, width, height)

for i in range(10):
    ctx.fill_style = f"hsl({i * 36}, 80%, 55%)"
    ctx.fill_rect(20 + i * 40, 40, 30, 120)
```

This is the simplest shape, good for trying things out. The drawing stays put when the canvas changes size, but it does not redraw to fit: for a picture that adapts to the canvas, or that moves, put the drawing in `draw()` (below), which redraws it every frame. Most examples in this guide do.

## 2. Draw every frame: `draw()` and `update(dt)`

Define a function called `draw` and it is called every frame, many times a second. Define `update(dt)` too and it is called just before each `draw()`, with `dt` the number of seconds since the last frame (about 0.016 at 60 frames a second).

Use `update` to move things and `draw` to paint them. Paint the background first in `draw()`: the canvas keeps what was drawn last frame until you cover it. Set the colours, font and line width in `draw()` too, next to what they style: a resize of the canvas resets them.

```python
x = 0

def update(dt):
    global x
    x = (x + 150 * dt) % width      # 150 points per second

def draw():
    ctx.fill_style = "#102030"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "tomato"
    ctx.fill_rect(x, height / 2 - 25, 50, 50)
```

Moving by `speed * dt` keeps the speed the same on a fast device and a slow one.

You can also define `setup()`. It is called once, after the top level has run and before the first frame. Code at the top level does the same job, so use whichever reads better.

A program with `draw()` or `update()` keeps running until you press Stop.

## 3. A loop with `await frame()`

If you prefer to write a loop, `await frame()` shows what you have drawn and waits for the next frame. Every pass of the loop is one frame.

```python
import math

t = 0
while True:
    ctx.fill_style = "black"
    ctx.fill_rect(0, 0, width, height)
    r = 60 + 40 * math.sin(t)
    ctx.fill_style = "hotpink"
    ctx.begin_path()
    ctx.arc(width / 2, height / 2, r, 0, math.tau)
    ctx.fill()
    t += 0.05
    await frame()
```

`await` works at the top level of the file, with no `async def` needed.

**Every `while True:` loop must `await frame()`** (or `await sleep(...)`). A loop that never waits never lets the canvas draw, and the program looks frozen. See [Tips and limits](tips.md).

`await sleep(seconds)` waits for that long, which is handy for slow, step-by-step programs:

```python
for word in ["3", "2", "1", "Go!"]:
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "black"
    ctx.font = "64px sans-serif"
    ctx.fill_text(word, 40, 100)
    await sleep(1)
```

## 4. Drawing step by step with `await flush()`

Without `draw()`, the canvas shows a top-level drawing when the program finishes. To watch it being built, call `await flush()`: it sends what has been drawn so far, now, and carries on.

```python
import math

ctx.fill_style = "#fffbe8"
ctx.fill_rect(0, 0, width, height)
cx, cy = width / 2, height / 2
for i in range(360):
    a = math.radians(i * 7)
    r = i * min(width, height) / 800
    ctx.fill_style = f"hsl({i}, 70%, 50%)"
    ctx.begin_path()
    ctx.arc(cx + math.cos(a) * r, cy + math.sin(a) * r, 4, 0, math.tau)
    ctx.fill()
    if i % 6 == 0:
        await flush()
```

Each `flush()` costs a frame, so flush every few steps rather than after every single shape.

## Keyboard, mouse and touch input

Your Python program can read keyboard input, the mouse and touch. Click or tap the canvas first so it has the keyboard.

### What is pressed right now: `keys` and `mouse`

`keys` is a set of the keys held down, by name: `"ArrowLeft"`, `"ArrowRight"`, `"ArrowUp"`, `"ArrowDown"`, `" "` (space), `"a"`, `"Enter"` and so on. `mouse.x` and `mouse.y` are where the pointer is, and `mouse.down` is `True` while the button or a finger is pressed. A finger on a touch screen counts as the mouse.

```python
x, y = 200, 150

def update(dt):
    global x, y
    if "ArrowLeft" in keys:  x -= 200 * dt
    if "ArrowRight" in keys: x += 200 * dt
    if "ArrowUp" in keys:    y -= 200 * dt
    if "ArrowDown" in keys:  y += 200 * dt
    if mouse.down:
        x, y = mouse.x, mouse.y

def draw():
    ctx.fill_style = "#222"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "lime"
    ctx.fill_rect(x - 15, y - 15, 30, 30)
```

### When something happens: the `on_` functions

Define any of these and they are called when the event happens:

| Function | Called when |
|---|---|
| `on_key_down(key)` | A key is pressed. `key` is its name, as in `keys`. |
| `on_key_up(key)` | A key is let go. |
| `on_mouse_down(x, y)` | The mouse button or a finger goes down. |
| `on_mouse_move(x, y)` | The pointer moves. |
| `on_mouse_up(x, y)` | The button or finger comes up. |

```python
dots = []

def on_mouse_down(x, y):
    dots.append((x, y))

def on_key_down(key):
    if key == "c":
        dots.clear()

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "crimson"
    for x, y in dots:
        ctx.begin_path()
        ctx.arc(x, y, 10, 0, 6.283)
        ctx.fill()
    ctx.fill_style = "gray"
    ctx.fill_text("Click to add dots, press c to clear", 10, 20)
```

Holding a key down does not repeat `on_key_down`. Use `keys` for things that should keep happening while a key is held.

### Callbacks

You can pass a Python function anywhere the canvas expects one. The function receives the event, and its fields read as attributes: `event.x`, `event.y`, `event.type`, `event.key`.

```python
def clicked(event):
    ctx.fill_style = "orange"
    ctx.fill_rect(event.x - 5, event.y - 5, 10, 10)

ctx.fill_style = "#eee"
ctx.fill_rect(0, 0, width, height)
canvas.add_event_listener("click", clicked)
```

A callback can be `async def`, so it can `await` a value (below).

## How calls work

The names above reach the canvas, and a few rules make them read like ordinary Python:

- **snake_case works.** `ctx.fill_rect` is `fillRect`, `ctx.fill_style` is `fillStyle`. The standard names work too, so `ctx.fillRect(...)` is the same call. This guide uses snake_case for 2D.
- **A capitalised name makes something new.** `THREE.Mesh(geometry, material)` creates a new mesh; you never write `new`.
- **Keyword arguments become an options object.** `THREE.MeshStandardMaterial(color="red", roughness=0.4)` passes `{color: "red", roughness: 0.4}`.
- **Python values travel as you would expect.** Numbers, strings, `True`/`False`/`None`, lists and dicts all work as arguments, and so do numbers from libraries such as numpy.
- **Changing a value in place works.** `mesh.rotation.y += 0.01` and `light.intensity *= 0.9` are worked out in the page, with no need to read the old value first.

## Reading a value back with `await`

Drawing only sends instructions to the canvas, which is why it is fast. Occasionally you need an answer back, such as the width of some text. Put `await` in front and you get the value:

```python
ctx.font = "40px sans-serif"
text_width = await ctx.measure_text("Hello there").width
print("The text is", text_width, "points wide")

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "black"
    ctx.font = "40px sans-serif"
    ctx.fill_text("Hello there", (width - text_width) / 2, height / 2)
```

Things to know:

- **Every read waits a frame**, so a program that reads every frame runs at half speed or less. Read rarely: once at the start, or when the user clicks.
- **Keep your own numbers in Python.** Rather than reading `mesh.position.x` back, keep `x` in a Python variable, change it, and set `mesh.position.x = x`. A value you set from Python is remembered, so reading it back needs no `await`.
- **Using a canvas value as if it were a Python number** (`if mesh.position.x > 3:`) stops with an error that says to read it with `await`.
- To `await` inside a function, make it `async def`. `draw`, `update` and callbacks can all be async.

## Related

- [Drawing in 2D](drawing-2d.md)
- [3D scenes](3d.md)
- [Tips and limits](tips.md)

← [Pyctures](getting-started.md) · [Drawing in 2D](drawing-2d.md) →
