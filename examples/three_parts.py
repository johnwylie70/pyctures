# Three Parts: three scenes on a timer, one after another, with a different change between each.
# Use: watch. Move the pointer over the picture for the scrubber: it has a tick where each part starts.
# Try changing: the three lengths; the transitions ("crossfade", "wipe", "slide_left", "fade", "cut").
#
# Run it:   pyctures run three_parts.py
import math

config(transition_time=0.8)   # for every scene


class Rings(Scene):
    length = 4
    transition = "fade"       # how it arrives, when the last part has ended and this one comes round again

    def draw(self):
        background("#101830")
        for i in range(8):
            size = (scene_time * 60 + i * 50) % 400
            circle(width / 2, height / 2, size, outline=f"hsl({200 + i * 12}, 80%, 60%)", thickness=4)


class Bars(Scene):
    length = 4
    transition = "wipe"

    def draw(self):
        background("#301020")
        n = 16
        for i in range(n):
            tall = (math.sin(scene_time * 3 + i * 0.5) * 0.4 + 0.5) * height
            rect(i * width / n + 2, height - tall, width / n - 4, tall, f"hsl({330 + i * 6}, 80%, 60%)")


class Stars(Scene):
    length = 4
    transition = "slide_left"

    def setup(self):
        self.stars = [[random(), random(), random(0.05, 0.4)] for i in range(80)]

    def update(self, dt):
        for star in self.stars:
            star[0] = (star[0] + star[2] * dt) % 1

    def draw(self):
        background("black")
        for x, y, speed in self.stars:
            circle(x * width, y * height, speed * 6, "white")
        if scene_progress > 0.5:
            section("Half way through the stars")   # a mark of your own on the scrubber
