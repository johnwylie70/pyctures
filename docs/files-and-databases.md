# Files and databases

[`save` and `load`](saved-values.md) keep a value under a name. When a program has more to keep, it can write a file, or keep a table of rows in a database. Both are still there the next time the program runs.

```python
notes = load_text("notes.txt", "")      # what the file holds, or "" the first time

def on_key_down(key):
    global notes
    if len(key) == 1:                   # a letter, a number or a space
        notes += key
        save_text("notes.txt", notes)

def draw():
    background("midnightblue")
    text(notes, 20, 40, "white", 22)
```

Click the scene and type a few words, then load the page again. They are still there.

## Text files and JSON files

| Call | What it does |
|---|---|
| `save_text(path, text)` | Writes a text file. If the file is there already, this replaces it. |
| `load_text(path, otherwise)` | Gives back the text in the file. If there is no such file, gives `otherwise`. |
| `save_json(path, value)` | Writes a value as a JSON file: a number, text, `True` or `False`, a list or a dictionary. |
| `load_json(path, otherwise)` | Gives back the value in a JSON file. If there is no such file, gives `otherwise`. |

All four answer at once, so there is no `await`.

Always give `load_text` and `load_json` their second value. The first time a program runs there is no file yet, and that value is what you get. Left out, you get `None`.

A JSON file holds the same kinds of value `save` keeps, so a whole level, or a drawing, fits in one:

```python
level = load_json("level.json", {"walls": [], "start": [40, 40]})

def on_mouse_down(x, y):
    level["walls"].append([x, y])
    save_json("level.json", level)

def draw():
    background("black")
    for x, y in level["walls"]:
        rect(x - 10, y - 10, 20, 20, "orange")
```

Something that cannot be written as JSON, such as a function or a sprite, stops the scene with an error that says so. So does `save_text` when it is given something that is not text: use `str(score)` to make text of a number, or use `save_json`. A JSON file that is there but has a mistake in it stops the scene with an error that says where.

## Paths

A path is from the scene's own folder: `"notes.txt"` is a file beside the scene. It can name a folder, and the folder is made if it is not there:

```python
save_json("levels/one.json", level)
```

A path cannot leave the scene's folder. A `/` at the front is dropped, and so are `.` and `..`, so `"../../notes.txt"` is `"notes.txt"`.

## Databases

A database keeps rows in tables, like a spreadsheet you can ask questions of: the five best scores, every word that starts with "a", how many games were played today. Pyctures uses SQLite, the database inside most phones and browsers, and you talk to it in SQL.

```python
db = open_database("scores")            # the file scores.db, made the first time
db.run("create table if not exists best (name, points)")

db.run("insert into best values (?, ?)", "Ann", 12)
db.run("insert into best values (?, ?)", "Bo", 7)

rows = db.query("select name, points from best where points > ? order by points desc", 10)
for row in rows:
    print(row["name"], row["points"])   # Ann 12
```

| Call | What it does |
|---|---|
| `open_database(name)` | Opens a database, making it if it is new. A name with no ending gets `.db`: `"scores"` is the file `scores.db`. Several can be open at once. |
| `db.query(sql, values...)` | Asks a question. Gives a list of rows, each a dictionary by column name. No rows is an empty list. |
| `db.run(sql, values...)` | Makes a change: `create table`, `insert`, `update`, `delete`. Gives the number of rows it changed. |
| `db.close()` | Finishes with the database. What it holds is kept. |

**Put values in with `?`.** Each `?` in the SQL takes the next value after it, in order. Do not build the SQL out of the values yourself: a name with a `'` in it would break it, and `?` never does.

```python
db.run("insert into best values (?, ?)", name, points)     # yes
db.run(f"insert into best values ('{name}', {points})")    # no
```

The values can also be given as one list: `db.query("select * from best where points > ?", [10])`.

**`create table if not exists`** at the top of the program makes the table the first time and does nothing after that, so the same program works on its first run and every later one.

When SQL has a mistake in it, the scene stops with an error that shows the SQL and what SQLite said about it, such as `no such column: nme`.

You do not have to call `close()`. What a frame changes is kept when the frame ends, however many `run`s it made, and a scene that stops closes its databases.

[`examples/top_scores.py`](../examples/top_scores.py) is a small game that writes every game into a database and shows the best five.

## Where they are kept

That depends on where the scene is running. The program is the same in each.

- **With `pyctures run`, they are real files beside the scene.** `save_text("notes.txt", ...)` writes `notes.txt` in the scene's folder, and `open_database("scores")` makes `scores.db` there. You can open them with anything: a text editor, or a SQLite tool. Python's own `open("notes.txt")` reads the same file.
- **On a web page, or a page you built, they are kept in the browser,** on the computer, tablet or phone being used. They are not sent anywhere, and another device, or another browser on the same one, starts with nothing. As with saved values, they are kept for that scene alone, by its address, until the browser's data for the site is cleared.
- **In an app that shows the scene,** such as [Circuitry Studio](https://www.circuitry.dev), the app can keep them as real files on the device ([Use it on your website](website.md#files-and-databases)).
- **In a private window, or where the browser will not keep anything,** all of this still works, and the files last until the page is closed.

In a browser, everything the scene has stored is handed to Python before the scene starts. That is why `load_text` can answer at once, and why it is best to keep what you store small: a few files, a database of thousands of rows rather than millions. A database is kept whole each time a frame changes it, so change it when something happens (a game ends, a level is saved), not on every frame.

## A file that comes with the scene

A scene can come with a file of its own: a `level.json` you made, or a database already filled in. Put it beside the scene. With `pyctures run` that is all. For a page, add it when you build (`pyctures build game.py --add level.json`), or name it on the scene's `<div>` (`data-pyctures-files="level.json"`).

`load_json("level.json", {})` reads that file until the scene saves one of the same name. After that, in a browser, it reads the saved one, and the file that came with the scene is left as it was.

## Things to know

- **Read what you saved with `load_text` and `load_json`.** In a browser, Python's own `open()` reads the files that came with the scene, not the ones the scene has saved.
- **A browser loads SQLite for a scene whose own file says `open_database`.** If the call is tucked away in a module the scene imports, mention `open_database` in the scene too.
- **With `pyctures run`, saving a `.py`, `.html`, `.css` or `.js` file in the scene's folder runs the scene again.** Give the files a scene writes other endings (`.txt`, `.json`, `.db`).
- **One scene, one set of files.** Two scenes can both keep `scores.db` in a browser and neither sees the other's. With `pyctures run`, scenes in the same folder share the folder, so they share its files.
- **A scene open in two tabs** has two copies of its database, and the one that changes it last is the one that is kept.
