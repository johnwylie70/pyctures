"""circle, rect, line, text and background: one command each, and a scene's own name wins."""
import json
import textwrap

import pytest

import pyctures

INFO = json.dumps({"width": 400, "height": 300, "pixel_ratio": 1})
H_DRAW = 7


def start(src):
    return json.loads(pyctures.start(textwrap.dedent(src), INFO))


@pytest.fixture(autouse=True)
def stopped():
    yield
    pyctures.stop()


def test_each_is_one_command_with_the_users_line():
    r = start("""
        background("navy")
        circle(200, 150, 80, "gold")
        rect(10, 20, 30, 40)
        line(0, 0, 400, 300, "white", 3)
        text("Hello", 200, 150, "white", 32, "centre")
    """)
    assert r["error"] is None
    assert r["cmds"] == [
        ["call", 2, 0, H_DRAW, "background", ["navy"]],
        ["call", 3, 0, H_DRAW, "circle", [200, 150, 80, "gold"]],
        ["call", 4, 0, H_DRAW, "rect", [10, 20, 30, 40, None]],
        ["call", 5, 0, H_DRAW, "line", [0, 0, 400, 300, "white", 3]],
        ["call", 6, 0, H_DRAW, "text", ["Hello", 200, 150, "white", 32, "centre"]],
    ]


def test_two_thousand_circles_are_two_thousand_commands():
    r = start("""
        def draw():
            for i in range(2000):
                circle(i, i, 5, "red")
    """)
    # (an earlier test's objects may be let go in this frame too: count the drawing only)
    assert r["error"] is None and len([c for c in r["cmds"] if c[0] == "call"]) == 2000


def test_a_scenes_own_name_wins():
    r = start("""
        def circle(n):
            return n * 2
        text = "my words"
        line = [1, 2, 3]
        print(circle(21), text, line)
        rect(1, 2, 3, 4, "red")
    """)
    assert r["error"] is None and r["out"] == "42 my words [1, 2, 3]\n"
    assert [c[4] for c in r["cmds"]] == ["rect"]


def test_ctx_forgets_a_colour_the_page_has_changed():
    r = start("""
        ctx.fill_style = "red"
        ctx.line_width = 4
        print(ctx.fill_style, ctx.line_width)
        background("black")            # leaves the colour alone
        print(ctx.fill_style)
        circle(1, 2, 3, "blue")        # the page's colour is blue now
        print(type(ctx.fill_style).__name__, ctx.line_width)
    """)
    assert r["error"] is None
    assert r["out"] == "red 4\nred\nJsRef 4\n"


def test_a_colour_can_be_something_made_in_the_page():
    r = start("""
        g = ctx.create_linear_gradient(0, 0, 100, 0)
        rect(0, 0, 100, 100, g)
    """)
    assert r["error"] is None
    made = [c for c in r["cmds"] if c[0] == "call" and c[4] == "create_linear_gradient"][0]
    assert r["cmds"][-1][5][4] == {"$h": made[2]}


def test_degrees_says_an_angle_in_degrees_and_a_scenes_own_wins():
    import math
    assert pyctures.degrees(180) == pytest.approx(math.pi) and pyctures.degrees(-90) == pytest.approx(-math.pi / 2)
    r = start("""
        s = Sprite("a", 0, 0)
        s.angle = degrees(90)
        s.push(10)
        print(round(s.vx, 6), round(s.vy, 6))
    """)
    assert r["error"] is None and r["out"] == "0.0 10.0\n"
    r = start("""
        from math import *
        print(round(degrees(pi)))
    """)
    assert r["error"] is None and r["out"] == "180\n"


def test_outline_and_the_other_keywords_travel_as_one_last_argument_only_when_given():
    r = start("""
        circle(1, 2, 3, "gold", outline="white", thickness=3)
        circle(1, 2, 3, outline="white")
        rect(0, 0, 10, 10, "red", round=4)
        triangle(0, 0, 10, 0, 5, 8, "red")
        ellipse(5, 5, 10, 4, "blue")
        polygon(5, 5, 4, 6)
        star(5, 5, 4, 5, "gold", inner=0.5)
    """)
    assert r["error"] is None
    assert [c[4:] for c in r["cmds"]] == [
        ["circle", [1, 2, 3, "gold", {"$d": {"outline": "white", "thickness": 3}}]],
        ["circle", [1, 2, 3, None, {"$d": {"outline": "white"}}]],
        ["rect", [0, 0, 10, 10, "red", {"$d": {"round": 4}}]],
        ["triangle", [0, 0, 10, 0, 5, 8, "red"]],
        ["ellipse", [5, 5, 10, 4, "blue"]],
        ["polygon", [5, 5, 4, 6, None]],
        ["star", [5, 5, 4, 5, "gold", {"$d": {"inner": 0.5}}]],
    ]


def test_picture_sends_an_emoji_as_it_is_and_a_file_as_the_image_it_loaded_once():
    r = start("""
        def draw():
            picture("🌙", 10, 20, 30)
            picture("cat.png", 1, 2)
            picture("cat.png", 3, 4)
    """)
    assert r["error"] is None
    pics = [c for c in r["cmds"] if c[0] == "call" and c[4] == "picture"]
    assert pics[0][5] == ["🌙", 10, 20, 30]
    assert pics[1][5][0] == pics[2][5][0] and "$h" in pics[1][5][0] and pics[1][5][1:] == [1, 2, 48]
    assert len([c for c in r["cmds"] if c[0] == "set" and c[3] == "src"]) == 1


def test_random_is_whole_numbers_fractions_and_still_pythons_module():
    r = start("""
        rolls = [random(1, 6) for i in range(300)]
        print(sorted(set(rolls)) == [1, 2, 3, 4, 5, 6], all(type(n) is int for n in rolls))
        print(sorted(set(random(3) for i in range(200))))
        print(all(0 <= random() < 1 for i in range(50)), all(0 <= random(0, 0.5) <= 0.5 for i in range(50)))
        print(any(random(0, 0.5) % 1 for i in range(20)), type(random(0, 4.0)) is int)
        print(pick(["a", "b"]) in "ab", random.randint(5, 5), round(random.uniform(2, 2)))
    """)
    assert r["error"] is None, r["error"]
    assert r["out"] == "True True\n[0, 1, 2, 3]\nTrue True\nTrue True\nTrue 5 2\n"


def test_a_scene_that_imports_random_any_way_keeps_both_meanings():
    for line in ("import random", "import random as random", "from random import random, randint, choice"):
        r = start(line + """
print(random(1, 1), 0 <= random() < 1)
def later():
    import random as r
    return r(2, 2), r.randint(3, 3), r.choice([4])
print(later())
""")
        assert r["error"] is None, r["error"]
        assert r["out"] == "1 True\n(2, 3, 4)\n", (line, r["out"])
    # Python's own module is as it was, for everything that is not the scene's file
    import random as real
    assert type(real).__name__ == "module" and not callable(real)
    with pytest.raises(TypeError):
        real.random(1, 6)
    r = start("""
        import random
        random.seed(7)
        a = random(1, 1000)
        random.seed(7)
        print(a == random.randint(1, 1000))
    """)
    assert r["error"] is None and r["out"] == "True\n"


def test_a_scenes_own_random_and_pick_win():
    r = start("""
        def random(n):
            return n + 1
        pick = len
        print(random(1), pick([1, 2, 3]))
    """)
    assert r["error"] is None and r["out"] == "2 3\n"
