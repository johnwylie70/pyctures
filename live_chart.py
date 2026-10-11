# Live Chart: a line chart of a made-up temperature, drawing itself as new readings arrive.
# Use: move the mouse over it to read a value.
# Try changing: 200, how many readings it keeps; low and high, the range the chart shows; 0.8, how fast the temperature swings.
#
# Run it:   pyctures run live_chart.py
# Share it: pyctures build live_chart.py -o site/

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
