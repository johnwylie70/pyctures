# High Score: catch the star as often as you can in 10 seconds. Your best score is still there the next time you play.
# Use: click or tap the star. When the time is up, click anywhere to play again.
# Try changing: 10, the seconds in a game; 60, the size of the star; "best", the name the score is saved under.
#
# Run it:   pyctures run high_score.py

best = load("best", 0)              # the score saved last time, or 0 the first time
score = 0
left = 10                           # seconds left in this game
star = Sprite("⭐", 200, 160, size=60)

def update(dt):
    global best, left
    if left <= 0:                   # the game is over
        return
    left -= dt
    if left <= 0 and score > best:
        best = score
        save("best", best)          # kept for next time

def on_mouse_down(x, y):
    global score, left
    if left <= 0:                   # start the next game
        score = 0
        left = 10
    elif star.contains(x, y):
        score += 1
        star.x = random(40, width - 40)
        star.y = random(90, height - 40)

def draw():
    background("midnightblue")
    star.draw()
    text(f"Score {score}", 16, 34, "white", 22, "left")
    text(f"Best {best}", width - 16, 34, "gold", 22, "right")
    if left > 0:
        text(round(left), width / 2, 26, "white", 22, "centre")
    else:
        text("Time is up. Click to play again", width / 2, height / 2, "white", 22, "centre")
