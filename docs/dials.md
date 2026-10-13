# Dials and a keyboard

A scene can have dials, sliders, buttons, a piano keyboard, a scope and level meters on it. You say what you want and it appears: nothing to position, nothing to draw. They work with a finger (several at once on the keyboard), with the mouse and with the computer's keys. The library is called **pydials**, and it comes with Pyctures. One line at the top of the scene brings its functions in:

```python
from pydials import *

points = dial("points", 3, 12, 5, step=1)     # from 3 to 12, starting at 5
size = slider("size", 40, 160, 110)

def draw():
    background("midnightblue")
    star(width / 2, height / 2 + 30, size, points, "gold")
```

A control stands for its number wherever a number is wanted: `star(..., size, points, ...)`, `speed * dt`, `if mute:`. `points.value` is the number itself, and `points.value = 8` sets it.

## A synth you can play

With [sound](sound.md), a dial can be a setting of a synth, and a keyboard plays it:

```python
from pyctures import *
from synths import *
from pydials import *

lead = make_synth("lead")
dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
slider("attack", lead, "attack")
scope(lead)
keyboard(lead, octave=4)
```

![A synth panel: two dials, a slider, a scope and a piano keyboard](images/synth-panel.png)

Each dial takes its range, its unit and where it starts from the synth, and turning it changes the sound as you hear it. The scope draws the wave the synth is making. The keyboard plays it: with fingers, with the mouse, and with the keys A S D F G H J (the white keys) and W E T Y U (the black ones); Z and X step down and up an octave.

A key sounds the moment it is touched, however busy Python is, because the page plays the synth itself. Python is told afterwards: `lead.cutoff` reads what the dial says, and `piano.notes` what is held.

`scope(sound_output())` and `meter(sound_output())` show all the sound together, and `dial("volume", sound_output(), "volume")` turns it up and down.

## The controls

All of them take `x=` and `y=` (to place it by hand: its top left corner) and `colour=`.

| Call | What it makes |
|---|---|
| `dial(label, min, max, start)` | A dial. Also `step=`, `unit=`, `log=True` (turned by ratio, as a pitch is), `size=`, `on_change=` |
| `dial(label, target, "setting")` | A dial that is a setting of a target, such as a synth |
| `slider(...)` | The same as a dial, as a slider. `vertical=True` stands it upright |
| `button(label, on_press)` | A button. `fire.pressed` is true once for each press (ask it in `update`); `fire.held` while it is down |
| `toggle(label, on)` | A switch: `if mute:` |
| `select(label, choices, start)` | One of a list. `wave.value` is the choice. `select("wave", lead, "wave")` takes the choices from the synth |
| `keyboard(target, octave=4)` | A piano keyboard along the bottom. `piano.notes` is what is held now (60 is middle C). `on_note_on=` is given the note and how hard |
| `scope(source)` | A line of numbers, live: a synth's wave, or with no source, `graph.push(value)` draws any value over time |
| `meter(source)` | A level from 0 to 1 as a bar of lights |
| `label(text)`, `row()` | Words in the row, and the start of a new row |
| `layout(at="bottom")`, `theme(accent="deepskyblue")` | Where the rows go, and the colours |

Every control has `value`, `remove()` and `place(x, y)`.

## With your hands

- Drag up or to the right on a dial to turn it up. The drag is the dial's until you let go, wherever the pointer wanders.
- Hold Shift to turn a tenth as far.
- Tap twice to put a dial or slider back where it started.
- Each finger on the keyboard holds its own key, and sliding along plays each key in turn.

## A button in a game

```python
from pydials import *

jump = button("jump")
gravity = dial("gravity", 200, 2000, 900)
y, vy = 0, 0

def update(dt):
    global y, vy
    if jump.pressed and y == 0:
        vy = 500
    vy -= gravity * dt
    y = max(0, y + vy * dt)
    if y == 0:
        vy = 0

def draw():
    background("#182033")
    rect(0, height - 60, width, 60, "seagreen")
    circle(width / 2, height - 90 - y, 30, "gold")
```

## How it works

Python never touches the page: it may be in a worker, or on another computer. So the page draws the controls and feels the fingers, and a dial turns smoothly however busy Python is. Each function sends one command that makes the control in the page, and what a hand changes comes back with the next frame. The page loads the controls the first time a scene uses them; a scene without them loads nothing extra.

The library on its own, with every option, is [pydials](https://github.com/johnwylie70/pydials); the same controls for JavaScript are [dials.js](https://github.com/johnwylie70/dials.js).
