# Brought across from JavaScript: a spinning square, a circle, and a click
# handler, written the way a JavaScript canvas example writes them.
# Shows: the few changes that turn a JavaScript canvas example into Python.
# See docs/from-javascript.md for the JavaScript it came from.
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
