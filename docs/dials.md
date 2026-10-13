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

All of them take `x=` and `y=` (to place it by hand: its top left corner), `colour=`, `size=`, `share=` and `span=`.

| Call | What it makes |
|---|---|
| `dial(label, min, max, start)` | A dial. Also `step=`, `unit=`, `log=True` (turned by ratio, as a pitch is), `size=`, `on_change=` |
| `dial(label, target, "setting")` | A dial that is a setting of a target, such as a synth |
| `slider(...)` | The same as a dial, as a slider. `vertical=True` stands it upright |
| `button(label, on_press)` | A button. `fire.pressed` is true once for each press (ask it in `update`); `fire.held` while it is down |
| `toggle(label, on)` | A switch: `if mute:` |
| `rotary(label, choices, start)` | A knob that clicks between a few choices, with a notch for each and their names round it where there is room. Drag to turn it from notch to notch, or tap a name. `mode.value` is the choice. `rotary("reverb", lead, "reverb_type")` takes the choices from the synth. The choice is written under the knob only where no names are round it; `show_value=True` or `False` says otherwise |
| `select(label, choices, start)` | One of a list, stepped through with the arrows at its sides. `wave.value` is the choice. `select("wave", lead, "wave")` takes the choices from the synth, and keeps up when they change (`"sample"` is a wave only once the synth has a sample). `style="rotary"` makes it a rotary |
| `keyboard(target, octave=4)` | A piano keyboard along the bottom. `piano.notes` is what is held now (60 is middle C). `on_note_on=` is given the note and how hard. Also `octaves=`, `height=`, and `animate=False` (the keys jump to a new octave, not slide) |
| `scope(source)` | A line of numbers, live: a synth's wave, or with no source, `graph.push(value)` draws any value over time |
| `meter(source)` | A level from 0 to 1 as a bar of lights |
| `label(text)` | Words. Made just before some controls, it is their heading, on the plate they share |
| `group`, `row`, `column`, `grid`, `page`, `spacer`, `wrap` | What goes with what: see [Laying it out](#laying-it-out) |
| `layout(at="bottom")` | Where the plates go (`"top"`, `"bottom"`, `"left"`, `"right"`), and `scale=`, `wrap=`, `fit=`, `min_scale=`, `max_scale=`, `columns=`, `size=`, `compact=`, `dividers=`, `plates=`, `align=`, `backdrop=`, `image=` and `on_resize=`. `layout()` gives back the width, height and scale the page last said |
| `room()` | The rectangle no control is on (`x`, `y`, `width`, `height`), for the scene to draw in. The page says it with a frame, so it is a frame late |
| `theme(accent="deepskyblue")` | The colours |

Every control has `value`, `remove()` and `place(x, y)`.

![Rotaries: a small one with its choice written under it, usual and large ones with the names round the knob, one with two choices, five, eight and twelve, and one beside dials](images/dials-rotary.png)

## With your hands

- Drag up or to the right on a dial to turn it up. The drag is the dial's until you let go, wherever the pointer wanders.
- Hold Shift to turn a tenth as far. On a touch screen, pull your finger well away from the dial for a quarter.
- Tap twice to put a dial or slider back where it started.
- Tap a slider's track and the handle comes to your finger.
- Each finger on the keyboard holds its own key, and sliding along plays each key in turn.
- The arrows above the keys step an octave, again and again while one is held, and the keys slide there. A finger on the strip between the arrows drags the keys sideways, and they settle on a whole octave.
- A rotary holds at each notch until you have gone most of the way to the next, then clicks over. Tap a name or a notch to go straight to it.
- When there is more than fits, drag a plate's title, or the room between controls, to move the plates. A drag that starts on a dial still turns the dial.
- On a touch screen the controls are made a little bigger, for fingers.

## Laying it out

**There is nothing to do.** Controls line up in the order you make them, on a plate, with the keyboard along the bottom. On a narrow screen the line wraps evenly (six dials are three and three, never five and one), on a touch screen everything is a little bigger, and when the picture changes size it is all laid out again. Controls are drawn a little smaller before a line has to wrap, but never tiny: when there is more than fits, the plates can be moved: with a finger (they carry on a little when it lets go), the mouse wheel, a trackpad or the thin bar beside them, while the keyboard and the scope above it stay where they are. A drag that starts on a dial turns the dial; one that starts on a plate's title, on words or between the plates moves them, passing over dials without turning any; and on a slider that lies across, a finger going along it moves the slider and one going up or down moves the plates. The keyboard is the instrument, and keeps its height: when the plates, the scope and the keyboard do not all fit, the scope is made shorter (never too short to read a wave), and if that is not enough it is the plates that are moved, under a scope and a keyboard that stay where they are. Only on a phone on its side, where there is hardly any height, does the keyboard give up some of its own and the scope go away. `keyboard(lead, height=200)` is kept to, whatever the room.

**A label is a heading.** A `label` made just before some controls is the title of their plate, and they are kept together: a plate moves to the next line whole, never leaving its heading behind. Plates with titles fill the width: they stand side by side, as many to a line as fit, every line reaching both edges, and `row()` says where a line should end when one has to. This is a whole synth panel, and it needs nothing else:

```py
label("oscillator")
select("wave", lead, "wave")
dial("width", lead, "width")

row()
label("unison")
dial("voices", lead, "voices")
dial("detune", lead, "detune")
label("filter")
dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
```

![A synth panel made of labels and controls: six titled plates, two of them side by side twice, a scope and a keyboard, at the width of a tablet's split view](images/dials-layout-headings.png)

**Groups.** `group` says the same thing out loud, and takes options. What is made inside `with` is in the group:

```py
with group("filter"):
    dial("cutoff", lead, "cutoff")
    dial("resonance", lead, "resonance")
```

Or in a straight line, with nothing to indent: `group("filter")` and then its controls, until the next `group`, `row()` or `page`. The plates of a line share its width and are as tall as each other, and every line is as wide as the others, so the panel looks made rather than poured. This is a whole synth in seven groups:

![The front panel example: oscillator, unison, filter, envelope, delay, reverb and output plates above a keyboard](images/dials-front-panel.png)

**Inside a group**, controls stand in a line. To arrange them another way, put these in it (they nest):

| | |
|---|---|
| `with row():` | In a line. (`row()` alone starts a new line.) |
| `with column():` | One under another. |
| `with grid(3):` | Three to a line, in columns that line up; fewer where three will not fit. `span=2` on a control covers two columns. |
| `spacer()` | All the room that is left over, so what follows is pushed to the far end. `spacer(20)` is 20 points. |
| `size="small"`, `"large"`, `1.5` | On any control: smaller, larger, or so many times the usual size. A dial, slider and meter also take a size in points (a number over 4). |
| `share=1` | On a control or a group: it takes the room its line has left over. Two things with shares of 2 and 1 split the line two to one. |

A group takes `colour=` (for its title and every control in it), `columns=3` (a grid), `gap=`, `align=` (`"start"`, `"center"`, `"end"`; left out, its controls are spread along the line), `dividers=True` (a line between the groups inside it) and `plate=False`.

```py
with group("filter", colour="deepskyblue"):
    with column():
        select("kind", lead, "filter")
        toggle("sync", lead, "sync")
    with grid(2):
        dial("cutoff", lead, "cutoff", size="large", span=2)
        dial("resonance", lead, "resonance", size="small")
        dial("chorus", lead, "chorus", size="small")
```

### Size and fit

**By itself**, a panel fits whatever it is on. On a phone held upright its plates are one to a line and are moved up and down with a finger, under a keyboard that stays put. In a tablet's split view they are two to a line, and across a whole tablet three or four, each line reaching both edges. On a touch screen everything is a little bigger, and nothing is ever drawn too small for a finger. Three lines change that: `layout(scale=1.3)`, `layout(wrap=False)` and `layout(size=(900, 640))`.

**Bigger or smaller.** `layout(scale=1.3)` draws everything that much bigger, and it works with everything below.

**Fit the width.** `layout(wrap=False)` keeps every row exactly as you wrote it (each `row()` is one row, whatever the screen) and draws the whole panel smaller until the widest row fits the width. There is one scale for the whole panel, set by that widest row, so a knob is the same size on every row.

```py
layout(wrap=False)
label("oscillator"); select("wave", lead, "wave"); dial("width", lead, "width"); dial("pwm", lead, "pwm"); dial("sub", lead, "sub")
row()
label("unison"); dial("voices", lead, "voices"); dial("detune", lead, "detune"); dial("spread", lead, "spread")
label("filter"); select("filter", lead, "filter"); dial("cutoff", lead, "cutoff"); dial("resonance", lead, "resonance")
row()
label("shape"); slider("attack", lead, "attack"); slider("decay", lead, "decay"); slider("sustain", lead, "sustain"); slider("release", lead, "release")
row()
label("delay"); dial("delay", lead, "echo"); dial("time", lead, "echo_time"); dial("feedback", lead, "echo_feedback")
label("reverb"); dial("reverb", lead, "reverb"); dial("size", lead, "reverb_size")
scope(lead)
keyboard(lead)
```

`layout(fit="width")` is the same, and also draws the panel bigger where there is room to spare, so that the widest row reaches both edges: no bigger than `max_scale=` (1.6 unless you say), and no bigger than still fits the height.

Under a finger the panel is not drawn smaller than eight tenths of its size, which is as small as is comfortable to touch (with a mouse, half). If the rows are still too wide they are left that size and moved from side to side. You choose the floor: `layout(wrap=False, min_scale=1)` never shrinks at all, and `min_scale=0` shrinks as far as it takes.

**A panel of a set size.** `layout(size=(900, 640))` lays the panel out once, as if every screen were 900 by 640, and then makes the whole of it bigger or smaller to fit the screen it is on, keeping its shape and standing in the middle. Nothing moves about from one screen to the next: only the size changes. A width alone, `layout(size=900)` (or `fit="width"` beside a size), fills the width instead, and what does not fit is moved up and down. `x` and `y` are measured in the same size.

![One panel on a phone three ways: by itself, one plate to a line; with wrap false, its rows as written and smaller; and at a set size, the whole panel made to fit](images/dials-fit-phone.png)

A panel made for a tablet is small on a phone. One more line gives the phone its own:

```py
layout(wrap=False) if layout().width < 600 else layout(size=(900, 640))
```

**A bigger knob is your choice, and it is kept.** `size="large"`, `"small"`, or a number of times the usual size (`size=1.5`) on any control makes it that much bigger than its neighbours on every screen and at every scale. Its label and its value still line up with theirs.

```py
layout(wrap=False)
with group("filter"):
    rotary("kind", lead, "filter")
    dial("cutoff", lead, "cutoff", size="large")
    dial("resonance", lead, "resonance")
    dial("drive", lead, "drive", size="small")
with group("mix"):
    dial("volume", lead, "volume", size=1.5)
    dial("pan", lead, "pan")
```

![A filter plate with a large cutoff knob among usual and small ones, and a mix plate with a big volume knob, all their labels on one line](images/dials-fit-big-knob.png)

### Controlling wrapping

Say nothing and the panel decides. Say something and it does as it is told.

| | |
|---|---|
| `layout(wrap=False)` | Never wrap. Every row is the row you wrote, drawn smaller to fit the width (see above). |
| `layout(wrap=True)` | Every `row()` starts a new line, and a row is split only when it does not fit. |
| `layout(columns=3)` | Three plates to a line, always. |
| `layout(columns={"phone": 1, "tablet": 2, "wide": 3})` | How many at each width. `phone` is any width, `tablet` 600 points and up, `wide` 900 and up; a number is a width of your own: `{0: 1, 700: 3}`. |
| `with group("shape", wrap=False):` | This group's controls stay on one line, whatever the width. |
| `with row(wrap=False):` | Groups made inside stay side by side. |
| `row()` | A new line starts here. Inside a group too. |
| `wrap()` | If this line has to be split, split it here. Nothing happens while it fits. |

When a row that may not wrap is too wide, the whole panel is drawn smaller, not that row alone: one scale, as above. Left to itself, a panel treats a `row()` between two plates with titles as the place to end a line when a line must end, and puts as many plates on a line as fit.

```py
layout(columns={"phone": 1, "tablet": 2, "wide": 3})
```

![The same panel with three plates to a line on a wide screen](images/dials-fit-columns.png)

```py
with group("shape"):
    slider("attack", lead, "attack")
    slider("decay", lead, "decay")
    wrap()                                # split here, if it must be split: never between sustain and release
    with row(wrap=False):
        slider("sustain", lead, "sustain")
        slider("release", lead, "release")
```

**Arranging it yourself.** `layout()` gives back what the layout came to: `layout().width`, `.height` and `.scale`. `layout(on_resize=fn)` is called when the picture changes size, with the same three, so a scene can take everything away and make another arrangement. The page tells Python these with a frame: in a scene’s very first lines the scale is still 1.

### Pages, edges and exact places

**Pages.** When there is too much for one screen, give it pages. Each has a tab; the keyboard, and what is made before the first page and after the last, stay on every page.

```py
page("osc")
group("oscillator")
select("wave", lead, "wave")
dial("width", lead, "width")
page("filter")
group("filter")
dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
page()                      # the pages end here
scope(lead)
keyboard(lead)
```

`with page("fx") as fx:` works too, and `fx.show()` turns to a page from your code.

![Three tabs, osc, filter and fx, with the filter page on show: two plates, then a scope and a keyboard that are on every page](images/dials-layout-pages.png)

**Along an edge, and the room that is left.** `layout(at="bottom")` puts the plates at the bottom, and `"left"` or `"right"` in a column down that side. One group can be a strip along an edge, and `room()` is the rectangle no control is on, for the scene to draw in:

```py
with group("moves", at="left"):
    speed = dial("speed", 0, 10, 4)
    jump = button("jump")
    spacer()
    trail = toggle("trail")
with group(at="bottom"):
    button("left")
    button("right")
    spacer()
    button("fire", size="large")

def draw():
    area = room()                         # its x, y, width and height
    rect(area.x, area.y, area.width, area.height, "steelblue")
```

The page works the rectangle out and tells Python with a frame, so in the scene's very first lines `room()` is still the whole picture.

![A strip of controls down the left, a strip of buttons along the bottom, and the scene drawn in the rectangle between them](images/dials-layout-strips.png)

Nothing here asks Python anything: each line above is one command to the page, and the page decides where things go.

**Exactly where you say.** `x=` and `y=` on a control or a group place its top left corner, and `control.place(x, y)` moves it. With `layout(size=(800, 480))` those numbers are in a panel 800 by 480 that is scaled to fit the picture, so a front panel drawn once is right on every screen:

```py
layout(size=(800, 480), image="panel.png")              # a picture behind the controls
dial("cutoff", lead, "cutoff", x=360, y=30, size="large")
with group("osc", x=20, y=20, width=300):
    select("wave", lead, "wave")
    dial("sub", lead, "sub")
keyboard(lead, x=20, y=340, width=760, height=120)
```

**The look.** `layout` also takes `compact=True` (less room around everything), `dividers=True`, `plates=False` (no plates: a picture of your own behind), `backdrop=` (a colour), `image=`, `align="center"` (plates keep their own widths) and `scale=`. `theme(accent="deepskyblue", plate="#20242c")` is still one call for the colours.

A whole program, to run as it is:

```python
from synths import *
from pydials import *

lead = make_synth("lead")

with group("oscillator"):
    rotary("wave", lead, "wave")
    dial("pwm", lead, "pwm")
with group("filter"):
    dial("cutoff", lead, "cutoff", size="large")
    dial("resonance", lead, "resonance")
with group("reverb"):
    rotary("space", lead, "reverb_type")
    dial("reverb", lead, "reverb")
scope(lead)
keyboard(lead, octave=4)

def draw():
    background("midnightblue")
    area = room()                         # the rectangle the controls leave
    circle(area.x + area.width / 2, area.y + area.height / 2, 10 + 200 * max(lead.level()), "gold")
```

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
