# Voice Changer: your voice as a robot, a chipmunk or a monster.
# Use: pick a voice, then press "listen" to hear yourself. Wear headphones: through loudspeakers a
# microphone that hears itself howls. Or press "record", say something, and press "play" to hear it
# back in whichever voice is chosen now. With no microphone everything still works, and the picture
# says why there is nothing to hear.
# Try changing: 3, the seconds a recording lasts; add dial("ring", mic, "ring") or
# dial("crush", mic, "crush"); play it back higher with take.play("G4"); or keep it, with
# save_sound(take, "me.wav"), which writes the file beside this one.
#
# Run it:   pyctures run voice_changer.py
# Share it: pyctures build voice_changer.py -o site/
# The browser asks whether the page may use the microphone: say yes. (A page has to be served over
# https or from localhost to be given one, which `pyctures run` does.)

from pyctures import *
from synths import *
from pydials import *

mic = use_microphone()         # nothing is heard until it is listened to
take = None

says = label("Asking for the microphone")
select("voice", mic, "voice")
dial("pitch", mic, "pitch")
dial("echo", mic, "echo")
toggle("listen", mic, "listening")

def record():
    global take
    take = mic.record(3)       # three seconds, starting now. It is given back at once and fills up behind
    says.value = "Recording"
    take.on_done(recorded)

def recorded():
    says.value = "Recorded: press play" if take.seconds else "Nothing was recorded: there is no microphone"

def play():
    if take:
        take.sound_like(mic).play()    # the same words, in the voice chosen now

button("record", record)
button("play", play)
scope(mic)
meter(mic)

def ready(there):
    says.value = "Say something" if there else "No microphone here (" + mic.state + "): the browser's console says why"

mic.on_ready(ready)            # called when the page has said whether there is a microphone

def draw():
    background("midnightblue")
    text("Pick a voice, press listen, and talk. Headphones are best", width / 2, height - 60, "#8a93a6", 16, "centre")
    text("the microphone is " + mic.state, width / 2, height - 34, "#5d6577", 14, "centre")
