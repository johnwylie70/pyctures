# Sound and music

A scene can make sound: a game sound where something happens, a note, a tune that goes round, a synth you shape yourself. The sound library is called **synths**, and it comes with Pyctures. One line at the top of the scene brings its functions in:

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
| `note = lead.start("E4")` | A note that stays until `note.stop()`. `note.slide_to("G4", 0.5)` slides it |
| `lead.stop()` | Let go of every note |
| `lead.play_notes("C4 E4 G4", 0.25)` | A tune on this synth |
| `lead.cutoff = 800` | Change a setting; notes already sounding change too. `print(lead.cutoff)` reads it back |
| `lead.set(cutoff=4000, slide=2)` | Slide there over two seconds |
| `lead.arp("Cm7")`, `chord = lead.start_arp("Am")` | A chord from one voice, as a fast arpeggio. `chord.change("F")` changes it as it plays |

The settings you will use most:

| Setting | What it is |
|---|---|
| `wave` | The raw sound: `"sine"`, `"triangle"`, `"saw"`, `"square"` |
| `volume`, `pan` | How loud (1 is normal), and left (-1) to right (1) |
| `attack`, `decay`, `sustain`, `release` | The shape of a note's loudness: seconds to reach full, seconds to fall to the `sustain` level, and seconds to die away |
| `cutoff`, `resonance` | How bright (20 to 20000), and a whistle at the cutoff (0 to 1) |
| `octave`, `pitch` | Move every note by octaves, or by semitones |
| `vibrato`, `vibrato_rate` | A wobble of pitch |
| `echo`, `reverb`, `chorus` | How much of the synth goes to each effect (0 to 1) |
| `distortion`, `crush` | Grit, and the bits each sample keeps (4 is an old games console) |

`setting_names()` lists every one. The echo, the reverb and the chorus are shared by all synths, and are shaped with `set_effects(echo_time=0.3, echo_feedback=0.5, reverb_size=0.8)`.

## Samples

A sample is a recorded sound in a file beside the scene: a `.wav`, or anything else a browser can read (`.mp3`, `.ogg`).

```py
kick = load_sample("sounds/kick.wav")
kick.play()                       # as it was recorded
kick.play("E4")                   # higher: a sample is a synth, and "C4" is its own pitch
```

There is nothing to wait for: play it straight away, and it sounds as soon as the file has arrived. `pyctures build` finds the sound files a scene names and takes them along: copied beside the scene in a folder, or inside a single `.html` file.

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

## Songs

`play_song("tune.mod")` is for tracker songs (`.mod`, `.xm`). It is **not ready yet**: today it plays nothing and says so once, and the rest of your sound is not affected.

## Mistakes

A mistake is said in plain words on the line that made it, with what was probably meant:

```
play_sound("lazer"): there is no sound called "lazer". Did you mean "laser"? The sounds are: coin, jump, laser, …
make_synth(): there is no setting called "cutof". Did you mean "cutoff"?
```

## Examples

- [Sound Catcher](../examples/sound_catcher.py): a game with sound effects
- [Tune](../examples/tune.py): drums, a bass and a melody, with lights in time
- [Arpeggio Chords](../examples/arpeggio_chords.py): one voice playing chords, as a sound chip would
- [Synth Panel](../examples/synth_panel.py): dials and a piano keyboard on the screen (see [Dials and a keyboard](dials.md))

## How it works

No sound is worked out in Python. Each function writes a command, plain data, and a frame's commands travel to the page inside the frame's own message, as drawing does. The page loads the sound engine the first time a scene uses it, and plays the commands on the browser's audio thread, so sound never stutters when Python or the picture is busy. A scene that makes no sound loads nothing extra.

It is the same wherever the scene's Python runs: in the browser (`pyctures build`), in your own Python (`pyctures run`), or on another computer.

The same library for JavaScript is [synths.js](https://github.com/johnwylie70/synths.js); the Python one on its own is [synths](https://github.com/johnwylie70/synths-py), where every function and setting is described. An app that shows scenes can take the commands and play them itself: see [Use it on your website](website.md#sound).
