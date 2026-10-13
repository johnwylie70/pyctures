# Synth Panel: a synth you can play. Dials and a slider for its settings, the wave it is making,
# and a piano keyboard: play it with a finger, the mouse, or the computer's keys (A S D F G H J
# are the white keys, W E T Y U the black ones, Z and X step down and up an octave).
# Try changing: "lead" to "bass", "pad" or "bell"; octave=4 to 2; add dial("echo", lead, "echo").
#
# Run it:   pyctures run synth_panel.py
# Share it: pyctures build synth_panel.py -o site/

from pyctures import *
from synths import *
from pydials import *

lead = make_synth("lead")
dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
slider("attack", lead, "attack")
scope(lead)
keyboard(lead, octave=4)

def draw():
    background("#14161c")
    text("Play the keys, and turn the dials while a note sounds", width / 2, height / 2 + 40, "#8a93a6", 16, "centre")
