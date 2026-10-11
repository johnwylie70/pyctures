# Bouncing Balls: balls of many colours fall, bounce and leave trails.
# Use: click or tap to add a ball.
# Try changing: 600, the pull of gravity; 0.85, how much speed a bounce keeps; 0.25, how fast the trails fade.
#
# Run it:   pyctures run bouncing_balls.py
# Share it: pyctures build bouncing_balls.py -o site/

import math, random

balls = []

def add_ball(x, y):
    balls.append({
        "x": x, "y": y,
        "vx": random.uniform(-220, 220), "vy": random.uniform(-260, -60),
        "r": random.uniform(10, 24),
        "hue": random.randint(0, 360),
    })

for _ in range(6):
    add_ball(random.uniform(40, 300), random.uniform(40, 200))

def on_mouse_down(x, y):
    add_ball(x, y)

def update(dt):
    for b in balls:
        b["vy"] += 600 * dt
        b["x"] += b["vx"] * dt
        b["y"] += b["vy"] * dt
        if b["x"] < b["r"] or b["x"] > width - b["r"]:
            b["vx"] = -b["vx"]
            b["x"] = max(b["r"], min(width - b["r"], b["x"]))
        if b["y"] > height - b["r"]:
            b["y"] = height - b["r"]
            b["vy"] = -b["vy"] * 0.85

def draw():
    ctx.fill_style = "rgba(10, 10, 20, 0.25)"
    ctx.fill_rect(0, 0, width, height)
    for b in balls:
        ctx.fill_style = f"hsl({b['hue']}, 80%, 60%)"
        ctx.begin_path()
        ctx.arc(b["x"], b["y"], b["r"], 0, math.tau)
        ctx.fill()
