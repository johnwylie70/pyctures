# Brick Breaker: bounce the ball off your bat and knock out every brick. You have 3 balls.
# Use: left and right move the bat. Or drag left and right.
# Try changing: COLOURS, one for each row of bricks; 100, how wide the bat is; -330, how fast the ball goes up.
#
# Run it:   pyctures run brick_breaker.py

COLOURS = ["tomato", "orange", "gold", "mediumseagreen", "dodgerblue"]   # one for each row

bat = Sprite.box(0, 0, 100, 14)
ball = Sprite.circle(0, 0, 14)
bricks = []
score = 0
lives = 3
wait = 0                        # seconds before the ball moves

# Five rows of eight bricks, which fill the width of the picture.
def build_wall():
    bricks.clear()
    across = width / 8
    for row in range(5):
        for column in range(8):
            bricks.append(Sprite.box(across * (column + 0.5), 70 + row * 26, across - 6, 20, COLOURS[row]))

def new_game():
    global score, lives
    score = 0
    lives = 3
    build_wall()
    bat.x = width / 2
    serve()

# Put the ball above the bat, going up.
def serve():
    global wait
    ball.x = bat.x
    ball.y = height - 80
    ball.vx = 165
    ball.vy = -330
    wait = 1

def game_over():
    return lives == 0 or not bricks

def update(dt):
    global wait, score, lives
    if game_over():
        if " " in pressed:
            new_game()
        return
    if "ArrowLeft" in keys: bat.x -= 520 * dt
    if "ArrowRight" in keys: bat.x += 520 * dt
    if mouse.down: bat.x = mouse.x
    bat.y = height - 40
    bat.bounce("left", "right")           # the bat stops at the sides
    wait -= dt
    if wait > 0:
        ball.x = bat.x                    # the ball waits on the bat
        return
    ball.update(dt)
    ball.bounce("left", "right", "top")
    # Off the bat the ball goes up, and further sideways the nearer the end it met.
    if ball.vy > 0 and ball.touches(bat):
        ball.vy = -ball.vy
        ball.vx = (ball.x - bat.x) * 7
    brick = ball.hit(bricks)
    if brick:
        remove(bricks, brick)
        ball.vy = -ball.vy
        score += 1
    if ball.y > height:
        lives -= 1
        serve()

def on_mouse_down(x, y):
    if game_over():
        new_game()

def draw():
    background("midnightblue")
    for brick in bricks:
        brick.draw()
    bat.draw()
    ball.draw()
    text(f"Score {score}   Balls {lives}", 12, 30, "white", 20, "left")
    if game_over():
        text("Game over" if lives == 0 else "You win!", width / 2, height / 2, "white", 32, "centre")
        text("Tap or press space to play again", width / 2, height / 2 + 40, "white", 18, "centre")

new_game()
