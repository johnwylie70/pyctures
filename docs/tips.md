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

If a program does get stuck, the canvas stays blank or stops changing (when `draw()` or `update()` is the one stuck, the page also says so after three seconds). To free it:

- **With `pyctures run`**, add the missing `await frame()` and save: the stuck Python is stopped and the scene runs again. `Ctrl+C` in the terminal stops everything.
- **In a built page**, Python runs inside the browser tab, so a loop that never waits holds the whole tab. Close or reload the tab, then fix the loop.

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

## Libraries

You can `import` the usual Python libraries. With `pyctures run`, your scene runs in your own Python, so anything you have installed with `pip` works. In a built page, it runs on Pyodide, the Python inside the browser, which has a large set of common libraries (numpy, pandas, Pillow and many more) and loads them the first time a scene imports them; libraries that need things a browser cannot do (opening network sockets, starting programs) do not work there. Numbers from numpy can be passed straight to drawing calls.

## Related

- [How a program is shaped](program-shape.md)
- [Finding mistakes](finding-mistakes.md)
- [Use it on your website](website.md)
