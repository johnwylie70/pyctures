# Space Rocks: steer a ship, shoot the rocks, and do not get hit. A rock breaks in two when it is shot.
# Use: left and right turn, up fires the engine, space shoots. Or hold the mouse or a finger to fly towards it; every tap shoots.
# Try changing: 3, the rocks in a wave; 500, the speed of a bullet; 7, the sides of a rock.
#
# Run it:   pyctures run space_rocks.py

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
    if lives == 0:
        new_game()
    else:
        shoot()

def steer(dt):
    ship.spin = 0
    if "ArrowLeft" in keys: ship.spin = degrees(-230)
    if "ArrowRight" in keys: ship.spin = degrees(230)
    if "ArrowUp" in keys: ship.push(300 * dt)
    if " " in pressed: shoot()
    if mouse.down:
        ship.angle = ship.angle_to(mouse)
        ship.push(300 * dt)
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
