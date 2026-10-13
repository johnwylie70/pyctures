# MIDI Lights: every key played on a MIDI keyboard rings a bell and throws a ball up the picture,
# and any knob or slider you turn changes how big the balls are. on_midi_note and on_midi_control
# are functions you write, and they are called when a key goes down and when a knob moves.
# Use: play a MIDI keyboard and turn a knob. With none plugged in, click or tap (left to right is
# low to high), or press a key of the computer: that pretends to be one.
# Try changing: "bell" to "pluck"; the colours; make the knob change the reverb instead
# (bell.reverb = value).
#
# Run it:   pyctures run midi_lights.py
# Share it: pyctures build midi_lights.py -o site/
# The browser asks whether the page may use your MIDI devices: say yes. (MIDI works in Chrome, Edge
# and Firefox on a computer. Safari, iPhones and iPads have none for web pages.)

from synths import *

bell = make_synth("bell", reverb=0.4)
balls = []
size = 0.4
message = "Looking for a MIDI keyboard"

# A key went down. note is its number (60 is middle C), velocity is how hard, from 0 to 1.
def on_midi_note(note, velocity, channel):
    bell.play(note, 0.4, velocity)
    balls.append({"x": width * (note - 36) / 60, "y": height, "speed": 150 + 450 * velocity,
                  "colour": "hsl(%d, 90%%, 60%%)" % (note * 30)})

# A key came up. (Without this function, on_midi_note would be called for it with velocity 0.)
def on_midi_note_off(note, channel):
    pass

# A knob or slider moved. number says which one, and value goes from 0 to 1.
def on_midi_control(number, value, channel):
    global size
    size = value

def on_midi_devices(devices):
    global message
    if devices["inputs"]:
        message = "Play " + ", ".join(devices["inputs"]) + ", and turn a knob"
    else:
        message = "No MIDI keyboard was found: click, or press a key, to pretend"

# With no keyboard: receive_midi hands the scene a message just as a keyboard would.
def on_mouse_down(x, y):
    global size
    receive_midi({"type": "noteOn", "note": round(36 + 60 * x / width), "velocity": 0.8, "channel": 1})
    size = 1 - y / height

def on_key_down(key):
    receive_midi({"type": "noteOn", "note": 48 + ord(key[0]) % 25, "velocity": 0.8, "channel": 1})

def update(dt):
    for ball in balls:
        ball["y"] -= ball["speed"] * dt
    balls[:] = [ball for ball in balls if ball["y"] > -60]

def draw():
    background("black")
    for ball in balls:
        circle(ball["x"], ball["y"], 6 + 44 * size, ball["colour"])
    text(message, width / 2, 30, "white", 16, "centre")
