# A lit 3D scene: shapes on a floor, with a spotlight and shadows.
# Shows: materials, lights, shadows and orbit controls.
# Drag to orbit, pinch or scroll to zoom.
#
# Run it:   pyctures run lit_scene.py
# Share it: pyctures build lit_scene.py -o site/

import math

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
renderer.shadowMap.enabled = True

scene = THREE.Scene()
scene.background = THREE.Color(0x0e0e16)
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(4, 4, 7)
controls = addons.OrbitControls(camera, canvas)
controls.enableDamping = True

scene.add(THREE.AmbientLight(0x404050))
key = THREE.SpotLight(0xffffff, 60, 30, 0.5, 0.4)
key.position.set(3, 8, 4)
key.castShadow = True
scene.add(key)

floor = THREE.Mesh(THREE.CircleGeometry(6, 64), THREE.MeshStandardMaterial(color=0x2a2a3a))
floor.rotation.x = -math.pi / 2
floor.receiveShadow = True
scene.add(floor)

shapes = []
for i, (geo, colour) in enumerate([
    (THREE.BoxGeometry(1, 1, 1), 0xff6b6b),
    (THREE.SphereGeometry(0.6, 48, 24), 0x4dabf7),
    (THREE.TorusKnotGeometry(0.4, 0.15, 128, 16), 0xffd43b),
    (THREE.ConeGeometry(0.6, 1.2, 32), 0x69db7c),
]):
    mesh = THREE.Mesh(geo, THREE.MeshStandardMaterial(color=colour, roughness=0.35, metalness=0.1))
    a = i * math.tau / 4
    mesh.position.set(math.cos(a) * 2.2, 0.8, math.sin(a) * 2.2)
    mesh.castShadow = True
    scene.add(mesh)
    shapes.append(mesh)

def draw():
    for i, m in enumerate(shapes):
        m.rotation.y += 0.01 + i * 0.004
    controls.update()
    renderer.render(scene, camera)
