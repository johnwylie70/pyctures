# Tutorial: A Spinning 3D Cube

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/spinning-cube](https://www.circuitry.dev/docs/pyctures/tutorials/spinning-cube) (in Circuitry Studio's help)

Your first 3D program: a lit cube that spins, then the same cube with a floor, outlined edges, and a camera you can turn by dragging. For the pieces in more depth, see [3D scenes](../3d.md).

## 1. The cube

```python
# the renderer draws on the canvas
renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)

# the world, and where we look at it from
scene = THREE.Scene()
scene.background = THREE.Color("#14141c")
camera = THREE.PerspectiveCamera(60, width / height, 0.1, 100)
camera.position.z = 3

# a cube: a box shape with a material that reacts to light
cube = THREE.Mesh(
    THREE.BoxGeometry(1, 1, 1),
    THREE.MeshStandardMaterial(color="dodgerblue"),
)
scene.add(cube)

# light: a soft fill everywhere, and one bright light from the top right
scene.add(THREE.AmbientLight("white", 0.5))
light = THREE.DirectionalLight("white", 2.5)
light.position.set(2, 3, 4)
scene.add(light)

def draw():
    cube.rotation.x += 0.01
    cube.rotation.y += 0.015
    renderer.render(scene, camera)
```

Reading it from the top:

1. **The renderer** draws the 3D picture on the canvas. These three lines start every 3D program; copy them as they are.
2. **The scene** is the world. Its background is a dark grey.
3. **The camera** is your eye. `60` is how wide it sees, in degrees; `width / height` is the shape of the canvas; it sees things between 0.1 and 100 units away. It sits 3 units back from the middle (`position.z = 3`), looking at the middle.
4. **The cube** is a *mesh*: a shape (`BoxGeometry`, 1 unit each way) plus a material (`MeshStandardMaterial`, blue).
5. **The lights**: without light, a standard material is black. The ambient light lights everything a little; the directional light shines from one direction like the sun, which is what makes the sides different shades.
6. **`draw()`** turns the cube a little more each frame and draws the scene.

Rotations are in radians, so `0.01` a frame at 60 frames a second is about 34 degrees a second.

## 2. Turn it with your finger

Add orbit controls and the camera circles the cube as you drag. A floor grid and outlined edges make the shape easier to read.

```python
renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)

scene = THREE.Scene()
scene.background = THREE.Color("#14141c")
camera = THREE.PerspectiveCamera(60, width / height, 0.1, 100)
camera.position.set(2, 2, 3)

# drag to turn, pinch or scroll to zoom
controls = addons.OrbitControls(camera, canvas)
controls.enableDamping = True

geometry = THREE.BoxGeometry(1, 1, 1)
cube = THREE.Mesh(geometry, THREE.MeshStandardMaterial(color="dodgerblue", roughness=0.4))
cube.position.y = 0.8
scene.add(cube)

# white lines along the cube's edges, added to the cube so they turn with it
edges = THREE.LineSegments(
    THREE.EdgesGeometry(geometry),
    THREE.LineBasicMaterial(color="white"),
)
cube.add(edges)

scene.add(THREE.GridHelper(6, 12, "#555", "#333"))
scene.add(THREE.AmbientLight("white", 0.5))
light = THREE.DirectionalLight("white", 2.5)
light.position.set(2, 3, 4)
scene.add(light)

spinning = True

def on_key_down(key):
    global spinning
    if key == " ":
        spinning = not spinning

def draw():
    if spinning:
        cube.rotation.y += 0.015
    controls.update()
    renderer.render(scene, camera)
```

- `addons.OrbitControls(camera, canvas)` moves the camera when you drag on the canvas. `enableDamping` lets it glide to a stop, and `controls.update()` in `draw()` keeps it moving.
- `cube.add(edges)` puts the lines inside the cube, so they move and turn with it.
- Press space (after clicking the canvas) to pause and restart the spin.

You never need to handle resizing: when the canvas changes size, the picture and the camera are refitted for you.

## Try this

- Swap `BoxGeometry(1, 1, 1)` for `TorusKnotGeometry(0.5, 0.15, 128, 16)`.
- Make it metal: `MeshStandardMaterial(color="silver", metalness=1, roughness=0.3)`.
- Make a row of cubes with a `for` loop, each with its own `position.x` and colour, and keep them in a list to spin in `draw()`.

## Related

- [3D scenes](../3d.md)
- Next: [lighting a scene](../tutorials/lighting.md)
