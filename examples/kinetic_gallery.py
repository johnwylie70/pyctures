# Kinetic text gallery: every moving-text effect in turn, three
# seconds each, in three voices, in a wide frame or a tall one.
# Try changing: the words (put *stars* round the word that matters);
# "playful", "techy" or "calm"; each, how long an effect shows.
#
# Run it:   pyctures run kinetic_gallery.py

# Each effect: its name, the function, and the words it is given.
show = [
    ("word_slam", word_slam, "Learn *to code* today"),
    ("letter_wave", letter_wave, "Everything *moves*"),
    ("letter_bounce", letter_bounce, "Drop in *bounce*"),
    ("typewriter_text", typewriter_text, "print('hello, world')"),
    ("glitch_text", glitch_text, "Signal *lost*"),
    ("mask_reveal", mask_reveal, "Wipe *it* clean"),
    ("scale_pop", scale_pop, "Make it *pop* now"),
    ("ticker_text", ticker_text, "Free to try   *Python*   JavaScript"),
    ("count_up", count_up, "12,000+"),
    ("highlight_sweep", highlight_sweep, "Mark the *important* part"),
]
voices = ["playful", "techy", "calm"]

# Seconds each effect is shown for.
each = 3


def draw():
    background(house_style.palette.ink)

    # Which effect it is, and how far into its slot.
    clock = kinetic_time()
    n = int(clock // each) % len(show)
    local = clock % each
    name, effect, words = show[n]

    # The name, at the top of the safe area.
    safe = kinetic_safe()
    label = safe.top + height * 0.03
    text(name, width / 2, label, house_style.palette.dim,
         height * 0.035, "centre")

    # The effect, given room under the name. t is the time in the slot.
    room = (safe.top + height * 0.08) / height
    effect(words, t=local, style=voices[n % 3], safe={"top": room})
