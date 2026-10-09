# A textured cube: a picture from a file, wrapped round a turning crate.
# Shows: THREE.TextureLoader().load() with a path beside the scene, and map= on a material.
# Drag to turn it.
#
# Run it:   pyctures run textured_cube.py
# Share it: pyctures build textured_cube.py -o site/   (textures/crate.png goes with it)

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color(0x1b2430)
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(0, 1.2, 4)
controls = addons.OrbitControls(camera, canvas)

texture = THREE.TextureLoader().load("textures/crate.png")
texture.colorSpace = THREE.SRGBColorSpace
crate = THREE.Mesh(THREE.BoxGeometry(1.6, 1.6, 1.6), THREE.MeshStandardMaterial(map=texture))
scene.add(crate)

light = THREE.DirectionalLight(0xffffff, 2.5)
light.position.set(3, 4, 5)
scene.add(light)
scene.add(THREE.AmbientLight(0xffffff, 0.6))

def draw():
    crate.rotation.y += 0.008
    crate.rotation.x = 0.35
    controls.update()
    renderer.render(scene, camera)
