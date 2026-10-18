"""pysay: make the computer talk. say("Hello") says it, and gives back how many seconds the line takes.

    say("Hello")
    say("Half of the width is the middle.", voice="calm", lang="en")
    sleep(say("Hello"))

and a talking face, with nothing more to set up:

    speaking()                      True while a line is being said
    voice_shape()                   the mouth now: {"width": 0 round to 1 spread, "height": the level, "viseme": ...}
    voice_level()                   how loud the voice is now, 0 (quiet) to 1 (loud)
    mouth(x, y)                     a mouth: a line when quiet, opening with the voice
    mouth(x, y, size=60, style="smile", color="red")     style is "oval" (the default), "smile" or "robot"

and voices and characters, so that two faces can talk to each other:

    voices()                        the voices on offer: [{"name", "lang", "default", "source"}], English first (may be empty at first)
    bob = speaker(voice="deep", pitch=1, rate=1, lang="en", name="Bob")     voice: a name, or "robot", "high", "deep", "squeaky", "slow", "fast"
    bob.say("Hello")                gives back the line's seconds; bob.say_at("Hello") gives {"start", "duration", "end"} (seconds from now)
    bob.level()  bob.shape()  bob.speaking()          this speaker's mouth only (voice_level(bob), voice_shape(bob), speaking(bob) too)
    mouth(x, y, speaker=bob)        opens only while Bob's line plays

Lines said by speakers wait their turn in one queue, so a conversation does not overlap; plain say() is not queued.

With nothing set up it is the draft voice: the device's own speech, free, no account, no network. It is heard live
and cannot be recorded into a video. A page that has a voice host (``mount(el, { voice: host })``, or
``window.pictureHost.voice``) plays the recorded audio of the lines it has instead, and the scene is timed from the
recording's measured length. Nothing here, or anywhere in the libraries, ever generates a voice.

A FILE DOES NOT IMPORT THIS. Pyctures' start() calls begin_run for a file that calls ``say(``, ``mouth(``, ``speaking(``
or ``voice_level(``, which gives the file the names. No other file loads it. (A file that defines a ``say`` of its own keeps its own.)

THE PAGE does the speaking and the playing (say.js beside this file, its ``keep``; the fixed handle H_SAY). Python
writes one command per call. The time a line takes is worked out here, the same way as there: 2.5 words a second,
never under 0.8, unless the page has told this run the measured length of the line (``info["say"]``, a list of
[text, voice, lang, seconds] for every line the host has a recording of that is known before the scene starts) or
tells it with a later frame, for a line made while the scene runs (listen: told is called with {"text", "voice",
"lang", "seconds"}).

THE LEVEL IS THE PAGE'S. Python cannot ask the page, so the page tells it (say.js, ``keep``): with each frame it hands
this run the voice's level and whether it is speaking, when they have changed, as the same ``listen`` callback that tells
it a line's length (an event with "level" and "speaking"). voice_level() and speaking() give the last it was told, so a
frame is told exactly the level of its own moment, also when a recorder steps the scene. How the level is found (the
audio itself for a recorded line, made up from the words for the draft voice, which is not true lip-sync) is said in
say.js, not here. mouth() writes one command with the level in it, and the page draws it among the frame's other
drawing, in the order the scene wrote it (the renderer's ``mouth``, say.js's ``drawMouth``). The look of a mouth
is in say.js only.

PYCTURES ITSELF is reached through `_p()`, never by a plain import at the top of this file.
"""
import ast
import re
import sys


def _p():
    return sys.modules["pyctures"]


H_SAY = 16   # the page's voice: say(text, voice, lang, source, line), listen(callback)

# The names this gives a file, and the calls that ask for them (pages.USES_SAY and pyctures.js's LIBRARIES say the same).
_NAMES = ("say", "say_at", "voices", "speaker", "speaking", "voice_level", "voice_shape", "mouth")
_USES = re.compile(r"(?:^|[^.\w])(?:say|say_at|voices|speaker|speaking|voice_level|voice_shape|mouth)[ \t]*\(")
# The styles of mouth: the page checks them again (say.js's mouthStyles), so a wrong one is said in Python with its line.
STYLES = ("oval", "smile", "robot")


def estimate(text):
    """How many seconds a line takes when nothing has measured it: 2.5 words a second, never under 0.8."""
    return max(0.8, len(str(text).split()) / 2.5)


class _Run:
    """What one run of a file keeps about its lines: the lengths the page has told it, and the lines written out."""

    def __init__(self, info, source):
        self.lengths = {}
        self.level = 0.0         # how loud the voice is, as the page last told this run
        self.speaking = False
        self.width = 0.5         # 0 round (oo) to 1 spread (ee)
        self.viseme = "closed"
        self.speakers = {}       # speaker number (as text) -> what the page last told of its mouth
        self.made = 0            # speakers made so far
        self.tail = 0.0          # when the speakers' queue is free again, on Python's clock
        self.voices = list(info.get("voices") or ())
        for text, voice, lang, seconds in info.get("say") or ():
            self.lengths[(text, voice or None, lang or "en")] = float(seconds)
        self.literal = _literals(source)

    def told(self, e):
        if "voices" in e:
            self.voices = list(e["voices"])
            return
        if "level" in e:
            self.speakers = dict(e.get("speakers") or {})
            self.level = float(e["level"])
            self.width = float(e.get("width", 0.5))
            self.viseme = e.get("viseme", "closed")
            self.speaking = bool(e.get("speaking"))
            return
        self.lengths[(e.get("text"), e.get("voice") or None, e.get("lang") or "en")] = float(e.get("seconds"))


def _literals(source):
    """The texts written out in the file's own calls of say(): {text: line of the first}."""
    found = {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return found
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "say"
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            found.setdefault(node.args[0].value, node.lineno)
    return found


def begin_run(ns, info, source):
    """A file is starting: if it calls say(), give it the name, and keep what the page says of the lines."""
    if not _USES.search(source):
        return
    S = _p().S
    run = S.say = _Run(info, source)
    for name in _NAMES:
        ns[name] = globals()[name]
    # The page tells this run the length of a line it finds later, through an ordinary callback with the next frame's events.
    cb = S.next_cb
    S.next_cb += 1
    S.callbacks[cb] = run.told
    S.cmds.append(["call", 0, 0, H_SAY, "listen", [cb]])


def _check_words(text, voice, lang):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("say(%r) needs the words to say, as in say(\"Hello\")" % (text,))
    if voice is not None and not isinstance(voice, str):
        raise ValueError("say(%r, voice=%r): the voice is the name of a voice, such as \"calm\"" % (text, voice))
    if not isinstance(lang, str) or not lang.strip():
        raise ValueError("say(%r, lang=%r): the language is such as \"en\" or \"fr\"" % (text, lang))


def _say(text, voice, lang, speaker):
    """Write the command, and work out when the line begins: {"start", "duration", "end"}, seconds from now."""
    p = _p()
    run = getattr(p.S, "say", None)
    if speaker is not None:
        if not isinstance(speaker, Speaker) or speaker._run is not run:
            raise ValueError("say(%r, speaker=%r) takes a speaker made with speaker(), as in bob = speaker(voice=\"deep\")" % (text, speaker))
        voice, lang = speaker.voice, speaker.lang
    voice = voice or None
    line = p._user_line()
    literal = run is not None and text in run.literal
    args = [text, voice, lang, "literal" if literal else "runtime", run.literal[text] if literal else line]
    if speaker is not None:
        args.append(speaker.id)
    p.S.cmds.append(["call", line, 0, H_SAY, "say", args])
    duration = run.lengths.get((text, voice, lang), estimate(text)) if run is not None else estimate(text)
    now = p._clock()
    # A speaker's line waits for the line before it; any other begins at once.
    begin = max(now, run.tail) if speaker is not None and run is not None else now
    if speaker is not None and run is not None:
        run.tail = begin + duration
    return {"start": begin - now, "duration": duration, "end": begin - now + duration}


def say(text, voice=None, lang="en", speaker=None):
    """The computer says it. Gives back how many seconds the line takes (the length of the recording the page has of
    it, else 2.5 words a second and never under 0.8). voice is the name of a voice, lang the language ("en").
    speaker=bob says it as that speaker, in its voice, waiting for the lines said before it."""
    _check_words(text, voice, lang)
    return _say(text, voice, lang, speaker)["duration"]


def say_at(text, voice=None, lang="en", speaker=None):
    """Like say(), giving {"start", "duration", "end"}: seconds from now until the line begins (a speaker's line waits
    its turn), how long it takes and when it ends. await sleep(bob.say_at("Hi")["end"]) waits for it."""
    _check_words(text, voice, lang)
    return _say(text, voice, lang, speaker)


def voices():
    """The voices on offer: [{"name", "lang", "default", "source": "device" or "host"}], English first. A device may load
    its voices late: the list is empty until the page has told this run, so ask again a moment later."""
    run = getattr(_p().S, "say", None)
    return [dict(v) for v in run.voices] if run is not None else []


class Speaker:
    """A character: its own voice, pitch and rate, its turn in the queue and its own mouth. Made by speaker()."""

    def __init__(self, run, id, voice, pitch, rate, lang, name):
        self._run, self.id = run, id
        self.voice, self.pitch, self.rate, self.lang, self.name = voice, pitch, rate, lang, name

    def say(self, text):
        """Say it as this speaker. Gives back how many seconds the line takes."""
        _check_words(text, None, self.lang)
        return _say(text, None, self.lang, self)["duration"]

    def say_at(self, text):
        """Like say(), giving {"start", "duration", "end"} in seconds from now."""
        _check_words(text, None, self.lang)
        return _say(text, None, self.lang, self)

    def _told(self):
        return self._run.speakers.get(str(self.id)) or {}

    def level(self):
        """How loud this speaker's voice is right now, 0 to 1."""
        return float(self._told().get("level", 0.0))

    def shape(self):
        """This speaker's mouth now: {"width", "height", "viseme"}."""
        t = self._told()
        return {"width": float(t.get("width", 0.5)), "height": float(t.get("level", 0.0)), "viseme": t.get("viseme", "closed")}

    def speaking(self):
        """True while this speaker's line is being said."""
        return bool(self._told().get("speaking"))

    def __repr__(self):
        return "<speaker %s>" % (self.name or self.voice or self.id)


def speaker(voice=None, pitch=1, rate=1, lang="en", name=None, like=None, fallback=None):
    """A character for a conversation: speaker(voice="deep"), speaker("robot", rate=0.8). voice is the name of a voice or
    "robot", "high", "deep", "squeaky", "slow" or "fast" (which work on any device); pitch is 0 to 2 and rate 0.1 to 4
    (1 is normal). bob.say("Hello") says a line, and mouth(x, y, speaker=bob) opens only while Bob talks.
    voice may also be "provider:voice" (system:Samantha, kokoro:af_heart, hq:nova, draft:). like={"gender": "female",
    "age": "child", "pitch": 1.3, "rate": 1} describes the voice for any provider to match, and fallback=["system:Samantha",
    "high"] lists voices to try in turn."""
    if voice is not None and (not isinstance(voice, str)):
        raise ValueError("speaker(voice=%r): the voice is a name such as \"deep\" or \"robot\"" % (voice,))
    for name_, value, lo, hi in (("pitch", pitch, 0, 2), ("rate", rate, 0.1, 4)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
            raise ValueError("speaker(%s=%r): %s is a number from %s to %s (1 is normal)" % (name_, value, name_, lo, hi))
    if not isinstance(lang, str) or not lang.strip():
        raise ValueError("speaker(lang=%r): the language is such as \"en\" or \"fr\"" % (lang,))
    if name is not None and not isinstance(name, str):
        raise ValueError("speaker(name=%r): the name is text" % (name,))
    if like is not None:
        if not isinstance(like, dict):
            raise ValueError("speaker(like=%r): like describes a voice, as in like={\"gender\": \"female\", \"age\": \"child\"}" % (like,))
        for k, v in like.items():
            if k not in ("gender", "age", "pitch", "rate"):
                raise ValueError("speaker(like=...): like has gender, age, pitch and rate, not %r" % (k,))
            if k in ("gender", "age") and v is not None and not isinstance(v, str):
                raise ValueError("speaker(like=...): like[%r] is a word such as %s, not %r" % (k, '"female"' if k == "gender" else '"child"', v))
            if k in ("pitch", "rate") and v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not v > 0):
                raise ValueError("speaker(like=...): like[%r] is a number above 0, not %r" % (k, v))
        like = dict(like)
    if fallback is not None and (isinstance(fallback, str) or not isinstance(fallback, (list, tuple)) or any(not isinstance(f, str) for f in fallback)):
        raise ValueError("speaker(fallback=%r): fallback is a list of voices to try in turn, as in fallback=[\"system:Samantha\", \"high\"]" % (fallback,))
    fallback = list(fallback) if fallback else None
    p = _p()
    run = getattr(p.S, "say", None)
    if run is None:
        raise RuntimeError("speaker() needs the voice, which the page brings when the file calls say() or speaker()")
    run.made += 1
    made = Speaker(run, run.made, voice or None, pitch, rate, lang, name)
    p.S.cmds.append(["call", p._user_line(), 0, H_SAY, "speaker", [made.id, made.voice, pitch, rate, lang, name, like, fallback]])
    return made


def _speaker_told(speaker, where):
    if not isinstance(speaker, Speaker):
        raise ValueError("%s takes a speaker made with speaker(), as in bob = speaker(voice=\"deep\")" % where)
    return speaker


def speaking(speaker=None):
    """True while a line is being said (a recorded line for its length, the draft voice for as long as the browser says it is
    speaking). With a speaker, only while that speaker's line is."""
    if speaker is not None:
        return _speaker_told(speaker, "speaking(speaker)").speaking()
    run = getattr(_p().S, "say", None)
    return run.speaking if run is not None else False


def voice_level(speaker=None):
    """How loud the voice is right now, from 0 (quiet) to 1 (loud). The recording's own loudness for a line that has one;
    for the draft voice, made up from the words (that is not true lip-sync). Smoothed, and 0 when nothing is being said.
    With a speaker, that speaker's alone; without, any speaker's."""
    if speaker is not None:
        return _speaker_told(speaker, "voice_level(speaker)").level()
    run = getattr(_p().S, "say", None)
    return run.level if run is not None else 0.0


def voice_shape(speaker=None):
    """The shape of the mouth now: {"width": 0 (round, like "oo") to 1 (spread, like "ee"), "height": the level, 0 to 1,
    "viseme": "closed", "oo", "oh", "ah", "mid" or "ee"}. Found by the page: from the audio's loudness and how
    quickly its wave crosses zero for a recording, from the words' vowels for the draft voice (not true lip-sync).
    With a speaker, that speaker's alone."""
    if speaker is not None:
        return _speaker_told(speaker, "voice_shape(speaker)").shape()
    run = getattr(_p().S, "say", None)
    if run is None:
        return {"width": 0.5, "height": 0.0, "viseme": "closed"}
    return {"width": run.width, "height": run.level, "viseme": run.viseme}


def mouth(x, y, size=None, style="oval", color="black", speaker=None):
    """Draw a mouth with its middle at (x, y): a line when it is quiet, opening with the voice. size is how wide it is
    (a sixth of the smaller side of the screen if you do not say); style is "oval", "smile" or "robot"; color is any colour.
    speaker=bob makes it open only while Bob's line plays.
    Gives back None (the page draws it, and has not yet when Python goes on)."""
    for name, value in (("x", x), ("y", y)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("mouth(%s=%r) needs the middle of the mouth as numbers, as in mouth(width / 2, height / 2)" % (name, value))
    if size is not None and (isinstance(size, bool) or not isinstance(size, (int, float)) or not size > 0):
        raise ValueError("mouth(size=%r): the size is a number of pixels above 0, as in mouth(x, y, size=60)" % (size,))
    if style not in STYLES:
        raise ValueError("mouth(style=%r): the style is one of %s" % (style, ", ".join(repr(s) for s in STYLES)))
    if not isinstance(color, str):
        raise ValueError("mouth(color=%r): the colour is a name or a code such as \"red\" or \"#c00\"" % (color,))
    p = _p()
    shape = voice_shape(speaker)
    p.S.cmds.append(["call", p._user_line(), 0, H_SAY, "mouth", [x, y, size, style, color, shape["height"], shape["width"]]])
