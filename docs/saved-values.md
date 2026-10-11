# Saved values

A program forgets everything when it stops. `save` keeps a value so that it is still there the next time the program runs, and `load` gives it back: a best score, a player's name, the level you reached.

```python
clicks = load("clicks", 0)          # what was saved last time, or 0 the first time

def on_mouse_down(x, y):
    global clicks
    clicks += 1
    save("clicks", clicks)

def draw():
    background("midnightblue")
    text(f"Clicks {clicks}", width / 2, height / 2, "white", 40, "centre")
```

Click a few times, then load the page again. The count carries on from where it was.

## save and load

| Call | What it does |
|---|---|
| `save(name, value)` | Keeps the value under that name. Saving under the same name again replaces what was there. |
| `load(name, otherwise)` | Gives back the value saved under that name. If nothing has been saved under it, gives `otherwise`. |

The name is any text you choose: `"best"`, `"player"`, `"level 3 time"`. Both answer at once, so there is no `await`.

Always give `load` its second value. The first time a program runs nothing has been saved yet, and that value is what you get: `load("best", 0)` is 0, `load("name", "nobody")` is `"nobody"`. Left out, you get `None`.

## What can be saved

Numbers, text, `True` and `False`, lists, and dictionaries with names and values. Lists and dictionaries can hold each other, as deep as you like.

```python
save("player", {"name": "Ada", "level": 3, "keys": ["red", "blue"]})

player = load("player", {"name": "", "level": 1, "keys": []})
print(player["name"], len(player["keys"]))
```

A function, a sprite or an image cannot be saved, and trying to stops the scene with an error that says so. Save the numbers that describe the thing: `save("ship", {"x": ship.x, "y": ship.y})`. A tuple comes back as a list.

What `load` gives you is a copy. Changing it does not change what is saved, so save it again when you want the change kept:

```python
player = load("player", {"name": "", "level": 1, "keys": []})
player["level"] += 1
save("player", player)
```

## When to save

Save when something worth keeping changes: a game ends, a level is finished, a setting is switched. There is no need to save every frame.

A best score is saved at the moment the game ends, and only when it has been beaten:

```python
if score > best:
    best = score
    save("best", best)
```

[`examples/high_score.py`](../examples/high_score.py) is a small game built round those lines, and [`examples/snake.py`](../examples/snake.py) keeps its best score the same way.

To start again from nothing, save the starting value: `save("best", 0)`.

## Where the values are kept

- **In your browser, on the computer, tablet or phone you are using.** They are not sent anywhere, and another device, or another browser on the same one, starts with nothing. This is so even with `run`, where your own Python runs the scene: the page keeps the values, not a file.
- **For this scene alone.** Each scene has its own names, so two scenes can both save `"best"` and neither sees the other's. Nothing else a web page keeps is touched.
- **By the scene's address.** A scene at a new address, such as a copy on another site or under another name, starts with nothing. With `run` the address includes the port, 8765 unless it is taken or you choose another.
- **Until the browser's data for the site is cleared.**
- **In a private window, or where the browser will not keep anything,** `save` and `load` still work, and the values last until the page is closed.

Keep what you save small: scores, names and settings, not pictures. A browser gives a site a few million characters in all.

These are not the functions for files. `save_text`, `save_json` and `open_database` write files and databases that are also there next time, and `load_text` and `load_json` read them ([Files and databases](files-and-databases.md)). Python's own `open()` reads a file that sits beside the scene ([Getting started](getting-started.md)).
