// Shot 1 (5 s): son sips soda by the fridge, Mom walks in, sees it, loses it.
// Rig angles in degrees. Arms: 0 = hanging, 90 = straight out sideways, 180 = straight up; elbow keeps turning the same way.
const lerp = (a, b, u) => a + (b - a) * u, cl = u => Math.max(0, Math.min(1, u));
const ease = u => { u = cl(u); return u * u * (3 - 2 * u); };
const back = u => { u = cl(u); const s = 1.7; return 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2); };
const blinkAt = (t, ts) => ts.some(b => t > b && t < b + 0.11) ? 1 : 0;
export const SHOT = { frames: 150, fps: 30 };
export function son(t) {
  const breathe = Math.sin(t * 2.4) * 1.2;
  if (t < 1.55) { const up = ease(t / 0.45), gulp = Math.sin(t * 9) * 2 * up;
    return { head: { mouth: "sip", brows: "up", blink: 1, eyes: [0, 0] }, tilt: -6 * up + gulp, lean: -3 * up + breathe * 0.4, bounce: 0,
             armL: [8 + breathe, 10], armR: [lerp(10, 128, up), lerp(10, 104, up)], legL: [3], legR: [-3] }; }
  const u = back((t - 1.55) / 0.32), hop = t < 1.9 ? Math.sin(cl((t - 1.55) / 0.35) * Math.PI) * 0.06 : 0;
  return { head: { mouth: t < 2.25 ? "shock" : "frown", brows: t < 2.25 ? "up" : "sad", blink: blinkAt(t, [3.6]), eyes: [1, -0.2], sweat: t > 2.35 },
           tilt: lerp(-6, 7, u) + Math.sin(t * 3) * 1.5, lean: lerp(-3, -6, u) + breathe * 0.4, bounce: hop,
           armL: [lerp(8, 22, u), lerp(10, 30, u)], armR: [lerp(128, 62, u), lerp(104, 70, u)], legL: [3], legR: [-3] };
}
export const MOM_X0 = -3.9, MOM_X1 = -5.75;
export function mom(t) {
  if (t < 1.35) { const w = t * 9.5, s = Math.sin(w), x = lerp(MOM_X0, MOM_X1, ease(t / 1.35) * 0.35 + (t / 1.35) * 0.65);
    return { head: { mouth: "flat", brows: "flat", blink: blinkAt(t, [0.55]), eyes: [-0.7, 0] }, x, tilt: s * 2, lean: 3, bounce: Math.abs(s) * 0.035,
             armL: [12 + 14 * s, 8], armR: [12 - 14 * s, 8], legL: [16 * s], legR: [-16 * s] }; }
  if (t < 1.95) { const u = back((t - 1.35) / 0.3);
    return { head: { mouth: "shock", brows: "up", blink: 0, eyes: [-1, 0] }, x: MOM_X1, tilt: 0, lean: lerp(3, -7, u), bounce: 0.07 * Math.sin(cl((t - 1.35) / 0.3) * Math.PI),
             armL: [lerp(12, 40, u), lerp(8, 95, u)], armR: [lerp(12, 40, u), lerp(8, 95, u)], legL: [4], legR: [-4] }; }
  const u = back((t - 1.95) / 0.26), ph = (t - 1.95) * 7.5, s = Math.sin(ph);
  return { head: { mouth: "rant", talk: 0.3 + 0.7 * Math.abs(Math.sin((t - 1.95) * 12.5)), brows: "angry", blink: 0, eyes: [-1, 0.1] }, x: MOM_X1,
           tilt: 6 * s, lean: lerp(-7, 5, u) + 3 * Math.sin(ph * 0.5), bounce: Math.abs(s) * 0.05,
           armL: [lerp(40, 150, u) + 10 * s, lerp(95, 25, u)], armR: [lerp(40, 158, u) - 10 * Math.sin(ph + 1.2), lerp(95, 20, u)],
           legL: [8 * Math.max(0, Math.sin(ph * 0.5))], legR: [-4] };
}
