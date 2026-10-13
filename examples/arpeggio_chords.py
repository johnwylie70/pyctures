# Arpeggio Chords: one voice playing the notes of a chord so fast that it sounds like a chord, as the
# sound chips of old home computers did. Click or tap a box to change the chord, or press a key from 1 to 4;
# space is quiet.
# The first click, tap or key press turns the sound on: a browser keeps a page silent until then.
# Try changing: speed=40 to 12, to hear the notes one by one; "up" to "up-down" or "random";
# "chip_lead" to "chip"; the chords ("Am", "Fmaj7", "Csus4", "G").
#
# Run it:   pyctures run arpeggio_chords.py
# Share it: pyctures build arpeggio_chords.py -o site/

from synths import *

CHORDS = ["Am", "F", "C", "G"]
COLOURS = ["#e76f51", "#2a9d8f", "#e9c46a", "#8ab6f9"]

voice = make_synth("chip_lead", volume=0.6)
bass = make_synth("chip_bass", volume=0.7)
arp = None                # the arpeggio that is sounding
playing = -1

def play(i):
    global arp, playing
    playing = i
    root = chord_notes(CHORDS[i])[0]
    if arp is None:
        arp = voice.start_arp(CHORDS[i], speed=40, order="up")
    else:
        arp.change(CHORDS[i])              # another chord, and the note carries on
    bass.play(root - 24, 0.4)

def box(i):
    w = width / len(CHORDS)
    return i * w + 8, height / 2 - 70, w - 16, 140

def on_mouse_down(x, y):
    for i in range(len(CHORDS)):
        bx, by, bw, bh = box(i)
        if bx <= x <= bx + bw and by <= y <= by + bh:
            play(i)

def on_key_down(key):
    global arp, playing
    if key in ("1", "2", "3", "4"):
        play(int(key) - 1)
    if key == " " and arp is not None:     # space: quiet
        arp.stop()
        arp, playing = None, -1

def draw():
    background("#0f1020")
    for i, name in enumerate(CHORDS):
        bx, by, bw, bh = box(i)
        rect(bx, by, bw, bh, COLOURS[i] if i == playing else "#24263f", round=14)
        text(name, bx + bw / 2, by + bh / 2, "white", 36, "centre")
        text(str(i + 1), bx + bw / 2, by + bh - 18, "#c8cbe0", 14, "centre")
    text("Click a arp", width / 2, 60, "white", 22, "centre")
