# Tutorial: A Bouncing Ball

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/bouncing-ball](https://www.circuitry.dev/docs/pyctures/tutorials/bouncing-ball) (in Circuitry Studio's help)

A ball that falls, bounces off the floor and walls, and slows down a little with every bounce. Tap or click to throw it again. Then a version with many balls. This is the pattern behind almost every moving picture: keep numbers in Python, change them in `update(dt)`, and paint them in `draw()`.

## 1. A ball that moves

```python
x, y = 100, 100      # where the ball is
vx, vy = 180, 0      # how fast it moves, in points per second
r = 24               # its radius

def update(dt):
    global x, y
    x += vx * dt
    y += vy * dt

def draw():
    background("#16213e")
    circle(x, y, r, "orange")
```

Run it and the ball slides off to the right and away. Each frame, `update(dt)` moves it by its speed times `dt`, the time since the last frame. `global x, y` lets the function change the variables made at the top.

## 2. Gravity and bounces

Gravity is a steady push downwards: add to `vy` every frame. A bounce is a speed turned round: when the ball reaches the floor, put it back on the floor and flip `vy`. Multiplying by 0.8 rather than 1 loses a little speed on each bounce.

```python
x, y = 100, 100
vx, vy = 180, 0
r = 24
gravity = 900        # points per second, per second
bounce = 0.8         # how much speed is kept after a bounce

def update(dt):
    global x, y, vx, vy
    vy += gravity * dt
    x += vx * dt
    y += vy * dt

    if y > height - r:           # the floor
        y = height - r
        vy = -vy * bounce
        vx *= 0.99               # a little friction
    if x < r:                    # the left wall
        x = r
        vx = -vx * bounce
    if x > width - r:            # the right wall
        x = width - r
        vx = -vx * bounce

def on_mouse_down(mx, my):
    global x, y, vx, vy
    x, y = mx, my
    vx, vy = 300, -500           # throw it up and to the right

def draw():
    background("#16213e")
    circle(x, y, r, "orange")
    ctx.fill_style = "white"
    ctx.font = "16px sans-serif"
    ctx.fill_text("Tap or click to throw the ball", 12, 24)
```

`on_mouse_down(mx, my)` is called when you click, or touch the canvas with a finger. It moves the ball to that spot and throws it.

## 3. Lots of balls

With many balls, each one needs its own numbers. A small class keeps them together.

```python
class Ball:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = random(-250, 250)
        self.vy = random(-600, -200)
        self.r = random(8, 26)
        self.colour = f"hsl({random(360)}, 85%, 60%)"

    def update(self, dt):
        self.vy += 900 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y > height - self.r:
            self.y = height - self.r
            self.vy *= -0.8
        if self.x < self.r or self.x > width - self.r:
            self.x = min(max(self.x, self.r), width - self.r)
            self.vx *= -0.8

    def draw(self):
        circle(self.x, self.y, self.r, self.colour)

balls = [Ball(random(50, 350), 100) for _ in range(20)]

def on_mouse_down(x, y):
    for _ in range(10):
        balls.append(Ball(x, y))

def update(dt):
    for ball in balls:
        ball.update(dt)

def draw():
    background("#16213e")
    for ball in balls:
        ball.draw()
    ctx.fill_style = "white"
    ctx.font = "16px sans-serif"
    ctx.fill_text(f"{len(balls)} balls. Tap to add more.", 12, 24)
```

Add `?measure=1` to the page's address and keep adding balls to see how many your device draws smoothly.

## The same thing as a loop

The ball of step 2 can also be written as one loop, with no `update` and no `draw`. `await frame()` waits for the screen's next refresh, so each pass of the loop is one frame.

```python
import time

x, y = 100, 100
vx, vy = 180, 0
r = 24
gravity = 900
bounce = 0.8
last = time.monotonic()

while True:
    await frame()                # wait for the screen
    now = time.monotonic()
    dt = now - last              # the time since the last frame
    last = now

    if mouse.down:               # hold to carry the ball, let go to throw it
        x, y = mouse.x, mouse.y
        vx, vy = 300, -500
    vy += gravity * dt
    x += vx * dt
    y += vy * dt
    if y > height - r:
        y = height - r
        vy = -vy * bounce
        vx *= 0.99
    if x < r:
        x = r
        vx = -vx * bounce
    if x > width - r:
        x = width - r
        vx = -vx * bounce

    background("#16213e")
    circle(x, y, r, "orange")
```

There is no `global` line: the loop is at the top level of the file, where the variables live. The loop reads `mouse` itself, in place of `on_mouse_down`.

`update` and `draw` suit games, where things happen in any order and the `on_` functions tell you about them. A loop suits a drawing made step by step, or a sequence: first this, then wait, then that. `await frame()` is also how a scene stays in step with the screen: everything drawn in one pass appears together at the next refresh, so nothing is ever shown half drawn.

## Try this

- Change `gravity` to 200 for the Moon, or make it negative.
- Let the balls bounce off the ceiling too.
- Give each ball a trail: paint the background with `"rgba(22, 33, 62, 0.3)"` instead of a solid colour, so the last few frames fade out slowly.

## Related

- [How a program is shaped](../program-shape.md): `update`, `draw` and the `on_` functions
- Next: [a simple game](../tutorials/game.md)
