"""Measure how smoothly a built scene plays, in headless Chromium.

    python scripts/measure_frames.py URL [--throttle 4] [--seconds 10]

Opens URL with ``?measure=1``, slows the CPU down by the given factor (as
Chrome's DevTools does, for the page and any workers it starts), skips the
first seconds while Python loads, then averages the scene's measure summary
over ``--seconds`` seconds. Needs Playwright (``pip install playwright``).
"""
import argparse
import json
import time

from playwright.sync_api import sync_playwright


def measure(url, rate=1, seconds=10, warmup=4, size=(800, 600), browser=None):
    own = browser is None
    pw = None
    if own:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(args=["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": size[0], "height": size[1]})
    if rate > 1:
        cdp = page.context.new_cdp_session(page)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": rate})
    sep = "&" if "?" in url else "?"
    page.goto(url + sep + "measure=1")
    end = time.time() + 90
    while time.time() < end:
        st = page.evaluate("() => (document.querySelector('[data-pyctures-src]') || {}).dataset?.pycturesStatus")
        if st in ("running", "error", "finished"):
            break
        page.wait_for_timeout(250)
    page.wait_for_timeout(warmup * 1000)
    samples = []
    last = None
    t_end = time.time() + seconds
    while time.time() < t_end:
        page.wait_for_timeout(1000)
        m = page.evaluate("() => window.__pycturesMeasure || null")
        if m and m != last:
            samples.append(m)
            last = m
    page.close()
    if own:
        browser.close()
        pw.stop()
    if not samples:
        return {"url": url, "throttle": rate, "error": "no measure summaries"}

    def avg(get):
        vals = [get(s) for s in samples if get(s) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None
    return {
        "url": url, "throttle": rate, "seconds": len(samples),
        "runtime": samples[-1].get("runtime"),
        "fps": avg(lambda s: s["fps"]),
        "missed_per_s": avg(lambda s: s["missedRefreshes"]),
        "python_ms": avg(lambda s: s["ms"].get("python")),
        "round_trip_ms": avg(lambda s: s["ms"].get("round_trip")),
        "draw_ms": avg(lambda s: s["ms"].get("draw_in_page")),
        "longest_refresh_ms": max(s.get("longestRefresh", 0) for s in samples),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--throttle", type=float, action="append", default=None)
    ap.add_argument("--seconds", type=int, default=10)
    a = ap.parse_args()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        for url in a.urls:
            for rate in a.throttle or [1]:
                print(json.dumps(measure(url, rate, a.seconds, browser=browser)), flush=True)
        browser.close()


if __name__ == "__main__":
    main()
