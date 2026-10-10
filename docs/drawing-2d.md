# Drawing in 2D

Full reference: [www.circuitry.dev/docs/pyctures/drawing](https://www.circuitry.dev/docs/pyctures/drawing) (in Circuitry Studio's help)

A first picture takes a handful of plain functions, such as `background`, `circle`, `rect`, `line` and `text`. Everything else 2D is drawn through `ctx`, the canvas's own drawing surface. This page starts with those, then lists what `ctx` can do, grouped by job, with a short program for each group that you can paste into a Python file and run.

## The basics

- **Positions are in points**, measured from the **top-left corner**. `x` grows to the right and `y` grows **down**. The bottom-right corner is `(width, height)`.
- Drawing is sharp on every screen: the canvas takes care of high-resolution displays for you.
- **Say angles in degrees with `degrees()`.** Wherever an angle is wanted, write `degrees(90)` for a quarter turn or `degrees(360)` for a full one. The canvas itself counts angles in radians, where a full turn is `math.tau` (about 6.283); `degrees()` does the sum for you, so you never need to. Examples you find elsewhere, and the later parts of this page, write angles in radians.
- **Colours** are text: a name (`"red"`, `"skyblue"`), a hex code (`"#ff8800"`), `"rgb(255, 136, 0)"`, `"rgba(255, 136, 0, 0.5)"` (the last number is opacity, 0 to 1), or `"hsl(30, 100%, 50%)"` (hue in degrees, then saturation and lightness).
- **Two spellings, one call.** Every name works in snake_case or in its standard form: `ctx.fill_rect(...)` is `ctx.fillRect(...)`, and `ctx.fill_style` is `ctx.fillStyle`. This guide uses snake_case from here on.
- The canvas's background is white in the light theme and near-black in the dark theme. Paint your own background first so your drawing looks the same in both.

## The quick way: plain functions

A handful of functions draw the things a first picture needs, one call each. They need no `ctx.` in front.

| Call | What it draws |
|---|---|
| `background(colour)` | Paints the whole canvas one colour |
| `circle(x, y, radius, colour)` | A filled circle. `x, y` is its centre |
| `ellipse(x, y, width, height, colour)` | An oval. `x, y` is its centre, as a circle's is |
| `rect(x, y, width, height, colour)` | A filled rectangle. `x, y` is its top-left corner |
| `triangle(x1, y1, x2, y2, x3, y3, colour)` | A triangle, by its three corners |
| `polygon(x, y, radius, sides, colour)` | A shape with that many equal sides (6 is a hexagon), centred on `x, y`, with one corner straight up |
| `star(x, y, radius, points, colour)` | A star with that many points, centred on `x, y`, with one point straight up |
| `line(x1, y1, x2, y2, colour, thickness)` | A straight line from one point to the other |
| `text(words, x, y, colour, size)` | Words. `x, y` is their left end, on the line the letters sit on. Add `"centre"` at the end and `x, y` is the middle of the words |
| `picture(what, x, y, size)` | An emoji, a word, or a picture from a file beside your program, centred on `x, y` and `size` high: `picture("🌙", 300, 80, 60)`, `picture("cat.png", 100, 100, 80)` |

```python
def draw():
    background("lightskyblue")
    rect(0, height - 80, width, 80, "yellowgreen")
    circle(width - 80, 80, 45, "gold")
    line(40, height - 80, 40, height - 200, "saddlebrown", 8)
    circle(40, height - 220, 50, "forestgreen")
    text("A tree in the sun", width / 2, 40, "white", 28, "centre")
```

The rules are the same for all of them:

- **The colour can be left out.** The shape then uses the colour already in use: the last one you gave, or the one set with `ctx.fill_style = "red"`. A canvas starts with black, so give a colour the first time.
- **What you give stays.** A colour, a thickness, a text's size and `"centre"` all stay for the shapes drawn after, until you give another. `background` is the exception: it paints and leaves the colour as it was.
- **Shapes are filled** unless you ask for an outline, which is next.
- **Your own names win.** If your program has its own function or variable called `circle`, `text`, `star` or any of the others, yours is used.
- **They are for 2D.** In a 3D scene they stop with an error that says so.
- **There is one `picture` for everything.** A moon, a heart, a rocket: any emoji is a picture, so there is no function for each thing. A file's picture is loaded the first time it is asked for, and appears once it has arrived. An image from `load_image` can be given too.

### Outlines and rounded corners

Every shape takes two more things by name: `outline="white", thickness=6`. With a colour, the shape is filled and has a border. Without a colour, only the edge is drawn.

```python
def draw():
    background("midnightblue")
    circle(90, 90, 50, "gold", outline="white", thickness=6)       # filled, with a border
    circle(220, 90, 50, outline="white", thickness=6)              # the edge alone
    star(350, 90, 55, 5, "gold")
    rect(40, 180, 160, 80, "tomato", round=20)                     # rounded corners
    polygon(280, 220, 50, 6, outline="lightgreen", thickness=4)    # six sides
    triangle(340, 270, 380, 180, 420, 270, "orchid")
    ellipse(220, 300, 300, 30, "steelblue")
    picture("🌙", 440, 60, 50)
```

The outline's colour and thickness stay for the next outline, as a fill colour does. `rect` also takes `round`, the size of its rounded corners, and `star` takes `inner`, how far out its inner corners are as a part of its radius (0.4 unless you say): `star(100, 100, 50, 5, "gold", inner=0.6)`.

### Chance: `random` and `pick`

| Call | What it gives |
|---|---|
| `random(1, 6)` | A whole number from 1 to 6. Either end can come up, as on a dice |
| `random(6)` | A whole number from 0 to 6 |
| `random()` | A fraction: from 0 up to, but never reaching, 1 |
| `random(0, 0.5)` | When an end has a fraction, so may the answer: any number from 0 to 0.5 |
| `pick(list)` | One thing from a list |

`random` is also the name of a module that comes with Python, and most Python books begin `import random`. Both work together here: after `import random`, `random(1, 6)` still gives a whole number, and `random.randint(1, 6)` and the rest of the module are there too.

```python
def draw():
    background("black")
    for i in range(50):
        circle(random(width), random(height), random(5, 20), pick(["red", "gold", "white"]))
```

## The long way: `ctx`

Each of the plain functions is a short way of writing what `ctx` does. `circle(200, 150, 80, "gold")` is these four lines:

```python
ctx.fill_style = "gold"
ctx.begin_path()
ctx.arc(200, 150, 80, 0, degrees(360))
ctx.fill()
```

A circle the long way is an arc that goes all the way round, from angle 0 to a full turn. Half of one is `ctx.arc(200, 150, 80, 0, degrees(180))`: part circles stay with `ctx`. `ctx` is the web's own 2D drawing surface, and it can do far more than they can: curves, any shape you can describe, gradients, shadows, clipping and transforms. The two mix freely in one program. The rest of this page is `ctx`.

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

A `Sprite` is a picture that moves. The picture can be an emoji or any short text, an image from `load_image`, or a function that draws it. It draws itself centred on its `x, y`.

```python
rocket = Sprite("🚀", x=100, y=200, size=64)
```

| Part | What it is |
|---|---|
| `picture` | An emoji or text, an image from `load_image`, or a function that draws it |
| `x`, `y` | Where its centre is |
| `vx`, `vy` | Its speed in points per second, used by `update(dt)` |
| `angle` | How far it is turned. 0 faces right, and it grows clockwise. Say it in degrees with `degrees(90)` |
| `spin` | How fast it turns each second, used by `update(dt)`: `degrees(180)` is half a turn a second |
| `size` | How big it is, in points (48 unless you say) |
| `visible` | `False` hides it |
| `sprite.update(dt)` | Moves it by its speed and turns it by its spin |
| `sprite.draw()` | Draws it (call this in your `draw()`) |

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
        f.wrap()
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

### Sprites that touch

| Call | What it gives |
|---|---|
| `sprite.touches(other)` | `True` when the two overlap |
| `sprite.hit(sprites)` | The first sprite in the list that it touches, or `None` when it touches none |
| `sprite.contains(x, y)` | `True` when that point is on it. `sprite.contains(mouse)` works too: anything with an `x` and a `y` |

`hit` is the one a game uses most: one thing against many.

```python
rock = bullet.hit(rocks)
if rock:
    remove(rocks, rock)
    score += 10
```

`sprite.touches(other)` is a question you ask a sprite. The list called [`touches`](program-shape.md#every-finger-touches) is a different thing: every finger that is down, which you loop over.

A sprite is tested as a circle or as a box. It is a circle unless you say otherwise.

| Part | What it is |
|---|---|
| `shape` | `"circle"` (as it starts) or `"box"` |
| `radius` | The size of its circle. It starts at 0.4 of `size`, because an emoji has some space round it. Set it to make a sprite easier or harder to hit |
| `width`, `height` | The size of its box. Both are `size` until you set them, so a box can be wider than it is tall |

What is exact, and what is not:

- Circle against circle, box against box and circle against box are all exact for the shapes above.
- A box that is turned (its `angle` is not 0) is tested properly against a circle and against a point. Two boxes are tested as if neither were turned.
- The shape is a circle or a box, never the outline of the picture. A long thin picture wants a box.
- Two shapes that only just meet at their edges do not touch. A sprite of size 0 touches nothing.
- A hidden sprite still touches. That is useful for a goal you cannot see. To stop a sprite touching, take it out of its list.

### Leaving the picture, and moving the way it faces

| Call | What it does |
|---|---|
| `sprite.wrap()` | When it has gone off one edge, it comes back on the opposite one |
| `sprite.bounce()` | Bounces it off the edges. Name the edges to use only some: `ball.bounce("top", "bottom")`. It gives the edge it bounced off (`"left"`, `"right"`, `"top"`, `"bottom"`), or `None` |
| `sprite.offscreen()` | `True` when all of it is outside the picture |
| `sprite.push(amount)` | Speeds it up the way it faces: this is an engine |
| `sprite.forward(distance)` | Steps it the way it faces, without changing its speed |
| `sprite.limit(speed)` | Slows it to that speed if it is going faster |
| `sprite.angle_to(other)` | The angle from it to another sprite, to `mouse`, or to a point: `angle_to(x, y)` |
| `sprite.distance_to(other)` | How far it is to another sprite, to `mouse`, or to a point: `distance_to(x, y)` |

Call `wrap()` or `bounce()` after `update(dt)`, every frame. With these there is no trigonometry to write: a ship that turns, flies and faces the mouse is

```python
ship.spin = 4 if "ArrowRight" in keys else 0
if "ArrowUp" in keys:
    ship.push(300 * dt)
if mouse.down:
    ship.angle = ship.angle_to(mouse)
ship.update(dt)
ship.wrap()
```

### Pictures you draw yourself

Give a sprite a function in place of a picture and it is called to draw the sprite. It is given the sprite's size. Draw round `0, 0`, which is the sprite's centre, and facing right: the sprite puts it in place and turns it.

```python
def arrow(size):
    triangle(size / 2, 0, -size / 2, -size / 3, -size / 2, size / 3, "gold")

pointer = Sprite(arrow, 200, 150, size=60)

def update(dt):
    pointer.angle = pointer.angle_to(mouse)

def draw():
    ctx.fill_style = "#123"
    ctx.fill_rect(0, 0, width, height)
    pointer.draw()
```

To draw with `ctx` itself, write the function as `def arrow(ctx, size):` and it is given `ctx` as well.

Two plain shapes are ready made. Each is hit-tested as exactly the shape you see.

| Call | What it makes |
|---|---|
| `Sprite.box(x, y, width, height, colour)` | A coloured box, tested as a box |
| `Sprite.circle(x, y, size, colour)` | A coloured circle `size` across, tested as that circle |

The colour is white unless you say, and can be changed later: `ball.colour = "red"` (`color` works too).

```python
ball = Sprite.circle(200, 100, 20, "orange")
bat = Sprite.box(200, 260, 100, 14)
ball.vx = 150
ball.vy = 200

def update(dt):
    bat.x = mouse.x
    ball.update(dt)
    ball.bounce()
    if ball.vy > 0 and ball.touches(bat):
        ball.vy = -ball.vy

def draw():
    ctx.fill_style = "#123"
    ctx.fill_rect(0, 0, width, height)
    ball.draw()
    bat.draw()
```

### Taking things out of a list

Games remove things all the time: a bullet that has left the picture, a rock that was hit. `remove(things, thing)` takes one thing out of a list (and does nothing if it is not there, where Python's own `things.remove(thing)` would stop with an error).

Removing from a list while a loop is going through that same list makes the loop skip things. So loop over a copy, written `things[:]`, and remove from the real one:

```python
for bullet in bullets[:]:
    bullet.update(dt)
    if bullet.offscreen():
        remove(bullets, bullet)
```

Use this one way everywhere and it is never wrong.

The [simple game tutorial](tutorials/game.md) builds a game from emoji sprites, and the [Space Rocks tutorial](tutorials/space-rocks.md) builds one from sprites you draw. The examples `space_rocks.py`, `bat_and_ball.py` and `brick_breaker.py` are whole games made this way.

## Everything else

`ctx` is the standard 2D drawing surface, so any other operation it has works the same way, in either spelling: clipping (`ctx.clip()`), pixel access (`ctx.get_image_data`, `ctx.put_image_data`), filters (`ctx.filter = "blur(4px)"`) and the rest. Reading pixels back is a read, so it needs `await` and is slow; drawing is not.

## Related

- [How a program is shaped](program-shape.md)
- [Tutorial: your first drawing](tutorials/first-drawing.md)
- [3D scenes](3d.md)

← [How a program is shaped](program-shape.md) · [3D scenes](3d.md) →
