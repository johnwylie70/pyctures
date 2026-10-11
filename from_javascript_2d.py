# From JavaScript, 2D: a canvas example brought across from JavaScript (docs/from-javascript.md shows the original). A square spins, and a click moves the circle.
# Use: click or tap.
# Try changing: 0.02, how fast the square turns; "Click me", the words.
#
# Run it:   pyctures run from_javascript_2d.py
# Share it: pyctures build from_javascript_2d.py -o site/

import math

angle = 0
ctx.font = "24px sans-serif"
label_width = await ctx.measure_text("Click me").width

def draw():
    global angle
    ctx.fill_style = "#123"
    ctx.fill_rect(0, 0, width, height)

    ctx.save()
    ctx.translate(width / 2, height / 2)
    ctx.rotate(angle)
    ctx.fill_style = "orange"
    ctx.fill_rect(-50, -50, 100, 100)
    ctx.restore()

    ctx.fill_style = "skyblue"
    ctx.begin_path()
    ctx.arc(width / 2, height / 2, 20, 0, math.pi * 2)
    ctx.fill()

    ctx.fill_style = "white"
    ctx.font = "24px sans-serif"
    ctx.fill_text("Click me", (width - label_width) / 2, height - 40)
    angle += 0.02

def clicked(event):
    print("clicked at", event.offsetX, event.offsetY)

canvas.add_event_listener("click", clicked)
