# First Game: stars fall, and you catch them in a basket for a point each.
# Use: move the mouse, or drag a finger, to move the basket.
# Try changing: 200, how fast the stars fall; 5, how many stars there are; the two emoji.
#
# Run it:   pyctures run first_game.py

basket = Sprite("🧺", 200, 250, size=64)
stars = [Sprite("⭐", random(400), random(300), size=36) for i in range(5)]
score = 0

def update(dt):
    global score
    if mouse.inside:                 # the pointer is over the picture
        basket.x = mouse.x
    basket.y = height - 50
    for star in stars:
        star.y += 200 * dt
        caught = star.touches(basket)
        if caught:
            score += 1
        if caught or star.y > height:    # caught or missed: back to the top
            star.x = random(width)
            star.y = 0

def draw():
    background("midnightblue")
    for star in stars:
        star.draw()
    basket.draw()
    text(f"Score {score}", 12, 30, "white", 20)
