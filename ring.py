# Ring: twelve circles of different colours in a ring.
# Try changing: 12, how many circles; 120, how wide the ring is; 20, the size of each circle.
#
# Run it:   pyctures run ring.py

import math

def draw():
    background("midnightblue")
    for i in range(12):
        x = width / 2 + 120 * math.cos(i / 1.91)
        y = height / 2 + 120 * math.sin(i / 1.91)
        circle(x, y, 20, f"hsl({i * 30}, 80%, 60%)")
