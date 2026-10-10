# Changes

## 0.2.0 (2026-10-10)

Everything written for 0.1.0 still runs. This release adds a quicker way to draw, a fuller way to read the keyboard, mouse and fingers, and sprites that can tell when they touch.

### New

- **Plain drawing functions**, one call each, nothing to import: `background`, `circle`, `ellipse`, `rect`, `triangle`, `polygon`, `star`, `line`, `text` and `picture`. A shape takes its colour as the last argument, and `outline=` and `thickness=` draw its edge. `ctx` is still there for everything else.
- **`random` and `pick`**: `random(1, 6)` is a whole number from 1 to 6, `random()` a fraction from 0 to 1, and `pick(list)` one thing from a list. `degrees(n)` gives an angle in degrees wherever an angle is wanted.
- **Keyboard**: `pressed` and `released` hold the keys that went down and came up since the last frame. `keys.shift`, `keys.ctrl`, `keys.alt` and `keys.meta` say which of those are held, and `keys.codes` holds keys by their place on the keyboard (`"KeyW"`), so WASD works on any layout. `on_key_repeat(key, code)` is called while a key is held.
- **Mouse**: `mouse.button`, `mouse.inside`, `mouse.dx`, `mouse.dy` and `mouse.wheel`, and `on_wheel(amount)`.
- **Touch**: `touches` is every finger that is down, each with where it is, where it began and how far it moved. `pinch` is two fingers as a zoom. `on_touch_start`, `on_touch_move`, `on_touch_end` and `on_pinch` are called as they happen.
- **Sprites that touch**: `sprite.touches(other)`, `sprite.hit(sprites)` and `sprite.contains(x, y)`. `Sprite.box(...)` and `Sprite.circle(...)` make a plain coloured box or circle, tested as the shape you see. `wrap()`, `bounce()`, `offscreen()`, `push()`, `forward()`, `limit()`, `angle_to()` and `distance_to()` move a sprite and aim it. `remove(things, thing)` takes one out of a list.
- **Saved values**: `save("best", 120)` keeps a value for the next time the program runs, and `load("best", 0)` gives it back (numbers, text, `True` or `False`, lists and dictionaries). It is kept in the browser's storage for that scene alone; where there is no storage it still works until the page is closed. See `docs/saved-values.md`.
- **A sprite's picture function can take the size alone**: `def draw_ship(size)`. `(ctx, size)` works as before.
- **Hit tests on their own**: `circles_touch`, `boxes_touch`, `circle_touches_box`, `point_in_circle` and `point_in_box`.
- **`vsync`**: another name for `frame`, for a program written as a loop: `await vsync()`.
- **Eleven more examples**: Hello, Moving, Follow, First Game, Ring, Night Sky, High Score, Space Rocks, Brick Breaker, Bat and Ball and Snake (which keeps its best score). The older examples now use the plain drawing functions where that makes them shorter.
- A new tutorial, Space Rocks, and the README starts with four small scenes that build up to a game.

### Different from 0.1.0

- The new names are there in every scene without importing: `circle`, `rect`, `line`, `text`, `background`, `random`, `pick`, `save`, `load`, `pressed`, `touches` and the rest. A scene that makes its own function or variable with one of those names keeps its own. `random` is also everything Python's own `random` module is, with or without `import random`: `random.choice(...)`, `random.uniform(...)` and `random.random()` work as before.
- A scene that uses the mouse now keeps a drag that leaves the picture, and a right-click in it is the right button, not the browser's menu.
- A scene that names the wheel (`on_wheel`, `mouse.wheel`) or the pinch takes it, so the page does not scroll or zoom under it. Under any other scene the wheel scrolls the page as before.
- When the scene loses the keyboard (you click away, or change window), the keys it thought were held are let go.

## 0.1.0 (2026-10-08)

First release.
