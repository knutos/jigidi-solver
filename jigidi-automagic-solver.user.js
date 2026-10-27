// ==UserScript==
// @name         Jigidi Automagic Solver
// @namespace    https://github.com/knutos/jigidi-solver
// @version      1.8.1
// @description  Solves Jigidi puzzles automatically: pieces are dragged into place one by one.
// @author       Knut Olav Sunde
// @match        https://www.jigidi.com/solve/*
// @match        https://www.jigidi.com/*/solve/*
// @match        https://www.jigidi.com/solve.php*
// @match        https://knutos.github.io/jigidi-solver/*
// @run-at       document-start
// @license      MIT
// @grant        none
// @inject-into  page
// @homepageURL  https://knutos.github.io/jigidi-solver/
// @supportURL   https://github.com/knutos/jigidi-solver/issues
// @downloadURL  https://knutos.github.io/jigidi-solver/jigidi-automagic-solver.user.js
// @updateURL    https://knutos.github.io/jigidi-solver/jigidi-automagic-solver.meta.js
// ==/UserScript==

// Based on "Jigidi Auto Solver" by WorlockM (MIT). https://github.com/WorlockM/jigidi-auto-solver

// On the install page this script only reports its version (so the page can offer updates).
const JAS_VERSION = '1.8.1';
const JAS_SITE = location.hostname === 'knutos.github.io';
if (JAS_SITE) {
  const v = (typeof GM_info === 'object' && GM_info && GM_info.script && GM_info.script.version) || JAS_VERSION;
  const mark = () => {
    document.documentElement.setAttribute('data-jas-installed', v);
    window.dispatchEvent(new CustomEvent('jas-installed', { detail: v }));
  };
  // At document-start the <html> element may not exist yet.
  if (document.documentElement) mark(); else document.addEventListener('DOMContentLoaded', mark, { once: true });
}

// Core hooks: must run before Jigidi's game script (document-start).
(function () {
  if (JAS_SITE) return;
  const W = window;
  const S = (W.__jas = {
    n: -1,             // index of the last piece rendered on the scratch canvas
    scratch: null,     // scratch canvas Jigidi uses to cut every piece
    piece: new Map(),  // piece canvas -> piece index (row-major solution order)
    off: [],           // piece index -> [sx, sy] source-image offset used when cutting
    pos: new Map(),    // piece index -> last draw {x, y, s, cx, cy, tick}
    L: [],             // captured pointer listeners
    Lv: 0,             // bumped whenever L changes (handler cache key)
    drawTick: 0,       // increments on every piece draw (later draw = higher in z-order)
    moveTick: 0,       // drawTick of the last draw that actually moved a piece
  });

  // If page scripts already ran before us, listeners they registered can't be captured.
  S.late = document.readyState !== 'loading';
  if (S.late) console.info('[Automagic Solver] injected late (readyState ' + document.readyState + ')');

  const RE = /^(mouse|touch|pointer|wheel|click|dblclick)/;
  const cap = (o) => (o && typeof o === 'object' ? !!o.capture : !!o);
  const oAdd = EventTarget.prototype.addEventListener;
  // Hook addEventListener in a realm (this window, or an iframe's window that a page could use
  // to get an unhooked copy of addEventListener).
  function hookRealm(w) {
    const ET = w.EventTarget.prototype;
    if (ET.__jas) return;
    const add = ET.addEventListener, rem = ET.removeEventListener;
    Object.defineProperty(ET, '__jas', { value: true });
    ET.addEventListener = function (t, f, o) {
      if (RE.test(t) && f) { S.L.push({ target: this, t, f, o }); S.Lv++; }
      return add.call(this, t, f, o);
    };
    ET.removeEventListener = function (t, f, o) {
      const n = S.L.length;
      S.L = S.L.filter((l) => !(l.target === this && l.t === t && l.f === f && cap(l.o) === cap(o)));
      if (S.L.length !== n) S.Lv++;
      return rem.call(this, t, f, o);
    };
  }
  hookRealm(W);
  for (const [proto, prop, toWin] of [[HTMLIFrameElement.prototype, 'contentWindow', (v) => v],
    [HTMLIFrameElement.prototype, 'contentDocument', (v) => v && v.defaultView]]) {
    const d = Object.getOwnPropertyDescriptor(proto, prop);
    if (!d || !d.get) continue;
    Object.defineProperty(proto, prop, Object.assign({}, d, {
      get() { const v = d.get.call(this); try { const w = toWin(v); if (w) hookRealm(w); } catch (e) { /* cross-origin */ } return v; },
    }));
  }

  // While solving, keep the user's real input away from the game (the panel stays usable).
  const block = (e) => {
    if (S.busy && e.isTrusted && !(e.target.closest && e.target.closest('#jas-panel'))) e.stopImmediatePropagation();
  };
  for (const t of ['mousedown', 'mousemove', 'mouseup', 'pointerdown', 'pointermove', 'pointerup', 'pointercancel',
    'touchstart', 'touchmove', 'touchend', 'touchcancel', 'wheel']) oAdd.call(W, t, block, true);

  // Some Jigidi builds use pointer events and call setPointerCapture(e.pointerId). For our synthetic
  // pointer there is no real active pointer, so the browser would throw; emulate capture instead.
  S.pid = 1; S.synth = false; S.cap = null;
  const EP = Element.prototype, oSet = EP.setPointerCapture, oRel = EP.releasePointerCapture, oHas = EP.hasPointerCapture;
  EP.setPointerCapture = function (id) { if (S.synth && id === S.pid) { S.cap = this; return; } return oSet.call(this, id); };
  EP.releasePointerCapture = function (id) { if (S.synth && id === S.pid) { if (S.cap === this) S.cap = null; return; } return oRel.call(this, id); };
  EP.hasPointerCapture = function (id) { return S.synth && id === S.pid ? S.cap === this : oHas.call(this, id); };

  const P = CanvasRenderingContext2D.prototype;
  const oPut = P.putImageData, oDraw = P.drawImage;
  P.putImageData = function (...a) {
    if (this.canvas.width > 10) { S.n++; S.scratch = this.canvas; }
    return oPut.apply(this, a);
  };
  P.drawImage = function (src, ...a) {
    const dst = this.canvas;
    if (S.n >= 0 && dst === S.scratch && src !== dst && S.off[S.n] === undefined && a.length === 2) {
      S.off[S.n] = [a[0], a[1]];
    } else if (src === S.scratch && dst !== src && !S.piece.has(dst)) {
      S.piece.set(dst, S.n);
    } else if (dst.isConnected && S.piece.has(src)) {
      const t = this.getTransform(), i = S.piece.get(src);
      let dx, dy, dw, dh;
      if (a.length >= 8) { dx = a[4]; dy = a[5]; dw = a[6]; dh = a[7]; }
      else { dx = a[0] || 0; dy = a[1] || 0; dw = a.length >= 4 ? a[2] : src.width; dh = a.length >= 4 ? a[3] : src.height; }
      const mx = dx + dw / 2, my = dy + dh / 2;
      const o = S.pos.get(i);
      if (!o || Math.abs(o.x - t.e) + Math.abs(o.y - t.f) > 0.01 || o.s !== t.a) S.moveTick = S.drawTick + 1;
      // cx/cy: on-screen centre of the piece image, i.e. the middle of its solid body.
      S.pos.set(i, { x: t.e, y: t.f, s: t.a, cx: t.e + t.a * mx + t.c * my, cy: t.f + t.b * mx + t.d * my, tick: ++S.drawTick });
    }
    return oDraw.call(this, src, ...a);
  };
})();

// Solver
(function () {
  if (JAS_SITE) return;
  const S = window.__jas;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  // One rendered frame; falls back to a timer when the tab is hidden (rAF paused).
  const frame = () => new Promise((r) => { let d = 0; const f = () => { if (!d) { d = 1; r(); } }; requestAnimationFrame(f); setTimeout(f, 60); });

  let board = null;
  const canvas = () => (board && board.isConnected ? board
    : (board = [...document.querySelectorAll('canvas')].find((c) => c.isConnected && c.width > 200)));

  function trusted(type, x, y, buttons, target) {
    const e = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, screenX: x, screenY: y, button: 0, buttons, view: window });
    return new Proxy(e, {
      get(t, k) {
        if (k === 'isTrusted') return true;
        if (k === 'target' || k === 'currentTarget' || k === 'srcElement') return target;
        const v = Reflect.get(t, k);
        return typeof v === 'function' ? v.bind(t) : v;
      },
    });
  }

  // Handler lists are cached until the game adds/removes a listener.
  let hv = -1, hc = {};
  const DOC = (t) => t === document, WIN = (t) => t === window, CAN = (t) => t === canvas();
  function fire(key, type, x, y, buttons, pred) {
    if (hv !== S.Lv) { hc = {}; hv = S.Lv; }
    const ls = hc[key] || (hc[key] = S.L.filter((l) => l.t === type && pred(l.target)));
    const c = canvas();
    for (const l of ls) l.f.call(l.target, trusted(type, x, y, buttons, c));
  }

  // Pointer mode: a small event dispatcher that mimics the browser (hit test, capture/target/bubble
  // phases, stopPropagation, pointer capture), for builds that listen to pointer events on a wrapper.
  const capOf = (o) => (o && typeof o === 'object' ? !!o.capture : !!o);
  // Listeners that belong to the solver's own panel are not the game's.
  const own = (t) => !!(t && t.getRootNode && ((t.id === 'jas-panel') || (t.getRootNode().host || {}).id === 'jas-panel'));
  function hitAt(x, y) {
    for (const el of document.elementsFromPoint(x, y)) if (el.id !== 'jas-panel') return el;
    return canvas();
  }
  function synth(type, x, y, buttons, target, path, st, cur, extra) {
    const init = Object.assign({ bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, screenX: x, screenY: y,
      button: /move|wheel/.test(type) ? (type === 'wheel' ? 0 : -1) : 0, buttons, view: window, pointerId: S.pid,
      pointerType: 'mouse', isPrimary: true, pressure: buttons ? 0.5 : 0, width: 1, height: 1 }, extra);
    const e = type.startsWith('pointer') ? new PointerEvent(type, init) : type === 'wheel' ? new WheelEvent(type, init) : new MouseEvent(type, init);
    const px = new Proxy(e, {
      get(t, k) {
        switch (k) {
          case 'isTrusted': return true;
          case 'target': case 'srcElement': return target;
          case 'currentTarget': return cur.el;
          case 'eventPhase': return cur.phase;
          case 'offsetX': case 'offsetY': case 'layerX': case 'layerY': {
            const r = target.getBoundingClientRect ? target.getBoundingClientRect() : { left: 0, top: 0 };
            return k.endsWith('X') ? x - r.left : y - r.top;
          }
          case 'stopPropagation': return () => { st.stop = true; };
          case 'stopImmediatePropagation': return () => { st.stop = st.imm = true; };
          case 'getCoalescedEvents': return () => [px];
          case 'getPredictedEvents': return () => [];
          case 'composedPath': return () => path.slice();
        }
        const v = Reflect.get(t, k);
        return typeof v === 'function' ? v.bind(t) : v;
      },
    });
    return px;
  }
  function dispatch(type, x, y, buttons, extra, forceTarget) {
    const target = forceTarget || (S.cap && S.cap.isConnected ? S.cap : hitAt(x, y));
    const path = [];
    for (let n = target; n; n = n.parentNode) path.push(n);
    path.push(window);
    const ls = S.L.filter((l) => l.t === type && !own(l.target));
    const st = { stop: false, imm: false }, cur = { el: null, phase: 0 };
    const ev = synth(type, x, y, buttons, target, path, st, cur, extra);
    const run = (node, phase, filter) => {
      cur.el = node; cur.phase = phase;
      for (const l of ls) {
        if (l.target !== node || !filter(l)) continue;
        try { typeof l.f === 'function' ? l.f.call(node, ev) : l.f.handleEvent(ev); } catch (err) { console.error(err); }
        if (st.imm) return;
      }
      // onpointerdown = ... style handlers (bubble/target phase only)
      const h = phase !== 1 && node['on' + type];
      if (typeof h === 'function') { try { h.call(node, ev); } catch (err) { console.error(err); } }
    };
    S.synth = true;
    try {
      for (let i = path.length - 1; i >= 1 && !st.stop; i--) run(path[i], 1, (l) => capOf(l.o));
      if (!st.stop) run(path[0], 2, () => true);
      for (let i = 1; i < path.length && !st.stop; i++) run(path[i], 3, (l) => !capOf(l.o));
    } finally { S.synth = false; }
  }
  // 'native': real (untrusted) events through dispatchEvent. Works whatever way the game registered
  // its handlers, as long as it doesn't insist on isTrusted. Pointer events first, then the
  // compatibility mouse events a browser would send (unless pointerdown was cancelled).
  function nativeEvent(type, x, y, buttons, target) {
    const init = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, screenX: x, screenY: y,
      button: /move/.test(type) ? (type.startsWith('pointer') ? -1 : 0) : 0, buttons, view: window, pointerId: S.pid,
      pointerType: 'mouse', isPrimary: true, pressure: buttons ? 0.5 : 0, width: 1, height: 1 };
    const e = type.startsWith('pointer') ? new PointerEvent(type, init) : new MouseEvent(type, init);
    S.synth = true;
    try { target.dispatchEvent(e); } finally { S.synth = false; }
    return e.defaultPrevented;
  }
  let compat = true;
  function nat(kind, x, y, buttons) {
    const t = S.cap && S.cap.isConnected ? S.cap : hitAt(x, y);
    const prevented = nativeEvent('pointer' + kind, x, y, buttons, t);
    if (kind === 'down') compat = !prevented;
    if (compat) nativeEvent('mouse' + kind, x, y, buttons, S.cap && S.cap.isConnected ? S.cap : t);
  }

  // Which game handlers do we know about? (Captured listeners or on... properties on the board's path.)
  function boardPath() {
    const c = canvas(), r = c.getBoundingClientRect(), path = [];
    for (let n = hitAt(r.left + r.width / 2, r.top + r.height / 2); n; n = n.parentNode) path.push(n);
    if (!path.includes(c)) path.unshift(c);
    path.push(window);
    return path;
  }
  // 'mouse' = the original Jigidi input model (mousedown on the canvas); 'pointer' = pointer events
  // through our own dispatcher; 'native' = dispatchEvent (fallback when no handlers are known).
  function detectMode() {
    const c = canvas(), game = S.L.filter((l) => !own(l.target));
    if (game.some((l) => l.t === 'mousedown' && l.target === c)) return 'mouse';
    if (game.some((l) => l.t === 'pointerdown')) return 'pointer';
    if (boardPath().some((n) => typeof n.onpointerdown === 'function' || typeof n.onmousedown === 'function')) return 'pointer';
    if (game.some((l) => l.t === 'mousedown')) return 'mouse';
    return 'native';
  }

  function toClient(p) {
    const c = canvas(), r = c.getBoundingClientRect();
    return { x: r.left + (p.x * r.width) / c.width, y: r.top + (p.y * r.height) / c.height };
  }

  // Wait until the game has drawn the result and nothing is moving any more.
  async function settle(stable = 1, maxF = 40) {
    let m = S.moveTick, still = 0, seen = false;
    for (let k = 0; k < maxF; k++) {
      await frame();
      if (S.moveTick !== m) { m = S.moveTick; seen = true; still = 0; }
      else if (++still >= stable && (seen || k >= 1)) return;
    }
  }

  // How long to wait after a fast (level 0) drag before reading the result. Measured on the first
  // drags of every solve ('cal'), then the cheapest mode that never missed a change is used:
  //   sync: the game redraws during the event itself -> no waiting at all
  //   f1:   the game redraws on the next animation frame -> wait one frame
  //   full: the game animates -> wait until nothing moves any more
  function settleMode(cfg, m0, mSync, mF1, mFull) {
    if (mFull === m0) return;            // nothing moved: no information
    const c = cfg.cal;
    c.n++;
    if (mSync === mFull) c.sync++;
    if (mF1 === mFull) c.f1++;
    if (c.n >= 8) {
      cfg.wait = c.sync === c.n ? 'sync' : c.f1 === c.n ? 'f1' : 'full';
      console.info('[Automagic Solver] wait mode:', cfg.wait);
    }
  }
  // A change showed up after we had stopped waiting: wait longer from now on.
  function late(cfg) {
    if (++cfg.late < 3) return;
    cfg.late = 0;
    cfg.wait = cfg.wait === 'sync' ? 'f1' : 'full';
    console.info('[Automagic Solver] wait mode:', cfg.wait);
  }
  const fast = (cfg) => cfg.level === 0 && (cfg.wait === 'sync' || cfg.wait === 'f1');

  // level 0: whole drag in one synchronous burst (fastest)
  // level 1: one animation frame between events
  // level 2: original timed drag (slowest, most compatible)
  async function dragClient(a, b, cfg, nowait) {
    const lv = cfg.level;
    const pause = lv === 0 ? null : lv === 1 ? frame : () => sleep(cfg.stepDelay);
    const n = lv === 2 ? cfg.moveSteps : lv === 1 ? 2 : 1;
    const m0 = S.moveTick;
    if (S.mode === 'native') {
      S.cap = null;
      nat('move', a.x, a.y, 0);
      if (pause) await pause();
      nat('down', a.x, a.y, 1);
      for (let i = 1; i <= n; i++) {
        if (pause) await pause();
        nat('move', a.x + ((b.x - a.x) * i) / n, a.y + ((b.y - a.y) * i) / n, 1);
      }
      if (pause) await pause();
      nat('up', b.x, b.y, 0);
      S.cap = null;
    } else if (S.mode === 'pointer') {
      S.cap = null;
      dispatch('pointermove', a.x, a.y, 0);
      if (pause) await pause();
      dispatch('pointerdown', a.x, a.y, 1);
      for (let i = 1; i <= n; i++) {
        if (pause) await pause();
        dispatch('pointermove', a.x + ((b.x - a.x) * i) / n, a.y + ((b.y - a.y) * i) / n, 1);
      }
      if (pause) await pause();
      dispatch('pointerup', b.x, b.y, 0);
      S.cap = null;
    } else {
      fire('mv', 'mousemove', a.x, a.y, 0, DOC);
      if (pause) await pause();
      fire('md', 'mousedown', a.x, a.y, 1, CAN);
      for (let i = 1; i <= n; i++) {
        if (pause) await pause();
        fire('mv', 'mousemove', a.x + ((b.x - a.x) * i) / n, a.y + ((b.y - a.y) * i) / n, 1, DOC);
      }
      if (pause) await pause();
      fire('mu', 'mouseup', b.x, b.y, 0, WIN);
    }
    if (lv === 2) { await sleep(cfg.settle); await settle(); return; }
    if (lv === 1 || cfg.wait === 'full') { await settle(); return; }
    if (nowait || cfg.wait === 'sync') return;
    if (cfg.wait === 'f1') { await frame(); return; }
    // 'cal': measure what this game needs
    const mSync = S.moveTick;
    await frame();
    const mF1 = S.moveTick;
    await settle();
    settleMode(cfg, m0, mSync, mF1, S.moveTick);
  }

  // Drag in canvas-pixel coordinates; returns the pieces that moved (null with nowait).
  async function drag(from, to, cfg, nowait) {
    const before = S.drawTick;
    const snap = new Map();
    if (!nowait) for (const [k, v] of S.pos) snap.set(k, { x: v.x, y: v.y });
    await dragClient(toClient(from), toClient(to), cfg, nowait);
    if (nowait) return null;
    const movedNow = () => {
      const r = [];
      for (const [k, v] of S.pos) {
        if (v.tick <= before) continue;
        const o = snap.get(k);
        if (!o || Math.abs(o.x - v.x) + Math.abs(o.y - v.y) > 0.5) r.push(k);
      }
      return r;
    };
    let moved = movedNow();
    const real = Math.hypot(to.x - from.x, to.y - from.y) > 5;
    if (!moved.length && real && fast(cfg)) {
      // Nothing seen yet: maybe the game just hasn't drawn it. Check properly before concluding.
      await settle();
      moved = movedNow();
      if (moved.length) late(cfg);
    }
    // Adaptive speed: if real drags keep doing nothing, the game needs slower input.
    if (moved.length) { cfg.idle = 0; cfg.dead = 0; cfg.proven = S.good = S.mode; }
    else if (real && cfg.level === 2 && ++cfg.dead >= 8) {
      throw new Error('The game ignores the solver\'s input' + (S.late ? ' – the script was injected too late, see console' : '. Jigidi may have changed.'));
    } else if (real && cfg.level < 2 && ++cfg.idle >= (cfg.proven ? 6 : 3)) {
      cfg.idle = 0;
      // Only look for another input mode while none has worked yet. Once a mode has moved pieces,
      // an unlucky streak (a grab on a transparent corner, a blocked piece) must not abandon it.
      const next = !cfg.proven && ['pointer', 'native', 'mouse'].find((m) => !cfg.tried.includes(m));
      if (next) {
        cfg.tried.push(next); S.mode = next;
        console.info('[Automagic Solver] no reaction, trying input mode:', next);
      } else {
        cfg.level++; cfg.tried = [S.mode]; cfg.log(`Switching to speed level ${cfg.level}…`);
      }
    }
    return moved;
  }

  async function zoom(dir, ms) {
    const id = dir < 0 ? 'game-zoom-out' : 'game-zoom-in';
    const l = S.L.find((l) => l.t === 'mousedown' && l.target.id === id);
    if (l) {
      l.f.call(l.target, trusted('mousedown', 0, 0, 1, l.target));
      await sleep(ms);
      fire('mu', 'mouseup', 0, 0, 0, WIN);
      await settle(3, 40);
      return true;
    }
    // Other builds: press the button with our dispatcher, then with real (untrusted) browser events.
    // (No mouse-wheel fallback: on a board the wheel may pan instead of zoom.)
    const p0 = S.pos.get(0), s0 = p0 && p0.s;
    const changed = () => { const q = S.pos.get(0); return q && Math.abs(q.s - s0) > 1e-6; };
    const btn = zoomButton(dir);
    if (!btn) return false;
    const r = btn.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
    dispatch('pointerdown', x, y, 1, null, btn);
    dispatch('mousedown', x, y, 1, null, btn);
    await sleep(ms);
    dispatch('pointerup', x, y, 0, null, btn);
    dispatch('mouseup', x, y, 0, null, btn);
    dispatch('click', x, y, 0, null, btn);
    await settle(3, 40);
    if (changed()) return true;
    for (const t of ['pointerdown', 'mousedown']) nativeEvent(t, x, y, 1, btn);
    await sleep(ms);
    for (const t of ['pointerup', 'mouseup']) nativeEvent(t, x, y, 0, btn);
    S.synth = true;
    try { btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: x, clientY: y, view: window })); } finally { S.synth = false; }
    await settle(3, 40);
    return changed();
  }

  // Find Jigidi's zoom-out / zoom-in button: by id first, then by label, title or a lone − / + sign.
  function zoomButton(dir) {
    const byId = document.getElementById(dir < 0 ? 'game-zoom-out' : 'game-zoom-in');
    if (byId && byId.isConnected) return byId;
    const word = dir < 0 ? /zoom[-_ ]?out|zoomout|smaller|minus/i : /zoom[-_ ]?in|zoomin|larger|plus/i;
    const sign = dir < 0 ? /^[−–-]$/ : /^\+$/;
    let best = null;
    for (const el of document.querySelectorAll('button, [role=button], a, div, span, svg')) {
      if (el.closest('#jas-panel') || !el.getClientRects().length) continue;
      const label = [el.id, typeof el.className === 'string' ? el.className : '', el.getAttribute('aria-label'), el.getAttribute('title')].join(' ');
      const txt = (el.textContent || '').trim();
      if (word.test(label) || (sign.test(txt) && el.children.length <= 1)) {
        const b = el.closest('button, [role=button], a') || el;
        if (!best || best.contains(b)) best = b;   // innermost clickable match
      }
    }
    return best;
  }

  function dims(N) {
    const found = [];
    const add = (txt) => { for (const m of txt.matchAll(/\((\d+)\s*[×x]\s*(\d+)\)/g)) found.push({ cols: +m[1], rows: +m[2] }); };
    for (const el of document.body.querySelectorAll('*')) {
      if (/^(SCRIPT|STYLE|NOSCRIPT)$/.test(el.tagName)) continue;
      const t = el.textContent;
      if (t.length <= 60) add(t);
    }
    add(document.body.innerText || '');
    return found.find((d) => d.cols * d.rows === N) || found[0] || null;
  }

  async function solve(opts = {}) {
    const cfg = Object.assign({ level: 0, idle: 0, dead: 0, wait: 'cal', cal: { n: 0, sync: 0, f1: 0 }, late: 0, tried: [], proven: null, stepDelay: 12, moveSteps: 5, settle: 60, margin: 20, maxTries: 12, passes: 2, log: () => {} }, opts);
    const N = S.off.length;
    const d = dims(N);
    if (!d || N === 0 || d.cols * d.rows !== N) throw new Error(`Puzzle not recognized (pieces=${N}, dims=${JSON.stringify(d)})`);
    if (d.cols < 2 || d.rows < 2) throw new Error(`Puzzle too small (${d.cols}×${d.rows})`);
    if (S.pos.size !== N) throw new Error(`Pieces not drawn yet (${S.pos.size}/${N})`);
    const c = canvas();
    if (!c) throw new Error('Game board not found');
    const W = c.width, H = c.height;
    S.mode = S.good || detectMode();     // a mode that worked earlier on this page wins
    cfg.tried.push(S.mode);
    console.info('[Automagic Solver] input mode:', S.mode);
    const stopped = () => !!(cfg.stop && cfg.stop());

    const stepX = Math.abs(S.off[1][0] - S.off[0][0]);
    const stepY = Math.abs(S.off[d.cols][1] - S.off[0][1]);

    for (let k = 0; k < 20; k++) {
      const s = S.pos.get(0).s;
      if (d.cols * stepX * s * d.rows * stepY * s < 0.5 * W * H && d.cols * stepX * s < 0.75 * W
        && (d.rows + 1) * stepY * s < H - 2 * cfg.margin - 50) break;
      if (!(await zoom(-1, 60))) break;
    }
    const s = () => S.pos.get(0).s;
    const pw = stepX * s(), ph = stepY * s();
    const cw = d.cols * pw, ch = d.rows * ph;
    const top = cfg.margin + 50;

    const boxFor = (p0) => ({ x0: p0.x - pw, y0: p0.y - ph, x1: p0.x + cw, y1: p0.y + ch });
    const fits = (b) => b.x0 >= cfg.margin && b.y0 >= top && b.x1 <= W - cfg.margin && b.y1 <= H - cfg.margin;
    // The finished puzzle must fit on the board, or pieces would have to be dropped off-screen.
    if (cw + pw > W - 2 * cfg.margin || ch + ph > H - top - cfg.margin) {
      throw new Error('The puzzle doesn\'t fit on the board. Zoom out (−) and press Solve again.');
    }
    const inB = (b, p) => p.x > b.x0 - pw * 0.6 && p.x < b.x1 + pw * 0.6 && p.y > b.y0 - ph * 0.6 && p.y < b.y1 + ph * 0.6;

    // Choose the anchor: a piece left where it lies, whose finished-puzzle box fits on the
    // board and contains the fewest stray pieces. Saves one drag plus most of the clearing.
    let anchor = null, box = null, bestCnt = Infinity, shift = null;
    const all = [...S.pos];
    const relOK0 = (i, j) => {
      const pi = S.pos.get(i), pj = S.pos.get(j), sc = s();
      return Math.hypot(pi.x - (pj.x + (S.off[j][0] - S.off[i][0]) * sc), pi.y - (pj.y + (S.off[j][1] - S.off[i][1]) * sc)) < 3;
    };
    // Already assembled pieces (from an earlier run or by hand): continue from the biggest group.
    const big = (() => {
      const par = Int32Array.from({ length: N }, (_, i) => i);
      const find = (i) => { while (par[i] !== i) { par[i] = par[par[i]]; i = par[i]; } return i; };
      for (let i = 0; i < N; i++) {
        if ((i + 1) % d.cols && relOK0(i, i + 1)) par[find(i)] = find(i + 1);
        if (i + d.cols < N && relOK0(i, i + d.cols)) par[find(i)] = find(i + d.cols);
      }
      const g = new Map();
      for (let i = 0; i < N; i++) { const r = find(i); if (!g.has(r)) g.set(r, []); g.get(r).push(i); }
      let b = [];
      for (const m of g.values()) if (m.length > b.length) b = m;
      return b.length >= 4 ? b : [];
    })();
    if (big.length) {
      anchor = big[0];
      const pa = () => S.pos.get(anchor);
      const boxNow = () => boxFor({ x: pa().x + (S.off[anchor][0] - S.off[0][0]) * s(), y: pa().y + (S.off[anchor][1] - S.off[0][1]) * s() });
      const b = boxNow();
      if (fits(b)) { box = b; bestCnt = 0; }
      else {
        // Plan to move the whole assembly back onto the board (done below, once the helpers exist).
        const dx = Math.max(cfg.margin - b.x0, Math.min(0, W - cfg.margin - b.x1));
        const dy = Math.max(top - b.y0, Math.min(0, H - cfg.margin - b.y1));
        box = { x0: b.x0 + dx, y0: b.y0 + dy, x1: b.x1 + dx, y1: b.y1 + dy };
        shift = { dx, dy, boxNow };
        bestCnt = 0;
      }
    }
    if (box === null) for (const [a, pa] of all) {
      const b = boxFor({ x: pa.x + (S.off[a][0] - S.off[0][0]) * s(), y: pa.y + (S.off[a][1] - S.off[0][1]) * s() });
      if (!fits(b)) continue;
      let cnt = 0;
      for (const [k, pk] of all) if (k !== a && inB(b, pk) && ++cnt >= bestCnt) break;
      if (cnt < bestCnt) { bestCnt = cnt; anchor = a; box = b; if (!cnt) break; }
    }
    if (box === null) box = boxFor({ x: cfg.margin + pw, y: top + ph });
    const A = { x: box.x0 + pw, y: box.y0 + ph };
    const inBox = (p) => inB(box, p);

    const placed = new Set();
    const markPlaced = (i) => { placed.add(i); if (anchor === null) anchor = i; };
    const target = (i) => {
      const a = anchor, base = a === null ? A : S.pos.get(a), o = S.off[a === null ? 0 : a];
      return { x: base.x + (o[0] - S.off[i][0]) * s(), y: base.y + (o[1] - S.off[i][1]) * s() };
    };
    const at = (i, t, tol = 3) => { const p = S.pos.get(i); return Math.hypot(p.x - t.x, p.y - t.y) < tol; };
    const relOK = (i, j, tol) => {
      const pi = S.pos.get(i), pj = S.pos.get(j), sc = s();
      return Math.hypot(pi.x - (pj.x + (S.off[j][0] - S.off[i][0]) * sc), pi.y - (pj.y + (S.off[j][1] - S.off[i][1]) * sc)) < tol;
    };
    const nbrs = (i) => {
      const r = [];
      if (i % d.cols) r.push(i - 1);
      if ((i + 1) % d.cols) r.push(i + 1);
      if (i >= d.cols) r.push(i - d.cols);
      if (i + d.cols < N) r.push(i + d.cols);
      return r;
    };
    const done = (i) => {
      if (anchor === null) return false;
      if (i === anchor) return true;
      const ns = nbrs(i).filter((j) => placed.has(j));
      if (ns.length) return ns.some((j) => relOK(i, j, 3));
      const far = Math.hypot((S.off[anchor][0] - S.off[i][0]) * s(), (S.off[anchor][1] - S.off[i][1]) * s());
      return relOK(i, anchor, Math.max(3, 0.01 * far));
    };

    // Grab point: the solid middle of the piece (never a transparent tab corner), shifted to a
    // spot no later-drawn (= higher) piece covers, so we don't pick up the wrong piece.
    const GRID = [[0, 0], [-0.25, -0.25], [0.25, -0.25], [-0.25, 0.25], [0.25, 0.25], [0, -0.3], [0, 0.3], [-0.3, 0], [0.3, 0]];
    const grabOff = (i) => {
      const p = S.pos.get(i);
      for (const [u, v] of GRID) {
        const qx = p.cx + u * pw, qy = p.cy + v * ph;
        let cov = false;
        for (const [j, r] of S.pos) {
          if (j !== i && r.tick > p.tick && Math.abs(r.cx - qx) < 0.62 * pw && Math.abs(r.cy - qy) < 0.62 * ph) { cov = true; break; }
        }
        if (!cov) return { x: qx - p.x, y: qy - p.y };
      }
      return { x: p.cx - p.x, y: p.cy - p.y };
    };
    const add = (p, g) => ({ x: p.x + g.x, y: p.y + g.y });

    const parking = (avoid, exclude = []) => {
      let best = null, bestGap = -1;
      for (let k = 0; k < 60; k++) {
        const p = { x: pw + Math.random() * (W - 2 * pw), y: Math.max(ph, top) + Math.random() * (H - ph - Math.max(ph, top)) };
        if (p.x > box.x0 - 1.2 * pw && p.x < box.x1 + 1.2 * pw && p.y > box.y0 - 1.2 * ph && p.y < box.y1 + 1.2 * ph) continue;
        if (avoid && Math.hypot(p.x - avoid.x, p.y - avoid.y) <= 3 * pw) continue;
        let gap = Infinity;
        for (const [i, q] of S.pos) {
          if (exclude.includes(i)) continue;
          gap = Math.min(gap, Math.max(Math.abs(p.x - q.x) / pw, Math.abs(p.y - q.y) / ph));
          if (gap <= bestGap) break;
        }
        if (gap > 0.9) return p;
        if (gap > bestGap) { bestGap = gap; best = p; }
      }
      return best || { x: W - pw, y: H - ph };
    };

    async function fixWrongGrab(moved, dropAt, dragFrom) {
      if (moved.some((k) => placed.has(k))) { await drag(dropAt, dragFrom, cfg); return; }
      for (const k of moved) if (done(k)) markPlaced(k);
      if (moved.some((k) => !placed.has(k))) await drag(dropAt, parking(dragFrom, moved), cfg);
    }

    if (anchor !== null) markPlaced(anchor);
    if (big.includes(anchor)) for (const k of big) placed.add(k);

    if (shift) {
      // 1) Clear the area the assembly will move onto (loose pieces there would end up underneath it).
      cfg.log('Making room for the assembled part…');
      const inBig = new Set(big);
      const dest = big.map((k) => { const q = S.pos.get(k); return [q.cx + shift.dx, q.cy + shift.dy]; });
      const underDest = (q) => dest.some(([x, y]) => Math.abs(q.cx - x) < 0.9 * pw && Math.abs(q.cy - y) < 0.9 * ph);
      for (let round = 0; round < 3; round++) {
        const todo = [...S.pos].filter(([k, q]) => !inBig.has(k) && underDest(q)).sort((a, b) => b[1].tick - a[1].tick).map(([k]) => k);
        if (!todo.length) break;
        for (const k of todo) {
          if (stopped()) return { placed: placed.size, total: N, stopped: true };
          if (!underDest(S.pos.get(k))) continue;
          const q = S.pos.get(k), g = grabOff(k), from = add(q, g), to = add(parking(undefined, [k]), g);
          const moved = await drag(from, to, cfg);
          if (moved.some((j) => inBig.has(j))) await drag(to, from, cfg);
        }
      }
      // 2) Move the assembly: grab one of its visible pieces and drag it.
      cfg.log('Moving the assembled part onto the board…');
      const inView = (k) => { const q = S.pos.get(k); return q.cx > 0.6 * pw && q.cx < W - 0.6 * pw && q.cy > 0.6 * ph && q.cy < H - 0.6 * ph; };
      for (const k of big.filter(inView).sort((u, v) => S.pos.get(v).tick - S.pos.get(u).tick).slice(0, 4)) {
        const q = S.pos.get(k), g = grabOff(k), from = add(q, g);
        const moved = await drag(from, { x: from.x + shift.dx, y: from.y + shift.dy }, cfg);
        if (moved.includes(anchor)) break;
        if (moved.length) await drag({ x: from.x + shift.dx, y: from.y + shift.dy }, from, cfg);   // grabbed a loose piece
      }
      if (!fits(shift.boxNow())) throw new Error('Could not move the assembled part onto the board. Drag it into view and press Solve again.');
    }

    let count = 0;
    const report = (i, ok, skipped) => {
      count++;
      if (!ok || count % 5 === 0) cfg.log(`Piece ${placed.size}/${N} ${ok ? (skipped ? 'already placed' : 'placed') : 'FAILED'}`);
      if (cfg.onProgress) cfg.onProgress(placed.size, N, ok);
    };

    // Stray pieces lying on or next to the spot where piece i will go (topmost first). Clearing them
    // just in time, instead of emptying the whole target area up front, lets many of them go straight
    // to their own spot instead of being parked first and placed later (one drag instead of two).
    const blockers = (i, chain) => {
      const t = target(i), r = [];
      for (const [k, p] of S.pos) {
        if (k === i || placed.has(k) || chain.has(k)) continue;
        if (Math.abs(p.x - t.x) < 1.5 * pw && Math.abs(p.y - t.y) < 1.5 * ph && inBox(p)) r.push([k, p.tick]);
      }
      return r.sort((a, b) => b[1] - a[1]).map(([k]) => k);
    };
    const chainOn = (k, chain) => {
      const t = target(k);
      for (const j of chain) { const p = S.pos.get(j); if (Math.abs(p.x - t.x) < pw && Math.abs(p.y - t.y) < ph) return true; }
      return false;
    };
    async function clearFor(i, depth, chain) {
      for (const k of blockers(i, chain)) {
        if (stopped()) return;
        if (placed.has(k) || !inBox(S.pos.get(k))) continue;
        if (done(k)) { markPlaced(k); report(k, true, true); continue; }
        if (depth < 3 && nbrs(k).some((j) => placed.has(j)) && !chainOn(k, chain)) {
          if (await place(k, depth + 1, chain)) continue;
          if (placed.has(k) || !inBox(S.pos.get(k))) continue;
        }
        const p = S.pos.get(k), g = grabOff(k), from = add(p, g), to = add(parking(undefined, [k]), g);
        const moved = await drag(from, to, cfg);
        if (moved.some((j) => placed.has(j))) await drag(to, from, cfg);
      }
    }

    async function place(i, depth = 0, chain = new Set()) {
      if (placed.has(i)) return true;
      if (done(i)) { markPlaced(i); report(i, true, true); return true; }
      chain.add(i);
      await clearFor(i, depth, chain);
      if (stopped()) { chain.delete(i); return false; }
      let ok = false;
      for (let tr = 0; tr < cfg.maxTries && !ok; tr++) {
        const p = { ...S.pos.get(i) }, t = target(i), g = grabOff(i);
        const from = add(p, g), to = add(t, g);
        const moved = await drag(from, to, cfg);
        if (at(i, target(i)) || done(i)) { ok = true; break; }
        if (fast(cfg) && moved.includes(i)) {
          await settle();
          if (at(i, target(i)) || done(i)) { late(cfg); ok = true; break; }
        }
        if (moved.some((k) => placed.has(k))) {
          await drag(to, from, cfg);
          if (moved.includes(i)) { ok = true; break; }
          continue;
        }
        if (moved.includes(i)) continue;
        await fixWrongGrab(moved, to, from);
        if (done(i)) ok = true;
      }
      chain.delete(i);
      if (ok) markPlaced(i);
      report(i, ok, false);
      return ok;
    }

    // Place pieces outward from the anchor (BFS), so every drop lands next to an already-placed
    // neighbour and snaps on the first try.
    const order = [], seen = new Uint8Array(N), start = anchor === null ? 0 : anchor;
    seen[start] = 1; order.push(start);
    for (let h = 0; h < order.length; h++) for (const j of nbrs(order[h])) if (!seen[j]) { seen[j] = 1; order.push(j); }

    for (let pass = 0; pass < cfg.passes; pass++) {
      const todo = order.filter((i) => !placed.has(i));
      if (!todo.length) break;
      if (pass > 0) cfg.log(`Retrying ${todo.length} failed piece${todo.length > 1 ? 's' : ''}...`);
      for (const i of todo) {
        if (stopped()) return { placed: placed.size, total: N, stopped: true };
        await place(i);
      }
    }
    for (let k = 0; k < 2; k++) for (let i = 0; i < N; i++) if (done(i)) placed.add(i);
    return { placed: placed.size, total: N, stopped: false, level: cfg.level, wait: cfg.wait };
  }

  S.solve = solve;
  S.zoom = zoom;
})();

// UI: compact floating pill. Lives in a Shadow DOM so Jigidi's CSS can't touch it.
// Drag it anywhere, click the ring to minimise, Esc stops a running solve.
(function () {
  if (JAS_SITE) return;
  const S = window.__jas;
  const KEY = 'jas-ui';
  const C = 100.53; // ring circumference (r = 16)
  const PIECE = 'M5 8h3.5a2.5 2.5 0 1 1 5 0H17v3.5a2.5 2.5 0 1 1 0 5V20H5z';
  const CSS = `
:host{all:initial}
*{box-sizing:border-box}
.p{--a:#34d399;--ad:#053b2a;display:flex;align-items:center;gap:10px;padding:5px;
 background:rgba(15,18,24,.8);-webkit-backdrop-filter:blur(16px) saturate(1.5);backdrop-filter:blur(16px) saturate(1.5);
 border:1px solid rgba(255,255,255,.08);border-radius:999px;
 box-shadow:0 10px 30px -8px rgba(0,0,0,.55),0 2px 6px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,255,.06);
 font:500 12px/1.25 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#e5e7eb;
 cursor:grab;user-select:none;-webkit-user-select:none;touch-action:none}
.p.drag{cursor:grabbing}
.p[data-s=warn]{--a:#fbbf24;--ad:#422006}
.p[data-s=err]{--a:#f87171;--ad:#450a0a}
.ic{position:relative;flex:none;width:36px;height:36px;padding:0;border:0;border-radius:50%;background:none;cursor:pointer}
.ic svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.tr{fill:rgba(255,255,255,.05);stroke:rgba(255,255,255,.09);stroke-width:2.5}
.pr{fill:none;stroke:var(--a);stroke-width:2.5;stroke-linecap:round;stroke-dasharray:100.53;stroke-dashoffset:100.53;
 transform:rotate(-90deg);transform-origin:18px 18px;transition:stroke-dashoffset .3s ease,stroke .3s}
.p[data-s=load] .pr{stroke-dashoffset:72;animation:spin .9s linear infinite}
@keyframes spin{to{transform:rotate(270deg)}}
.ic .pz,.ic .ck{inset:9px;width:18px;height:18px;transition:opacity .2s,transform .3s}
.pz path{fill:var(--a);transition:fill .3s}
.ck path{fill:none;stroke:var(--a);stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
.ck{opacity:0;transform:scale(.5)}
.p[data-s=done] .pz{opacity:0;transform:scale(.5)}
.p[data-s=done] .ck{opacity:1;transform:none}
.p[data-s=run] .pz{animation:bob 1.1s ease-in-out infinite}
@keyframes bob{50%{transform:translateY(-1.5px) rotate(-10deg)}}
.tx{width:146px;min-width:0}
.t{font-size:12.5px;font-weight:650;color:#f9fafb;letter-spacing:.01em}
.st{margin-top:2px;font-size:11px;color:#9ca3af;font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.p[data-s=err] .st{color:#fca5a5}
.go{flex:none;height:30px;min-width:66px;padding:0 14px;border:0;border-radius:999px;background:var(--a);color:var(--ad);
 font:inherit;font-weight:700;letter-spacing:.01em;cursor:pointer;transition:transform .12s,filter .15s,background .2s,color .2s}
.go:hover{filter:brightness(1.1)}
.go:active{transform:scale(.95)}
.go:focus-visible,.ic:focus-visible{outline:2px solid var(--a);outline-offset:2px}
.go:disabled{background:rgba(255,255,255,.07);color:#6b7280;cursor:default;filter:none;transform:none}
.p[data-s=run] .go{background:rgba(248,113,113,.14);color:#fca5a5;box-shadow:inset 0 0 0 1px rgba(248,113,113,.3)}
.p.min{padding:4px;gap:0}
.p.min .tx,.p.min .go{display:none}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}`;

  function mount() {
    if (!document.body) return setTimeout(mount, 100);
    let pref = {};
    try { pref = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { /* storage blocked */ }
    const save = () => { try { localStorage.setItem(KEY, JSON.stringify(pref)); } catch (e) { /* ignore */ } };

    const host = document.createElement('div');
    host.id = 'jas-panel';
    host.style.cssText = 'position:fixed;z-index:2147483647;left:16px;bottom:16px';
    const root = host.attachShadow({ mode: 'open' });
    root.innerHTML = `<style>${CSS}</style><div class="p" data-s="load">`
      + `<button class="ic" aria-label="Minimise"><svg viewBox="0 0 36 36"><circle class="tr" cx="18" cy="18" r="16"/>`
      + `<circle class="pr" cx="18" cy="18" r="16"/></svg><svg class="pz" viewBox="0 0 24 24"><path d="${PIECE}"/></svg>`
      + `<svg class="ck" viewBox="0 0 24 24"><path d="M6 12.5l4 4 8-9"/></svg></button>`
      + `<div class="tx"><div class="t">Automagic Solver</div><div class="st">Loading puzzle…</div></div>`
      + `<button class="go" disabled>Solve</button></div>`;
    document.body.appendChild(host);
    const $ = (q) => root.querySelector(q);
    const p = $('.p'), ic = $('.ic'), st = $('.st'), go = $('.go'), pr = $('.pr');

    const clamp = () => {
      if (pref.x == null) return;
      const r = host.getBoundingClientRect();
      pref.x = Math.max(4, Math.min(innerWidth - r.width - 4, pref.x));
      pref.y = Math.max(4, Math.min(innerHeight - r.height - 4, pref.y));
      host.style.left = pref.x + 'px'; host.style.top = pref.y + 'px'; host.style.bottom = 'auto';
    };
    if (pref.min) p.classList.add('min');
    clamp();
    addEventListener('resize', clamp);

    const set = (s, text, frac) => {
      p.dataset.s = s;
      if (text != null) { st.textContent = text; ic.title = 'Automagic Solver · ' + text; }
      if (s === 'load') pr.style.strokeDashoffset = '';
      else if (frac != null) pr.style.strokeDashoffset = C * (1 - Math.max(0, Math.min(1, frac)));
    };

    // Ready detection
    const ready = () => S.off.length > 1 && S.pos.size === S.off.length;
    const iv = setInterval(() => {
      if (!ready()) return;
      clearInterval(iv); go.disabled = false;
      set('ready', `${S.off.length} pieces · ready`, 0);
    }, 300);

    // Solve / stop
    let running = false, stop = false;
    const fmt = (s) => (s < 60 ? `${Math.ceil(s)}s` : `${Math.floor(s / 60)}m ${String(Math.ceil(s % 60)).padStart(2, '0')}s`);
    const requestStop = () => { stop = true; go.textContent = 'Stopping'; };
    async function run() {
      if (running) return requestStop();
      if (!ready()) return set('load', 'Still loading…');
      running = true; stop = false; S.busy = true;
      go.textContent = 'Stop'; set('run', 'Starting…', 0);
      const t0 = performance.now();
      let last = 0;
      try {
        const r = await S.solve({
          stop: () => stop,
          log: (m) => { if (!/^Piece/.test(m)) st.textContent = m; },
          onProgress: (n, N) => {
            pr.style.strokeDashoffset = C * (1 - n / N);
            const now = performance.now();
            if (now - last < 120 && n < N) return;
            last = now;
            const rate = n / ((now - t0) / 1000);
            set('run', `${n}/${N} · ${rate.toFixed(1)}/s · ${fmt((N - n) / Math.max(rate, 0.01))} left`);
          },
        });
        const sec = (performance.now() - t0) / 1000;
        const ok = !r.stopped && r.placed === r.total;
        set(ok ? 'done' : 'warn', `${r.placed}/${r.total} · ${sec.toFixed(1)}s · ${(r.placed / sec).toFixed(1)}/s`
          + (r.stopped ? ' · stopped' : ''), r.placed / r.total);
      } catch (e) {
        set('err', e.message, 1); console.error(e);
      }
      S.busy = false; running = false; go.textContent = 'Solve';
    }
    go.addEventListener('click', run);
    addEventListener('keydown', (e) => { if (running && e.key === 'Escape') requestStop(); }, true);

    // Drag to move; a click on the ring (without dragging) toggles the minimised state.
    let d = null;
    p.addEventListener('pointerdown', (e) => {
      if (e.button !== 0 || e.target.closest('.go')) return;
      const r = host.getBoundingClientRect();
      d = { dx: e.clientX - r.left, dy: e.clientY - r.top, x0: e.clientX, y0: e.clientY, icon: !!e.target.closest('.ic'), moved: false };
      p.setPointerCapture(e.pointerId);
      e.preventDefault(); e.stopPropagation();
    });
    p.addEventListener('pointermove', (e) => {
      if (!d) return;
      if (!d.moved && Math.hypot(e.clientX - d.x0, e.clientY - d.y0) < 4) return;
      d.moved = true; p.classList.add('drag');
      pref.x = e.clientX - d.dx; pref.y = e.clientY - d.dy;
      clamp();
    });
    const end = () => {
      if (!d) return;
      if (d.moved) save();
      else if (d.icon) { pref.min = p.classList.toggle('min'); clamp(); save(); }
      p.classList.remove('drag'); d = null;
    };
    p.addEventListener('pointerup', end);
    p.addEventListener('pointercancel', end);
    ic.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pref.min = p.classList.toggle('min'); clamp(); save(); }
    });
    ic.addEventListener('click', (e) => e.preventDefault());
  }
  mount();
})();
