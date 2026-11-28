# Ep2 keys. exec'd inside build_ep2.py. Times in seconds (dialogue timeline), character-local units: x right, z up, feet at 0.
import math, random
SC = 1.3
Lt = [l["t0"] for l in LINES]; Le = [l["t1"] for l in LINES]
def wt(who, needle, which=0, end=False):
    w_ = word_t(who, needle, which); return w_[1] if end else w_[0]
def sstep(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

# ------------------------------------------------------------ where everyone is (speed profiles, integrated per frame)
T_GO = -1.0                         # already running when the short starts (hook first)
T_STOP = Lt[7] - 0.05               # Jess stops dead on "Oh my god."
T_RE = Lt[9] + 0.35                 # bin, then running again on "If I'm not flat by Friday"
T_SPRINT = Lt[10] + 0.15            # Nora: "Deal." and she's gone
VR = 2.0
def vprof(pts, t):
    if t <= pts[0][0]: return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1: return v0 + (v1 - v0) * sstep((t - t0) / (t1 - t0)) if t1 > t0 else v1
    return pts[-1][1]
VJ = [(0, VR), (T_STOP - 0.3, VR), (T_STOP + 0.05, 0), (T_RE, 0), (T_RE + 0.8, VR), (99, VR)]
VN = [(0, VR), (T_STOP, VR), (T_STOP + 0.75, 0), (T_RE, 0), (T_RE + 0.8, VR), (T_SPRINT, VR), (T_SPRINT + 0.7, 4.0), (99, 4.0)]
def integ(V, y0):
    ys = [y0]
    for f in range(2, NFR + 2): t = (f - 1.5) / FPS; ys.append(ys[-1] - vprof(V, t) / FPS)
    return ys
YJ = integ(VJ, 0.0); YN = integ(VN, 0.0)
# Nora jogs back level with Jess after overshooting
fs, fe = F(T_STOP + 0.8), F(T_STOP + 1.9)
over = YJ[F(T_STOP + 0.8) - 1] - YN[fs - 1]
for f in range(fs, NFR + 1):
    YN[f - 1] += over * sstep((f - fs) / (fe - fs))
XN = [0.55 + (0.5 * sstep(((f - 1) / FPS - T_SPRINT) / 1.0)) for f in range(1, NFR + 1)]
for f in range(1, NFR + 1):
    key(nora["arm"], "location", Vector((XN[f - 1], YN[f - 1], 0)), f); key(jess["arm"], "location", Vector((-0.55, YJ[f - 1], 0)), f)
JSTOP_Y = YJ[F(T_STOP + 0.3) - 1]

# ------------------------------------------------------------ run cycle + gestures
def amp(V, t, inplace=None):
    a = min(1.0, vprof(V, t) / VR)
    if inplace and inplace[0] <= t <= inplace[1]: a = max(a, 0.6)
    return a
CAMP = {}
# ------------------------------------------------------------ camera: leads the runners, then Nora's POV with the phone, then back
# one continuous camera, new framing every 2.5-3.5 s (Ricks Clips), blended 0.35 s between beats
T0, T1 = wt("nora", "snap") - 0.45, Le[5] + 0.15
def P(f): return Vector((XN[f - 1], YN[f - 1])), Vector((-0.55, YJ[f - 1]))
def V3(x, y, z): return Vector((x, y, z))
def beat_fns():
    def two(f, u, d=3.8, h=1.7):
        n, j = P(f); m = (n + j) / 2; return V3(0.0, m.y - d + 0.25 * u, h), V3(0.0, m.y, 1.45)
    def hook(f, u):     # low angle pushing in on Nora pointing at the cup
        n, j = P(f); m = (n + j) / 2; return V3(0.45, m.y - 3.0 + 0.7 * u, 1.0), V3(0.15, m.y, 1.62)
    def jess_close(f, u):
        n, j = P(f); return V3(-1.45, j.y - 2.1 + 0.2 * u, 1.8), V3(-0.5, j.y, 1.78)
    def nora_close(f, u):
        n, j = P(f); return V3(1.3, n.y - 2.0 + 0.2 * u, 1.85), V3(0.55, n.y, 1.85)
    def cup(f, u):
        n, j = P(f); c = V3(-0.55 + 0.38 * SC, j.y, 1.18 * SC); return c + V3(0.3, -1.75 + 0.3 * u, 0.1), c
    def high(f, u):
        n, j = P(f); m = (n + j) / 2; return V3(0.3 * (1 - u), m.y - 3.1, 3.7 - 0.4 * u), V3(0.0, m.y + 0.4, 1.1)
    def front(f, u):
        n, j = P(f); m = (n + j) / 2; return V3(0.25 - 0.5 * u, m.y - 2.6, 1.6), V3(0.0, m.y, 1.7)
    def punch_jess(f, u):
        n, j = P(f); return V3(-0.85, j.y - 1.65 + 0.15 * u, 1.65), V3(-0.55, j.y, 1.55)
    def crash(f, u):
        n, j = P(f); return V3(-0.55, j.y - 1.05, 1.92), V3(-0.55, j.y, 1.92)
    def wide(f, u):
        n, j = P(f); return V3(0.35, j.y - 4.6 - 0.4 * u, 2.2), V3(0.0, j.y, 1.3)
    def toss(f, u):
        n, j = P(f); return V3(-0.6, j.y - 3.2, 1.7), V3(-1.2, j.y - 0.2, 1.05)
    def sprint(f, u):
        n, j = P(f); return V3(0.45, j.y - 4.3, 1.6), V3(0.35, j.y, 1.55)
    return [(0.0, hook, 0.3), (Lt[1], jess_close, 0.35), (Lt[2], nora_close, 0.3), (Lt[3], cup, 0.35), (Lt[4], two, 0.35),
            (T1, high, 0.4), (Lt[6] + 3.0, front, 0.45), (wt("nora", "balloon") - 0.3, punch_jess, 0.3), (Lt[7], crash, 0.15),
            (Lt[8], wide, 0.4), (T_RE - 0.6, toss, 0.35), (Lt[10] - 0.15, sprint, 0.4)]
BEATS = beat_fns()
def pov(f):
    t = (f - 1) / FPS; A = amp(VN, t); bob = 0.03 * A * math.sin(2 * math.pi * 2.6 * t)
    eye = Vector((XN[f - 1] - 0.08, YN[f - 1] - 0.05, 1.9 + bob)); cupp = Vector((-0.55 + 0.42 * SC, YJ[f - 1] - 0.15, 1.0 * SC + bob))
    return eye, eye + (cupp - eye).normalized() * 0.30
def beat_at(f, i):
    t0, fn, bl = BEATS[i]; t1 = BEATS[i + 1][0] if i + 1 < len(BEATS) else (NFR - 1) / FPS
    u = max(0.0, min(1.0, ((f - 1) / FPS - t0) / max(0.1, t1 - t0))); return fn(f, u)
for f in range(1, NFR + 1):
    t = (f - 1) / FPS
    if T0 <= t <= T1: cp, tp = pov(f)
    else:
        i = max(k for k, b_ in enumerate(BEATS) if b_[0] <= t or k == 0); cp, tp = beat_at(f, i)
        bl = BEATS[i][2]; w_ = sstep((t - BEATS[i][0]) / bl) if i > 0 else 1.0
        if w_ < 1:
            pc, pt = (pov(F(T1)) if BEATS[i][0] == T1 else beat_at(f, i - 1)); cp = pc.lerp(cp, w_); tp = pt.lerp(tp, w_)
        if T0 - 0.4 <= t < T0:      # whip into her eyes from the side (she is already hidden)
            u = sstep((t - (T0 - 0.4)) / 0.4); ec, et = pov(F(T0)); cp = cp.lerp(ec, u); tp = tp.lerp(et, u)
        A = max(amp(VN, t), amp(VJ, t)); bob = 0.015 * A * math.sin(2 * math.pi * 2.6 * t); cp = cp + Vector((0, 0, bob))
    key(cam, "location", cp, f); key(tgt, "location", tp, f); CAMP[f] = cp


def fwd_fn(xs, ys):
    def fwd(f):
        c = CAMP.get(f) or CAMP[min(CAMP, key=lambda k: abs(k - f))]; tx, ty = c.x - xs(f), c.y - ys(f); l = math.hypot(tx, ty) or 1; tx, ty = tx / l, ty / l
        hx, hy = 0.0, -1.0
        return (hx * (-ty) + hy * tx, hx * tx + hy * ty)
    return fwd
def build_anim(r, V, gest, kinds, inplace=None, hold=None, seed=1, fwd=None):
    a_ = rig2.Anim(r, fwd); z = r["z"]; Sk = r["S"]; ph = seed * 1.3
    for f in range(1, NFR + 1):
        t = (f - 1) / FPS; A = amp(V, t, inplace); ph += 2 * math.pi * (2.0 + 0.8 * A) / FPS * (1 if A > 0.02 else 0)
        sL, sR = math.sin(ph), math.sin(ph + math.pi)
        for sd_, s__, sw_ in (("L", -1, sL), ("R", 1, sR)):     # feet in body space: forward/back + lift, the rig turns that into what this camera sees
            a_.key(f"foot3.{sd_}", f, s__ * Sk["hipW"] * 0.95, 0.17 * A * sw_, z["ank"] + 0.1 * A * max(0.0, sw_))
        a_.key("hips", f, 0.035 * A * abs(math.cos(ph))); a_.key("spine", f, 3.5 * A * math.sin(ph)); a_.key("head", f, -2.5 * A * math.sin(ph))
        for sd, s_, sw in (("L", -1, sR), ("R", 1, sL)):        # each arm swings with the opposite leg
            k_ = 0.35 if (hold and hold[0] == sd and t < hold[1]) else 1.0
            base = (s_ * 0.24, 0.74 + 0.03 * A * sw, -90 + s_ * 10)
            if A < 0.02: base = (s_ * 0.22, 0.6, -90)
            x, zz, fg = base; wmax = 0.0
            for (g0, g1, gs, gx, gz, gf) in gest:
                if gs != sd: continue
                w_ = (1.0 if g0 <= 0 else sstep((t - g0) / 0.25)) * (1 - sstep((t - g1) / 0.3))
                if w_ > 0:
                    wmax = max(wmax, w_)
                    x, zz = x + (gx - x) * w_, zz + (gz - zz) * w_
                    vx = math.cos(R(fg)) * (1 - w_) + math.cos(R(gf)) * w_; vz = math.sin(R(fg)) * (1 - w_) + math.sin(R(gf)) * w_
                    fg = math.degrees(math.atan2(vz, vx))
            a_.key(f"hand.{sd}", f, x, zz); a_.key(f"fingers.{sd}", f, fg)
            run = (1 - wmax) * min(1.0, 3 * A) * (k_ if k_ < 1 else 1.0)
            a_.key(f"hand3.{sd}", f, s_ * 0.2, 0.2 * sw, 0.86 + 0.06 * sw); a_.key(f"w3.{sd}", f, run)   # arm pumps forward/back in the body's own space
    a_.bake(1, NFR, bend={"arm.L": -1, "arm.R": 1})
    for sd, ks in kinds.items():
        for t, k in ks: rig2.set_hand(r, sd, k, max(1, F(t)))
    return a_

# ---- Nora: stretching by the bench, roasting, phone, jog in place, sprint
GN = [
    (0.0, Le[0] + 0.1, "L", -0.62, 0.98, 180),                                           # "a whole smoothie to a run?" points at the cup
    (Lt[2], Le[2] + 0.1, "L", -0.5, 1.02, 165),                                           # "You look like one too."
    (Lt[4], Lt[4] + 0.8, "R", 0.45, 1.15, 60),                                            # "Fruit, my ass" brush-off
    (Lt[4] + 0.85, Le[5] + 0.45, "R", 0.33, 1.12, 90),                                     # phone up
    (Le[5] + 0.15, wt("nora", "rest.") + 0.3, "R", 0.42, 1.05, 60),                       # explaining (takes over straight from the phone)
    (wt("nora", "balloon") - 0.35, Le[6] + 0.2, "L", -0.62, 0.76, 190),                   # "That's your [bleep] balloon" points at her belly
    (T_STOP + 0.9, T_RE, "L", -0.25, 0.66, -100), (T_STOP + 0.9, T_RE, "R", 0.25, 0.66, -80),
    (Lt[10], Lt[10] + 0.6, "L", -0.35, 1.25, 120),                                        # "Deal." flick
]
KN = {"L": [(0, "point"), (Le[0] + 0.25, "fist"), (Lt[2], "open"), (Le[2] + 0.2, "fist"),
            (wt("nora", "balloon") - 0.35, "point"), (Le[6] + 0.4, "fist"), (Lt[10], "wave"), (Lt[10] + 0.7, "fist")],
      "R": [(0, "fist"), (Lt[4], "wave"), (Lt[4] + 0.85, "palm"), (Le[5] + 0.5, "open"), (wt("nora", "rest.") + 0.5, "fist")]}
na = build_anim(nora, VN, GN, KN, inplace=(T_STOP + 1.9, T_RE), seed=1, fwd=fwd_fn(lambda f: XN[f - 1], lambda f: YN[f - 1]))

# ---- Jess: runs in with the smoothie, sips, defends it, stops dead, dumps it
CUP_UP = 0                     # right hand: fingers pointing +x keeps the cup upright
GJ = [
    (0.0, Le[0] + 0.1, "R", 0.25, 1.27, 30),                                             # sipping while she gets called out
    (Lt[1], Le[1] + 0.2, "L", -0.08, 0.8, -60),                                          # hand on belly: "I feel like a balloon"
    (Lt[3], Le[3] + 0.2, "R", 0.38, 1.18, CUP_UP),                                       # "Mango. It's fruit." holds it up
    (Le[3] + 0.2, Lt[6], "R", 0.42, 1.0, CUP_UP),                                        # cup out where Nora can snap it
    (T_STOP, Lt[8], "L", -0.06, 0.78, -40), (T_STOP, Lt[8], "R", 0.3, 0.78, CUP_UP),     # stops dead, hand on belly
    (Lt[8], Le[8], "R", 0.3, 1.18, CUP_UP), (Lt[8], Le[8], "L", -0.06, 0.78, -40),       # stares at the cup: "with a straw"
    (Le[8], T_RE - 0.15, "R", 0.32, 0.85, CUP_UP),
    (T_RE - 0.75, T_RE + 0.05, "R", 0.32, 1.3, 60),                                     # swings it across into the bin
]
KJ = {"L": [(0, "fist"), (Lt[1], "open"), (Le[1] + 0.4, "fist"), (T_STOP, "open"), (Le[8] + 0.2, "fist")],
      "R": [(0, "grip"), (T_RE + 0.05, "open"), (T_RE + 0.6, "fist")]}
ja = build_anim(jess, VJ, GJ, KJ, hold=("R", T_RE), seed=2, fwd=fwd_fn(lambda f: -0.55, lambda f: YJ[f - 1]))

# ------------------------------------------------------------ props in hands
cup = smoothie_cup("smoothie_cup")
holders(cup, [(jess, "R", 90, 0, T_RE)])
ph_n, scr_n = phone("phone_nora")
holders(ph_n, [(nora, "R", 0, Lt[4] + 0.85, Le[5] + 0.6)]); pop(ph_n, Lt[4] + 0.85, Le[5] + 0.45)
# the toss: from the hand on the release frame, an arc into the bin
BIN_X, BIN_Y = -2.05, JSTOP_Y - 0.35
for o in [o for o in bpy.data.objects if o.name.startswith("bush")] + [o for o in bpy.data.objects if o.parent and o.parent.name.startswith("bush")]:
    root = o if o.parent is None else o.parent
    if abs(root.location.y - BIN_Y) < 1.3 and root.location.x < 0: root.location.y += 2.6
bin_("bin", BIN_X, BIN_Y)
fr = F(T_RE); S.frame_set(fr); bpy.context.view_layer.update(); p0 = cup.matrix_world.translation.copy()
key(cup, "location", Vector((0, 0, 0)), 1); key(cup, "location", Vector((0, 0, 0)), fr)
top = Vector((BIN_X, BIN_Y, 1.25)); inside = Vector((BIN_X, BIN_Y, 0.82))
for i in range(1, 15):
    u = i / 14; p = p0.lerp(top, u); p.z += 0.45 * math.sin(math.pi * u); key(cup, "location", p, fr + i)
key(cup, "location", inside, fr + 18); key(cup, "rotation_euler", Euler((0, 0, 0)), fr); key(cup, "rotation_euler", Euler((R(80), R(30), 0)), fr + 14); key(cup, "rotation_euler", Euler((R(100), R(40), 0)), fr + 18)
for fc in rig2.all_fcurves(cup.animation_data.action):
    if fc.data_path == "location":
        for kp in fc.keyframe_points:
            if int(kp.co[0]) == fr: kp.interpolation = "CONSTANT"

# the 'focus' empty doubles as the look target; in POV it sits on the phone (0.30 m), so the cup and Jess go soft

# hide Nora while we are inside her head; show the POV hand + phone
def tree_(o):
    yield o
    for c in o.children: yield from tree_(c)
def vis(o, frames):
    for f, h in frames: o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
nobjs = set(tree_(nora["arm"])) | set(tree_(ph_n)) | {o for o in bpy.data.objects if o.name.startswith("nora_")}
for o in nobjs: vis(o, [(1, False), (F(T0 - 0.4), True), (F(T1), False)])
root = bpy.data.objects.new("pov_root", None); S.collection.objects.link(root); root.parent = cam
root.location = (0.0, -0.05, -0.30); root.rotation_euler = (R(-90 + 7), R(-5), R(2))
pv, scr_pov = phone("phone_pov"); pv.parent = root
ART = os.path.join(ARTD, "nora"); HJ = json.load(open(os.path.join(ART, "pov_hand.json")))
def cardxz(name, img, x0, x1, z0, z1, y, uv=((0, 0), (1, 0), (1, 1), (0, 1)), rot=0.0, piv=(0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)], [], [(0, 1, 2, 3)]); me.update()
    u = me.uv_layers.new(); [setattr(u.data[i], "uv", c) for i, c in enumerate(uv)]
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.parent = root; o.location = (piv[0], y, piv[1]); o.rotation_euler = (0, R(rot), 0)
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(ART, img)); tx.extension = "CLIP"; tx.interpolation = "Cubic"
    b.inputs["Base Color"].default_value = (0, 0, 0, 1); nt.links.new(tx.outputs["Alpha"], b.inputs["Alpha"]); b.inputs["Specular IOR Level"].default_value = 0.0
    nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 1.0
    o.data.materials.append(m); o.visible_shadow = False; return o
D = pv["depth"]
cardxz("pov_hand_back", "pov_back.png", HJ["x0"], HJ["x1"], HJ["z0"], HJ["z1"], D / 2 + 0.0035)
cardxz("pov_hand_front", "pov_front.png", HJ["x0"], HJ["x1"], HJ["z0"], HJ["z1"], -D / 2 - 0.0009)
wx, wz = HJ["wrist"]
cardxz("pov_arm", "arm.png", -0.045, 0.045, -0.40, 0.0, D / 2 + 0.006, uv=((0, 0.62), (1, 0.62), (1, 0.0), (0, 0.0)), rot=-28, piv=(wx + 0.002, wz + 0.024))
for o in set(tree_(root)): vis(o, [(1, True), (F(T0), False), (F(T1), True)])
SCREENS = [ph_n, pv]
TIMES = {"T_GO": T_GO, "T_STOP": T_STOP, "T_RE": T_RE, "T_SPRINT": T_SPRINT, "POV": [T0, T1], "snap": wt("nora", "snap", end=True), "bin": [BIN_X, BIN_Y]}
json.dump(TIMES, open(OUT.replace(".blend", "_times.json"), "w"))
