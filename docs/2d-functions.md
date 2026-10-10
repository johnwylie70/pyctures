# 2D Functions

Full reference: [www.circuitry.dev/docs/pyctures/2d-functions](https://www.circuitry.dev/docs/pyctures/2d-functions) (in Circuitry Studio's help)

Every function and setting of the 2D drawing surface, `ctx`, grouped by job, one line each. Each entry shows the Python spelling first and the standard name after it; both work, so `ctx.fill_rect(…)` and `ctx.fillRect(…)` are the same call. After each group there is a short program you can run, with a picture of what it draws.

New to drawing? Start with [Drawing in 2D](drawing-2d.md), which explains the ideas, and come back here to look things up. Colours have a page of their own: [Colours](colours.md).

**A note on `await`.** Almost every call here just draws, and returns straight away. A few give you an answer back (a width, a yes or no, some pixels). Those are marked **(await)**: put `await` in front to get the value, as in `w = await ctx.measure_text("hi").width`. Each one waits a frame, so use them now and then rather than every frame. See [reading a value back](program-shape.md#reading-a-value-back-with-await).

## Plain drawing

Functions for a first picture, one call each, with no `ctx.` in front ([the quick way](drawing-2d.md#the-quick-way-plain-functions)). A colour that is left out is the one already in use; one that is given stays for what is drawn next.

| Call | What it draws |
|---|---|
| `background(colour)` | Paints the whole canvas. It leaves the colour in use as it was. With no colour it wipes the canvas clear |
| `circle(x, y, radius, colour)` | A filled circle centred on `x, y` |
| `ellipse(x, y, width, height, colour)` | An oval centred on `x, y` |
| `rect(x, y, width, height, colour)` | A filled rectangle, top-left corner at `x, y`. `round=12` rounds its corners |
| `triangle(x1, y1, x2, y2, x3, y3, colour)` | A triangle, by its three corners |
| `polygon(x, y, radius, sides, colour)` | A shape with that many equal sides, centred on `x, y`, one corner straight up |
| `star(x, y, radius, points, colour)` | A star with that many points, one straight up. Its inner corners are 0.4 of the radius out; `inner=0.6` changes that |
| `line(x1, y1, x2, y2, colour, thickness)` | A straight line |
| `text(words, x, y, colour, size, align)` | Words, `size` points high. `align` is `"left"` (as it starts), `"right"` or `"centre"`; with `"centre"`, `x, y` is the middle of the words |
| `picture(what, x, y, size)` | An emoji or a word, an image file beside the program, or a loaded image, centred on `x, y` and `size` high (48 unless you say). A file draws once it has loaded |

Every shape (`circle`, `ellipse`, `rect`, `triangle`, `polygon`, `star`) takes `outline="white", thickness=3` last. With a colour it is a filled shape with a border; without a colour it is the edge alone. The outline's colour and thickness stay for the next outline.

| Call | What it gives |
|---|---|
| `random(min, max)` | A whole number from `min` to `max`, either end included. If an end has a fraction, any number between them |
| `random(max)`, `random()` | From 0 to `max`; with nothing, a fraction from 0 up to 1 |
| `pick(list)` | One thing from a list, by chance |
| `degrees(n)` | An angle said in degrees, wherever an angle is wanted: `ctx.rotate(degrees(45))`, `ship.angle = degrees(90)`. Everything else here counts angles in radians |

Everything below is `ctx`, which does all of this and much more.

## Size and helpers

These come ready to use, as well as `ctx`:

| Name | What it is |
|---|---|
| `width`, `height` | The size of the canvas, in points. They change when the canvas is resized. |
| `pixel_ratio` | Real pixels per point (2 or 3 on most phones). Needed only for pixel and hit-test calls below. |
| `canvas` | The canvas, for `canvas.add_event_listener(...)` |
| `await frame()` | Shows this frame and waits for the next |
| `await flush()` | Shows what is drawn so far, now, and carries on |
| `await sleep(seconds)` | Waits that long |
| `keys` | The set of keys held down: `"ArrowLeft" in keys`. Also `keys.shift`, `keys.ctrl`, `keys.alt`, `keys.meta`, and `keys.codes` (keys by their place: `"KeyW"`) |
| `pressed`, `released` | The keys that went down, and came up, since the last frame: `" " in pressed` |
| `mouse.x`, `mouse.y`, `mouse.down` | Where the pointer or finger is, and whether it is pressed |
| `mouse.button`, `mouse.inside` | Which button is down (`"left"`, `"middle"`, `"right"` or `None`), and whether the pointer is over the scene |
| `mouse.dx`, `mouse.dy`, `mouse.wheel` | How far the pointer moved, and the wheel turned, since the last frame |
| `touches` | Every finger (or pressed mouse button) that is down: each has `id`, `x`, `y`, `start_x`, `start_y`, `dx`, `dy`, `type` |
| `pinch.scale`, `pinch.change`, `pinch.x`, `pinch.y` | Two fingers as a zoom: the scale since the pinch began, its change since the last frame, and its middle |
| `load_image(address)` | Loads a picture to draw ([Images](#images)) |
| `save(name, value)`, `load(name, otherwise)` | Keep a value for the next time the program runs, and get it back: a number, text, `True` or `False`, a list or a dictionary ([Saved values](saved-values.md)) |
| `Sprite(picture, x, y, size=48)` | A moving picture with `x`, `y`, `vx`, `vy`, `angle`, `spin`, `size`, `visible`, `update(dt)` and `draw()`. The picture is an emoji, an image, or a function that draws it, given the sprite's size ([Sprites](drawing-2d.md#sprites)) |
| `Sprite.box(x, y, width, height, colour)`, `Sprite.circle(x, y, size, colour)` | A plain coloured box or circle, hit-tested as the shape you see |
| `sprite.touches(other)`, `sprite.hit(sprites)`, `sprite.contains(x, y)` | Do two sprites overlap; the first sprite in a list that it touches, or `None`; is a point on it. A sprite's `shape` is `"circle"` or `"box"` ([Sprites that touch](drawing-2d.md#sprites-that-touch)) |
| `sprite.wrap()`, `sprite.bounce()`, `sprite.offscreen()` | Come back on the opposite edge; bounce off the edges, or the ones named; is all of it outside the picture |
| `sprite.push(amount)`, `sprite.forward(distance)`, `sprite.limit(speed)` | Speed up the way it faces; step the way it faces; never faster than this |
| `sprite.angle_to(other)`, `sprite.distance_to(other)` | The angle and the distance to another sprite, to `mouse`, or to a point `(x, y)` |
| `remove(things, thing)` | Take a thing out of a list. Loop over a copy while removing: `for rock in rocks[:]:` |
| `js` | Everything else the page has, such as `js.Path2D` and `js.document` |

## Rectangles

| Python | Standard | What it does |
|---|---|---|
| `ctx.fill_rect(x, y, w, h)` | `fillRect` | A filled rectangle, top-left corner at `x, y` |
| `ctx.stroke_rect(x, y, w, h)` | `strokeRect` | The outline of a rectangle |
| `ctx.clear_rect(x, y, w, h)` | `clearRect` | Rubs that area out, back to see-through |

## Paths

A path is a shape you build from pieces and then fill, outline, or cut with.

| Python | Standard | What it does |
|---|---|---|
| `ctx.begin_path()` | `beginPath` | Starts a new, empty path. Forgetting it joins your new shape to the last one. |
| `ctx.move_to(x, y)` | `moveTo` | Lifts the pen and puts it down at `x, y` |
| `ctx.line_to(x, y)` | `lineTo` | A straight line to `x, y` |
| `ctx.close_path()` | `closePath` | A straight line back to where this piece started |
| `ctx.rect(x, y, w, h)` | `rect` | A rectangle, as part of the path |
| `ctx.round_rect(x, y, w, h, r)` | `roundRect` | A rounded rectangle. `r` can be one radius or a list of up to four, one per corner. |
| `ctx.arc(x, y, r, start, end)` | `arc` | Part of a circle round `x, y`, from angle `start` to `end` in radians (`0` to `math.tau` is all of it). Add `True` to go anticlockwise. |
| `ctx.arc_to(x1, y1, x2, y2, r)` | `arcTo` | A rounded corner of radius `r`, turning at `x1, y1` towards `x2, y2` |
| `ctx.ellipse(x, y, rx, ry, turn, start, end)` | `ellipse` | Part of an oval, `rx` wide and `ry` tall, turned by `turn` radians |
| `ctx.quadratic_curve_to(cx, cy, x, y)` | `quadraticCurveTo` | A curve to `x, y`, pulled towards one control point |
| `ctx.bezier_curve_to(c1x, c1y, c2x, c2y, x, y)` | `bezierCurveTo` | A curve to `x, y` with two control points |
| `ctx.fill()` | `fill` | Fills the path. `ctx.fill("evenodd")` leaves holes where shapes overlap. |
| `ctx.stroke()` | `stroke` | Draws the path's outline |

```python
import math

def draw():
    ctx.fill_style = "#f6f3ec"
    ctx.fill_rect(0, 0, width, height)
    ctx.line_width = 4
    ctx.stroke_style = "#333"

    ctx.fill_style = "tomato"
    ctx.fill_rect(20, 20, 100, 70)              # fill_rect
    ctx.stroke_rect(140, 20, 100, 70)           # stroke_rect

    ctx.begin_path()                            # round_rect, different corners
    ctx.round_rect(260, 20, 100, 70, [30, 4, 30, 4])
    ctx.fill_style = "gold"
    ctx.fill()
    ctx.stroke()

    ctx.begin_path()                            # arc: three-quarters of a circle
    ctx.move_to(70, 165)
    ctx.arc(70, 165, 50, 0, math.tau * 0.75)
    ctx.close_path()
    ctx.fill_style = "mediumseagreen"
    ctx.fill()

    ctx.begin_path()                            # ellipse, turned
    ctx.ellipse(190, 165, 60, 30, math.radians(20), 0, math.tau)
    ctx.fill_style = "deepskyblue"
    ctx.fill()

    ctx.begin_path()                            # arc_to: a rounded corner
    ctx.move_to(260, 120)
    ctx.arc_to(360, 120, 360, 220, 40)
    ctx.line_to(360, 220)
    ctx.stroke()

    ctx.begin_path()                            # quadratic and bezier curves
    ctx.move_to(20, 290)
    ctx.quadratic_curve_to(110, 220, 200, 290)
    ctx.bezier_curve_to(240, 220, 320, 360, 380, 270)
    ctx.stroke_style = "orchid"
    ctx.stroke()
```


## Colours and styles

| Python | Standard | What it does |
|---|---|---|
| `ctx.fill_style = …` | `fillStyle` | The colour, gradient or pattern for fills and filled text |
| `ctx.stroke_style = …` | `strokeStyle` | The same, for outlines |
| `ctx.global_alpha = 0.5` | `globalAlpha` | How solid everything drawn next is, from 0 (invisible) to 1 |
| `ctx.create_linear_gradient(x0, y0, x1, y1)` | `createLinearGradient` | A gradient along a line |
| `ctx.create_radial_gradient(x0, y0, r0, x1, y1, r1)` | `createRadialGradient` | A gradient between two circles |
| `ctx.create_conic_gradient(angle, x, y)` | `createConicGradient` | A gradient round a point, like a colour wheel |
| `gradient.add_color_stop(position, colour)` | `addColorStop` | A colour at a point (0 to 1) along a gradient |
| `ctx.create_pattern(picture, "repeat")` | `createPattern` | A repeating fill from a picture or another canvas. Also `"repeat-x"`, `"repeat-y"`, `"no-repeat"`. |

Every colour form, with examples of gradients and patterns, is on the [Colours](colours.md) page.

## Lines

| Python | Standard | What it does |
|---|---|---|
| `ctx.line_width = 4` | `lineWidth` | How thick outlines are, in points |
| `ctx.line_cap = "round"` | `lineCap` | How line ends look: `"butt"` (flat, stops at the end), `"round"`, `"square"` (flat, sticks out by half the width) |
| `ctx.line_join = "round"` | `lineJoin` | How corners look: `"miter"` (sharp), `"round"`, `"bevel"` (cut off) |
| `ctx.miter_limit = 10` | `miterLimit` | How far a sharp corner may stick out before it is cut off like a bevel |
| `ctx.set_line_dash([10, 5])` | `setLineDash` | Dashes: 10 drawn, 5 gap. Longer lists make patterns. `[]` is solid. |
| `await ctx.get_line_dash()` | `getLineDash` | **(await)** The current dash list |
| `ctx.line_dash_offset = 4` | `lineDashOffset` | Slides the dashes along. Change it each frame for "marching ants". |

```python
t = 0

def update(dt):
    global t
    t += dt

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "#333"
    ctx.font = "14px sans-serif"

    # line_cap: the thin line shows where each line really ends
    for i, cap in enumerate(["butt", "round", "square"]):
        y = 30 + i * 40
        ctx.line_width = 18
        ctx.line_cap = cap
        ctx.stroke_style = "steelblue"
        ctx.begin_path(); ctx.move_to(40, y); ctx.line_to(200, y); ctx.stroke()
        ctx.fill_text(cap, 225, y + 5)
    ctx.line_cap = "butt"
    ctx.line_width = 1
    ctx.stroke_style = "red"
    ctx.begin_path(); ctx.move_to(40, 10); ctx.line_to(40, 125)
    ctx.move_to(200, 10); ctx.line_to(200, 125); ctx.stroke()

    # line_join
    for i, join in enumerate(["miter", "round", "bevel"]):
        x = 40 + i * 120
        ctx.line_width = 18
        ctx.line_join = join
        ctx.stroke_style = "darkorange"
        ctx.begin_path(); ctx.move_to(x, 230); ctx.line_to(x + 40, 160); ctx.line_to(x + 80, 230); ctx.stroke()
        ctx.fill_text(join, x + 20, 260)

    # dashes, and dashes that march
    ctx.line_width = 4
    ctx.stroke_style = "#333"
    for i, dash in enumerate([[12, 6], [2, 6], [16, 4, 2, 4]]):
        ctx.set_line_dash(dash)
        ctx.line_dash_offset = -t * 20 if i == 0 else 0
        y = 290 + i * 25
        ctx.begin_path(); ctx.move_to(40, y); ctx.line_to(340, y); ctx.stroke()
    ctx.set_line_dash([])
```


## Text

| Python | Standard | What it does |
|---|---|---|
| `ctx.fill_text(text, x, y)` | `fillText` | Draws text. Add a fourth number to squeeze it into that width. |
| `ctx.stroke_text(text, x, y)` | `strokeText` | Draws the outline of the text |
| `await ctx.measure_text(text).width` | `measureText` | **(await)** How wide the text will be, in points. The answer also has `actual_bounding_box_ascent` and `actual_bounding_box_descent` (how far it reaches above and below `y`). |
| `ctx.font = "bold 24px serif"` | `font` | Style, size and family. Families that always work: `sans-serif`, `serif`, `monospace`, `system-ui`, `cursive`. Add `italic` or `bold` at the front. |
| `ctx.text_align = "center"` | `textAlign` | Where `x` is: `"left"`, `"center"`, `"right"`, or `"start"`/`"end"` (which follow the writing direction) |
| `ctx.text_baseline = "middle"` | `textBaseline` | Where `y` is: `"alphabetic"` (the line letters sit on, the default), `"top"`, `"hanging"`, `"middle"`, `"ideographic"`, `"bottom"` |
| `ctx.direction = "rtl"` | `direction` | Writing direction: `"ltr"`, `"rtl"` or `"inherit"` |
| `ctx.letter_spacing = "4px"` | `letterSpacing` | Extra space between letters (older devices ignore it) |
| `ctx.word_spacing = "10px"` | `wordSpacing` | Extra space between words (older devices ignore it) |
| `ctx.font_kerning = "none"` | `fontKerning` | Whether letter pairs are fitted closer: `"auto"`, `"normal"`, `"none"` |

Emoji are text, so `ctx.fill_text("🚀", x, y)` draws a rocket. Text has no line wrapping; draw each line yourself, a line height apart.

```python
def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.font = "20px sans-serif"

    # text_align: the red line is x
    ctx.stroke_style = "red"
    ctx.begin_path(); ctx.move_to(200, 10); ctx.line_to(200, 110); ctx.stroke()
    ctx.fill_style = "#222"
    for i, align in enumerate(["left", "center", "right"]):
        ctx.text_align = align
        ctx.fill_text(f"text_align {align}", 200, 35 + i * 30)

    # text_baseline: the red line is y
    ctx.text_align = "left"
    ctx.begin_path(); ctx.move_to(10, 170); ctx.line_to(width - 10, 170); ctx.stroke()
    ctx.font = "16px sans-serif"
    for i, base in enumerate(["top", "middle", "alphabetic", "bottom"]):
        ctx.text_baseline = base
        ctx.fill_text(base, 15 + i * 105, 170)
    ctx.text_baseline = "alphabetic"

    # outline, spacing, squeezing
    ctx.font = "bold 40px serif"
    ctx.line_width = 1.5
    ctx.stroke_style = "navy"
    ctx.stroke_text("Outline", 15, 250)
    ctx.font = "18px monospace"
    ctx.letter_spacing = "6px"
    ctx.fill_text("SPACED", 230, 250)
    ctx.letter_spacing = "0px"
    ctx.fill_text("This sentence is squeezed into 200 points", 15, 290, 200)
```


## Images

| Python | Standard | What it does |
|---|---|---|
| `img = load_image(address)` | | Starts loading a picture from a path beside the scene (`"cat.png"`), a web address or a `data:` address. It draws once loaded. |
| `ctx.draw_image(img, x, y)` | `drawImage` | Draws it at its own size, top-left at `x, y` |
| `ctx.draw_image(img, x, y, w, h)` | `drawImage` | Draws it stretched to `w` by `h` |
| `ctx.draw_image(img, sx, sy, sw, sh, x, y, w, h)` | `drawImage` | Cuts the part `sx, sy, sw, sh` out of the picture and draws it at `x, y, w, h`. This is how sprite sheets work. |
| `ctx.image_smoothing_enabled = False` | `imageSmoothingEnabled` | Keeps pixel art crisp and blocky when scaled up |
| `ctx.image_smoothing_quality = "high"` | `imageSmoothingQuality` | How carefully pictures are smoothed: `"low"`, `"medium"`, `"high"` |

`draw_image` can draw another canvas too, not only a picture. Make one with `js.document.create_element("canvas")`, draw on its own `get_context("2d")`, and use it like an image.

```python
from urllib.parse import quote

# a 4 x 4 pixel picture, as an SVG drawing
svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='4' height='4' shape-rendering='crispEdges'>"
       "<rect width='4' height='4' fill='gold'/><rect x='1' y='1' width='1' height='1' fill='black'/>"
       "<rect x='2' y='1' width='1' height='1' fill='black'/><rect x='1' y='3' width='2' height='1' fill='black'/></svg>")
face = load_image("data:image/svg+xml," + quote(svg))

def draw():
    ctx.fill_style = "#dde"
    ctx.fill_rect(0, 0, width, height)
    ctx.draw_image(face, 20, 20)                           # its own size: tiny
    ctx.image_smoothing_enabled = True
    ctx.draw_image(face, 50, 20, 120, 120)                 # stretched, smoothed
    ctx.image_smoothing_enabled = False
    ctx.draw_image(face, 190, 20, 120, 120)                # stretched, crisp
    ctx.draw_image(face, 0, 0, 2, 2, 330, 20, 120, 120)    # just the top-left quarter
```

## Transforms

A transform moves, turns or stretches the drawing grid, so everything drawn after it is moved, turned or stretched too.

| Python | Standard | What it does |
|---|---|---|
| `ctx.translate(x, y)` | `translate` | Moves the grid's corner `(0, 0)` to `x, y` |
| `ctx.rotate(angle)` | `rotate` | Turns the grid round `(0, 0)` by `angle` radians, clockwise |
| `ctx.scale(sx, sy)` | `scale` | Stretches the grid. A negative number flips it, so `ctx.scale(-1, 1)` makes a mirror image. |
| `ctx.transform(a, b, c, d, e, f)` | `transform` | Applies any stretch, slant and move at once. `ctx.transform(1, 0, 0.5, 1, 0, 0)` slants things sideways. |
| `ctx.save()` | `save` | Remembers the transform and every setting on this page |
| `ctx.restore()` | `restore` | Goes back to what the last `save()` remembered |
| `ctx.set_transform(a, b, c, d, e, f)` | `setTransform` | Replaces the transform completely |
| `ctx.reset_transform()` | `resetTransform` | Clears the transform |
| `await ctx.get_transform()` | `getTransform` | **(await)** The current transform, as numbers `a` to `f` |

**Use `save()` and `restore()` rather than `set_transform` or `reset_transform`.** The canvas starts with its own scale so drawing is sharp on high-resolution screens, and those two calls remove it: afterwards everything draws `pixel_ratio` times too small. If you do use them, put the scale back with `ctx.set_transform(pixel_ratio, 0, 0, pixel_ratio, 0, 0)`.

```python
import math

def arrow():
    # an arrow drawn round (0, 0), pointing right
    ctx.begin_path()
    ctx.move_to(-30, -10); ctx.line_to(10, -10); ctx.line_to(10, -22)
    ctx.line_to(35, 0); ctx.line_to(10, 22); ctx.line_to(10, 10); ctx.line_to(-30, 10)
    ctx.close_path()
    ctx.fill()

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    steps = [
        ("as drawn", lambda: None),
        ("rotate", lambda: ctx.rotate(math.radians(-45))),
        ("scale", lambda: ctx.scale(1.5, 0.6)),
        ("mirror", lambda: ctx.scale(-1, 1)),
        ("slant", lambda: ctx.transform(1, 0, 0.8, 1, 0, 0)),
    ]
    ctx.font = "14px sans-serif"
    ctx.text_align = "center"
    for i, (name, change) in enumerate(steps):
        ctx.save()
        ctx.translate(55 + i * 90, 80)      # move to this slot
        change()
        ctx.fill_style = f"hsl({i * 60}, 70%, 50%)"
        arrow()
        ctx.restore()                       # back to normal for the label
        ctx.fill_style = "#333"
        ctx.fill_text(name, 55 + i * 90, 150)
```


## Shadows

| Python | Standard | What it does |
|---|---|---|
| `ctx.shadow_color = "rgba(0, 0, 0, 0.5)"` | `shadowColor` | The shadow's colour. A see-through colour looks most natural. Shadows are off until this is set. |
| `ctx.shadow_blur = 10` | `shadowBlur` | How soft the shadow is. 0 is a hard edge. |
| `ctx.shadow_offset_x = 5` | `shadowOffsetX` | How far right the shadow falls |
| `ctx.shadow_offset_y = 5` | `shadowOffsetY` | How far down the shadow falls |

A coloured shadow with no offset makes a glow.

```python
import math

def draw():
    ctx.fill_style = "#eef"
    ctx.fill_rect(0, 0, width, height)
    ctx.save()
    for i, blur in enumerate([0, 8, 24]):
        ctx.shadow_color = "rgba(0, 0, 0, 0.5)"
        ctx.shadow_blur = blur
        ctx.shadow_offset_x = 8
        ctx.shadow_offset_y = 8
        ctx.fill_style = "tomato"
        ctx.fill_rect(30 + i * 130, 30, 90, 90)
    # a glow: coloured shadow, no offset
    ctx.shadow_color = "deepskyblue"
    ctx.shadow_blur = 30
    ctx.shadow_offset_x = 0
    ctx.shadow_offset_y = 0
    ctx.fill_style = "white"
    ctx.begin_path()
    ctx.arc(200, 210, 40, 0, math.tau)
    ctx.fill()
    ctx.restore()                # shadows off again
```


## Blending and filters

| Python | Standard | What it does |
|---|---|---|
| `ctx.global_composite_operation = "multiply"` | `globalCompositeOperation` | How new drawing mixes with what is already there. Set it back to `"source-over"` when you are done. |
| `ctx.filter = "blur(4px)"` | `filter` | An effect on everything drawn next. Set back to `"none"`. |

The blend modes:

| Mode | What you see |
|---|---|
| `source-over` | The new drawing on top. The normal one. |
| `destination-over` | The new drawing behind what is there |
| `source-in` | The new drawing, only where it overlaps the old; the rest is wiped |
| `source-out` | The new drawing, only where it does **not** overlap; the rest is wiped |
| `source-atop` | The new drawing, only on top of the old; the old stays |
| `destination-in` | The old drawing, only where the new one overlaps it |
| `destination-out` | Rubs out the old drawing where the new one goes, like an eraser |
| `destination-atop` | The old drawing, only inside the new one, which shows behind |
| `lighter` | Adds the colours together, so overlaps get brighter. Good for glows and fire. |
| `copy` | Only the new drawing; everything else is wiped |
| `xor` | Both, with the overlap cut out |
| `multiply` | Darkens, like overlapping inks |
| `screen` | Lightens, like overlapping lights |
| `overlay`, `soft-light`, `hard-light` | Boost contrast in different strengths |
| `darken`, `lighten` | Keeps whichever is darker, or lighter |
| `color-dodge`, `color-burn` | Brightens, or darkens, strongly |
| `difference`, `exclusion` | Inverts where the colours differ |
| `hue`, `saturation`, `color`, `luminosity` | Takes one quality from the new colour and the rest from the old |

Filters, which can be combined with spaces (`"blur(2px) grayscale(1)"`): `blur(4px)`, `brightness(1.5)`, `contrast(2)`, `grayscale(1)`, `sepia(1)`, `saturate(3)`, `hue-rotate(90deg)`, `invert(1)`, `opacity(0.5)` and `drop-shadow(4px 4px 4px black)`.

This program draws every blend mode: a blue square first, then a red circle over it with that mode.

```python
import math

modes = ["source-over", "destination-over", "source-in", "source-out", "source-atop",
         "destination-in", "destination-out", "destination-atop", "lighter", "copy", "xor",
         "multiply", "screen", "overlay", "darken", "lighten", "color-dodge", "color-burn",
         "hard-light", "soft-light", "difference", "exclusion", "hue", "saturation", "color", "luminosity"]

# Each mode gets its own little canvas, so one mode can't affect the others.
tiles = []
for mode in modes:
    tile = js.document.create_element("canvas")
    tile.width = 80
    tile.height = 80
    t = tile.get_context("2d")
    t.fill_style = "royalblue"
    t.fill_rect(5, 5, 45, 45)
    t.global_composite_operation = mode
    t.fill_style = "crimson"
    t.begin_path()
    t.arc(48, 48, 26, 0, math.tau)
    t.fill()
    tiles.append(tile)

def draw():
    ctx.fill_style = "#eee"
    ctx.fill_rect(0, 0, width, height)
    ctx.font = "10px sans-serif"
    ctx.text_align = "center"
    ctx.fill_style = "#222"
    for i, (mode, tile) in enumerate(zip(modes, tiles)):
        x, y = 10 + (i % 7) * 92, 10 + (i // 7) * 100
        ctx.draw_image(tile, x, y)
        ctx.fill_text(mode, x + 40, y + 92)
```


## Clipping and hit testing

| Python | Standard | What it does |
|---|---|---|
| `ctx.clip()` | `clip` | Makes the current path a window: everything drawn next shows only inside it. Wrap it in `save()`/`restore()` to undo it. |
| `await ctx.is_point_in_path(x, y)` | `isPointInPath` | **(await)** Whether a point is inside the current path |
| `await ctx.is_point_in_stroke(x, y)` | `isPointInStroke` | **(await)** Whether a point is on the path's outline |

The point for `is_point_in_path` and `is_point_in_stroke` is in real pixels: multiply your `x` and `y` by `pixel_ratio`. For simple shapes it is quicker to do the sum in Python, such as `(x - cx) ** 2 + (y - cy) ** 2 < r * r` for a circle.

```python
import math

message = "Click inside or outside the star"

def star_path():
    ctx.begin_path()
    for i in range(10):
        r = 110 if i % 2 == 0 else 45
        a = i * math.pi / 5 - math.pi / 2
        ctx.line_to(200 + r * math.cos(a), 160 + r * math.sin(a))
    ctx.close_path()

async def clicked(event):
    global message
    star_path()
    inside = await ctx.is_point_in_path(event.x * pixel_ratio, event.y * pixel_ratio)
    message = "Inside the star!" if inside else "Outside the star"

canvas.add_event_listener("pointerdown", clicked)

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.save()
    star_path()
    ctx.clip()                                # only the star shows from here...
    for i in range(12):
        ctx.fill_style = f"hsl({i * 30}, 80%, 55%)"
        ctx.fill_rect(0, i * 25, width, 25)  # ...so stripes become a striped star
    ctx.restore()
    ctx.fill_style = "#333"
    ctx.font = "18px sans-serif"
    ctx.fill_text(message, 20, 310)
```


## Paths you can keep: Path2D

`js.Path2D()` makes a path object you build once and draw many times. It takes the same pieces as `ctx` (`move_to`, `line_to`, `arc`, `rect`, `round_rect`, `ellipse`, `bezier_curve_to`…). It can also be made from SVG path text, such as `js.Path2D("M10 10 h 80 v 80 h -80 Z")`, which is handy for copying shapes from drawing programs.

| Call | What it does |
|---|---|
| `ctx.fill(path)` | Fills that path |
| `ctx.stroke(path)` | Outlines it |
| `ctx.clip(path)` | Clips to it |
| `await ctx.is_point_in_path(path, x, y)` | **(await)** Whether a point is inside it |
| `path.add_path(other)` | Adds another path's pieces to this one |

```python
heart = js.Path2D("M 0 -12 C -8 -28 -36 -24 -36 -2 C -36 18 -10 30 0 40 C 10 30 36 18 36 -2 C 36 -24 8 -28 0 -12 Z")
ring = js.Path2D()
ring.arc(0, 0, 30, 0, 6.283)

def draw():
    ctx.fill_style = "#fff5f7"
    ctx.fill_rect(0, 0, width, height)
    for i in range(5):
        ctx.save()
        ctx.translate(60 + i * 75, 80)
        ctx.scale(0.6 + i * 0.15, 0.6 + i * 0.15)
        ctx.fill_style = f"hsl({340 + i * 8}, 80%, {65 - i * 6}%)"
        ctx.fill(heart)
        ctx.restore()
        ctx.save()
        ctx.translate(60 + i * 75, 200)
        ctx.line_width = 2 + i * 2
        ctx.stroke_style = "slateblue"
        ctx.stroke(ring)
        ctx.restore()
```


## Pixels

| Python | Standard | What it does |
|---|---|---|
| `await ctx.get_image_data(x, y, w, h).data` | `getImageData` | **(await)** The colours of every pixel in that area, as one long list: red, green, blue, alpha (0 to 255) for each pixel in turn |
| `ctx.create_image_data(w, h)` | `createImageData` | A blank block of pixels |
| `ctx.put_image_data(pixels, x, y)` | `putImageData` | Puts a block of pixels straight onto the canvas, ignoring transforms, alpha and blend modes |
| `js.ImageData(js.Uint8ClampedArray(numbers), w, h)` | | Makes a block of pixels from a Python list of numbers |

Pixel positions and sizes here are in **real pixels**, not points, so multiply by `pixel_ratio` to match your drawing. Reading pixels is slow (it waits a frame and copies every pixel), and so is building big lists in Python: use pixels for small areas or one-off effects, and drawing calls for everything else.

```python
# a small pattern made pixel by pixel, then shown big
size = 32
numbers = []
for y in range(size):
    for x in range(size):
        numbers += [x * 8, y * 8, (x ^ y) * 8, 255]     # red, green, blue, alpha
pixels = js.ImageData(js.Uint8ClampedArray(numbers), size, size)

# put it on a small canvas, so it can be drawn scaled up
tile = js.document.create_element("canvas")
tile.width = size
tile.height = size
tile.get_context("2d").put_image_data(pixels, 0, 0)

def draw():
    ctx.fill_style = "black"
    ctx.fill_rect(0, 0, width, height)
    ctx.image_smoothing_enabled = False
    ctx.draw_image(tile, 20, 20, 256, 256)
```


## Saving and resetting

| Python | Standard | What it does |
|---|---|---|
| `ctx.save()` | `save` | Remembers every setting on this page, the transform and the clip |
| `ctx.restore()` | `restore` | Goes back to the last `save()` |
| `ctx.reset()` | `reset` | Clears the canvas and puts every setting back to the start, including the canvas's sharp-screen scale; follow it with `ctx.scale(pixel_ratio, pixel_ratio)` |

`canvas.width` and `canvas.height` are the canvas's size in real pixels. You don't need to set them: the canvas keeps them matched to its size.

## Related

- [Drawing in 2D](drawing-2d.md): the ideas, with examples
- [Colours](colours.md)
- [3D functions](3d-functions.md)
