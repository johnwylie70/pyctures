# Tutorial: A Simple Game

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/game](https://www.circuitry.dev/docs/pyctures/tutorials/game) (in Circuitry Studio's help)

Build a catching game in three steps: a basket you move with the arrow keys or your finger, stars that fall from the sky for you to catch, and then a score, lives and a game over screen. Each step is a whole program you can run.

The game uses sprites: pictures that move. Here every picture is an emoji, so there is nothing to download. See [Sprites](../drawing-2d.md#sprites) for everything a sprite can do.

## Step 1: a player you can move

```python
player = Sprite("🧺", 200, 300, size=56)
speed = 350          # points per second

def update(dt):
    # arrow keys
    if "ArrowLeft" in keys:
        player.x -= speed * dt
    if "ArrowRight" in keys:
        player.x += speed * dt
    # a finger or the mouse: glide towards it
    if mouse.down:
        player.x += (mouse.x - player.x) * 0.25
    # stay on the screen, near the bottom
    player.x = min(max(player.x, 30), width - 30)
    player.y = height - 50

def draw():
    ctx.fill_style = "#0b1026"
    ctx.fill_rect(0, 0, width, height)
    player.draw()
```

Run it, then click the canvas so it has the keyboard, and press the left and right arrow keys. On a phone or tablet, put a finger on the canvas and slide it.

- `keys` holds the keys that are down right now, so holding an arrow keeps the basket moving.
- `mouse.down` is `True` while a finger or the mouse button is pressed, and `mouse.x` is where. Moving a quarter of the way there each frame makes the basket glide rather than jump.
- `min(max(...))` keeps the basket from leaving the screen. `player.y` follows the bottom edge, so it stays put if the canvas is resized.

## Step 2: falling stars to catch

Add a list of stars. Each frame they fall a little; when one reaches the bottom, or touches the basket, it goes back to the top at a random place.

```python
player = Sprite("🧺", 200, 300, size=56)
speed = 350
score = 0

def new_star():
    star = Sprite("⭐", random(20, width - 20), random(-300, -20), size=36)
    star.vy = random(100, 220)      # its falling speed
    return star

stars = [new_star() for _ in range(5)]

def update(dt):
    global score
    if "ArrowLeft" in keys:
        player.x -= speed * dt
    if "ArrowRight" in keys:
        player.x += speed * dt
    if mouse.down:
        player.x += (mouse.x - player.x) * 0.25
    player.x = min(max(player.x, 30), width - 30)
    player.y = height - 50

    for i, star in enumerate(stars):
        star.update(dt)                     # moves it by its speed
        star.angle += dt                    # and spins it slowly
        if star.touches(player):
            score += 1
            stars[i] = new_star()
        elif star.y > height + 20:
            stars[i] = new_star()

def draw():
    ctx.fill_style = "#0b1026"
    ctx.fill_rect(0, 0, width, height)
    for star in stars:
        star.draw()
    player.draw()
    ctx.fill_style = "white"
    ctx.font = "bold 22px sans-serif"
    ctx.fill_text(f"Score: {score}", 14, 32)
```

- `star.vy` is the star's speed downwards. `star.update(dt)` moves it by that speed every frame.
- `star.touches(player)` is `True` when the two pictures overlap.
- `global score` lets `update` change the score made at the top of the file.

## Step 3: lives, bombs and game over

Now some things are dangerous: a bomb costs a life, and so does a star you miss. With no lives left, the game stops and waits for a tap, or the space bar, to start again.

```python
player = Sprite("🧺", 200, 300, size=56)
speed = 350

def new_thing():
    picture = pick(["💣", "⭐", "⭐", "⭐"])
    thing = Sprite(picture, random(20, width - 20), random(-300, -20), size=36)
    thing.vy = random(100, 220) + score * 4     # faster as you score
    return thing

def start():
    global score, lives, playing, things
    score, lives, playing = 0, 3, True
    things = [new_thing() for _ in range(6)]

start()

def on_key_down(key):
    if key == " " and not playing:
        start()

def on_mouse_down(x, y):
    if not playing:
        start()

def update(dt):
    global score, lives, playing
    if not playing:
        return
    if "ArrowLeft" in keys:
        player.x -= speed * dt
    if "ArrowRight" in keys:
        player.x += speed * dt
    if mouse.down:
        player.x += (mouse.x - player.x) * 0.25
    player.x = min(max(player.x, 30), width - 30)
    player.y = height - 50

    for i, thing in enumerate(things):
        thing.update(dt)
        if thing.touches(player):
            if thing.picture == "💣":
                lives -= 1
            else:
                score += 1
            things[i] = new_thing()
        elif thing.y > height + 20:
            if thing.picture == "⭐":
                lives -= 1                  # a missed star costs a life
            things[i] = new_thing()
    if lives <= 0:
        playing = False

def draw():
    ctx.fill_style = "#0b1026"
    ctx.fill_rect(0, 0, width, height)
    for thing in things:
        thing.draw()
    player.draw()

    ctx.fill_style = "white"
    ctx.font = "bold 22px sans-serif"
    ctx.text_align = "left"
    ctx.fill_text(f"Score: {score}", 14, 32)
    ctx.text_align = "right"
    ctx.fill_text("❤️" * lives, width - 14, 32)

    if not playing:
        ctx.fill_style = "rgba(0, 0, 0, 0.6)"
        ctx.fill_rect(0, 0, width, height)
        ctx.fill_style = "white"
        ctx.text_align = "center"
        ctx.font = "bold 44px sans-serif"
        ctx.fill_text("Game over", width / 2, height / 2 - 10)
        ctx.font = "20px sans-serif"
        ctx.fill_text(f"You caught {score} stars.", width / 2, height / 2 + 30)
        ctx.fill_text("Tap or press space to play again.", width / 2, height / 2 + 58)
```

What changed:

- `start()` sets everything up, so the same function starts the first game and every game after.
- `playing` says whether the game is on. When it is `False`, `update` does nothing and `draw` shows the game over screen on top.
- `on_key_down` and `on_mouse_down` are called once per press, which suits "press to restart". Moving uses `keys` and `mouse`, which say what is held down right now.
- `"❤️" * lives` repeats the heart once for each life.

## Make it yours

- Use your own pictures: `Sprite(load_image("https://…/basket.png"), ...)` works the same as an emoji.
- Add a power-up, such as a 🍀 that gives back a life.
- Ask one question in place of a loop: `thing = player.hit(things)` gives the first thing the basket touches, or `None`.
- Add a high score: keep the best `score` in a variable that `start()` does not reset.
- Add `?measure=1` to the page's address to see how smoothly it runs.

## Related

- [Drawing in 2D: sprites](../drawing-2d.md#sprites)
- [How a program is shaped: keyboard, mouse and touch](../program-shape.md#keyboard-mouse-and-touch-input)
- [Finding mistakes](../finding-mistakes.md): errors, printing and speed
- Next: [Space Rocks](space-rocks.md), a game with sprites you draw yourself
