# Torus Knot: one shape, lit, turning. Drag to look around it.
renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
camera = THREE.PerspectiveCamera(45, width / height, 0.1, 100)
camera.position.z = 8
controls = addons.OrbitControls(camera, canvas)

knot = THREE.Mesh(THREE.TorusKnotGeometry(1.6, 0.5, 200, 32, 3, 5),
                  THREE.MeshNormalMaterial())
scene.add(knot)

def draw():
    knot.rotation.x += 0.004
    knot.rotation.y += 0.007
    renderer.render(scene, camera)
