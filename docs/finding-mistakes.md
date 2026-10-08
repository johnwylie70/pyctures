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

Add `?measure=1` to the page's address (for example `http://localhost:8765/?measure=1`) and, every second, the browser's console shows how many frames the scene drew and where each frame's time went: in your `update` and `draw`, in Python as a whole, and in drawing in the page. Wrap a slow part of your own in `with measure("physics"):` and it is timed too. Most screens show 60 frames a second, and some 120.

If the number drops, your program is doing more each frame than the device can keep up with. The usual causes:

- **Reading values back with `await` every frame.** Each read waits a whole frame. Keep your numbers in Python instead (see [Tips and limits](tips.md)).
- **Very many separate drawing calls.** Thousands of shapes a frame is fine; tens of thousands is slow. Draw fewer, bigger things, or join many lines into one path and `stroke()` it once.
- **Heavy Python work every frame.** Work things out once at the start and keep the results.

## When the canvas is frozen or stops moving

If the canvas stays blank or stops changing, the program is usually stuck. When `draw()` or `update()` has not finished for three seconds, the page says so; a loop at the top of the file that never waits just leaves the canvas blank. The usual cause is a `while True:` loop that never waits: every loop that runs forever must `await frame()` (or `await sleep(...)`) inside it. See [Tips and limits](tips.md#canvas-frozen-a-loop-must-wait-for-the-next-frame) for how to free it.

## Related

- [How a program is shaped](program-shape.md)
- [Tips and limits](tips.md)
