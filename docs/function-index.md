# Function index

Every name a Pyctures program can use, by area, one line each. The link on each row goes to the page that explains it, with examples.

| Area | pictures.js | Pyctures |
|---|---|---|
| 2D drawing: the plain functions | yes | yes |
| 2D drawing: the canvas, `ctx` | yes | yes |
| 3D: three.js | yes | yes |
| Sprites and hit-testing | yes | yes |
| Keyboard, mouse and touch | yes | yes |
| Frames and timing | yes | yes |
| Scenes | yes | yes |
| Saved values | yes | yes |
| Files | yes | yes |
| Databases (SQLite) | yes | yes |
| Sound and music | with synths.js | yes, `from synths import *` |
| Dials and a keyboard | with dials.js | yes, `from pydials import *` |
| Image processing | Circuitry only | Circuitry only |

This page is Pyctures's own index, in its own spellings. pictures.js has the same areas in JavaScript: [the pictures.js function index](https://www.circuitry.dev/docs/pictures/functions).

Everything on this page works wherever Pyctures runs. Nothing here needs an app.

## The shape of a program

Functions you write. They are called if the program defines them.

Explained in [How a program is shaped](program-shape.md#2-draw-every-frame-draw-and-updatedt).

| Name | What it does |
|---|---|
| `setup()` | Called once, before the first frame |
| `update(dt)` | Called every frame, with the seconds since the last one: move things here |
| `draw()` | Called every frame, after `update`: draw the picture here |

## Scenes

A program in several scenes, each with the functions above as its own.

Explained in [Scenes](scenes.md).

| Name | What it does |
|---|---|
| `class Title(Scene):` | A scene: `setup`, `update`, `draw` and the `on_` functions as its methods, its variables on `self`. Every `Scene` class plays, in the order written |
| `scene(name, draw=..., update=...)` | A scene from plain functions, with no class |
| `go(scene)` | Change to a scene, by its name or its class. `go("Game", transition="wipe", transition_time=0.5)` says how; `keep=True` goes back to a scene as it was left |
| `next_scene()` | Change to the next scene written; after the last comes the first |
| `restart()` | Begin this scene again, from empty |
| `length`, `beats`, `bars` | On a scene: it ends by itself after so many seconds, beats or bars |
| `transition`, `transition_time`, `transition_color` | On a scene: how it arrives. `"cut"`, `"crossfade"`, `"fade"`, `"wipe"`, `"wipe_left"`, `"wipe_up"`, `"wipe_down"`, `"slide_left"`, `"slide_right"`, `"slide_up"`, `"slide_down"` |
| `resume(self)`, `on_stop(self)` | A scene's own: `resume` is called in place of `setup` when it is come back to with `keep=True`, and `on_stop` when it ends |
| `scene_time` | Seconds since this scene began |
| `scene_progress` | How far through its length the scene is, from 0 to 1 |
| `scene_name` | The name of the scene on show |
| `section(name)` | A tick on the scrubber at this moment |
| `config(loop=..., transition=...)` | Settings for every scene: `loop`, `transition`, `transition_time`, `transition_color`, `beats_per_bar` |
| `on_seek(seconds)` | A function you write at the top level: called when the scrubber is moved |

## 2D drawing: the plain functions

One call each, with no `ctx.` in front.

Explained in [2D functions](2d-functions.md#plain-drawing).

| Name | What it does |
|---|---|
| `background(colour)` | Paints the whole canvas |
| `circle(x, y, radius, colour)` | A filled circle centred on `x, y` |
| `ellipse(x, y, width, height, colour)` | An oval centred on `x, y` |
| `rect(x, y, width, height, colour)` | A filled rectangle, top-left corner at `x, y` |
| `triangle(x1, y1, x2, y2, x3, y3, colour)` | A triangle, by its three corners |
| `polygon(x, y, radius, sides, colour)` | A shape with that many equal sides, centred on `x, y`, one corner straight up |
| `star(x, y, radius, points, colour)` | A star with that many points, one straight up |
| `line(x1, y1, x2, y2, colour, thickness)` | A straight line |
| `text(words, x, y, colour, size, align)` | Words, `size` points high |
| `picture(what, x, y, size)` | An emoji or a word, an image file beside the program, or a loaded image, centred on `x, y` and … |

### Chance and angles

Explained in [2D functions](2d-functions.md#plain-drawing).

| Name | What it does |
|---|---|
| `random(min, max)` | A whole number from `min` to `max`, either end included |
| `random(max)`, `random()` | From 0 to `max`; with nothing, a fraction from 0 up to 1 |
| `pick(list)` | One thing from a list, by chance |
| `degrees(n)` | An angle said in degrees, wherever an angle is wanted: `ctx.rotate(degrees(45))`, `ship.angle = …` |

## 2D drawing: the canvas, `ctx`

The web's own 2D drawing surface: everything the plain functions do, and much more.

### Size and pictures

Explained in [2D functions](2d-functions.md#size-and-helpers).

| Name | What it does |
|---|---|
| `width`, `height` | The size of the canvas, in points |
| `pixel_ratio` | Real pixels per point (2 or 3 on most phones) |
| `canvas` | The canvas, for `canvas.add_event_listener(...)` |
| `load_image(address)` | Loads a picture to draw |
| `js` | Everything else the page has, such as `js.Path2D` and `js.document` |

### Rectangles

Explained in [2D functions](2d-functions.md#rectangles).

| Name | What it does |
|---|---|
| `ctx.fill_rect(x, y, w, h)` | A filled rectangle, top-left corner at `x, y` |
| `ctx.stroke_rect(x, y, w, h)` | The outline of a rectangle |
| `ctx.clear_rect(x, y, w, h)` | Rubs that area out, back to see-through |

### Paths

Explained in [2D functions](2d-functions.md#paths).

| Name | What it does |
|---|---|
| `ctx.begin_path()` | Starts a new, empty path |
| `ctx.move_to(x, y)` | Lifts the pen and puts it down at `x, y` |
| `ctx.line_to(x, y)` | A straight line to `x, y` |
| `ctx.close_path()` | A straight line back to where this piece started |
| `ctx.rect(x, y, w, h)` | A rectangle, as part of the path |
| `ctx.round_rect(x, y, w, h, r)` | A rounded rectangle |
| `ctx.arc(x, y, r, start, end)` | Part of a circle round `x, y`, from angle `start` to `end` in radians (`0` to `math.tau` is all … |
| `ctx.arc_to(x1, y1, x2, y2, r)` | A rounded corner of radius `r`, turning at `x1, y1` towards `x2, y2` |
| `ctx.ellipse(x, y, rx, ry, turn, start, end)` | Part of an oval, `rx` wide and `ry` tall, turned by `turn` radians |
| `ctx.quadratic_curve_to(cx, cy, x, y)` | A curve to `x, y`, pulled towards one control point |
| `ctx.bezier_curve_to(c1x, c1y, c2x, c2y, x, y)` | A curve to `x, y` with two control points |
| `ctx.fill()` | Fills the path |
| `ctx.stroke()` | Draws the path's outline |

### Colours and styles

Explained in [2D functions](2d-functions.md#colours-and-styles).

| Name | What it does |
|---|---|
| `ctx.fill_style = …` | The colour, gradient or pattern for fills and filled text |
| `ctx.stroke_style = …` | The same, for outlines |
| `ctx.global_alpha = 0.5` | How solid everything drawn next is, from 0 (invisible) to 1 |
| `ctx.create_linear_gradient(x0, y0, x1, y1)` | A gradient along a line |
| `ctx.create_radial_gradient(x0, y0, r0, x1, y1, r1)` | A gradient between two circles |
| `ctx.create_conic_gradient(angle, x, y)` | A gradient round a point, like a colour wheel |
| `gradient.add_color_stop(position, colour)` | A colour at a point (0 to 1) along a gradient |
| `ctx.create_pattern(picture, "repeat")` | A repeating fill from a picture or another canvas |

### Lines

Explained in [2D functions](2d-functions.md#lines).

| Name | What it does |
|---|---|
| `ctx.line_width = 4` | How thick outlines are, in points |
| `ctx.line_cap = "round"` | How line ends look: `"butt"` (flat, stops at the end), `"round"`, `"square"` (flat, sticks out … |
| `ctx.line_join = "round"` | How corners look: `"miter"` (sharp), `"round"`, `"bevel"` (cut off) |
| `ctx.miter_limit = 10` | How far a sharp corner may stick out before it is cut off like a bevel |
| `ctx.set_line_dash([10, 5])` | Dashes: 10 drawn, 5 gap |
| `await ctx.get_line_dash()` | **(await)** The current dash list |
| `ctx.line_dash_offset = 4` | Slides the dashes along |

### Text

Explained in [2D functions](2d-functions.md#text).

| Name | What it does |
|---|---|
| `ctx.fill_text(text, x, y)` | Draws text |
| `ctx.stroke_text(text, x, y)` | Draws the outline of the text |
| `await ctx.measure_text(text).width` | **(await)** How wide the text will be, in points |
| `ctx.font = "bold 24px serif"` | Style, size and family |
| `ctx.text_align = "center"` | Where `x` is: `"left"`, `"center"`, `"right"`, or `"start"`/`"end"` (which follow the writing … |
| `ctx.text_baseline = "middle"` | Where `y` is: `"alphabetic"` (the line letters sit on, the default), `"top"`, `"hanging"` … |
| `ctx.direction = "rtl"` | Writing direction: `"ltr"`, `"rtl"` or `"inherit"` |
| `ctx.letter_spacing = "4px"` | Extra space between letters (older devices ignore it) |
| `ctx.word_spacing = "10px"` | Extra space between words (older devices ignore it) |
| `ctx.font_kerning = "none"` | Whether letter pairs are fitted closer: `"auto"`, `"normal"`, `"none"` |

### Images

Explained in [2D functions](2d-functions.md#images).

| Name | What it does |
|---|---|
| `img = load_image(address)` | Starts loading a picture from a path beside the scene (`"cat.png"`), a web address or a `data:` … |
| `ctx.draw_image(img, x, y)` | Draws it at its own size, top-left at `x, y` |
| `ctx.draw_image(img, x, y, w, h)` | Draws it stretched to `w` by `h` |
| `ctx.draw_image(img, sx, sy, sw, sh, x, y, w, h)` | Cuts the part `sx, sy, sw, sh` out of the picture and draws it at `x, y, w, h` |
| `ctx.image_smoothing_enabled = False` | Keeps pixel art crisp and blocky when scaled up |
| `ctx.image_smoothing_quality = "high"` | How carefully pictures are smoothed: `"low"`, `"medium"`, `"high"` |

### Transforms

Explained in [2D functions](2d-functions.md#transforms).

| Name | What it does |
|---|---|
| `ctx.translate(x, y)` | Moves the grid's corner `(0, 0)` to `x, y` |
| `ctx.rotate(angle)` | Turns the grid round `(0, 0)` by `angle` radians, clockwise |
| `ctx.scale(sx, sy)` | Stretches the grid |
| `ctx.transform(a, b, c, d, e, f)` | Applies any stretch, slant and move at once |
| `ctx.save()` | Remembers the transform and every setting on this page |
| `ctx.restore()` | Goes back to what the last `save()` remembered |
| `ctx.set_transform(a, b, c, d, e, f)` | Replaces the transform completely |
| `ctx.reset_transform()` | Clears the transform |
| `await ctx.get_transform()` | **(await)** The current transform, as numbers `a` to `f` |

### Shadows

Explained in [2D functions](2d-functions.md#shadows).

| Name | What it does |
|---|---|
| `ctx.shadow_color = "rgba(0, 0, 0, 0.5)"` | The shadow's colour |
| `ctx.shadow_blur = 10` | How soft the shadow is |
| `ctx.shadow_offset_x = 5` | How far right the shadow falls |
| `ctx.shadow_offset_y = 5` | How far down the shadow falls |

### Blending and filters

Explained in [2D functions](2d-functions.md#blending-and-filters).

| Name | What it does |
|---|---|
| `ctx.global_composite_operation = "multiply"` | How new drawing mixes with what is already there |
| `ctx.filter = "blur(4px)"` | An effect on everything drawn next |

### Clipping and hit testing

Explained in [2D functions](2d-functions.md#clipping-and-hit-testing).

| Name | What it does |
|---|---|
| `ctx.clip()` | Makes the current path a window: everything drawn next shows only inside it |
| `await ctx.is_point_in_path(x, y)` | **(await)** Whether a point is inside the current path |
| `await ctx.is_point_in_stroke(x, y)` | **(await)** Whether a point is on the path's outline |

### Paths you can keep: Path2D

Explained in [2D functions](2d-functions.md#paths-you-can-keep-path2d).

| Name | What it does |
|---|---|
| `ctx.fill(path)` | Fills that path |
| `ctx.stroke(path)` | Outlines it |
| `ctx.clip(path)` | Clips to it |
| `await ctx.is_point_in_path(path, x, y)` | **(await)** Whether a point is inside it |
| `path.add_path(other)` | Adds another path's pieces to this one |

### Pixels

Explained in [2D functions](2d-functions.md#pixels).

| Name | What it does |
|---|---|
| `await ctx.get_image_data(x, y, w, h).data` | **(await)** The colours of every pixel in that area, as one long list: red, green, blue, alpha … |
| `ctx.create_image_data(w, h)` | A blank block of pixels |
| `ctx.put_image_data(pixels, x, y)` | Puts a block of pixels straight onto the canvas, ignoring transforms, alpha and blend modes |
| `js.ImageData(js.Uint8ClampedArray(numbers), w, h)` | Makes a block of pixels from a Python list of numbers |

### Saving and resetting

Explained in [2D functions](2d-functions.md#saving-and-resetting).

| Name | What it does |
|---|---|
| `ctx.save()` | Remembers every setting on this page, the transform and the clip |
| `ctx.restore()` | Goes back to the last `save()` |
| `ctx.reset()` | Clears the canvas and puts every setting back to the start, including the canvas's sharp-screen … |

## 3D: three.js

three.js is there as `THREE`, and its orbit controls as `addons.OrbitControls`.

### Renderer

Explained in [3D functions](3d-functions.md#renderer).

| Name | What it does |
|---|---|
| `renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)` | Makes a renderer that draws on the canvas, with smooth edges |
| `renderer.setPixelRatio(pixel_ratio)` | Sharp on high-resolution screens |
| `renderer.setSize(width, height, False)` | Fits the canvas |
| `renderer.render(scene, camera)` | Draws one picture; call it in `draw()` |
| `renderer.setClearColor("navy", 1)` | The colour behind the scene when it has no background; the second number is how solid |
| `renderer.shadowMap.enabled = True` | Turns shadows on |
| `renderer.shadowMap.type = THREE.PCFSoftShadowMap` | Soft-edged shadows |
| `renderer.toneMapping = THREE.ACESFilmicToneMapping` | Softens very bright light the way a film camera does |
| `renderer.toneMappingExposure = 1.2` | Overall brightness when tone mapping is on |
| `renderer.outputColorSpace = THREE.SRGBColorSpace` | How colours are sent to the screen |

### Scene and fog

Explained in [3D functions](3d-functions.md#scene-and-fog).

| Name | What it does |
|---|---|
| `scene = THREE.Scene()` | The world everything goes in |
| `scene.add(thing)`, `scene.remove(thing)` | Puts something in the world, or takes it out |
| `scene.background = THREE.Color("skyblue")` | The colour behind everything |
| `scene.fog = THREE.Fog("white", near, far)` | Fog that starts at distance `near` and hides everything by `far` |
| `scene.fog = THREE.FogExp2("white", 0.05)` | Fog that thickens steadily with distance; the number is how thick |

### Cameras

Explained in [3D functions](3d-functions.md#cameras).

| Name | What it does |
|---|---|
| `THREE.PerspectiveCamera(fov, width / height, near, far)` | A camera that sees the way eyes do: far things look smaller |
| `THREE.OrthographicCamera(left, right, top, bottom, near, far)` | A camera with no perspective: far things look the same size |
| `camera.position.set(x, y, z)` | Where the camera is |
| `camera.lookAt(x, y, z)` | Points it at a spot |
| `camera.fov = 30`, `camera.near`, `camera.far`, `camera.zoom = 2` | Change its settings; follow with `camera.updateProjectionMatrix()` |
| `camera.updateProjectionMatrix()` | Applies changed camera settings |

### Geometries: shapes

Explained in [3D functions](3d-functions.md#geometries-shapes).

| Name | What it does |
|---|---|
| `THREE.BoxGeometry(w, h, d)` | A box |
| `THREE.SphereGeometry(radius, 32, 16)` | A ball |
| `THREE.PlaneGeometry(w, h)` | A flat rectangle, facing you |
| `THREE.CircleGeometry(radius, 32)` | A flat disc |
| `THREE.RingGeometry(inner, outer, 32)` | A flat ring, like a washer |
| `THREE.CylinderGeometry(top_radius, bottom_radius, height, 32)` | A cylinder; different radii make a tapered tube |
| `THREE.ConeGeometry(radius, height, 32)` | A cone |
| `THREE.CapsuleGeometry(radius, length, 8, 16)` | A pill |
| `THREE.TorusGeometry(radius, tube, 16, 64)` | A ring doughnut |
| `THREE.TorusKnotGeometry(radius, tube, 128, 16)` | A knotted tube |
| `THREE.TetrahedronGeometry(radius)` | 4 faces |
| `THREE.OctahedronGeometry(radius)` | 8 faces |
| `THREE.DodecahedronGeometry(radius)` | 12 faces |
| `THREE.IcosahedronGeometry(radius, detail)` | 20 faces; raise `detail` to make it rounder |
| `THREE.LatheGeometry(points, 32)` | Spins a side outline (a list of `THREE.Vector2`) round the up axis, like a vase on a potter's … |
| `THREE.ExtrudeGeometry(shape, depth=0.5, bevelEnabled=False)` | Pushes a flat `THREE.Shape` out into a solid, like a cookie cutter |
| `THREE.TubeGeometry(curve, 64, radius, 8, False)` | A tube along a curve, such as `THREE.CatmullRomCurve3([...points])` |
| `THREE.EdgesGeometry(geometry)` | Just the edges of another shape, for `LineSegments` |
| `THREE.WireframeGeometry(geometry)` | Every triangle's edges, for `LineSegments` |
| `THREE.BufferGeometry()` | Your own shape from numbers: `geometry.setAttribute("position" …` |

### Materials: how surfaces look

Explained in [3D functions](3d-functions.md#materials-how-surfaces-look).

| Name | What it does |
|---|---|
| `THREE.MeshBasicMaterial(color=…)` | Flat colour, ignores light, always visible |
| `THREE.MeshLambertMaterial(color=…)` | Matte, like chalk or paper |
| `THREE.MeshPhongMaterial(color=…, shininess=80, specular="white")` | Shiny highlights, like plastic |
| `THREE.MeshStandardMaterial(color=…, roughness=0.5, metalness=0)` | Realistic |
| `THREE.MeshPhysicalMaterial(color=…, clearcoat=1, transmission=0.9, thickness=0.5)` | Standard, plus extras: `clearcoat` (a varnish layer), `transmission` (glass that lets light … |
| `THREE.MeshToonMaterial(color=…)` | Cartoon shading in a few flat bands |
| `THREE.MeshNormalMaterial()` | Rainbow colours by which way each face points; needs no light |
| `THREE.MeshDepthMaterial()` | White near the camera, fading to black far away |
| `THREE.LineBasicMaterial(color=…)` | For lines (`Line`, `LineSegments`, `LineLoop`) |
| `THREE.LineDashedMaterial(color=…, dashSize=0.2, gapSize=0.1)` | Dashed lines; call `line.computeLineDistances()` once |
| `THREE.PointsMaterial(color=…, size=0.05)` | For `Points` |
| `THREE.SpriteMaterial(map=texture)` | For `Sprite`, a picture that always faces the camera |
| `color="tomato"` | The surface colour |
| `emissive="orange"`, `emissiveIntensity=1` | A glow the surface gives off by itself |
| `map=texture` | A picture wrapped round the surface |
| `roughness`, `metalness` | Standard and Physical only: rough or polished, metal or not |
| `wireframe=True` | Draws the edges of every triangle only |
| `flatShading=True` | Shows the flat faces rather than smoothing over them |
| `side=THREE.DoubleSide` | Shows both sides of flat shapes (`FrontSide` is the default, `BackSide` the inside) |
| `transparent=True, opacity=0.5` | See-through; `opacity` does nothing without `transparent` |

### Lights

Explained in [3D functions](3d-functions.md#lights).

| Name | What it does |
|---|---|
| `THREE.AmbientLight(colour, intensity)` | A little light everywhere, from no direction |
| `THREE.HemisphereLight(sky, ground, intensity)` | Sky colour from above, ground colour from below |
| `THREE.DirectionalLight(colour, intensity)` | The sun: parallel light from `position` towards `target` (the middle unless you move it) |
| `THREE.PointLight(colour, intensity, distance, decay)` | A bulb: light in every direction from one spot |
| `THREE.SpotLight(colour, intensity, distance, angle, penumbra, decay)` | A torch: a cone of light from `position` towards `target` |
| `THREE.RectAreaLight(colour, intensity, w, h)` | A glowing panel, like a window or a softbox |
| `light.intensity = 2` | Brightness |
| `light.color.set("orange")` | Colour |
| `light.position.set(x, y, z)` | Where it is |
| `light.target.position.set(x, y, z)` | Where directional and spot lights point; also `scene.add(light.target)` |
| `light.visible = False` | Switches it off |
| `light.castShadow = True` | Directional, point and spot lights can cast shadows (turn on `renderer.shadowMap.enabled` and … |
| `light.shadow.mapSize.width = 2048` (and `.height`) | Sharper shadows, at a cost in speed |
| `light.shadow.bias = -0.0005` | Removes stripy marks on surfaces that shadow themselves |
| `light.shadow.radius = 4` | Blurs shadow edges (with `PCFSoftShadowMap` off, `PCFShadowMap` on) |
| `light.shadow.camera.left` / `right` / `top` / `bottom` | How big an area a directional light's shadows cover |

### Objects

Explained in [3D functions](3d-functions.md#objects).

| Name | What it does |
|---|---|
| `THREE.Mesh(geometry, material)` | A solid object |
| `THREE.Group()` | An empty holder: things added to it move, turn and scale with it |
| `THREE.Points(geometry, THREE.PointsMaterial(size=0.05))` | A dot at every position in the geometry |
| `THREE.Line(geometry, material)` | A line through the positions, in order |
| `THREE.LineLoop(geometry, material)` | The same, joined back to the start |
| `THREE.LineSegments(geometry, material)` | Separate lines, one for each pair of positions |
| `THREE.Sprite(THREE.SpriteMaterial(map=texture))` | A flat picture that always faces the camera, for labels and particles |
| `THREE.InstancedMesh(geometry, material, count)` | Many copies of one mesh drawn at once, much faster than many meshes |

### Moving and arranging

Explained in [3D functions](3d-functions.md#moving-and-arranging).

| Name | What it does |
|---|---|
| `thing.position.set(x, y, z)`, `thing.position.x = 2` | Where it is |
| `thing.rotation.set(x, y, z)`, `thing.rotation.y += 0.01` | How it is turned round each axis, in radians |
| `thing.scale.set(2, 1, 1)`, `thing.scale.setScalar(2)` | How big it is along each axis |
| `thing.lookAt(x, y, z)` | Turns it to face a spot |
| `thing.add(other)`, `thing.remove(other)` | Puts `other` inside `thing`, so it moves with it |
| `thing.visible = False` | Hides it |
| `thing.name = "door"` | A name, handy when picking |
| `thing.castShadow`, `thing.receiveShadow` | Whether it makes shadows and shows them |

### Textures

Explained in [3D functions](3d-functions.md#textures).

| Name | What it does |
|---|---|
| `THREE.TextureLoader().load(address)` | Loads a picture: a path from the scene (`"textures/brick.png"`, included by `pyctures build`) … |
| `THREE.CanvasTexture(a_canvas)` | Uses a 2D canvas you drew on as the picture: text, patterns, anything from 2D functions |
| `texture.needsUpdate = True` | After you draw on that canvas again, shows the change |
| `texture.wrapS = texture.wrapT = THREE.RepeatWrapping` | Lets the picture repeat across and down (write it as two lines in Python) |
| `texture.repeat.set(4, 4)` | How many times it repeats |
| `texture.colorSpace = THREE.SRGBColorSpace` | Shows a photo's colours correctly |
| `texture.magFilter = THREE.NearestFilter` | Keeps pixel-art textures blocky |

### Helpers

Explained in [3D functions](3d-functions.md#helpers).

| Name | What it does |
|---|---|
| `THREE.GridHelper(size, divisions)` | A grid on the floor |
| `THREE.AxesHelper(length)` | The three axes: x red, y green, z blue |
| `THREE.DirectionalLightHelper(light, size)` | Where a directional light is and which way it points |
| `THREE.PointLightHelper(light, size)` | Where a point light is |
| `THREE.SpotLightHelper(light)` | A spot light's cone |
| `THREE.HemisphereLightHelper(light, size)` | A hemisphere light |
| `THREE.CameraHelper(light.shadow.camera)` | The box a light's shadows cover |
| `THREE.BoxHelper(thing, "yellow")` | A box round an object |

### Maths

Explained in [3D functions](3d-functions.md#maths).

| Name | What it does |
|---|---|
| `THREE.Vector3(x, y, z)` | A position or direction in 3D |
| `THREE.Vector2(x, y)` | The same in 2D |
| `THREE.Color(…)` | A colour |
| `THREE.Euler(x, y, z)` | A turn round each axis, in radians: what `rotation` is |
| `THREE.Quaternion()` | Another way to store a turn, which never gets stuck |
| `THREE.Matrix4()` | Position, turn and size in one; used by `InstancedMesh` |
| `THREE.MathUtils.degToRad(90)` | Degrees to radians; in Python, `math.radians(90)` does the same and needs no answer back |

### Picking and controls

Explained in [3D functions](3d-functions.md#picking-and-controls).

| Name | What it does |
|---|---|
| `ray = THREE.Raycaster()` | Makes a picker |
| `ray.setFromCamera(THREE.Vector2(x, y), camera)` | Aims it through a point, where `x` and `y` run from -1 to 1 across and up the canvas: `x = …` |
| `hits = ray.intersectObjects(list_of_things)` | What it hits, nearest first |
| `controls = addons.OrbitControls(camera, canvas)` | Drag to orbit, pinch or scroll to zoom, two fingers or right-drag to pan |
| `controls.update()` | Call every frame in `draw()` |
| `controls.target.set(x, y, z)` | The point it orbits round |
| `controls.enableDamping = True` | Glides to a stop when you let go |
| `controls.autoRotate = True`, `controls.autoRotateSpeed = 2` | Turns slowly by itself |
| `controls.minDistance = 2`, `controls.maxDistance = 20` | How close and how far you can zoom |
| `controls.maxPolarAngle = math.pi / 2` | Stops the camera going below the floor |
| `controls.enableZoom`, `controls.enablePan`, `controls.enableRotate` | Switch each gesture on or off |

## Sprites and hit-testing

Moving pictures that can tell when they touch.

| Name | What it does | More |
|---|---|---|
| `Sprite(picture, x, y, size=48)` | A moving picture with `x`, `y`, `vx`, `vy`, `angle`, `spin`, `size`, `visible`, `update(dt)` … | [2D functions](2d-functions.md#size-and-helpers) |
| `remove(things, thing)` | Take a thing out of a list | [2D functions](2d-functions.md#size-and-helpers) |
| `sprite.picture` | An emoji or text, an image from `load_image`, or a function that draws it | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.x`, `sprite.y` | Where its centre is | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.vx`, `sprite.vy` | Its speed in points per second, used by `update(dt)` | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.angle` | How far it is turned | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.spin` | How fast it turns each second, used by `update(dt)`: `degrees(180)` is half a turn a second | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.size` | How big it is, in points (48 unless you say) | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.visible` | `False` hides it | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.update(dt)` | Moves it by its speed and turns it by its spin | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.draw()` | Draws it (call this in your `draw()`) | [Drawing in 2D](drawing-2d.md#sprites) |
| `sprite.touches(other)` | `True` when the two overlap | [Drawing in 2D](drawing-2d.md#sprites-that-touch) |
| `sprite.hit(sprites)` | The first sprite in the list that it touches, or `None` when it touches none | [Drawing in 2D](drawing-2d.md#sprites-that-touch) |
| `sprite.contains(x, y)` | `True` when that point is on it | [Drawing in 2D](drawing-2d.md#sprites-that-touch) |
| `sprite.shape` | `"circle"` (as it starts) or `"box"` | [Drawing in 2D](drawing-2d.md#sprites-that-touch) |
| `sprite.radius` | The size of its circle | [Drawing in 2D](drawing-2d.md#sprites-that-touch) |
| `sprite.width`, `sprite.height` | The size of its box | [Drawing in 2D](drawing-2d.md#sprites-that-touch) |
| `sprite.wrap()` | When it has gone off one edge, it comes back on the opposite one | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `sprite.bounce()` | Bounces it off the edges | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `sprite.offscreen()` | `True` when all of it is outside the picture | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `sprite.push(amount)` | Speeds it up the way it faces: this is an engine | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `sprite.forward(distance)` | Steps it the way it faces, without changing its speed | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `sprite.limit(speed)` | Slows it to that speed if it is going faster | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `sprite.angle_to(other)` | The angle from it to another sprite, to `mouse`, or to a point: `angle_to(x, y)` | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `sprite.distance_to(other)` | How far it is to another sprite, to `mouse`, or to a point: `distance_to(x, y)` | [Drawing in 2D](drawing-2d.md#leaving-the-picture-and-moving-the-way-it-faces) |
| `Sprite.box(x, y, width, height, colour)` | A coloured box, tested as a box | [Drawing in 2D](drawing-2d.md#pictures-you-draw-yourself) |
| `Sprite.circle(x, y, size, colour)` | A coloured circle `size` across, tested as that circle | [Drawing in 2D](drawing-2d.md#pictures-you-draw-yourself) |

## Keyboard, mouse and touch

What is held now, what went down since the last frame, and functions called when something happens.

Explained in [2D functions](2d-functions.md#size-and-helpers).

| Name | What it does |
|---|---|
| `keys` | The set of keys held down: `"ArrowLeft" in keys` |
| `pressed`, `released` | The keys that went down, and came up, since the last frame: `" " in pressed` |
| `mouse.x`, `mouse.y`, `mouse.down` | Where the pointer or finger is, and whether it is pressed |
| `mouse.button`, `mouse.inside` | Which button is down (`"left"`, `"middle"`, `"right"` or `None`), and whether the pointer is … |
| `mouse.dx`, `mouse.dy`, `mouse.wheel` | How far the pointer moved, and the wheel turned, since the last frame |
| `touches` | Every finger (or pressed mouse button) that is down: each has `id`, `x`, `y`, `start_x` … |
| `pinch.scale`, `pinch.change`, `pinch.x`, `pinch.y` | Two fingers as a zoom: the scale since the pinch began, its change since the last frame, and … |

### Functions you write

Explained in [How a program is shaped](program-shape.md#when-something-happens-the-on_-functions).

| Name | What it does |
|---|---|
| `on_key_down(key, code)` | A key is pressed |
| `on_key_up(key, code)` | A key is let go |
| `on_key_repeat(key, code)` | A key that is held down repeats, as it does when you type |
| `on_mouse_down(x, y, button)` | The mouse button or a finger goes down |
| `on_mouse_move(x, y)` | The pointer moves |
| `on_mouse_up(x, y, button)` | The button or finger comes up |
| `on_touch_start(touch)` | A finger or a mouse button goes down |
| `on_touch_move(touch)` | A finger that is down moves |
| `on_touch_end(touch, cancelled)` | A finger comes up |
| `on_wheel(amount)` | The wheel turns |
| `on_pinch(scale, change)` | Two fingers move together or apart |

## Frames and timing

Used with `await`, in a loop of your own.

| Name | What it does | More |
|---|---|---|
| `await frame()` | Shows this frame and waits for the next | [2D functions](2d-functions.md#size-and-helpers) |
| `await flush()` | Shows what is drawn so far, now, and carries on | [2D functions](2d-functions.md#size-and-helpers) |
| `await sleep(seconds)` | Waits that long | [2D functions](2d-functions.md#size-and-helpers) |
| `await vsync()` | Another name for `frame()`: waits for the screen's next refresh | [How a program is shaped](program-shape.md#3-a-loop-with-await-frame) |

## Saved values

One value under a name, still there the next time.

Explained in [Saved values](saved-values.md#save-and-load).

| Name | What it does | In pictures.js |
|---|---|---|
| `save(name, value)` | Keeps the value under that name | `save` |
| `load(name, otherwise)` | Gives back the value saved under that name | `load` |

## Files

A text or JSON file the program writes and reads back. Kept in the browser on a web page, and as real files beside the scene with `pyctures run`: [where they are kept](files-and-databases.md#where-they-are-kept).

Explained in [Files and databases](files-and-databases.md#text-files-and-json-files).

| Name | What it does | In pictures.js |
|---|---|---|
| `save_text(path, text)` | Writes a text file | `saveText` |
| `load_text(path, otherwise)` | Gives back the text in the file | `loadText` |
| `save_json(path, value)` | Writes a value as a JSON file: a number, text, `True` or `False`, a list or a dictionary | `saveJSON` |
| `load_json(path, otherwise)` | Gives back the value in a JSON file | `loadJSON` |

## Databases

Rows in a SQLite database, asked for in SQL. Kept in the browser on a web page, and as real files beside the scene with `pyctures run`: [where they are kept](files-and-databases.md#where-they-are-kept).

Explained in [Files and databases](files-and-databases.md#databases).

| Name | What it does | In pictures.js |
|---|---|---|
| `open_database(name)` | Opens a database, making it if it is new | `openDatabase` |
| `db.query(sql, values...)` | Asks a question | `db.query` |
| `db.run(sql, values...)` | Makes a change: `create table`, `insert`, `update`, `delete` | `db.run` |
| `db.close()` | Finishes with the database | `db.close` |

## Sound and music

These come with `from synths import *` at the top of the scene. Explained in [Sound and music](sound.md).

| Name | What it does |
|---|---|
| `play_sound(name)` | A ready-made game sound: `coin`, `jump`, `laser`, `shoot`, `explosion`, `hit`, `powerup`, `blip`, `click`, `zap`, `bounce`, `pop`, `win`, `lose` |
| `play_note(note, length, volume)` | A note, or a chord |
| `play_notes(notes, step)` | A tune; `repeat=True` goes round until `.stop()` |
| `note(note, length)`, `chord(name, length)`, `rest(length)` | A tune a line at a time: each begins where the last ended. A length is `"quarter"`, `"eighth"`, or a number of beats |
| `loop_notes()`, `start_lines()` | `with loop_notes():` has a section go round; `start_lines()` begins every line again |
| `make_synth(name, ...)` | A synth of your own: `.play`, `.start`, `.stop`, `.play_notes`, `.arp`, and its settings as attributes |
| `lead.play(note, length, bend=, glide=, slide=, vibrato=)` | A note whose pitch moves: `bend="scoop"`, `"fall"`, `"dip"` or `{"to": 2, "over": "eighth"}`, `glide` from the last note, `slide=12`, `vibrato=True`. Also on `start` and `play_note`; a held note has `vibrato()` |
| `pad.trance_gate = "x.x.xx.x"`, `pad.set_trance_gate(pattern, rate=, depth=)`, `pad.trance_gate_step()` | The trance gate: a synth's sound chopped in a pattern of steps on the beat, with the settings `trance_gate_rate`, `trance_gate_depth`, `trance_gate_smooth`, `trance_gate_swing`, `trance_gate_stereo`, `trance_gate_sends` |
| `lead.arp_pattern = "trance"`, `lead.arp_step()` | A pattern of the synth's own that its arpeggios follow, and the step that is sounding |
| `lead.note_on(note, velocity, at=)`, `lead.note_off(note, at=)` | A key down and up, at a time of `sound_time()` for a sequencer of your own |
| `load_sample(path)` | A recorded sound from a file, as a synth |
| `load_samples(files)` | Several recordings as one instrument: `load_samples({"C2": "piano-C2.wav", "C3": "piano-C3.wav"})`; `kit=True` is a drum kit |
| `play_arp(chord)`, `start_arp(chord)` | A chord as an arpeggio: fast on one voice, or with `step="sixteenth"` a note struck at each step in time with the tempo, with `gate`, `octaves`, `swing`, `accent`, `pattern` and `order` |
| `chord_notes(name)`, `note_number(note)` | The notes of a chord, and a note as a number |
| `set_effects(...)` | The echo, reverb and chorus every synth shares; `reverb_level` and `echo_level` are how loud each comes back |
| `set_tempo(bpm)`, `beats(n)`, `beat()`, `length_beats(name)`, `sound_time()` | The beat, and the sound clock |
| `set_sound_buffer(size)`, `sound_buffer()` | How much sound is made at a time (`"small"`, `"medium"`, `"large"`, `"auto"`, or frames), for a page that clicks; and what it is now |
| `set_volume(v)`, `mute_sound()`, `unmute_sound()`, `stop_sound()` | All the sound |
| `main_synth()`, `sound_output()` | The synth `play_note` uses, and all the sound together, for dials and scopes |
| `sound_names()`, `synth_names()`, `setting_names()` | What there is |
| `play_song(path)` | A song from a file (`.mod`, `.xm`): `.pause()`, `.resume()`, `.stop()`, `.seek(part)`, `.volume` |
| `song.channel(n).volume`, `.pan`, `.reverb`, `.echo`; `song.loop(start, end)` | A channel's place in the song's mix, moved while it plays; and a stretch of the song that goes round |
| `song.mute(channel)`, `song.solo(channel)`, `song.loop_pattern()`, `song.replace(song)` | One channel silenced or heard alone, the pattern going round, and an edited song put in its place |
| `song.position`, `song.channel(n).level()` | Where the song is and what a channel is doing, for drawing them (a frame late) |
| `lead.samples()`, `lead.level()`, `lead.notes()` | What a synth is doing, for your own scope, meter and lit keys (a frame late). Also on `sound_output()` and the microphone |
| `lead.set(cutoff=4000, glide=2)` | Change settings, gliding there over two seconds |
| `use_microphone()` | The microphone, as a synth whose sound comes in: `.listen()`, `.mute()`, `.voice`, `.pitch`, `.ring`, `.comb`, `.gain`, `.gate`, `.state`, `.ready`, `.on_ready(fn)`. See [Your voice](sound.md#your-voice) |
| `lead.voice = "robot"`, `voice_names()` | A voice changer on a synth, a recording or the microphone: `robot`, `chipmunk`, `monster`, `cave`, `telephone`, `alien`, `whisper`, `"none"` |
| `lead.pitch_shift`, `lead.ring_mod`, `lead.comb`, `lead.flanger` | The voice effects, on any synth |
| `record_sound(seconds)`, `start_recording()`, `stop_recording()` | Record the microphone into a take, given back at once: `.done`, `.seconds`, `.on_done(fn)`, `.when_done()`, `.play("E4")`, `.sound_like(mic)` |
| `record_output(seconds)`, `lead.record(seconds)` | Record everything that is played, or one synth |
| `save_sound(take, "hello.wav")` | A recording or a sample as a WAV file: beside the scene with `pyctures run`, a download in a built page |
| `stop_microphone()` | Let the microphone go |
| `lead.play_from_midi()` | A MIDI keyboard plays a synth; `channel=2` for one channel, `False` to stop. See [MIDI](sound.md#midi) |
| `lead.learn(setting)`, `lead.map_midi(number, setting)`, `lead.unmap_midi(setting)` | A knob turns a setting: the next one moved, or one by its number |
| `on_midi_note`, `on_midi_note_off`, `on_midi_control`, `on_midi`, `on_midi_devices` | Functions you write, called with what a MIDI device sent. `on_midi_note(played)` hands one over by another name |
| `send_midi_note(note, velocity, length)`, `send_midi_note_off(note)` | A note out to another device |
| `send_midi_control(number, value)`, `send_midi_bend(bend)`, `send_midi_program(number)`, `send_midi(bytes)`, `send_midi_clock()` | A knob, the pitch wheel, a sound by number, any message, and the beat |
| `lead.send_to_midi()` | What a synth plays also goes out as MIDI |
| `midi_devices()`, `use_midi_input(name)`, `use_midi_output(name)` | What is plugged in, and which to use |
| `midi_input()`, `lead.midi_input()`, `midi_output()` | The MIDI device and channel as something a control is tied to: `select("device", midi_input(), "device")`, and `"channel"` |
| `receive_midi(message)`, `stop_midi()` | Pretend a message arrived; finish with MIDI |

## Dials and a keyboard

These come with `from pydials import *` at the top of the scene. Explained in [Dials and a keyboard](dials.md).

| Name | What it does |
|---|---|
| `dial(label, min, max, start)`, `slider(...)` | A number to turn or slide; or a setting of a synth: `dial("cutoff", lead, "cutoff")` |
| `button(label)`, `toggle(label)`, `select(label, choices)` | A button, a switch, and one of a list |
| `rotary(label, choices)` | A knob that clicks between a few choices; or a setting of a synth: `rotary("space", lead, "reverb_type")` |
| `keyboard(target, octave=4)` | A piano keyboard that plays a synth |
| `scope(source)`, `meter(source)` | A wave, or any value over time; a level |
| `number(label, min, max, start)`, `text_box(label, text)`, `readout(label, fn)` | A number box with − and +, a line of text to type, and a value shown |
| `checkbox(label, on)`, `choose(label, choices)`, `radio(...)`, `dropdown(label, choices)` | A box that is ticked; one of a few, all in sight; one of a long list |
| `xy_pad(label, target, "across", "up")`, `range_slider(label, min, max, [low, high])`, `fader(...)` | Two numbers under one finger, a slider with two handles, and an upright slider |
| `colour_picker(label, colour)`, `progress(label, value)`, `light(label, on)`, `busy(label)` | A colour to pick, a bar that fills, a light, and a ring that goes round |
| `joystick()`, `dpad()`, `action_button(label)` | For games: a stick for a thumb, a pad of arrows, a round button |
| `envelope(label, target)`, `step_grid(label, steps, rows)`, `pads(label, names, target)`, `pitch_wheel(...)`, `mod_wheel(...)`, `wheel(...)` | For music: the shape of a note as a graph, a grid of steps, pads to hit, and wheels |
| `steps(label, 16)`, `gate_pattern(label, target)`, `arp_pattern(label, target)`, `drum_seq(label, drums, target)` | A lane of steps, a gate's and an arpeggio's pattern, and a drum sequencer that plays by itself |
| `label(text)` | Words; made just before some controls, their heading |
| `with group(title):`, `with row():`, `with column():`, `with grid(3):` | Controls kept together on a titled plate; in a line, one under another, or in columns |
| `row()`, `wrap()`, `spacer()` | A new line, where a line may be split, and the room left over |
| `page(name)` | A page of controls with a tab |
| `layout(...)`, `theme(...)` | Where the plates go, how big, whether they wrap, a panel of a set size; the colours |
| `room()` | The rectangle no control is on |

## Other names

| Name | What it does | More |
|---|---|---|
| `measure(name)` | Times a part of a frame: `with measure("physics"):`, shown in the measure box | [Debugging](finding-mistakes.md) |
| `Event` | What a JavaScript event listener is handed: `canvas.addEventListener("click", on_click)` | [How a program is shaped](program-shape.md#callbacks) |

## Image processing

There are none in the library. A scene loads and draws a picture (`load_image`, `picture`, `ctx.draw_image`). Picture methods such as `await img.remove_background()` belong to Python programs inside Circuitry Studio, and are not part of Pyctures used on its own or in a built page: [Images from Code](https://www.circuitry.dev/docs/pyctures/images).

## Related

- [2D functions](2d-functions.md): every 2D function, with pictures and examples
- [3D functions](3d-functions.md): every 3D function
- [How a program is shaped](program-shape.md): how a program is put together
