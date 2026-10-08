# Colours

Full reference: [www.circuitry.dev/docs/pyctures/colours](https://www.circuitry.dev/docs/pyctures/colours) (in Circuitry Studio's help)

Every way to write a colour in a Python drawing, in 2D and in 3D: colour names, hex codes, rgb, hsl, see-through colours, gradients and patterns. Each one has a short program you can paste into a Python file and run.

In 2D a colour is a piece of text that you give to `ctx.fill_style` or `ctx.stroke_style`. The same text works in 3D too, along with a few extra forms shown at the end.

## Colour names

The easiest way: just say the colour. There are about 140 names, from the plain (`"red"`, `"blue"`, `"black"`) to the fancy (`"tomato"`, `"orchid"`, `"papayawhip"`, `"cornflowerblue"`). Capital letters don't matter.

```swatches
names tomato gold mediumseagreen deepskyblue orchid slategray papayawhip cornflowerblue crimson darkorange khaki teal navy hotpink sienna lavender
```

```python
names = ["tomato", "gold", "mediumseagreen", "deepskyblue", "orchid", "slategray", "papayawhip", "cornflowerblue"]

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.font = "16px sans-serif"
    for i, name in enumerate(names):
        ctx.fill_style = name
        ctx.fill_rect(20, 20 + i * 40, 60, 30)
        ctx.fill_style = "black"
        ctx.fill_text(name, 95, 41 + i * 40)
```

`"transparent"` is a colour too: it draws nothing.

## Hex codes: #rrggbb

A hex code mixes red, green and blue light. It is a `#` and then three pairs of digits, one pair each for red, green and blue. Each pair goes from `00` (none) to `ff` (all), counting in hexadecimal: `0 1 2 3 4 5 6 7 8 9 a b c d e f`.

| Code | Colour |
|---|---|
| `"#ff0000"` | All red, no green, no blue: red |
| `"#00ff00"` | Green |
| `"#0000ff"` | Blue |
| `"#ffff00"` | Red and green light together make yellow |
| `"#ffffff"` | All three at full: white |
| `"#000000"` | None at all: black |
| `"#808080"` | All three at half: grey |
| `"#ff6347"` | Tomato |

There are two more forms:

- **Short hex**, `"#f63"`: one digit per colour, each doubled, so `"#f63"` is `"#ff6633"`.
- **Hex with see-through**, `"#ff634780"`: a fourth pair says how solid the colour is, from `00` (invisible) to `ff` (solid). `80` is about half. The short form has one too: `"#f638"`.

```python
def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "#ff6347"        # tomato
    ctx.fill_rect(20, 20, 120, 120)
    ctx.fill_style = "#f63"           # short form of #ff6633
    ctx.fill_rect(160, 20, 120, 120)
    ctx.fill_style = "#3366ff80"      # blue at about half strength, over the others
    ctx.fill_rect(80, 80, 160, 120)
```

Many design tools show colours as hex codes, so this is how you copy a colour you have seen somewhere else.

## rgb() and rgba()

The same red, green and blue mix written with ordinary numbers from 0 to 255:

- `"rgb(255, 99, 71)"` is tomato (the same as `"#ff6347"`).
- `"rgba(255, 99, 71, 0.5)"` adds a fourth number, the **alpha**: how solid it is, from 0 (invisible) to 1 (solid).

Because these are numbers, they are easy to work out in Python with an f-string:

```python
def draw():
    ctx.fill_style = "black"
    ctx.fill_rect(0, 0, width, height)
    # from black to full red, in 16 steps
    for i in range(16):
        red = i * 17                  # 0, 17, 34 ... 255
        ctx.fill_style = f"rgb({red}, 0, 0)"
        ctx.fill_rect(10 + i * 30, 20, 28, 80)
    # see-through white, getting more solid
    for i in range(10):
        ctx.fill_style = f"rgba(255, 255, 255, {i / 10})"
        ctx.fill_rect(10 + i * 48, 130, 44, 80)
```

## hsl(): colours by hue, saturation and lightness

`hsl` describes a colour the way people talk about it: **which colour** it is, **how vivid** it is, and **how light** it is. That makes it the most useful colour form in code.

`"hsl(hue, saturation%, lightness%)"`

### Hue: an angle round the colour wheel

Picture the colours of the rainbow bent into a circle. The **hue** is how far round the circle you go, in degrees:

| Hue | Colour |
|---|---|
| 0 | Red |
| 30 | Orange |
| 60 | Yellow |
| 120 | Green |
| 180 | Cyan |
| 240 | Blue |
| 300 | Magenta |
| 360 | Back to red |

Numbers past 360 carry on round the wheel, so 400 is the same as 40.

These are the hues at every 30 degrees, at full strength:

```swatches
hue
```

### Saturation: how vivid

`100%` is the strongest colour; `50%` is softer; `0%` is no colour at all, just grey. Here is hue 200 from 0% to 100%:

```swatches
saturation
```

### Lightness: how light

`0%` is always black and `100%` always white, whatever the hue. `50%` is the full colour. Below 50% is darker, above it paler. Hue 200 from 0% to 100%:

```swatches
lightness
```

### Alpha with hsla()

`"hsla(200, 80%, 50%, 0.5)"` adds alpha, as rgba does: 0 is invisible, 1 is solid. Over a checkerboard, from 0 to 1:

```swatches
alpha
```

### Try it

Move the sliders, then copy the line into your program.

```swatches
picker
```

```python
def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.font = "13px sans-serif"
    # hue: round the colour wheel
    for i in range(12):
        ctx.fill_style = f"hsl({i * 30}, 90%, 50%)"
        ctx.fill_rect(10 + i * 36, 30, 32, 50)
    ctx.fill_style = "black"
    ctx.fill_text("hue 0 to 330", 10, 20)
    # saturation: grey to vivid
    for i in range(11):
        ctx.fill_style = f"hsl(200, {i * 10}%, 50%)"
        ctx.fill_rect(10 + i * 36, 115, 32, 50)
    ctx.fill_style = "black"
    ctx.fill_text("saturation 0% to 100%", 10, 105)
    # lightness: black to white
    for i in range(11):
        ctx.fill_style = f"hsl(200, 90%, {i * 10}%)"
        ctx.fill_rect(10 + i * 36, 200, 32, 50)
    ctx.fill_style = "black"
    ctx.fill_text("lightness 0% to 100%", 10, 190)
```

### Why hsl is handy in code

**A rainbow is one loop.** Step the hue and keep the rest the same:

```python
import math

def draw():
    ctx.fill_style = "black"
    ctx.fill_rect(0, 0, width, height)
    for i in range(36):
        ctx.fill_style = f"hsl({i * 10}, 85%, 55%)"
        ctx.begin_path()
        ctx.arc(width / 2, height / 2, 150 - i * 4, 0, math.tau)
        ctx.fill()
```

**Animating colour is changing one number.** Make the hue grow over time and the colour cycles round the wheel; change the lightness and it fades.

```python
t = 0

def update(dt):
    global t
    t += dt

def draw():
    hue = t * 60                         # once round the wheel every 6 seconds
    ctx.fill_style = f"hsl({hue}, 80%, 60%)"
    ctx.fill_rect(0, 0, width / 2, height)
    light = 50 + 40 * abs((t % 2) - 1)   # glides between 50% and 90%
    ctx.fill_style = f"hsl(30, 90%, {light}%)"
    ctx.fill_rect(width / 2, 0, width / 2, height)
```

**A colour that matches its value.** In a chart or a game, `f"hsl({120 * health}, 80%, 50%)"` goes from green (healthy, 1) through yellow to red (0).

## Making things see-through

There are two ways, and they mix:

- **Alpha in the colour**: `"rgba(…, 0.5)"`, `"hsla(…, 0.5)"` or `"#rrggbb80"`. Only that one colour is see-through.
- **`ctx.global_alpha = 0.5`**: everything drawn after it is see-through, whatever its colour, including pictures and text. Set it back to `1` when you are done, or wrap it in `ctx.save()` and `ctx.restore()`.

When both are used, they multiply: half-see-through colour with `global_alpha = 0.5` shows at a quarter.

```python
import math

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    # alpha in the colour
    for i, hue in enumerate([0, 120, 240]):
        ctx.fill_style = f"hsla({hue}, 90%, 50%, 0.5)"
        ctx.begin_path()
        ctx.arc(110 + i * 50, 110, 70, 0, math.tau)
        ctx.fill()
    # global_alpha: solid colours, drawn see-through
    ctx.save()
    ctx.global_alpha = 0.4
    ctx.fill_style = "navy"
    ctx.fill_rect(320, 40, 140, 140)
    ctx.font = "bold 40px sans-serif"
    ctx.fill_text("faded", 320, 240)
    ctx.restore()
```

## Gradients and patterns

A fill or stroke style can be more than one colour.

**Gradients** blend between colours. Make one, add colour stops (positions from 0 to 1), then use it as a style:

| Call | Blends |
|---|---|
| `ctx.create_linear_gradient(x0, y0, x1, y1)` | Along a line |
| `ctx.create_radial_gradient(x0, y0, r0, x1, y1, r1)` | Outwards from one circle to another |
| `ctx.create_conic_gradient(angle, x, y)` | Round a centre, like a colour wheel |
| `gradient.add_color_stop(position, colour)` | Puts a colour at a point along it; any colour form works |

**Patterns** repeat a picture, or another canvas you drew on: `ctx.create_pattern(picture, "repeat")`. The second word can be `"repeat"`, `"repeat-x"`, `"repeat-y"` or `"no-repeat"`.

```python
# a linear gradient: sunset
sky = ctx.create_linear_gradient(0, 0, 0, 300)
sky.add_color_stop(0, "hsl(230, 60%, 25%)")
sky.add_color_stop(0.6, "hsl(330, 70%, 60%)")
sky.add_color_stop(1, "hsl(40, 100%, 70%)")

# a conic gradient: a colour wheel
wheel = ctx.create_conic_gradient(0, 380, 150)
for i in range(7):
    wheel.add_color_stop(i / 6, f"hsl({i * 60}, 100%, 50%)")

# a pattern from a small canvas we draw a check on
tile = js.document.create_element("canvas")
tile.width = 20
tile.height = 20
t = tile.get_context("2d")
t.fill_style = "white"
t.fill_rect(0, 0, 20, 20)
t.fill_style = "lightgray"
t.fill_rect(0, 0, 10, 10)
t.fill_rect(10, 10, 10, 10)
checks = ctx.create_pattern(tile, "repeat")

def draw():
    ctx.fill_style = checks
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = sky
    ctx.fill_rect(20, 20, 240, 260)
    ctx.fill_style = wheel
    ctx.begin_path()
    ctx.arc(380, 150, 90, 0, 6.283)
    ctx.fill()
```

## Colours in 3D

Materials, lights and the background take colours too. Every text form above works, and 3D adds a few of its own.

| Form | Example | Notes |
|---|---|---|
| Text | `color="tomato"`, `color="#ff6347"`, `color="hsl(200, 80%, 50%)"` | Any colour text from this page, without alpha |
| Hex number | `color=0xff6347` | The same six digits as a hex code, written as a Python number with `0x` in front |
| A colour object | `THREE.Color("tomato")`, `THREE.Color(0xff6347)` | For `scene.background`, or to keep and change |
| Red, green, blue from 0 to 1 | `THREE.Color(1, 0.4, 0.3)` | Note: 0 to 1, not 0 to 255 |

To change a colour that is already there, use the colour's own methods:

| Call | What it does |
|---|---|
| `mesh.material.color.set("gold")` | Any colour form |
| `mesh.material.color.setHSL(h, s, l)` | **Hue, saturation and lightness all from 0 to 1** here, not degrees and percent. Hue 0.33 is green, 0.66 is blue. |
| `mesh.material.color.setRGB(r, g, b)` | Each from 0 to 1 |

Materials have a few colour settings of their own:

- `color`: the surface colour that light falls on.
- `emissive`: a colour the surface gives off by itself, as if it glows. It shows even in the dark. `emissiveIntensity` makes it stronger.
- `opacity` with `transparent=True`: see-through, from 0 to 1. Opacity does nothing unless `transparent` is on.
- `scene.background = THREE.Color("…")`: the colour behind everything.

```python
import math

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color("hsl(220, 30%, 12%)")
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(0, 0, 9)
scene.add(THREE.AmbientLight("white", 0.4))
sun = THREE.DirectionalLight("white", 2)
sun.position.set(2, 4, 5)
scene.add(sun)

balls = []
for i in range(5):
    material = THREE.MeshStandardMaterial(color=0xff6347, roughness=0.4)
    ball = THREE.Mesh(THREE.SphereGeometry(0.6, 32, 16), material)
    ball.position.x = (i - 2) * 1.5
    ball.position.y = 1
    scene.add(ball)
    balls.append(ball)

glow = THREE.Mesh(THREE.TorusGeometry(0.6, 0.2, 16, 48),
                  THREE.MeshStandardMaterial(color="black", emissive="orange", emissiveIntensity=1.5))
glow.position.set(-2, -1.4, 0)
scene.add(glow)

glass = THREE.Mesh(THREE.BoxGeometry(1.4, 1.4, 1.4),
                   THREE.MeshStandardMaterial(color="deepskyblue", transparent=True, opacity=0.4))
glass.position.set(2, -1.4, 0)
scene.add(glass)

t = 0

def update(dt):
    global t
    t += dt
    for i, ball in enumerate(balls):
        # setHSL takes 0 to 1: each ball a different hue, all drifting round the wheel
        ball.material.color.setHSL((t * 0.1 + i / 5) % 1, 0.8, 0.5)
    glass.rotation.y += dt

def draw():
    renderer.render(scene, camera)
```

## Related

- [2D functions](2d-functions.md): every drawing call and setting
- [3D functions](3d-functions.md): materials, lights and everything else in 3D
- [Drawing in 2D](drawing-2d.md)
