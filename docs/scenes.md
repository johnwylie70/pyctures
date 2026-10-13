# Scenes

A program can be made of several scenes: a title screen, the game and a game-over screen, or the parts of a show that play one after another. Each scene has its own `setup`, `update`, `draw` and `on_` functions, and starts empty. This page shows two screens of a game, then scenes on a timer, then the transitions between them, then the scrubber.

A file with no scenes in it is one scene, as it always was. Nothing on this page changes it.

## Two screens

A scene is a class with `Scene` in brackets. Inside it go the same functions a file has, each with `self` as its first name.

```python
class Title(Scene):
    def draw(self):
        background("midnightblue")
        text("Click to start", width / 2, height / 2, "white", 30, "centre")

    def on_mouse_down(self, x, y):
        go("Game")


class Game(Scene):
    def setup(self):
        self.x = 0

    def update(self, dt):
        self.x = (self.x + 200 * dt) % width

    def draw(self):
        background("black")
        circle(self.x, height / 2, 20, "gold")

    def on_mouse_down(self, x, y):
        go("Title")
```

You do not create a scene or call anything. Pyctures finds every `Scene` class in the file. The first one written starts, and `go("Game")` changes to another by its name. `go(Game)`, with the class itself, does the same.

Three things to know:

- **A scene's own variables go on `self`.** `self.x` belongs to the scene. Set them in `setup()`.
- **`setup()` is called every time the scene begins**, so each game starts afresh.
- **Only the scene on show is called.** While `Title` is on show, `Game`'s `update`, `draw` and `on_mouse_down` are not called.

### What is shared and what is a scene's own

Anything made at the top level of the file, outside every class, is shared by all the scenes: the score, a synth, a picture that was loaded. A scene that changes one says `global`, as any function does.

```python
score = 0     # shared: Game adds to it and GameOver shows it
```

Each scene starts empty:

| A scene's own | What happens when the scene ends |
|---|---|
| Its variables on `self` | Forgotten. The next time it begins they are set again by `setup()` |
| Dials and other controls it made in `setup()` (`dial`, `slider`, `button`…) | Taken away. Controls made at the top level of the file stay |
| The picture | The next scene starts with a clear canvas and the drawing settings (`ctx.fill_style`, `ctx.font`…) as they start |

Sound is not a scene's own. A song or a tune that is playing goes on playing across scenes until something stops it (`stop_sound()`, `song.stop()`). To stop it with a scene, do so in the scene's `on_stop(self)`, which is called when the scene ends.

The file's own top-level functions still work. A `def on_key_down(key):` outside every class is called for every key, before the scene's own, whichever scene is on show: a good place for a key that mutes the sound. A top-level `draw()` is drawn before the scene's.

### Changing scene

| Call | What it does |
|---|---|
| `go("Game")`, `go(Game)` | Change to that scene. Capital letters in the name do not matter |
| `next_scene()` | Change to the next scene written. After the last one comes the first |
| `restart()` | Begin this scene again, from empty |
| `go("Menu", keep=True)` | Go back to a scene as it was left: see below |

The change happens at the start of the next frame, so the function that asked for it runs to its end.

`go("Menu", keep=True)` goes back to a scene with its variables as they were when it was left. Its `setup()` is not called again. If the scene has a `resume(self)`, that is called. Use it for a pause screen: the game goes to `"Pause"`, and the pause screen goes back with `go("Game", keep=True)`. Controls the scene made are not kept; make them again in `resume()`.

### Without classes

If you are not ready for classes, `scene` groups plain functions under a name.

```python
def draw_title():
    background("midnightblue")
    text("Click to start", width / 2, height / 2, "white", 30, "centre")

def draw_game():
    background("black")
    circle(mouse.x, mouse.y, 20, "gold")

def start_game(x, y):
    go("game")

def back_to_title(x, y):
    go("title")

scene("title", draw=draw_title, on_mouse_down=start_game)
scene("game", draw=draw_game, on_mouse_down=back_to_title)
```

The names are the ones a class would use: `setup`, `update`, `draw`, `on_mouse_down`, `on_key_down` and the rest, and the settings below (`length=4`, `transition="wipe"`). Scenes made this way keep their variables at the top level of the file, so they are not emptied when a scene begins: set them in the scene's `setup`.

`examples/three_screens.py` is a whole game with a title, the game and a game-over screen.

## Scenes on a timer

Give a scene a `length` in seconds and it ends by itself. The next scene written begins, and after the last one the first comes round again.

```python
class Intro(Scene):
    length = 4

    def draw(self):
        background("navy")
        text("Part one", width / 2, height / 2, "white", 40, "centre")


class Main(Scene):
    length = 8

    def draw(self):
        background("black")
        circle(width * scene_progress, height / 2, 30, "tomato")
```

| Name | What it is |
|---|---|
| `scene_time` | Seconds since this scene began |
| `scene_progress` | How far through its length the scene is, from 0 to 1. It is 0 in a scene with no length |
| `scene_name` | The name of the scene on show |

`update(dt)` works as it always did.

### Lengths in beats

A scene that goes with music can be so many beats long, or so many bars. A bar is four beats.

```python
from synths import *

set_tempo(120)

class Verse(Scene):
    bars = 4        # 16 beats: 8 seconds at 120 beats a minute

class Break(Scene):
    beats = 8
```

The beats are the sound library's (`set_tempo`, `beat()`), so a scene ends on the beat however the frames fall. In a program with no sound a beat is half a second. See [Sound and music](sound.md).

To end a scene when a song reaches a place of its own, ask the song in `update` and call `next_scene()`:

```python
from synths import *

song = play_song("tune.mod")

class Opening(Scene):
    def update(self, dt):
        if song.position["order"] >= 2:
            next_scene()
```

### Settings for every scene

`config`, at the top of the file, sets things for every scene.

```python
config(loop=False, transition="crossfade", transition_time=0.8)
```

| Setting | Starts as | What it is |
|---|---|---|
| `loop` | `True` | After the last scene, begin the first again. With `False` the last scene stays on show |
| `transition` | `"cut"` | How every scene arrives, unless it says otherwise |
| `transition_time` | `0.5` | How long a transition takes, in seconds |
| `transition_color` | `"black"` | The colour a `"fade"` goes through |
| `beats_per_bar` | `4` | How many beats `bars = 1` is |

## Transitions

A scene can arrive with a transition. Set it on the scene:

```python
class Main(Scene):
    transition = "crossfade"
    transition_time = 0.8
```

or say it when you change scene:

```python
go("Game", transition="wipe", transition_time=0.5)
```

| Transition | What you see |
|---|---|
| `"cut"` | The new scene at once. This is what happens when nothing is said. `"none"` is the same |
| `"crossfade"` | The old scene fades into the new one |
| `"fade"` | The old scene fades to a colour, and the new one comes out of it. `transition_color = "white"` changes the colour |
| `"wipe"` | An edge crosses from the left with the new scene behind it. `"wipe_left"`, `"wipe_up"` and `"wipe_down"` cross the other ways |
| `"slide_left"` | The old scene slides out to the left and the new one follows it in. Also `"slide_right"`, `"slide_up"`, `"slide_down"` |

During a transition the old scene is a still picture of its last frame. The new scene has already begun: its `setup()` has been called and its `update` and `draw` are running underneath. A transition starts and ends gently.

**A transition is smooth however busy Python is.** Python only tells the page which transition to make. The page keeps the old scene's last picture and fades, wipes or slides it away itself, at the screen's own rate, while your new scene's frames arrive underneath.

The first scene of a program arrives with no transition. A 3D program has the same transitions.

`examples/three_parts.py` is three parts on a timer with a different transition into each.

## The scrubber

When every scene has a length, the program is a sequence with a length of its own, and it has a scrubber. Move the pointer over the picture to see it.

- The button pauses and plays.
- The track has a tick where each scene starts. Point at a tick for the scene's name.
- Press or drag on the track to go to that time. The scene there is set up, and `scene_time` is already at that point in it.

`section("name")` adds a tick of your own at the moment it is called:

```python
class Main(Scene):
    length = 20

    def update(self, dt):
        if scene_time > 12:
            section("The chorus")
```

A program that plays a song can move the song when the scrubber moves, with a top-level `on_seek`. A song is moved by its orders, so the program says which order that time is:

```python
def on_seek(seconds):
    song.seek(int(seconds / 8))    # in this song an order lasts 8 seconds
```

A program with a scene that has no length has no scrubber: its length is not known. Pausing the scrubber stops the scenes, not the sound.

## Mistakes

A mistake in a scene says which scene, on its line:

```
In the scene Menu: LookupError: go("nowhere"): there is no scene called "nowhere". The scenes are: Menu, Game
```

Things to know:

- **Every class with `Scene` in brackets plays**, in the order written, including one made from another scene.
- **Name scenes at the top level.** `scene("name", ...)` inside a function that is called later is too late.
- **Inside Circuitry Studio**, transitions and the scrubber need a version of the app that has them. Until then every change of scene is a cut, and everything else on this page works.

## If you know Pymations

> [Pymations](https://github.com/johnwylie70/pymations) has scenes too, and the words here are the same wherever the thing is the same.
>
> **The same**
>
> - `class Intro(Scene):` is a scene. Every `Scene` class in the file plays, in the order written, each starting empty.
> - `setup(self)` is called when the scene begins.
> - `section("name")` is a tick on the scrubber.
> - `transition = "crossfade"` and `transition_time = 0.5` on a scene, and `config(transition="crossfade")` for every scene.
> - `"crossfade"`, `"slide_left"`, `"slide_right"`, `"wipe"` and `"none"` are the same transitions, drawn the same way.
> - The scrubber: play and pause, a tick where each scene starts, the time.
>
> **Different**
>
> - `setup`, `update(dt)` and `draw()` in place of `construct()`. A Pymations scene describes a timeline once. A scene here runs every frame, for as long as it is on show.
> - `go()`, `next_scene()` and `restart()`. A Pymations scene ends when its animations do. Here the program decides, or the scene has a `length`.
> - `length`, `beats` and `bars`. A Pymations scene is as long as what it plays.
> - The last scene is followed by the first. A Pymations timeline stops at its end; `config(loop=False)` does that here.
> - `"cut"`, `"fade"` and the other wipes and slides are added here. `"none"` still works.
> - `section()` takes a name only. A transition here belongs to a change of scene.
> - In a file that begins `from pymations import *`, `Scene`, `section` and `config` are Pymations' own. Scenes of this kind are for a file that does not.

## Related

- [How a program is shaped](program-shape.md)
- [Sound and music](sound.md)
- [Dials and a keyboard](dials.md)
- [Use it on your website](website.md)
