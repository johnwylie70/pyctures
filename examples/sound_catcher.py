# Sound Catcher: a game with sound effects. Catch the coins and dodge the bombs; you have three lives.
# Use: move the mouse or a finger, or the left and right arrow keys. A click or a tap plays again.
# The first click, tap or key press turns the sound on: a browser keeps a page silent until then.
# Try changing: "coin" to "powerup" or "pop"; pitch=score % 12 to pitch=0; 0.7, the seconds between drops.
#
# Run it:   pyctures run sound_catcher.py
# Share it: pyctures build sound_catcher.py -o site/

from synths import *

sound_button()                  # a speaker in the corner to switch the sound off (so does M)

basket = Sprite("🧺", 200, 300, size=64)
things = []
score = 0
lives = 3
wait = 0.0

def drop():
    bomb = random(1, 4) == 1
    thing = Sprite("💣" if bomb else "🪙", random(30, int(width) - 30), -30, size=40)
    thing.bomb = bomb
    thing.vy = random(160, 260)
    things.append(thing)

def update(dt):
    global score, lives, wait
    if lives <= 0:
        return
    if mouse.inside: basket.x = mouse.x
    if "ArrowLeft" in keys: basket.x -= 400 * dt
    if "ArrowRight" in keys: basket.x += 400 * dt
    basket.y = height - 50
    wait -= dt
    if wait <= 0:
        wait = 0.7
        drop()
    for thing in things[:]:
        thing.update(dt)
        if thing.touches(basket):
            things.remove(thing)
            if thing.bomb:
                lives -= 1
                play_sound("explosion" if lives > 0 else "lose")
            else:
                score += 1
                play_sound("coin", pitch=score % 12)      # each coin a little higher, then round again
        elif thing.y > height + 30:
            things.remove(thing)
            if not thing.bomb:
                play_sound("blip", 0.5, pitch=-12)        # a coin got away

def on_mouse_down(x, y):
    global score, lives
    if lives <= 0:
        score, lives = 0, 3
        things.clear()
        play_sound("powerup")

def draw():
    background("#101a33")
    for thing in things:
        thing.draw()
    basket.draw()
    text(f"Coins {score}", 16, 34, "white", 22, "left")
    text("❤️" * lives, width - 16, 34, "white", 22, "right")
    if lives <= 0:
        text("Game over. Click to play again", width / 2, height / 2, "gold", 28, "centre")
