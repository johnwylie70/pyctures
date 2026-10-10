"""The Python half: the command protocol it records, and how runs behave."""
import json
import textwrap

import pytest

import pyctures

INFO = json.dumps({"width": 400, "height": 300, "pixel_ratio": 2})
H_WINDOW, H_CANVAS, H_THREE, H_CTX = 1, 2, 3, 4


def start(src):
    return json.loads(pyctures.start(textwrap.dedent(src), INFO))


def tick(**payload):
    payload.setdefault("dt", 1 / 60)
    return json.loads(pyctures.tick(json.dumps(payload)))


def cmds(reply, kind=None):
    return [c for c in reply["cmds"] if kind is None or c[0] == kind]


@pytest.fixture(autouse=True)
def stopped():
    yield
    pyctures.stop()


# ---------------------------------------------------------------- commands

def test_call_records_one_command_with_the_user_line():
    r = start("""
        x = 1
        ctx.fill_rect(0, 0, 10, 20)
    """)
    assert r["error"] is None
    [c] = cmds(r, "call")
    kind, line, new_h, obj_h, name, args = c
    assert (line, obj_h, name, args) == (3, H_CTX, "fill_rect", [0, 0, 10, 20])
    # an unused result needs no handle
    assert new_h == 0


def test_snake_case_names_are_sent_as_written():
    # the browser half maps fill_style -> fillStyle (tested in test_browser.py)
    r = start('ctx.fill_style = "red"\nctx.fillStyle = "blue"')
    sets = cmds(r, "set")
    assert [s[3] for s in sets] == ["fill_style", "fillStyle"]
    assert [s[4] for s in sets] == ["red", "blue"]


def test_handles_are_pipelined_in_the_same_frame():
    r = start("""
        g = canvas.getContext("2d")
        g.fill_rect(1, 2, 3, 4)
    """)
    first, second = cmds(r, "call")
    assert first[3] == H_CANVAS and first[4] == "getContext"
    handle = first[2]
    assert handle > 1000
    assert second[3] == handle


def test_capitalised_names_construct_and_keywords_become_options():
    r = start("""
        geo = THREE.BoxGeometry(1, 2, 3)
        mat = THREE.MeshStandardMaterial(color=0xff0000, roughness=0.5)
        mesh = THREE.Mesh(geo, mat)
        scene = THREE.Scene()
        scene.add(mesh)
    """)
    news = cmds(r, "new")
    assert [n[4] for n in news] == ["BoxGeometry", "MeshStandardMaterial", "Mesh", "Scene"]
    assert all(n[3] == H_THREE for n in news)
    assert news[1][5] == [{"$d": {"color": 0xff0000, "roughness": 0.5}}]
    geo_h, mat_h, mesh_h = news[0][2], news[1][2], news[2][2]
    assert news[2][5] == [{"$h": geo_h}, {"$h": mat_h}]
    [add] = cmds(r, "call")
    assert add[4] == "add" and add[5] == [{"$h": mesh_h}]


def test_lazy_members_become_get_commands_when_used():
    r = start("camera = THREE.PerspectiveCamera(50, 1, 0.1, 100)\ncamera.position.set(0, 1, 2)")
    [new] = cmds(r, "new")
    [get] = cmds(r, "get")
    assert get[3] == new[2] and get[4] == "position"
    [call] = cmds(r, "call")
    assert call[3] == get[2] and call[4] == "set" and call[5] == [0, 1, 2]


def test_deferred_maths_is_sent_as_an_expression():
    r = start("""
        mesh = THREE.Mesh()
        mesh.rotation.y += 0.5
    """)
    s = cmds(r, "set")[-1]
    assert s[3] == "y"
    expr = s[4]["$e"]
    assert expr[0] == "+"
    assert expr[1][0] == "get" and expr[1][2] == "y"
    assert expr[2] == ["v", 0.5]


def test_reversed_and_chained_maths():
    r = start("""
        light = THREE.PointLight()
        light.intensity = 2 * light.intensity - 1
    """)
    expr = cmds(r, "set")[-1][4]["$e"]
    assert expr[0] == "-" and expr[2] == ["v", 1]
    assert expr[1][0] == "*" and expr[1][1] == ["v", 2]


def test_a_value_set_from_python_reads_back_without_a_round_trip():
    r = start("""
        ctx.line_width = 3
        print(ctx.line_width * 2)
    """)
    assert r["out"] == "6\n"
    assert not cmds(r, "read")


def test_values_encode_lists_dicts_nan_and_tolist():
    r = start("""
        class Arr:
            def tolist(self):
                return [1, 2, 3]
        js.f(Arr(), {"a": [1, None]}, float("nan"), float("inf"), (4, 5), True)
    """)
    [c] = cmds(r, "call")
    assert c[5] == [[1, 2, 3], {"$d": {"a": [1, None]}}, {"$e": ["num", "NaN"]},
                    {"$e": ["num", "Infinity"]}, [4, 5], True]


def test_comparing_a_page_value_says_to_await_it():
    r = start("""
        mesh = THREE.Mesh()
        if mesh.position.x > 3:
            pass
    """)
    assert "await" in r["error"]
    assert r["errorLine"] == 3


# ---------------------------------------------------------------- reads

def test_await_reads_a_value_back_at_the_end_of_the_frame():
    r = start("""
        ctx.font = "20px sans-serif"
        w = await ctx.measure_text("hello").width
        print("width", w)
    """)
    [read] = cmds(r, "read")
    rid = read[2]
    assert read[1] == 3
    assert read[3]["$e"][0] == "get" and read[3]["$e"][2] == "width"
    assert r["running"] is True and r["out"] == ""
    r = tick(reads={str(rid): 42.5})
    assert r["out"] == "width 42.5\n"
    assert r["running"] is False


def test_async_draw_is_not_called_again_while_it_waits():
    start("""
        n = 0
        async def draw():
            global n
            n += 1
            v = await js.innerWidth
            print("got", v, n)
    """)
    r = tick()
    assert not cmds(r, "read")       # the first draw's read went out in start()
    r = tick(reads={"1": 640})
    assert r["out"] == "got 640 1\n"


# ---------------------------------------------------------------- frames, input and callbacks

def test_draw_runs_every_frame_with_size_names_and_dt():
    r = start("""
        frames = []
        def update(dt):
            frames.append(round(dt, 3))
        def draw():
            ctx.fill_rect(0, 0, width, height)
    """)
    assert r["running"] is True
    assert cmds(r, "call")[0][5] == [0, 0, 400, 300]
    r = tick(dt=0.5, width=800, height=600)
    assert cmds(r, "call")[0][5] == [0, 0, 800, 600]
    assert pyctures.S.ns["frames"] == [0.0, 0.5]


def test_await_frame_loop_sends_one_frame_per_pass():
    r = start("""
        i = 0
        while i < 3:
            ctx.fill_rect(i, 0, 1, 1)
            i += 1
            await frame()
    """)
    assert len(cmds(r, "call")) == 1 and r["running"]
    r = tick()
    assert len(cmds(r, "call")) == 1 and r["running"]
    tick()
    r = tick()
    assert r["running"] is False


def test_keys_mouse_and_on_functions():
    start("""
        log = []
        def on_key_down(k): log.append(("down", k))
        def on_key_up(k): log.append(("up", k))
        def on_mouse_down(x, y): log.append(("press", x, y))
        def draw(): pass
    """)
    tick(events=[{"k": "input", "e": {"type": "keydown", "key": "ArrowLeft"}},
                 {"k": "input", "e": {"type": "pointerdown", "x": 5, "y": 6}}])
    assert "ArrowLeft" in pyctures.keys
    assert pyctures.mouse.down and (pyctures.mouse.x, pyctures.mouse.y) == (5, 6)
    tick(events=[{"k": "input", "e": {"type": "keyup", "key": "ArrowLeft"}},
                 {"k": "input", "e": {"type": "pointerup", "x": 5, "y": 6}}])
    assert not pyctures.keys and not pyctures.mouse.down
    assert pyctures.S.ns["log"] == [("down", "ArrowLeft"), ("press", 5, 6), ("up", "ArrowLeft")]


def inp(type, **e):
    return {"k": "input", "e": dict(e, type=type)}


def test_touches_are_every_pointer_down_and_mouse_follows_the_first():
    start("""
        log = []
        def on_mouse_down(x, y, button): log.append(("md", x, y, button))
        def on_mouse_move(x, y): log.append(("mm", x, y))
        def on_mouse_up(x, y, button): log.append(("mu", x, y, button))
        def on_touch_start(t): log.append(("ts", t.id, t.x, t.y, t.type))
        def on_touch_move(t): log.append(("tm", t.id, t.x, t.y))
        def on_touch_end(t, cancelled): log.append(("te", t.id, t.x, t.y, cancelled))
        def draw(): pass
    """)
    log = pyctures.S.ns["log"]
    t, m = pyctures.touches, pyctures.mouse
    tick(events=[inp("pointerdown", id=7, pt="touch", x=100, y=50, button=0),
                 inp("pointerdown", id=8, pt="touch", x=300, y=50, button=0)])
    assert [(a.id, a.x, a.y, a.start_x, a.type) for a in t] == [(7, 100, 50, 100, "touch"), (8, 300, 50, 300, "touch")]
    assert (m.x, m.y, m.down, m.button, m.inside) == (100, 50, True, "left", True)
    assert (m.dx, m.dy) == (0, 0)   # a finger going down is not a movement
    assert log == [("md", 100, 50, "left"), ("ts", 7, 100, 50, "touch"), ("ts", 8, 300, 50, "touch")]
    del log[:]
    tick(events=[inp("pointermove", id=8, pt="touch", x=310, y=70),
                 inp("pointermove", id=8, pt="touch", x=320, y=80),
                 inp("pointermove", id=7, pt="touch", x=90, y=50)])
    assert (t[1].dx, t[1].dy, t[1].x, t[1].start_x) == (20, 30, 320, 300)
    assert (t[0].dx, m.dx, m.x) == (-10, -10, 90)   # the mouse follows the first finger only
    assert [e[0] for e in log] == ["tm", "tm", "mm", "tm"]
    tick()
    assert (t[1].dx, t[1].dy, m.dx) == (0, 0, 0)   # what happened last frame is cleared
    del log[:]
    first = t[0]
    tick(events=[inp("pointerup", id=7, pt="touch", x=90, y=55),
                 inp("pointercancel", id=8, pt="touch", x=320, y=80),
                 inp("pointerleave")])
    assert t == [] and not m.down and m.button is None and not m.inside
    assert log == [("mu", 90, 55, "left"), ("te", 7, 90, 55, False), ("te", 8, 320, 80, True)]
    assert "touch(id=7" in repr(first)


def test_mouse_buttons_movement_wheel_and_inside():
    start("""
        wheel = []
        def on_wheel(amount): wheel.append(amount)
        def draw(): pass
    """)
    m = pyctures.mouse
    tick(events=[inp("pointermove", id=1, pt="mouse", x=10, y=10)])
    assert (m.x, m.dx, m.inside) == (10, 0, True)   # its first place is not a movement
    tick(events=[inp("pointermove", id=1, pt="mouse", x=25, y=4)])
    assert (m.dx, m.dy) == (15, -6)
    for number, name in ((0, "left"), (1, "middle"), (2, "right")):
        tick(events=[inp("pointerdown", id=1, pt="mouse", x=25, y=4, button=number)])
        assert m.down and m.button == name and len(pyctures.touches) == 1
        tick(events=[inp("pointerup", id=1, pt="mouse", x=25, y=4, button=number)])
        assert not m.down and m.button is None and pyctures.touches == []
    tick(events=[inp("wheel", amount=120), inp("wheel", amount=-20)])
    assert m.wheel == 100 and pyctures.S.ns["wheel"] == [120, -20]
    assert repr(m) == "mouse(x=25, y=4, down=False, button=None, inside=True, dx=0, dy=0, wheel=100)"
    tick()
    assert m.wheel == 0
    tick(events=[inp("pointermove", id=1, pt="mouse", x=900, y=4)])
    assert not m.inside   # a drag that left the scene (it is 400 wide)


def test_pinch_from_two_fingers_and_from_a_trackpad():
    start("""
        log = []
        def on_pinch(scale, change): log.append((round(scale, 3), round(change, 3)))
        def draw(): pass
    """)
    log, pinch = pyctures.S.ns["log"], pyctures.pinch
    tick(events=[inp("pointerdown", id=1, pt="touch", x=100, y=100), inp("pointerdown", id=2, pt="touch", x=300, y=100)])
    assert pinch.scale == 1
    tick(events=[inp("pointermove", id=2, pt="touch", x=400, y=100)])
    assert (pinch.scale, pinch.change, pinch.x, pinch.y) == (1.5, 1.5, 250, 100)
    tick(events=[inp("pointermove", id=1, pt="touch", x=200, y=100)])
    assert (pinch.scale, round(pinch.change, 3)) == (1.0, 0.667)
    assert log == [(1.5, 1.5), (1.0, 0.667)]
    tick()
    assert pinch.change == 1
    tick(events=[inp("pointerup", id=2, pt="touch", x=400, y=100)])
    assert pinch.scale == 1 and "pinch(scale=1" in repr(pinch)
    tick(events=[inp("pointerup", id=1, pt="touch", x=200, y=100)])
    # A trackpad: the page sends each step's change.
    del log[:]
    tick(events=[inp("pinch", change=1.1, x=5, y=6), inp("pinch", change=1.1, x=5, y=6)])
    assert (round(pinch.scale, 2), round(pinch.change, 2), pinch.x) == (1.21, 1.21, 5)
    assert log == [(1.1, 1.1), (1.21, 1.1)]
    pyctures._in.pinched_at -= 1   # as if a quarter of a second had passed
    tick()
    assert pinch.scale == 1 and pinch.change == 1


def test_pressed_released_modifiers_codes_and_the_shift_fix():
    start("""
        log = []
        def on_key_down(key, code): log.append(("down", key, code))
        def on_key_up(key): log.append(("up", key))
        def on_key_repeat(key, code): repeats.append(key)
        repeats = []
        def draw(): pass
    """)
    log, keys = pyctures.S.ns["log"], pyctures.keys
    tick(events=[inp("keydown", key="Shift", code="ShiftLeft", m=1), inp("keydown", key="A", code="KeyA", m=1)])
    assert keys == {"Shift", "A"} and keys.shift and not keys.ctrl
    assert keys.codes == {"ShiftLeft", "KeyA"} and pyctures.pressed == {"Shift", "A"}
    assert repr(keys) == "keys({'A', 'Shift'}, shift=True)"
    tick(events=[inp("keydown", key="A", code="KeyA", m=1, r=1)])   # the keyboard repeating
    assert pyctures.pressed == set() and len(log) == 2 and pyctures.S.ns["repeats"] == ["A"]
    # Shift let go first: the page now calls the key "a", and "A" is what must come out.
    tick(events=[inp("keyup", key="Shift", code="ShiftLeft", m=0), inp("keyup", key="a", code="KeyA", m=0)])
    assert keys == set() and keys.codes == set() and not keys.shift
    assert pyctures.released == {"Shift", "A"}
    assert log == [("down", "Shift", "ShiftLeft"), ("down", "A", "KeyA"), ("up", "Shift"), ("up", "A")]
    tick()
    assert pyctures.released == set() and repr(keys) == "keys()"
    # Two keys with one name: it stays while either is held.
    tick(events=[inp("keydown", key="Shift", code="ShiftLeft", m=1), inp("keydown", key="Shift", code="ShiftRight", m=1),
                 inp("keyup", key="Shift", code="ShiftLeft", m=1)])
    assert keys == {"Shift"} and keys.codes == {"ShiftRight"}
    tick(events=[inp("keydown", key="b", code="KeyB", m=10), inp("blur")])
    assert keys == set() and keys.codes == set() and not keys.ctrl and not keys.meta


def test_a_loop_with_await_frame_sees_what_happened_once():
    start("""
        seen = []
        while True:
            await frame()
            seen.append((sorted(pressed), mouse.wheel))
    """)
    tick()
    tick(events=[inp("keydown", key="x", code="KeyX", m=0), inp("wheel", amount=3)])
    tick()
    assert pyctures.S.ns["seen"][-2:] == [(["x"], 3), ([], 0)]


def test_vsync_is_another_name_for_frame():
    start("""
        n = 0
        while True:
            await vsync()
            n += 1
    """)
    tick()
    tick()
    assert pyctures.S.ns["n"] == 2 and pyctures.vsync is pyctures.frame


def test_names_the_file_makes_its_own_are_its_own():
    r = start("""
        pressed = False
        touches = 3
        def draw(): pass
    """)
    assert r["error"] is None and pyctures.S.ns["touches"] == 3 and pyctures.touches == []


def test_callbacks_come_back_as_events():
    r = start("""
        seen = []
        def clicked(event):
            seen.append((event.type, event.x, event["y"]))
        canvas.add_event_listener("click", clicked)
    """)
    [call] = cmds(r, "call")
    cb = call[5][1]["$cb"]
    assert r["running"] is True       # a live callback keeps the program running
    tick(events=[{"k": "cb", "id": cb, "e": {"type": "click", "x": 1, "y": 2}}])
    assert pyctures.S.ns["seen"] == [("click", 1, 2)]


def test_sprite_and_text_picture_are_drawn_with_ctx():
    r = start("""
        s = Sprite("*", 10, 20, size=30)
        s.vx = 60
        s.update(0.5)
        s.draw()
        print(s.x)
    """)
    assert r["out"] == "40.0\n"
    names = [c[4] for c in cmds(r, "call")]
    assert "createElement" in names and "drawImage" in names


# ---------------------------------------------------------------- errors

def test_runtime_error_reports_the_users_line_and_text():
    r = start("""
        a = 1
        def draw():
            return 1 / 0
    """)
    assert r["errorLine"] == 4
    assert "ZeroDivisionError" in r["error"]
    assert "return 1 / 0" in r["error"]
    assert r["running"] is False


def test_syntax_error_reports_its_line():
    r = start("x = 1\ny = (\nprint('never')\nz = = 2\n")
    assert r["errorLine"] >= 2
    assert "SyntaxError" in r["error"]


def test_error_in_a_later_frame():
    start("""
        n = 0
        def update(dt):
            global n
            n += 1
            if n == 3:   # start() runs update once, then each tick
                raise ValueError("boom")
    """)
    assert tick()["error"] is None
    r = tick()
    assert r["errorLine"] == 7 and "ValueError: boom" in r["error"]
    assert tick()["error"] == "Nothing is running"


def test_print_goes_to_out_and_stderr_to_err():
    r = start("import sys\nprint('hi')\nprint('oops', file=sys.stderr)")
    assert r["out"] == "hi\n" and r["err"] == "oops\n"


# ---------------------------------------------------------------- stop and restart

def test_stop_then_tick_says_nothing_is_running():
    start("def draw(): pass")
    assert pyctures.stop() == "stopped"
    assert tick()["error"] == "Nothing is running"


def test_each_run_gets_fresh_root_names_and_input_state():
    start("""
        doc = js.document
        def draw(): pass
    """)
    old_js = pyctures.js
    tick(events=[{"k": "input", "e": {"type": "keydown", "key": "a"}}])
    assert "a" in pyctures.keys
    r = start("""
        js.document.title = "two"
    """)
    assert pyctures.js is not old_js
    assert not pyctures.keys
    # The new run looks js.document up again: nothing from the old run is reused.
    [get] = cmds(r, "get")
    assert get[3] == H_WINDOW and get[4] == "document"


def test_handles_never_repeat_across_runs():
    r1 = start("a = THREE.Scene()")
    r2 = start("b = THREE.Scene()")
    assert cmds(r2, "new")[0][2] > cmds(r1, "new")[0][2]


def test_a_new_run_does_not_receive_the_old_runs_commands():
    start("def draw(): ctx.fill_rect(0, 0, 1, 1)")
    r = start("x = 1")
    assert r["cmds"] == [] or all(c[0] == "free" for c in r["cmds"])


def test_from_pyctures_import_star_works():
    r = start("""
        from pyctures import *
        ctx.fill_rect(0, 0, 1, 1)
    """)
    assert r["error"] is None and len(cmds(r, "call")) == 1
