# Typing: what you type appears in the middle, in a box drawn to fit the words.
# Use: click the picture, then type. Backspace rubs out.
# Try changing: "Type something", the words it starts with; 44px, the size of the letters.
#
# Run it:   pyctures run type_and_measure.py
# Share it: pyctures build type_and_measure.py -o site/

text = "Type something"
measured = None        # the text the width below belongs to
text_width = 0

def on_key_down(key):
    global text
    if text == "Type something":
        text = ""
    if key == "Backspace":
        text = text[:-1]
    elif key == "Escape":
        text = ""
    elif len(key) == 1:            # a letter, number, space or symbol
        text += key

async def draw():
    global measured, text_width
    ctx.font = "bold 44px system-ui, sans-serif"
    if measured != text:
        # Reading a value back from the browser waits a frame, so only
        # measure when the text has changed.
        measured = text
        text_width = await ctx.measure_text(text).width

    ctx.fill_style = "#101828"
    ctx.fill_rect(0, 0, width, height)

    # a box that fits the text
    box_w = max(text_width, 40) + 40
    ctx.fill_style = "#1f2a44"
    ctx.fill_rect((width - box_w) / 2, height / 2 - 44, box_w, 76)
    ctx.stroke_style = "#7cc4ff"
    ctx.line_width = 2
    ctx.stroke_rect((width - box_w) / 2, height / 2 - 44, box_w, 76)

    ctx.fill_style = "white"
    ctx.font = "bold 44px system-ui, sans-serif"
    ctx.text_align = "center"
    ctx.text_baseline = "middle"
    ctx.fill_text(text, width / 2, height / 2 - 6)

    ctx.font = "15px system-ui, sans-serif"
    ctx.fill_style = "#9aa3b2"
    ctx.fill_text(f"{text_width:.0f} points wide   ·   Backspace deletes, Escape clears",
                  width / 2, height / 2 + 60)
    held = ", ".join(sorted(k if k != " " else "Space" for k in keys))
    ctx.fill_text(f"Keys held: {held or 'none'}", width / 2, height - 30)
