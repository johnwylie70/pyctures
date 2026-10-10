# Bouncing balls, for the example web page (index.html beside this file).
# Use: click to add a ball.
# Try changing: 600, the pull of gravity.

import math, random

balls = []

def add_ball(x, y):
    balls.append([x, y, random.uniform(-200, 200), random.uniform(-250, -50),
                  random.uniform(10, 22), random.randint(0, 360)])

for _ in range(8):
    add_ball(random.uniform(40, 300), random.uniform(40, 160))

def on_mouse_down(x, y):
    add_ball(x, y)

def update(dt):
    for b in balls:
        b[3] += 600 * dt
        b[0] += b[2] * dt
        b[1] += b[3] * dt
        if b[0] < b[4] or b[0] > width - b[4]:
            b[2] = -b[2]
            b[0] = max(b[4], min(width - b[4], b[0]))
        if b[1] > height - b[4]:
            b[1] = height - b[4]
            b[3] = -b[3] * 0.85

def draw():
    ctx.fill_style = "rgba(16, 24, 40, 0.3)"
    ctx.fill_rect(0, 0, width, height)
    for x, y, vx, vy, r, hue in balls:
        ctx.fill_style = f"hsl({hue}, 80%, 60%)"
        ctx.begin_path()
        ctx.arc(x, y, r, 0, math.tau)
        ctx.fill()
