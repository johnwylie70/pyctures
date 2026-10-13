# Sound and music

A scene can make sound: a game sound where something happens, a note, a tune that goes round, a synth you shape yourself, a whole song from a file, and your own voice from a microphone, changed, recorded and saved. The sound library is called **synths**, and it comes with Pyctures. One line at the top of the scene brings its functions in:

```python
from synths import *

ball = Sprite("⚽", 200, 100, size=48)
ball.vy = 0

def update(dt):
    ball.vy += 900 * dt
    ball.update(dt)
    if ball.y > height - 24:          # the ground
        ball.y = height - 24
        ball.vy = -ball.vy * 0.9
        play_sound("bounce")

def draw():
    background("seagreen")
    ball.draw()
```

Run it as you run any scene (`pyctures run ball.py`), and click the picture once.

Sound is new: it is in this repository and not yet in the Pyctures that `pip install pyctures` gives (0.2.0). It will be in the next release.

## The first tap

A browser keeps a page silent until the person using it has clicked, tapped or pressed a key. Until then the scene says so, in grey words over the picture: "Click, tap or press a key to turn the sound on". The first touch turns the sound on, and from then on it stays on.

- A **tune** you started before the touch waits, and begins at the touch.
- A **single note or sound effect** from long before the touch is let go, because played late it would be wrong. The sound that the touch itself asks for is heard.

So a game needs nothing special: the click that starts the game turns the sound on. A scene that is only music is best started by a click of its own, as [the Tune example](../examples/tune.py) is.

## Game sounds

```py
play_sound("coin")
play_sound("laser", 0.5)                 # half as loud
play_sound("coin", pitch=score % 12)     # higher, by semitones
play_sound("jump", pan=-1)               # from the left
```

The ready-made sounds: `coin`, `jump`, `laser`, `shoot`, `explosion`, `hit`, `powerup`, `blip`, `click`, `zap`, `bounce`, `pop`, `win` and `lose`. `sound_names()` lists them.

## Notes and tunes

```python
from synths import *

def on_mouse_down(x, y):
    play_note("C4")                                  # middle C, for half a second
    play_notes("E4 G4 C5 - G4 C5:2", 0.25, after=1)  # then a tune, a second later

def draw():
    background("midnightblue")
    text("Click for a tune", width / 2, height / 2, "white", 28, "centre")
```

A note is a letter and a number: `"C4"` is middle C, `"A4"` is the A above it, `"F#3"` is F sharp and `"Bb5"` is B flat. A number works too, where 60 is middle C and each whole number is one key of a piano.

| Call | What it does |
|---|---|
| `play_note("C4")` | A note for half a second |
| `play_note("C4", 2, 0.3)` | Two seconds long, and quiet: loudness goes from 0 to 1 |
| `play_note(["C4", "E4", "G4"])`, `play_note("Cm7")` | A chord: a list of notes, or its name |
| `play_notes("C4 E4 G4 - C5:2", 0.25)` | A tune, a step every quarter of a second. `-` is a rest, `:2` lasts two steps, `C4+E4` or `Cm` is a chord |
| `tune = play_notes(..., repeat=True)` | Round and round, until `tune.stop()` |

A tune keeps exact time however busy the scene is, because the sound engine keeps the time, not your program.

## A tune, one note a line

`play_note` plays a note now. `note` plays the **next** note of a tune: each one begins where the one before it ended, so a tune is written as ordinary lines, with loops and ifs.

```python
from synths import *

def on_mouse_down(x, y):
    start_lines()
    set_tempo(100)
    note("E4", "quarter")
    note("G4", "quarter")
    rest("quarter")
    note("C5", "half")
    for name in ["C4", "D4", "E4"]:
        note(name, "eighth")
    chord("Cm", "whole")

def draw():
    background("midnightblue")
    text("Click for a tune", width / 2, height / 2, "white", 28, "centre")
```

A length is a note length by name, measured against the tempo (`"whole"`, `"half"`, `"quarter"`, `"eighth"`, `"sixteenth"`; `"quarter."` is half as long again), or a number of beats. The same names work wherever a length is wanted, and there a number is seconds: `play_note("C4", "half")`, `play_note("C4", 0.5)`.

Every synth has a line of its own (`lead.note("C4", "eighth")`, `bass.note("C2", "half")`), and lines written one after the other begin together. `with loop_notes():` has what is written inside go round, kept in time by the sound engine:

```py
kick, snare = make_synth("kick"), make_synth("snare")
with loop_notes() as drums:
    kick.note("C3", "quarter")
    snare.note("A3", "quarter")
drums.stop()
```

## A synth of your own

```python
from synths import *

lead = make_synth("lead", cutoff=1200)

def on_mouse_down(x, y):
    lead.cutoff = 200 + x * 6             # brighter to the right
    lead.play(["C4", "E4", "G4"], 0.6)

def draw():
    background("#14161c")
    text("Click: left is dull, right is bright", width / 2, height / 2, "white", 22, "centre")
```

`make_synth("bass")` starts from a ready-made synth; `make_synth(wave="saw", attack=0.2)` starts from nothing. The ready-made ones: `keys`, `bass`, `lead`, `pad`, `pluck`, `organ`, `strings`, `bell`, `flute`, the chip sounds `chip`, `chip_lead`, `chip_bass`, `chip_noise`, `chip_kick`, `chip_snare` and `chip_hat`, and the drums `kick`, `snare` and `hat`.

| Call | What it does |
|---|---|
| `lead.play("E4", 0.5)` | A note for half a second. No note at all plays the synth's own (a drum's) |
| `held = lead.start("E4")` | A note that stays until `held.stop()`. `held.slide_to("G4", 0.5)` slides it |
| `lead.note("E4", "quarter")` | The next note of this synth's line: see [A tune, one note a line](#a-tune-one-note-a-line) |
| `lead.stop()` | Let go of every note |
| `lead.play_notes("C4 E4 G4", 0.25)` | A tune on this synth |
| `lead.cutoff = 800` | Change a setting; notes already sounding change too. `print(lead.cutoff)` reads it back |
| `lead.set(cutoff=4000, glide=2)` | Glide there over two seconds (`slide=2` is an older word for the same) |
| `lead.voice = "robot"` | A voice changer on everything it plays: see [Your voice](#your-voice) |
| `lead.samples()`, `lead.level()`, `lead.notes()` | What it is doing, for your own drawing: see [Drawing the sound yourself](#drawing-the-sound-yourself) |
| `lead.arp("Cm7")`, `arp = lead.start_arp("Am")` | A chord as an arpeggio, fast or in time with the tempo (`step="sixteenth"`). `arp.change("F")` changes it as it plays: see [Arpeggios, fast and musical](#arpeggios-fast-and-musical) |

The settings you will use most:

| Setting | What it is |
|---|---|
| `wave` | The raw sound: `"sine"`, `"triangle"`, `"saw"`, `"square"` |
| `volume`, `pan` | How loud (1 is normal), and left (-1) to right (1) |
| `attack`, `decay`, `sustain`, `release` | The shape of a note's loudness: seconds to reach full, seconds to fall to the `sustain` level, and seconds to die away |
| `cutoff`, `resonance` | How bright (20 to 20000), and a whistle at the cutoff (0 to 1) |
| `octave`, `pitch` | Move every note by octaves, or by semitones |
| `vibrato`, `vibrato_rate` | A wobble of pitch |
| `pwm`, `pwm_rate` | How far a `"pulse"` wave's width moves by itself (0 to 1), and how many times a second: the thick, moving sound of an old string synth |
| `echo`, `reverb`, `chorus` | How much of the synth goes to each effect (0 to 1) |
| `distortion`, `crush` | Grit, and the bits each sample keeps (4 is an old games console) |

`setting_names()` lists every one. The echo, the reverb and the chorus are shared by all synths, and are shaped with `set_effects(echo_time=0.3, echo_feedback=0.5, reverb_size=0.8)`. The reverb is one room that every synth sends into: `set_effects(reverb_type="hall")` chooses what kind of space it is (`"room"`, `"hall"`, `"plate"`, `"cathedral"` or `"spring"`), `reverb_decay=3` how many seconds it rings, `reverb_predelay=0.03` how long before it starts, and `reverb_low_cut=300` how much of the bass it leaves out (in hertz). A shared setting has one value whoever set it: `lead.reverb_type = "hall"` is the same thing, and every synth reads it back.

## Arpeggios, fast and musical

A chord is notes together. An arpeggio is the notes of a chord one at a time. There are two kinds here, and they sound nothing alike.

**Fast: the chord of a Commodore 64 tune.** One voice whose pitch jumps through the chord fifty times a second, which the ear hears as a shimmering chord. The chip had only three voices to spend.

```py
play_arp("Cm7")                             # half a second of C minor seventh
play_arp("C4", "minor", 2)                  # a note and a kind, for two seconds
play_arp(["C4", "E4", "G4", "C5"], 1, speed=12, order="up-down")
```

`speed` is steps a second: 50 unless you say, which is the speed chip music was written at; at 12 you can hear each step.

**Musical: each step a note of its own, in time with the tempo.** Say how long a step is with `step`, a note length, and every step is struck afresh, held for part of the step and let go.

```py
set_tempo(138)
lead = make_synth("pluck")
lead.arp("Am", "whole", step="sixteenth", octaves=2, gate=0.5)       # a trance arpeggio: up through two octaves
lead.arp("C", "whole", step="eighth", order="up-down", gate=0.9)     # a pop arpeggio: slower, nearly joined up
```

What an arpeggio can be told:

| | |
|---|---|
| `step` | how long a step is: `"sixteenth"`, `"eighth"`, `"eighth."`, `"1/12"`, or a number of beats. It follows `set_tempo`, even while the arpeggio is sounding |
| `speed` | steps a second instead (50): the fast kind |
| `order` | `"up"`, `"down"`, `"up-down"`, `"up-down2"` (the top and bottom notes twice), `"as written"`, `"random"`, `"together"` (the whole chord at each step: stabs) |
| `octaves` | 1 to 4: through the chord, then the same an octave up |
| `gate` | how much of its step each note is held, 0.05 to 1 (0.5). Short is plucked; 1 is joined up |
| `swing` | 0 to 0.75: every second step is that much of a step late (0.33 is a triplet feel) |
| `accent` | how hard each step is struck, up to eight numbers from 0 to 1 that go round: `[1, 0.5, 0.5, 0.5]`. 0 is a rest |
| `pattern` | a rhythm of its own in the place of the order: `"1 - 3 2 _ 1 3 5^"`, or one by name |
| `style` | `"strike"` (each step a new note: what `step` gives) or `"slide"` (one voice whose pitch jumps: what `speed` gives). Say it to have the other |

In a **pattern** each step is a number (that note of the chord, counted from 1 at the lowest; past the top it carries on an octave up), `-` for a rest, or `_` to hold the last note through the step. After a note, `'` is an octave up, `,` an octave down, `^` an accent and `:3` its own gate in tenths; `~` before a note slides into it. The patterns by name are `bounce`, `octaves`, `root-fifth`, `thumb`, `converge`, `diverge`, `offbeat`, `gallop`, `trance` and `acid`.

One that stays, and changes chord under your hands:

```py
chord = lead.start_arp("Am", step="sixteenth", pattern="trance")
chord.change("F")                          # from the next step, and it keeps its place in the pattern
chord.gate = 0.3                           # so do gate, octaves, swing, accent, pattern, order, step and speed
chord.stop()
```

A chord has room for eight notes. Every synth has `arp` and `start_arp`; with no synth (`play_arp`, `start_arp`) they play on a chip sound. The length after the chord is how long the arpeggio sounds, as for any note (half a second unless you say), and it takes `volume`, `pan`, `after`, `at` and `beat` like any note; `chord.change("F", after=2)` changes it later. A struck arpeggio is ordinary notes, so it goes through the synth's envelope and filter at every step, and plays the right recordings of an instrument from `load_samples`. The tempo an arpeggio in steps keeps is the page's: where several scenes share a page, it is the tempo that was set last. [Arpeggio Chords](../examples/arpeggio_chords.py) is the fast kind, with a tune over it.

A synth can have a pattern of its own, which every arpeggio of it follows unless it says another: `lead.arp_pattern = "trance"` (or the steps, or a list of them such as `[1, 0, 3, 2]`, where 0 is a rest). It reads back as its text, `"1^ - 3 2 - 1^ 3 -"`, and `lead.arp_pattern = "off"` takes it away. `lead.arp_step()` is the step that is sounding, counted from 0, for drawing it.

For a sequencer of your own that looks ahead: `sound_time()` is the sound's clock in seconds, and `lead.play("C4", at=sound_time() + 0.25)`, `lead.note_on("C4", 0.8, at=when)` and `lead.note_off("C4", at=when)` happen on the exact sample of that time.

### Bending a note

A note's pitch can move, on any synth and on a sample:

```py
lead.play("A4", 1, bend="scoop")                  # up into the note from just below, as a singer starts one
lead.play("C5", 1, glide="sixteenth")             # slides to C5 from the note this synth played last
lead.play("E5", 2, vibrato=True)                  # begins straight, then starts to sing
lead.play("A3", 1, bend="fall")                   # droops away at its end
lead.play("C4", 1, slide=12)                      # an octave up, at once: a laser
```

| | |
|---|---|
| `glide` | the note starts at the pitch of the synth's last note and slides to its own: `True` (a sixteenth), a note length, or seconds |
| `bend` | `"scoop"` (from 2 semitones below, over a sixteenth), `"fall"` (5 down over an eighth, ending with the note), `"dip"` (a semitone down and back), or `{"to": 2, "over": "eighth"}`: how far in semitones, or to a note by name, and how long. `{"shape": "scoop", "to": -5}` is a scoop of another size |
| `slide` | a bend by a number of semitones over a sixteenth, or `{"to": ..., "over": ...}` |
| `vibrato` | `True`, or `{"depth": 0.3, "rate": 6, "delay": "eighth"}`: semitones each way, times a second, and how long the note sounds first |

They are for one note at a time (a chord's notes would all be moved to one pitch), in `play`, `start` and `play_note`; a tune from `play_notes` does not take them. A note that is held can be moved as it sounds: `held = lead.start("C4")`, then `held.slide_to("E4", 0.2)`, `held.vibrato()` and `held.vibrato(False)`.

## The trance gate

A trance gate turns a synth's sound up and down in a pattern of steps, in time with the tempo, so a held chord becomes a rhythm. It chops whatever the synth is playing.

```py
set_tempo(138)
pad = make_synth("pad", echo=0.3)
pad.trance_gate = "x.x.xx.x"                # x is open, . is closed; a step is a sixteenth
pad.start(["A3", "C4", "E4"])
```

`pad.trance_gate = "trance"` is a pattern by name: `eighths`, `offbeat`, `gallop`, `trance`, `stutter`, `pump`, `triplets` (with `trance_gate_rate` 6) and `dotted`. A digit from `0` to `9` in a pattern is a step part of the way open, so `"2468"` swells; a list of levels from 0 to 1 is a pattern too. It reads back as the pattern's text, and `pad.trance_gate = "off"` takes it away.

Its settings, each one a dial can be tied to:

| | |
|---|---|
| `trance_gate_rate` | steps to a beat: 4 is sixteenths, 2 eighths, 3 and 6 triplets |
| `trance_gate_depth` | how far a closed step closes: 1 is silence, 0.5 is half. Giving a pattern makes it 1 |
| `trance_gate_smooth` | seconds from one level to the next; longer is softer |
| `trance_gate_swing` | every second step that much of a step late |
| `trance_gate_stereo` | left and right by turns |
| `trance_gate_sends` | `False`: the echo and the reverb are fed the sound before it is chopped |

`pad.set_trance_gate("x.x.xx.x", rate="eighth", depth=0.8, smooth=0.02)` says a pattern and its settings in one line, with the rate as a note length. The steps begin at `set_tempo`: call it where the bar begins and the gate is on the beat. `pad.trance_gate_step()` is the step that is sounding, for drawing it. (The word `gate` alone is something else twice over: an arpeggio's `gate` is how long each of its notes is held, and the microphone's `mic.gate` is its noise gate.)

## Samples

A sample is a recorded sound in a file beside the scene: a `.wav`, or anything else a browser can read (`.mp3`, `.ogg`).

```py
kick = load_sample("sounds/kick.wav")
kick.play()                       # as it was recorded
kick.play("E4")                   # higher: a sample is a synth, and "C4" is its own pitch
```

A sample can also be the wave of any synth, under its filter and its envelope: `lead.sample = load_sample("sounds/piano.wav")` turns its wave to the recording (`lead.wave = "saw"` goes back), and `make_synth(sample="sounds/piano.wav", note="C4", cutoff=1800)` does it in one line.

There is nothing to wait for: play it straight away, and it sounds as soon as the file has arrived. `pyctures build` finds the sound files a scene names and takes them along: copied beside the scene in a folder, or inside a single `.html` file.

### Several recordings for one instrument

One recording stretched over a whole keyboard sounds thin at one end and muddy at the other. A real instrument is several recordings, each playing the keys near the note it was recorded at:

```py
piano = load_samples({"C2": "piano-C2.wav", "F#2": "piano-Fs2.wav", "C3": "piano-C3.wav"})   # the note each was played at
piano.play("E2")                  # the nearest recording (F#2), moved down to E
piano.reverb = 0.3                # a synth like any other: settings, dials, keyboard(piano), a tune, an arpeggio
```

The keys are split halfway between neighbours, and every key plays, below the lowest recording and above the highest too. With the notes in the files' names there is less to write: `load_samples(["piano-C2.wav", "piano-Fs2.wav", "piano-C3.wav"])` reads `C2`, `Fs2` (or `F#2`, `Gb2`) and `C3` from them, and a number alone (`60.wav`) is that key; `note_in_name("piano-Fs2.wav")` is how it reads one. A name with no note in it is refused, with what to do about it.

A drum kit is the same with `kit=True`: each key is its own sound, played as it was recorded whatever the key, to its end, and the keys between are silent.

```py
kit = load_samples({"C2": "kick.wav", "D2": "snare.wav", "F#2": "hat.wav"}, kit=True)
kit.play_notes("C2 F#2 D2 F#2", 0.25, repeat=True)
```

What else can be said:

- **`crossfade=3`** fades neighbouring recordings into each other over three keys, where a change from one to the next would be heard. `crossfade={"keys": 3, "loud": 0.1}` fades the loudness layers too.
- **Layers by how hard a note is played**, in the explicit form, a list of dicts: `load_samples([{"file": "soft-C4.wav", "note": "C4", "loud": [0, 0.5]}, {"file": "hard-C4.wav", "note": "C4", "loud": [0.5, 1]}])`. `loud` is the note's volume, from and to.
- **Takes that go in turn**: several files for one note, `{"C4": ["snare-1.wav", "snare-2.wav"]}`, and each hit plays the next.
- **By hand**, for each recording: `"from"` and `"to"` (its keys), `"tune"` (cents), `"volume"`, `"pan"`, `"release"` (seconds), `"one_shot"`, `"as_recorded"`, `"loop"`, `"start"` (frames). `loop=True` and `one_shot=True` after the files are for all of them.
- **Release.** With nothing said each recording has a release that suits its note, longer for the low ones, as a piano's are. `load_samples(files, release=1)` gives every recording that release in their place.
- **On an ordinary synth**: `lead.samples = {"C3": "a.wav", "C4": "b.wav"}`, `lead.set_samples(files, crossfade=3)` or `make_synth(samples={...}, cutoff=1800)`, and the recordings go through that synth's filter and envelope. `lead.samples = None` takes them away. (`lead.samples()` is still the wave for a scope.)
- **Reading it back**: `piano.zones()` is the list as you gave it, each with its file and its note. The keys each was worked out to play are the page's to know.

The files are beside the scene, as for `load_sample`.

## When things start

Everything that makes a sound takes one of these:

```py
play_sound("coin", after=0.5)             # half a second from now
play_note("C4", 1, at=sound_time() + 2)   # at a time on the sound clock, which sound_time() reads
lead.play("E4", beats(1), beat=8)         # on beat 8
```

Beats are counted from `set_tempo(120)` (beats a minute; beat 0 is the moment you call it). `beats(2)` is how many seconds two beats last, and `beat()` is which beat it is now.

A sound is placed on the exact moment it was asked for, to a fraction of a thousandth of a second, even though a scene's sounds are sent to the page only once a frame. Each one carries the time it was called.

## Volume, mute and stop

```py
set_volume(0.5)      # everything half as loud. 1 is normal
mute_sound()         # silence, and unmute_sound() to bring it back
stop_sound()         # stop everything that is sounding or waiting to sound
```

A scene that scrolls out of view, or whose tab is hidden, goes quiet until it is seen again.

### If the sound clicks

```py
set_sound_buffer("large")        # "small" (1024 frames), "medium" (2048), "large" (4096), "auto", or a number of frames
now = sound_buffer()             # {"frames": 4096, "delay": 179, "thread": "page", "underruns": 0, "setting": 4096}
```

A page that is not served over https (`pyctures run` opened on a phone or an iPad by the computer's address) makes its sound on the page's own thread, a buffer at a time, and clicks when the page is busy for longer than a buffer lasts. A larger buffer rides over that and is heard later: `"large"` is about a fifth of a second from a key to its note, `"small"` a twentieth. `"auto"` lets the page choose, and double it once if it keeps clicking. It may be called before the first sound or at any time. `delay` is the milliseconds from a key to its note, `underruns` counts the clicks, and `thread` is `"page"` there and `"audio"` on an https page or on the computer itself, where there is nothing to fix and the same call sets how far ahead everything is scheduled instead. What `sound_buffer()` says is what the page last said: a frame late, and all zeros before it has.

## A sound button, and asking first

Two lines, each for its own job. Neither happens unless you write it. Neither needs an import: they are Pyctures' own, like `Sprite` and `save`, and a page loads the little they take only for a scene that names one.

### The button

```py
sound_button()
```

A small speaker in a corner of the scene. A click or a tap on it switches all of the scene's sound off, and another switches it back on; the picture on it shows which. The **M** key does the same while the scene has the keyboard. The choice is remembered for this scene on this device, with its [saved values](saved-values.md), so a scene that was switched off is still off the next time. It asks nothing: your game starts as it always did.

```py
sound_button("bottom left")          # a corner: "top right" unless you say, "bottom right", "top left"
```

| Option | What it does |
|---|---|
| `corner` | `"top right"`, `"bottom right"`, `"top left"` or `"bottom left"` |
| `size` | How many points across. Unless you say: 34 with a mouse, 44 where a finger does the pointing |
| `inset` | How far in from the two edges of its corner, in points: a number, or `(across, down)` to sit beside something your scene draws in that corner. Unless you say: 8, or 10 for a finger |
| `colour` | `"auto"` looks at the scene under the button and is light on a dark scene and dark on a light one; or say `"light"` or `"dark"` |
| `key` | The key that switches the sound: `"m"` unless you say, `None` for none |

- **The page draws it, not your scene.** It is laid over the picture, and the page does the switching at once, however busy Python is. It keeps off any [dials and sliders](dials.md), and goes when the scene stops. A tap on it is not a tap on your game: `on_mouse_down` is not called.
- **A scene that reads M itself** (it has `"m"` in its code) keeps M, and the button leaves it alone.

To read the switch, or turn it yourself:

```py
sound = sound_button()

def draw():
    background("midnightblue")
    if not sound_is_on():
        text("Sound is off: press M", 20, 30, "white", 16)
```

`sound_is_on()` is `True` or `False`. `sound.on` is the same thing, and can be set: `sound.on = False`. `sound.over(x, y)` says whether a point of the scene is on the button, and `sound.remove()` takes the button away. `mute_sound()` and `unmute_sound()` are the same switch: the button shows what they did. Only what a person chose is remembered, not what your code switched.

The page holds the switch, and tells Python with the next frame. So after a tap, or after `mute_sound()`, `sound_is_on()` is right one frame later; after `sound.on = False` it is right at once.

### Asking first, in a demo

A demo is something other people open, perhaps in a quiet room. One line has it ask before it makes a sound:

```py
ask_about_sound()
```

Before anything is heard a card is laid over the scene: "This demo has sound", with two big buttons, "Play with sound" and "Play without sound". Nothing sounds until one is chosen, and the game waits behind the card: its first frame is shown, and `update` and `draw` are not called again until the answer. "Play with sound" is also the click a browser needs before it lets a page make sound. The line puts the sound button up as well, if the scene has not, so a demo needs only this one line.

It is for demos you publish. A game of your own does not need it, and nothing shows the card unless the scene has this line.

```py
ask_about_sound("Music and sound effects")                      # say what kind of sound it is
ask_about_sound(with_sound="Sound on", without_sound="Quiet")
```

| Option | What it does |
|---|---|
| `title`, `with_sound`, `without_sound` | The card's words. The title can be given by itself, first |
| `remember` | `True` asks only until there is an answer, and uses that answer from then on |
| `wait` | `False` keeps the scene running behind the card (still silent) |
| `corner`, `size`, `inset`, `colour`, `key` | For the button it puts up, as above |

- **When it asks.** Every time the scene is opened afresh, with last time's answer ready under Enter: the card is there so that nobody is surprised, and yesterday's answer is not today's. It does not ask again when the scene is run again within five minutes of an answer, so working on a demo is not a card at every run.
- **Keys on the card.** Enter or Space presses the button that has the keyboard, the arrows or Tab go between the two, and Escape is "Play without sound". No key and no tap reaches the game while the card is up.
- **What was asked for before the answer.** A sound effect or a note is dropped, because played late it would be wrong; a tune that repeats, or a song, starts at "Play with sound".
- While the card is up `sound_is_on()` is `False` and `sound.asking` is `True`.

## Songs

A song is a whole piece of music in one file, played by the sound engine itself: a tracker's `.mod` or `.xm` file, or a song in synths' own format.

```py
song = play_song("tune.mod")          # it goes round and round until it is stopped

song.pause()
song.resume()
song.volume = 0.5
song.stop()
```

`play_song("tune.xm", repeat=False)` plays it once. One song plays at a time, and your own notes and game sounds play over it. It starts at the first tap, like a tune.

A song is made of channels, counted from 0, and of patterns it plays in turn:

```py
song.mute(2)                          # silence channel 2. song.mute(2, False) or song.unmute(2) brings it back
song.solo(0)                          # hear only the channels that are soloed. song.solo("all", False) hears the rest again
song.loop_pattern()                   # stay on the pattern that is playing. song.loop_pattern(False) carries on
song.seek(2)                          # jump to the third part of the song (and seek(2, 16): its row 16)
```

**The mix.** Each channel has a place in the song's mix that can be moved while it plays, and the changes glide, so a fader can be dragged:

```py
song.channel(0).volume = 0.6               # its fader, 0 to 2
song.channel(0).pan = -0.5                 # -1 is left, 1 is right
song.channel(0).reverb = 0.4               # how much of it goes to the reverb, 0 to 1
song.channel(0).echo = 0.3                 # and to the echo
song.loop([1, 0], [5, 0])                  # go round from the top of place 1 in the order to the top of place 5; song.loop(None) runs on
```

`volume` and `pan` reach a channel whatever plays on it. `reverb` and `echo` reach a channel's sampled instruments; a synth instrument has the sends of its own synth (`reverb` and `echo` in its patch). Each reads back what was last set here. The reverb and the echo are the ones every synth shares, so `set_effects(reverb_type="hall", reverb_level=0.8, echo_time=0.3, echo_level=0.7)` shapes them; `reverb_level` and `echo_level` are how loud each comes back, for everything sent to it.

`song.position` says where the song is, for drawing it: `{"state", "order", "pattern", "row", "tick", "speed", "tempo", "rounds", "rows", "orders"}`, where `state` is `"playing"`, `"paused"`, `"stopped"` or `"none"`. It is [a frame late](#drawing-the-sound-yourself), and `"none"` the first time it is read. `song.replace(edited)` puts an edited song in the place of the one playing: its bytes, its JSON as text, or the song as a dictionary.

## MIDI

MIDI is how music keyboards, drum pads, boxes of knobs and synths talk to each other and to a computer. Plug a MIDI keyboard into your computer and one line makes it play a synth:

```python
from synths import *

lead = make_synth("keys", reverb=0.3)
lead.play_from_midi()

def draw():
    background("midnightblue")
    text("Play your MIDI keyboard", width / 2, height / 2, "white", 28, "centre")
```

It follows the notes, how hard you hit each key, the pitch wheel, the modulation wheel and the sustain pedal. The first time a scene uses MIDI the browser asks whether the page may use your MIDI devices: say yes.

The page plays the synth itself, where the keyboard is, without asking Python first. So a key sounds at once, even while your program is busy drawing, or runs on another computer.

MIDI works in Chrome, Edge and Firefox on a computer. Safari, iPhones and iPads have no MIDI for web pages. Where there is none the scene still runs: the browser's console says so once, and everything else carries on.

### Your own functions

Give a function one of these names and it is called, as `on_key_down` is:

| Function | Called when |
|---|---|
| `on_midi_note(note, velocity, channel)` | A key goes down. `note` is a number, where 60 is middle C. `velocity` is how hard it was hit, from 0 to 1. |
| `on_midi_note_off(note, channel)` | A key comes up. Without this function, `on_midi_note` is called for it with velocity 0. |
| `on_midi_control(number, value, channel)` | A knob, slider or pedal moves. `number` says which (0 to 127; the sustain pedal is 64) and `value` goes from 0 to 1. |
| `on_midi(message)` | Anything at all arrives. `message.type` is `"noteOn"`, `"noteOff"`, `"control"`, `"bend"`, `"program"` and so on, with `message.note`, `message.velocity`, `message.control`, `message.value`, `message.bend`, `message.channel`, `message.device`, `message.data` (the bytes) and `message.time`. |
| `on_midi_devices(devices)` | The devices are known, and again when one is plugged in or pulled out: `devices["inputs"]` and `devices["outputs"]` are lists of names, and `devices["available"]` is `False` where there is no MIDI. |

A function may leave arguments off the end: `def on_midi_note(note, velocity):` is fine.

```python
from synths import *

bell = make_synth("bell", reverb=0.4)
dots = []

def on_midi_note(note, velocity, channel):
    bell.play(note, 0.4, velocity)
    dots.append([width * (note - 36) / 60, height * (1 - velocity)])

def on_mouse_down(x, y):             # with no keyboard: a click pretends to be one
    receive_midi({"type": "noteOn", "note": round(36 + 60 * x / width), "velocity": 1 - y / height, "channel": 1})

def draw():
    background("black")
    for x, y in dots:
        circle(x, y, 12, "gold")
    text("Play a MIDI keyboard, or click", width / 2, 30, "white", 16, "centre")
```

Your functions are called once a frame, with everything that arrived since the last one, so they hear of a key up to a frame after it was pressed. `message.time` says exactly when it happened, on the clock that `sound_time()` reads. That wait is only for your own functions: `play_from_midi()` and `learn()`, below, do not have it.

### A knob turns a setting

```py
lead.learn("cutoff")                     # the next knob you turn on your controller is the cutoff from then on
lead.map_midi(74, "resonance")           # or say which knob, by its number
```

The knob goes through the setting's whole range, and the page changes the synth itself, at once. `lead.cutoff` reads what the knob set, a frame later, and a dial on the screen that is tied to the same setting (`dial("cutoff", lead, "cutoff")`, see [Dials and a keyboard](dials.md)) turns with the knob. `lead.learn("cutoff", changed)` calls your function with each new value; `min=200, max=4000` narrow the range; `lead.unmap_midi("cutoff")` lets it go.

### Sending

A synth or a drum machine on your desk can be played from your scene:

```py
send_midi_note("C4")                                  # a note, let go half a second later
send_midi_note("C4", 0.8, length="quarter", channel=1)  # how hard, how long (seconds, or a note length), which channel (1 to 16)
send_midi_note(["C4", "E4", "G4"], beat=4)            # a chord, on beat 4
send_midi_control(74, 0.5)                            # turn knob 74 on the other device to half way
send_midi([0x90, 60, 100])                            # any message at all, as its bytes
```

Each takes `after=`, `at=` or `beat=`, as a sound does, and leaves at exactly that time. There are also `send_midi_note_off("C4")` (for a note sent with `length=None`, which is held), `send_midi_bend(0.5)`, `send_midi_program(5)` and `send_midi_clock()`, which sends the beat so another device keeps time with `set_tempo`. `bass.send_to_midi()` sends everything a synth plays out as MIDI too.

### Which device

`midi_devices()` gives `{"inputs": [...], "outputs": [...], "available": ...}`: the names of what is plugged in. The page has to be asked, and its answer comes with a later frame, so the first time it is called the lists are empty and `available` is `None`. Write `def on_midi_devices(devices):` to be told when they are known. `use_midi_input("Keystation 49")` listens to one device alone, `use_midi_output("Minilogue")` sends to one, and `stop_midi()` stops everything MIDI is doing.

## Your voice

The microphone is a synth whose sound comes in instead of being made. Ask for it, give it a voice, and listen:

```python
from pyctures import *
from synths import *

mic = use_microphone()            # the browser asks whether the page may use the microphone
mic.voice = "robot"               # robot, chipmunk, monster, cave, telephone, alien, whisper, or "none"

def on_mouse_down(x, y):
    mic.listen()                  # now you hear yourself, as a robot. mic.mute() stops it

def draw():
    background("midnightblue")
    text("Click, and talk like a robot", width / 2, height / 2, "white", 28, "centre")
    text("the microphone is " + mic.state, width / 2, height / 2 + 40, "#8a93a6", 16, "centre")
```

**Wear headphones when you listen.** Through loudspeakers the microphone hears itself, and the sound goes round and round until it howls. That is why nothing is heard until you say `listen()`. Recording does not need it.

| Voice | What it is |
|---|---|
| `robot` | A machine, ringing in a metal pipe |
| `chipmunk` | Small and squeaky: seven semitones higher |
| `monster` | Huge and deep: seven semitones lower, with a growl |
| `cave` | Far inside a cave: long echoes in a very big room |
| `telephone` | Down an old phone line |
| `alien` | Not from here: higher, with a slow metallic sweep |
| `whisper` | Hoarse and breathy, with no pitch at all |

`voice_names()` lists them. A voice is only a handful of settings, and you can turn them yourself once it is on. A microphone has every setting a synth has, and a few words of its own:

```py
mic.pitch = 7                     # semitones up or down, -12 to 12, without getting faster or slower
mic.echo = 0.4                    # and reverb, chorus, distortion, crush, cutoff, pan, volume, as on a synth
mic.ring = 1                      # multiply the voice by a wave: mic.ring_speed = 50 is how fast (the robot)
mic.comb = 0.5                    # ring like a pipe at one note: mic.comb_tone = 110. mic.flanger sweeps it
mic.gain = 2                      # turn a quiet microphone up
mic.gate = -40                    # quieter than this (in dB) counts as silence. It starts at -50; "off" for none
```

Choosing another voice first puts back what the last one changed, so pick the voice and then turn the dials. `use_microphone("robot", listen=True, echo=0.3)` does it in one line.

With [dials](dials.md) the microphone is a synth too: `select("voice", mic, "voice")`, `dial("pitch", mic, "pitch")`, `toggle("listen", mic, "listening")`, `scope(mic)`, `meter(mic)`. They act on the microphone in the page, at once, however busy Python is, and the scope and the meter show your voice even while it is muted.

### The first moments

The browser asks about the microphone as soon as the scene calls `use_microphone()`, without waiting for a click. The sound itself still waits for [the first tap](#the-first-tap), so a scene that begins with the microphone says "Click, tap or press a key to turn the sound and the microphone on": until that touch nothing is heard and nothing is recorded, whatever the answer was.

### Recording

```py
take = record_sound(3)                  # three seconds of the microphone, starting now
take.on_done(lambda: take.play())       # when it is over, play it back
```

`record_sound` gives you the recording at once and does not wait: your scene carries on drawing, and the take fills up behind it. A take is a sample, so everything a sample does it does, even while it is still recording:

```py
take.play()                       # as you said it
take.play("E4")                   # higher and faster: middle C is its own pitch
take.reverse = True               # backwards
take.loop = True                  # round and round while its note is held
take.voice = "monster"            # any voice, afterwards
take.done, take.seconds           # is it over, and how long it is
```

- What is recorded is **your plain voice**, whether or not you are listening. The take is then given the voice the microphone has, so it plays back the way the microphone sounds, and you can change your mind afterwards: `take.voice = "none"` is you, and `take.sound_like(mic)` is the microphone as it is set now.
- `start_recording()` records until `stop_recording()`. It stops by itself after 30 seconds; `start_recording(max=60)` gives it longer, up to 120.
- One recording is made at a time: starting another ends the one before, which keeps what it had.
- `record_sound(3, effects=True)` records the voice after its effects instead of before. That only works while you are listening.
- `tune = record_output(10)` records everything that is played for ten seconds, in stereo, and `lead.record(4)` one synth alone.

### What is a frame late

The page has the microphone and makes the recording. Python is told what happened with the next frame's message, so:

- `take.done` and `take.seconds` change the frame **after** the recording ended, and `take.on_done(...)` is called then.
- `mic.state` is `"asking"` until a frame after the browser answered. `mic.ready` is `None` until then, and `mic.on_ready(fn)` calls your function with `True` or `False`.
- A file is saved a frame or two after the recording is over: `saved.done`.

Nothing in your scene ever waits for any of these: `update` and `draw` carry on. What you *hear* is not late at all, because the page does it: listening, a voice, a dial tied to the microphone, the start and the end of a recording on the exact sample. In a scene that can wait, `await take.when_done()` and `await mic.when_ready()` look again each frame until it is so:

```py
async def on_key_down(key):
    take = record_sound(2)
    await take.when_done()        # the scene goes on drawing meanwhile
    take.play()
```

### Saving

`save_sound(take, "hello.wav")` makes a WAV file from a recording or a sample. A recording that is still being made is saved when it is over. Where the file goes:

- **With `pyctures run`**, it is written beside your scene, like a file from `save_text`: the page hands Python the file, and Python writes it.
- **In a built page** (`pyctures build`), the browser downloads it. An app that shows the scene and keeps its files (the `storage` option in [Use it on your website](website.md#files-and-databases)) is given it with the scene's other files instead.
- `saved = save_sound(take, download=False)` saves nothing anywhere and hands Python the file's bytes: `saved.bytes`, once `saved.done`.

It gives back at once: `saved.done`, `saved.path` (where Python wrote it, or `None`) and `saved.on_done(...)`.

### With no microphone

A computer with no microphone, a person who says no, a page that is not allowed to ask: none of these stops your scene. Every function still works, the browser's console says once why there is no microphone and what to do about it, and a recording is simply empty and done (`take.seconds` is 0). `mic.state` is `"on"`, or says why not: `"refused"`, `"none"`, `"busy"` or `"unavailable"`.

A page has to be served over `https` or from `localhost` to be given a microphone (`pyctures run` is), and a page inside a frame needs `allow="microphone"` on the frame.

### The voice effects on a synth

The pitch shifter, the ring modulator and the comb are not only for voices. Every synth has them, under names that do not clash with its own `pitch` and `ring`:

```py
lead.pitch_shift = 12             # an octave up, with the same length
lead.ring_mod = 0.6               # bell-like and strange: lead.ring_speed = 300
lead.comb = 0.5                   # a metal pipe: lead.comb_tone, lead.comb_feedback
lead.flanger = 0.6                # the comb, sweeping: lead.flanger_rate
lead.voice = "robot"              # or a whole voice at once
```

Eight synths can use the pitch shifter or the comb at once.

## Drawing the sound yourself

`scope(lead)` and `meter(lead)` from [dials](dials.md) are drawn by the page and need nothing more. For a picture of the sound that is your own, three functions give you what a synth is doing:

```python
from pyctures import *
from synths import *

lead = make_synth("lead")

def on_mouse_down(x, y):
    lead.play(["C4", "E4", "G4"], 2)

def draw():
    background("black")
    wave = lead.samples()             # about a thousand numbers from -1 to 1
    for i in range(0, len(wave) - 8, 8):
        line(i * width / len(wave), height / 2 - wave[i] * 200, (i + 8) * width / len(wave), height / 2 - wave[i + 8] * 200, "orange", 2)
    left, right = lead.level()        # how loud, each from 0 to 1
    rect(20, height - 20 - left * 200, 16, left * 200, "lime")
    text("notes: %s" % lead.notes(), width / 2, 40, "white", 20, "centre")
```

`sound_output()` has the same three for everything that is sounding, the microphone has them for your voice, and a song has them a channel at a time (`song.channel(3).level()`). They are **a frame late**: Python cannot ask the page and be answered, so the first call asks the page to start saying, and from the next frame on each call gives what the page said with that frame. The very first call gives an empty list, zeros and no notes. The page stops saying a second and a half after your scene stops asking.

## Recording a video with sound

**In Circuitry**, press the video button under the scene, choose a size and 30 or 60 frames a second, and press Record. The scene starts again from its beginning and is recorded until you press Stop. You get one `.mp4` file with the pictures and the sound in it, saved beside the scene (or to Photos or a folder you choose, on an iPad).

The sound in the video is exactly in step with the pictures, however slowly the frames were made. A recorder gives a scene one frame at a time, and a frame may take much longer to make and encode than the sixtieth of a second it stands for. So while a scene is recorded its sound is not played by the sound card: it is worked out for one frame at a time, on the same clock as the pictures, and you hear nothing until you play the video. Your scene does not change. `sound_time()`, `beat()` and `sleep()` go by the video's time, not the computer's; a note you play in a frame starts on that frame's first sample; `after=`, `at=` and `beat=` mean what they always did; and recording the same scene twice gives the same sound. What a scene reads back (`lead.samples()`, a song's position) is a frame late, as it is when it is not recorded. There is no microphone in a recording.

**On a page of your own** a scene can be run a frame at a time, by whoever is making the film: `mount(el, { src, stepped: { fps: 60 } })`, then `await scene.step()` for each frame after the first, and `scene.sound.take()` for the samples. [Putting scenes on a website](website.md) has the details.

## Mistakes

A mistake is said in plain words on the line that made it, with what was probably meant:

```
play_sound("lazer"): there is no sound called "lazer". Did you mean "laser"? The sounds are: coin, jump, laser, …
make_synth(): there is no setting called "cutof". Did you mean "cutoff"?
"robt" is not a voice. Did you mean "robot"? The voices are: robot, chipmunk, monster, cave, telephone, alien, whisper, and "none"
```

## Examples

- [Sound Catcher](../examples/sound_catcher.py): a game with sound effects
- [Tune](../examples/tune.py): drums, a bass and a melody, with lights in time
- [Arpeggio Chords](../examples/arpeggio_chords.py): one voice playing chords, as a sound chip would
- [Synth Panel](../examples/synth_panel.py): dials and a piano keyboard on the screen (see [Dials and a keyboard](dials.md))
- [MIDI Keyboard](../examples/midi_keyboard.py): a synth that a MIDI keyboard plays, with dials its knobs learn
- [MIDI Lights](../examples/midi_lights.py): a ball and a bell for every key, from `on_midi_note`
- [Voice Changer](../examples/voice_changer.py): your voice as a robot or a monster, with a voice to pick, dials, a scope, and record and play
- [Sampler](../examples/sampler.py): record a word and play it on the keys

## How it works

No sound is worked out in Python. Each function writes a command, plain data, and a frame's commands travel to the page inside the frame's own message, as drawing does. The page loads the sound engine the first time a scene uses it, and plays the commands on the browser's audio thread, so sound never stutters when Python or the picture is busy. A scene that makes no sound loads nothing extra.

It is the same wherever the scene's Python runs: in the browser (`pyctures build`), in your own Python (`pyctures run`), or on another computer.

The same library for JavaScript is [synths.js](https://github.com/johnwylie70/synths.js); the Python one on its own is [synths](https://github.com/johnwylie70/synths-py), where every function and setting is described. An app that shows scenes can take the commands and play them itself: see [Use it on your website](website.md#sound).

MIDI goes the same way. Its functions write commands too, and the page, where the devices are, carries them out: it plays a synth from a keyboard and turns a setting from a knob itself, and hands Python what was received with the next frame. Its code is one more file of the sound library, loaded only by a scene that uses MIDI.

The microphone is the page's as well. `use_microphone()` writes a command, and the page asks the browser when that command arrives: a scene that never calls it never asks. The page listens, changes the voice and records on the audio thread, and tells Python what happened (the microphone is on, a recording is over, a file is saved) with the next frame. What Python reads back (`lead.samples()`, `song.position`) comes the same way, only while it is being read.
