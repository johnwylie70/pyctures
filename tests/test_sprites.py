"""Sprites: hit-testing (pure Python), the movement helpers, and what draw() sends."""
import json
import math
import textwrap

import pytest

import pyctures
from pyctures import (Sprite, boxes_touch, circle_touches_box, circles_touch,
                      point_in_box, point_in_circle, remove)

INFO = json.dumps({"width": 400, "height": 300, "pixel_ratio": 1})


def start(src=""):
    return json.loads(pyctures.start(textwrap.dedent(src), INFO))


@pytest.fixture(autouse=True)
def scene():
    """A running scene 400 by 300, so wrap(), bounce() and offscreen() know the edges."""
    start()
    yield
    pyctures.stop()


# ---------------------------------------------------------------- the pure tests

def test_circles_touch_inside_but_not_exactly_at_the_edge():
    assert circles_touch(0, 0, 10, 19.9, 0, 10)
    assert not circles_touch(0, 0, 10, 20, 0, 10)
    assert not circles_touch(0, 0, 0, 0, 0, 0)


def test_boxes_touch_inside_but_not_edge_to_edge():
    assert boxes_touch(0, 0, 100, 20, 99, 0, 100, 20)
    assert not boxes_touch(0, 0, 100, 20, 100, 0, 100, 20)
    assert boxes_touch(0, 0, 100, 20, 0, 19.9, 10, 20)
    assert not boxes_touch(0, 0, 100, 20, 0, 20, 10, 20)
    assert boxes_touch(0, 0, 100, 20, 0, 0, 2, 2)


def test_circle_and_box_sides_corners_and_one_inside_the_other():
    assert circle_touches_box(0, 0, 10, 59.9, 0, 100, 20)
    assert not circle_touches_box(0, 0, 10, 60, 0, 100, 20)
    k = 10 / math.sqrt(2)   # the box's corner is this far across and down
    assert circle_touches_box(0, 0, 10, 50 + k - 0.01, 10 + k - 0.01, 100, 20)
    assert not circle_touches_box(0, 0, 10, 50 + k + 0.01, 10 + k + 0.01, 100, 20)
    # the squares round the two overlap here, the shapes do not
    assert not circle_touches_box(0, 0, 10, 59, 19, 100, 20)
    assert circle_touches_box(0, 0, 100, 5, 5, 4, 4)      # box inside circle
    assert circle_touches_box(50, 50, 2, 0, 0, 200, 200)  # circle inside box
    assert not circle_touches_box(0, 0, 0, 0, 0, 200, 200)  # nothing touches a circle of no size


def test_a_turned_box_is_tested_turned_against_a_circle_and_a_point():
    quarter = math.pi / 2   # a 100 by 10 box turned a quarter is 10 by 100
    assert circle_touches_box(0, 55, 10, 0, 0, 100, 10, quarter)
    assert not circle_touches_box(40, 0, 10, 0, 0, 100, 10, quarter)
    assert point_in_box(0, 45, 0, 0, 100, 10, quarter)
    assert not point_in_box(45, 0, 0, 0, 100, 10, quarter)


def test_points_on_the_edge_are_inside():
    assert point_in_circle(10, 0, 0, 0, 10) and not point_in_circle(10.1, 0, 0, 0, 10)
    assert point_in_box(50, 10, 0, 0, 100, 20) and not point_in_box(50.1, 0, 0, 0, 100, 20)


# ---------------------------------------------------------------- sprites touching

def test_touches_is_what_it_always_was_for_plain_sprites():
    a = Sprite("A", 0, 0, 50)
    assert a.touches(Sprite("B", 39.9, 0, size=50))
    assert not a.touches(Sprite("B", 40, 0, 50))
    assert Sprite("x").size == 48 and a.shape == "circle"


def test_box_sprites_and_circle_sprites_touch_every_way_round():
    bat, ball = Sprite.box(0, 0, 100, 20), Sprite.circle(0, 0, 20)
    assert ball.radius == 10 and bat.shape == "box" and (bat.width, bat.height) == (100, 20)
    for x, want in ((59.9, True), (60, False)):
        other = Sprite.box(x, 0, 100, 20)
        assert ball.touches(other) is want and other.touches(ball) is want
    assert bat.touches(Sprite.box(99, 0, 100, 20)) and not bat.touches(Sprite.box(100, 0, 100, 20))
    tall = Sprite.box(0, 0, 100, 10)
    tall.angle = math.pi / 2
    assert Sprite.circle(0, 55, 20).touches(tall) and not tall.touches(Sprite.circle(40, 0, 20))
    assert tall.contains(0, 45) and not tall.contains(45, 0)


def test_any_sprite_can_be_a_box_and_its_width_follows_its_size_until_set():
    e = Sprite("E", 0, 0, 40)
    assert (e.width, e.height) == (40, 40)
    e.size = 60
    assert e.width == 60
    e.shape = "box"
    e.width, e.height = 200, 10
    assert e.touches(Sprite.box(104, 0, 10, 10)) and not e.touches(Sprite.box(106, 0, 10, 10))
    e.shape = "circle"
    assert e.touches(Sprite("B", 47.9, 0, 60)) and not e.touches(Sprite("B", 48, 0, 60))
    e.radius = 5
    assert e.touches(Sprite("B", 28.9, 0, 60)) and not e.touches(Sprite("B", 29, 0, 60))
    e.color = "red"
    assert e.colour == "red" == e.color


def test_size_nothing_and_hidden():
    a, box = Sprite("A", 0, 0, 50), Sprite.box(0, 0, 100, 20)
    assert not Sprite("z", 0, 0, 0).touches(Sprite("z", 0, 0, 0))
    assert not Sprite("z", 0, 0, 0).touches(box)
    assert Sprite.box(0, 0, 0, 0).touches(a) and Sprite.box(0, 0, 0, 0).touches(box)
    ghost = Sprite("g", 0, 0, 50)
    ghost.visible = False
    assert ghost.touches(a) and ghost.contains(0, 0)


def test_contains_a_point_or_anything_with_x_and_y():
    a = Sprite("A", 0, 0, 50)
    assert a.contains(0, 0) and a.contains(20, 0) and not a.contains(20.1, 0)
    assert a.contains(Sprite("p", 3, 3)) and a.contains(pyctures.mouse)


def test_hit_gives_the_first_one_touched_and_never_itself():
    a = Sprite("A", 0, 0, 50)
    rocks = [Sprite("r", 500, 0, 50), Sprite("r", 30, 0, 50), Sprite("r", 10, 30, 50)]
    assert a.hit(rocks) is rocks[1]
    assert rocks[1].hit(rocks) is rocks[2]
    assert Sprite("n", -500, 0, 5).hit(rocks) is None and a.hit([]) is None


def test_remove_while_looping_over_a_copy():
    rocks = [Sprite("r") for _ in range(4)]
    gone = rocks[1]
    assert remove(rocks, gone) and len(rocks) == 3
    assert remove(rocks, gone) is False and len(rocks) == 3
    seen = 0
    for rock in rocks[:]:
        seen += 1
        remove(rocks, rock)
    assert seen == 3 and rocks == []


# ---------------------------------------------------------------- moving

def test_update_moves_and_spins():
    s = Sprite("s", 0, 0, 10)
    s.vx, s.vy = 10, -20
    s.update(0.5)
    assert (s.x, s.y, s.angle) == (5, -10, 0)
    s.spin = 2
    s.update(0.5)
    assert s.angle == 1


def test_wrap_comes_back_on_the_other_side_once_it_has_all_gone():
    w = Sprite("w", -24.9, 50, 50)
    w.wrap()
    assert w.x == -24.9
    w.x = -25.1
    w.wrap()
    assert w.x == 425
    w.x, w.y = 426, 326
    w.wrap()
    assert (w.x, w.y) == (-25, -25)
    w.y = -26
    w.wrap()
    assert w.y == 325


def test_bounce_all_edges_or_the_ones_named():
    b = Sprite.circle(5, 50, 20)
    b.vx, b.vy = -100, 30
    assert b.bounce() == "left" and (b.x, b.vx) == (10, 100)
    assert b.bounce() is None
    b.x, b.vx = 5, 100            # already heading back in: never turned out again
    b.bounce()
    assert b.vx == 100
    b.x, b.vx = 400, 50
    assert b.bounce() == "right" and b.vx == -50
    b.y, b.vy = -3, -9
    assert b.bounce("left", "right") is None and b.vy == -9
    assert b.bounce("top", "bottom") == "top" and b.vy == 9
    b.y = 309
    assert b.bounce("bottom") == "bottom" and b.y == 290
    bat = Sprite.box(10, 50, 80, 16)
    bat.bounce()
    assert bat.x == 40


def test_offscreen_only_when_all_of_it_is_out():
    o = Sprite("o", -25.1, 0, 50)
    assert o.offscreen()
    o.x = -24
    assert not o.offscreen()
    o.x, o.y = 50, 326
    assert o.offscreen()


def test_push_forward_limit_and_aiming():
    s = Sprite("s", 0, 0, 10)
    s.push(10)
    assert (s.vx, s.vy) == pytest.approx((10, 0))
    s.angle = math.pi / 2
    s.push(5)
    assert s.vy == pytest.approx(5)
    s.forward(4)
    assert (s.x, s.y) == pytest.approx((0, 4))
    s.vx, s.vy = 30, 40
    s.limit(100)
    assert (s.vx, s.vy) == (30, 40)
    s.limit(5)
    assert (s.vx, s.vy) == pytest.approx((3, 4))
    z = Sprite("z", 0, 0, 10)
    z.limit(5)
    assert z.vx == 0
    assert z.angle_to(Sprite("t", 0, 10)) == pytest.approx(math.pi / 2)
    assert z.angle_to(-10, 0) == pytest.approx(math.pi)
    assert z.distance_to(3, 4) == 5 and z.distance_to(Sprite("t", 6, 8)) == 10


# ---------------------------------------------------------------- drawing

def calls(reply):
    return [(c[4], c[5]) for c in reply["cmds"] if c[0] == "call"]


def test_a_picture_can_be_a_function_given_ctx_and_the_size():
    r = start("""
        def arrow(ctx, size):
            ctx.fill_rect(0, 0, size, 2)
        s = Sprite(arrow, 10, 20, size=30)
        s.draw()
    """)
    assert r["error"] is None
    assert calls(r) == [("save", []), ("translate", [10, 20]), ("fill_rect", [0, 0, 30, 2]), ("restore", [])]


def test_a_picture_function_may_take_the_size_alone():
    """Drawn with the easy functions, round the sprite's own middle."""
    r = start("""
        def draw_ship(size):
            ctx.fill_rect(0, 0, size, 2)
        s = Sprite(draw_ship, 10, 20, size=30)
        s.draw()
        Sprite(lambda size: ctx.fill_rect(1, 1, size, 3), 0, 0, 8).draw()
    """)
    assert r["error"] is None
    assert calls(r) == [("save", []), ("translate", [10, 20]), ("fill_rect", [0, 0, 30, 2]), ("restore", []),
                        ("save", []), ("translate", [0, 0]), ("fill_rect", [1, 1, 8, 3]), ("restore", [])]


def test_every_other_picture_function_is_called_as_it_always_was():
    """One parameter: the size. Two, or any number: (ctx, size)."""
    r = start("""
        got = []
        def two(c, size): got.append(("two", c is ctx, size))
        def with_a_default(c, size=5): got.append(("default", c is ctx, size))
        def any_number(*args): got.append(("any", len(args)))
        def alone(size): got.append(("alone", size))
        def another_name(s): got.append(("another name", s))
        class Painter:
            def paint(self, size): got.append(("method", size))
            def old(self, c, size): got.append(("old method", size))
        for f in (two, with_a_default, any_number, alone, another_name, Painter().paint, Painter().old):
            Sprite(f, 0, 0, 30).draw()
        # A sprite whose picture is changed is asked again.
        s = Sprite(alone, 0, 0, 12)
        s.draw()
        s.picture = two
        s.draw()
        s.picture = alone
        s.draw()
        print(got)
    """)
    assert r["error"] is None, r["error"]
    assert r["out"].strip() == str([("two", True, 30), ("default", True, 30), ("any", 2), ("alone", 30), ("another name", 30),
                                    ("method", 30), ("old method", 30), ("alone", 12), ("two", True, 12), ("alone", 12)])


def test_a_box_and_a_circle_draw_their_own_shape_in_their_colour():
    r = start("""
        Sprite.box(50, 60, 40, 20, "red").draw()
        Sprite.circle(5, 6, 30, colour="blue").draw()
    """)
    assert r["error"] is None
    assert ("fillRect", [-20.0, -10.0, 40, 20]) in calls(r)
    assert ("arc", [0, 0, 15.0, 0, math.pi * 2]) in calls(r)
    assert [c[4] for c in r["cmds"] if c[0] == "set"] == ["red", "blue"]


def test_remove_is_ready_in_a_scene_without_an_import():
    r = start("""
        rocks = [Sprite("r"), Sprite("r")]
        for rock in rocks[:]:
            remove(rocks, rock)
        print(len(rocks))
    """)
    assert r["error"] is None and r["out"] == "0\n"
