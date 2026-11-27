// Rest-pose art for a real Blender rig: one straight drawing per limb (bent later by bones), torso, shoes, hand atlas.
import { SKEL, U, tube, sleeve, torsoMom, torsoSon, shoe, hand } from "./puppet2.js";
import { CAST } from "./puppet.js";
const SKIN = "#f7e2bd", NO = "rgba(0,0,0,0)", SK = [SKIN, NO, NO];
// matte cylinder shading: soft light on the left, soft core shadow on the right, applied over the whole straight limb
function matte(c, cx, w) { const o = document.createElement("canvas"); o.width = c.width; o.height = c.height; const g = o.getContext("2d"); g.drawImage(c, 0, 0); g.globalCompositeOperation = "source-atop";
  const gr = g.createLinearGradient(cx - w / 2, 0, cx + w / 2, 0); gr.addColorStop(0, "rgba(255,250,235,0.32)"); gr.addColorStop(0.38, "rgba(255,250,235,0)"); gr.addColorStop(0.7, "rgba(60,30,20,0)"); gr.addColorStop(1, "rgba(60,30,20,0.32)");
  g.fillStyle = gr; g.fillRect(0, 0, o.width, o.height); const cc = c.getContext("2d"); cc.clearRect(0, 0, c.width, c.height); cc.drawImage(o, 0, 0); return c; }
const cv = (w, h) => { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; };
const V = (x, y) => ({ x, y });
// tube()/sleeve() draw into a CW x CH sized offscreen; give them a big canvas then crop
function onBig(w, h, fn) { const big = cv(1700, 2500), c = big.getContext("2d"); fn(c); const o = cv(w, h); o.getContext("2d").drawImage(big, 0, 0); return o; }
export function arm(who) {
  const S = SKEL[who], [base, dark, light] = S.sleeveCol, W = 120, top = 60, L = (S.up + S.fo) * U, H = Math.round(top + L + 60), cx = W / 2;
  const s0 = V(cx, top), el = V(cx, top + S.up * U), wr = V(cx, top + L);
  const c = onBig(W, H, g => {
    if (S.sleeve === "wrist") sleeve(g, [s0, V(cx, top + L - 0.012 * U)], S.armW * U, base, NO, NO, "#1d4a2c");
    else { tube(g, [s0, wr], [S.foW * U * 1.0], ...SK); sleeve(g, [s0, V(cx, top + S.up * U * 0.82)], S.armW * U * 1.12, base, NO, NO, "#7a2622"); }
  });
  matte(c, cx, S.armW * U * 1.3);
  return { c, meta: { W, H, shoulder: [cx, top], elbow: [cx, top + S.up * U], wrist: [cx, top + L] } };
}
export function leg(who) {
  const S = SKEL[who], k = CAST[who], W = 96, top = 30, L = (S.th + S.sn) * U, H = Math.round(top + L + 30), cx = W / 2;
  const c = onBig(W, H, g => {
    tube(g, [V(cx, top), V(cx, top + L)], [S.legW * U], ...SK);
    if (who === "son") { tube(g, [V(cx, top + L - 0.075 * U), V(cx, top + L - 0.008 * U)], [S.legW * U * 1.15], "#ffffff", NO, NO);
      g.strokeStyle = k.shoeTrim; g.lineWidth = 6; g.beginPath(); g.moveTo(cx - 0.03 * U, top + L - 0.055 * U); g.lineTo(cx + 0.03 * U, top + L - 0.055 * U); g.stroke(); }
  });
  matte(c, cx, S.legW * U * 1.3);
  return { c, meta: { W, H, hip: [cx, top], knee: [cx, top + S.th * U], ankle: [cx, top + L] } };
}
export function foot(who) {   // right shoe, toe to +x; ankle pivot
  const W = 260, H = 140, a = V(80, 50);
  const c = cv(W, H); shoe(c.getContext("2d"), who, a, 1, CAST[who]);
  return { c, meta: { W, H, ankle: [a.x, a.y] } };
}
export function torso(who) {
  const S = SKEL[who], W = 600, H = 820, hip = V(300, 560), sh = V(300, 560 - (S.sh - S.hip) * U);
  const c = cv(W, H); (who === "mom" ? torsoMom : torsoSon)(c.getContext("2d"), CAST[who], hip, sh, 0);
  return { c, meta: { W, H, hip: [hip.x, hip.y], shoulder: [sh.x, sh.y] } };
}
// hand atlas: cells of 300x300, wrist at (150, 40), fingers pointing down (+y), thumb toward +x (right hand, palm to camera)
export const HANDS = ["open", "fist", "point", "gripBack", "gripFront", "wave"];
const OUT = "#2b1b20";
function caps(list) { return list; }   // [ [x0,y0,x1,y1,w] ... ] capsules, or {rr:[x,y,w,h,r]} rounded rects
function union(g, shapes, fill, lw = 7) {
  const draw = (c, extra, col) => { c.strokeStyle = col; c.fillStyle = col; c.lineCap = "round"; c.lineJoin = "round";
    for (const s of shapes) { if (s.rr) { const [x, y, w, h, r] = s.rr; c.beginPath(); c.roundRect(x - extra, y - extra, w + 2 * extra, h + 2 * extra, r + extra); c.fill(); }
      else { const [x0, y0, x1, y1, w] = s; c.lineWidth = w + 2 * extra; c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke(); } } };
  draw(g, lw, OUT);
  const o = cv(300, 300), c = o.getContext("2d"); draw(c, 0, fill);
  c.globalCompositeOperation = "source-atop";
  let gr = c.createRadialGradient(110, 90, 5, 120, 110, 170); gr.addColorStop(0, "rgba(255,252,240,0.85)"); gr.addColorStop(0.5, "rgba(255,240,215,0)"); c.fillStyle = gr; c.fillRect(0, 0, 300, 300);
  gr = c.createRadialGradient(230, 270, 5, 230, 270, 200); gr.addColorStop(0, "rgba(160,100,55,0.6)"); gr.addColorStop(1, "rgba(160,100,55,0)"); c.fillStyle = gr; c.fillRect(0, 0, 300, 300);
  g.drawImage(o, 0, 0);
}
function crease(g, pts, w = 4, col = "rgba(120,70,45,0.6)") { g.strokeStyle = col; g.lineWidth = w; g.lineCap = "round"; g.beginPath(); g.moveTo(pts[0], pts[1]); for (let i = 2; i < pts.length; i += 2) g.lineTo(pts[i], pts[i + 1]); g.stroke(); }
function drawHand(g, kind, s) {
  const h = 140 * s, x = 150, y = 40, pw = 0.6 * h, fw = 0.165 * h, py = y + 0.12 * h;          // palm top, palm size, finger width
  const palm = { rr: [x - pw / 2, py, pw, 0.5 * h, 0.22 * h] };
  const fx = i => x - pw / 2 + fw * 0.62 + i * (pw - fw * 1.24) / 3;                               // finger columns, index finger is on the thumb side (+x)
  const thumbOpen = [x + pw * 0.42, py + 0.2 * h, x + pw * 0.42 + 0.26 * h, py + 0.44 * h, fw * 1.1];
  if (kind === "open" || kind === "wave") {
    const sp = kind === "wave" ? 0.11 : 0.05, L = [0.36, 0.46, 0.48, 0.42];
    const fingers = [0, 1, 2, 3].map(i => { const a = (i - 1.5) * sp, x0 = fx(i), y0 = py + 0.42 * h; return [x0, y0, x0 + Math.sin(a) * L[i] * h, y0 + Math.cos(a) * L[i] * h, fw]; });
    union(g, [palm, ...fingers, thumbOpen], SKIN);
    for (let i = 0; i < 3; i++) { const xm = (fx(i) + fx(i + 1)) / 2; crease(g, [xm, py + 0.55 * h, xm + (i - 1) * 3, py + 0.55 * h + 0.25 * h]); }
    crease(g, [x - pw * 0.25, py + 0.3 * h, x + pw * 0.15, py + 0.36 * h], 3.5, "rgba(120,70,45,0.4)");
  } else if (kind === "fist" || kind === "point") {
    const fist = { rr: [x - pw / 2, py, pw, 0.62 * h, 0.24 * h] };
    const thumb = [x + pw * 0.4, py + 0.2 * h, x - pw * 0.05, py + 0.44 * h, fw * 1.1];
    const sh = [fist, thumb]; if (kind === "point") sh.push([fx(3) - 2, py + 0.5 * h, fx(3) - 6, py + 0.5 * h + 0.48 * h, fw]);
    union(g, sh, SKIN);
    for (let i = 0; i < 3; i++) { const xm = (fx(i) + fx(i + 1)) / 2; crease(g, [xm, py + 0.5 * h, xm, py + 0.62 * h]); }
    crease(g, [x - pw * 0.45, py + 0.38 * h, x - pw * 0.1, py + 0.4 * h], 3.5, "rgba(120,70,45,0.45)");
  } else if (kind === "gripBack") {
    union(g, [{ rr: [x - pw / 2, py, pw, 0.58 * h, 0.22 * h] }], SKIN);
  } else if (kind === "gripFront") {          // curled fingers across the front of a bar held at y = py + 0.48h (bar runs along x)
    const yb = py + 0.48 * h, fr = [0, 1, 2, 3].map(i => [fx(i), yb - 0.1 * h, fx(i), yb + 0.1 * h, fw * 1.05]);
    const thumb = [x + pw * 0.5, py + 0.24 * h, x + pw * 0.05, yb - 0.14 * h, fw * 1.1];
    union(g, [...fr, thumb], SKIN);
    for (let i = 0; i < 4; i++) crease(g, [fx(i) - fw * 0.35, yb + 0.02 * h, fx(i) + fw * 0.35, yb + 0.02 * h], 3.5, "rgba(120,70,45,0.5)");
  }
}
export function hands(who) {
  const S = SKEL[who], N = HANDS.length, CS = 300, c = cv(CS * N, CS), g = c.getContext("2d");
  HANDS.forEach((name, i) => { const t = cv(CS, CS); drawHand(t.getContext("2d"), name, S.hand); g.drawImage(t, i * CS, 0); });
  const h = 140 * S.hand;
  return { c, meta: { W: CS * N, H: CS, cell: CS, wrist: [150, 40], names: HANDS, grip: [150, 40 + 0.12 * h + 0.48 * h] } };
}
