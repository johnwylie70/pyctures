# 3D Functions

Full reference: [www.circuitry.dev/docs/pyctures/3d-functions](https://www.circuitry.dev/docs/pyctures/3d-functions) (in Circuitry Studio's help)

The 3D parts you can use from Python, grouped by job, one line each. `THREE` is the full three.js 3D toolkit, so everything in its documentation works; this page covers the parts used most. For the rest, see [threejs.org/docs](https://threejs.org/docs/).

New to 3D? Start with [3D scenes](3d.md) and the [spinning cube tutorial](tutorials/spinning-cube.md), and come back here to look things up.

**Writing three.js in Python.** A capitalised name makes something new: `THREE.Mesh(...)`, never `new`. Options are keyword arguments: `THREE.MeshStandardMaterial(color="red", roughness=0.4)`. Values change in place: `mesh.rotation.y += 0.01`. snake_case works (`set_pixel_ratio`), but this page uses three.js's own names so they match its documentation. Reading a value that three.js worked out needs `await` (see [reading a value back](program-shape.md#reading-a-value-back-with-await)).

## Renderer

The renderer draws the scene onto the canvas. Start every 3D program with the first three lines.

| Python | What it does |
|---|---|
| `renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)` | Makes a renderer that draws on the canvas, with smooth edges |
| `renderer.setPixelRatio(pixel_ratio)` | Sharp on high-resolution screens |
| `renderer.setSize(width, height, False)` | Fits the canvas. Done again for you whenever the canvas is resized. |
| `renderer.render(scene, camera)` | Draws one picture; call it in `draw()` |
| `renderer.setClearColor("navy", 1)` | The colour behind the scene when it has no background; the second number is how solid |
| `renderer.shadowMap.enabled = True` | Turns shadows on ([Lights](#lights)) |
| `renderer.shadowMap.type = THREE.PCFSoftShadowMap` | Soft-edged shadows. Also `BasicShadowMap` (hard, fastest), `PCFShadowMap` (the default), `VSMShadowMap`. |
| `renderer.toneMapping = THREE.ACESFilmicToneMapping` | Softens very bright light the way a film camera does. Also `NoToneMapping` (the default), `LinearToneMapping`, `ReinhardToneMapping`, `AgXToneMapping`, `NeutralToneMapping`. |
| `renderer.toneMappingExposure = 1.2` | Overall brightness when tone mapping is on |
| `renderer.outputColorSpace = THREE.SRGBColorSpace` | How colours are sent to the screen. This is already the default; leave it unless you know you need `LinearSRGBColorSpace`. |

## Scene and fog

| Python | What it does |
|---|---|
| `scene = THREE.Scene()` | The world everything goes in |
| `scene.add(thing)`, `scene.remove(thing)` | Puts something in the world, or takes it out |
| `scene.background = THREE.Color("skyblue")` | The colour behind everything. A texture works too. |
| `scene.fog = THREE.Fog("white", near, far)` | Fog that starts at distance `near` and hides everything by `far`. Use the background colour for the fog colour. |
| `scene.fog = THREE.FogExp2("white", 0.05)` | Fog that thickens steadily with distance; the number is how thick |

## Cameras

| Python | What it does |
|---|---|
| `THREE.PerspectiveCamera(fov, width / height, near, far)` | A camera that sees the way eyes do: far things look smaller. `fov` is how wide it sees, in degrees (50 to 75 is usual); it sees from `near` to `far`. |
| `THREE.OrthographicCamera(left, right, top, bottom, near, far)` | A camera with no perspective: far things look the same size. Good for plans, maps and some games. It is not refitted on resize; set its sides from `width` and `height` yourself. |
| `camera.position.set(x, y, z)` | Where the camera is |
| `camera.lookAt(x, y, z)` | Points it at a spot |
| `camera.fov = 30`, `camera.near`, `camera.far`, `camera.zoom = 2` | Change its settings; follow with `camera.updateProjectionMatrix()` |
| `camera.updateProjectionMatrix()` | Applies changed camera settings |

Perspective cameras are refitted to the canvas's shape for you when it is resized.

## Geometries: shapes

A geometry is a shape. Put it in a `THREE.Mesh` with a material to see it. Sizes are in scene units; the optional numbers at the end (segments) say how smooth curved surfaces are.

| Python | Shape |
|---|---|
| `THREE.BoxGeometry(w, h, d)` | A box |
| `THREE.SphereGeometry(radius, 32, 16)` | A ball |
| `THREE.PlaneGeometry(w, h)` | A flat rectangle, facing you. Turn it flat with `mesh.rotation.x = -math.pi / 2` for a floor. |
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
| `THREE.LatheGeometry(points, 32)` | Spins a side outline (a list of `THREE.Vector2`) round the up axis, like a vase on a potter's wheel |
| `THREE.ExtrudeGeometry(shape, depth=0.5, bevelEnabled=False)` | Pushes a flat `THREE.Shape` out into a solid, like a cookie cutter |
| `THREE.TubeGeometry(curve, 64, radius, 8, False)` | A tube along a curve, such as `THREE.CatmullRomCurve3([...points])` |
| `THREE.EdgesGeometry(geometry)` | Just the edges of another shape, for `LineSegments` |
| `THREE.WireframeGeometry(geometry)` | Every triangle's edges, for `LineSegments` |
| `THREE.BufferGeometry()` | Your own shape from numbers: `geometry.setAttribute("position", THREE.Float32BufferAttribute(numbers, 3))`, three numbers per corner |

A `THREE.Shape()` is drawn like a 2D path: `shape.moveTo(x, y)`, `shape.lineTo(x, y)`, `shape.quadraticCurveTo(...)`, `shape.bezierCurveTo(...)`, `shape.absarc(x, y, r, start, end)`, `shape.closePath()`.

```python
import math

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color("#15151c")
camera = THREE.PerspectiveCamera(40, width / height, 0.1, 100)
camera.position.set(0, 0, 18)
scene.add(THREE.HemisphereLight("white", "#334", 1.5))
sun = THREE.DirectionalLight("white", 2)
sun.position.set(3, 5, 6)
scene.add(sun)

# a star outline, for ExtrudeGeometry
star = THREE.Shape()
for i in range(10):
    r = 0.7 if i % 2 == 0 else 0.3
    a = i * math.pi / 5 + math.pi / 2
    if i == 0:
        star.moveTo(r * math.cos(a), r * math.sin(a))
    else:
        star.lineTo(r * math.cos(a), r * math.sin(a))
star.closePath()

# a vase outline, for LatheGeometry
vase = [THREE.Vector2(0.25 + 0.3 * math.sin(i / 2.5), i * 0.14 - 0.7) for i in range(11)]

# a wiggly path, for TubeGeometry
path = THREE.CatmullRomCurve3([THREE.Vector3(-0.7, -0.5, 0), THREE.Vector3(-0.3, 0.6, 0.3),
                               THREE.Vector3(0.3, -0.6, -0.3), THREE.Vector3(0.7, 0.5, 0)])

shapes = [
    THREE.BoxGeometry(1.1, 1.1, 1.1),
    THREE.SphereGeometry(0.7, 32, 16),
    THREE.PlaneGeometry(1.3, 1.3),
    THREE.CircleGeometry(0.7, 32),
    THREE.RingGeometry(0.35, 0.7, 32),
    THREE.CylinderGeometry(0.5, 0.5, 1.3, 32),
    THREE.ConeGeometry(0.6, 1.3, 32),
    THREE.CapsuleGeometry(0.4, 0.6, 8, 16),
    THREE.TorusGeometry(0.5, 0.2, 16, 48),
    THREE.TorusKnotGeometry(0.45, 0.14, 100, 16),
    THREE.TetrahedronGeometry(0.8),
    THREE.OctahedronGeometry(0.75),
    THREE.DodecahedronGeometry(0.7),
    THREE.IcosahedronGeometry(0.7),
    THREE.LatheGeometry(vase, 32),
    THREE.ExtrudeGeometry(star, depth=0.3, bevelEnabled=False),
    THREE.TubeGeometry(path, 64, 0.12, 8, False),
]
meshes = []
for i, geometry in enumerate(shapes):
    mesh = THREE.Mesh(geometry, THREE.MeshStandardMaterial(
        color=f"hsl({i * 21}, 70%, 60%)", roughness=0.5, side=THREE.DoubleSide))
    mesh.position.set((i % 6 - 2.5) * 2.1, 2.3 - (i // 6) * 2.3, 0)
    scene.add(mesh)
    meshes.append(mesh)

# EdgesGeometry and WireframeGeometry draw lines, not surfaces
box = THREE.BoxGeometry(1.1, 1.1, 1.1)
edges = THREE.LineSegments(THREE.EdgesGeometry(box), THREE.LineBasicMaterial(color="white"))
edges.position.set(2.5 * 2.1, -2.3, 0)
scene.add(edges)
meshes.append(edges)

t = 0

def update(dt):
    global t
    t += dt

def draw():
    for m in meshes:
        m.rotation.x = 0.5
        m.rotation.y = 0.6 + 0.4 * math.sin(t)     # rock gently, so flat shapes stay in view
    renderer.render(scene, camera)
```


From the top left: box, sphere, plane, circle, ring, cylinder; cone, capsule, torus, torus knot, tetrahedron, octahedron; dodecahedron, icosahedron, lathe, extrude, tube and edges.

## Materials: how surfaces look

| Python | Looks |
|---|---|
| `THREE.MeshBasicMaterial(color=…)` | Flat colour, ignores light, always visible |
| `THREE.MeshLambertMaterial(color=…)` | Matte, like chalk or paper |
| `THREE.MeshPhongMaterial(color=…, shininess=80, specular="white")` | Shiny highlights, like plastic |
| `THREE.MeshStandardMaterial(color=…, roughness=0.5, metalness=0)` | Realistic. `roughness` 0 is polished, 1 is rough; `metalness` 1 is metal. |
| `THREE.MeshPhysicalMaterial(color=…, clearcoat=1, transmission=0.9, thickness=0.5)` | Standard, plus extras: `clearcoat` (a varnish layer), `transmission` (glass that lets light through), `sheen` (cloth), `iridescence` (soap-bubble colours) |
| `THREE.MeshToonMaterial(color=…)` | Cartoon shading in a few flat bands |
| `THREE.MeshNormalMaterial()` | Rainbow colours by which way each face points; needs no light |
| `THREE.MeshDepthMaterial()` | White near the camera, fading to black far away |
| `THREE.LineBasicMaterial(color=…)` | For lines (`Line`, `LineSegments`, `LineLoop`) |
| `THREE.LineDashedMaterial(color=…, dashSize=0.2, gapSize=0.1)` | Dashed lines; call `line.computeLineDistances()` once |
| `THREE.PointsMaterial(color=…, size=0.05)` | For `Points` |
| `THREE.SpriteMaterial(map=texture)` | For `Sprite`, a picture that always faces the camera |

Options most materials take:

| Option | What it does |
|---|---|
| `color="tomato"` | The surface colour ([Colours](colours.md#colours-in-3d)) |
| `emissive="orange"`, `emissiveIntensity=1` | A glow the surface gives off by itself |
| `map=texture` | A picture wrapped round the surface ([Textures](#textures)) |
| `roughness`, `metalness` | Standard and Physical only: rough or polished, metal or not |
| `wireframe=True` | Draws the edges of every triangle only |
| `flatShading=True` | Shows the flat faces rather than smoothing over them |
| `side=THREE.DoubleSide` | Shows both sides of flat shapes (`FrontSide` is the default, `BackSide` the inside) |
| `transparent=True, opacity=0.5` | See-through; `opacity` does nothing without `transparent` |

```python
renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color("#20232b")
camera = THREE.PerspectiveCamera(40, width / height, 0.1, 100)
camera.position.set(0, 0, 14)
scene.add(THREE.AmbientLight("white", 0.3))
sun = THREE.DirectionalLight("white", 2.5)
sun.position.set(-3, 4, 5)
scene.add(sun)

materials = [
    THREE.MeshBasicMaterial(color="tomato"),
    THREE.MeshLambertMaterial(color="tomato"),
    THREE.MeshPhongMaterial(color="tomato", shininess=100),
    THREE.MeshStandardMaterial(color="tomato", roughness=0.3),
    THREE.MeshStandardMaterial(color="gold", roughness=0.3, metalness=0.6),
    THREE.MeshPhysicalMaterial(color="tomato", roughness=0.4, clearcoat=1),
    THREE.MeshToonMaterial(color="tomato"),
    THREE.MeshNormalMaterial(),
    THREE.MeshStandardMaterial(color="tomato", wireframe=True),
    THREE.MeshStandardMaterial(color="tomato", flatShading=True),
    THREE.MeshStandardMaterial(color="#311", emissive="orange", emissiveIntensity=0.8),
    THREE.MeshStandardMaterial(color="deepskyblue", transparent=True, opacity=0.4),
]
balls = []
for i, material in enumerate(materials):
    ball = THREE.Mesh(THREE.SphereGeometry(0.8, 32, 16), material)
    ball.position.set((i % 4 - 1.5) * 2.1, 2.3 - (i // 4) * 2.3, 0)
    scene.add(ball)
    balls.append(ball)

def draw():
    for b in balls:
        b.rotation.y += 0.01
    renderer.render(scene, camera)
```


Top row: basic, Lambert, Phong, standard. Middle row: standard with some metalness, physical with clearcoat, toon, normal. Bottom row: wireframe, flat shading, emissive, see-through. Shiny metal reflects its surroundings, so in a scene with nothing round it, full metalness looks dark.

## Lights

| Python | What it is |
|---|---|
| `THREE.AmbientLight(colour, intensity)` | A little light everywhere, from no direction |
| `THREE.HemisphereLight(sky, ground, intensity)` | Sky colour from above, ground colour from below |
| `THREE.DirectionalLight(colour, intensity)` | The sun: parallel light from `position` towards `target` (the middle unless you move it) |
| `THREE.PointLight(colour, intensity, distance, decay)` | A bulb: light in every direction from one spot. `distance` 0 means no cut-off; `decay` 2 is natural fading. |
| `THREE.SpotLight(colour, intensity, distance, angle, penumbra, decay)` | A torch: a cone of light from `position` towards `target`. `angle` is how wide in radians; `penumbra` 0 to 1 how soft the edge is. |
| `THREE.RectAreaLight(colour, intensity, w, h)` | A glowing panel, like a window or a softbox. Lights only Standard and Physical materials, and casts no shadows. Point it with `light.lookAt(x, y, z)`. |

Settings lights share:

| Python | What it does |
|---|---|
| `light.intensity = 2` | Brightness |
| `light.color.set("orange")` | Colour |
| `light.position.set(x, y, z)` | Where it is |
| `light.target.position.set(x, y, z)` | Where directional and spot lights point; also `scene.add(light.target)` |
| `light.visible = False` | Switches it off |
| `light.castShadow = True` | Directional, point and spot lights can cast shadows (turn on `renderer.shadowMap.enabled` and set `castShadow`/`receiveShadow` on objects) |
| `light.shadow.mapSize.width = 2048` (and `.height`) | Sharper shadows, at a cost in speed |
| `light.shadow.bias = -0.0005` | Removes stripy marks on surfaces that shadow themselves |
| `light.shadow.radius = 4` | Blurs shadow edges (with `PCFSoftShadowMap` off, `PCFShadowMap` on) |
| `light.shadow.camera.left` / `right` / `top` / `bottom` | How big an area a directional light's shadows cover |

The [lighting tutorial](tutorials/lighting.md) explains each light and shadows step by step. This program shows each light on its own, in six small views of the same scene:

```python
import math

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
renderer.shadowMap.enabled = True
renderer.setScissorTest(True)       # lets us draw into one part of the canvas at a time
camera = THREE.PerspectiveCamera(45, 1, 0.1, 100)
camera.position.set(4, 4, 6)
camera.lookAt(0, 0.6, 0)

def make_scene(light, name):
    scene = THREE.Scene()
    scene.background = THREE.Color("#0c0c10")
    floor = THREE.Mesh(THREE.PlaneGeometry(8, 8), THREE.MeshStandardMaterial(color="#999"))
    floor.rotation.x = -math.pi / 2
    floor.receiveShadow = True
    scene.add(floor)
    ball = THREE.Mesh(THREE.SphereGeometry(0.8, 32, 16), THREE.MeshStandardMaterial(color="tomato", roughness=0.4))
    ball.position.set(-0.9, 0.8, 0)
    box = THREE.Mesh(THREE.BoxGeometry(1.2, 1.2, 1.2), THREE.MeshStandardMaterial(color="mediumseagreen"))
    box.position.set(1, 0.6, 0.3)
    for thing in (ball, box):
        thing.castShadow = True
        scene.add(thing)
    scene.add(light)
    return scene, name

sun = THREE.DirectionalLight("white", 3)
sun.position.set(4, 6, 3)
sun.castShadow = True
bulb = THREE.PointLight("orange", 30, 0)
bulb.position.set(0, 2.2, 1.5)
bulb.castShadow = True
spot = THREE.SpotLight("white", 60, 0, 0.45, 0.4)
spot.position.set(-3, 5, 2)
spot.castShadow = True
panel = THREE.RectAreaLight("white", 6, 3, 1.5)
panel.position.set(0, 3, 2.5)
panel.lookAt(0, 0, 0)

views = [
    make_scene(THREE.AmbientLight("white", 1), "AmbientLight"),
    make_scene(THREE.HemisphereLight("skyblue", "saddlebrown", 2.5), "HemisphereLight"),
    make_scene(sun, "DirectionalLight"),
    make_scene(bulb, "PointLight"),
    make_scene(spot, "SpotLight"),
    make_scene(panel, "RectAreaLight"),
]

def draw():
    w, h = width / 3, height / 2
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    for i, (scene, name) in enumerate(views):
        x, y = (i % 3) * w, (1 - i // 3) * h      # y counts up from the bottom here
        renderer.setViewport(x, y, w, h)
        renderer.setScissor(x, y, w, h)
        renderer.render(scene, camera)
```


Top row: ambient, hemisphere, directional. Bottom row: point, spot, rectangle area.

## Objects

| Python | What it is |
|---|---|
| `THREE.Mesh(geometry, material)` | A solid object |
| `THREE.Group()` | An empty holder: things added to it move, turn and scale with it |
| `THREE.Points(geometry, THREE.PointsMaterial(size=0.05))` | A dot at every position in the geometry |
| `THREE.Line(geometry, material)` | A line through the positions, in order |
| `THREE.LineLoop(geometry, material)` | The same, joined back to the start |
| `THREE.LineSegments(geometry, material)` | Separate lines, one for each pair of positions |
| `THREE.Sprite(THREE.SpriteMaterial(map=texture))` | A flat picture that always faces the camera, for labels and particles |
| `THREE.InstancedMesh(geometry, material, count)` | Many copies of one mesh drawn at once, much faster than many meshes. Place each with `mesh.setMatrixAt(i, matrix)`, then set `mesh.instanceMatrix.needsUpdate = True`. Colour each with `mesh.setColorAt(i, THREE.Color(...))`. |

A geometry for lines and points is made from a list of positions: `THREE.BufferGeometry().setFromPoints([THREE.Vector3(0, 0, 0), THREE.Vector3(1, 1, 0)])`.

```python
import math, random

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color("#101018")
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(0, 5, 11)
camera.lookAt(0, 0, 0)
scene.add(THREE.HemisphereLight("white", "#223", 2))

# 400 cubes in one InstancedMesh
count = 400
cubes = THREE.InstancedMesh(THREE.BoxGeometry(0.25, 0.25, 0.25), THREE.MeshStandardMaterial(), count)
place = THREE.Matrix4()
for i in range(count):
    a = i * 0.25
    r = 1 + i * 0.01
    place.setPosition(r * math.cos(a), i * 0.008 - 1.6, r * math.sin(a))
    cubes.setMatrixAt(i, place)
    cubes.setColorAt(i, THREE.Color(f"hsl({i}, 80%, 60%)"))
cubes.instanceMatrix.needsUpdate = True
scene.add(cubes)

# a circle as a LineLoop, and a dashed line
circle = [THREE.Vector3(4 * math.cos(a / 20 * math.tau), -1.7, 4 * math.sin(a / 20 * math.tau)) for a in range(20)]
scene.add(THREE.LineLoop(THREE.BufferGeometry().setFromPoints(circle), THREE.LineBasicMaterial(color="white")))
dashed = THREE.Line(THREE.BufferGeometry().setFromPoints([THREE.Vector3(0, -1.7, 0), THREE.Vector3(0, 2.5, 0)]),
                    THREE.LineDashedMaterial(color="gold", dashSize=0.2, gapSize=0.1))
dashed.computeLineDistances()
scene.add(dashed)

# a label: a Sprite with a picture drawn on a 2D canvas
label = js.document.create_element("canvas")
label.width = 256
label.height = 64
pen = label.get_context("2d")
pen.fill_style = "white"
pen.font = "bold 40px sans-serif"
pen.text_align = "center"
pen.fill_text("400 cubes", 128, 46)
sign = THREE.Sprite(THREE.SpriteMaterial(map=THREE.CanvasTexture(label)))
sign.scale.set(2, 0.5, 1)
sign.position.y = 2.8
scene.add(sign)

def draw():
    cubes.rotation.y += 0.005
    renderer.render(scene, camera)
```


## Moving and arranging

Every object has these:

| Python | What it does |
|---|---|
| `thing.position.set(x, y, z)`, `thing.position.x = 2` | Where it is. `y` is up. |
| `thing.rotation.set(x, y, z)`, `thing.rotation.y += 0.01` | How it is turned round each axis, in radians |
| `thing.scale.set(2, 1, 1)`, `thing.scale.setScalar(2)` | How big it is along each axis |
| `thing.lookAt(x, y, z)` | Turns it to face a spot |
| `thing.add(other)`, `thing.remove(other)` | Puts `other` inside `thing`, so it moves with it ([groups](3d.md#groups)) |
| `thing.visible = False` | Hides it |
| `thing.name = "door"` | A name, handy when [picking](#picking-and-controls) |
| `thing.castShadow`, `thing.receiveShadow` | Whether it makes shadows and shows them |

To change many objects, keep them in a Python list and loop over it. Three.js's own `traverse` does not suit Python: functions you pass to the canvas are called later, as events, not straight away.

## Textures

A texture is a picture wrapped round a surface. Give it to a material as `map=texture`.

| Python | What it does |
|---|---|
| `THREE.TextureLoader().load(address)` | Loads a picture: a path from the scene (`"textures/brick.png"`, included by `pyctures build`), or a web address, whose site must allow other pages to use its pictures. |
| `THREE.CanvasTexture(a_canvas)` | Uses a 2D canvas you drew on as the picture: text, patterns, anything from [2D functions](2d-functions.md) |
| `texture.needsUpdate = True` | After you draw on that canvas again, shows the change |
| `texture.wrapS = texture.wrapT = THREE.RepeatWrapping` | Lets the picture repeat across and down (write it as two lines in Python) |
| `texture.repeat.set(4, 4)` | How many times it repeats |
| `texture.colorSpace = THREE.SRGBColorSpace` | Shows a photo's colours correctly |
| `texture.magFilter = THREE.NearestFilter` | Keeps pixel-art textures blocky |

```python
import math

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color("#1a1a22")
scene.fog = THREE.Fog("#1a1a22", 6, 18)
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(0, 2.5, 5)
camera.lookAt(0, 0.5, 0)
scene.add(THREE.HemisphereLight("white", "#334", 2.5))

# draw a checkerboard on a small 2D canvas...
board = js.document.create_element("canvas")
board.width = 64
board.height = 64
pen = board.get_context("2d")
for row in range(8):
    for col in range(8):
        pen.fill_style = "#eee" if (row + col) % 2 == 0 else "#447"
        pen.fill_rect(col * 8, row * 8, 8, 8)

# ...and use it as a repeating floor texture
floor_texture = THREE.CanvasTexture(board)
floor_texture.wrapS = THREE.RepeatWrapping
floor_texture.wrapT = THREE.RepeatWrapping
floor_texture.repeat.set(6, 6)
floor_texture.magFilter = THREE.NearestFilter
floor = THREE.Mesh(THREE.PlaneGeometry(30, 30), THREE.MeshStandardMaterial(map=floor_texture))
floor.rotation.x = -math.pi / 2
scene.add(floor)

# a die: one canvas per face
faces = []
for n in range(1, 7):
    face = js.document.create_element("canvas")
    face.width = 128
    face.height = 128
    p = face.get_context("2d")
    p.fill_style = "white"
    p.fill_rect(0, 0, 128, 128)
    p.fill_style = "crimson"
    p.font = "bold 90px sans-serif"
    p.text_align = "center"
    p.text_baseline = "middle"
    p.fill_text(str(n), 64, 70)
    faces.append(THREE.MeshStandardMaterial(map=THREE.CanvasTexture(face)))
die = THREE.Mesh(THREE.BoxGeometry(1.2, 1.2, 1.2), faces)
die.position.y = 0.9
scene.add(die)

def draw():
    die.rotation.x += 0.007
    die.rotation.y += 0.01
    renderer.render(scene, camera)
```


A mesh given a list of six materials uses one per face of a box, as the die does.

## Helpers

Lines that help you see what is going on while you build a scene. Remove them when you are done.

| Python | Shows |
|---|---|
| `THREE.GridHelper(size, divisions)` | A grid on the floor |
| `THREE.AxesHelper(length)` | The three axes: x red, y green, z blue |
| `THREE.DirectionalLightHelper(light, size)` | Where a directional light is and which way it points |
| `THREE.PointLightHelper(light, size)` | Where a point light is |
| `THREE.SpotLightHelper(light)` | A spot light's cone |
| `THREE.HemisphereLightHelper(light, size)` | A hemisphere light |
| `THREE.CameraHelper(light.shadow.camera)` | The box a light's shadows cover |
| `THREE.BoxHelper(thing, "yellow")` | A box round an object |

## Maths

| Python | What it is |
|---|---|
| `THREE.Vector3(x, y, z)` | A position or direction in 3D. `.set`, `.add(v)`, `.multiplyScalar(n)`, `.normalize()`, `.lerp(v, t)` |
| `THREE.Vector2(x, y)` | The same in 2D |
| `THREE.Color(…)` | A colour ([Colours](colours.md#colours-in-3d)) |
| `THREE.Euler(x, y, z)` | A turn round each axis, in radians: what `rotation` is |
| `THREE.Quaternion()` | Another way to store a turn, which never gets stuck. `thing.quaternion.setFromAxisAngle(THREE.Vector3(0, 1, 0), angle)` |
| `THREE.Matrix4()` | Position, turn and size in one; used by `InstancedMesh`. `.setPosition(x, y, z)`, `.makeRotationY(a)`, `.compose(position, quaternion, scale)` |
| `THREE.MathUtils.degToRad(90)` | Degrees to radians; in Python, `math.radians(90)` does the same and needs no answer back |

Time: use the `dt` that `update(dt)` is given, rather than a three.js clock.

Most maths is easiest in plain Python: keep positions as Python numbers, work them out with `math`, and set the results with `position.set(...)`.

## Picking and controls

**Picking** finds what is under a point on the screen:

| Python | What it does |
|---|---|
| `ray = THREE.Raycaster()` | Makes a picker |
| `ray.setFromCamera(THREE.Vector2(x, y), camera)` | Aims it through a point, where `x` and `y` run from -1 to 1 across and up the canvas: `x = event.x / width * 2 - 1`, `y = -(event.y / height) * 2 + 1` |
| `hits = ray.intersectObjects(list_of_things)` | What it hits, nearest first. `await hits.length` says how many; `hits[0].object` is the nearest thing, `hits[0].point` where. |

A full example is in [3D scenes: picking](3d.md#picking-what-did-i-click).

**Orbit controls** let you turn the camera by dragging:

| Python | What it does |
|---|---|
| `controls = addons.OrbitControls(camera, canvas)` | Drag to orbit, pinch or scroll to zoom, two fingers or right-drag to pan |
| `controls.update()` | Call every frame in `draw()` |
| `controls.target.set(x, y, z)` | The point it orbits round |
| `controls.enableDamping = True` | Glides to a stop when you let go |
| `controls.autoRotate = True`, `controls.autoRotateSpeed = 2` | Turns slowly by itself |
| `controls.minDistance = 2`, `controls.maxDistance = 20` | How close and how far you can zoom |
| `controls.maxPolarAngle = math.pi / 2` | Stops the camera going below the floor |
| `controls.enableZoom`, `controls.enablePan`, `controls.enableRotate` | Switch each gesture on or off |

## Related

- [3D scenes](3d.md): the ideas, with examples
- [Tutorial: lighting a scene](tutorials/lighting.md)
- [Colours](colours.md)
- [2D functions](2d-functions.md)
- [three.js documentation](https://threejs.org/docs/)
