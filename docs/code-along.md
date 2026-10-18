# Code-along

Code typed on one side, and on the other side what that code really draws, for each stage of the typing. It is for a tutorial video, a lesson or a demo: the picture is never faked, so if the code is wrong the picture is wrong, and you see it.

```python
stages = [
    {"code": """def draw():
    background("navy")"""},
    {"code": """def draw():
    background("navy")
    circle(width / 2, height / 2, 80, "gold")"""},
]


def draw():
    background(house_style.palette.ink)
    code_along(stages=stages, duration=8)
```

Stage 1 is typed from an empty editor. Stage 2 types only what changed (the new `circle` line) and the lines that were already right stay where they are. When a stage is typed the preview on the right runs it, and the new lines are lit on the left. The same call works in a wide frame (1920 by 1080, code on the left) and a tall one (1080 by 1920, code above the preview): it is laid out from the size of the scene.

Nothing to import. The part that does this is loaded only by a scene that uses one of its names (it takes its colours from the [kinetic text](kinetic-text.md), which is loaded with it). See the example `code_along_circle.py`. It is the same library as [pictures.js's](https://www.circuitry.dev/pictures), so the same call draws the same pixels in both.

## Stages

A stage is `{"code": ..., "language": ..., "hold": ...}`, and a string is a stage of its own.

| Key | Meaning |
|---|---|
| `code` | The text of the editor after this stage |
| `language` | `"python"` (the default here) or `"javascript"`: what the colours are for, and who runs the preview |
| `hold` | Seconds the finished stage stays before the next one is typed (1.5) |
| `at`, `type_at`, `type_time` | When this stage's typing begins, to match a voice-over: `at` in seconds into the beat, `type_at` as a share (0 to 1) of `duration`; `type_time` is how many seconds the typing takes. A stage with no time follows the one before it |

Between two stages the editor does what a person does: the lines both have stay, each run of lines that differ is a place to type, and in a line that changes only the part that differs is typed again. The old text stays until the cursor gets there.

## Options

All of them but `stages` are optional.

| Option | Meaning |
|---|---|
| `start` | Seconds into the scene when the beat begins (0). Before that nothing is drawn |
| `duration` | Seconds the whole beat takes. Typing is made faster (or the holds shorter) to fit, and the holds longer when there is time to spare. Left out, it is the natural time |
| `typing_speed` | Characters a second (22), before it is fitted to `duration` |
| `layout` | `"auto"`: code beside the preview in a wide frame, above it in a tall one. Or `"side"` or `"stack"` |
| `x`, `y`, `w`, `h` | The box, in pixels. The safe area of the frame by default |
| `style` | A voice of `house_style` (`"techy"`), or a dict that changes one. Its accent lights the changed lines, the cursor and the callouts |
| `run` | `True` (the default): the preview runs each stage. `False`: only the code, in the whole box |
| `live` | `False` (the default): the preview changes when a stage is fully typed. `True`: it runs the typed text whenever that is a program, for a live-coding feel (a Python stage; for a JavaScript one the page does it) |
| `font_scale` | 1. The text is never smaller than 3 percent of the frame's height; a smaller scale is raised to that |
| `callouts` | `[{"at": 6.4, "line": 3, "text": "half the width", "duration": 2}]`: a label with an arrow at a line of the code, `at` seconds into the beat |
| `t` | The time to draw at. Left out, it is the scene's own seconds, `kinetic_time()` |
| `hold` | `hold=False` takes the whole thing away when the beat ends |
| `seed` | Changes the typing's unevenness (1) |
| `preview_pad` | Pixels the stage's box is set in from the preview's edges (4 percent of its smaller side) |
| `demo_voice` | `False`. `True` makes the mouth in a stage talk (see below) |

## The preview

A **Python stage** is run here, by Python, in a namespace of its own: the drawing functions and the rest of what a scene is given, its own `width` and `height` (the preview's, not the frame's), and its own `setup()`, `update(dt)` and `draw()`. What it draws is clipped to the preview, and the box the stage sees is set in from the edge, so a ball at `x = 40` is whole on the first frame. `update(dt)` is called with a fixed 1/60 of a second from 0 up to the stage's own time, so a ball that moves is in the same place whenever you ask. `import random` in a stage gives a seeded `random`, the same every time, and the scene's own is put back after.

A **JavaScript stage** (`"language": "javascript"`) is run by the page, which gives it `background`, `circle`, `rect`, `ellipse`, `triangle`, `polygon`, `star`, `line`, `text`, `picture`, `random`, `pick` and `degrees`, and `width` and `height`; it has no sound or controls.

A stage that raises shows its message in the preview, and is in `warnings`. Before stage 1 is typed there is nothing to show yet, and while a stage is typed the preview keeps showing the one before it.

`code_along()` gives back a dict of what Python knows (`progress`, `stage`, `phase`, `typed`, `preview`, `box`, `warnings`), or `None` before it starts. It does not see what the page worked out, which is a part of `warnings` only in pictures.js (the page's own message about a JavaScript stage that raised).

## Voice in a preview

A stage that calls `say("Hello!")` never speaks in the preview: the beat's voice-over owns the sound. `say()` gives back how long the line would take. `mouth(x, y)` in a preview is a sixth of the preview's smaller side across and stays shut, unless the call has `demo_voice=True`: then it talks from a made-up level for the stage's last `say()` (a simple one here; pictures.js uses the draft voice's own).

## Readable

Code in a video is read on a phone, so it is larger than anyone codes, and the code-along never shrinks it to make it fit.

- **Size.** The text is 3 percent of the frame's height or more. In 1920 by 1080 that is 37 pixels, in 1080 by 1920 it is 58.
- **Line length.** About 60 characters a line is the budget in a wide frame and 34 in a tall one, and what really fits is less: about 43 and 23. A line that does not fit is wrapped after a comma, or after an opening bracket so the argument starts the next row; a stage with more lines than fit scrolls to keep the cursor in view. Both are in `warnings`, so you can shorten the line: keep lines under about 24 characters if the video is tall (Python's four-space indent is a lot of that).
- **Safe area.** Nothing is drawn outside the part of the frame that phone apps leave clear (14 percent kept clear at the top of a tall frame and 18 at the bottom, 5 percent all round in a wide one).

## Which stage, and when

`code_along_stage_at(stages, t, ...)` tells you, with no drawing, which stage is being typed `t` seconds into the beat and how many characters of it are in. It takes the options that change the timing (`duration`, `typing_speed`, `seed`) and gives back a dict.

```py
now = code_along_stage_at(stages, 5.5, duration=12)
# now["stage"] (0 first), now["phase"], now["typed"], now["inserted"] (how many
# in all), now["text"], now["cursor"], now["changed"] (the lines lit),
# now["preview"] (the stage on show, -1 for none), now["preview_time"], now["total"]
```

It is a pure function of its arguments, and it gives the same answer as pictures.js's `codeAlongStageAt`.

## Time

Like the kinetic text, the code-along is a function of time and nothing else: the time is the scene's own `kinetic_time()` (which a recorded scene moves by exactly one frame), or the `t=` you give, which wins.

## Related

- [Kinetic text](kinetic-text.md): moving words for the first seconds of a video, and the house style the code-along borrows
- [Make it talk](say.md): a voice for the lines the code-along is about
