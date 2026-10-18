# Two Faces: click, and two faces talk to each other.
# Each face has a voice of its own, one low and one high.
# The voices are your device's own: you hear them, but they
# are not recorded if you make a video.
# Try changing: the words; the voices to "robot", "slow" or
# "squeaky"; the colours.
#
# Run it:   pyctures run two_faces.py

# Two speakers, each with a voice.
sam = speaker(voice="deep")
pip = speaker(voice="squeaky")

# Who says what. The lines wait for each other.
script = [
    (sam, "Hello Pip! Guess what I had for breakfast?"),
    (pip, "Um... pancakes?"),
    (sam, "Nope. A whole bowl of socks!"),
    (pip, "Socks? That is silly! Did they taste good?"),
    (sam, "They were a little bit stinky."),
    (pip, "Ha ha ha! Tomorrow I will eat a hat."),
    (sam, "Great! I will bring the ketchup."),
]

# True while they are talking.
busy = False

# A click starts the talk. Click again when it is over.
async def on_mouse_down(x, y):
    global busy
    if busy:
        return
    busy = True
    end = 0
    for who, words in script:
        end = who.say_at(words)["end"]
    await sleep(end + 0.5)
    busy = False

# One face: it bounces and glows while it talks.
def face(x, y, r, who, color, eyes):
    top = y - who.level() * r * 0.2
    if who.speaking():
        circle(x, top, r * 1.15, "rgba(255, 255, 255, 0.3)")
    circle(x, top, r, color)

    # The eyes.
    gap = r * 0.35
    circle(x - gap, top - r * 0.25, eyes, "white")
    circle(x + gap, top - r * 0.25, eyes, "white")
    circle(x - gap, top - r * 0.25, eyes / 2.5, "black")
    circle(x + gap, top - r * 0.25, eyes / 2.5, "black")

    # The mouth opens only for this face's voice.
    mouth(x, top + r * 0.4, size=r * 0.7, style="oval",
      color="black", speaker=who)

def draw():
    background("midnightblue")

    # Side by side if wide, one above the other if tall.
    wide = width > height
    if wide:
        r = min(height * 0.3, width * 0.2)
        one = (width * 0.27, height / 2)
        two = (width * 0.73, height / 2)
    else:
        r = min(width * 0.28, height * 0.14)
        one = (width / 2, height * 0.3)
        two = (width / 2, height * 0.68)

    face(*one, r, sam, "gold", r * 0.12)
    face(*two, r, pip, "hotpink", r * 0.2)

    if not busy:
        text("Click to start", width / 2, height - 30,
          "white", height / 40, "centre")
