# Kinetic text

Words that move: for the first seconds of a video, a title, a caption that needs to catch the eye. Each effect is one line, and the same line works in a wide video (1920 by 1080) and a tall one (1080 by 1920): the words lay themselves out from the size of the scene.

```python
def draw():
    background(house_style.palette.ink)
    word_slam("Learn *to code*. From zero.")
```

Nothing to import. The part that does this is loaded only by a scene that uses one of its names. See the examples `kinetic_gallery.py` (every effect in turn) and `hook.py` (six seconds that open a video). It is the same library as [pictures.js's](https://www.circuitry.dev/pictures), so the same call draws the same pixels in both.

## The effects

| Call | What you see |
|---|---|
| `word_slam(text, ...)` | The words land one at a time, hard, and the whole text shakes a little |
| `letter_wave(text, ...)` | The letters appear one after another, then ride a wave; `speed=` changes it |
| `letter_bounce(text, ...)` | The letters drop in and bounce |
| `typewriter_text(text, ...)` | Typed out, a little unevenly, with a cursor that blinks after |
| `glitch_text(text, ...)` | Red and blue copies split apart and slices jump sideways, strongly at first and in short bursts after; `amount=` is how much |
| `mask_reveal(text, ...)` | A wipe uncovers the text; `direction=` is `"right"` (the usual), `"left"`, `"up"` or `"down"` |
| `scale_pop(text, ...)` | The words rise into place and each `*starred*` word swells and settles |
| `ticker_text(text, ...)` | One line scrolling along a strip, for as long as it is on; `speed=` changes it |
| `count_up("12,000+", ...)` | A number counting up, with its commas, decimals and the words round it; `from_=` is where it starts (0) |
| `highlight_sweep(text, ...)` | A highlighter sweeps under the `*starred*` words (or under each line, if none) |

`kinetic_text("slam", text, ...)` is any of them by a short name: `"slam"`, `"wave"`, `"bounce"`, `"type"`, `"glitch"`, `"reveal"`, `"pop"`, `"ticker"`, `"count"` or `"highlight"`. `kinetic_effects()` gives that list of names.

Put stars round a word to make it the one that matters: `"Make it *pop*"`. It is coloured in every effect, and the effects above that single words out use it.

## Options

All of them are optional, and all are keywords.

| Option | Meaning |
|---|---|
| `start` | Seconds into the scene when it begins (0). Before that nothing is drawn |
| `duration` | Seconds the movement takes. After that the text stays as it ended; `hold=False` takes it away instead |
| `t` | The time to draw at. Left out, it is the scene's own seconds, `kinetic_time()` |
| `x`, `y` | Where the middle of the text goes, as a share of the scene: 0 is the left or top, 1 the right or bottom. The middle by default |
| `size` | `"hook"`, `"title"`, `"body"` or `"caption"` (`house_style.scale`), or a number: up to 1 is a share of the scene's shorter side, above 1 is pixels |
| `style` | `"playful"`, `"techy"` or `"calm"`, or a dict that changes one: `{"voice": "techy", "accent": "hotpink"}` |
| `colour` (or `color`), `accent` | The text's colour, and the colour of the starred words |
| `beat` | A number of beats, or anything with a `.beat` (such as the music object a tracker song gives): the text pulses on each beat. Without it nothing pulses; `pulse=0.1` makes it stronger |
| `safe` | A dict `{"top": ..., "bottom": ..., "side": ...}`, shares of the scene to keep clear, in place of the usual |
| `seed` | Changes the shaking and the unevenness (1) |

A call gives back nothing. (pictures.js gives back where the text is and how far along it is; here the page has not drawn it yet when your code goes on.)

## Wide and tall

A scene is laid out from its own size, so the same call makes a wide video and a tall one. In a tall one the text wraps onto more lines. Two rules hold in both:

- **Safe area.** Text stays inside the part of the scene that phone apps leave clear. In a tall scene that is the middle: 14 percent is kept clear at the top and 18 percent at the bottom, for the buttons and captions the app lays over the video. In a wide one it is 5 percent all round. `kinetic_safe()` gives the area in pixels (with `.left`, `.top`, `.right`, `.bottom`, `.width` and `.height`) if you want to put something of your own inside it.
- **Readable.** Text is never smaller than 3 percent of the scene's height, however small a `size` you ask for. A text that will not fit is wrapped onto more lines and only then made smaller, and never below that.

## Time

An effect is a function of the time it is given, so a recorded video is exact and a frame can be drawn again. By default the time is the scene's seconds, which start at 0 and go on by one frame's time each frame (the recorder's own time, in a scene recorded a frame at a time). `kinetic_time()` reads them; `kinetic_time(5)` sets them, and `kinetic_time(5, hold=True)` stops them there. To time one effect by hand give it `t=`, as the gallery does, so that each effect starts at 0 in its own slot.

The shaking and the unevenness are never random: they come from a fixed recipe of the letter's place, the time and `seed`, so the same time always draws the same picture. `seeded_random(seed)` gives you a random function of your own that does the same, and gives the same numbers as pictures.js's.

## The house style

`house_style` is what every video of ours shares, and the effects read it. It is a dictionary you can also read with a dot:

- `house_style.palette`: `ink` (the dark backdrop), `paper`, `dim`, and `blue`, `cyan`, `pink`, `yellow`, `green`
- `house_style.fonts`: `display` and `mono`
- `house_style.scale`: the sizes `hook`, `title`, `body` and `caption`, as shares of the scene's shorter side
- `house_style.minimum`: 0.03, the least size, as a share of the height
- `house_style.safe`: the safe area of each shape
- `house_style.voices`: **playful** (big, round, heavy, springy), **techy** (monospace, cyan, little spring) and **calm** (light, quiet, no spring)

Changing it in your scene does not change the effects (they read the page's copy); pass your own `style=` dict to one call instead.
