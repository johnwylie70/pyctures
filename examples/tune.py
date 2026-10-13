# Tune: drums, a bass and a melody that go round and round, with lights that flash in time.
# Click, tap or press a key to start it: a browser keeps a page silent until it has been touched.
# Try changing: 104, the beats a minute; "lead" to "bell" or "chip_lead"; the notes ("-" is a rest,
# ":2" makes a note last two steps); lead.echo = 0.35 to 0.
#
# Run it:   pyctures run tune.py
# Share it: pyctures build tune.py -o site/

from synths import *

set_tempo(104)
step = beats(0.25)                  # four steps to a beat
start = None                        # when the tune began, on the sound clock

kick = make_synth("kick")
snare = make_synth("snare")
hat = make_synth("hat", volume=0.4)
bass = make_synth("bass")
lead = make_synth("lead")
lead.echo = 0.35
set_effects(echo_time=beats(0.75), echo_feedback=0.4, reverb_size=0.7)

def begin():
    global start
    if start is not None:
        return
    start = sound_time() + 0.1      # every part begins at the same moment, so they stay together
    kick.play_notes("C2 - - - - - C2 - C2 - - - - - - -", step, repeat=True, at=start)
    snare.play_notes("- - - - E3 - - - - - - - E3 - - E3", step, repeat=True, at=start)
    hat.play_notes("C4 - C4 - C4 - C4 C4 C4 - C4 - C4 - C4 -", step, repeat=True, at=start)
    bass.play_notes("A1 - A1 A2 - A1 - C2 | F1 - F1 F2 - F1 - G1", step, repeat=True, at=start)
    lead.play_notes("E4:2 A4:2 C5 B4 A4:2 | F4:2 A4:2 C5 D5 C5 B4 | "
                    "E4:2 A4:2 C5 B4 A4:2 | G4:2 B4:2 D5:3 -", step, repeat=True, at=start)

def on_mouse_down(x, y):
    begin()

def on_key_down(key):
    begin()

def draw():
    background("#12101f")
    if start is None:
        text("Click to start the tune", width / 2, height / 2, "white", 28, "centre")
        return
    now = max(0, (sound_time() - start) / step)     # which step of the tune it is
    for i in range(16):
        x = (i + 0.5) * width / 16
        on = int(now) % 16 == i
        circle(x, height / 2, 16 if on else 9, "gold" if on else "#3b3560")
    thump = 1 - (now / 4) % 1                        # 1 on each beat, falling away until the next
    circle(width / 2, height / 2 - 110, 30 + 30 * thump, "tomato")
    text("Tune", width / 2, height - 60, "white", 28, "centre")
