# Tutorial: A Live Chart

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/live-chart](https://www.circuitry.dev/docs/pyctures/tutorials/live-chart) (in Circuitry Studio's help)

Draw charts straight from Python data: first a bar chart from a list, then a line chart that updates as new readings arrive, with gridlines, labels and a readout that follows your finger or mouse. Because you draw every line yourself, the chart can look exactly the way you want.

## The idea: data space and screen space

Your data has its own units (degrees, pounds, visitors). The screen has points, with `y` counting **down**. A chart is a pair of small functions that turn one into the other:

```text
screen x = left  + (index / (count - 1)) * plot width
screen y = bottom - (value - lowest) / (highest - lowest) * plot height
```

The minus sign in the second line is what makes bigger values go **up**.

## 1. A bar chart from a list

```python
sales = {"Mon": 12, "Tue": 19, "Wed": 7, "Thu": 15, "Fri": 22, "Sat": 30, "Sun": 18}

def draw():
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)

    # the plot area, leaving room for labels
    left, right, top, bottom = 50, width - 20, 56, height - 40
    plot_w, plot_h = right - left, bottom - top
    biggest = max(sales.values())

    # title
    ctx.fill_style = "#222"
    ctx.font = "bold 18px sans-serif"
    ctx.text_align = "left"
    ctx.fill_text("Cups of coffee sold", left, 26)

    # gridlines and their numbers
    ctx.font = "12px sans-serif"
    ctx.text_align = "right"
    ctx.text_baseline = "middle"
    for i in range(0, biggest + 1, 5):
        y = bottom - i / biggest * plot_h
        ctx.stroke_style = "#e5e5e5"
        ctx.line_width = 1
        ctx.begin_path()
        ctx.move_to(left, y)
        ctx.line_to(right, y)
        ctx.stroke()
        ctx.fill_style = "#777"
        ctx.fill_text(str(i), left - 8, y)

    # one bar per day, with its name underneath
    slot = plot_w / len(sales)
    ctx.text_align = "center"
    ctx.text_baseline = "top"
    for n, (day, value) in enumerate(sales.items()):
        bar_h = value / biggest * plot_h
        x = left + n * slot + slot * 0.15
        ctx.fill_style = "#2a9d8f" if value < 20 else "#e76f51"
        ctx.fill_rect(x, bottom - bar_h, slot * 0.7, bar_h)
        ctx.fill_style = "#444"
        ctx.fill_text(day, x + slot * 0.35, bottom + 8)
```

- `left`, `right`, `top` and `bottom` are the edges of the plot area, worked out from `width` and `height` every frame, so the chart fills the canvas at any size.
- Each gridline is placed with the same sum as the bars: `bottom - value / biggest * plot_h`.
- `text_align` and `text_baseline` line the labels up: numbers right-aligned beside the axis, day names centred under their bars.
- Bars of 20 or more are drawn in a second colour. Change the data and run again.

## 2. A live line chart

Now the data changes while you watch. Each frame `update` adds a new reading and drops the oldest, and `draw` plots whatever is in the list. Move the mouse over the chart, or touch it, to read off a value.

```python
import math, random

readings = []          # the last 200 readings
t = 0.0
temperature = 20.0

def update(dt):
    global t, temperature
    t += dt
    # a made-up sensor: a slow daily swing plus some noise
    temperature += (20 + 5 * math.sin(t * 0.8) - temperature) * 0.05 + random.uniform(-0.3, 0.3)
    readings.append(temperature)
    if len(readings) > 200:
        readings.pop(0)

def draw():
    ctx.fill_style = "#0f172a"
    ctx.fill_rect(0, 0, width, height)
    if len(readings) < 2:
        return

    left, right, top, bottom = 50, width - 20, 50, height - 30
    plot_w, plot_h = right - left, bottom - top
    low, high = 10, 30                        # the range the chart shows

    def sx(i):                                 # reading number -> screen x
        return left + i / (len(readings) - 1) * plot_w

    def sy(v):                                 # temperature -> screen y
        return bottom - (v - low) / (high - low) * plot_h

    # gridlines every 5 degrees
    ctx.font = "12px sans-serif"
    ctx.text_align = "right"
    ctx.text_baseline = "middle"
    ctx.line_width = 1
    for v in range(low, high + 1, 5):
        ctx.stroke_style = "#1e293b"
        ctx.begin_path()
        ctx.move_to(left, sy(v))
        ctx.line_to(right, sy(v))
        ctx.stroke()
        ctx.fill_style = "#94a3b8"
        ctx.fill_text(f"{v}°", left - 8, sy(v))

    # the shaded area under the line
    ctx.begin_path()
    ctx.move_to(sx(0), bottom)
    for i, v in enumerate(readings):
        ctx.line_to(sx(i), sy(v))
    ctx.line_to(sx(len(readings) - 1), bottom)
    ctx.close_path()
    shade = ctx.create_linear_gradient(0, top, 0, bottom)
    shade.add_color_stop(0, "rgba(56, 189, 248, 0.35)")
    shade.add_color_stop(1, "rgba(56, 189, 248, 0)")
    ctx.fill_style = shade
    ctx.fill()

    # the line itself
    ctx.begin_path()
    for i, v in enumerate(readings):
        if i == 0:
            ctx.move_to(sx(i), sy(v))
        else:
            ctx.line_to(sx(i), sy(v))
    ctx.stroke_style = "#38bdf8"
    ctx.line_width = 2
    ctx.line_join = "round"
    ctx.stroke()

    # title and the latest value
    ctx.text_align = "left"
    ctx.text_baseline = "alphabetic"
    ctx.fill_style = "white"
    ctx.font = "bold 18px sans-serif"
    ctx.fill_text(f"Temperature now: {readings[-1]:.1f}°", left, 30)

    # a readout where the pointer is
    if left <= mouse.x <= right:
        i = round((mouse.x - left) / plot_w * (len(readings) - 1))
        i = min(max(i, 0), len(readings) - 1)
        x, y = sx(i), sy(readings[i])
        ctx.stroke_style = "#64748b"
        ctx.set_line_dash([4, 4])
        ctx.begin_path()
        ctx.move_to(x, top)
        ctx.line_to(x, bottom)
        ctx.stroke()
        ctx.set_line_dash([])
        ctx.fill_style = "white"
        ctx.begin_path()
        ctx.arc(x, y, 5, 0, math.tau)
        ctx.fill()
        ctx.font = "13px sans-serif"
        ctx.fill_text(f"{readings[i]:.1f}°", x + 8, y - 8)
```

What to notice:

- **`sx` and `sy`** are the two small functions from the top of the page. Every point on the chart goes through them, so changing `low` and `high` rescales everything at once.
- **The shaded area** is the same path as the line, closed down to the bottom edge and filled with a gradient that fades out.
- **The readout** uses `mouse.x`, which follows a finger on a touch screen too, to find the nearest reading.
- The chart is drawn from scratch every frame, which is plenty fast for hundreds of points.

## Your own data

Anything Python can produce can be charted this way: a list you typed in, numbers worked out in a loop, or results from numpy. To chart a fixed list, put it in place of `readings` and leave out `update`. To make it scale itself, use `low, high = min(readings), max(readings)` in place of fixed numbers, adding a little margin so the line does not touch the edges.

## Try this

- Draw dots on the bar chart's values, or a line joining the tops of the bars.
- Plot two series in different colours, with a small key in a corner.
- Make the bar chart grow: keep a `grow` number that `update` takes from 0 to 1, and multiply every `bar_h` by it.

## Related

- [Drawing in 2D](../drawing-2d.md): paths, gradients and text
- [How a program is shaped](../program-shape.md): `update` and `draw`
- [Finding mistakes](../finding-mistakes.md)
