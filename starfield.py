# Starfield: you fly through 300 stars.
# Use: hold the mouse button or a finger down to go faster.
# Try changing: 300, how many stars; 1.2 and 0.35, the fast and slow speeds.
#
# Run it:   pyctures run starfield.py

import random

def new_star(z=None):
    return [random.uniform(-1, 1), random.uniform(-1, 1), z or random.random()]

stars = [new_star() for _ in range(300)]

def update(dt):
    speed = 1.2 if mouse.down else 0.35
    for s in stars:
        s[2] -= speed * dt
        if s[2] < 0.02:
            s[:] = new_star(1)

def draw():
    ctx.fill_style = "rgba(0, 0, 12, 0.4)"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "white"
    for x, y, z in stars:
        size = (1 - z) * 4
        ctx.fill_rect(width / 2 + x / z * width / 2, height / 2 + y / z * height / 2, size, size)
