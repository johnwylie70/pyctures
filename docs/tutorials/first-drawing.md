# Tutorial: Your First Drawing

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/first-drawing](https://www.circuitry.dev/docs/pyctures/tutorials/first-drawing) (in Circuitry Studio's help)

In this tutorial you draw a house on a hill, with the sun in the sky, using a rectangle, a triangle, some circles and a line of text. It takes about ten minutes and needs no Python beyond the basics.

## 1. Make the file

Make a new file called `house.py` in your editor, and start it in a terminal:

```bash
pyctures run house.py
```

Your browser opens beside it. Each time you save the file, the drawing runs again.

## 2. Paint the sky

Type this and save:

```python
def draw():
    ctx.fill_style = "lightskyblue"
    ctx.fill_rect(0, 0, width, height)
```

The canvas turns blue.

- `def draw():` is a function the canvas calls every frame. Anything inside it is drawn again and again, so your picture stays put even when the canvas changes size.
- `ctx` is the drawing surface. `fill_style` picks a colour and `fill_rect(x, y, w, h)` fills a rectangle.
- `(0, 0)` is the **top-left** corner, and `width` and `height` are the size of the canvas, so this rectangle covers everything.

Save after each change to see it. Press `Ctrl+C` in the terminal when you are done.

## 3. Add the ground

Add these lines inside `draw()`, under the sky. Keep the four spaces at the start of each line: they are what put a line inside the function.

```python
def draw():
    ctx.fill_style = "lightskyblue"
    ctx.fill_rect(0, 0, width, height)

    ground = height * 0.7
    ctx.fill_style = "yellowgreen"
    ctx.fill_rect(0, ground, width, height - ground)
```

`y` counts **down** from the top, so `height * 0.7` is 70% of the way down. The green rectangle starts there and fills the rest.

## 4. The whole picture

Here is the finished drawing. Read the comments to see which lines draw what, then run it.

```python
import math

def draw():
    # sky and ground
    ctx.fill_style = "lightskyblue"
    ctx.fill_rect(0, 0, width, height)
    ground = height * 0.7
    ctx.fill_style = "yellowgreen"
    ctx.fill_rect(0, ground, width, height - ground)

    # the sun: a circle is an arc that goes all the way round
    ctx.fill_style = "gold"
    ctx.begin_path()
    ctx.arc(width - 80, 80, 45, 0, math.tau)
    ctx.fill()

    # the house
    x = width / 2 - 100        # left edge of the house
    w, h = 200, 140            # its width and height
    top = ground - h           # its top edge
    ctx.fill_style = "bisque"
    ctx.fill_rect(x, top, w, h)

    # the roof: a triangle is a path of three lines
    ctx.fill_style = "firebrick"
    ctx.begin_path()
    ctx.move_to(x - 20, top)
    ctx.line_to(x + w / 2, top - 90)
    ctx.line_to(x + w + 20, top)
    ctx.close_path()
    ctx.fill()

    # the door and a window, with outlines
    ctx.fill_style = "saddlebrown"
    ctx.fill_rect(x + 80, ground - 70, 40, 70)
    ctx.fill_style = "lightcyan"
    ctx.fill_rect(x + 20, top + 30, 45, 40)
    ctx.stroke_style = "white"
    ctx.line_width = 4
    ctx.stroke_rect(x + 20, top + 30, 45, 40)

    # a name for the picture
    ctx.fill_style = "white"
    ctx.font = "bold 28px sans-serif"
    ctx.fill_text("My house", 20, 44)
```

The house is placed with `x`, `w`, `h` and `top`, and everything else is worked out from them. Change `w, h = 200, 140` to `w, h = 260, 100` and the whole house, roof and door included, changes with it.

## Try this

- Change the colours. Any colour name works, or a code such as `"#ff8800"`.
- Add a cloud: three white circles that overlap.
- Make it night: a dark blue sky, a pale moon instead of the sun, and `"yellow"` windows.
- Make the sun move: add `t = 0` above `draw()`, an `update(dt)` function that does `global t` and `t += dt`, and draw the sun at `80 + t * 20` across.

## Related

- [Drawing in 2D](../drawing-2d.md): every shape, colour and text setting
- [How a program is shaped](../program-shape.md)
- Next: [a bouncing ball](../tutorials/bouncing-ball.md)
