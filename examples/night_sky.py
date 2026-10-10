# Night Sky: stars, a moon, a hill and a house, drawn with the plain drawing functions alone.
# Try changing: 70, how many stars; the moon to another emoji; "sienna" and "maroon", the colours of the house.
#
# Run it:   pyctures run night_sky.py
# Share it: pyctures build night_sky.py -o site/

# The stars are placed once, by chance, and kept in a list.
# random() is a fraction from 0 to 1: how far across, and how far down.
stars = []
for i in range(70):
    stars.append((random(), random(), random(2, 6), pick(["white", "lightyellow", "lightblue"])))

def draw():
    background("midnightblue")
    for across, down, size, colour in stars:
        star(across * width, down * height * 0.7, size, 5, colour)
    picture("🌙", width - 90, 80, 70)

    # a hill: the top of a very wide oval
    ellipse(width / 2, height, width * 1.4, 220, "darkgreen")

    # a house on the hill
    ground = height - 90
    x = width / 2 - 60                      # the left edge of the house
    rect(x, ground - 80, 120, 80, "sienna")
    triangle(x - 15, ground - 80, x + 60, ground - 140, x + 135, ground - 80, "maroon")
    rect(x + 48, ground - 45, 24, 45, "saddlebrown", round=4)
    rect(x + 14, ground - 62, 26, 24, "gold", outline="black", thickness=2)
    rect(x + 80, ground - 62, 26, 24, "gold", outline="black", thickness=2)
    circle(x + 67, ground - 22, 2, "gold")

    text("Good night", width / 2, 44, "white", 28, "centre")
