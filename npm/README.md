# pyctures (browser)

The browser half of [Pyctures](https://github.com/johnwylie70/pyctures) ([try it in your browser](https://www.circuitry.dev/pyctures)): Python 2D and 3D graphics on any web page. Python runs in the visitor's browser with [Pyodide](https://pyodide.org), loaded from its official CDN.

```html
<div data-pyctures-src="scene.py"></div>
<script type="module" src="https://cdn.jsdelivr.net/npm/pyctures@0.1.0/pyctures.js"></script>
```

`scene.py` is an ordinary Pyctures scene:

```python
def draw():
    ctx.fill_style = "midnightblue"
    ctx.fill_rect(0, 0, width, height)
    ctx.fill_style = "gold"
    ctx.begin_path()
    ctx.arc(width / 2, height / 2, 60, 0, 6.283)
    ctx.fill()
```

The canvas fills its `<div>` (16:9 if the div has no height), starts when it scrolls into view, and pauses when it is out of view. See [Use it on your website](https://github.com/johnwylie70/pyctures/blob/main/docs/website.md) for every setting.

To write and test scenes on your own computer, install the Python package: `pip install pyctures`, then `pyctures run scene.py`.

Includes three.js (MIT). Author: John Wylie. MIT licence.
