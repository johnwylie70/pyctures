# Tutorial: A Solar System

Full reference: [www.circuitry.dev/docs/pyctures/tutorials/solar-system](https://www.circuitry.dev/docs/pyctures/tutorials/solar-system) (in Circuitry Studio's help)

A glowing sun, planets going round it at different speeds, a moon going round one of the planets, and a sky full of stars. The trick that makes orbits easy is the **group**: put a planet in a group at the sun, move the planet out along the group's arm, and turning the group swings the planet round the sun.

## How an orbit works

```text
sun (in the middle)
└── orbit group  ← turn this
    └── planet   ← placed 4 units out along x
```

The planet never moves by itself. Its group turns, and it is carried round, like a ball on the end of a stick. A moon is one more level: a group inside the planet's group, at the planet's position, with the moon out on its own arm.

## The program

```python
import math, random

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)

scene = THREE.Scene()
scene.background = THREE.Color("black")
camera = THREE.PerspectiveCamera(55, width / height, 0.1, 500)
camera.position.set(0, 14, 24)
controls = addons.OrbitControls(camera, canvas)
controls.enableDamping = True

# --- the sun: glows by itself, and lights everything ---------------------
sun = THREE.Mesh(THREE.SphereGeometry(1.5, 48, 24), THREE.MeshBasicMaterial(color="gold"))
scene.add(sun)
scene.add(THREE.PointLight("white", 400, 0))     # a bulb at the sun's centre
scene.add(THREE.AmbientLight("white", 0.08))     # so night sides are not pure black

# --- planets ---------------------------------------------------------------
#          name      colour         size  distance  speed (turns a second)
planets_data = [
    ("Mercury", "darkgray",       0.25,  3.0,  0.40),
    ("Venus",   "navajowhite",    0.45,  4.5,  0.25),
    ("Earth",   "royalblue",      0.5,   6.5,  0.16),
    ("Mars",    "orangered",      0.35,  8.5,  0.11),
    ("Jupiter", "sandybrown",     1.1,  12.0,  0.05),
]

orbits = []     # (group, speed) pairs to turn each frame
earth = None

for name, colour, size, distance, speed in planets_data:
    orbit = THREE.Group()
    orbit.rotation.y = random.uniform(0, math.tau)      # start somewhere along the orbit
    scene.add(orbit)

    planet = THREE.Mesh(THREE.SphereGeometry(size, 32, 16), THREE.MeshStandardMaterial(color=colour, roughness=0.8))
    planet.position.x = distance
    orbit.add(planet)
    orbits.append((orbit, speed))

    # a faint ring to show the path
    path = THREE.Mesh(
        THREE.RingGeometry(distance - 0.02, distance + 0.02, 128),
        THREE.MeshBasicMaterial(color="#333", side=THREE.DoubleSide),
    )
    path.rotation.x = -math.pi / 2
    scene.add(path)

    if name == "Earth":
        earth = planet

# --- a moon going round the Earth ---------------------------------------
moon_orbit = THREE.Group()
earth.add(moon_orbit)                  # the moon's group rides along with the Earth
moon = THREE.Mesh(THREE.SphereGeometry(0.14, 16, 8), THREE.MeshStandardMaterial(color="lightgray"))
moon.position.x = 0.9
moon_orbit.add(moon)

# --- stars: a few thousand points far away ---------------------------------
positions = []
for _ in range(2000):
    # a random direction, 80 to 150 units away
    theta = random.uniform(0, math.tau)
    phi = math.acos(random.uniform(-1, 1))
    r = random.uniform(80, 150)
    positions += [r * math.sin(phi) * math.cos(theta), r * math.cos(phi), r * math.sin(phi) * math.sin(theta)]
stars_geometry = THREE.BufferGeometry()
stars_geometry.setAttribute("position", THREE.Float32BufferAttribute(positions, 3))
scene.add(THREE.Points(stars_geometry, THREE.PointsMaterial(color="white", size=0.4)))

# --- every frame ---------------------------------------------------------
speed_up = 1.0

def on_key_down(key):
    global speed_up
    if key == "ArrowUp":
        speed_up *= 2
    elif key == "ArrowDown":
        speed_up /= 2

def update(dt):
    for orbit, speed in orbits:
        orbit.rotation.y += speed * math.tau * dt * speed_up / 4
    moon_orbit.rotation.y += 2 * dt * speed_up
    earth.rotation.y += 3 * dt * speed_up          # the Earth spins on its own axis too
    sun.rotation.y += 0.1 * dt

def draw():
    controls.update()
    renderer.render(scene, camera)
```

Drag to look around, pinch or scroll to zoom in, and press the up and down arrows (after clicking the canvas) to speed time up or slow it down.

## What each part does

- **The sun** uses `MeshBasicMaterial`, which ignores light, so it always looks lit. The `PointLight` at the centre is what lights the planets, so each planet's sun-facing side is bright and its far side is dark. See [lighting a scene](../tutorials/lighting.md).
- **Each planet** sits `distance` units out along its own group's x axis. Turning the group (`orbit.rotation.y`) carries it round. Different speeds give different years.
- **The moon's group is added to the Earth**, so it goes wherever the Earth goes, and turns on its own as well.
- **The paths** are very thin flat rings (`RingGeometry`), laid flat by turning them a quarter turn about x.
- **The stars** are one `Points` object with 2,000 positions, placed on a big shell around everything.

The sizes and distances are chosen to fit on screen, not to scale: at true scale the planets would be too small to see.

## Try this

- Add Saturn with a ring: a `RingGeometry(1.4, 2.2, 64)` added to the planet, tilted a little with `rotation.x`.
- Tilt an orbit: set `orbit.rotation.z = 0.1` so the planet goes slightly above and below the others.
- Give Mars two small moons, each in its own group with its own speed.

## Related

- [3D scenes: groups](../3d.md#groups)
- [Tutorial: lighting a scene](../tutorials/lighting.md)
- Next: [a live chart](../tutorials/live-chart.md)
