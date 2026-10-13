# MIDI Keyboard: plug a MIDI keyboard in and play this synth with it, and turn its dials with the
# keyboard's knobs.
# Use: play the keyboard. The first three knobs or sliders you move become the cutoff, the resonance
# and the echo, and the dial on the screen turns with the knob. With nothing plugged in it is still a
# synth: play the keys on the screen with the mouse, your fingers or A S D F G H J, and drag the dials.
# Try changing: "lead" to "pad", "bass" or "keys"; learn another setting ("attack", "reverb"); or tie
# a knob by its number, with lead.map_midi(74, "cutoff"), instead of learning it.
#
# Run it:   pyctures run midi_keyboard.py
# Share it: pyctures build midi_keyboard.py -o site/
# The browser asks whether the page may use your MIDI devices: say yes. (MIDI works in Chrome, Edge
# and Firefox on a computer. Safari, iPhones and iPads have none for web pages.)

from pyctures import *
from synths import *
from pydials import *

lead = make_synth("lead")

dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
dial("echo", lead, "echo")
scope(lead)
keyboard(lead, octave=4)

lead.play_from_midi()       # the MIDI keyboard plays it: notes, how hard, the pitch wheel and the pedal

# learn: the next knob that is moved turns this setting from then on, and its dial with it.
lead.learn("cutoff")
lead.learn("resonance")
lead.learn("echo")

found = label("Looking for a MIDI keyboard")

def on_midi_devices(devices):
    if devices["inputs"]:
        found.value = "Play " + ", ".join(devices["inputs"]) + ", and move three knobs"
    else:
        found.value = "No MIDI keyboard was found: play the keys below"

def draw():
    background("midnightblue")
    text("cutoff %d Hz" % lead.cutoff, width / 2, height / 2 + 40, "#8a93a6", 16, "centre")
