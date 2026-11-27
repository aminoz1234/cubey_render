// Puppet v2: one skeleton per character, limbs drawn every frame as continuous rounded tubes (IK arms, FK legs),
// real hand shapes, and a grip that sandwiches the prop between the palm layer and the finger layer.
// Layers (back to front): body (legs + torso), head, arms (+ palms), [prop goes here in 3D], fingers.
import { head as drawHead, CAST } from "./puppet.js";
export const U = 1000, CW = 1700, CH = 2500, FOOT = 70;       // canvas size and foot line (px)
const OUT = "#2b1b20", SKIN = "#f7e2bd", SKIN_D = "#d9b383", SKIN_L = "#fff6e2";
const LW = 7;

export const SKEL = {
  mom: { hip: 0.62, sh: 1.1, neck: 1.15, shW: 0.165, hipW: 0.07, up: 0.25, fo: 0.235, th: 0.31, sn: 0.29, armW: 0.072, foW: 0.05, legW: 0.05, hand: 1.0,
         sleeve: "elbow", sleeveCol: ["#e0604f", "#a63a33", "#ff9a7e"] },
  son: { hip: 0.5, sh: 0.9, neck: 0.95, shW: 0.14, hipW: 0.07, up: 0.21, fo: 0.195, th: 0.25, sn: 0.235, armW: 0.07, foW: 0.05, legW: 0.05, hand: 0.9,
         sleeve: "wrist", sleeveCol: ["#3f9a5e", "#24653c", "#7fd394"] },
};

const V = (x, y) => ({ x, y }), add = (a, b) => V(a.x + b.x, a.y + b.y), sub = (a, b) => V(a.x - b.x, a.y - b.y), mul = (a, k) => V(a.x * k, a.y * k);
const len = a => Math.hypot(a.x, a.y), nrm = a => mul(a, 1 / (len(a) || 1)), rot = (a, t) => V(a.x * Math.cos(t) - a.y * Math.sin(t), a.x * Math.sin(t) + a.y * Math.cos(t));
const P = (x, y) => V(CW / 2 + x * U, CH - FOOT - y * U);                 // units (y up) -> canvas px
const dirA = a => V(Math.sin(a), Math.cos(a));                            // angle 0 = straight down (canvas y down)

// 2-bone IK in canvas space. bend = +1 / -1 picks which way the elbow points.
function ik(a, t, l1, l2, bend) {
  let d = sub(t, a), D = len(d); const maxD = (l1 + l2) * 0.999; if (D > maxD) { t = add(a, mul(nrm(d), maxD)); d = sub(t, a); D = maxD; }
  D = Math.max(D, Math.abs(l1 - l2) + 1);
  const ca = (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D), ang = Math.acos(Math.max(-1, Math.min(1, ca)));
  const e = add(a, mul(rot(nrm(d), bend * ang), l1)); return [e, t];
}

// draw a tube polyline with round joins into an offscreen layer, shaded, then composite with an outline
export function tube(ctx, pts, ws, base, dark, light, outline = true) {
  const o = document.createElement("canvas"); o.width = CW; o.height = CH; const c = o.getContext("2d");
  c.lineCap = "round"; c.lineJoin = "round";
  const seg = (col, k, off) => { for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1], n = rot(nrm(sub(b, a)), -Math.PI / 2);
      const s = n.x + n.y < 0 ? 1 : -1;                                     // normal that faces the upper-left light
      c.strokeStyle = col; c.lineWidth = ws[i] * k; c.beginPath(); const sh = mul(n, s * off * ws[i]); c.moveTo(a.x + sh.x, a.y + sh.y); c.lineTo(b.x + sh.x, b.y + sh.y); c.stroke(); } };
  seg(base, 1, 0);
  c.globalCompositeOperation = "source-atop";
  seg(dark, 0.5, -0.34); seg(light, 0.3, 0.2);
  if (outline) { ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.strokeStyle = OUT; for (let i = 0; i < pts.length - 1; i++) { ctx.lineWidth = ws[i] + 2 * LW; ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[i + 1].x, pts[i + 1].y); ctx.stroke(); } }
  ctx.drawImage(o, 0, 0);
}
// sleeve: round at the shoulder, cut flat at the end with a visible opening
export function sleeve(ctx, pts, w, base, dark, light, cuffCol) {
  const o = document.createElement("canvas"); o.width = CW; o.height = CH; const c = o.getContext("2d");
  const path = (cc, ww) => { cc.lineJoin = "round"; cc.lineCap = "butt"; cc.lineWidth = ww; cc.beginPath(); cc.moveTo(pts[0].x, pts[0].y); for (const p of pts.slice(1)) cc.lineTo(p.x, p.y); cc.stroke();
    cc.beginPath(); cc.arc(pts[0].x, pts[0].y, ww / 2, 0, 7); cc.fill(); };
  ctx.strokeStyle = OUT; ctx.fillStyle = OUT; path(ctx, w + 2 * LW);
  c.strokeStyle = base; c.fillStyle = base; path(c, w);
  c.globalCompositeOperation = "source-atop";
  for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1], n = rot(nrm(sub(b, a)), -Math.PI / 2), s = n.x + n.y < 0 ? 1 : -1;
    for (const [col, k, off] of [[dark, 0.5, -0.34], [light, 0.3, 0.2]]) { const sh = mul(n, s * off * w); c.strokeStyle = col; c.lineWidth = w * k; c.lineCap = "round"; c.beginPath(); c.moveTo(a.x + sh.x, a.y + sh.y); c.lineTo(b.x + sh.x, b.y + sh.y); c.stroke(); } }
  ctx.drawImage(o, 0, 0);
  const a = pts[pts.length - 2], b = pts[pts.length - 1], d = nrm(sub(b, a)), ang = Math.atan2(d.y, d.x);
  ctx.beginPath(); ctx.ellipse(b.x, b.y, w * 0.17, w * 0.5 + LW / 2, ang, 0, Math.PI * 2); ctx.fillStyle = cuffCol; ctx.fill(); ctx.lineWidth = LW; ctx.strokeStyle = OUT; ctx.stroke();
  stitch(ctx, cc => { const q = sub(b, mul(d, w * 0.32)), n = rot(d, Math.PI / 2); cc.moveTo(q.x - n.x * w * 0.42, q.y - n.y * w * 0.42); cc.lineTo(q.x + n.x * w * 0.42, q.y + n.y * w * 0.42); }, "rgba(255,235,215,0.7)", 3, [8, 7]);
}
function blob(c, path, fill, lw = LW) { c.beginPath(); path(c); c.closePath(); c.fillStyle = fill; c.fill(); if (lw) { c.lineWidth = lw; c.strokeStyle = OUT; c.lineJoin = "round"; c.stroke(); } }
function shade(c, path, x, y, w, h, dark, light) {
  c.save(); c.beginPath(); path(c); c.closePath(); c.clip();
  let g = c.createRadialGradient(x + w * 0.3, y + h * 0.22, 0, x + w * 0.3, y + h * 0.22, Math.max(w, h) * 0.7); g.addColorStop(0, light); g.addColorStop(1, "rgba(0,0,0,0)"); c.fillStyle = g; c.fillRect(x, y, w, h);
  g = c.createRadialGradient(x + w, y + h, 0, x + w, y + h, Math.max(w, h) * 0.85); g.addColorStop(0, dark); g.addColorStop(1, "rgba(0,0,0,0)"); c.fillStyle = g; c.fillRect(x, y, w, h);
  c.restore();
}
function stitch(c, path, col, w = 3.5, dash = [11, 9]) { c.save(); c.setLineDash(dash); c.lineWidth = w; c.strokeStyle = col; c.lineCap = "round"; c.beginPath(); path(c); c.stroke(); c.restore(); }

// ---------------------------------------------------------------- hands
// local frame at the wrist: d = along the forearm, p = across (toward the thumb side)
function capsule(c, a, b, w, fill) { c.lineCap = "round"; c.strokeStyle = OUT; c.lineWidth = w + 2 * 6; c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke();
  c.strokeStyle = fill; c.lineWidth = w; c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke();
  c.strokeStyle = "rgba(255,255,245,0.55)"; c.lineWidth = w * 0.3; const n = mul(nrm(rot(sub(b, a), -Math.PI / 2)), w * 0.18); c.beginPath(); c.moveTo(a.x - n.x, a.y - n.y); c.lineTo(b.x - n.x, b.y - n.y); c.stroke(); }
function palm(c, at, d, p, r) {
  const path = cc => { cc.ellipse(at.x, at.y, r * 1.0, r * 1.12, Math.atan2(d.y, d.x) - Math.PI / 2, 0, Math.PI * 2); };
  blob(c, path, SKIN, 6); shade(c, path, at.x - r, at.y - r * 1.2, 2 * r, 2.4 * r, "rgba(170,110,60,0.55)", "rgba(255,255,240,0.75)");
}
export function hand(cb, cf, wrist, d, p, kind, s, opt = {}) {
  const r = 0.046 * U * s, at = add(wrist, mul(d, r * 0.95));
  const F = (base, ang, L, w = r * 0.42) => { const dd = rot(d, ang); return [add(at, add(mul(dd, r * 0.75), mul(p, base))), add(at, add(mul(dd, r * 0.75 + L), mul(p, base)))]; };
  if (kind === "open" || kind === "wave") {
    for (const [i, b] of [[-0.55, -0.32], [-0.18, -0.08], [0.18, 0.12], [0.52, 0.34]].entries()) { const [a, e] = F(b[0] * r, b[1], r * (i === 3 ? 0.55 : 0.72)); capsule(cb, a, e, r * 0.4, SKIN); }
    palm(cb, at, d, p, r);
    const t0 = add(at, mul(p, r * 0.75)), t1 = add(t0, add(mul(p, r * 0.5), mul(d, r * 0.2))); capsule(cb, t0, t1, r * 0.44, SKIN);
    cb.strokeStyle = "rgba(140,80,50,0.5)"; cb.lineWidth = 3.5; cb.beginPath(); cb.arc(at.x, at.y, r * 0.5, Math.atan2(d.y, d.x) - 0.8, Math.atan2(d.y, d.x) + 0.8); cb.stroke();
  } else if (kind === "fist" || kind === "point") {
    palm(cb, at, d, p, r * 1.02);
    cb.strokeStyle = "rgba(120,70,45,0.65)"; cb.lineWidth = 4; for (const k of [-0.45, 0, 0.45]) { const q = add(at, add(mul(d, r * 0.55), mul(p, k * r))); cb.beginPath(); cb.moveTo(q.x - d.x * r * 0.28, q.y - d.y * r * 0.28); cb.lineTo(q.x, q.y); cb.stroke(); }
    const t0 = add(at, add(mul(p, r * 0.7), mul(d, -r * 0.1))), t1 = add(at, add(mul(p, r * 0.05), mul(d, r * 0.25))); capsule(cf, t0, t1, r * 0.46, SKIN);
    if (kind === "point") { const [a, e] = F(-0.2 * r, 0, r * 1.05); capsule(cf, a, e, r * 0.42, SKIN); }
  } else if (kind === "grip") {
    // object axis o (unit, canvas space); palm sits behind the object, curled fingers wrap across the front
    const o = opt.axis || V(0, -1), q = rot(o, Math.PI / 2), c0 = opt.at || add(at, mul(d, r * 0.3)), rad = (opt.radius || 0.062) * U * (opt.scale || 1);
    palm(cb, add(c0, mul(q, -rad * 0.75 * (opt.side || 1))), d, p, r);
    const t0 = add(c0, add(mul(q, -rad * 0.9 * (opt.side || 1)), mul(o, r * 0.62))), t1 = add(c0, add(mul(q, rad * 0.1 * (opt.side || 1)), mul(o, r * 0.75)));
    capsule(cf, t0, t1, r * 0.44, SKIN);                                                         // thumb over the top
    for (let i = 0; i < 4; i++) { const y = (0.36 - i * 0.26) * r, a = add(c0, add(mul(o, y), mul(q, -rad * 0.8 * (opt.side || 1)))), e = add(c0, add(mul(o, y - r * 0.04), mul(q, rad * (0.55 - i * 0.05) * (opt.side || 1))));
      capsule(cf, a, e, r * 0.4, SKIN); }
  }
}

// ---------------------------------------------------------------- torso shapes (rounder bean bodies)
export function torsoMom(c, k, hip, sh, lean) {
  const H = (sh.y - hip.y), cx = hip.x;      // canvas: H < 0
  const skirt = cc => { cc.moveTo(cx - 0.17 * U, hip.y + 0.03 * U); cc.bezierCurveTo(cx - 0.2 * U, hip.y + 0.12 * U, cx - 0.25 * U, hip.y + 0.2 * U, cx - 0.255 * U, hip.y + 0.26 * U);
    cc.quadraticCurveTo(cx, hip.y + 0.3 * U, cx + 0.255 * U, hip.y + 0.26 * U); cc.bezierCurveTo(cx + 0.25 * U, hip.y + 0.2 * U, cx + 0.2 * U, hip.y + 0.12 * U, cx + 0.17 * U, hip.y + 0.03 * U); };
  blob(c, skirt, k.skirt); shade(c, skirt, cx - 0.26 * U, hip.y, 0.52 * U, 0.3 * U, "rgba(10,25,45,0.7)", "rgba(140,190,230,0.5)");
  c.strokeStyle = "rgba(10,25,45,0.45)"; c.lineWidth = 5; for (const dx of [-0.12, -0.04, 0.04, 0.12]) { c.beginPath(); c.moveTo(cx + dx * 0.8 * U, hip.y + 0.05 * U); c.quadraticCurveTo(cx + dx * U, hip.y + 0.15 * U, cx + dx * 1.35 * U, hip.y + 0.27 * U); c.stroke(); }
  stitch(c, cc => { cc.moveTo(cx - 0.24 * U, hip.y + 0.245 * U); cc.quadraticCurveTo(cx, hip.y + 0.28 * U, cx + 0.24 * U, hip.y + 0.245 * U); }, "rgba(200,225,240,0.8)");
  const body = cc => { const t = sh.y - 0.04 * U;
    cc.moveTo(cx, t - 0.015 * U); cc.bezierCurveTo(cx + 0.12 * U, t - 0.015 * U, cx + 0.175 * U, t + 0.01 * U, cx + 0.18 * U, t + 0.07 * U);
    cc.bezierCurveTo(cx + 0.2 * U, t + 0.25 * U, cx + 0.19 * U, hip.y - 0.06 * U, cx + 0.165 * U, hip.y + 0.06 * U); cc.quadraticCurveTo(cx, hip.y + 0.1 * U, cx - 0.165 * U, hip.y + 0.06 * U);
    cc.bezierCurveTo(cx - 0.19 * U, hip.y - 0.06 * U, cx - 0.2 * U, t + 0.25 * U, cx - 0.18 * U, t + 0.07 * U); cc.bezierCurveTo(cx - 0.175 * U, t + 0.01 * U, cx - 0.12 * U, t - 0.015 * U, cx, t - 0.015 * U); };
  blob(c, body, k.top); shade(c, body, cx - 0.2 * U, sh.y - 0.06 * U, 0.4 * U, hip.y - sh.y + 0.17 * U, "rgba(120,20,25,0.7)", "rgba(255,200,170,0.6)");
  for (const sx of [-1, 1]) blob(c, cc => { cc.moveTo(cx, sh.y - 0.03 * U); cc.quadraticCurveTo(cx + sx * 0.06 * U, sh.y - 0.06 * U, cx + sx * 0.1 * U, sh.y - 0.045 * U); cc.quadraticCurveTo(cx + sx * 0.08 * U, sh.y + 0.03 * U, cx + sx * 0.02 * U, sh.y + 0.04 * U); }, "#fff6e6", 6);
  const apron = cc => { const t = sh.y + 0.06 * U; cc.moveTo(cx - 0.085 * U, t); cc.quadraticCurveTo(cx, t - 0.012 * U, cx + 0.085 * U, t); cc.lineTo(cx + 0.1 * U, hip.y - 0.06 * U);
    cc.bezierCurveTo(cx + 0.16 * U, hip.y - 0.04 * U, cx + 0.17 * U, hip.y + 0.1 * U, cx + 0.16 * U, hip.y + 0.2 * U); cc.quadraticCurveTo(cx, hip.y + 0.225 * U, cx - 0.16 * U, hip.y + 0.2 * U);
    cc.bezierCurveTo(cx - 0.17 * U, hip.y + 0.1 * U, cx - 0.16 * U, hip.y - 0.04 * U, cx - 0.1 * U, hip.y - 0.06 * U); };
  blob(c, apron, k.apron); shade(c, apron, cx - 0.17 * U, sh.y + 0.06 * U, 0.34 * U, hip.y - sh.y + 0.17 * U, "rgba(150,115,70,0.55)", "rgba(255,255,250,0.7)");
  stitch(c, cc => { const t = sh.y + 0.075 * U; cc.moveTo(cx - 0.07 * U, t); cc.lineTo(cx - 0.085 * U, hip.y - 0.07 * U); cc.moveTo(cx + 0.07 * U, t); cc.lineTo(cx + 0.085 * U, hip.y - 0.07 * U); }, "rgba(170,120,80,0.8)");
  stitch(c, cc => { cc.moveTo(cx - 0.14 * U, hip.y + 0.185 * U); cc.quadraticCurveTo(cx, hip.y + 0.205 * U, cx + 0.14 * U, hip.y + 0.185 * U); }, "rgba(170,120,80,0.8)");
  blob(c, cc => { cc.moveTo(cx - 0.07 * U, hip.y + 0.03 * U); cc.lineTo(cx + 0.07 * U, hip.y + 0.03 * U); cc.quadraticCurveTo(cx + 0.072 * U, hip.y + 0.12 * U, cx + 0.06 * U, hip.y + 0.13 * U); cc.quadraticCurveTo(cx, hip.y + 0.142 * U, cx - 0.06 * U, hip.y + 0.13 * U); cc.quadraticCurveTo(cx - 0.072 * U, hip.y + 0.12 * U, cx - 0.07 * U, hip.y + 0.03 * U); }, "#faf2df", 5);
  c.fillStyle = "#e0604f"; for (const [hx, hy] of [[-0.03, 0.08], [0.01, 0.065], [0.037, 0.095]]) { c.beginPath(); c.arc(cx + hx * U, hip.y + hy * U, 9, 0, 7); c.fill(); }
  blob(c, cc => { cc.moveTo(cx - 0.155 * U, hip.y - 0.075 * U); cc.quadraticCurveTo(cx, hip.y - 0.085 * U, cx + 0.155 * U, hip.y - 0.075 * U); cc.lineTo(cx + 0.16 * U, hip.y - 0.04 * U); cc.quadraticCurveTo(cx, hip.y - 0.05 * U, cx - 0.16 * U, hip.y - 0.04 * U); }, "#efe2c4", 6);
  blob(c, cc => { cc.moveTo(cx + 0.15 * U, hip.y - 0.06 * U); cc.quadraticCurveTo(cx + 0.22 * U, hip.y - 0.02 * U, cx + 0.2 * U, hip.y + 0.07 * U); cc.quadraticCurveTo(cx + 0.19 * U, hip.y + 0.0 * U, cx + 0.15 * U, hip.y - 0.04 * U); }, "#efe2c4", 5);
}
export function torsoSon(c, k, hip, sh) {
  const cx = hip.x;
  const shorts = cc => { cc.moveTo(cx - 0.135 * U, hip.y - 0.04 * U); cc.lineTo(cx + 0.135 * U, hip.y - 0.04 * U); cc.quadraticCurveTo(cx + 0.155 * U, hip.y + 0.06 * U, cx + 0.15 * U, hip.y + 0.13 * U);
    cc.quadraticCurveTo(cx + 0.08 * U, hip.y + 0.145 * U, cx + 0.02 * U, hip.y + 0.13 * U); cc.lineTo(cx, hip.y + 0.06 * U); cc.lineTo(cx - 0.02 * U, hip.y + 0.13 * U);
    cc.quadraticCurveTo(cx - 0.08 * U, hip.y + 0.145 * U, cx - 0.15 * U, hip.y + 0.13 * U); cc.quadraticCurveTo(cx - 0.155 * U, hip.y + 0.06 * U, cx - 0.135 * U, hip.y - 0.04 * U); };
  blob(c, shorts, k.shorts); shade(c, shorts, cx - 0.16 * U, hip.y - 0.04 * U, 0.32 * U, 0.19 * U, "rgba(10,20,50,0.7)", "rgba(150,190,255,0.5)");
  stitch(c, cc => { cc.moveTo(cx - 0.14 * U, hip.y + 0.11 * U); cc.lineTo(cx - 0.035 * U, hip.y + 0.115 * U); cc.moveTo(cx + 0.035 * U, hip.y + 0.115 * U); cc.lineTo(cx + 0.14 * U, hip.y + 0.11 * U); }, "rgba(240,200,120,0.85)", 3, [8, 7]);
  const body = cc => { const t = sh.y - 0.035 * U;
    cc.moveTo(cx, t - 0.012 * U); cc.bezierCurveTo(cx + 0.1 * U, t - 0.012 * U, cx + 0.15 * U, t + 0.01 * U, cx + 0.155 * U, t + 0.07 * U);
    cc.bezierCurveTo(cx + 0.175 * U, t + 0.2 * U, cx + 0.17 * U, hip.y - 0.04 * U, cx + 0.15 * U, hip.y + 0.02 * U); cc.quadraticCurveTo(cx, hip.y + 0.06 * U, cx - 0.15 * U, hip.y + 0.02 * U);
    cc.bezierCurveTo(cx - 0.17 * U, hip.y - 0.04 * U, cx - 0.175 * U, t + 0.2 * U, cx - 0.155 * U, t + 0.07 * U); cc.bezierCurveTo(cx - 0.15 * U, t + 0.01 * U, cx - 0.1 * U, t - 0.012 * U, cx, t - 0.012 * U); };
  blob(c, body, k.top); shade(c, body, cx - 0.18 * U, sh.y - 0.05 * U, 0.36 * U, hip.y - sh.y + 0.12 * U, "rgba(10,60,30,0.72)", "rgba(190,255,200,0.55)");
  stitch(c, cc => { cc.moveTo(cx - 0.14 * U, hip.y - 0.005 * U); cc.quadraticCurveTo(cx, hip.y + 0.03 * U, cx + 0.14 * U, hip.y - 0.005 * U); }, "rgba(200,255,210,0.7)");
  blob(c, cc => { cc.moveTo(cx - 0.11 * U, sh.y - 0.03 * U); cc.quadraticCurveTo(cx, sh.y + 0.07 * U, cx + 0.11 * U, sh.y - 0.03 * U); cc.quadraticCurveTo(cx, sh.y + 0.01 * U, cx - 0.11 * U, sh.y - 0.03 * U); }, k.topD, 6);
  for (const sx of [-1, 1]) { c.lineWidth = 7; c.strokeStyle = "#f6f1e4"; c.lineCap = "round"; c.beginPath(); c.moveTo(cx + sx * 0.028 * U, sh.y + 0.02 * U); c.quadraticCurveTo(cx + sx * 0.036 * U, sh.y + 0.1 * U, cx + sx * 0.03 * U, sh.y + 0.15 * U); c.stroke();
    blob(c, cc => cc.arc(cx + sx * 0.03 * U, sh.y + 0.156 * U, 9, 0, 7), "#d8d0bc", 4); }
  const pk = cc => { cc.moveTo(cx - 0.09 * U, hip.y - 0.13 * U); cc.quadraticCurveTo(cx, hip.y - 0.14 * U, cx + 0.09 * U, hip.y - 0.13 * U); cc.quadraticCurveTo(cx + 0.125 * U, hip.y - 0.06 * U, cx + 0.12 * U, hip.y - 0.02 * U); cc.quadraticCurveTo(cx, hip.y, cx - 0.12 * U, hip.y - 0.02 * U); cc.quadraticCurveTo(cx - 0.125 * U, hip.y - 0.06 * U, cx - 0.09 * U, hip.y - 0.13 * U); };
  blob(c, pk, "rgba(44,128,76,1)", 6); stitch(c, cc => { cc.moveTo(cx - 0.08 * U, hip.y - 0.118 * U); cc.quadraticCurveTo(cx, hip.y - 0.128 * U, cx + 0.08 * U, hip.y - 0.118 * U); }, "rgba(200,255,210,0.7)", 3, [8, 7]);
  blob(c, cc => cc.arc(cx + 0.07 * U, sh.y + 0.08 * U, 20, 0, 7), "#ffd23a", 5); c.fillStyle = OUT; c.beginPath(); c.arc(cx + 0.064 * U, sh.y + 0.076 * U, 3.5, 0, 7); c.arc(cx + 0.077 * U, sh.y + 0.076 * U, 3.5, 0, 7); c.fill();
}
export function shoe(c, who, ankle, side, k) {
  const s = who === "son" ? 0.9 : 1, f = side, a = ankle;
  const path = cc => { cc.moveTo(a.x - f * 0.035 * U * s, a.y - 0.02 * U * s); cc.quadraticCurveTo(a.x + f * 0.01 * U * s, a.y - 0.035 * U * s, a.x + f * 0.04 * U * s, a.y - 0.012 * U * s);
    cc.bezierCurveTo(a.x + f * 0.1 * U * s, a.y - 0.0 * U * s, a.x + f * 0.115 * U * s, a.y + 0.02 * U * s, a.x + f * 0.11 * U * s, a.y + 0.05 * U * s);
    cc.lineTo(a.x - f * 0.045 * U * s, a.y + 0.05 * U * s); cc.quadraticCurveTo(a.x - f * 0.055 * U * s, a.y + 0.01 * U * s, a.x - f * 0.035 * U * s, a.y - 0.02 * U * s); };
  blob(c, path, k.shoe); shade(c, path, a.x - 0.06 * U, a.y - 0.04 * U, 0.17 * U, 0.09 * U, "rgba(40,10,10,0.5)", "rgba(255,255,255,0.65)");
  if (who === "son") { c.fillStyle = k.shoeTrim; c.fillRect(Math.min(a.x - f * 0.045 * U * s, a.x + f * 0.11 * U * s), a.y + 0.033 * U * s, 0.155 * U * s, 0.017 * U * s);
    stitch(c, cc => { cc.moveTo(a.x - f * 0.0 * U, a.y - 0.02 * U); cc.lineTo(a.x + f * 0.04 * U, a.y - 0.005 * U); }, "#d8432f", 4, [6, 6]); }
}

// ---------------------------------------------------------------- one frame, one character, four layers
// pose: { x?, lean (deg, + = toward screen right), bounce (units), tilt (deg), head:{...expr},
//         armL/armR: { to:[x,y] units in body space | "mouth" | "hip" | "chest", bend:+1/-1, hand:'open'|'fist'|'point'|'grip', handAng (deg), grip:{axisDeg, radius} },
//         legL/legR: [hipDeg, kneeDeg] }
export function frame(layers, who, pose) {
  const k = CAST[who], S = SKEL[who], [cb, ch, ca, cf] = layers;
  for (const c of layers) c.clearRect(0, 0, CW, CH);
  const lean = (pose.lean || 0) * Math.PI / 180, bo = pose.bounce || 0;
  const hip = P(0, S.hip + bo);
  const up = p => add(hip, rot(sub(p, hip), lean));                       // rotate the upper body about the hips
  const sh = up(P(0, S.sh + bo)), neck = up(P(0, S.neck + bo));
  // legs (FK), drawn first on the body layer
  for (const side of [-1, 1]) {
    const [ha, ka] = pose[side < 0 ? "legL" : "legR"] || [0, 0], h0 = P(side * S.hipW, S.hip + bo);
    const kn = add(h0, mul(dirA(ha * Math.PI / 180 * -side), S.th * U)), an = add(kn, mul(dirA((ha - ka) * Math.PI / 180 * -side), S.sn * U));
    const skinTube = [SKIN, "rgba(170,110,60,0.6)", "rgba(255,255,240,0.6)"];
    tube(cb, [h0, kn, an], [S.legW * U, S.legW * U * 0.92], ...skinTube);
    if (who === "son") { tube(cb, [add(an, V(0, -0.075 * U)), add(an, V(0, -0.01 * U))], [S.legW * U * 1.15], "#ffffff", "rgba(120,120,120,0.4)", "rgba(255,255,255,0.8)");
      cb.strokeStyle = k.shoeTrim; cb.lineWidth = 6; cb.beginPath(); cb.moveTo(an.x - 0.03 * U, an.y - 0.055 * U); cb.lineTo(an.x + 0.03 * U, an.y - 0.055 * U); cb.stroke(); }
    shoe(cb, who, an, side, k);
  }
  cb.save(); cb.translate(hip.x, hip.y); cb.rotate(lean); cb.translate(-hip.x, -hip.y);
  (who === "mom" ? torsoMom : torsoSon)(cb, k, hip, P(0, S.sh + bo), lean); cb.restore();
  // head on its own layer
  const hc = document.createElement("canvas"); hc.width = 1100; hc.height = 1100; const hm = drawHead(hc.getContext("2d"), who, pose.head || {});
  ch.save(); ch.translate(neck.x, neck.y); ch.rotate(lean + (pose.tilt || 0) * Math.PI / 180); ch.drawImage(hc, -hm.pivot[0], -hm.pivot[1]); ch.restore();
  // anchor points the hands can reach for (canvas px)
  const headC = add(neck, rot(V(0, -(k.headR * U * 0.92)), lean + (pose.tilt || 0) * Math.PI / 180));
  const anchors = { mouth: add(headC, rot(V(0, k.headR * U * 0.5), lean + (pose.tilt || 0) * Math.PI / 180)), chest: up(P(0, S.sh + bo - 0.12)), hipL: up(P(-0.17, S.hip + bo + 0.05)), hipR: up(P(0.17, S.hip + bo + 0.05)) };
  const out = { grips: {} };
  // arms: IK to a target, sleeve over the upper arm, skin forearm, then the hand
  for (const side of [-1, 1]) {
    const A = pose[side < 0 ? "armL" : "armR"]; if (!A) continue;
    const s0 = up(P(side * S.shW, S.sh + bo - 0.02));
    let tgt = typeof A.to === "string" ? (A.to === "hip" ? anchors[side < 0 ? "hipL" : "hipR"] : anchors[A.to]) : up(P(A.to[0] * side, A.to[1] + bo));
    if (A.off) tgt = add(tgt, V(A.off[0] * U * side, -A.off[1] * U));
    const [el, wr] = ik(s0, tgt, S.up * U, S.fo * U, (A.bend ?? 1) * side);
    const [base, dark, light] = S.sleeveCol;
    if (S.sleeve === "wrist") { const end = add(wr, mul(nrm(sub(el, wr)), 0.012 * U)); sleeve(ca, [s0, el, end], S.armW * U, base, dark, light, "#1d4a2c"); }
    else { tube(ca, [s0, el, wr], [S.foW * U * 1.05, S.foW * U * 0.92], SKIN, "rgba(170,110,60,0.6)", "rgba(255,255,240,0.6)");
      const mid = add(s0, mul(sub(el, s0), 0.8)); sleeve(ca, [s0, mid], S.armW * U * 1.1, base, dark, light, "#7a2622"); }
    const d = nrm(sub(wr, el)); let hd = A.handAng != null ? rot(V(0, 1), A.handAng * Math.PI / 180 * -side + lean) : d;
    const p = mul(rot(hd, -Math.PI / 2), -side);
    let gopt = {};
    if (A.hand === "grip") { const ax = rot(V(0, -1), ((A.grip?.axisDeg) || 0) * Math.PI / 180 + lean); const r = 0.046 * U * S.hand;
      const c0 = add(wr, mul(hd, r * 1.15)); gopt = { axis: ax, at: c0, radius: A.grip?.radius || 0.062, scale: 1 / 1.3, side };
      out.grips[side < 0 ? "L" : "R"] = { x: (c0.x - CW / 2) / U, y: (CH - FOOT - c0.y) / U, axisDeg: ((A.grip?.axisDeg) || 0) + (pose.lean || 0) }; }
    hand(ca, cf, wr, hd, p, A.hand || "open", S.hand, gopt);
  }
  return out;
}
