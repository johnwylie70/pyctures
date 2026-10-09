# Cube Spiral: 400 cubes in a rainbow spiral, turning.
import math, random

renderer = THREE.WebGLRenderer(canvas=canvas, antialias=True)
renderer.setPixelRatio(pixel_ratio)
renderer.setSize(width, height, False)
scene = THREE.Scene()
scene.background = THREE.Color("#101018")
camera = THREE.PerspectiveCamera(50, width / height, 0.1, 100)
camera.position.set(0, 5, 11)
camera.lookAt(0, 0, 0)
scene.add(THREE.HemisphereLight("white", "#223", 2))

# 400 cubes in one InstancedMesh
count = 400
cubes = THREE.InstancedMesh(THREE.BoxGeometry(0.25, 0.25, 0.25), THREE.MeshStandardMaterial(), count)
place = THREE.Matrix4()
for i in range(count):
    a = i * 0.25
    r = 1 + i * 0.01
    place.setPosition(r * math.cos(a), i * 0.008 - 1.6, r * math.sin(a))
    cubes.setMatrixAt(i, place)
    cubes.setColorAt(i, THREE.Color(f"hsl({i}, 80%, 60%)"))
cubes.instanceMatrix.needsUpdate = True
scene.add(cubes)

# a circle as a LineLoop, and a dashed line
circle = [THREE.Vector3(4 * math.cos(a / 20 * math.tau), -1.7, 4 * math.sin(a / 20 * math.tau)) for a in range(20)]
scene.add(THREE.LineLoop(THREE.BufferGeometry().setFromPoints(circle), THREE.LineBasicMaterial(color="white")))
dashed = THREE.Line(THREE.BufferGeometry().setFromPoints([THREE.Vector3(0, -1.7, 0), THREE.Vector3(0, 2.5, 0)]),
                    THREE.LineDashedMaterial(color="gold", dashSize=0.2, gapSize=0.1))
dashed.computeLineDistances()
scene.add(dashed)

# a label: a Sprite with a picture drawn on a 2D canvas
label = js.document.create_element("canvas")
label.width = 256
label.height = 64
pen = label.get_context("2d")
pen.fill_style = "white"
pen.font = "bold 40px sans-serif"
pen.text_align = "center"
pen.fill_text("400 cubes", 128, 46)
sign = THREE.Sprite(THREE.SpriteMaterial(map=THREE.CanvasTexture(label)))
sign.scale.set(2, 0.5, 1)
sign.position.y = 2.8
scene.add(sign)

def draw():
    cubes.rotation.y += 0.005
    renderer.render(scene, camera)
