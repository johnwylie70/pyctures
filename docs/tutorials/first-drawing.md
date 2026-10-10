# Tutorial: Your First Drawing

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/first-drawing](https://www.circuitry.dev/docs/pyctures/tutorials/first-drawing) (in Circuitry Studio's help)

In this tutorial you draw a house on a hill, with the sun in the sky, using rectangles, a circle, a triangle and some words. It takes about ten minutes and needs no Python beyond the basics.

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
    background("lightskyblue")
```

The canvas turns blue.

- `def draw():` is a function the canvas calls every frame. Anything inside it is drawn again and again, so your picture stays put even when the canvas changes size.
- `background("lightskyblue")` paints the whole canvas that colour. A colour is a name in quotes; there are about 140 names, and [Colours](../colours.md) lists other ways to write one.

Save after each change to see it. Press `Ctrl+C` in the terminal when you are done.

## 3. Add the ground

Add these lines inside `draw()`, under the sky. Keep the four spaces at the start of each line: they are what put a line inside the function.

```python
def draw():
    background("lightskyblue")

    ground = height * 0.7
    rect(0, ground, width, height - ground, "yellowgreen")
```

`rect(x, y, width, height, colour)` draws a filled rectangle. `x, y` is its top-left corner, and `(0, 0)` is the **top-left** corner of the canvas. `y` counts **down** from the top, so `height * 0.7` is 70% of the way down. The green rectangle starts there and fills the rest: `width` and `height` are the size of the canvas.

## 4. The whole picture

Here is the finished drawing. Read the comments to see which lines draw what, then run it.

```python
def draw():
    # sky and ground
    background("lightskyblue")
    ground = height * 0.7
    rect(0, ground, width, height - ground, "yellowgreen")

    # the sun
    circle(width - 80, 80, 45, "gold")

    # the house
    x = width / 2 - 100        # left edge of the house
    w, h = 200, 140            # its width and height
    top = ground - h           # its top edge
    rect(x, top, w, h, "bisque")

    # the roof: a triangle, by its three corners
    triangle(x - 20, top, x + w / 2, top - 90, x + w + 20, top, "firebrick")

    # the door, and a window with a white frame
    rect(x + 80, ground - 70, 40, 70, "saddlebrown")
    rect(x + 20, top + 30, 45, 40, "lightcyan", outline="white", thickness=4)

    # a name for the picture
    text("My house", 20, 44, "white", 28)
```

- `circle(x, y, radius, colour)` draws a filled circle. `x, y` is its centre.
- `text(words, x, y, colour, size)` writes words, starting at `x, y`.
- `triangle(x1, y1, x2, y2, x3, y3, colour)` draws a triangle from its three corners: the roof.
- The window has `outline="white", thickness=4` at the end: a filled shape with a border. Every shape can have one.

The house is placed with `x`, `w`, `h` and `top`, and everything else is worked out from them. Change `w, h = 200, 140` to `w, h = 260, 100` and the whole house, roof and door included, changes with it.

## 5. The long way

There is no `ctx` in the house: the plain functions drew all of it. `ctx` is the canvas's own drawing surface, and each plain function is a short way of writing what it does. The sun, written the long way, is these four lines:

```python
ctx.fill_style = "gold"
ctx.begin_path()
ctx.arc(width - 80, 80, 45, 0, degrees(360))
ctx.fill()
```

A circle the long way is an arc that goes all the way round, from 0 to a full turn. `degrees(360)` is a full turn: it lets you say any angle in degrees. You never need to write a circle like this, but every drawing example you find elsewhere does, and now you can read it. [Drawing in 2D](../drawing-2d.md) shows the rest of what `ctx` can do.

## Try this

- Change the colours. Any colour name works, or a code such as `"#ff8800"`.
- Add a cloud: three white circles that overlap.
- Add a path to the door with a thick line: `line(x1, y1, x2, y2, colour, thickness)` draws from one point to another, so try `line(width / 2, height * 0.7, width / 2, height, "tan", 30)`.
- Make it night: a dark blue sky, a pale moon instead of the sun, and `"yellow"` windows.
- Make the sun move: add `t = 0` above `draw()`, an `update(dt)` function that does `global t` and `t += dt`, and draw the sun at `80 + t * 20` across.

## Related

- [Drawing in 2D](../drawing-2d.md): every shape, colour and text setting
- [How a program is shaped](../program-shape.md)
- Next: [a bouncing ball](../tutorials/bouncing-ball.md)
