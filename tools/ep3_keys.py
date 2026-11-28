# Ep3 keys. exec'd inside build_ep3.py. Times in seconds (dialogue timeline). Character-local units: x right, z up, feet at 0.
# Hand targets: "2d" = (x, z) in the character's card plane; "3d" = (side, forward, up) in body space (forward = toward camera here).
import math, random
Lt = [l["t0"] for l in LINES]; Le = [l["t1"] for l in LINES]
def wt(who, needle, which=0, end=False):
    w_ = word_t(who, needle, which); return w_[1] if end else w_[0]
def sstep(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def V3(x, y, z): return Vector((x, y, z))
CAMP = {}

# ------------------------------------------------------------ camera beats (new framing every ~2.5-3.5 s, each lands on a line), then Marcus's POV for the scan
T0, T1 = Lt[5] - 0.35, Le[5] + 0.12
RAYH, DALEH, MARH = V3(-0.6, TY + 0.62, 1.62), V3(0.6, TY + 0.62, 1.62), V3(1.58, TY + 0.05, 2.25)
PLATE_R = V3((PIE0[0] + CK[0]) / 2, (PIE0[1] + CK[1]) / 2, TOP + 0.06)
def beat_fns():
    def hook(f, u):        # Ray stuffing pie with a Coke, Marcus looming in at the right; slow push
        return V3(0.05 + 0.1 * u, TY - 1.75 + 0.3 * u, 1.62), V3(-0.15, TY + 0.4, 1.4)
    def ray_close(f, u):   # crash in on Ray
        return V3(-0.75, TY - 0.75 + 0.1 * u, 1.62), V3(-0.6, TY + 0.6, 1.58)
    def marcus_low(f, u):  # low hero angle on Marcus
        return V3(1.05 - 0.15 * u, TY - 1.35, 1.0), V3(1.58, TY + 0.05, 2.1)
    def dale_close(f, u):
        return V3(0.85, TY - 0.8 + 0.12 * u, 1.6), V3(0.6, TY + 0.6, 1.58)
    def uncles_wide(f, u):
        return V3(0.0, TY - 2.1 + 0.25 * u, 1.65), V3(0.0, TY + 0.5, 1.35)
    def food_high(f, u):   # high angle over Ray's pie and Coke
        return V3(-0.95, TY - 0.75, 2.2 - 0.12 * u), V3(-0.5, TY + 0.25, 1.1)
    def ray_sus(f, u):
        return V3(-0.35, TY - 0.85 + 0.08 * u, 1.55), V3(-0.6, TY + 0.6, 1.6)
    def marcus_close(f, u):
        return V3(1.05, TY - 1.45 + 0.15 * u, 2.1), V3(1.58, TY + 0.05, 2.05)
    def crash(f, u):       # "SEVENTY-ONE?" crash zoom on Ray
        k = sstep(u * 4); return V3(-0.6, TY - 1.3 + 0.55 * k, 1.6), V3(-0.6, TY + 0.6, 1.62)
    def three(f, u):       # everyone, Marcus showing the phone
        return V3(0.45, TY - 2.75 + 0.45 * u, 1.85), V3(0.45, TY + 0.4, 1.6)
    def ray_end(f, u):     # Ray gives in, phone out
        return V3(-0.2, TY - 1.2 + 0.35 * u, 1.65), V3(-0.5, TY + 0.55, 1.55)
    def ray_phone(f, u):
        return V3(-0.85, TY - 0.7 + 0.08 * u, 1.7), V3(-0.55, TY + 0.55, 1.6)
    return [(0.0, hook, 0.3), (Lt[1], ray_close, 0.15), (Lt[2], marcus_low, 0.3), (Lt[3], dale_close, 0.3), (Lt[4], uncles_wide, 0.25),
            (Lt[4] + 1.9, food_high, 0.4), (T1, ray_sus, 0.35), (Lt[7], marcus_close, 0.3), (Lt[8] - 0.05, crash, 0.12), (Lt[9], three, 0.35),
            (Lt[10], ray_end, 0.25), (Lt[10] + 2.0, ray_phone, 0.35)]
BEATS = beat_fns()
EYE = MARH + V3(-0.12, -0.08, -0.05)
def pov(f):
    t = (f - 1) / FPS; u = sstep((t - T0) / (T1 - T0)); look = PLATE_R + V3(0.12, 0.0, 0.0)
    eye = EYE.lerp(V3(-0.2, TY - 0.3, 1.75), 0.55 + 0.1 * u)       # leaning over the table toward Ray's pie and Coke
    return eye, eye + (look - eye).normalized() * 0.30
def beat_at(f, i):
    t0, fn, bl = BEATS[i]; t1 = BEATS[i + 1][0] if i + 1 < len(BEATS) else (NFR - 1) / FPS
    u = max(0.0, min(1.0, ((f - 1) / FPS - t0) / max(0.1, t1 - t0))); return fn(f, u)
def F_(t): return F(t)
for f in range(1, NFR + 1):
    t = (f - 1) / FPS
    if T0 <= t <= T1: cp, tp = pov(f)
    else:
        i = max(k for k, b_ in enumerate(BEATS) if b_[0] <= t or k == 0); cp, tp = beat_at(f, i)
        bl = BEATS[i][2]; w_ = sstep((t - BEATS[i][0]) / bl) if i > 0 else 1.0
        if w_ < 1:
            pc, pt = (pov(F(T1)) if BEATS[i][0] == T1 else beat_at(f, i - 1)); cp = pc.lerp(cp, w_); tp = pt.lerp(tp, w_)
        if T0 - 0.35 <= t < T0:     # swing up into Marcus's eyes from the side (he is hidden by then)
            u = sstep((t - (T0 - 0.35)) / 0.35); ec, et = pov(F(T0)); cp = cp.lerp(ec, u); tp = tp.lerp(et, u)
    key(cam, "location", cp, f); key(tgt, "location", tp, f); CAMP[f] = cp

def fwd_fn(xs, ys):
    def fwd(f):
        c = CAMP.get(f) or CAMP[min(CAMP, key=lambda k: abs(k - f))]; tx, ty = c.x - xs(f), c.y - ys(f); l = math.hypot(tx, ty) or 1; tx, ty = tx / l, ty / l
        hx, hy = 0.0, -1.0
        return (hx * (-ty) + hy * tx, hx * tx + hy * ty)
    return fwd

# ------------------------------------------------------------ arms: base pose + gestures, blended (2D card-plane targets and 3D body-space targets)
def build_anim(r, base, gest, kinds, talk_who, seed=1, head_extra=None, fwd=None):
    """base[sd] = ("2d", (x, z), fg) or ("3d", (side, fwd, up), fg). gest = [(t0, t1, sd, mode, target, fg, ease)]"""
    a_ = rig2.Anim(r, fwd); rnd_ = random.Random(seed)
    for f in range(1, NFR + 1):
        t = (f - 1) / FPS
        # body: breathing, talking bob, small weight shifts
        talking = any(l["who"] == talk_who and l["t0"] <= t <= l["t1"] for l in LINES)
        a_.key("spine", f, 1.2 * math.sin(2 * math.pi * 0.3 * t + seed) + (2.2 * math.sin(2 * math.pi * 2.1 * t) if talking else 0))
        hd = -1.5 * math.sin(2 * math.pi * 0.25 * t + seed) + (3.0 * math.sin(2 * math.pi * 2.6 * t + 1) if talking else 0)
        if head_extra: hd += head_extra(t)
        a_.key("head", f, hd); a_.key("hips", f, 0.006 * math.sin(2 * math.pi * 0.3 * t))
        for sd in ("L", "R"):
            mode, p, fg = base[sd]
            p2 = p if mode == "2d" else ((-1 if sd == "L" else 1) * 0.22, 0.6); p3 = p if mode == "3d" else (0.0, 0.0, 0.0); w3 = 1.0 if mode == "3d" else 0.0
            fgv = fg
            for (g0, g1, gs, gm, gp, gf, ez) in gest:
                if gs != sd: continue
                w_ = (1.0 if g0 <= 0 else sstep((t - g0) / ez)) * (1 - sstep((t - g1) / ez))
                if w_ <= 0: continue
                gp_ = gp(t) if callable(gp) else gp
                if gm == "2d": p2 = (p2[0] + (gp_[0] - p2[0]) * w_, p2[1] + (gp_[1] - p2[1]) * w_); w3 *= (1 - w_)
                else:
                    p3 = gp_ if w3 <= 1e-4 else tuple(p3[i] + (gp_[i] - p3[i]) * w_ for i in range(3)); w3 = w3 + (1 - w3) * w_
                fgv = fgv + w_ * (((gf - fgv) + 180) % 360 - 180)
            a_.key(f"hand.{sd}", f, *p2); a_.key(f"hand3.{sd}", f, *p3); a_.key(f"w3.{sd}", f, w3); a_.key(f"fingers.{sd}", f, fgv)
    a_.bake(1, NFR, bend={"arm.L": -1, "arm.R": 1})
    for sd, ks in kinds.items():
        for t, k in ks: rig2.set_hand(r, sd, k, max(1, F(t)))
    return a_

UP_T = (TOP - POS["ray"][2]) / 1.3          # table top in the uncles' local units
def eat(t0, t1, period=1.1, to=(0.05, 0.16, 1.33), frm=(0.12, 0.32, None)):
    frm = (frm[0], frm[1], UP_T + 0.08)
    def p(t):
        u = 0.5 - 0.5 * math.cos(2 * math.pi * (t - t0) / period); return tuple(frm[i] + (to[i] - frm[i]) * u for i in range(3))
    return p
CKL = ((CK[0] - POS["ray"][0]) / 1.3, (POS["ray"][1] - CK[1]) / 1.3)          # the Coke's table spot in Ray's body space (side, forward)
PIEL = ((PIE0[0] - POS["ray"][0]) / 1.3, (POS["ray"][1] - PIE0[1]) / 1.3)
COKE_SIP = (-0.02, 0.17, 1.36)
# Ray: pie slice in the right hand, Coke in the left
GR = [
    (0.0, Lt[1] - 0.05, "R", "3d", eat(0, 4, 1.05), 120, 0.2),
    (1.6, 2.7, "L", "3d", COKE_SIP, 70, 0.3),                                                                      # sip
    (Lt[1] + 0.05, Le[1] + 0.15, "R", "2d", (0.56, 1.2), 10, 0.2),                                                 # "The f*ck did you just say to me?" slice pointed at Marcus
    (Le[1] + 0.4, Lt[4] - 0.1, "R", "3d", eat(Le[1] + 0.4, 9, 1.3), 120, 0.3),
    (Lt[4] + 0.05, Lt[4] + 1.1, "R", "2d", (0.55, 1.12), 0, 0.2),                                                  # "Shut up, Dale"
    (Lt[4] + 1.3, Lt[4] + 2.2, "L", "3d", (CKL[0], CKL[1], UP_T + 0.1), 0, 0.3),                                 # puts the Coke down by the pie
    (Lt[4] + 2.3, Le[4] + 0.2, "L", "2d", (-0.42, 0.98), 130, 0.25), (Lt[4] + 2.3, Le[4] + 0.2, "R", "2d", (0.42, 0.98), 60, 0.25),   # "how much sugar is this?"
    (Lt[6], Le[6] + 0.1, "R", "2d", (0.55, 1.15), 0, 0.2),                                                         # "And how much am I allowed?"
    (Lt[8] - 0.75, Lt[8] - 0.35, "L", "3d", (CKL[0], CKL[1], UP_T + 0.1), 0, 0.15),                              # grabs the Coke back
    (Lt[8] - 0.35, Lt[8] + 0.05, "L", "3d", COKE_SIP, 70, 0.15),                                                   # mid-sip ...
    (Lt[8] + 0.05, Le[8] + 0.3, "L", "2d", (-0.55, 1.32), 105, 0.2), (Lt[8] + 0.05, Le[8] + 0.3, "R", "2d", (0.55, 1.32), 50, 0.15),  # "SEVENTY-ONE?"
    (Lt[10] - 0.1, Lt[10] + 0.4, "L", "3d", (CKL[0], CKL[1], UP_T + 0.1), 0, 0.12),                              # slams it down
    (Lt[10] + 1.1, 99, "R", "2d", (0.34, 1.02), 110, 0.5),                                                         # phone up, downloading
]
KR = {"L": [(0, "grip"), (Lt[4] + 2.2, "open"), (Lt[8] - 0.75, "grip"), (Lt[10] + 0.45, "open"), (Lt[10] + 0.8, "fist")],
      "R": [(0, "grip"), (Lt[1] + 0.05, "point"), (Le[1] + 0.3, "grip"), (Lt[4] + 0.05, "point"), (Lt[4] + 1.15, "grip"), (Lt[4] + 2.3, "open"), (Le[4] + 0.3, "grip"),
            (Lt[6], "point"), (Le[6] + 0.2, "grip"), (Lt[8] + 0.05, "open"), (Le[8] + 0.4, "grip"), (Lt[10] + 0.9, "palm")]}
# Dale: drumstick, freezes mid-bite when Ray snaps at him
GD = [
    (0.0, Lt[4], "R", "3d", eat(0, 9.5, 1.3, to=(0.05, 0.16, 1.33)), 120, 0.2),
    (Lt[4], Lt[5] - 0.3, "R", "3d", (0.05, 0.16, 1.33), 120, 0.15),                                                # caught mid-bite
    (Lt[5] - 0.3, 99, "R", "3d", eat(Lt[5] - 0.3, 30, 1.4, to=(0.05, 0.16, 1.33)), 120, 0.3),
    (Lt[3], Le[3] + 0.1, "L", "2d", (-0.5, 1.05), 160, 0.2),                                                       # "he's not wrong, Ray"
]
KD = {"R": [(0, "grip")], "L": [(0, "fist"), (Lt[3], "open"), (Le[3] + 0.3, "fist")]}
# Marcus: points at the pie, shrugs, phone in the right hand from the scan on
GM = [
    (0.6, Le[0] + 0.2, "L", "2d", (-0.55, 1.1), 180, 0.25),                                                        # "Unc. Keep going."
    (Lt[2], Le[2] + 0.1, "L", "2d", (-0.38, 0.84), 150, 0.3), (Lt[2], Le[2] + 0.1, "R", "2d", (0.38, 0.84), 30, 0.3),   # shrug
    (Lt[5] - 0.7, Le[5] + 0.3, "R", "2d", (0.3, 1.25), 90, 0.25),                                                  # phone up for the scan
    (Lt[7], Le[7], "L", "2d", (-0.45, 1.12), 170, 0.25),
    (Lt[9], Le[9] + 0.3, "R", "2d", (-0.05, 1.2), 90, 0.3),                                                        # shows Ray the app
]
KM = {"L": [(0, "fist"), (0.6, "point"), (Le[0] + 0.3, "fist"), (Lt[2], "open"), (Le[2] + 0.3, "fist"), (Lt[7], "point"), (Le[7] + 0.2, "fist")],
      "R": [(0, "fist"), (Lt[2], "open"), (Le[2] + 0.3, "fist"), (Lt[5] - 0.7, "palm"), (Le[9] + 0.5, "fist")]}
BASE_U = {"L": ("3d", (-0.2, 0.3, UP_T + 0.08), -70), "R": ("3d", (0.2, 0.3, UP_T + 0.08), -110)}
BASE_M = {"L": ("2d", (-0.25, 0.62), -90), "R": ("2d", (0.25, 0.62), -90)}
shake = lambda t: 0.0
ra = build_anim(ray, BASE_U, GR, KR, "ray", seed=1, fwd=fwd_fn(lambda f: POS["ray"][0], lambda f: POS["ray"][1]))
da = build_anim(dale, BASE_U, GD, KD, "dale", seed=2, fwd=fwd_fn(lambda f: POS["dale"][0], lambda f: POS["dale"][1]))
ma = build_anim(marcus, BASE_M, GM, KM, "marcus", seed=3, head_extra=shake, fwd=fwd_fn(lambda f: POS["marcus"][0], lambda f: POS["marcus"][1]))

# ------------------------------------------------------------ props in hands
holders(slice_, [(ray, "R", 0, 0, Lt[10] + 0.85)]); pop(slice_, None, Lt[10] + 0.85)
holders(can, [(ray, "L", -90, 0, Lt[4] + 2.15), (ray, "L", -90, Lt[8] - 0.4, Lt[10] + 0.38)])
holders(drum, [(dale, "R", 90, 0, 99)])
ph_m, scr_m = phone("phone_marcus")
holders(ph_m, [(marcus, "R", 0, Lt[5] - 0.7, Le[9] + 0.5)]); pop(ph_m, Lt[5] - 0.7, Le[9] + 0.5)
ph_r, scr_r = phone("phone_ray")
holders(ph_r, [(ray, "R", 0, Lt[10] + 0.95, 99)]); pop(ph_r, Lt[10] + 0.95)
# ------------------------------------------------------------ Marcus's POV: hide him, show his hand + phone under the camera
def tree_(o):
    yield o
    for c in o.children: yield from tree_(c)
def vis(o, frames):
    for f, h in frames: o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
mobjs = set(tree_(marcus["arm"])) | set(tree_(ph_m)) | {o for o in bpy.data.objects if o.name.startswith("marcus_")}
for o in mobjs: vis(o, [(1, False), (F(T0 - 0.35), True), (F(T1), False)])
root = bpy.data.objects.new("pov_root", None); S.collection.objects.link(root); root.parent = cam
root.location = (0.02, -0.06, -0.30); root.rotation_euler = (R(-90 + 9), R(-4), R(2))
pv, scr_pov = phone("phone_pov"); pv.parent = root
ART = os.path.join(ARTD, "marcus"); HJ = json.load(open(os.path.join(ART, "pov_hand.json")))
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
cardxz("pov_arm", "arm.png", -0.05, 0.05, -0.40, 0.0, D / 2 + 0.006, uv=((0, 0.62), (1, 0.62), (1, 0.0), (0, 0.0)), rot=-28, piv=(wx + 0.002, wz + 0.024))
for o in set(tree_(root)): vis(o, [(1, True), (F(T0), False), (F(T1), True)])
SCREENS = [ph_m, pv, ph_r]
TIMES = {"POV": [T0, T1], "scan": Lt[5] - 0.05, "slam": Lt[10] + 0.38, "choke": Lt[8]}
json.dump(TIMES, open(OUT.replace(".blend", "_times.json"), "w"))
