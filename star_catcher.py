# Star Catcher: a game with emoji sprites. Catch the stars and dodge the rocks; you have three lives.
# Use: the left and right arrow keys, or drag. Space or a tap plays again.
# Try changing: 0.6, the seconds between new stars; 320, how fast the rocket moves; the emoji.
#
# Run it:   pyctures run star_catcher.py
# Share it: pyctures build star_catcher.py -o site/

import random

player = Sprite("🚀", 200, 400, size=48)
stars = []
rocks = []
score = 0
lives = 3
spawn = 0.0

def reset():
    global score, lives
    score, lives = 0, 3
    stars.clear()
    rocks.clear()
    player.x, player.y = width / 2, height - 80

def drop(picture, size):
    s = Sprite(picture, random.uniform(20, width - 20), -20, size=size)
    s.vy = random.uniform(120, 220)
    return s

def update(dt):
    global spawn, score, lives
    if lives <= 0:
        if " " in keys or mouse.down:
            reset()
        return
    speed = 320 * dt
    if "ArrowLeft" in keys: player.x -= speed
    if "ArrowRight" in keys: player.x += speed
    if mouse.down:
        player.x = mouse.x
    player.x = max(24, min(width - 24, player.x))
    player.y = height - 80

    spawn -= dt
    if spawn <= 0:
        spawn = 0.6
        stars.append(drop("⭐", 32))
        if random.random() < 0.4:
            rocks.append(drop("🪨", 36))

    for s in stars + rocks:
        s.update(dt)
        s.angle += dt
    for s in stars[:]:
        if s.touches(player):
            score += 1
            stars.remove(s)
        elif s.y > height + 30:
            stars.remove(s)
    for r in rocks[:]:
        if r.touches(player):
            lives -= 1
            rocks.remove(r)
        elif r.y > height + 30:
            rocks.remove(r)

def draw():
    ctx.fill_style = "#0b1020"
    ctx.fill_rect(0, 0, width, height)
    for s in stars + rocks:
        s.draw()
    player.draw()
    ctx.fill_style = "white"
    ctx.font = "bold 20px system-ui"
    ctx.text_align = "left"
    ctx.fill_text(f"Score {score}   Lives {'❤️' * lives}", 12, 30)
    if lives <= 0:
        ctx.text_align = "center"
        ctx.font = "bold 32px system-ui"
        ctx.fill_text("Game over", width / 2, height / 2)
        ctx.font = "18px system-ui"
        ctx.fill_text("Tap or press space to play again", width / 2, height / 2 + 34)

reset()
