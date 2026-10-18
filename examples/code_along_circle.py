# Code-along: a 12 second lesson. A circle is typed in three
# stages, and beside the code is what each stage really draws.
# Same code for a wide video and a tall one: the code goes
# beside the preview, or above it.
# Try changing: the stages; duration; typing_speed.
#
# Run it:   pyctures run code_along_circle.py

# The three stages. Each types only what changed.
stages = [
    {
        "code": """def draw():
    background("navy")""",
    },
    {
        "code": """def draw():
    background("navy")
    x = width / 2
    y = height / 2
    circle(x, y, 80, "gold")""",
    },
    {
        "code": """r = 20

def update(dt):
    global r
    r += 60 * dt

def draw():
    background("navy")
    x = width / 2
    y = height / 2
    circle(x, y, r, "gold")""",
        "hold": 2.5,
    },
]


def draw():
    background(house_style.palette.ink)

    # Points at a line of the code while it is on screen.
    callouts = [
        {"at": 6.4, "line": 3, "text": "half the width", "duration": 2},
    ]

    code_along(stages=stages, start=0, duration=12, callouts=callouts)
