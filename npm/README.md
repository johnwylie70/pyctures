# pyctures (browser)

The browser half of [Pyctures](https://github.com/johnwylie70/pyctures) ([try it in your browser](https://www.circuitry.dev/pyctures)): 2D and 3D graphics and games in Python, on any web page. Pyctures is for any age and any level, a first program or a thousandth, and is designed to bring the joy back into programming: you type a few lines and see something move. Python runs in the visitor's browser with [Pyodide](https://pyodide.org), loaded from its official CDN.

```html
<div data-pyctures-src="scene.py"></div>
<script type="module" src="https://cdn.jsdelivr.net/npm/pyctures@0.3.0/pyctures.js"></script>
```

`scene.py` is an ordinary Pyctures scene:

```python
def draw():
    background("midnightblue")
    circle(width / 2, height / 2, 80, "gold")
```

The canvas fills its `<div>` (16:9 if the div has no height), starts when it scrolls into view, and pauses when it is out of view. See [Use it on your website](https://github.com/johnwylie70/pyctures/blob/main/docs/website.md) for every setting.

A scene can keep things for next time: `save("best", 120)` and `load("best", 0)` for a value, `save_text`, `load_text`, `save_json` and `load_json` for files, and `open_database("scores")` for a SQLite database. They are kept in the visitor's browser. An app that shows scenes can keep them as real files instead, by giving `mount(el, { src, storage })` its own `list`, `readText`, `writeText`, `readBytes` and `writeBytes` ([Files and databases](https://github.com/johnwylie70/pyctures/blob/main/docs/website.md#files-and-databases)).

For scenes written in JavaScript, with the same shape of program and no HTML to write, see the sibling library [pictures.js](https://www.circuitry.dev/pictures).

To write and test scenes on your own computer, install the Python package: `pip install pyctures`, then `pyctures run scene.py`.

Includes three.js (MIT). Author: John Wylie. MIT licence.
