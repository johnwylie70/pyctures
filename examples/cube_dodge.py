# Cube Dodge: a 3D game.
# Shows: a three.js scene driven from Python, shadows, fog, and keyboard input.
# Move left and right with the arrow keys, or drag. Dodge the red blocks.
#
# Run it:   pyctures run cube_dodge.py
# Share it: pyctures build cube_dodge.py -o site/

import math, random

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
renderer.shadowMap.enabled = True

scene = THREE.Scene()
scene.background = THREE.Color(0x101828)
scene.fog = THREE.Fog(0x101828, 20, 60)
camera = THREE.PerspectiveCamera(60, width / height, 0.1, 100)
camera.position.set(0, 4, 9)
camera.lookAt(0, 0, -6)

scene.add(THREE.HemisphereLight(0xffffff, 0x334455, 1.2))
sun = THREE.DirectionalLight(0xffffff, 2.5)
sun.position.set(4, 10, 6)
sun.castShadow = True
scene.add(sun)

floor = THREE.Mesh(THREE.PlaneGeometry(12, 80), THREE.MeshStandardMaterial(color=0x22304a))
floor.rotation.x = -math.pi / 2
floor.position.z = -30
floor.receiveShadow = True
scene.add(floor)

player = THREE.Mesh(THREE.SphereGeometry(0.5, 32, 16), THREE.MeshStandardMaterial(color=0x44ddaa))
player.position.y = 0.5
player.castShadow = True
scene.add(player)

block_geo = THREE.BoxGeometry(1, 1, 1)
block_mat = THREE.MeshStandardMaterial(color=0xff5566)
blocks = []          # [mesh, x, z]
x = 0.0
score = 0.0
alive = True
spawn = 0.0

def new_block():
    mesh = THREE.Mesh(block_geo, block_mat)
    mesh.castShadow = True
    bx = random.choice([-4, -2, 0, 2, 4])
    mesh.position.set(bx, 0.5, -60)
    scene.add(mesh)
    blocks.append([mesh, bx, -60.0])

def restart():
    global x, score, alive
    for b in blocks:
        scene.remove(b[0])
    blocks.clear()
    x, score, alive = 0.0, 0.0, True

def update(dt):
    global x, score, alive, spawn
    if not alive:
        if " " in keys or mouse.down:
            restart()
        return
    if "ArrowLeft" in keys: x -= 8 * dt
    if "ArrowRight" in keys: x += 8 * dt
    if mouse.down:
        x += ((mouse.x / width - 0.5) * 10 - x) * 0.2
    x = max(-5, min(5, x))
    score += dt
    speed = 14 + score * 0.5
    spawn -= dt
    if spawn <= 0:
        spawn = max(0.25, 0.8 - score * 0.01)
        new_block()
    for b in blocks[:]:
        b[2] += speed * dt
        if b[2] > 10:
            scene.remove(b[0])
            blocks.remove(b)
        elif abs(b[2]) < 0.9 and abs(b[1] - x) < 0.9:
            alive = False

def draw():
    player.position.x = x
    player.rotation.x -= 0.15
    for mesh, bx, bz in blocks:
        mesh.position.z = bz
    renderer.render(scene, camera)

print("Dodge the red blocks. Your score is how long you last.")
