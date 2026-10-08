# A spinning knot, for the example web page. Drag to turn it.
renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)

scene = THREE.Scene()
scene.background = THREE.Color(0x101828)
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(0, 0, 6)
controls = addons.OrbitControls(camera, canvas)
controls.enableZoom = False      # so the page still scrolls over the scene

scene.add(THREE.HemisphereLight(0xffffff, 0x223344, 1.5))
light = THREE.DirectionalLight(0xffffff, 2.5)
light.position.set(3, 4, 5)
scene.add(light)

knot = THREE.Mesh(THREE.TorusKnotGeometry(1.2, 0.38, 200, 24),
                  THREE.MeshStandardMaterial(color=0xffb347, roughness=0.3, metalness=0.2))
scene.add(knot)

def update(dt):
    knot.rotation.x += 0.4 * dt
    knot.rotation.y += 0.6 * dt

def draw():
    controls.update()
    renderer.render(scene, camera)
