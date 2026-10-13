# Sound and music

A scene can make sound: a game sound where something happens, a note, a tune that goes round, a synth you shape yourself, a whole song from a file. The sound library is called **synths**, and it comes with Pyctures. One line at the top of the scene brings its functions in:

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
| `lead.set(cutoff=4000, slide=2)` | Slide there over two seconds |
| `lead.arp("Cm7")`, `arp = lead.start_arp("Am")` | A chord from one voice, as a fast arpeggio. `arp.change("F")` changes it as it plays |

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

A song is a whole piece of music in one file, played by the sound engine itself: a tracker's `.mod` or `.xm` file, or a song in synths' own format.

```py
song = play_song("tune.mod")          # it goes round and round until it is stopped

song.pause()
song.resume()
song.volume = 0.5
song.stop()
```

`play_song("tune.xm", repeat=False)` plays it once. One song plays at a time, and your own notes and game sounds play over it. It starts at the first tap, like a tune.

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
- [MIDI Keyboard](../examples/midi_keyboard.py): a synth that a MIDI keyboard plays, with dials its knobs learn
- [MIDI Lights](../examples/midi_lights.py): a ball and a bell for every key, from `on_midi_note`

## How it works

No sound is worked out in Python. Each function writes a command, plain data, and a frame's commands travel to the page inside the frame's own message, as drawing does. The page loads the sound engine the first time a scene uses it, and plays the commands on the browser's audio thread, so sound never stutters when Python or the picture is busy. A scene that makes no sound loads nothing extra.

It is the same wherever the scene's Python runs: in the browser (`pyctures build`), in your own Python (`pyctures run`), or on another computer.

The same library for JavaScript is [synths.js](https://github.com/johnwylie70/synths.js); the Python one on its own is [synths](https://github.com/johnwylie70/synths-py), where every function and setting is described. An app that shows scenes can take the commands and play them itself: see [Use it on your website](website.md#sound).

MIDI goes the same way. Its functions write commands too, and the page, where the devices are, carries them out: it plays a synth from a keyboard and turns a setting from a knob itself, and hands Python what was received with the next frame. Its code is one more file of the sound library, loaded only by a scene that uses MIDI.
