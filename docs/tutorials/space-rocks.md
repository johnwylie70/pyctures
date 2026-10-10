# Tutorial: Space Rocks

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/space-rocks](https://www.circuitry.dev/docs/pyctures/tutorials/space-rocks) (in Circuitry Studio's help)

Steer a ship and shoot the rocks: a ship that turns and fires its engine, rocks that drift and break in two when shot, and a picture that wraps round at its edges. It is built in four steps, and each step is a whole program you can run. Nothing is downloaded: the ship is a triangle and the rocks are seven-sided shapes.

The game is made of sprites. A sprite knows how to move, how to wrap round the edges and how to tell what it is touching, so the game reads much like a description of itself. See [Sprites](../drawing-2d.md#sprites) for everything a sprite can do.

## Step 1: a ship you can fly

A sprite's picture can be a function that draws it. The function is given the sprite's size, and draws round `0, 0` facing right: here one `triangle`, with an outline and no colour, so only its edge is drawn. The sprite puts the drawing where the ship is and turns it to the ship's angle.

```python
# A sprite's picture is drawn round 0, 0, facing right.
def draw_ship(size):
    triangle(size / 2, 0, -size / 2, -size / 3, -size / 2, size / 3, outline="white", thickness=2)

ship = Sprite(draw_ship, 200, 150, size=30)

def update(dt):
    ship.spin = 0
    if "ArrowLeft" in keys: ship.spin = degrees(-230)
    if "ArrowRight" in keys: ship.spin = degrees(230)
    if "ArrowUp" in keys: ship.push(300 * dt)
    ship.limit(350)
    ship.update(dt)
    ship.wrap()

def draw():
    background("black")
    ship.draw()
```

Click the picture first, so it has the keyboard. Left and right turn the ship and up fires the engine.

- `ship.spin` is how fast the ship turns: `degrees(230)` is 230 degrees a second. `ship.update(dt)` does the turning and the moving.
- `ship.push(300 * dt)` speeds the ship up in the direction it faces. Let go and it keeps drifting, as things do in space. `ship.limit(350)` stops it going faster than 350 points a second.
- `ship.wrap()` brings the ship back on the opposite side when it leaves the picture.

## Step 2: rocks

The rocks are sprites too, kept in a list. Each has a speed and a spin of its own, and wraps like the ship.

```python
def draw_ship(size):
    triangle(size / 2, 0, -size / 2, -size / 3, -size / 2, size / 3, outline="white", thickness=2)

def draw_rock(size):
    polygon(0, 0, size / 2, 7, outline="white", thickness=2)

ship = Sprite(draw_ship, 200, 150, size=30)
rocks = []

def add_rock(x, y, size):
    rock = Sprite(draw_rock, x, y, size=size)
    rock.vx = random(-70, 70)
    rock.vy = random(-70, 70)
    rock.spin = degrees(random(-60, 60))
    rocks.append(rock)

for i in range(4):
    add_rock(0, random(height), 80)

def update(dt):
    ship.spin = 0
    if "ArrowLeft" in keys: ship.spin = degrees(-230)
    if "ArrowRight" in keys: ship.spin = degrees(230)
    if "ArrowUp" in keys: ship.push(300 * dt)
    ship.limit(350)
    ship.update(dt)
    ship.wrap()
    for rock in rocks:
        rock.update(dt)
        rock.wrap()
    # Hit a rock and the ship goes back to the middle.
    if ship.hit(rocks):
        ship.x, ship.y = width / 2, height / 2
        ship.vx, ship.vy = 0, 0

def draw():
    background("black")
    for rock in rocks:
        rock.draw()
    ship.draw()
```

- `draw_rock` is one `polygon` with seven sides. Its radius is half the rock's size, so the same function draws a big rock and a small one.
- `ship.hit(rocks)` gives the first rock the ship is touching, or `None` when it touches none. That is all a collision takes.
- Sprites are tested as circles. A rock's circle is a little smaller than its picture, which is fair to the player: a near miss is a miss.

## Step 3: shooting, and rocks that split

A bullet is a small white circle, `Sprite.circle`. It starts at the ship, takes the ship's angle, and one `push` sends it on its way.

```python
def draw_ship(size):
    triangle(size / 2, 0, -size / 2, -size / 3, -size / 2, size / 3, outline="white", thickness=2)

def draw_rock(size):
    polygon(0, 0, size / 2, 7, outline="white", thickness=2)

ship = Sprite(draw_ship, 200, 150, size=30)
rocks = []
bullets = []
score = 0

def add_rock(x, y, size):
    rock = Sprite(draw_rock, x, y, size=size)
    rock.vx = random(-70, 70)
    rock.vy = random(-70, 70)
    rock.spin = degrees(random(-60, 60))
    rocks.append(rock)

for i in range(4):
    add_rock(0, random(height), 80)

# A bullet starts at the ship and is pushed the way the ship faces.
def shoot():
    bullet = Sprite.circle(ship.x, ship.y, 5)
    bullet.angle = ship.angle
    bullet.push(500)
    bullets.append(bullet)

def update(dt):
    global score
    ship.spin = 0
    if "ArrowLeft" in keys: ship.spin = degrees(-230)
    if "ArrowRight" in keys: ship.spin = degrees(230)
    if "ArrowUp" in keys: ship.push(300 * dt)
    if " " in pressed: shoot()
    ship.limit(350)
    ship.update(dt)
    ship.wrap()
    for rock in rocks:
        rock.update(dt)
        rock.wrap()
    # Loop over a copy of the list (bullets[:]), because the loop removes bullets from it.
    for bullet in bullets[:]:
        bullet.update(dt)
        rock = bullet.hit(rocks)
        if rock:
            remove(bullets, bullet)
            remove(rocks, rock)
            score += 10
            if rock.size > 20:
                add_rock(rock.x, rock.y, rock.size / 2)
                add_rock(rock.x, rock.y, rock.size / 2)
        elif bullet.offscreen():
            remove(bullets, bullet)
    # Hit a rock and the ship goes back to the middle.
    if ship.hit(rocks):
        ship.x, ship.y = width / 2, height / 2
        ship.vx, ship.vy = 0, 0

def draw():
    background("black")
    for rock in rocks:
        rock.draw()
    for bullet in bullets:
        bullet.draw()
    ship.draw()
    text(f"Score {score}", 12, 30, "white", 20)
```

Press space to shoot.

- `" " in pressed` is true once for each press of the space bar. With `keys` in its place, holding space would pour out sixty bullets a second.
- `bullet.hit(rocks)` finds the rock a bullet has met. Both are taken out of their lists with `remove`, and a big rock leaves two rocks of half the size.
- The loop goes over a copy of the list, written `bullets[:]`. Removing things from a list while a loop is going through that same list makes it skip some. Looping over a copy and removing from the real list is always safe.
- `bullet.offscreen()` is true when a bullet has left the picture, so it can be removed too. Without this the list would grow for ever.

## Step 4: lives, waves and starting again

The last step turns it into a game: three lives, a new wave of rocks when the last one is shot, a ship that cannot be hurt for two seconds after it appears, and a way to play on a phone.

```python
# A sprite's picture is drawn round 0, 0, facing right.
def draw_ship(size):
    triangle(size / 2, 0, -size / 2, -size / 3, -size / 2, size / 3, outline="white", thickness=2)

def draw_rock(size):
    polygon(0, 0, size / 2, 7, outline="white", thickness=2)

ship = Sprite(draw_ship, 0, 0, size=30)
rocks = []
bullets = []
score = 0
lives = 3
safe = 0                        # seconds in which nothing can hurt the ship
held = 0                        # seconds the mouse or a finger has been down

def add_rock(x, y, size):
    rock = Sprite(draw_rock, x, y, size=size)
    rock.vx = random(-70, 70)
    rock.vy = random(-70, 70)
    rock.spin = degrees(random(-60, 60))
    rocks.append(rock)

def new_ship():
    global safe
    ship.x = width / 2
    ship.y = height / 2
    ship.vx = 0
    ship.vy = 0
    ship.angle = degrees(-90)   # pointing up: 0 faces right
    safe = 2

def new_game():
    global score, lives
    score = 0
    lives = 3
    rocks.clear()
    bullets.clear()
    new_ship()

def shoot():
    bullet = Sprite.circle(ship.x, ship.y, 5)
    bullet.angle = ship.angle
    bullet.push(500)            # off it goes, the way the ship faces
    bullets.append(bullet)

def on_mouse_down(x, y):
    global held
    held = 0
    if lives == 0:
        new_game()
    else:
        ship.angle = ship.angle_to(x, y)
        shoot()

def steer(dt):
    global held
    ship.spin = 0
    if "ArrowLeft" in keys: ship.spin = degrees(-230)
    if "ArrowRight" in keys: ship.spin = degrees(230)
    if "ArrowUp" in keys: ship.push(300 * dt)
    if " " in pressed: shoot()
    # A tap is over before the engine starts. Keep holding and the ship flies to your finger.
    if mouse.down:
        held += dt
        ship.angle = ship.angle_to(mouse)
        if held > 0.18: ship.push(300 * dt)
    ship.limit(350)

def update(dt):
    global score, lives, safe
    if lives == 0:
        if " " in pressed:
            new_game()
        return
    if not rocks:               # a new wave, starting on the left edge
        for i in range(3):
            add_rock(0, random(height), 80)
        safe = 2
    safe -= dt
    steer(dt)
    ship.update(dt)
    ship.wrap()
    for rock in rocks:
        rock.update(dt)
        rock.wrap()
    # Loop over a copy of the list (bullets[:]), because the loop removes bullets from it.
    for bullet in bullets[:]:
        bullet.update(dt)
        rock = bullet.hit(rocks)
        if rock:
            remove(bullets, bullet)
            remove(rocks, rock)
            score += 10
            if rock.size > 20:  # a big rock breaks in two
                add_rock(rock.x, rock.y, rock.size / 2)
                add_rock(rock.x, rock.y, rock.size / 2)
        elif bullet.offscreen():
            remove(bullets, bullet)
    if safe <= 0 and ship.hit(rocks):
        lives -= 1
        new_ship()

def draw():
    background("black")
    for rock in rocks:
        rock.draw()
    for bullet in bullets:
        bullet.draw()
    ship.visible = lives > 0 and (safe <= 0 or safe % 0.25 > 0.12)   # it blinks while it is safe
    ship.draw()
    text(f"Score {score}   Lives {lives}", 12, 30, "white", 20, "left")
    if lives == 0:
        text("Game over", width / 2, height / 2, "white", 32, "centre")
        text("Tap or press space to play again", width / 2, height / 2 + 40, "white", 18, "centre")

new_game()
```

- `safe` counts down the seconds in which nothing can hurt the ship. Without it, a new ship could appear inside a rock and be lost at once. While it is safe the ship blinks: `ship.visible` is switched on and off.
- A new wave of three rocks starts whenever the list of rocks is empty. They start on the left edge, away from the ship.
- On a phone or with a mouse, `on_mouse_down` is called once for each press. It turns the ship to face the press with `ship.angle_to(x, y)` and shoots, so a tap aims and fires.
- `held` counts the seconds the mouse or a finger has been down. A tap is over in about a tenth of a second, so the engine, which waits for 0.18, never starts. Keep holding a moment longer and the ship flies towards your finger, turning to follow it with `ship.angle_to(mouse)`.
- When the lives run out, the same tap or the space bar starts a new game.

This is the example `space_rocks.py`. Three more small games are written the same way: `bat_and_ball.py`, `brick_breaker.py` and `snake.py`.

## Make it yours

- Change the numbers: a faster ship, slower rocks, bigger bullets.
- Give the rocks five sides, or nine. Make the ship a `star`.
- Give the ship a little drag, so it slows down by itself: multiply `ship.vx` and `ship.vy` by 0.99 in `steer`.
- Add a flying saucer worth 100 points: one more sprite, and one more `hit`.
- Keep the best score in a variable that `new_game` does not reset.

## Related

- [Drawing in 2D: sprites](../drawing-2d.md#sprites)
- [How a program is shaped: keyboard, mouse and touch](../program-shape.md#keyboard-mouse-and-touch-input)
- [Tutorial: a simple game](game.md), with emoji sprites
- Next: [a spinning 3D cube](spinning-cube.md)
