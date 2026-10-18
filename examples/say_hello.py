# Say Hello: click the face and the computer talks.
# The voice is your device's own: you hear it, but it is not
# recorded if you make a video.
# Try changing: the words; the mouth to style="smile" or "robot".
#
# Run it:   pyctures run say_hello.py

# A click makes it talk.
def on_mouse_down(x, y):
    say("Hello! I am talking.")

def draw():
    background("midnightblue")

    # The face, as big as the screen allows.
    r = min(width, height) * 0.3
    circle(width / 2, height / 2, r, "gold")
    circle(width / 2 - r / 3, height / 2 - r / 4, r / 11, "black")
    circle(width / 2 + r / 3, height / 2 - r / 4, r / 11, "black")

    # The mouth opens as the voice gets louder.
    mouth(width / 2, height / 2 + r / 3)

    text("Click the face", width / 2, height - 30,
      "white", 20, "centre")
