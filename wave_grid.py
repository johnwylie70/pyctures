# Wave Grid: 225 cubes rising and falling like water.
# Try changing: n, the cubes along each side; 0.8, the height and the width of the waves.
#
# Run it:   pyctures run wave_grid.py

import math

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color("#0b0b14")
camera = THREE.PerspectiveCamera(45, width / height, 0.1, 100)
camera.position.set(0, 12, 18)
camera.lookAt(0, 0, 0)
scene.add(THREE.HemisphereLight("white", "#334", 2.5))

n = 15
cubes = []
for row in range(n):
    for col in range(n):
        cube = THREE.Mesh(THREE.BoxGeometry(0.6, 0.6, 0.6),
                          THREE.MeshStandardMaterial(color=f"hsl({(row + col) * 12}, 80%, 55%)"))
        cube.position.set(col - n / 2 + 0.5, 0, row - n / 2 + 0.5)
        scene.add(cube)
        cubes.append((cube, math.hypot(col - n / 2, row - n / 2)))

t = 0

def update(dt):
    global t
    t += dt

def draw():
    for cube, distance in cubes:
        cube.position.y = math.sin(distance * 0.8 - t * 3) * 0.8
    renderer.render(scene, camera)
