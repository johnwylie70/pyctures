"""pyvisualfx: effects for a Pyctures scene. Draw some shapes, then turn one on.

    from pyctures import *
    from pyvisualfx import *

    kaleidoscope(8)                              # on, eight segments
    glow(0.8)                                    # bright things shine
    trail = trails(0.5, zoom=1.5, spin=20)

    def update(dt):
        trail.spin = 40                          # a setting is a plain attribute: change it any time

EFFECTS APPLY IN THE ORDER THEY ARE TURNED ON, to everything the scene has
drawn, 2D or 3D. Each has ``off()``, ``on()`` and ``remove()``, and ``amount``
(0 to 1: how much of it is mixed in). ``clear_effects()`` takes them all away.
``look("dream")`` is several at once.

THE PAGE'S GRAPHICS CARD DOES THE WORK. Python never touches the page (it may be
in a worker, or on another computer). Each function here sends ONE command that
turns the effect on in the page, from ``web/visualfx.js`` (the very file that is the
JavaScript library; a Pyctures that has it built in says so with ``H_EFFECTS``,
and then this module reads no other file), and Python keeps a small object that
stands for it. Setting an attribute is one command more. The effects are run
once for each frame Python sends, straight after its drawing, on Python's clock:
so a scene recorded a frame at a time gives exactly the frames it should.

MUSIC: ``listen_to(sound_output())`` (or a synth: anything that makes sound in
the page), then ``react(shine, "strength", "bass", 0.3, 1.2)`` ties a setting
to the bass, the mids, the highs, the loudness or the pulse of a beat. That
is done in the page, on the beat, with no trip through Python. ``bass()``,
``mids()``, ``highs()``, ``loudness()`` and ``pulse()`` are the same numbers for
your own drawing, as the page last told them: a frame late.

YOUR OWN: ``shader("vec4 effect(vec2 uv) { return texture(picture, uv).bgra; }")``.

The effects, their settings and their ranges are those of the JavaScript library,
written into this file by ``scripts/sync_js.py``: this module is one file.

MIT licence.
"""
import json
import os
import re
import sys

__version__ = "0.0.0"

_HERE = os.path.dirname(os.path.abspath(__file__))
# Every effect, its settings and their ranges, as the JavaScript library has them. Written by
# scripts/sync_js.py (which runs that library and asks it): do not edit it by hand.
# EFFECTS:BEGIN
_TABLE = json.loads(r"""{"effects":{
"kaleidoscope":{"order":["segments"],"settings":{"segments":{"kind":"int","default":8,"min":2,"max":32},"angle":{"kind":"float","default":0,"min":-360,"max":360,"unit":"degrees"},"zoom":{"kind":"float","default":1,"min":0.2,"max":5},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"One slice of the picture, folded round and round. The slice starts at the middle and points right: turn it with angle."},
"mirror":{"order":["side"],"settings":{"side":{"kind":"choice","default":"left","choices":["left","right","top","bottom","four"]},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"One half of the picture shown on both sides, or one quarter in all four."},
"pixelate":{"order":["size"],"settings":{"size":{"kind":"float","default":10,"min":1,"max":100},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"Big square pixels."},
"waves":{"order":["size"],"settings":{"size":{"kind":"float","default":12,"min":0,"max":100},"length":{"kind":"float","default":160,"min":10,"max":1000},"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The picture ripples like a flag in the wind."},
"ripple":{"order":["size"],"settings":{"size":{"kind":"float","default":8,"min":0,"max":100},"length":{"kind":"float","default":60,"min":10,"max":1000},"speed":{"kind":"float","default":1,"min":-5,"max":5},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"Rings spreading from a point, as from a stone dropped in water."},
"wobble":{"order":["size"],"settings":{"size":{"kind":"float","default":14,"min":0,"max":100},"scale":{"kind":"float","default":120,"min":10,"max":1000},"speed":{"kind":"float","default":0.4,"min":-5,"max":5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The picture wobbles like jelly, or something seen under water."},
"swirl":{"order":["angle"],"settings":{"angle":{"kind":"float","default":180,"min":-1440,"max":1440,"unit":"degrees"},"radius":{"kind":"float","default":0,"min":0,"max":2000},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The middle of the picture twisted round, like stirred paint."},
"fisheye":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":-1,"max":1},"radius":{"kind":"float","default":0,"min":0,"max":2000},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"A bulge, as through a round lens. Below zero it pinches instead."},
"tunnel":{"order":["speed"],"settings":{"speed":{"kind":"float","default":0.4,"min":-5,"max":5},"repeat":{"kind":"int","default":2,"min":1,"max":12},"depth":{"kind":"float","default":0.5,"min":0.05,"max":4},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The picture becomes the walls of a tunnel you are flying down."},
"tile":{"order":["across"],"settings":{"across":{"kind":"int","default":3,"min":1,"max":40},"down":{"kind":"int","default":0,"min":0,"max":40},"flip":{"kind":"bool","default":false,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The picture repeated in rows and columns."},
"zoomBlur":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.25,"min":0,"max":1},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Blur and light","about":"Rushing towards a point."},
"spinBlur":{"order":["angle"],"settings":{"angle":{"kind":"float","default":8,"min":-90,"max":90,"unit":"degrees"},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Blur and light","about":"Spinning round a point."},
"rgbSplit":{"order":["size"],"settings":{"size":{"kind":"float","default":4,"min":0,"max":60},"angle":{"kind":"float","default":0,"min":-360,"max":360,"unit":"degrees"},"spread":{"kind":"bool","default":false,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Red and blue pulled apart, like a cheap lens or a bad signal."},
"hue":{"order":["shift"],"settings":{"shift":{"kind":"float","default":90,"min":-360,"max":360,"unit":"degrees"},"speed":{"kind":"float","default":0,"min":-720,"max":720},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Every colour moved round the colour wheel. With speed, the colours keep turning."},
"saturate":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1.6,"min":0,"max":4},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"More colour, or less: at 0 the picture is grey."},
"brighten":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1.3,"min":0,"max":4},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Brighter, or darker below 1."},
"contrast":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1.4,"min":0,"max":4},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Lights lighter and darks darker."},
"invert":{"order":[],"settings":{"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"A negative: every colour swapped for its opposite."},
"posterize":{"order":["levels"],"settings":{"levels":{"kind":"int","default":4,"min":2,"max":16},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Only a few shades of each colour, like a poster."},
"tint":{"order":["colour"],"settings":{"colour":{"kind":"colour","default":"gold"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Seen through coloured glass."},
"duotone":{"order":["dark","light"],"settings":{"dark":{"kind":"colour","default":"midnightblue"},"light":{"kind":"colour","default":"gold"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Two colours only: one for the dark parts and one for the light."},
"colourCycle":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"rainbow"},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"bands":{"kind":"float","default":1,"min":0.1,"max":8},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Brightness becomes a colour from a palette, and the colours move round."},
"scanlines":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":0,"max":1},"size":{"kind":"float","default":3,"min":1,"max":40},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Screens and old computers","about":"Dark lines across the picture, as on an old screen."},
"crt":{"order":["curve"],"settings":{"curve":{"kind":"float","default":0.18,"min":0,"max":1},"lines":{"kind":"float","default":0.45,"min":0,"max":1},"size":{"kind":"float","default":3,"min":1,"max":40},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Screens and old computers","about":"An old television: curved glass, lines, and thin stripes of red, green and blue."},
"glitch":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":0,"max":1},"speed":{"kind":"float","default":1,"min":0,"max":10},"seed":{"kind":"int","default":1,"min":0,"max":9999},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Screens and old computers","about":"A broken signal: blocks that jump sideways, a line that tears, a band of snow."},
"grain":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.18,"min":0,"max":1},"size":{"kind":"float","default":1.5,"min":0.5,"max":20},"seed":{"kind":"int","default":1,"min":0,"max":9999},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"The fine speckle of film."},
"vignette":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":1},"size":{"kind":"float","default":0.75,"min":0,"max":2},"colour":{"kind":"colour","default":"black"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"Dark corners, which draw the eye to the middle."},
"edges":{"order":["strength"],"settings":{"strength":{"kind":"float","default":2,"min":0,"max":10},"size":{"kind":"float","default":1.5,"min":0.5,"max":20},"fill":{"kind":"float","default":0,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"Only the outlines, each in its own colour."},
"dots":{"order":["size"],"settings":{"size":{"kind":"float","default":9,"min":2,"max":100},"angle":{"kind":"float","default":25,"min":-360,"max":360,"unit":"degrees"},"paper":{"kind":"colour","default":"black"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"Printed in dots, big where the picture is bright, as a comic or a newspaper is."},
"letters":{"order":["size"],"settings":{"size":{"kind":"float","default":10,"min":4,"max":100},"colour":{"kind":"colour","default":"white"},"own":{"kind":"bool","default":true,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Screens and old computers","about":"The picture made of marks, as an old terminal would show it."},
"plasma":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"sunset"},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"scale":{"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Slow rolling colour."},
"starfield":{"order":["speed"],"settings":{"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"stars":{"kind":"float","default":1,"min":0,"max":4},"colour":{"kind":"colour","default":"white"},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Flying through stars."},
"metaballs":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"neon"},"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"count":{"kind":"int","default":7,"min":1,"max":12},"size":{"kind":"float","default":1,"min":0.2,"max":4},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Blobs that melt into each other when they meet: a lava lamp."},
"flow":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"ocean"},"speed":{"kind":"float","default":0.2,"min":-5,"max":5},"scale":{"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Colour that folds and curls like ink in water."},
"droste":{"order":["zoom"],"settings":{"zoom":{"kind":"float","default":3,"min":1.2,"max":10},"twist":{"kind":"int","default":1,"min":0,"max":4},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The picture inside itself, smaller each time, for ever. With a twist it winds in as a spiral."},
"rotozoom":{"order":["speed"],"settings":{"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"zoom":{"kind":"float","default":1.5,"min":0.2,"max":8},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The picture tiled, turning and zooming: an old demo-scene favourite."},
"hexagons":{"order":["size"],"settings":{"size":{"kind":"float","default":14,"min":3,"max":100},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"Six-sided pixels, like a honeycomb."},
"glassTiles":{"order":["size"],"settings":{"size":{"kind":"float","default":40,"min":6,"max":300},"strength":{"kind":"float","default":0.4,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"Seen through a wall of glass blocks."},
"frosted":{"order":["size"],"settings":{"size":{"kind":"float","default":6,"min":0,"max":60},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"Seen through frosted glass."},
"heatHaze":{"order":["size"],"settings":{"size":{"kind":"float","default":5,"min":0,"max":60},"scale":{"kind":"float","default":40,"min":5,"max":400},"speed":{"kind":"float","default":1,"min":-5,"max":5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The shimmer of hot air rising."},
"caustics":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":0,"max":2},"scale":{"kind":"float","default":120,"min":20,"max":600},"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"colour":{"kind":"colour","default":"#bfe8ff"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The net of bright lines that sunlight makes on the floor of a pool."},
"shake":{"order":["strength"],"settings":{"strength":{"kind":"float","default":10,"min":0,"max":200},"speed":{"kind":"float","default":25,"min":1,"max":100},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"The whole picture shakes. Set strength when something hits, and let it fall away."},
"punch":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.15,"min":-0.9,"max":4},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Shapes of the picture","about":"A zoom in towards a point. Tie its strength to the beat."},
"motionBlur":{"order":["size"],"settings":{"size":{"kind":"float","default":24,"min":0,"max":300},"angle":{"kind":"float","default":0,"min":-360,"max":360,"unit":"degrees"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"some","feedback":false,"group":"Blur and light","about":"Moving fast in one direction."},
"tiltShift":{"order":["strength"],"settings":{"strength":{"kind":"float","default":8,"min":0,"max":60},"size":{"kind":"float","default":70,"min":5,"max":1000},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"some","feedback":false,"group":"Blur and light","about":"A band in focus and the rest blurred, which makes a scene look like a tiny model."},
"lightRays":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.7,"min":0,"max":3},"size":{"kind":"float","default":0.6,"min":0,"max":1},"threshold":{"kind":"float","default":0.6,"min":0,"max":1},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"some","feedback":false,"group":"Blur and light","about":"Rays of light streaming out from a point, through whatever is bright."},
"streaks":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":3},"size":{"kind":"float","default":120,"min":0,"max":800},"threshold":{"kind":"float","default":0.6,"min":0,"max":1},"colour":{"kind":"colour","default":"#88aaff"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"some","feedback":false,"group":"Blur and light","about":"Long sideways flares from bright lights, as a film camera makes."},
"softFocus":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":1},"size":{"kind":"float","default":6,"min":0,"max":60},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Blur and light","about":"A soft, dreamy haze over the bright parts."},
"smear":{"order":["length"],"settings":{"length":{"kind":"float","default":3,"min":0,"max":30},"size":{"kind":"float","default":40,"min":0,"max":400},"scale":{"kind":"float","default":150,"min":20,"max":1000},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":true,"group":"What was drawn stays","about":"What was drawn is carried away on a slow current, like wet paint."},
"stutter":{"order":["speed"],"settings":{"speed":{"kind":"float","default":8,"min":0.5,"max":60},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":true,"group":"What was drawn stays","about":"Only so many new pictures a second: the last one is held between them."},
"gradientMap":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"sunset"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Brightness becomes a colour from a palette, dark to light."},
"thermal":{"order":[],"settings":{"palette":{"kind":"palette","default":"thermal"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"A heat camera: cold is dark blue, hot is yellow and white."},
"nightVision":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1.6,"min":0,"max":6},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Green, grainy and bright in the dark, like a night-vision scope."},
"sepia":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"The warm brown of an old photograph."},
"threshold":{"order":["level"],"settings":{"level":{"kind":"float","default":0.5,"min":0,"max":1},"dark":{"kind":"colour","default":"black"},"light":{"kind":"colour","default":"white"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Two colours and nothing between: dark or light."},
"solarize":{"order":["level"],"settings":{"level":{"kind":"float","default":0.5,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"The bright parts turned to their opposite, as in an over-exposed photograph."},
"colourBleed":{"order":["size"],"settings":{"size":{"kind":"float","default":10,"min":0,"max":100},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Colours smeared sideways, as on old videotape."},
"rainbowEdges":{"order":["strength"],"settings":{"strength":{"kind":"float","default":2,"min":0,"max":10},"size":{"kind":"float","default":1.5,"min":0.5,"max":20},"speed":{"kind":"float","default":0.1,"min":-5,"max":5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Colours","about":"Every edge in the picture drawn in rainbow colours."},
"dither":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"gameboy"},"size":{"kind":"float","default":2,"min":1,"max":40},"strength":{"kind":"float","default":0.35,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Screens and old computers","about":"A few colours made to pass for many with a pattern of dots, as old computers did."},
"interlace":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":1},"size":{"kind":"float","default":2,"min":1,"max":20},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Screens and old computers","about":"Every other line dark, swapping each frame, like old video."},
"led":{"order":["size"],"settings":{"size":{"kind":"float","default":8,"min":3,"max":80},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Screens and old computers","about":"A wall of round lamps."},
"emboss":{"order":["strength"],"settings":{"strength":{"kind":"float","default":2,"min":0,"max":10},"angle":{"kind":"float","default":135,"min":-360,"max":360,"unit":"degrees"},"size":{"kind":"float","default":1.5,"min":0.5,"max":20},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"Pressed into grey metal: only the bumps and hollows show."},
"sharpen":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1,"min":0,"max":5},"size":{"kind":"float","default":1,"min":0.5,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"Crisper edges."},
"sketch":{"order":["strength"],"settings":{"strength":{"kind":"float","default":3,"min":0,"max":10},"size":{"kind":"float","default":1.2,"min":0.5,"max":20},"paper":{"kind":"colour","default":"#f4efe2"},"colour":{"kind":"colour","default":"#2a2a33"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"A pencil drawing on paper."},
"cartoon":{"order":["levels"],"settings":{"levels":{"kind":"int","default":4,"min":2,"max":12},"strength":{"kind":"float","default":2.5,"min":0,"max":10},"size":{"kind":"float","default":1.5,"min":0.5,"max":20},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"Flat colours and black outlines."},
"stainedGlass":{"order":["size"],"settings":{"size":{"kind":"float","default":40,"min":8,"max":400},"colour":{"kind":"colour","default":"#101010"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"Pieces of coloured glass with dark lead between them."},
"crosshatch":{"order":["size"],"settings":{"size":{"kind":"float","default":6,"min":2,"max":60},"colour":{"kind":"colour","default":"#1a1a22"},"paper":{"kind":"colour","default":"#f6f2e8"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"Drawn, printed and painted","about":"Shaded with crossing pen lines: more lines where it is darker."},
"oil":{"order":["size"],"settings":{"size":{"kind":"float","default":4,"min":1,"max":30},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"heavy","feedback":false,"group":"Drawn, printed and painted","about":"Smoothed into patches of colour, like oil paint. Heavy: it looks at 36 places for every pixel."},
"dust":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":0,"max":1},"seed":{"kind":"int","default":1,"min":0,"max":9999},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"Specks and scratches, as on old film."},
"lightLeaks":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":2},"speed":{"kind":"float","default":0.2,"min":-5,"max":5},"colour":{"kind":"colour","default":"#ff7a2a"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"Warm light creeping in from the sides, as in an old camera."},
"rain":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":2},"speed":{"kind":"float","default":1,"min":0,"max":5},"angle":{"kind":"float","default":12,"min":-80,"max":80,"unit":"degrees"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"Rain falling in front of the picture."},
"snow":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.8,"min":0,"max":2},"speed":{"kind":"float","default":1,"min":0,"max":5},"size":{"kind":"float","default":3,"min":0.5,"max":20},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"Snow falling in front of the picture."},
"bokeh":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":0,"max":2},"size":{"kind":"float","default":30,"min":4,"max":200},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"Soft discs of coloured light drifting by: lamps out of focus."},
"fog":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":1},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"scale":{"kind":"float","default":220,"min":20,"max":2000},"colour":{"kind":"colour","default":"#dfe6ee"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"Drifting mist, thicker towards the bottom."},
"lightning":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1,"min":0,"max":3},"speed":{"kind":"float","default":1,"min":0,"max":10},"seed":{"kind":"int","default":1,"min":0,"max":9999},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"In front of the picture","about":"A flash, now and then."},
"warp":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"neon"},"speed":{"kind":"float","default":1,"min":-10,"max":10},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"A chequered tunnel rushing past."},
"voronoi":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"candy"},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"scale":{"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Soft coloured cells that slowly shift."},
"moire":{"order":["colour"],"settings":{"colour":{"kind":"colour","default":"white"},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"scale":{"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Two sets of rings crossing, making patterns neither has alone."},
"interference":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"ocean"},"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"scale":{"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Waves from four moving points, crossing."},
"aurora":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"aurora"},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"The northern lights over a night sky."},
"fire":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"fire"},"speed":{"kind":"float","default":1,"min":-5,"max":5},"scale":{"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Flames rising from the bottom of the picture."},
"clouds":{"order":["colour"],"settings":{"colour":{"kind":"colour","default":"#3a8fdc"},"speed":{"kind":"float","default":0.1,"min":-5,"max":5},"scale":{"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"A sky with drifting clouds."},
"matrixRain":{"order":["colour"],"settings":{"colour":{"kind":"colour","default":"#3dff7a"},"speed":{"kind":"float","default":1,"min":0,"max":10},"size":{"kind":"float","default":14,"min":6,"max":80},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Green marks falling in columns."},
"copperBars":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"rainbow"},"count":{"kind":"int","default":5,"min":1,"max":8},"speed":{"kind":"float","default":1,"min":-5,"max":5},"size":{"kind":"float","default":34,"min":4,"max":300},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"Shining bars sliding up and down: a demo-scene classic."},
"checkerFloor":{"order":["colour"],"settings":{"colour":{"kind":"colour","default":"#ff2a6d"},"dark":{"kind":"colour","default":"#101a3a"},"speed":{"kind":"float","default":1,"min":-10,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"A chequered floor rushing towards you under a glowing horizon."},
"twister":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"candy"},"speed":{"kind":"float","default":1,"min":-5,"max":5},"size":{"kind":"float","default":0.22,"min":0.02,"max":0.5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"Backdrops that need no drawing","about":"A twisting four-sided bar, another demo-scene classic."},
"spectrumBars":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"rainbow"},"count":{"kind":"int","default":32,"min":4,"max":64},"size":{"kind":"float","default":0.7,"min":0.05,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"The music, drawn","about":"The music as bars: low notes at the left, high at the right."},
"spectrumRing":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"rainbow"},"size":{"kind":"float","default":90,"min":10,"max":1000},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"The music, drawn","about":"The music as bars round a ring."},
"waveformRing":{"order":["colour"],"settings":{"colour":{"kind":"colour","default":"white"},"size":{"kind":"float","default":110,"min":10,"max":1000},"strength":{"kind":"float","default":3,"min":0.5,"max":40},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true,"cost":"light","feedback":false,"group":"The music, drawn","about":"The sound's own wave, bent into a ring."},
"beatFlash":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":0,"max":2},"colour":{"kind":"colour","default":"white"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"The music, drawn","about":"A flash of colour on each beat."},
"bassShake":{"order":["strength"],"settings":{"strength":{"kind":"float","default":14,"min":0,"max":200},"speed":{"kind":"float","default":25,"min":1,"max":100},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"light","feedback":false,"group":"The music, drawn","about":"The picture shakes with the bass."},
"blur":{"order":["radius"],"settings":{"radius":{"kind":"float","default":8,"min":0,"max":200},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"some","feedback":false,"group":"Blur and light","about":"Out of focus."},
"glow":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.8,"min":0,"max":4},"threshold":{"kind":"float","default":0.5,"min":0,"max":1},"radius":{"kind":"float","default":24,"min":2,"max":200},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"some","feedback":false,"group":"Blur and light","about":"Bright things shine and spread light around them."},
"trails":{"order":["length"],"settings":{"length":{"kind":"float","default":0.5,"min":0,"max":20,"unit":"s"},"zoom":{"kind":"float","default":1,"min":0.1,"max":10},"spin":{"kind":"float","default":0,"min":-720,"max":720,"unit":"degrees"},"hue":{"kind":"float","default":0,"min":-720,"max":720,"unit":"degrees"},"dx":{"kind":"float","default":0,"min":-2000,"max":2000},"dy":{"kind":"float","default":0,"min":-2000,"max":2000},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false,"cost":"some","feedback":true,"group":"What was drawn stays","about":"What was drawn stays and fades. With zoom, spin and hue it becomes the classic screensaver tunnel."}
},
"groups":["Shapes of the picture","Blur and light","What was drawn stays","Colours","Screens and old computers","Drawn, printed and painted","In front of the picture","Backdrops that need no drawing","The music, drawn","More"],
"looks":["dream","arcade","vhs","neon","comic","underwater","oldfilm","disco","gameboy","c64","noir","comicbook","storm","winter","cinema","terminal"],
"recipes":{"dream":[["glow",{"strength":1,"threshold":0.35,"radius":40}],["saturate",{"strength":1.3}],["vignette",{"strength":0.5}]],"arcade":[["glow",{"strength":0.7,"threshold":0.4,"radius":20}],["crt",{"curve":0.2,"lines":0.5}]],"vhs":[["saturate",{"strength":1.35}],["rgbSplit",{"size":3}],["glitch",{"strength":0.35}],["scanlines",{"strength":0.3,"size":4}],["grain",{"strength":0.2,"size":2}],["vignette",{"strength":0.45}]],"neon":[["edges",{"strength":3,"fill":0.15}],["glow",{"strength":1.4,"threshold":0.2,"radius":28}]],"comic":[["posterize",{"levels":4}],["dots",{"size":7}]],"underwater":[["wobble",{"size":10,"scale":160}],["tint",{"colour":"#7fd4ff"}],["glow",{"strength":0.5,"threshold":0.5}],["vignette",{"strength":0.6,"colour":"#001830"}]],"oldfilm":[["duotone",{"dark":"#1a1208","light":"#f2e2c0"}],["grain",{"strength":0.3,"size":2}],["vignette",{"strength":0.75}]],"disco":[["kaleidoscope",{"segments":10}],["hue",{"shift":0,"speed":60}],["glow",{"strength":0.8}]],"gameboy":[["dither",{"palette":"gameboy","size":3}]],"c64":[["dither",{"palette":"c64","size":3}],["scanlines",{"strength":0.2,"size":3}]],"noir":[["saturate",{"strength":0}],["contrast",{"strength":1.6}],["grain",{"strength":0.25,"size":2}],["vignette",{"strength":0.8}]],"comicbook":[["cartoon",{"levels":4}],["dots",{"size":5,"paper":"#101018"}]],"storm":[["rain",{"strength":0.7}],["lightning",{}],["fog",{"strength":0.35,"colour":"#8a94a8"}],["vignette",{"strength":0.6}]],"winter":[["tint",{"colour":"#cfe4ff"}],["snow",{}],["softFocus",{"strength":0.4}],["vignette",{"strength":0.4,"colour":"#0a1830"}]],"cinema":[["streaks",{"strength":0.5}],["tiltShift",{"strength":5}],["grain",{"strength":0.1}],["vignette",{"strength":0.5}]],"terminal":[["letters",{"size":9,"own":false,"colour":"#3dff7a"}],["glow",{"strength":0.6,"threshold":0.2,"radius":14}],["scanlines",{"strength":0.25}]]},
"lookAbout":{"dream":"Soft, glowing and rich.","arcade":"The curved glass of an old arcade machine.","vhs":"A worn videotape.","neon":"Glowing outlines in the dark.","comic":"A few flat colours, printed in dots.","underwater":"Blue, wobbling and dim at the edges.","oldfilm":"Brown, grainy and dark at the corners.","disco":"A kaleidoscope whose colours keep turning.","gameboy":"Four shades of green.","c64":"The colours of a 1980s home computer.","noir":"Black and white, high contrast, grainy.","comicbook":"Black outlines over printed dots.","storm":"Rain, lightning and fog.","winter":"Cold light and falling snow.","cinema":"A film camera: flares, a narrow focus, grain.","terminal":"Green marks on a dark screen."},
"palettes":["rainbow","fire","ocean","sunset","neon","candy","forest","ice","lava","mono","thermal","aurora","gameboy","c64","amiga","pico"],
"paletteColours":{"rainbow":["#ff2a2a","#ffd92a","#3cff5a","#2ad4ff","#5a3cff","#ff2ad4"],"fire":["#000000","#5a0a00","#d43a00","#ff9a1a","#ffe98a","#5a0a00"],"ocean":["#02102a","#0a3a7a","#1a8ad4","#6ae0e0","#e8fff8","#0a3a7a"],"sunset":["#1a0a3a","#6a1a7a","#e0407a","#ff8a3a","#ffd86a","#6a1a7a"],"neon":["#0a001a","#ff1ad9","#1affea","#f6ff1a","#7a1aff","#1affea"],"candy":["#ff8ad4","#ffd0e8","#8ad4ff","#b8ffd0","#fff0a0","#d0a0ff"],"forest":["#04140a","#0e4a22","#3a8a2a","#a8d44a","#f0f0a0","#0e4a22"],"ice":["#020818","#103a6a","#4a9ae0","#b8e8ff","#ffffff","#4a9ae0"],"lava":["#1a0000","#8a0a00","#ff3a00","#ff9a00","#ffe27a","#ff5a00"],"mono":["#000000","#ffffff"],"thermal":["#000000","#20008c","#cc0077","#ff3000","#ffd000","#ffffff"],"aurora":["#00ff9a","#00b0ff","#8a2be2","#00ff9a"],"gameboy":["#0f380f","#306230","#8bac0f","#9bbc0f"],"c64":["#000000","#352879","#6c5eb5","#9a6759","#b8c76f","#ffffff"],"amiga":["#000022","#0055aa","#ff8800","#ffffff"],"pico":["#1d2b53","#7e2553","#ff004d","#ffa300","#29adff","#fff1e8"]},
"aliases":{"bloom":"glow","colorCycle":"colourCycle","bulge":"fisheye","halftone":"dots","colorBleed":"colourBleed","godRays":"lightRays"}}""")
# EFFECTS:END
_EFFECTS = _TABLE["effects"]
_source = [None]


def _snake(name):
    return re.sub(r"[A-Z]", lambda m: "_" + m.group(0).lower(), name)


def _camel(name):
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), name)


# Python's spelling of a setting: colour or color, and `from_` where a word is Python's own.
_SPELLING = {"color": "colour", "colors": "colours"}


def _key(name):
    name = _camel(name.rstrip("_"))
    return _SPELLING.get(name, name)


def _library():
    """The page's half as text that can be made into a function: a page is given no file to load."""
    if _source[0] is None:
        with open(os.path.join(_HERE, "web", "visualfx.js"), encoding="utf-8") as f:
            _source[0] = f.read().replace("export {", "return {")
    return _source[0]


class _Run:
    """One run of a scene: its page, and the effects made in it."""

    def __init__(self, js=None):
        self.js = js
        self.api = None
        self.next_id = 1
        self.bands = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.hearing = False
        self.dt = None


_run = _Run()


def _pyctures():
    # Looked up each time: in a browser every scene has its own copy of the module.
    module = sys.modules.get("pyctures")
    if module is None:
        import pyctures as module
    return module


def _page():
    """The page's effects for the scene that is running, made the first time one is wanted."""
    global _run
    p = _pyctures()
    # A new run has a new `js`: what was made for the last run is gone with its page.
    if _run.js is not p.js:
        _run = _Run(p.js)
        handle = getattr(p, "H_EFFECTS", None)
        if handle is not None:
            _run.api = p.JsRef(handle)      # a Pyctures that has the effects built in
        else:
            lib = p.js.Function(_library())()
            _run.api = lib.effects(p.canvas, {"fresh": True, "manual": True})
        # The effects are run once for every frame Python sends, after its drawing, on Python's clock.
        ending = getattr(getattr(p, "S", None), "ending", None)
        if isinstance(ending, list):
            ending.append(_frame)
        _watch_dt(p)
    return _run.api


def _watch_dt(p):
    """The seconds each frame is given (what update(dt) is told). A Pyctures that keeps it says so with S.dt;
    one that does not is listened to where it hands dt to the scene's functions."""
    call = getattr(p, "_call_frame_functions", None)
    if hasattr(getattr(p, "S", None), "dt") or call is None or getattr(call, "_visualfx", False):
        return

    def frame_functions(dt):
        _run.dt = dt
        return call(dt)
    frame_functions._visualfx = True
    p._call_frame_functions = frame_functions


def _frame():
    """As a frame is sent: the last command in it runs the effects over what the frame drew."""
    p = _pyctures()
    if _run.js is not p.js or _run.api is None:
        return
    dt = getattr(p.S, "dt", None)
    if not isinstance(dt, (int, float)):
        dt = _run.dt
    # A frame that is not one of the clock's (the page asked for a picture again) moves nothing on.
    _run.dt = None
    # What a file draws as it starts is a frame too, given no time (dt is 0): the effects are run on it, and nothing moves on.
    if isinstance(dt, (int, float)) and dt >= 0:
        _run.api.frame(dt)


def _told(e):
    """What the page reports with a frame: the music's five numbers."""
    bands = e.get("b") if hasattr(e, "get") else None
    if bands:
        _run.bands = [float(b) for b in bands]
    _run.api.ack()


def _in_page(target):
    """The target as an object in the page, when that is where it lives; else None."""
    if target is None:
        return None
    if hasattr(type(target), "_enc"):
        return target
    page = getattr(target, "page", None)
    if callable(page) and not hasattr(type(page), "_enc"):
        page = page()
    return page if hasattr(type(page), "_enc") else None


class Effect:
    """What Python keeps of an effect that is on in the page. Its settings are plain attributes."""

    def __init__(self, kind, settings, values, args):
        api = _page()
        object.__setattr__(self, "_kind", kind)
        object.__setattr__(self, "_settings", settings)
        object.__setattr__(self, "_values", values)
        object.__setattr__(self, "active", True)
        object.__setattr__(self, "_id", _run.next_id)
        _run.next_id += 1
        api.make(kind, self._id, args)

    @property
    def name(self):
        return self._kind

    @property
    def settings(self):
        return list(self._settings)

    def _setting(self, name):
        key = _key(name)
        if key not in self._settings:
            raise AttributeError("%s has no setting called %r. Its settings are %s"
                                 % (_snake(self._kind), name, ", ".join(_snake(s) for s in self._settings)))
        return key

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._values.get(self._setting(name))

    def __setattr__(self, name, value):
        self.set(name, value)

    def set(self, name, value):
        """Change a setting: effect.set("segments", 12) is effect.segments = 12."""
        key = self._setting(name)
        _check(self._kind, key, self._settings[key], value)
        self._values[key] = value
        _page().set(self._id, key, value)

    def get(self, name):
        return self._values.get(self._setting(name))

    def describe(self, name):
        """What a dial needs to know of a setting: its range, its kind, where it starts."""
        key = self._setting(name)
        s = self._settings[key]
        d = {"name": _snake(key), "kind": "text" if s["kind"] in ("colour", "palette") else s["kind"], "default": s.get("default")}
        for k in ("min", "max", "choices"):
            if k in s:
                d[k] = s[k]
        return d

    def on(self):
        object.__setattr__(self, "active", True)
        _page().call(self._id, "on")
        return self

    def off(self):
        object.__setattr__(self, "active", False)
        _page().call(self._id, "off")
        return self

    def remove(self):
        """Take it off the scene for good."""
        object.__setattr__(self, "active", False)
        _page().call(self._id, "remove")

    def __repr__(self):
        return "<%s %s>" % (_snake(self._kind), ", ".join("%s=%r" % (_snake(k), v) for k, v in self._values.items() if k != "amount"))


def _check(kind, key, s, value):
    """A wrong value is said here, in Python, on the line that gave it: the page would say it a frame later."""
    name, what = _snake(kind), _snake(key)
    k = s["kind"]
    if k == "choice":
        if value not in s["choices"]:
            raise ValueError("%s's %s is one of %s, not %r" % (name, what, ", ".join('"%s"' % c for c in s["choices"]), value))
    elif k == "palette":
        if isinstance(value, str) and value.lower() not in _TABLE["palettes"]:
            raise ValueError('There is no palette called "%s". There are %s, or give a list of colours: ["navy", "magenta", "gold"]'
                             % (value, ", ".join(_TABLE["palettes"])))
    elif k == "colour":
        if not isinstance(value, (str, list, tuple)):
            raise ValueError("%s's %s is a colour (\"gold\", \"#ff8800\"), not %r" % (name, what, value))
    elif k == "bool":
        pass
    elif value is None and s.get("place"):
        pass
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s's %s is a number, not %r" % (name, what, value))


def _maker(kind):
    spec = _EFFECTS[kind]
    order, settings = spec["order"], spec["settings"]

    def make(*args, **options):
        if len(args) > len(order):
            raise TypeError("%s() was given %d values and takes %s. Its other settings go in by name: %s(%s)" % (
                _snake(kind), len(args), "%d (%s)" % (len(order), ", ".join(order)) if order else "none", _snake(kind),
                ", ".join("%s=…" % _snake(n) for n in list(settings)[len(order):len(order) + 2])))
        given = dict(zip(order, args))
        for name, value in options.items():
            key = _key(name)
            if key not in settings:
                raise TypeError("%s has no setting called %r. Its settings are %s" % (_snake(kind), name, ", ".join(_snake(s) for s in settings)))
            given[key] = value
        for key, value in given.items():
            _check(kind, key, settings[key], value)
        values = {k: s.get("default") for k, s in settings.items()}
        values.update(given)
        return Effect(kind, settings, values, [given])

    make.__name__ = _snake(kind)
    shown = ", ".join("%s=%r" % (_snake(k), s.get("default")) for k, s in settings.items() if k != "amount")
    make.__doc__ = "Turn %s on: %s(%s). It gives the effect back: its settings are attributes, and it has off(), on() and remove()." % (
        _snake(kind), _snake(kind), shown)
    return make


__all__ = []
for _kind in _EFFECTS:
    globals()[_snake(_kind)] = _maker(_kind)
    __all__.append(_snake(_kind))
for _alias, _kind in _TABLE["aliases"].items():
    globals()[_snake(_alias)] = globals()[_snake(_kind)]
    __all__.append(_snake(_alias))


class Look:
    """Several effects turned on together: look("dream")."""

    def __init__(self, name, amount):
        api = _page()
        self.name = name
        self._amount = amount
        self._id = _run.next_id
        _run.next_id += 1
        api.make("look", self._id, [name, amount])

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = value
        _page().set(self._id, "amount", value)

    def on(self):
        _page().call(self._id, "on")
        return self

    def off(self):
        _page().call(self._id, "off")
        return self

    def remove(self):
        _page().call(self._id, "remove")


def look(name, amount=1):
    """Several effects at once: look("dream"), look("arcade"), look("vhs"). The names: look_names()."""
    key = re.sub(r"[\s_-]", "", str(name).lower())
    if key not in _TABLE["looks"]:
        raise ValueError('There is no look called "%s". There are %s' % (name, ", ".join(_TABLE["looks"])))
    return Look(key, amount)


def shader(source, **settings):
    """Your own effect, from a program for the graphics card that has `vec4 effect(vec2 uv)`: the colour at one
    place of the picture. Settings by name are numbers it can use: shader(source, speed=2). A mistake in it is
    said by the page, with its line."""
    if not isinstance(source, str) or not re.search(r"\beffect\s*\(", source):
        raise ValueError('shader() takes a program that has a function `vec4 effect(vec2 uv)`: the colour at one place of the picture. '
                         'For example: shader("vec4 effect(vec2 uv) { return texture(picture, uv).bgra; }")')
    table = {k: {"kind": "colour" if isinstance(v, str) else "bool" if isinstance(v, bool) else "float", "default": v} for k, v in settings.items()}
    table["amount"] = {"kind": "float", "default": 1}
    values = dict(settings, amount=1)
    return Effect("shader", table, values, [source, {k: (list(v) if isinstance(v, tuple) else v) for k, v in settings.items()}])


def clear_effects():
    """Take every effect off the scene."""
    _page().clearEffects()


def listen_to(target):
    """What the music is taken from: sound_output(), a synth, a song or the microphone (anything that makes its
    sound in the page). None stops listening."""
    api = _page()
    if target is None:
        api.listen(None)
        return
    page = _in_page(target)
    if page is None:
        raise ValueError("listen_to() is given something that makes sound in the page: sound_output(), or a synth from make_synth()")
    api.listen(page)


_BANDS = ("bass", "mids", "highs", "loudness", "pulse")


def react(effect, setting, band="loudness", low=None, high=None, **given):
    """Tie a setting to the music: react(shine, "strength", "bass", 0.3, 1.2) makes the glow 0.3 when there is
    no bass and 1.2 when there is all of it. The bands: bass, mids, highs, loudness, pulse. It is done in the
    page, on the beat."""
    if not isinstance(effect, Effect):
        raise ValueError('react() is given an effect, the name of one of its settings and what to follow: react(shine, "strength", "bass")')
    key = effect._setting(setting)
    which = {"level": "loudness", "beat": "pulse"}.get(str(band).lower(), str(band).lower())
    if which not in _BANDS:
        raise ValueError('"%s" is not something the music has. There are %s' % (band, ", ".join(_BANDS)))
    low = given.get("from_", given.get("start", low))
    high = given.get("to", given.get("end", high))
    span = {}
    if low is not None:
        span["from"] = low
    if high is not None:
        span["to"] = high
    _page().react(effect._id, key, which, span)
    return effect


def _band(i):
    def read():
        api = _page()
        if not _run.hearing:
            _run.hearing = True
            api.report(_told)
        return _run.bands[i]
    read.__name__ = _BANDS[i]
    read.__doc__ = "The music's %s, from 0 to 1, as the page last told it (a frame ago). For a setting that must be on the beat, use react()." % _BANDS[i]
    return read


bass, mids, highs, loudness, pulse = (_band(i) for i in range(5))


def effects_quality(value):
    """How many of the picture's pixels the effects work on: 1 is all, 0.5 is half each way, "auto" lets the device decide."""
    if value != "auto" and not (isinstance(value, (int, float)) and value > 0):
        raise ValueError('effects_quality() is given a number from 0.25 to 1, or "auto"')
    _page().effectsQuality(value)


def look_names():
    return list(_TABLE["looks"])


def effect_names():
    return [_snake(k) for k in _EFFECTS]


def palette_names():
    return list(_TABLE["palettes"])


__all__ += ["shader", "look", "clear_effects", "listen_to", "react", "bass", "mids", "highs", "loudness", "pulse",
            "effects_quality", "look_names", "effect_names", "palette_names"]
