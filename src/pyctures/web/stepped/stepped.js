/**
 * STEPPED: a scene run one frame at a time, for a host that records it as a video.
 *
 * A recorder wants every frame exactly 1/fps after the last, however long Python and the drawing took, and the
 * sound in step with the pictures. This is loaded only by `mount(el, { src, stepped: { fps: 60 } })`, so a page
 * that is never recorded carries none of it. The scene then does not run by the screen's refreshes: it starts,
 * draws its first frame at time 0, and waits to be told.
 *
 *   const scene = mount(el, { src: 'game.py', stepped: { fps: 60 } })
 *   await scene.ready                      // the first frame is on the canvas
 *   await scene.step()                     // one frame: time moves on by 1/60, and the frame is drawn
 *   scene.sound.take()                     // { left, right, sampleRate, length }: the samples made since the last take
 *   await scene.sound.stepTo(frames / 60)  // the last frame lasts 1/60 too: its sound
 *
 * TIME. The scene's time is the recorder's, here and in Python: each frame says its time (`vt`, which the
 * runtime keeps in S.vt), so sound_time(), beat() and sleep() go by it.
 * SOUND is made by a player of the scene's own with no sound card (synths.js's createPlayer({ stepped })), on
 * this same clock: the sound keeper is given the clock and the player (its `host.clock` and `host.player`). The
 * sound up to a frame's time is made before Python is asked for the frame, so a note played in a frame begins on
 * that frame's first sample, and n frames are round(n × sampleRate / fps) samples. Nothing is heard.
 * A CHANGE OF SCENE moves on by one frame for each step, not by the screen's refreshes.
 */
export async function stepped(scene, given) {
  const fps = given.fps > 0 ? given.fps : 60, sampleRate = given.sampleRate || 48000
  const opt = scene.opt
  let time = 0, frame = 0, player = null
  scene.stepping = { fps, sampleRate }

  // The sound keeper's clock is this one, and its player a stepped one for this scene alone.
  const host = opt.sound || {}
  opt.sound = {
    ...host,
    clock: () => time,
    player: (synths) => (player = synths.createPlayer({ ...(host.wasm ? { wasm: host.wasm } : {}), stepped: { fps, sampleRate } })),
  }
  // Python is told that its time begins at 0.
  const told = (transport) => {
    const start = transport.start.bind(transport)
    transport.start = (source, info, stored) => start(source, { ...info, vt: 0 }, stored)
    return transport
  }
  if (opt.makeTransport) { const make = opt.makeTransport; opt.makeTransport = () => told(make()) } else if (opt.transport) told(opt.transport)
  // The screen asks for nothing: no frame loop, and nothing paused when the scene is out of view.
  scene.loop = scene.requestFrame = scene.resume = scene.hush = () => {}

  await scene.start()
  // The first frame is drawn on a refresh, as any is; every one after it at once, so the canvas can be copied.
  while (scene.renderer && scene.renderer.waiting) await new Promise((done) => requestAnimationFrame(done))
  if (scene.renderer) { const renderer = scene.renderer, push = renderer.push; renderer.push = (cmds, at) => push(cmds, at, true) }
  if (scene.sound) {
    /** The clock now reads `seconds`: a promise of the sound up to there having been made. */
    scene.sound.stepTo = (seconds) => { time = seconds; return player ? player.stepped.advance(seconds) : Promise.resolve(0) }
    /** The samples made since the last take, { left, right, sampleRate, length }, or null when the scene has made no sound. */
    scene.sound.take = () => (player ? player.stepped.take() : null)
  }

  /** One frame. It gives { frame, time, running }: `running` is false once the scene has ended or failed. */
  scene.step = async () => {
    const r = scene.r, token = r.token
    const at = ++frame / fps
    let running = false
    // The sound up to this frame first: what Python reads back of it with this frame is this frame's.
    if (scene.sound) await scene.sound.stepTo(at)
    else time = at
    if (token !== r.token || !r.live) return { frame, time: at, running }
    if (scene.sound) scene.sound.frame()
    const payload = { dt: 1 / fps, vt: at, events: r.events, reads: r.reads, ...r.size, measure: false }
    r.events = []
    r.reads = {}
    r.busy = true
    r.busySince = performance.now()
    try {
      const text = await scene.transport.tick(payload)
      if (token !== r.token) return { frame, time: at, running }
      r.busy = false
      if (r.warnedStuck) scene.unstuck()
      running = scene.handleReply(JSON.parse(text), token)
      if (scene.stage) scene.stage.step(1 / fps)
    } catch (error) {
      if (token !== r.token) return { frame, time: at, running }
      r.busy = r.live = false
      const msg = String((error && error.message) || error)
      scene.log('err', msg)
      scene.showError(msg, 0)
      scene.setStatus('error')
    }
    return { frame, time: at, running }
  }
}
