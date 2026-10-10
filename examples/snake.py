# Snake: eat the apples and grow, without running into a wall or yourself. It is played on a grid of squares, and your best score is kept.
# Use: the arrow keys turn the snake. Or tap the side of its head you want it to turn to.
# Try changing: SQUARE, the size of a square; 0.15, the seconds between steps (smaller is faster); the colours in draw().
#
# Run it:   pyctures run snake.py

SQUARE = 24                     # the size of one square of the grid

columns = 0
rows = 0
snake = []                      # its squares, the head first: (x, y)
apple = (0, 0)
going = (1, 0)                  # one square right each step
turn = going                    # the turn asked for, taken at the next step
timer = 0
score = 0
best = load("best", 0)          # the best score saved last time, or 0 the first time
alive = True
waiting = True                  # nothing moves until the first key or tap

def new_game():
    global columns, rows, snake, going, turn, score, alive, waiting
    columns = int(width // SQUARE)
    rows = int(height // SQUARE)
    y = rows // 2
    snake = [(4, y), (3, y), (2, y)]
    going = (1, 0)
    turn = going
    score = 0
    alive = True
    waiting = True
    move_apple()

# Try squares until one is free.
def move_apple():
    global apple
    apple = (random(columns - 1), random(rows - 1))
    if apple in snake:
        move_apple()

# Turn, unless that would send the snake straight back into itself.
def turn_to(x, y):
    global turn
    if (x, y) != (-going[0], -going[1]):
        turn = (x, y)

def on_key_down(key):
    global waiting
    if key == "ArrowLeft": turn_to(-1, 0)
    if key == "ArrowRight": turn_to(1, 0)
    if key == "ArrowUp": turn_to(0, -1)
    if key == "ArrowDown": turn_to(0, 1)
    if key.startswith("Arrow"): waiting = False
    if key == " " and not alive: new_game()

def on_mouse_down(x, y):
    global waiting
    if not alive:
        new_game()
        return
    waiting = False
    # How far the tap is from the middle of the head, across and down.
    across = x - (snake[0][0] + 0.5) * SQUARE
    down = y - (snake[0][1] + 0.5) * SQUARE
    if abs(across) > abs(down):
        turn_to(1 if across > 0 else -1, 0)
    else:
        turn_to(0, 1 if down > 0 else -1)

def step():
    global going, alive, score, best
    going = turn
    head = (snake[0][0] + going[0], snake[0][1] + going[1])
    outside = head[0] < 0 or head[1] < 0 or head[0] >= columns or head[1] >= rows
    if outside or head in snake:
        alive = False
        if score > best:
            best = score
            save("best", best)  # still there the next time you play
        return
    snake.insert(0, head)       # a new head at the front
    if head == apple:
        score += 1
        move_apple()
    else:
        snake.pop()             # and the tail moves up, unless it has just eaten

def update(dt):
    global timer
    if not alive or waiting:
        return
    timer += dt
    if timer >= 0.15:           # a step every 0.15 seconds: smaller is faster
        timer = 0
        step()

def square(x, y, colour):
    rect(x * SQUARE + 1, y * SQUARE + 1, SQUARE - 2, SQUARE - 2, colour, round=5)

def draw():
    background("dimgray")
    rect(0, 0, columns * SQUARE, rows * SQUARE, "midnightblue")
    square(apple[0], apple[1], "tomato")
    for x, y in snake:
        square(x, y, "mediumseagreen")
    square(snake[0][0], snake[0][1], "palegreen")
    text(f"Score {score}", 12, 30, "white", 20, "left")
    text(f"Best {best}", width - 12, 30, "gold", 20, "right")
    if waiting:
        text("Press an arrow key or tap to start", width / 2, height / 2 + 60, "white", 18, "centre")
    if not alive:
        text("Game over", width / 2, height / 2, "white", 32, "centre")
        text("Tap or press space to play again", width / 2, height / 2 + 40, "white", 18, "centre")

new_game()
