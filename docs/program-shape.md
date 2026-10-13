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
| `vsync` | Another name for `frame`: `await vsync()`. |
| `keys`, `mouse` | What is pressed right now. |
| `pressed`, `released` | The keys that went down, and came up, since the last frame. |
| `touches`, `pinch` | Every finger that is down, and two fingers as a zoom. |
| `degrees` | An angle said in degrees: `ship.angle = degrees(90)`. |
| `background`, `circle`, `ellipse`, `rect`, `triangle`, `polygon`, `star`, `line`, `text`, `picture` | Plain drawing, one call each. See [the quick way](drawing-2d.md#the-quick-way-plain-functions). |
| `random`, `pick` | A number, or one thing from a list, by chance: `random(1, 6)`, `pick(["red", "gold"])`. |
| `Sprite`, `load_image` | Moving pictures that can tell when they touch, and loading an image. See [Sprites](drawing-2d.md#sprites). |
| `remove` | Takes a thing out of a list: `remove(rocks, rock)`. |
| `save`, `load` | Keep a value for the next time the program runs: `save("best", 120)`, `load("best", 0)`. See [Saved values](saved-values.md). |
| `save_text`, `load_text`, `save_json`, `load_json` | Write a file and read it back: `save_text("notes.txt", words)`, `load_json("level.json", {})`. See [Files and databases](files-and-databases.md). |
| `open_database` | A SQLite database: `db = open_database("scores")`, then `db.query(...)` and `db.run(...)`. |
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

`await vsync()` is another name for `await frame()`: the same function. Use whichever you prefer. Both wait for the screen's next refresh.

The page never shows a half-drawn frame. Everything you draw before the next `await frame()` or `await vsync()` appears together, at the next refresh. So clear the canvas and draw the new picture in the same frame, as the loop above does, and nothing flickers.

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

`mouse` has more to read:

| Name | What it is |
|---|---|
| `mouse.x`, `mouse.y` | Where the pointer is, in points from the top left of the scene. |
| `mouse.down` | `True` while a button or a finger is pressed. |
| `mouse.button` | Which button is down: `"left"`, `"middle"` or `"right"`. `None` when none is. A finger is `"left"`. |
| `mouse.inside` | `True` while the pointer is over the scene. |
| `mouse.dx`, `mouse.dy` | How far the pointer moved since the last frame. |
| `mouse.wheel` | How far the wheel turned since the last frame. Rolling down is positive. One click of a mouse wheel is about 100. |

A scene that uses the pointer gets the right button too: no menu opens over it.

`keys` also says which of the modifier keys are held, with no name to remember:

| Name | What it is |
|---|---|
| `keys.shift`, `keys.ctrl`, `keys.alt`, `keys.meta` | `True` while that key is held. `meta` is the Command key on a Mac and the Windows key on a PC. |
| `keys.codes` | The keys held, by their place on the keyboard: `"KeyW" in keys.codes`. See [Keys by their place](#keys-by-their-place-wasd-on-any-keyboard). |

`print(keys)` and `print(mouse)` show everything they hold, which helps when a key or a button does not do what you expect.

### Once for each press: `pressed` and `released`

`keys` says a key is down for as long as it is held. To do something once for each press, such as a jump or a shot, use `pressed`: the set of keys that went down since the last frame. `released` is the set of keys that came up.

| You want it to happen | Use |
|---|---|
| Once for each press | `" " in pressed` in `update`, or the function `on_key_down(key)` |
| While the key is held, every frame | `" " in keys` in `update` |
| While the key is held, at the speed a held key types | the function `on_key_repeat(key)` |

```python
y = 0      # how high the box is above the ground
vy = 0     # its speed upwards

def update(dt):
    global y, vy
    if " " in pressed and y == 0:
        vy = 500                      # one jump for each press of the space bar
    vy -= 1200 * dt
    y = max(0, y + vy * dt)

def draw():
    ctx.fill_style = "#1b2a3a"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "seagreen"
    ctx.fill_rect(0, height - 40, width, 40)
    ctx.fill_style = "gold"
    ctx.fill_rect(width / 2 - 20, height - 80 - y, 40, 40)
    ctx.fill_style = "white"
    ctx.fill_text("Press space to jump", 10, 20)
```

Hold the space bar down and the box jumps once. With `" " in keys` in its place it would jump again each time it landed.

`pressed`, `released`, `mouse.dx`, `mouse.dy` and `mouse.wheel` tell you what happened since the last frame. They are set at the start of each frame and stay the same all through it, so they read the same in `update`, in `draw` and after an `await frame()`.

### When something happens: the `on_` functions

Define any of these and they are called when the event happens:

| Function | Called when |
|---|---|
| `on_key_down(key, code)` | A key is pressed. `key` is its name, as in `keys`. `code` is its place on the keyboard. |
| `on_key_up(key, code)` | A key is let go. |
| `on_key_repeat(key, code)` | A key that is held down repeats, as it does when you type. |
| `on_mouse_down(x, y, button)` | The mouse button or a finger goes down. `button` is `"left"`, `"middle"` or `"right"`. |
| `on_mouse_move(x, y)` | The pointer moves. |
| `on_mouse_up(x, y, button)` | The button or finger comes up. |
| `on_touch_start(touch)` | A finger or a mouse button goes down. See [Every finger](#every-finger-touches). |
| `on_touch_move(touch)` | A finger that is down moves. |
| `on_touch_end(touch, cancelled)` | A finger comes up. |
| `on_wheel(amount)` | The wheel turns. Rolling down is positive. |
| `on_pinch(scale, change)` | Two fingers move together or apart. See [Zooming](#zooming-pinch-and-the-wheel). |
| `on_midi_note(note, velocity, channel)`, `on_midi_control(number, value, channel)` | A key of a MIDI keyboard goes down, or a knob moves, in a scene with `from synths import *`. See [MIDI](sound.md#midi). |

A function may leave out the arguments it does not need: `def on_key_down(key):` and `def on_mouse_down(x, y):` are fine.

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

Holding a key down does not repeat `on_key_down`. Use `keys` for things that should keep happening while a key is held, and `on_key_repeat` for a key that should repeat as it does in a text box, such as Backspace.

The `on_` functions are called just before `update`, with everything that happened since the last frame.

### Keys by their place: WASD on any keyboard

A key's name is the letter it types, and that depends on the keyboard. The key a British or American keyboard calls W types Z on a French one. A key's code is its place on the keyboard and is the same everywhere: `"KeyW"`, `"KeyA"`, `"KeyS"`, `"KeyD"`, `"Space"`, `"ArrowLeft"`, `"Digit1"`, `"ShiftLeft"`. `keys.codes` is the set of codes held, and `on_key_down` is given the code after the name.

```python
x, y = 200, 150

def update(dt):
    global x, y
    if "KeyW" in keys.codes: y -= 200 * dt
    if "KeyS" in keys.codes: y += 200 * dt
    if "KeyA" in keys.codes: x -= 200 * dt
    if "KeyD" in keys.codes: x += 200 * dt

def on_key_down(key, code):
    global x, y
    if code == "Space":
        x, y = width / 2, height / 2

def draw():
    ctx.fill_style = "#222"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "orange"
    ctx.fill_rect(x - 15, y - 15, 30, 30)
```

### Every finger: `touches`

`mouse` follows one pointer: the first finger to go down. `touches` is a list of every finger that is down right now. A pressed mouse button is in the list too, so one piece of code works on a phone and on a computer. Each touch has:

| Name | What it is |
|---|---|
| `touch.x`, `touch.y` | Where it is, in points, like `mouse.x`. |
| `touch.start_x`, `touch.start_y` | Where it went down. |
| `touch.dx`, `touch.dy` | How far it moved since the last frame. |
| `touch.id` | A number that tells it from the others. |
| `touch.type` | `"touch"` for a finger, `"mouse"` or `"pen"`. |

This scene paints with every finger at once, each in its own colour:

```python
colours = ["crimson", "royalblue", "seagreen", "orange", "purple"]
count = 0

ctx.fill_style = "white"
ctx.fill_rect(0, 0, width, height)

def on_touch_start(touch):
    global count
    touch.colour = colours[count % len(colours)]
    count += 1

def update(dt):
    ctx.line_width = 8
    ctx.line_cap = "round"
    for touch in touches:
        ctx.stroke_style = touch.colour
        ctx.begin_path()
        ctx.move_to(touch.x - touch.dx, touch.y - touch.dy)   # where it was last frame
        ctx.line_to(touch.x, touch.y)
        ctx.stroke()
```

A touch is the same object from the moment it goes down until it comes up, so a scene can keep things of its own on it, as `touch.colour` is kept here. `on_touch_end(touch, cancelled)` is given it one last time. `cancelled` is `True` when the device took the touch away, for example for a gesture of its own, so it should not count as a tap.

### Zooming: `pinch` and the wheel

Two fingers moving apart or together is a pinch. `pinch.scale` is 1 when the second finger goes down, 2 when the fingers are twice as far apart, and 0.5 when they are half as far. `pinch.change` is how much the scale changed since the last frame, so multiplying by it every frame is all a zoom needs. `pinch.x` and `pinch.y` are the point between the fingers. A pinch on a trackpad sets the same values.

```python
zoom = 1

def update(dt):
    global zoom
    zoom *= pinch.change            # two fingers, or a pinch on a trackpad
    zoom *= 0.999 ** mouse.wheel    # the mouse wheel: rolling up zooms in
    zoom = max(0.2, min(5, zoom))

def draw():
    ctx.fill_style = "#111"
    ctx.fill_rect(0, 0, width, height)
    size = 100 * zoom
    ctx.fill_style = "deepskyblue"
    ctx.fill_rect(width / 2 - size / 2, height / 2 - size / 2, size, size)
    ctx.fill_style = "white"
    ctx.fill_text("zoom %.2f" % zoom, 10, 20)
```

When no pinch is going on, `pinch.scale` and `pinch.change` are 1. `on_pinch(scale, change)` and `on_wheel(amount)` are called as it happens, if you would rather have a function.

A scene that names the wheel (`mouse.wheel` or `on_wheel`) keeps it: on a web page, the page does not scroll while the pointer is over the scene. Under any other scene the wheel scrolls the page as usual. In the same way, a scene that names `pinch` or `on_pinch` keeps a trackpad's pinch, and the page is not zoomed.

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
