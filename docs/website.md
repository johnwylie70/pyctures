# Use It on Your Website

A Pyctures scene can live on any web page: a blog post, a course page, a portfolio. Python runs in the visitor's browser (with [Pyodide](https://pyodide.org)), so your site needs nothing but files.

There are two ways to put a scene on a page.

## 1. An iframe: the simplest

Build the scene into a folder of its own:

```bash
pyctures build orbit.py -o my-site/orbit
```

Then, in any page of your site:

```html
<iframe src="orbit/index.html" style="width: 100%; aspect-ratio: 16 / 9; border: 0"
        title="An orbit, drawn in Python"></iframe>
```

A single file works the same way: `pyctures build orbit.py -o my-site/orbit.html`, then `<iframe src="orbit.html" …>`.

The scene fills the iframe and follows its size. Nothing on your page can disturb it, and it cannot disturb your page. Each iframe runs its own copy of Python, which is fine for one or two scenes on a page.

## 2. Inline: scenes as part of the page

Put a `<div>` where each scene should go, naming its Python file, and one script tag at the end of the page:

```html
<div data-pyctures-src="balls.py"></div>
<div data-pyctures-src="knot.py" style="height: 420px"></div>

<script type="module" src="pyctures/pyctures.js"></script>
```

The scenes share one copy of Python, so a page with several stays light. It runs in a Web Worker, a background thread, so the page itself only draws and stays smooth. Each scene still has its own names and its own state: they cannot see each other.

To get the `pyctures/` folder beside your page, build the folder your page is in:

```bash
pyctures build my-page/ -o site/
```

That copies everything in `my-page/` (your HTML, your `.py` files, pictures) into `site/` and adds the `pyctures/` folder. Or load the browser half from a CDN instead, once the npm package is published (replace the version with the one you want):

```html
<script type="module" src="https://cdn.jsdelivr.net/npm/pyctures@0.2.0/pyctures.js"></script>
```

### What a scene's box does

- **The canvas fills its box** and follows it when the box changes size, so size the `<div>` with CSS like any other element. A box with no height of its own is given a 16:9 shape.
- **A scene starts when it is scrolled into view**, and pauses while it is out of view or the tab is hidden. A long page with many scenes only runs the ones being looked at.
- **The keyboard** reaches a scene after a visitor clicks or taps it, so the arrow keys still scroll the page until then.
- **Touch** on a scene is the mouse (`mouse.down`, `mouse.x`), and every finger is in `touches`. Scrolling a phone with a finger on a scene moves the scene, not the page, so leave some page around it to scroll by. In 3D, turn off zooming with `controls.enableZoom = False` so the mouse wheel scrolls the page.
- **The mouse wheel** scrolls the page when the pointer is over a scene, unless the scene names the wheel (`mouse.wheel` or `on_wheel`). Such a scene keeps the wheel, so give visitors some page beside it to scroll by. A scene that names `pinch` keeps a trackpad's pinch in the same way.
- **The right mouse button** opens no menu over a scene that uses the pointer: the scene reads it as `mouse.button == "right"`.
- **Printing** goes to the browser's console.
- **Errors** are shown over the scene, with the line in the Python file, and a **Run again** button.

### Settings

Put these on the `<div>`:

| Attribute | What it does |
|---|---|
| `data-pyctures-src="game.py"` | The scene's Python file, relative to the page. Required. |
| `data-pyctures-files="words.txt,maps/level1.json"` | Files the scene opens with `open()`, `load_text` or `load_json`, or imports, fetched before it starts. |
| `data-pyctures-background="#ffffff"` | The colour behind the canvas while the scene loads. |
| `data-pyctures-output="panel"` | Show printed text over the bottom of the scene, not only in the console. |
| `data-pyctures-fullpage` | The scene is the whole page: it has the keyboard from the start. |
| `data-pyctures-measure` | Show the frame rate and where each frame's time goes, in a box over the scene ([The frame rate](finding-mistakes.md#the-frame-rate)). `?measure=1` on the page's address does the same for every scene on it. |
| `data-pyctures-worker="off"` | Run Python on the page's own thread instead of a background one. Only for a browser without Web Workers. |

The div also tells you how its scene is doing: `data-pyctures-status` is `starting`, `running`, `finished` or `error`, and a `pyctures-status` event fires on it when that changes.

### From JavaScript

The module also exports what it uses, for a page that adds scenes itself:

```js
import { mount } from "./pyctures/pyctures.js"

const scene = mount(document.querySelector("#game"), { src: "game.py" })
// later
await scene.destroy()
```

The second argument takes `src`, `files` (a list of paths), `background`, `output` and `fullPage`, as the attributes do, and settings that have no attribute: `storage`, `sound`, `midi`, `microphone` and `save`, below.

Set `window.PYCTURES_NO_AUTO = true` before the script loads to stop it starting every `[data-pyctures-src]` by itself, and `window.PYCTURES_PYODIDE_URL` to load Pyodide from somewhere other than its official CDN (your own copy, for example).

### Files and databases

A scene can write files and keep SQLite databases: `save_text`, `save_json`, `open_database` ([Files and databases](files-and-databases.md)). On a web page they are kept in the visitor's browser, for that scene alone, and you need do nothing:

- a text or JSON file is one entry in `localStorage`, under `pyctures:<the scene's address>:file:<path>`;
- a database is its file's bytes in IndexedDB (a database called `pyctures`, a store called `files`), under the same key;
- where the browser will keep neither, they last until the page is closed.

An app that shows scenes, and has somewhere better to put files (a phone's or a computer's own file system, a server), gives `mount` a `storage`: an object with any of these five functions. Each returns a promise.

```js
mount(el, {
  src: "game.py",
  storage: {
    list: async () => ["notes.txt", "scores.db"],     // every path the scene has stored
    readText: async (path) => "…" /* or null */,
    writeText: async (path, text) => {},
    readBytes: async (path) => new Uint8Array() /* or null */,
    writeBytes: async (path, bytes) => {},            // bytes is a Uint8Array
  },
})
```

- **A host only ever sees files.** A path is as the scene wrote it, with `/` between folders and no `.` or `..` in it: `notes.txt`, `levels/one.json`. A database is the file `scores.db`, written whole.
- **Whatever you leave out, the browser does** as above. Give only `readText` and `writeText`, and databases stay in IndexedDB.
- **Every stored file is read before the scene starts.** Python cannot wait for an answer in the middle of a frame, so the page asks `list()` for the paths, reads each one (`readBytes` first, then `readText` if that gave `null`), and hands them all to Python. So `list()` should give only that scene's files, and they should be small enough to read each time it starts. Without `list()`, the page notes the paths it has written through your functions (in `localStorage`) and reads those.
- **Writes arrive in order,** each as the scene makes it: a text file when it is saved, a database at most once a frame, when a frame changed it. A write that fails is reported once in the console and the scene carries on.
- **With `pyctures run` none of this is used:** the files are real ones beside the scene.

### Sound

A scene that makes sound ([Sound and music](sound.md)) plays it on the page it is on, and you need do nothing: the first time a scene asks for a sound the page loads the sound engine from the `synths/` folder beside `pyctures.js` (`synths.js`, `synths_core.wasm` and `synths-worklet.js`), and the engine runs on the browser's audio thread. A scene with dials loads `dials/dials.js` in the same way. A scene with neither loads neither.

An app that shows scenes can take the sound over with `sound`, an object with any of these:

```js
mount(el, {
  src: "game.py",
  sound: {
    send(batch) { port.postMessage(batch) },   // take the commands and play them somewhere else
    read(id, scope) { return latest(id, scope) },   // with send: what a synth is doing, for scopes and meters
    synths: import("./synths/synths.js"),      // synths.js itself: the module, a promise of it, or its address
    wasm: engineBytes,                         // the engine's bytes, for a page that may not fetch them
    worklet: "blob",                           // how the audio worklet is loaded: "blob", "file" or an address
    latency: 0.06,                             // seconds everything is played ahead
    onState(state) {},                         // "waiting" (for a tap), "on" or "failed"
  },
})
```

- **`send(batch)`** is handed every batch of commands, `{ synths: 1, scope, now, cmds }`, in the format of synths.js ([its docs/commands.md](https://github.com/johnwylie70/synths.js/blob/main/docs/commands.md)). With it nothing is played here and no engine is loaded: play the batches with `createPlayer()` from synths.js wherever sound may be made (`player.send(batch)`), or with an engine of your own.
- **`scope`** names the scene a batch is from (`"scene1"`, `"scene2"`), because each scene chooses its own ids: one player can play them all. A scene out of view sends `{ op: "master", pause: true }` in its scope, and a scene that stops sends `{ op: "close" }`.
- **One clock.** Every time in a batch is on the page's clock, `performance.now() / 1000`, whether the command came from Python (whose own clock may be another computer's) or from a key or a dial on the page. `now` is that clock when the batch was handed over.
- **`read(id, scope)`** gives `{ samples, level: [left, right], notes }` for one synth, or for all the sound when there is no id, as `player.read(id, scope)` does. Without it scopes and meters stay flat.
- **Without `send`** the page plays the sound itself, and `synths`, `wasm` and `worklet` say where its parts come from, so a page that may fetch nothing (a sandboxed frame) still has sound. They are `createPlayer`'s options. `dials`, beside `sound`, is `dials.js` in the same way: the module, a promise of it, or its address.
- **`onMidi(listener, scope)`**, with `send`: the `midi` commands of a scene that uses MIDI are in the batches you are sent, and this is how what your player received comes back. Pass it straight to your player (`onMidi: (listener, scope) => player.onMidi(listener, scope)`); it gives back a function that stops it.
- **`onSoundEvents(listener, scope)`**, with `send`: how what your player says back reaches the scene (the microphone is on or is not, a recording is over, a file is saved). Pass it to your player in the same way (`player.onSoundEvents`). With it a scene's `take.done` and `mic.state` work; without it they never change. `songPosition()`, also with `send`, is where your player's song is, for a scene that draws it.
- **No `eval` is needed**, for sound or for dials. A page's policy has to allow `'wasm-unsafe-eval'` (the engine is WebAssembly) and, for the worklet from a Blob, `blob:` in `script-src`; `worklet: "file"` loads `synths-worklet.js` by its address instead.

### The microphone, and saved sound

A scene that calls `use_microphone()` ([Sound and music](sound.md#your-voice)) has the page ask the browser for the microphone, at that moment and not before, and you need do nothing, as long as the page may ask:

- The page is served over **`https` or from `localhost`**. Anywhere else a browser gives pages no microphone.
- A scene in an **`<iframe>`** from another origin needs `allow="microphone"` on the frame (and `allow="microphone; autoplay"` if sound should not wait for a tap inside it). A sandboxed frame with no origin of its own (`sandbox="allow-scripts"`) is refused whatever it allows: give it the microphone yourself, as below.
- Where there is none, the scene carries on: the console says once why, `mic.state` says which, and a recording is empty.

An app that has the microphone some other way, or that owns the device's audio session, gives it with `microphone`:

```js
mount(el, {
  src: "voice.py",
  microphone: stream,                    // a MediaStream you already have (or a promise of one, or a function that gives one)
  // or: microphone: { open(wants) { … return true }, close() { … } }   // push the frames yourself: wants.push(frames, sampleRate)
  // or: microphone: false                                               // there is none here: never ask
  save(file) { keep(file.name, file.bytes) },   // { name, bytes, type: "audio/wav" } for each file save_sound() makes
})
```

It is the `microphone` option of synths.js, and [its docs/microphone.md](https://github.com/johnwylie70/synths.js/blob/main/docs/microphone.md) is the contract: what `wants` holds, how pushed frames are played, and what the native side of an app needs (on an iPad, `NSMicrophoneUsageDescription` and a play-and-record audio session). Both may be given inside `sound` instead.

**Where a file from `save_sound()` goes.** With `pyctures run` Python writes it beside the scene and the page saves nothing. In a built page, in this order: to `save(file)` if you gave it; else to `storage.writeBytes(path, bytes)` if your `storage` has it, with the scene's other files; else the browser downloads it. A sandboxed frame may not download, which is one more reason to give `save` or `storage`.

With `sound.send` your own player has the microphone and saves the files: the `mic`, `record` and `save` commands are in the batches, and `onSoundEvents` above carries back what it says.

### MIDI

A scene that uses MIDI ([Sound and music](sound.md#midi)) uses the browser's Web MIDI, and you need do nothing: the page fetches `synths/synths-midi.js` the first time a scene uses MIDI, and the browser asks the person's permission then. A page inside a frame of another origin needs `allow="midi"` on the frame.

Safari has no Web MIDI, and so no browser or web view on an iPhone or an iPad has. An app that reaches MIDI some other way (CoreMIDI, behind its web view) gives it to the scene with `midi`, a **MIDI transport**:

```js
mount(el, {
  src: "keys.py",
  midi: {
    open() {},                           // optional, may give a promise: called once, when MIDI is first used. Throw if there is none
    inputs() { return ["Keystation 49"] },    // the names of the devices there now
    outputs() { return ["Minilogue"] },
    send(bytes, time, output) {},        // one whole message; time is milliseconds on performance.now(); output is a name, or undefined for the first
    receive(listener) {},                // keep it, and call listener(bytes, time, input) for what arrives
    changed(listener) {},                // optional: call listener() when a device is plugged in or pulled out
  },
})
```

It is the `midi` option of synths.js, and [its docs/midi.md](https://github.com/johnwylie70/synths.js/blob/main/docs/midi.md) is the contract, with what the native side of an app needs. `midi: false` switches MIDI off. Everything else is done in the page: reading the bytes, the keyboard that plays a synth, the knob that turns a setting, and the timing of what is sent. The scenes of a page share one player, so the first scene to make a sound decides the transport for all of them.

Python is handed what was received with the next frame, so a scene's own `on_midi_note` hears a key up to a frame late (each message carries the time it happened). A keyboard playing a synth and a knob turning a setting do not wait for Python at all.

## Try the example

The `examples/website` folder is a page with two scenes, a 2D one and a 3D one further down:

```bash
pyctures run examples/website          # with your own Python
pyctures build examples/website -o site/   # the static version
```

While `pyctures run` serves a folder, the pages in it run their scenes with your own Python, and saving a `.py` or `.html` file reloads them.

## Things to know

- **The first visit loads Python** (several megabytes, from Pyodide's CDN), which takes a few seconds. After that, the browser keeps it.
- **A loop that never waits** (`while True:` without `await frame()`) stops that scene, and any other scene on the page, until it is stopped: after three seconds the scene says so and offers **Stop**. The page itself keeps working. Use `draw()` and `update()`, or wait in every loop.
- **A built folder must be served** over `http://` or `https://`. Opening its `index.html` straight from disk (`file://`) does not work, because the browser will not load the scene's `.py` file that way. A single-file build (`-o scene.html`) opens from disk.
- **Image paths are relative to the scene's file**, not the page: a scene at `scenes/game.py` that loads `"sprites/ship.png"` reads `scenes/sprites/ship.png`.
