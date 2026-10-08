# Brought across from JavaScript: the classic spinning cube from a three.js
# example, line for line in Python.
# Shows: new X() becomes X(), {color: ...} becomes color=..., and the
# animation loop becomes draw().
# See docs/from-javascript.md for the JavaScript it came from.
#
# Run it:   pyctures run from_javascript_3d.py
# Share it: pyctures build from_javascript_3d.py -o site/

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setSize(width, height, False)
scene = THREE.Scene()
camera = THREE.PerspectiveCamera(60, width / height, 0.1, 100)
camera.position.z = 4

cube = THREE.Mesh(THREE.BoxGeometry(1, 1, 1), THREE.MeshStandardMaterial(color=0x44aaff))
scene.add(cube)
light = THREE.DirectionalLight(0xffffff, 3)
light.position.set(2, 3, 4)
scene.add(light)
scene.add(THREE.AmbientLight(0xffffff, 0.3))

def draw():
    cube.rotation.x += 0.01
    cube.rotation.y += 0.015
    renderer.render(scene, camera)
