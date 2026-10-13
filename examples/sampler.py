# Sampler: record a word, then play it on the keys.
# Use: press "record" and say a word. Middle C is the word as you said it; higher keys are higher
# and faster, lower keys lower and slower, and several keys make a chord of you. Play with the mouse,
# your fingers or the keys A S D F G H J (white) and W E T Y U (black). With no microphone the keys
# play a bell instead.
# Try changing: 1.5, the seconds recorded; "bell" to "pluck"; take.loop = True; take.voice = "robot".
#
# Run it:   pyctures run sampler.py
# Share it: pyctures build sampler.py -o site/
# The browser asks whether the page may use the microphone: say yes.

from pyctures import *
from synths import *
from pydials import *

mic = use_microphone()
word = make_synth("bell")      # what the keys play until a word is recorded
take = None

says = label("Press record and say a word")

def record():
    global take
    take = mic.record(1.5)
    says.value = "Recording"
    take.on_done(recorded)

def recorded():
    global word
    if not take.seconds:
        says.value = "No microphone here, so the keys play a bell"
        return
    take.release = 0.2
    take.reverb = 0.2
    word = take
    says.value = "Now play the keys"

def backwards():
    word.reverse = not word.reverse

def echo(value):
    word.echo = value

button("record", record)
button("backwards", backwards)
dial("echo", 0, 1, 0, on_change=echo)

# The keyboard plays whatever `word` is now.
def key_down(note, loud):
    word.note_on(note, loud)

def key_up(note):
    word.note_off(note)

keyboard(octave=4, on_note_on=key_down, on_note_off=key_up)

def draw():
    background("darkslategray")
    text("Record a word, then play it on the keys: middle C is the word as you said it", width / 2, height / 2 - 40, "#b8c4c0", 16, "centre")
