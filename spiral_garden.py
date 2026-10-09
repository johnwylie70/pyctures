# Spiral Garden: 200 dots placed on the golden angle, turning slowly.
import math

t = 0

def update(dt):
    global t
    t += dt

def draw():
    ctx.fill_style = "rgba(8, 8, 20, 0.2)"   # see-through, so the dots leave trails
    ctx.fill_rect(0, 0, width, height)
    cx, cy = width / 2, height / 2
    spread = min(width, height) / 32
    for i in range(200):
        angle = i * 2.39996 + t * 0.5           # 2.39996 radians is the golden angle
        r = math.sqrt(i) * spread
        size = 2 + 4 * math.sin(i * 0.15 - t * 3) ** 2
        ctx.fill_style = f"hsl({i * 1.5 + t * 40}, 90%, 60%)"
        ctx.begin_path()
        ctx.arc(cx + r * math.cos(angle), cy + r * math.sin(angle), size, 0, math.tau)
        ctx.fill()
