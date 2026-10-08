# Drawing in 2D

Full reference: [www.circuitry.dev/docs/pyctures/drawing](https://www.circuitry.dev/docs/pyctures/drawing) (in Circuitry Studio's help)

Everything 2D is drawn on the canvas through `ctx`, its 2D drawing surface. This page lists what it can do, grouped by job, with a short program for each group that you can paste into a Python file and run.

## The basics

- **Positions are in points**, measured from the **top-left corner**. `x` grows to the right and `y` grows **down**. The bottom-right corner is `(width, height)`.
- Drawing is sharp on every screen: the canvas takes care of high-resolution displays for you.
- **Angles are in radians.** A full turn is `math.tau` (about 6.283), half a turn is `math.pi`. `math.radians(90)` turns degrees into radians.
- **Colours** are text: a name (`"red"`, `"skyblue"`), a hex code (`"#ff8800"`), `"rgb(255, 136, 0)"`, `"rgba(255, 136, 0, 0.5)"` (the last number is opacity, 0 to 1), or `"hsl(30, 100%, 50%)"` (hue in degrees, then saturation and lightness).
- **Two spellings, one call.** Every name works in snake_case or in its standard form: `ctx.fill_rect(...)` is `ctx.fillRect(...)`, and `ctx.fill_style` is `ctx.fillStyle`. This guide uses snake_case from here on.
- The canvas's background is white in the light theme and near-black in the dark theme. Paint your own background first so your drawing looks the same in both.

## Rectangles

| Call | What it does |
|---|---|
| `ctx.fill_rect(x, y, w, h)` | A filled rectangle, top-left corner at `x, y` |
| `ctx.stroke_rect(x, y, w, h)` | The outline of a rectangle |
| `ctx.clear_rect(x, y, w, h)` | Erases that area back to the canvas's background |

```python
def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)

    ctx.fill_style = "steelblue"
    ctx.fill_rect(40, 40, 160, 100)

    ctx.stroke_style = "crimson"
    ctx.line_width = 6
    ctx.stroke_rect(240, 40, 160, 100)
```

## Paths: lines, circles and any shape

A path is a shape you build from pieces, then fill or outline. Start with `begin_path()`, add pieces, then call `fill()` or `stroke()` (or both).

| Call | What it adds |
|---|---|
| `ctx.begin_path()` | Starts a new, empty shape |
| `ctx.move_to(x, y)` | Lifts the pen and puts it down at `x, y` |
| `ctx.line_to(x, y)` | A straight line to `x, y` |
| `ctx.arc(x, y, r, start, end)` | Part of a circle around `x, y`. `0` to `math.tau` is a whole circle. Add `True` at the end to go anticlockwise. |
| `ctx.ellipse(x, y, rx, ry, rotation, start, end)` | Part of an oval |
| `ctx.rect(x, y, w, h)` | A rectangle, as part of the path |
| `ctx.round_rect(x, y, w, h, r)` | A rectangle with rounded corners of radius `r` |
| `ctx.quadratic_curve_to(cx, cy, x, y)` | A curve to `x, y`, pulled towards one control point |
| `ctx.bezier_curve_to(c1x, c1y, c2x, c2y, x, y)` | A curve with two control points |
| `ctx.close_path()` | A straight line back to the start of the shape |
| `ctx.fill()` | Fills the shape with `fill_style` |
| `ctx.stroke()` | Draws its outline with `stroke_style` and `line_width` |

```python
import math

def draw():
    ctx.fill_style = "#f4f1ea"
    ctx.fill_rect(0, 0, width, height)

    # a circle
    ctx.fill_style = "orange"
    ctx.begin_path()
    ctx.arc(100, 100, 50, 0, math.tau)
    ctx.fill()

    # a triangle, filled and outlined
    ctx.begin_path()
    ctx.move_to(200, 150)
    ctx.line_to(260, 50)
    ctx.line_to(320, 150)
    ctx.close_path()
    ctx.fill_style = "mediumseagreen"
    ctx.fill()
    ctx.stroke_style = "darkgreen"
    ctx.line_width = 4
    ctx.stroke()

    # a wave
    ctx.begin_path()
    ctx.move_to(20, 220)
    ctx.bezier_curve_to(120, 140, 220, 300, 340, 220)
    ctx.stroke_style = "royalblue"
    ctx.stroke()

    # a rounded button
    ctx.begin_path()
    ctx.round_rect(360, 60, 140, 60, 16)
    ctx.fill_style = "teal"
    ctx.fill()
```

## Colours, gradients, lines and transparency

| Setting | What it does |
|---|---|
| `ctx.fill_style = "red"` | The colour (or gradient) for fills and `fill_text` |
| `ctx.stroke_style = "blue"` | The colour (or gradient) for outlines |
| `ctx.line_width = 4` | Outline thickness, in points |
| `ctx.line_cap = "round"` | How line ends look: `"butt"`, `"round"` or `"square"` |
| `ctx.line_join = "round"` | How corners look: `"miter"`, `"round"` or `"bevel"` |
| `ctx.set_line_dash([10, 5])` | Dashed lines: 10 drawn, 5 gap. `[]` is solid again. |
| `ctx.global_alpha = 0.5` | Makes everything after it see-through: 0 invisible, 1 solid |
| `ctx.shadow_color`, `ctx.shadow_blur`, `ctx.shadow_offset_x`, `ctx.shadow_offset_y` | A soft shadow behind what you draw |
| `ctx.global_composite_operation = "lighter"` | How new drawing mixes with what is there (`"source-over"` is normal) |

A **gradient** is made once, given colour stops from 0 to 1, then used as a style:

| Call | Makes |
|---|---|
| `ctx.create_linear_gradient(x0, y0, x1, y1)` | A gradient along a line |
| `ctx.create_radial_gradient(x0, y0, r0, x1, y1, r1)` | A gradient between two circles |
| `gradient.add_color_stop(position, colour)` | A colour at a point along it |

```python
import math

sky = ctx.create_linear_gradient(0, 0, 0, 400)
sky.add_color_stop(0, "#1e3c72")
sky.add_color_stop(1, "#f7b267")

glow = ctx.create_radial_gradient(300, 120, 5, 300, 120, 60)
glow.add_color_stop(0, "white")
glow.add_color_stop(1, "rgba(255, 220, 120, 0)")

def draw():
    ctx.fill_style = sky
    ctx.fill_rect(0, 0, width, height)

    ctx.fill_style = glow
    ctx.fill_rect(220, 40, 160, 160)

    # see-through circles
    ctx.global_alpha = 0.6
    for i, colour in enumerate(["red", "lime", "blue"]):
        ctx.fill_style = colour
        ctx.begin_path()
        ctx.arc(100 + i * 40, 260, 50, 0, math.tau)
        ctx.fill()
    ctx.global_alpha = 1

    # a dashed, round-ended line
    ctx.stroke_style = "white"
    ctx.line_width = 6
    ctx.line_cap = "round"
    ctx.set_line_dash([12, 14])
    ctx.begin_path()
    ctx.move_to(20, 360)
    ctx.line_to(width - 20, 360)
    ctx.stroke()
    ctx.set_line_dash([])
```

## Text and fonts: drawing text on the canvas

| Call or setting | What it does |
|---|---|
| `ctx.font = "bold 24px sans-serif"` | Style, size and family, written the way web pages write fonts. Families that always work: `sans-serif`, `serif`, `monospace`, `system-ui`. |
| `ctx.fill_text(text, x, y)` | Draws filled text |
| `ctx.stroke_text(text, x, y)` | Draws the outline of the text |
| `ctx.text_align = "center"` | Where `x` is: `"left"`, `"center"` or `"right"` |
| `ctx.text_baseline = "middle"` | Where `y` is: `"alphabetic"` (the default, the line letters sit on), `"top"`, `"middle"` or `"bottom"` |
| `await ctx.measure_text(text).width` | How wide the text will be, in points (a read: see [Reading a value back](program-shape.md#reading-a-value-back-with-await)) |

Emoji are text too, so `ctx.fill_text("🚀", x, y)` draws a rocket.

```python
def draw():
    ctx.fill_style = "#202833"
    ctx.fill_rect(0, 0, width, height)

    ctx.fill_style = "white"
    ctx.font = "bold 40px sans-serif"
    ctx.text_align = "center"
    ctx.text_baseline = "middle"
    ctx.fill_text("Centred title", width / 2, 60)

    ctx.font = "20px monospace"
    ctx.text_align = "left"
    ctx.fill_style = "#9fe"
    for i, line in enumerate(["first line", "second line", "third line"]):
        ctx.fill_text(line, 30, 130 + i * 30)

    ctx.font = "64px sans-serif"
    ctx.fill_text("🌈 ⭐ 🚀", 30, 260)

    ctx.font = "bold 48px serif"
    ctx.stroke_style = "gold"
    ctx.line_width = 2
    ctx.stroke_text("Outline", 30, 340)
```

## Moving, turning and scaling: transforms

A transform moves the whole drawing grid, so the shapes after it are drawn in the moved grid. It is the easy way to rotate something around its own centre.

| Call | What it does |
|---|---|
| `ctx.translate(x, y)` | Moves the starting corner `(0, 0)` to `x, y` |
| `ctx.rotate(angle)` | Turns the grid around `(0, 0)`, by `angle` radians clockwise |
| `ctx.scale(sx, sy)` | Stretches the grid. `ctx.scale(2, 2)` draws everything twice as big. |
| `ctx.save()` | Remembers the current transform and every style setting |
| `ctx.restore()` | Goes back to what `save()` remembered |

Always pair `save()` with `restore()`, so one shape's transform does not leak into the next.

```python
import math

angle = 0

def update(dt):
    global angle
    angle += dt

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    for i in range(5):
        ctx.save()
        ctx.translate(80 + i * 110, height / 2)   # move to the square's centre
        ctx.rotate(angle * (i + 1) / 2)          # spin around it
        ctx.scale(1 + i * 0.2, 1 + i * 0.2)
        ctx.fill_style = f"hsl({i * 60}, 70%, 50%)"
        ctx.fill_rect(-20, -20, 40, 40)          # drawn around (0, 0)
        ctx.restore()
```

## Pictures

`load_image(address)` loads a picture from a web address or a `data:` address and gives you an image to draw. It draws once it has finished loading, so draw it in `draw()` and it appears as soon as it is ready.

| Call | What it does |
|---|---|
| `img = load_image("https://…/picture.png")` | Starts loading a picture |
| `img = load_image("cat.png")` | A picture beside your scene, by its path from the scene. `pyctures build` includes it. |
| `ctx.draw_image(img, x, y)` | Draws it at its own size, top-left at `x, y` |
| `ctx.draw_image(img, x, y, w, h)` | Draws it stretched to `w` by `h` |
| `ctx.draw_image(img, sx, sy, sw, sh, x, y, w, h)` | Draws one part of it (for sprite sheets) |
| `ctx.image_smoothing_enabled = False` | Keeps pixel art crisp when you scale it up |

This picture is made in Python as a small SVG drawing, so it needs no internet:

```python
from urllib.parse import quote

svg = """<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'>
<circle cx='32' cy='32' r='30' fill='gold'/>
<circle cx='22' cy='26' r='5' fill='black'/>
<circle cx='42' cy='26' r='5' fill='black'/>
<path d='M18 40 Q32 54 46 40' stroke='black' stroke-width='4' fill='none'/>
</svg>"""
smiley = load_image("data:image/svg+xml," + quote(svg))

def draw():
    ctx.fill_style = "#cde"
    ctx.fill_rect(0, 0, width, height)
    ctx.draw_image(smiley, 20, 20)
    ctx.draw_image(smiley, 120, 20, 160, 160)
```

## Sprites

A `Sprite` is a picture that moves. The picture can be an emoji or any short text, or an image from `load_image`. It draws itself centred on its `x, y`.

```python
rocket = Sprite("🚀", x=100, y=200, size=64)
```

| Part | What it is |
|---|---|
| `picture` | An emoji or text, or an image from `load_image` |
| `x`, `y` | Where its centre is |
| `vx`, `vy` | Its speed in points per second, used by `update(dt)` |
| `angle` | How far it is turned, in radians |
| `size` | How big it is, in points (48 unless you say) |
| `visible` | `False` hides it |
| `sprite.update(dt)` | Moves it by its speed: `x += vx * dt`, `y += vy * dt` |
| `sprite.draw()` | Draws it (call this in your `draw()`) |
| `sprite.touches(other)` | `True` when two sprites overlap |

```python
import math, random

fish = [Sprite("🐟", random.uniform(0, 400), random.uniform(40, 300), size=40) for _ in range(6)]
for f in fish:
    f.vx = random.uniform(40, 120)
shark = Sprite("🦈", 0, 200, size=72)
shark.vx = 60

def update(dt):
    for f in fish + [shark]:
        f.update(dt)
        if f.x > width + 40:
            f.x = -40
    for f in fish:
        f.visible = not f.touches(shark)
    shark.angle = math.sin(shark.x / 40) * 0.2

def draw():
    ctx.fill_style = "#0b4f6c"
    ctx.fill_rect(0, 0, width, height)
    for f in fish:
        f.draw()
    shark.draw()
```

The [simple game tutorial](tutorials/game.md) builds a whole game from sprites.

## Everything else

`ctx` is the standard 2D drawing surface, so any other operation it has works the same way, in either spelling: clipping (`ctx.clip()`), pixel access (`ctx.get_image_data`, `ctx.put_image_data`), filters (`ctx.filter = "blur(4px)"`) and the rest. Reading pixels back is a read, so it needs `await` and is slow; drawing is not.

## Related

- [How a program is shaped](program-shape.md)
- [Tutorial: your first drawing](tutorials/first-drawing.md)
- [3D scenes](3d.md)

← [How a program is shaped](program-shape.md) · [3D scenes](3d.md) →
