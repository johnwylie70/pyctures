# Tutorial: Lighting a Scene

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/lighting](https://www.circuitry.dev/docs/pyctures/tutorials/lighting) (in Circuitry Studio's help)

Light decides how a 3D scene looks. This page explains the five kinds of light, what each one is for, and how to turn on shadows, then gives you a lit scene where number keys switch each light on and off so you can see what it adds.

## Materials need light

`MeshStandardMaterial`, `MeshLambertMaterial` and `MeshPhongMaterial` show nothing but black until a light reaches them. `MeshBasicMaterial` and `MeshNormalMaterial` ignore light and always show, which is useful for things that glow, like a lamp or the sun.

Each light has a **colour** and an **intensity** (how bright it is). Add it to the scene with `scene.add(light)`, and switch it off with `light.visible = False`.

## The five lights

### Ambient light: a little light everywhere

```python
ambient = THREE.AmbientLight("white", 0.4)
scene.add(ambient)
```

Lights every surface equally, from no direction. It stops shadows from being pitch black, but on its own it makes objects look flat, because every side is the same shade. Keep it low (0.2 to 0.5) and use it with another light.

### Hemisphere light: sky above, ground below

```python
hemi = THREE.HemisphereLight("lightskyblue", "saddlebrown", 1.2)
scene.add(hemi)
```

Like ambient light, but surfaces facing up get the first colour (the sky) and surfaces facing down get the second (the ground). It is a simple way to make an outdoor scene look natural, and a good first light for any scene.

### Directional light: the sun

```python
sun = THREE.DirectionalLight("white", 2.5)
sun.position.set(4, 6, 3)
scene.add(sun)
```

Parallel rays from one direction, like sunlight. Only the direction matters: it shines from its `position` towards the middle of the scene. Sides facing it are bright, sides facing away are dark, which is what makes shapes look solid. Most scenes have one.

### Point light: a light bulb

```python
bulb = THREE.PointLight("orange", 20, 0)
bulb.position.set(0, 2, 0)
scene.add(bulb)
```

Shines in every direction from one spot and fades with distance, like a bulb or a candle. The third number is how far it reaches (`0` means it fades naturally with no cut-off). Because it fades, it needs a bigger intensity than the sun: try 10 to 50 for a light a few units away.

### Spot light: a torch or stage light

```python
spot = THREE.SpotLight("white", 60)
spot.position.set(-3, 5, 2)
spot.angle = 0.4          # how wide the beam is, in radians
spot.penumbra = 0.5       # how soft its edge is, 0 to 1
scene.add(spot)
```

A cone of light from one spot, pointing at the middle of the scene. Like a point light it fades with distance.

## Shadows

Shadows are off until you turn them on in three places: the renderer, each light that should cast them, and each object.

```python
renderer.shadowMap.enabled = True              # 1. the renderer draws shadows
renderer.shadowMap.type = THREE.PCFSoftShadowMap   # soft edges

sun.castShadow = True                          # 2. this light makes shadows
sun.shadow.mapSize.width = 2048                # sharper shadows (costs speed)
sun.shadow.mapSize.height = 2048

ball.castShadow = True                         # 3. this object throws a shadow
floor.receiveShadow = True                     #    and this one shows shadows on it
```

- **Directional, point and spot lights** can cast shadows. Ambient and hemisphere lights cannot.
- An object can both cast and receive shadows: set both to `True`.
- A directional light only makes shadows inside a box around the middle of the scene. If shadows are cut off at an edge, make the box bigger: `sun.shadow.camera.left = -8`, and the same for `right` (8), `top` (8) and `bottom` (-8).
- If a surface shows stripes on itself (called shadow acne), set `sun.shadow.bias = -0.0005`.
- Each shadow-casting light costs drawing time, so use one or two.

## A lit scene to try

Run this, click the canvas so it has the keyboard, and press the number keys **1** to **5** to switch each light on and off. Press **s** to switch shadows on and off. Drag to look around.

```python
import math

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
renderer.shadowMap.enabled = True
renderer.shadowMap.type = THREE.PCFSoftShadowMap

scene = THREE.Scene()
scene.background = THREE.Color("#0c0c12")
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(6, 5, 8)
controls = addons.OrbitControls(camera, canvas)
controls.target.set(0, 1, 0)

# --- things to light -----------------------------------------------------
floor = THREE.Mesh(THREE.PlaneGeometry(14, 14), THREE.MeshStandardMaterial(color="#bbbbbb"))
floor.rotation.x = -math.pi / 2          # lay the plane flat
floor.receiveShadow = True
scene.add(floor)

ball = THREE.Mesh(THREE.SphereGeometry(1, 48, 24), THREE.MeshStandardMaterial(color="tomato", roughness=0.35))
ball.position.set(-1.6, 1, 0)
box = THREE.Mesh(THREE.BoxGeometry(1.5, 1.5, 1.5), THREE.MeshStandardMaterial(color="mediumseagreen"))
box.position.set(1.6, 0.75, 0.5)
knot = THREE.Mesh(THREE.TorusKnotGeometry(0.5, 0.17, 128, 16), THREE.MeshStandardMaterial(color="gold", metalness=0.5, roughness=0.3))
knot.position.set(0, 1.4, -2)
for thing in (ball, box, knot):
    thing.castShadow = True
    thing.receiveShadow = True
    scene.add(thing)

# --- the five lights -----------------------------------------------------
ambient = THREE.AmbientLight("white", 0.3)

hemi = THREE.HemisphereLight("lightskyblue", "saddlebrown", 1.0)

sun = THREE.DirectionalLight("white", 2.5)
sun.position.set(5, 8, 4)
sun.castShadow = True
sun.shadow.mapSize.width = 2048
sun.shadow.mapSize.height = 2048
for side, value in (("left", -8), ("right", 8), ("top", 8), ("bottom", -8)):
    setattr(sun.shadow.camera, side, value)

bulb = THREE.PointLight("orange", 25, 0)
bulb.castShadow = True
# a small glowing ball to show where the bulb is
bulb.add(THREE.Mesh(THREE.SphereGeometry(0.1, 16, 8), THREE.MeshBasicMaterial(color="orange")))

spot = THREE.SpotLight("deepskyblue", 80)
spot.position.set(-5, 6, 3)
spot.angle = 0.35
spot.penumbra = 0.5
spot.castShadow = True

lights = {"1": ambient, "2": hemi, "3": sun, "4": bulb, "5": spot}
names = {"1": "ambient", "2": "hemisphere", "3": "directional", "4": "point", "5": "spot"}
on = {"1": False, "2": True, "3": True, "4": True, "5": False}
for key, light in lights.items():
    light.visible = on[key]
    scene.add(light)

shadows = True

def on_key_down(key):
    global shadows
    if key in lights:
        on[key] = not on[key]
        lights[key].visible = on[key]
        print(names[key], "light", "on" if on[key] else "off")
    elif key == "s":
        shadows = not shadows
        for light in (sun, bulb, spot):
            light.castShadow = shadows
        print("shadows", "on" if shadows else "off")

print("Keys 1-5 switch the lights: ambient, hemisphere, directional, point, spot. s switches shadows.")

t = 0

def update(dt):
    global t
    t += dt
    # the bulb circles the scene, so you can watch its shadows move
    bulb.position.set(math.cos(t) * 3, 2.5, math.sin(t) * 3)
    knot.rotation.y += dt

def draw():
    controls.update()
    renderer.render(scene, camera)
```

Things to look for:

- **Only ambient (1)**: everything is flat, one shade per object.
- **Hemisphere (2)** gives tops a blue tint and undersides a brown one.
- **Directional (3)** gives the solid look, and the sharp shadows on the floor.
- **Point (4)** moves round the scene; watch its warm light and its shadows swing round with it.
- **Spot (5)** makes a soft-edged blue pool of light.

## Tips for good lighting

- Start with a hemisphere light and one directional light. Add more only when you want a particular effect.
- If a scene is too dark, raise the directional light's intensity before adding more lights.
- Coloured lights mix: a blue spot and an orange bulb on the same object make a warm and cool look that reads well.
- Light settings change live: `sun.intensity = 1` or `bulb.color.set("cyan")` in `update()` makes lights flicker, fade or change colour.

## Related

- [3D scenes](../3d.md)
- [Tutorial: a spinning cube](../tutorials/spinning-cube.md)
- Next: [a solar system](../tutorials/solar-system.md)
- [three.js documentation](https://threejs.org/docs/), for every option each light has
