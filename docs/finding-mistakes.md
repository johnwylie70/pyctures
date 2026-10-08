# Finding Mistakes

Full reference: [www.circuitry.dev/docs/pyctures/debugging](https://www.circuitry.dev/docs/pyctures/debugging) (in Circuitry Studio's help)

When a drawing program does something you did not expect, read its errors and printed output, and check how fast it runs. This page covers each of them.

## Errors: read them, then tap them

When your program stops with an error, the page shows it over the scene, with the line it happened on and the lines around it:

```text
Traceback (most recent call last):
  line 14, in update
NameError: name 'speed' is not defined
```

With `pyctures run`, the error is also printed in the terminal, with the file's name. Fix the line and save, and the scene runs again. In a built page, press **Run again**.

A mistake in a drawing call, such as a misspelt name (`ctx.fil_rect`), is reported the same way, with the line in your file that made it:

```text
line 6: TypeError: ctx has no method "fil_rect"
```

## Printing

`print()` works as usual. With `pyctures run`, what you print appears at the bottom of the page and in the terminal; in a built page or on your website, it goes to the browser's console (open the browser's developer tools to see it). It is the quickest way to see a value:

```python
score = 0

def update(dt):
    global score
    score += 1
    if score % 60 == 0:
        print("score is", score)

def draw():
    ctx.fill_style = "black"
    ctx.fill_rect(0, 0, width, height)
```

Print now and then, as above, rather than every frame: sixty lines a second is hard to read.

## The frame rate

Add `?measure=1` to the page's address (for example `http://localhost:8765/?measure=1`, or `game.html?measure=1` for a built page). A small box in the corner of the scene then shows, every second:

| Line | What it means |
|---|---|
| `60 fps` | Frames shown in the last second. Most screens show 60 frames a second, and some 120. |
| `missed 0` | Screen refreshes that showed no new frame. Zero is smooth; a few now and then is a small stutter. |
| `longest 17 ms` | The longest time between two screen refreshes. At 60 frames a second, 17 ms is normal. |
| `python 0.5 ms` | Time spent in Python for one frame (your `update` and `draw`, and the rest). |
| `round trip 0.8 ms` | From asking Python for a frame to having it back. |
| `draw 0.1 ms` | Time spent drawing the frame in the page. |
| `queued 2` | Frames ready and waiting for a screen refresh (at most 2). |

The last line says where Python is running. The same numbers go to the browser's console, with your `update` and `draw` timed separately. Wrap a slow part of your own in `with measure("physics"):` and it is timed too. On a scene placed on your own web page, put `data-pyctures-measure` on its `<div>` instead.

If the number drops, your program is doing more each frame than the device can keep up with. The usual causes:

- **Reading values back with `await` every frame.** Each read waits a whole frame. Keep your numbers in Python instead (see [Tips and limits](tips.md)).
- **Very many separate drawing calls.** Thousands of shapes a frame is fine; tens of thousands is slow. Draw fewer, bigger things, or join many lines into one path and `stroke()` it once.
- **Heavy Python work every frame.** Work things out once at the start and keep the results.

## When the canvas is frozen or stops moving

If the canvas stays blank or stops changing, the program is usually stuck. When Python has not finished a frame for three seconds, the page says so; a built page also offers a **Stop** button. The usual cause is a `while True:` loop that never waits: every loop that runs forever must `await frame()` (or `await sleep(...)`) inside it. See [Tips and limits](tips.md#canvas-frozen-a-loop-must-wait-for-the-next-frame) for how to free it.

## Related

- [How a program is shaped](program-shape.md)
- [Tips and limits](tips.md)
