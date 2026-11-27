// Paper-puppet parts in the Ricks/Boris look: painted gradients, thin warm outlines, stitching, glossy eyes.
// Every part is drawn at U px per world unit; pivots are returned in px so Blender can place them.
export const U = 1000;
const OUT = "#2b1b20", SKIN = "#f7e2bd", SKIN_D = "#dcb789", SKIN_L = "#fff3dc";
const LW = 7;

function grad(c, x0, y0, x1, y1, stops) { const g = c.createLinearGradient(x0, y0, x1, y1); stops.forEach(([o, col]) => g.addColorStop(o, col)); return g; }
function rgrad(c, x, y, r0, x1, y1, r1, stops) { const g = c.createRadialGradient(x, y, r0, x1, y1, r1); stops.forEach(([o, col]) => g.addColorStop(o, col)); return g; }
function fillPath(c, path, fill, lw = LW, stroke = OUT) { c.beginPath(); path(c); c.closePath(); c.fillStyle = fill; c.fill(); if (lw) { c.lineWidth = lw; c.strokeStyle = stroke; c.lineJoin = "round"; c.stroke(); } }
function clipTo(c, path, fn) { c.save(); c.beginPath(); path(c); c.closePath(); c.clip(); fn(); c.restore(); }
function stitch(c, path, col = "rgba(255,240,200,0.9)", w = 3.5, dash = [11, 9]) { c.save(); c.setLineDash(dash); c.lineWidth = w; c.strokeStyle = col; c.lineCap = "round"; c.beginPath(); path(c); c.stroke(); c.restore(); }
function noise(c, w, h, n, col, r = 2.2, seed = 1) { let s = seed; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647); c.fillStyle = col; for (let i = 0; i < n; i++) { c.beginPath(); c.arc(rnd() * w, rnd() * h, r * (0.5 + rnd()), 0, 7); c.fill(); } }
// soft painted shading inside a shape: light from upper-left, core shadow lower-right, warm bounce at the rim
function paint(c, path, base, dark, light, bx) {
  clipTo(c, path, () => {
    c.fillStyle = base; c.fillRect(bx[0], bx[1], bx[2], bx[3]);
    c.fillStyle = rgrad(c, bx[0] + bx[2] * 0.3, bx[1] + bx[3] * 0.25, 0, bx[0] + bx[2] * 0.3, bx[1] + bx[3] * 0.25, Math.max(bx[2], bx[3]) * 0.75, [[0, light], [0.55, "rgba(0,0,0,0)"]]); c.fillRect(bx[0], bx[1], bx[2], bx[3]);
    c.fillStyle = rgrad(c, bx[0] + bx[2] * 0.95, bx[1] + bx[3] * 1.0, 0, bx[0] + bx[2] * 0.95, bx[1] + bx[3] * 1.0, Math.max(bx[2], bx[3]) * 0.8, [[0, dark], [0.75, "rgba(0,0,0,0)"]]); c.fillRect(bx[0], bx[1], bx[2], bx[3]);
  });
}

export const CAST = {
  mom: { hair: "#5a3020", hairL: "#8a4a2c", hairD: "#331810", brow: "#4a2416", top: "#e0604f", topD: "#a63a33", topL: "#ff9a7e",
         apron: "#f4ead2", apronD: "#c9b48f", skirt: "#2f5a78", skirtD: "#1c3850", shoe: "#b8322b", lash: true, scale: 1.0, headR: 0.36 },
  son: { hair: "#7a3e1c", hairL: "#a8602c", hairD: "#4a2410", brow: "#6a2e14", cap: "#d8432f", capD: "#922a20", capL: "#ff7e5c", top: "#3f9a5e", topD: "#24653c", topL: "#7fd394",
         shorts: "#3d5f9c", shortsD: "#253d6c", shoe: "#f2f2ea", shoeTrim: "#d8432f", freckles: true, scale: 0.8, headR: 0.34 },
};

// ---------------------------------------------------------------- head (drawn every frame: eyes, brows, mouth change)
// expr: { mouth: smile|flat|shock|rant|frown|sip|grin, talk 0..1, brows: angry|up|sad|flat|smug, eyes:[dx,dy], blink 0..1, sweat }
export function head(c, who, e) {
  const k = CAST[who], W = 1100, H = 1100, cx = 550, cy = 600, R = k.headR * U;
  c.clearRect(0, 0, W, H);
  const circ = cc => cc.arc(cx, cy, R, 0, Math.PI * 2);
  // back hair (behind head)
  if (who === "mom") {
    fillPath(c, cc => { cc.arc(cx + 10, cy - R * 1.02, R * 0.36, 0, Math.PI * 2); }, rgrad(c, cx - 40, cy - R * 1.15, 10, cx, cy - R, R * 0.4, [[0, k.hairL], [1, k.hair]]));
    stitch(c, cc => { cc.arc(cx + 10, cy - R * 1.02, R * 0.22, 3.6, 5.6); }, "rgba(40,15,10,0.45)", 4, [20, 10]);
    fillPath(c, cc => { cc.moveTo(cx - R * 1.06, cy + R * 0.25); cc.quadraticCurveTo(cx - R * 1.2, cy - R * 0.9, cx, cy - R * 1.05); cc.quadraticCurveTo(cx + R * 1.2, cy - R * 0.9, cx + R * 1.06, cy + R * 0.25);
      cc.quadraticCurveTo(cx + R * 1.0, cy + R * 0.42, cx + R * 0.86, cy + R * 0.3); cc.lineTo(cx - R * 0.86, cy + R * 0.3); cc.quadraticCurveTo(cx - R * 1.0, cy + R * 0.42, cx - R * 1.06, cy + R * 0.25); }, k.hairD);
  } else {
    for (const sx of [-1, 1]) fillPath(c, cc => { cc.moveTo(cx + sx * R * 0.8, cy - R * 0.2); cc.lineTo(cx + sx * R * 1.08, cy + R * 0.02); cc.lineTo(cx + sx * R * 0.95, cy + R * 0.08); cc.lineTo(cx + sx * R * 1.1, cy + R * 0.22); cc.lineTo(cx + sx * R * 0.86, cy + R * 0.2); }, k.hair, 5);
  }
  // ears
  for (const sx of [-1, 1]) { fillPath(c, cc => cc.ellipse(cx + sx * R * 0.97, cy + R * 0.12, R * 0.13, R * 0.17, 0, 0, Math.PI * 2), SKIN_D, 6); }
  // the head: painted sphere
  fillPath(c, circ, SKIN, 0);
  clipTo(c, circ, () => {
    c.fillStyle = rgrad(c, cx - R * 0.35, cy - R * 0.45, R * 0.05, cx - R * 0.2, cy - R * 0.25, R * 1.1, [[0, SKIN_L], [0.45, SKIN], [1, SKIN_D]]); c.fillRect(cx - R, cy - R, 2 * R, 2 * R);
    c.fillStyle = rgrad(c, cx + R * 0.55, cy + R * 0.75, 0, cx + R * 0.55, cy + R * 0.75, R * 0.9, [[0, "rgba(190,120,80,0.35)"], [1, "rgba(190,120,80,0)"]]); c.fillRect(cx - R, cy - R, 2 * R, 2 * R);
    // blush
    for (const sx of [-1, 1]) { c.fillStyle = rgrad(c, cx + sx * R * 0.52, cy + R * 0.3, 0, cx + sx * R * 0.52, cy + R * 0.3, R * 0.24, [[0, "rgba(245,120,110,0.55)"], [1, "rgba(245,120,110,0)"]]); c.fillRect(cx - R, cy - R, 2 * R, 2 * R); }
    if (k.freckles) { c.fillStyle = "rgba(170,90,50,0.55)"; for (const [fx, fy] of [[-0.6, 0.18], [-0.5, 0.26], [-0.42, 0.17], [0.42, 0.17], [0.5, 0.26], [0.6, 0.18]]) { c.beginPath(); c.arc(cx + fx * R, cy + fy * R, 6, 0, 7); c.fill(); } }
  });
  c.lineWidth = LW + 2; c.strokeStyle = OUT; c.beginPath(); circ(c); c.stroke();
  // front hair / cap
  if (who === "mom") {
    const bang = cc => { cc.moveTo(cx - R * 0.98, cy - R * 0.05); cc.quadraticCurveTo(cx - R * 0.95, cy - R * 1.0, cx, cy - R * 1.02); cc.quadraticCurveTo(cx + R * 0.95, cy - R * 1.0, cx + R * 0.98, cy - R * 0.05);
      cc.quadraticCurveTo(cx + R * 0.7, cy - R * 0.55, cx + R * 0.15, cy - R * 0.5); cc.quadraticCurveTo(cx - R * 0.1, cy - R * 0.62, cx - R * 0.3, cy - R * 0.48); cc.quadraticCurveTo(cx - R * 0.75, cy - R * 0.5, cx - R * 0.98, cy - R * 0.05); };
    fillPath(c, bang, k.hair);
    clipTo(c, bang, () => { c.fillStyle = rgrad(c, cx - R * 0.4, cy - R * 0.9, 0, cx - R * 0.3, cy - R * 0.8, R * 0.9, [[0, k.hairL], [1, "rgba(0,0,0,0)"]]); c.fillRect(cx - R, cy - R * 1.1, 2 * R, R);
      c.strokeStyle = "rgba(255,200,160,0.45)"; c.lineWidth = 5; for (let i = -3; i <= 3; i++) { c.beginPath(); c.moveTo(cx + i * R * 0.18, cy - R * 0.98); c.quadraticCurveTo(cx + i * R * 0.24, cy - R * 0.75, cx + i * R * 0.3, cy - R * 0.55); c.stroke(); } });
  } else {
    const dome = cc => { cc.moveTo(cx - R * 0.99, cy - R * 0.3); cc.bezierCurveTo(cx - R * 1.04, cy - R * 1.3, cx + R * 1.04, cy - R * 1.3, cx + R * 0.99, cy - R * 0.3); cc.quadraticCurveTo(cx, cy - R * 0.5, cx - R * 0.99, cy - R * 0.3); };
    fillPath(c, dome, k.cap);
    clipTo(c, dome, () => { c.fillStyle = rgrad(c, cx - R * 0.45, cy - R * 0.9, 0, cx - R * 0.3, cy - R * 0.7, R * 1.2, [[0, k.capL], [0.5, k.cap], [1, k.capD]]); c.fillRect(cx - R * 1.1, cy - R * 1.2, 2.2 * R, R * 1.1);
      fillPath(c, cc => { cc.moveTo(cx - R * 0.45, cy - R * 0.44); cc.quadraticCurveTo(cx - R * 0.42, cy - R * 0.98, cx, cy - R * 0.98); cc.quadraticCurveTo(cx + R * 0.42, cy - R * 0.98, cx + R * 0.45, cy - R * 0.44); }, "rgba(255,248,235,0.95)", 5); });
    stitch(c, cc => { cc.moveTo(cx - R * 0.9, cy - R * 0.42); cc.quadraticCurveTo(cx, cy - R * 0.58, cx + R * 0.9, cy - R * 0.42); }, "rgba(255,230,200,0.9)");
    stitch(c, cc => { cc.moveTo(cx - R * 0.38, cy - R * 0.4); cc.quadraticCurveTo(cx - R * 0.36, cy - R * 0.9, cx, cy - R * 0.9); }, "rgba(200,60,40,0.7)", 3);
    fillPath(c, cc => cc.arc(cx, cy - R * 1.0, 22, 0, 7), k.capD, 5);
    // brim toward camera-left, painted underside
    const brim = cc => { cc.moveTo(cx - R * 0.95, cy - R * 0.34); cc.quadraticCurveTo(cx - R * 1.6, cy - R * 0.32, cx - R * 1.62, cy - R * 0.17); cc.quadraticCurveTo(cx - R * 1.3, cy - R * 0.1, cx - R * 0.6, cy - R * 0.24); cc.quadraticCurveTo(cx - R * 0.8, cy - R * 0.34, cx - R * 0.95, cy - R * 0.34); };
    fillPath(c, brim, grad(c, cx - R * 1.6, 0, cx - R * 0.6, 0, [[0, k.cap], [1, k.capD]]));
    stitch(c, cc => { cc.moveTo(cx - R * 1.5, cy - R * 0.24); cc.quadraticCurveTo(cx - R * 1.2, cy - R * 0.17, cx - R * 0.75, cy - R * 0.26); }, "rgba(255,230,200,0.85)", 3, [8, 7]);
    // tufts under the cap
    for (const [tx, s] of [[-0.85, -1], [0.82, 1]]) fillPath(c, cc => { cc.moveTo(cx + tx * R, cy - R * 0.34); cc.lineTo(cx + (tx + s * 0.16) * R, cy - R * 0.02); cc.lineTo(cx + (tx + s * 0.02) * R, cy - R * 0.08); cc.lineTo(cx + (tx + s * 0.08) * R, cy + R * 0.08); cc.lineTo(cx + (tx - s * 0.1) * R, cy - R * 0.1); }, k.hair, 5);
  }
  // ----- face
  const [edx, edy] = e.eyes || [0, 0], bl = Math.min(1, e.blink || 0), ex0 = R * 0.33, ey0 = cy + R * 0.0;
  for (const sx of [-1, 1]) {
    const x = cx + sx * ex0 + edx * R * 0.05, y = ey0 + edy * R * 0.05, rw = R * 0.1, rh = R * 0.15 * (e.brows === "up" ? 1.12 : 1);
    if (bl > 0.6) { c.lineWidth = 9; c.strokeStyle = OUT; c.lineCap = "round"; c.beginPath(); c.arc(x, y - rh * 0.2, rw * 1.05, 0.15 * Math.PI, 0.85 * Math.PI); c.stroke(); continue; }
    c.fillStyle = "#1c1216"; c.beginPath(); c.ellipse(x, y, rw, rh * (1 - bl * 0.8), 0, 0, Math.PI * 2); c.fill();
    c.fillStyle = "#ffffff"; c.beginPath(); c.arc(x - rw * 0.3, y - rh * 0.38, rw * 0.36, 0, 7); c.fill(); c.beginPath(); c.arc(x + rw * 0.35, y + rh * 0.25, rw * 0.16, 0, 7); c.fill();
    if (k.lash) { c.lineWidth = 7; c.strokeStyle = "#1c1216"; c.lineCap = "round"; c.beginPath(); c.moveTo(x + sx * rw * 0.8, y - rh * 0.55); c.lineTo(x + sx * rw * 1.5, y - rh * 0.85); c.stroke(); }
  }
  // brows: thick rounded capsules
  const B = { angry: [0.32, 0], up: [-0.12, -0.16], sad: [-0.3, -0.04], flat: [0, 0], smug: [0.1, 0] }[e.brows || "flat"];
  for (const sx of [-1, 1]) {
    const x = cx + sx * ex0, y = ey0 - R * (who === "son" ? 0.22 : 0.33) + B[1] * R, a = -sx * B[0] * (e.brows === "smug" && sx < 0 ? -1 : 1);
    c.save(); c.translate(x, y); c.rotate(a); c.lineCap = "round"; c.lineWidth = R * 0.1; c.strokeStyle = OUT; c.beginPath(); c.moveTo(-R * 0.14, R * 0.02); c.quadraticCurveTo(0, -R * 0.05, R * 0.14, R * 0.02); c.stroke();
    c.lineWidth = R * 0.072; c.strokeStyle = k.brow; c.stroke(); c.restore();
  }
  // nose: little check
  c.lineWidth = 7; c.strokeStyle = "rgba(60,30,25,0.85)"; c.lineCap = "round"; c.beginPath(); c.moveTo(cx - R * 0.02, cy + R * 0.12); c.quadraticCurveTo(cx - R * 0.08, cy + R * 0.24, cx + R * 0.05, cy + R * 0.24); c.stroke();
  // mouth
  const m = e.mouth || "flat", my = cy + R * 0.48, o = e.talk ?? 0.6;
  const teethRow = (x0, x1, y, h, n) => { c.fillStyle = "#fffdf6"; c.fillRect(x0, y, x1 - x0, h); c.strokeStyle = "rgba(60,30,30,0.5)"; c.lineWidth = 3; for (let i = 1; i < n; i++) { const x = x0 + (x1 - x0) * i / n; c.beginPath(); c.moveTo(x, y); c.lineTo(x, y + h); c.stroke(); } };
  if (m === "smile" || m === "sip") { c.lineWidth = 9; c.strokeStyle = OUT; c.beginPath(); c.arc(cx, my - R * 0.18, R * 0.16, 0.22 * Math.PI, 0.78 * Math.PI); c.stroke(); }
  else if (m === "flat") { c.lineWidth = 9; c.strokeStyle = OUT; c.beginPath(); c.moveTo(cx - R * 0.1, my); c.quadraticCurveTo(cx, my + 4, cx + R * 0.1, my - 2); c.stroke(); }
  else if (m === "frown") { c.lineWidth = 9; c.strokeStyle = OUT; c.beginPath(); c.arc(cx, my + R * 0.16, R * 0.13, 1.22 * Math.PI, 1.78 * Math.PI); c.stroke(); }
  else if (m === "grin") { const mp = cc => { cc.moveTo(cx - R * 0.32, my - R * 0.08); cc.quadraticCurveTo(cx, my + R * 0.36, cx + R * 0.32, my - R * 0.08); cc.quadraticCurveTo(cx, my + R * 0.02, cx - R * 0.32, my - R * 0.08); };
    fillPath(c, mp, "#fffdf6", 8); clipTo(c, mp, () => { c.strokeStyle = "rgba(60,30,30,0.55)"; c.lineWidth = 4; for (let i = -3; i <= 3; i++) { c.beginPath(); c.moveTo(cx + i * R * 0.085, my - R * 0.1); c.lineTo(cx + i * R * 0.085, my + R * 0.3); c.stroke(); } c.beginPath(); c.moveTo(cx - R * 0.4, my + R * 0.06); c.quadraticCurveTo(cx, my + R * 0.16, cx + R * 0.4, my + R * 0.06); c.stroke(); }); }
  else { // open: shock (round O) or rant (wide, top teeth, tongue)
    const shock = m === "shock", w = shock ? R * 0.12 : R * (0.2 + 0.06 * o), h = shock ? R * 0.17 : R * (0.06 + 0.2 * o);
    const mp = cc => cc.ellipse(cx, my + h * 0.3, w, h, 0, 0, Math.PI * 2);
    fillPath(c, mp, "#5a1c20", 8);
    clipTo(c, mp, () => { c.fillStyle = "#e86a6a"; c.beginPath(); c.ellipse(cx + w * 0.1, my + h * 1.15, w * 0.8, h * 0.6, 0, 0, 7); c.fill(); if (!shock) teethRow(cx - w, cx + w, my + h * 0.3 - h, h * 0.42, 6); });
  }
  if (e.sweat) fillPath(c, cc => { const x = cx + R * 0.8, y = cy - R * 0.08; cc.moveTo(x, y - 46); cc.quadraticCurveTo(x + 32, y + 6, x, y + 26); cc.quadraticCurveTo(x - 32, y + 6, x, y - 46); }, grad(c, 0, cy - R * 0.5, 0, cy - R * 0.3, [[0, "#d8f4ff"], [1, "#6cc6f0"]]), 5);
  return { pivot: [cx, cy + R * 0.92], W, H };     // neck point
}

// ---------------------------------------------------------------- static parts (drawn once)
export const PARTS = {
  torso(c, who) {     // pivot at the hips; returns attach points
    const k = CAST[who];
    if (who === "mom") {
      const W = 620, H = 900, cx = 310, top = 150, hip = 640;
      c.clearRect(0, 0, W, H);
      const skirt = cc => { cc.moveTo(cx - 175, hip - 40); cc.lineTo(cx + 175, hip - 40); cc.quadraticCurveTo(cx + 230, hip + 120, cx + 250, hip + 220); cc.quadraticCurveTo(cx, hip + 250, cx - 250, hip + 220); cc.quadraticCurveTo(cx - 230, hip + 120, cx - 175, hip - 40); };
      fillPath(c, skirt, k.skirt); paint(c, skirt, k.skirt, "rgba(10,25,45,0.7)", "rgba(120,170,210,0.55)", [cx - 260, hip - 40, 520, 280]);
      c.strokeStyle = "rgba(10,25,45,0.5)"; c.lineWidth = 5; for (const dx of [-120, -40, 40, 120]) { c.beginPath(); c.moveTo(cx + dx * 0.7, hip); c.quadraticCurveTo(cx + dx * 1.0, hip + 120, cx + dx * 1.3, hip + 225); c.stroke(); }
      stitch(c, cc => { cc.moveTo(cx - 240, hip + 200); cc.quadraticCurveTo(cx, hip + 228, cx + 240, hip + 200); }, "rgba(200,225,240,0.8)");
      const body = cc => { cc.moveTo(cx - 150, top + 20); cc.quadraticCurveTo(cx, top - 30, cx + 150, top + 20); cc.quadraticCurveTo(cx + 205, top + 210, cx + 175, hip); cc.lineTo(cx - 175, hip); cc.quadraticCurveTo(cx - 205, top + 210, cx - 150, top + 20); };
      fillPath(c, body, k.top); paint(c, body, k.top, "rgba(120,20,25,0.75)", "rgba(255,190,160,0.6)", [cx - 210, top - 30, 420, hip - top + 30]);
      // collar
      for (const sx of [-1, 1]) fillPath(c, cc => { cc.moveTo(cx, top + 8); cc.lineTo(cx + sx * 95, top - 2); cc.lineTo(cx + sx * 70, top + 78); cc.closePath(); }, "#fff6e6", 6);
      // apron: bib + waist, stitched, pocket, ties
      const apron = cc => { cc.moveTo(cx - 95, top + 95); cc.lineTo(cx + 95, top + 95); cc.lineTo(cx + 110, hip - 70); cc.quadraticCurveTo(cx + 165, hip - 50, cx + 170, hip + 180); cc.quadraticCurveTo(cx, hip + 200, cx - 170, hip + 180); cc.quadraticCurveTo(cx - 165, hip - 50, cx - 110, hip - 70); };
      fillPath(c, apron, k.apron); paint(c, apron, k.apron, "rgba(150,115,70,0.6)", "rgba(255,255,250,0.7)", [cx - 175, top + 95, 350, hip + 105 - top]);
      stitch(c, cc => { cc.moveTo(cx - 80, top + 112); cc.lineTo(cx + 80, top + 112); cc.lineTo(cx + 94, hip - 76); cc.moveTo(cx - 80, top + 112); cc.lineTo(cx - 94, hip - 76); }, "rgba(170,120,80,0.8)");
      stitch(c, cc => { cc.moveTo(cx - 150, hip + 160); cc.quadraticCurveTo(cx, hip + 178, cx + 150, hip + 160); }, "rgba(170,120,80,0.8)");
      fillPath(c, cc => { cc.moveTo(cx - 75, hip + 20); cc.lineTo(cx + 75, hip + 20); cc.lineTo(cx + 68, hip + 120); cc.quadraticCurveTo(cx, hip + 132, cx - 68, hip + 120); }, "#f9f1de", 5);
      stitch(c, cc => { cc.moveTo(cx - 62, hip + 34); cc.lineTo(cx + 62, hip + 34); }, "rgba(170,120,80,0.8)", 3, [8, 7]);
      c.fillStyle = "#e0604f"; for (const [hx, hy] of [[-30, 75], [10, 62], [38, 90]]) { c.beginPath(); c.arc(cx + hx, hip + hy, 9, 0, 7); c.fill(); }    // little hearts-ish dots on the pocket
      fillPath(c, cc => cc.rect(cx - 160, hip - 70, 320, 34), "#efe2c4", 6);
      stitch(c, cc => { cc.moveTo(cx - 150, hip - 53); cc.lineTo(cx + 150, hip - 53); }, "rgba(170,120,80,0.8)", 3, [8, 7]);
      fillPath(c, cc => { cc.moveTo(cx + 150, hip - 60); cc.quadraticCurveTo(cx + 215, hip - 20, cx + 200, hip + 70); cc.lineTo(cx + 180, hip + 68); cc.quadraticCurveTo(cx + 190, hip - 10, cx + 145, hip - 44); }, "#efe2c4", 5);
      return { W, H, pivot: [cx, hip], neck: [cx, top + 10], shL: [cx - 150, top + 50], shR: [cx + 150, top + 50], hipL: [cx - 60, hip + 150], hipR: [cx + 60, hip + 150] };
    }
    const W = 520, H = 720, cx = 260, top = 120, hip = 520;
    c.clearRect(0, 0, W, H);
    // shorts
    const sh = cc => { cc.moveTo(cx - 140, hip - 40); cc.lineTo(cx + 140, hip - 40); cc.lineTo(cx + 150, hip + 120); cc.lineTo(cx + 20, hip + 128); cc.lineTo(cx, hip + 60); cc.lineTo(cx - 20, hip + 128); cc.lineTo(cx - 150, hip + 120); };
    fillPath(c, sh, k.shorts); paint(c, sh, k.shorts, "rgba(10,20,50,0.7)", "rgba(150,190,255,0.5)", [cx - 160, hip - 40, 320, 170]);
    stitch(c, cc => { cc.moveTo(cx - 138, hip + 100); cc.lineTo(cx - 30, hip + 106); cc.moveTo(cx + 30, hip + 106); cc.lineTo(cx + 138, hip + 100); cc.moveTo(cx, hip - 30); cc.lineTo(cx, hip + 55); }, "rgba(240,200,120,0.85)", 3, [8, 7]);
    // hoodie body
    const body = cc => { cc.moveTo(cx - 130, top + 20); cc.quadraticCurveTo(cx, top - 26, cx + 130, top + 20); cc.quadraticCurveTo(cx + 185, top + 200, cx + 150, hip + 10); cc.quadraticCurveTo(cx, hip + 30, cx - 150, hip + 10); cc.quadraticCurveTo(cx - 185, top + 200, cx - 130, top + 20); };
    fillPath(c, body, k.top); paint(c, body, k.top, "rgba(10,60,30,0.75)", "rgba(190,255,200,0.55)", [cx - 190, top - 26, 380, hip - top + 60]);
    stitch(c, cc => { cc.moveTo(cx - 140, hip - 14); cc.quadraticCurveTo(cx, hip + 6, cx + 140, hip - 14); }, "rgba(200,255,210,0.7)");
    // hood around the neck + strings
    fillPath(c, cc => { cc.moveTo(cx - 120, top + 22); cc.quadraticCurveTo(cx, top + 120, cx + 120, top + 22); cc.quadraticCurveTo(cx, top + 60, cx - 120, top + 22); }, k.topD, 6);
    for (const sx of [-1, 1]) { c.lineWidth = 7; c.strokeStyle = "#f6f1e4"; c.lineCap = "round"; c.beginPath(); c.moveTo(cx + sx * 30, top + 70); c.quadraticCurveTo(cx + sx * 40, top + 150, cx + sx * 32, top + 200); c.stroke(); fillPath(c, cc => cc.arc(cx + sx * 32, top + 206, 9, 0, 7), "#d8d0bc", 4); }
    // kangaroo pocket
    const pk = cc => { cc.moveTo(cx - 100, hip - 150); cc.lineTo(cx + 100, hip - 150); cc.lineTo(cx + 130, hip - 30); cc.lineTo(cx - 130, hip - 30); };
    fillPath(c, pk, "rgba(40,120,70,1)", 6); stitch(c, cc => { cc.moveTo(cx - 92, hip - 138); cc.lineTo(cx + 92, hip - 138); }, "rgba(200,255,210,0.7)", 3, [8, 7]);
    // little Cubey-yellow badge
    fillPath(c, cc => cc.arc(cx + 70, top + 110, 22, 0, 7), "#ffd23a", 5); c.fillStyle = OUT; c.beginPath(); c.arc(cx + 63, top + 106, 3.5, 0, 7); c.arc(cx + 77, top + 106, 3.5, 0, 7); c.fill();
    return { W, H, pivot: [cx, hip], neck: [cx, top + 6], shL: [cx - 128, top + 44], shR: [cx + 128, top + 44], hipL: [cx - 70, hip + 105], hipR: [cx + 70, hip + 105] };
  },
  upper(c, who) {    // upper arm (sleeve), pivot at the shoulder (top), elbow at bottom
    const k = CAST[who], L = who === "mom" ? 250 : 210, W = 150, H = L + 90, cx = 75, y0 = 45;
    c.clearRect(0, 0, W, H);
    const s = cc => { cc.moveTo(cx - 46, y0); cc.quadraticCurveTo(cx, y0 - 40, cx + 46, y0); cc.lineTo(cx + 34, y0 + L); cc.quadraticCurveTo(cx, y0 + L + 18, cx - 34, y0 + L); };
    fillPath(c, s, k.top); paint(c, s, k.top, who === "mom" ? "rgba(120,20,25,0.7)" : "rgba(10,60,30,0.7)", "rgba(255,255,230,0.45)", [cx - 50, y0 - 40, 100, L + 60]);
    stitch(c, cc => { cc.moveTo(cx - 32, y0 + L - 18); cc.quadraticCurveTo(cx, y0 + L - 6, cx + 32, y0 + L - 18); }, "rgba(255,230,210,0.75)", 3, [8, 7]);
    return { W, H, pivot: [cx, y0], end: [cx, y0 + L] };
  },
  fore(c, who) {     // forearm skin + mitten hand, pivot at the elbow
    const L = who === "mom" ? 220 : 180, W = 170, H = L + 150, cx = 85, y0 = 30;
    c.clearRect(0, 0, W, H);
    const a = cc => { cc.moveTo(cx - 22, y0); cc.lineTo(cx + 22, y0); cc.lineTo(cx + 19, y0 + L); cc.lineTo(cx - 19, y0 + L); };
    fillPath(c, a, SKIN, 6); paint(c, a, SKIN, "rgba(180,120,70,0.55)", "rgba(255,255,240,0.6)", [cx - 25, y0, 50, L]);
    // mitten hand: palm + thumb + finger creases
    const hy = y0 + L + 42;
    const palm = cc => { cc.ellipse(cx, hy, 48, 56, 0, 0, Math.PI * 2); };
    fillPath(c, cc => cc.ellipse(cx - 44, hy - 18, 18, 30, -0.6, 0, Math.PI * 2), SKIN, 6);
    fillPath(c, palm, SKIN, 7); paint(c, palm, SKIN, "rgba(180,120,70,0.55)", "rgba(255,255,240,0.7)", [cx - 50, hy - 58, 100, 116]);
    c.strokeStyle = "rgba(120,70,50,0.6)"; c.lineWidth = 4; for (const dx of [-14, 8]) { c.beginPath(); c.moveTo(cx + dx, hy + 24); c.lineTo(cx + dx + 3, hy + 52); c.stroke(); }
    return { W, H, pivot: [cx, y0], hand: [cx, hy] };
  },
  leg(c, who) {      // thin leg + shoe, pivot at the hip (top)
    const k = CAST[who], L = who === "mom" ? 520 : 420, W = 220, H = L + 140, cx = 90, y0 = 20;
    c.clearRect(0, 0, W, H);
    const lg = cc => { cc.moveTo(cx - 20, y0); cc.lineTo(cx + 20, y0); cc.lineTo(cx + 17, y0 + L); cc.lineTo(cx - 17, y0 + L); };
    if (who === "son") { fillPath(c, lg, SKIN, 6); paint(c, lg, SKIN, "rgba(180,120,70,0.5)", "rgba(255,255,240,0.5)", [cx - 22, y0, 44, L]);
      fillPath(c, cc => cc.rect(cx - 21, y0 + L - 70, 42, 62), "#ffffff", 5); c.strokeStyle = k.shoeTrim; c.lineWidth = 6; c.beginPath(); c.moveTo(cx - 19, y0 + L - 50); c.lineTo(cx + 19, y0 + L - 50); c.stroke(); }
    else { fillPath(c, lg, SKIN, 6); paint(c, lg, SKIN, "rgba(180,120,70,0.5)", "rgba(255,255,240,0.5)", [cx - 22, y0, 44, L]); }
    const fy = y0 + L + 32;
    const shoe = cc => { cc.moveTo(cx - 30, fy - 46); cc.quadraticCurveTo(cx + 10, fy - 56, cx + 30, fy - 40); cc.quadraticCurveTo(cx + 100, fy - 30, cx + 104, fy + 4); cc.lineTo(cx + 104, fy + 22); cc.lineTo(cx - 40, fy + 22); cc.quadraticCurveTo(cx - 48, fy - 10, cx - 30, fy - 46); };
    fillPath(c, shoe, k.shoe); paint(c, shoe, k.shoe, "rgba(40,10,10,0.55)", "rgba(255,255,255,0.65)", [cx - 48, fy - 56, 152, 78]);
    if (who === "son") { fillPath(c, cc => cc.rect(cx - 40, fy + 6, 144, 16), k.shoeTrim, 5); stitch(c, cc => { cc.moveTo(cx - 6, fy - 40); cc.lineTo(cx + 30, fy - 30); }, "#d8432f", 4, [6, 6]); }
    else stitch(c, cc => { cc.moveTo(cx - 34, fy + 2); cc.lineTo(cx + 96, fy + 2); }, "rgba(255,210,200,0.8)", 3, [8, 7]);
    return { W, H, pivot: [cx, y0], foot: [cx, fy + 22] };
  },
};
