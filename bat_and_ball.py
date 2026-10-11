# Bat and Ball: keep the ball out of your goal, and get it past the computer's bat. First to 5 wins.
# Use: up and down move your bat, the left one. Or drag up and down.
# Try changing: 230, the computer's speed (bigger is harder); 90, how tall the bats are; 1.08, how much faster the ball gets with each hit.
#
# Run it:   pyctures run bat_and_ball.py

you = Sprite.box(0, 0, 14, 90)
computer = Sprite.box(0, 0, 14, 90)
ball = Sprite.circle(0, 0, 16)
your_score = 0
computer_score = 0
wait = 0                        # seconds before the ball moves

def new_game():
    global your_score, computer_score
    your_score = 0
    computer_score = 0
    you.y = height / 2
    computer.y = height / 2
    serve(1)

# Put the ball in the middle, moving left (-1) or right (1).
def serve(direction):
    global wait
    ball.x = width / 2
    ball.y = height / 2
    ball.vx = direction * width * 0.45    # a wide court has a faster ball
    ball.vy = random(-150, 150)
    wait = 1

def game_over():
    return your_score == 5 or computer_score == 5

def move_bats(dt):
    if "ArrowUp" in keys: you.y -= 420 * dt
    if "ArrowDown" in keys: you.y += 420 * dt
    if mouse.down: you.y = mouse.y
    # The computer chases the ball, but it is slower than a ball hit off the end of your bat.
    if ball.vx > 0 and ball.y < computer.y - 10: computer.y -= 230 * dt
    if ball.vx > 0 and ball.y > computer.y + 10: computer.y += 230 * dt
    you.x = 30
    computer.x = width - 30
    you.bounce("top", "bottom")           # a bat stops at the edges
    computer.bounce("top", "bottom")

# Send the ball back, a little faster. Where it met the bat decides how steeply it leaves.
def hit_ball(bat, direction):
    ball.vx = direction * abs(ball.vx) * 1.08
    ball.vy = (ball.y - bat.y) * 9
    ball.limit(900)

def update(dt):
    global wait, your_score, computer_score
    if game_over():
        if " " in pressed:
            new_game()
        return
    move_bats(dt)
    wait -= dt
    if wait > 0:
        return
    ball.update(dt)
    ball.bounce("top", "bottom")
    # Only a ball coming towards a bat is sent back, so it can never stick to one.
    if ball.vx < 0 and ball.touches(you): hit_ball(you, 1)
    if ball.vx > 0 and ball.touches(computer): hit_ball(computer, -1)
    if ball.x < 0:
        computer_score += 1
        serve(1)
    if ball.x > width:
        your_score += 1
        serve(-1)

def on_mouse_down(x, y):
    if game_over():
        new_game()

def draw():
    background("black")
    for y in range(10, int(height), 30):
        rect(width / 2 - 2, y, 4, 15, "dimgray")
    you.draw()
    computer.draw()
    ball.draw()
    text(your_score, width / 2 - 60, 60, "white", 48, "centre")
    text(computer_score, width / 2 + 60, 60, "white", 48, "centre")
    if game_over():
        text("You win!" if your_score == 5 else "The computer wins", width / 2, height / 2, "white", 32, "centre")
        text("Tap or press space to play again", width / 2, height / 2 + 40, "white", 18, "centre")

new_game()
