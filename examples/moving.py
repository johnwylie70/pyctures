# Moving: a circle that crosses the picture, again and again.
# Try changing: 200, its speed; 40, its size.
#
# Run it:   pyctures run moving.py

x = 0

def update(dt):
    global x
    x += 200 * dt            # 200 points every second
    if x > width:            # off the right edge: start again on the left
        x = 0

def draw():
    background("midnightblue")
    circle(x, height / 2, 40, "gold")
