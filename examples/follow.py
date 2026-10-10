# Follow: a circle you move.
# Use: the left and right arrow keys, or hold the mouse button or a finger on the picture. Click it first, so it has the keyboard.
# Try changing: 300, its speed; 40, its size.
#
# Run it:   pyctures run follow.py

x, y = 200, 150

def update(dt):
    global x, y
    if "ArrowLeft" in keys: x -= 300 * dt
    if "ArrowRight" in keys: x += 300 * dt
    if mouse.down:           # a mouse button, or a finger
        x, y = mouse.x, mouse.y

def draw():
    background("midnightblue")
    circle(x, y, 40, "gold")
