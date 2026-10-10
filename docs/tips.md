# Tips and Limits

Full reference: [www.circuitry.dev/docs/pyctures/tips](https://www.circuitry.dev/docs/pyctures/tips) (in Circuitry Studio's help)

A few things that are good to know once your programs grow: what keeps them fast, what makes a canvas freeze, and why a drawing can disappear.

## Keep reads rare

Your drawing calls are sent to the canvas in one batch per frame, which is what makes them fast. Reading a value back with `await` is different: the program has to wait for the canvas to answer, which takes a whole frame.

- Read once at the start, or when something happens (a click), not every frame.
- **Keep the numbers you need in Python.** Track a sprite's position, a cube's angle or a score in your own variables, change them in `update()`, and set them on the canvas. You then always know them without asking.
- A value you set from Python (`mesh.position.x = 2`) is remembered, so reading it straight back needs no `await`. A value worked out in the page (after `mesh.position.x += 0.1`, or anything three.js changes by itself) needs `await`.
- Using a canvas value as if it were a Python number, as in `if mesh.position.x > 3:`, stops with an error that tells you to read it with `await`.

## Canvas frozen? A loop must wait for the next frame

The canvas draws between frames. A loop that runs forever without waiting never gives it the chance, and the canvas looks frozen:

```python
# The canvas freezes: this loop never waits.
x = 0
while True:
    x += 1
    ctx.fill_rect(x % width, 50, 10, 10)
```

Put `await frame()` at the end of the loop, and each pass becomes one frame:

```python
x = 0
while True:
    ctx.fill_style = "white"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "black"
    ctx.fill_rect(x % width, 50, 10, 10)
    x += 2
    await frame()
```

Or use `update()` and `draw()`, which can never freeze the canvas this way.

If a program does get stuck, the canvas stays blank or stops changing, and after three seconds the page says so. To free it:

- **With `pyctures run`**, add the missing `await frame()` and save: the stuck Python is stopped and the scene runs again. `Ctrl+C` in the terminal stops everything.
- **In a built page**, Python runs in a background thread, so the page itself keeps working. Press **Stop** on the message, fix the loop, and build again.

## Starting and stopping

With `pyctures run`, and on a page you build, a scene starts as soon as the page opens, and starts again each time you save the file. It runs until you close the page, or press the Stop button the page shows. On a web page with several scenes, a scene that is scrolled out of view waits until it is in view again.

In [Circuitry Studio](https://www.circuitry.dev) a scene starts by itself when its tab comes on screen, and the footer has Run and Stop; a scene also starts over a moment after you stop typing. To make a file wait for Run there, put this comment near the top, within the first 30 lines:

```python
# pyctures: manual
def draw():
    background("navy")
```

Outside Circuitry Studio the line is only a comment, and does nothing.

## When the canvas changes size

The canvas follows the size of the window, or of the box it sits in on a web page. It changes size when you resize the window, rotate a tablet or turn a phone.

- A drawing made once, at the top level, is kept. It stays the size it was drawn, so run it again (save the file, or reload the page) to fit the new size.
- A program with `draw()` redraws every frame using the new `width` and `height`.
- 3D scenes are refitted to the new size automatically, as long as you call `renderer.render(...)` in `draw()`.

## Paint your own background

The canvas's own background is near-black. Start `draw()` by painting your own background (`ctx.fill_rect(0, 0, width, height)`, or `scene.background` in 3D), so your picture looks the way you meant it. On a web page you can change the colour behind a scene with `data-pyctures-background` (see [Use it on your website](website.md)).

## Fit any screen

The canvas can be a tall, narrow phone or a wide desktop window. Work out positions from `width` and `height` (`width / 2` for the middle, `height - 50` for near the bottom) rather than fixed numbers, and read them inside `draw()` and `update()` so they follow a resize.

## Speed

- Most devices draw 60 frames a second, and some 120. Add `?measure=1` to the page's address to see yours ([Finding mistakes](finding-mistakes.md#the-frame-rate)).
- Move things by `speed * dt` in `update(dt)`, so they move at the same speed whatever the frame rate.
- Thousands of shapes a frame are fine. For tens of thousands, draw fewer, bigger things, or join lines into one path and stroke it once. In 3D, one `Points` object with thousands of positions is far quicker than thousands of separate meshes.
- Do heavy Python work once, at the start, and keep the results.

## Keyboard focus

When a scene fills the page, key presses go straight to it. On a web page with other things on it, key presses go to a scene only after you click or tap it, so the page's own keys (scrolling with the arrows, typing in a box) keep working. If the arrow keys do nothing, click the scene first.

A key's name is what the key types, so with Shift held the A key is `"A"`, not `"a"`. A game that uses letter keys can check both: `"a" in keys or "A" in keys`. Or ask for the key by its place on the keyboard, which Shift and the keyboard's language do not change: `"KeyA" in keys.codes`.

To ask whether Shift, Control, Alt or Command is held, read `keys.shift`, `keys.ctrl`, `keys.alt` and `keys.meta`.

For something that should happen once for each press, such as a jump or a shot, use `" " in pressed` in `update`, or the function `on_key_down`. `" " in keys` stays true for as long as the key is held. See [Once for each press](program-shape.md#once-for-each-press-pressed-and-released).

## Fingers, the wheel and zooming

- **More than one finger.** `mouse` follows the first finger only. `touches` has every finger that is down, and a pressed mouse button too. See [Every finger](program-shape.md#every-finger-touches).
- **Zoom.** Multiply by `pinch.change` every frame for two fingers or a trackpad, and read `mouse.wheel` for the mouse wheel. See [Zooming](program-shape.md#zooming-pinch-and-the-wheel).
- **The wheel belongs to the page** unless the scene names it. A scene that reads `mouse.wheel` or defines `on_wheel` keeps the wheel while the pointer is over it.
- **Movement since the last frame.** `mouse.dx`, `mouse.dy`, `mouse.wheel`, `pinch.change`, `pressed` and `released` are set at the start of a frame and are back to nothing at the start of the next. Read them every frame, in `update` or in your loop.
- **Reading them costs nothing.** The page tells Python what happened with each frame, so `mouse.x` or `touches` is an ordinary value: no `await`, and no frame spent.
- **You do not need `add_event_listener` for these.** A listener of your own still works, for anything this list does not cover.

## Libraries

You can `import` the usual Python libraries. With `pyctures run`, your scene runs in your own Python, so anything you have installed with `pip` works. In a built page, it runs on Pyodide, the Python inside the browser, which has a large set of common libraries (numpy, pandas, Pillow and many more) and loads them the first time a scene imports them; libraries that need things a browser cannot do (opening network sockets, starting programs) do not work there. Numbers from numpy can be passed straight to drawing calls.

## Related

- [How a program is shaped](program-shape.md)
- [Finding mistakes](finding-mistakes.md)
- [Use it on your website](website.md)
