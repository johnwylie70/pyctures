# Make it talk: say()

```python
background("navy")
circle(width / 2, height / 2, 60, "gold")
say("Hello")
```

That is a whole program. Run it and the computer says "Hello". There is nothing to import and nothing to set up: no account and no internet, because the voice is the one your device already has.

Change the word and run it again. (The `say_hello` example is a face that talks when you click it.)

```py
say("My name is Sam")
```

One thing to know from the start: you hear this voice as the scene runs, but it is **not recorded** into a video file.

## How long does it take?

`say` gives back how many seconds the line takes, so you can wait for it to finish before the next thing happens.

```python
background("navy")
circle(width / 2, height / 2, 60, "gold")

await sleep(say("Hello"))
await sleep(say("This is my first talking program"))
say("Goodbye")
```

Without a better voice behind it the length is a guess: two and a half words a second, and never less than 0.8 of a second. It is the same guess every time, so a scene that waits for it always works out the same.

## A talking face

`mouth` draws a mouth for you. It is a straight line while nothing is being said, and it opens wider the louder the voice is. So a face that talks is a face, a `say`, and a `mouth`:

```python
def on_mouse_down(x, y):
    say("Hello! I am talking.")

def draw():
    background("midnightblue")
    circle(width / 2, height / 2, 90, "gold")
    circle(width / 2 - 30, height / 2 - 25, 8, "black")
    circle(width / 2 + 30, height / 2 - 25, 8, "black")
    mouth(width / 2, height / 2 + 30)
```

Click the face. (The `say_hello` example is this, with the face as big as the screen allows.)

`mouth(x, y)` puts the middle of the mouth at `x, y`. Say how it looks after:

```python
say("I can talk three ways at once")

def draw():
    background("midnightblue")
    mouth(width / 2, height / 3, style="oval")
    mouth(width / 2, height / 2, style="smile", color="crimson")
    mouth(width / 2, height * 2 / 3, style="robot", size=100)
```

- `style` is `"oval"` (a cartoon mouth, the one you get if you say nothing), `"smile"`, or `"robot"` (five bars, like a speaker).
- `size` is how wide the mouth is, in pixels. If you leave it out, it is a sixth of the screen's shorter side, so the same program works on a phone and on a wide video.
- `color` is the colour it is drawn in. It is black if you leave it out.

Two more functions tell you what the voice is doing, for a face of your own:

```python
say("Watch the circle")

def draw():
    background("gold" if speaking() else "gray")
    circle(width / 2, height / 2, 10 + voice_level() * 30, "white")
```

- `speaking()` is `True` while a line is being said, and `False` otherwise.
- `voice_level()` is how loud the voice is right now, from 0 (quiet) to 1 (loud). It moves smoothly, so a shape that follows it does not flicker.
- `voice_shape()` is the mouth now as a dictionary with `width`, `height` and `viseme`: `height` is the level, `width` is 0 for a round mouth ("oo") up to 1 for a spread one ("ee"), and `viseme` is a word for it: `"closed"`, `"oo"`, `"oh"`, `"ah"`, `"mid"` or `"ee"`. The `"oval"` mouth uses it, and so can a face of your own:

```python
say("Hello there, my friend")

def draw():
    background("navy")
    shape = voice_shape()
    ellipse(width / 2, height / 2, 40 + shape["width"] * 80, 10 + shape["height"] * 80, "gold")
```

### Is the mouth really lip-synced?

**Not with the free voice.** The browser sends that voice straight to the speaker and gives the scene no sound to listen to. So the mouth is *made up from the words*: the words are split into syllables, and each one opens the mouth for its vowel ("a" tall, "o" round, "u" small and round, "e" and "i" wide), shuts between syllables, shuts the lips first after an "m", "b" or "p", and stays shut for a moment at the end of a word and for longer at a comma or a full stop. A little jitter, the same every time, keeps it from looking like a machine. It starts when the browser says the speech started, moves on to each word as the browser says it got there, and stops when the browser says it ended. The same words always give the same mouth, but it moves like a talking mouth, not with the actual sounds. It is a good face for a kid's program, and it is not true lip-sync.

**With a recorded voice it is.** When an app gives the scene a recording of the line (see the voice host below), `voice_level()` is the real loudness of that recording at that moment, so the mouth follows the sound: every hundredth of a second it opens as far as the sound is loud, and how often the sound's wave crosses zero says whether it is a low, round sound ("oh", "ah") or a high, spread one ("ee", "s"), so the mouth gets wider or rounder with it, and it shuts between words. In a video recorded a frame at a time, it is exact for every frame, and two recordings are the same.

Python is told the level with each frame, so `voice_level()` is the level of the frame being drawn, not of a moment before or after it.

## A different voice, or another language

```py
say("Half of the width is the middle.", voice="calm")
say("Bonjour tout le monde", lang="fr")
```

`voice` is the name of a voice on your device (the names differ from one device to the next, and a name that is not found is simply left out), and `lang` is the language, `"en"` unless you say. If the device has a voice for the language, it is used.

## Voices and characters

Two faces can talk to each other, and each can have a voice of its own. A **speaker** is a character: it has a voice, and it says lines.

```python
sam = speaker(voice="deep")
pip = speaker(voice="squeaky")

def on_mouse_down(x, y):
    sam.say("Hello Pip!")
    pip.say("Hello Sam! You sound funny.")
    sam.say("So do you!")

def draw():
    background("midnightblue")
    circle(width / 3, height / 2, 60, "gold" if sam.speaking() else "orange")
    circle(width * 2 / 3, height / 2, 60, "hotpink" if pip.speaking() else "pink")
    mouth(width / 3, height / 2 + 20, speaker=sam)
    mouth(width * 2 / 3, height / 2 + 20, speaker=pip)
```

Click, and they talk **in turn**. Lines said by speakers go into one queue, so Pip waits until Sam has finished, and nobody talks over anybody. You do not have to wait yourself.

What a speaker can do:

- `sam.say("Hello")` says a line, and gives back how many seconds it takes, like `say`.
- `sam.speaking()` is `True` only while Sam's own line is being said.
- `sam.level()` and `sam.shape()` are Sam's own `voice_level()` and `voice_shape()`.
- `mouth(x, y, speaker=sam)` draws a mouth that opens only while Sam talks. (`voice_level(sam)`, `voice_shape(sam)` and `speaking(sam)` do the same. With no speaker they mean whoever is talking.)

### Choosing a voice

`speaker(voice=None, pitch=1, rate=1, lang="en", name=None)`: every part is optional.

- `voice` is the exact name of a voice on your device, or one of these words: `"robot"`, `"high"`, `"deep"`, `"squeaky"`, `"slow"`, `"fast"`. Each word sets a pitch and a speed and looks for an installed voice that suits it. They work on every device: where none suits, the device's usual voice is used with the new pitch and speed.
- `pitch` is how high the voice is, from 0 to 2 (1 is normal). `rate` is how fast, from 0.1 to 4 (1 is normal). They are multiplied with the word's own.
- `lang` is the language, `"en"` unless you say. `name` is a name for the speaker, which an app can show.
- `like` describes the voice in words instead of a name: `like={"gender": "female", "age": "child"}` (and `pitch`, `rate`). `fallback` is a list of voices to try if the first is not there: `fallback=["system:Samantha", "high"]`. A voice can start with where it comes from (`system:Samantha`, `kokoro:af_heart`, `hq:nova`, `draft:`), and a name with nothing before it is looked for on your device first. So a speaker is a character, and the computer finds the best voice it has for it, on any device or app.

```py
robot = speaker(voice="robot")
slowpoke = speaker(voice="slow", pitch=1.3)
```

`voices()` lists the voices your device has, English first, as dictionaries with `name`, `lang`, `default` and `source`. Some devices load their voices a moment after the page starts, so the list can be empty at first: ask again a little later.

```py
names = [v["name"] for v in voices()]
```

### When does a line start?

`sam.say(...)` gives back how long the line is. If you also want to know when it starts (because it waits its turn), use `say_at`, which gives `{"start", "duration", "end"}`, all in seconds from now:

```python
background("midnightblue")
circle(width / 2, height / 2, 60, "gold")

sam = speaker(voice="deep")
pip = speaker(voice="high")

sam.say("Hello")
reply = pip.say_at("Hi!")
# reply["start"] is when Hi begins: after Hello is over.
await sleep(reply["end"])
```

`say_at("Hi", speaker=sam)` works on its own too. A line said with plain `say` (no speaker) is not in the queue: it starts at once.

### What the free voice and a recorded voice do with these

The free voice (the device's own) follows `pitch` and `rate`. A voice that an app has recorded is the app's: it plays the recording of the line for that speaker's voice, and whether it can change its pitch and speed is up to the app. Either way each speaker's mouth follows its own line.

## What the free voice can and cannot do

It is the voice the browser speaks with, so:

- It is free, works offline, and nothing you type is sent anywhere.
- It sounds a little different on each device, and some devices have few voices.
- **You hear it live, but it cannot be recorded.** The browser sends it straight to the speaker, so a video made from a scene has the pictures, the music and the sound effects, but not these words. When a scene is being recorded, a line with no recorded voice behind it is reported in the browser's console, so you know which lines are missing, instead of the video quietly being silent there.

A better voice that does go into a video is possible with an app that supplies one. That is the next part.

## For an app: a voice host

`say` never makes a voice itself. It asks a **voice host**, an object you give to `mount` (`mount(el, { src, voice: host })`), or put on the page as `window.pictureHost.voice`. It never generates anything: not when a scene runs, not ever. Whatever makes the voices (and spends the money, if there is any) is the host's, and it only does so when a person asks. The host has three functions, written in JavaScript:

```js
const host = {
  // What is known about this line right now, or null.
  lookup({ text, voice, lang }) {
    return {
      key: "9f2c0a41b7d3e856",
      file: "voice/9f2c0a41b7d3e856.mp3",
      duration: 2.31,
      provider: "mine", voice: "calm", lang: "en",
    }
  },
  // A line was asked for. Keep a list, for a "make the voices" button.
  note({ text, voice, lang, source, line }) {},
  // Optional: speak the line in your own draft voice.
  speakDraft({ text, voice, lang }) {},
}
```

- `lookup` is how a line with a recorded voice is found. The scene then plays `file` (a relative `file` is looked for beside the scene; an entry can also give `url`), and `say` gives back the entry's `duration`, which is measured, not guessed.
- `note` is told of every different line the scene asks for, whether it has a recording or not, once each time a scene runs: its `text`, `voice`, `lang`, whether it was written out in the code (`source: "literal"`, with its `line`) or made while the scene runs (`"runtime"`), such as `say(f"Score {score}")`. A button that says "make the voices for 3 lines" can be built from these minus the ones `lookup` has.
- `speakDraft` is optional. Without it the browser's speech is used.
- A host may also have `resolveVoice(spec)` (spec is `{ name, voice, like, fallback, pitch, rate, lang }`), which casts the speaker in its own set and gives back `{ voice, exact, note }`; `exact: false` means a stand-in was chosen. `lookup` then gets that voice, and `note` gets `resolved`, `exact` and the host's `note`. Without it the device's best match is used.
- A line said by a speaker has its `voice` set to the speaker's voice (`"deep"`, `"Daniel"`, a voice of the host's) and, when they are not the normal 1, its `pitch` and `rate`; `note` also gets the speaker's `name`. Use them to choose the recording. A host may also have an optional `voices()`, giving the voices it can make (each a name, or `{ id, name, lang, provider }`), which `voices()` adds to the device's.

**One difference from JavaScript.** Your Python runs apart from the page, so it cannot be answered on the spot. The page tells it the measured length of every line that is written out in the code (`say("Hello")`, not `say(f"Hello {name}")`) before it starts. A line made while the scene runs gets the estimate the first time it is said, and its measured length from then on and the next time the scene is run. The recorded voice itself always plays at the right moment: only the number `say` gives back is late for such a line.

### Recording a video

A scene that is recorded a frame at a time (`mount(el, { src, stepped: { fps: 60 } })`, see [Sound and music](sound.md)) plays the entry's file through the stepped sound, so the voice begins on the exact sample of the frame where `say` was called. A line that `lookup` does not have is not spoken, since the draft voice cannot be recorded: it is told to `note`, and said once in the console with `console.warn`, so a render can stop and tell you which lines to make first.

## How it is loaded

`say` is a small part of its own, `voice/say.js` and `voice/pysay.py` beside `pyctures.js`, fetched only for a file that calls `say(`. A scene that says things in the draft voice loads no sound library. A scene with a voice host, or one that is recorded, does, since a recorded voice is played through the sound.

In pictures.js the same functions are `say(text, { voice, lang, speaker })`, `sayAt(...)`, `speaker({ voice, pitch, rate, lang, name })`, `voices()`, `speaking(speaker)`, `voiceLevel(speaker)`, `voiceShape(speaker)` and `mouth(x, y, { size, style, color, speaker })`.

## Related

- [Sound and music](sound.md)
- [Function index](function-index.md#talking)
