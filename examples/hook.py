# Hook: the first six seconds of a video. A promise, said in big
# type, then the proof that follows. Same code for a wide video
# and a tall one: the text lays itself out from width and height.
# Try changing: the words; the seconds in start and duration.
#
# Run it:   pyctures run hook.py

def draw():
    background(house_style.palette.ink)

    # The beat of a pretend song, 120 beats a minute (a real
    # song's music object would do: it has a .beat too).
    beat = kinetic_time() * 2

    # 0 to 1.6 s: the promise, one word at a time.
    word_slam("Learn to code.", start=0.2, duration=1.4)

    # 1.8 s on: the surprise, wiped in under it, with a pulse.
    mask_reveal("*From zero.*", y=0.68, start=1.8, duration=0.8,
                size="title", style="calm", beat=beat)

    # 3.2 s on: a number counts up, and the line under it types.
    count_up("1,000+ lessons", y=0.3, start=3.2, duration=1.5,
             size="title", style="techy")
    typewriter_text("No install. Just press run.", y=0.86,
                    start=4.4, duration=1.4, size="body",
                    style="techy")
