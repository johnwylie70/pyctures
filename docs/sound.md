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

`setting_names()` lists every one. The echo, the reverb and the chorus are shared by all synths, and are shaped with `set_effects(echo_time=0.3, echo_feedback=0.5, reverb_size=0.8)`. The reverb is one room that every synth sends into: `set_effects(reverb_type="hall")` chooses what kind of space it is (`"room"`, `"hall"`, `"plate"`, `"cathedral"` or `"spring"`), and `reverb_decay=3` how many seconds it rings. A shared setting has one value whoever set it: `lead.reverb_type = "hall"` is the same thing, and every synth reads it back.

## Samples

A sample is a recorded sound in a file beside the scene: a `.wav`, or anything else a browser can read (`.mp3`, `.ogg`).

```py
kick = load_sample("sounds/kick.wav")
kick.play()                       # as it was recorded
kick.play("E4")                   # higher: a sample is a synth, and "C4" is its own pitch
```

A sample can also be the wave of any synth, under its filter and its envelope: `lead.sample = load_sample("sounds/piano.wav")` turns its wave to the recording (`lead.wave = "saw"` goes back), and `make_synth(sample="sounds/piano.wav", note="C4", cutoff=1800)` does it in one line.

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

A song is made of channels, counted from 0, and of patterns it plays in turn:

```py
song.mute(2)                          # silence channel 2. song.mute(2, False) or song.unmute(2) brings it back
song.solo(0)                          # hear only the channels that are soloed. song.solo("all", False) hears the rest again
song.loop_pattern()                   # stay on the pattern that is playing. song.loop_pattern(False) carries on
song.seek(2)                          # jump to the third part of the song (and seek(2, 16): its row 16)
```

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
