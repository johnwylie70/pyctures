# Three Screens: a game with a title screen, the game, and a game-over screen. Each screen is a scene.
# Use: click or tap to start; move the mouse, or drag a finger, to catch the stars; click to play again.
# Try changing: 15, how long a game lasts; "crossfade" to "wipe" or "slide_left"; 0.4, how long a change takes.
#
# Run it:   pyctures run three_screens.py

score = 0                 # made at the top of the file, so every scene shares it
best = load("best", 0)


class Title(Scene):
    def draw(self):
        background("midnightblue")
        text("Star Basket", width / 2, height / 2 - 20, "gold", 48, "centre")
        text("Click to start", width / 2, height / 2 + 40, "white", 20, "centre")

    def on_mouse_down(self, x, y):
        go("Game", transition="crossfade", transition_time=0.4)


class Game(Scene):
    length = 15               # seconds: then the next scene written, GameOver, begins

    def setup(self):          # called each time the game begins, so every game starts afresh
        global score
        score = 0
        self.basket = Sprite("🧺", width / 2, height - 50, size=64)
        self.stars = [Sprite("⭐", random(width), random(height // 2), size=36) for i in range(5)]

    def update(self, dt):
        global score
        if mouse.inside:
            self.basket.x = mouse.x
        self.basket.y = height - 50
        for star in self.stars:
            star.y += 200 * dt
            caught = star.touches(self.basket)
            if caught:
                score += 1
            if caught or star.y > height:
                star.x = random(width)
                star.y = 0

    def draw(self):
        background("midnightblue")
        for star in self.stars:
            star.draw()
        self.basket.draw()
        text(f"Score {score}", 12, 30, "white", 20, "left")
        rect(0, height - 6, width * (1 - scene_progress), 6, "gold")   # the time that is left


class GameOver(Scene):
    transition = "slide_up"   # how this scene arrives

    def setup(self):
        global best
        if score > best:
            best = score
            save("best", best)

    def draw(self):
        background("#301030")
        text("Time!", width / 2, height / 2 - 40, "white", 48, "centre")
        text(f"You caught {score}. Best {best}", width / 2, height / 2 + 10, "gold", 22, "centre")
        if scene_time > 1:
            text("Click to play again", width / 2, height / 2 + 60, "white", 18, "centre")

    def on_mouse_down(self, x, y):
        if scene_time > 1:
            go("Title", transition="fade")
