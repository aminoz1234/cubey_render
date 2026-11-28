# Ep4 keys. exec'd inside build_ep4.py. Times in seconds (dialogue timeline). Character-local units: x right, z up, feet at 0.
import math, random
Lt = [l["t0"] for l in LINES]; Le = [l["t1"] for l in LINES]
def sstep(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def V3(x, y, z): return Vector((x, y, z))
CAMP = {}
T_BUMP = 0.28; T_GO = Lt[12] + 0.7; VW = 1.4
# ------------------------------------------------------------ where everyone is: walk in, bump, stand, scatter when the taxi honks
def xpath(x_stop, x_from, x_away, t_stop, recoil):
    def x(t):
        if t < t_stop: return x_from + (x_stop - x_from) * (t / t_stop)
        r = recoil * sstep((t - t_stop) / 0.25) * (1 - 0.6 * sstep((t - t_stop - 0.25) / 0.6))
        u = max(0.0, t - T_GO); return x_stop + r + (x_away - x_stop) * min(1.0, (u * u * 0.9 + u * 0.4) / 5.0)
    return x
XP = {"kayla": xpath(-0.42, -0.42 - VW * T_BUMP, -6.0, T_BUMP, -0.09), "tasha": xpath(0.42, 0.42 + VW * T_BUMP, 6.0, T_BUMP, 0.09),
      "josh": xpath(-1.05, -1.05 - VW * 0.6, -6.5, 0.6, 0.0), "devin": xpath(1.05, 1.05 + VW * 0.7, 6.5, 0.7, 0.0)}
HEAD = {"kayla": 1, "tasha": -1, "josh": 1, "devin": -1}          # +x / -x heading while walking in; reversed when they scatter
for who in WHO:
    for f in range(1, NFR + 1):
        t = (f - 1) / FPS; key(RIG[who]["arm"], "location", Vector((XP[who](t), POS[who][1], 0)), f)
def speed(who, t): return abs(XP[who](t + 0.5 / FPS) - XP[who](t - 0.5 / FPS)) * FPS
def heading(who, t): return HEAD[who] * (1 if t < T_GO else -1)

# ------------------------------------------------------------ camera beats (new framing every ~2.5-3.5 s), Devin's POV for the scan
FRAP_AT = lambda: V3(XP["kayla"](17) - 0.45, 0.0, 1.42)
BOBA_AT = lambda: V3(XP["tasha"](17) + 0.45, 0.05, 1.42)
T0, T1 = Lt[7] - 0.35, Le[7] + 0.12
def beats():
    shake = lambda t: V3(0.03 * math.sin(t * 90), 0, 0.02 * math.cos(t * 77)) * math.exp(-8 * max(0, t - T_BUMP)) * (t > T_BUMP)
    def hook(f, u):  t = (f - 1) / FPS; return V3(0.0, -3.3 + 0.4 * u, 1.35) + shake(t), V3(0.0, 0.1, 1.65)
    def tasha_c(f, u): return V3(0.85, -1.8 + 0.15 * u, 1.95), V3(0.42, 0.12, 1.9)
    def kayla_c(f, u): return V3(-0.85, -1.8 + 0.15 * u, 1.9), V3(-0.42, 0.05, 1.88)
    def tasha_h(f, u): return V3(0.2, -1.85, 2.6 - 0.1 * u), V3(0.42, 0.12, 1.85)
    def josh_c(f, u):  return V3(-1.45, -1.9 + 0.15 * u, 1.95), V3(-1.05, 0.55, 1.95)
    def devin_l(f, u): return V3(1.1 + 0.1 * u, -1.95, 1.05), V3(1.05, 0.6, 1.95)
    def girls(f, u):   return V3(0.0, -3.4 + 0.3 * u, 1.7), V3(0.0, 0.1, 1.75)
    def tasha_w(f, u): return V3(0.7, -1.75 + 0.12 * u, 1.85), V3(0.42, 0.12, 1.88)
    def devin_s(f, u): return V3(-0.3, -2.3 + 0.3 * u, 1.95), V3(0.85, 0.6, 1.8)
    def two(f, u):     return V3(0.05, -3.2 + 0.25 * u, 1.8), V3(0.0, 0.1, 1.85)
    def kayla_s(f, u): return V3(-0.7, -1.75 + 0.12 * u, 1.8), V3(-0.42, 0.05, 1.86)
    def tasha_m(f, u): return V3(0.65, -1.75, 1.85), V3(0.42, 0.12, 1.88)
    def wide(f, u):    return V3(0.4, -3.4 - 1.4 * u, 2.0 + 0.4 * u), V3(0.0, 2.0, 1.45)
    return [(0.0, hook, 0.3), (Lt[1], tasha_c, 0.2), (Lt[2], kayla_c, 0.2), (Lt[3], tasha_h, 0.25), (Lt[4], josh_c, 0.15), (Lt[5], devin_l, 0.3),
            (Lt[6], girls, 0.25), (T1, tasha_w, 0.3), (Lt[9], devin_s, 0.3), (Lt[9] + 1.8, two, 0.35), (Lt[10], kayla_s, 0.2), (Lt[11], tasha_m, 0.15), (Lt[12] - 0.1, wide, 0.2)]
BEATS = beats()
EYE = V3(1.0, 0.42, 2.05)
def pov(f):
    t = (f - 1) / FPS; u = sstep((t - (Lt[7] + 1.6)) / 1.3)
    look = FRAP_AT().lerp(BOBA_AT(), u) + V3(0.1, 0, -0.5); eye = V3(0.15 + 0.1 * u, -1.15, 2.3)
    return eye, eye + (look - eye).normalized() * 0.3
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
        if T0 - 0.35 <= t < T0:
            u = sstep((t - (T0 - 0.35)) / 0.35); ec, et = pov(F(T0)); cp = cp.lerp(ec, u); tp = tp.lerp(et, u)
    key(cam, "location", cp, f); key(tgt, "location", tp, f); CAMP[f] = cp

def fwd_for(who):
    def fwd(f):
        t = (f - 1) / FPS; c = CAMP.get(f) or CAMP[min(CAMP, key=lambda k: abs(k - f))]; x_, y_ = XP[who](t), POS[who][1]
        tx, ty = c.x - x_, c.y - y_; l = math.hypot(tx, ty) or 1; tx, ty = tx / l, ty / l
        hx, hy = heading(who, t), 0.0
        if speed(who, t) < 0.2: hx, hy = 0.35 * heading(who, t), -0.94      # standing: mostly facing the street/camera, turned toward the other couple
        return (hx * (-ty) + hy * tx, hx * tx + hy * ty)
    return fwd

# ------------------------------------------------------------ walking + gestures (2D card-plane targets; walking arms swing in body space)
def build_anim(r, who, gest, kinds, talk_who, seed=1, hold=None):
    a_ = rig2.Anim(r, fwd_for(who)); z = r["z"]; Sk = r["S"]; ph = seed * 1.3
    for f in range(1, NFR + 1):
        t = (f - 1) / FPS; A = min(1.0, speed(who, t) / VW); ph += 2 * math.pi * (1.6 + 0.9 * A) / FPS * (1 if A > 0.03 else 0)
        sL, sR = math.sin(ph), math.sin(ph + math.pi)
        for sd_, s__, sw_ in (("L", -1, sL), ("R", 1, sR)):
            a_.key(f"foot3.{sd_}", f, s__ * Sk["hipW"] * 0.95, 0.15 * A * sw_, z["ank"] + 0.08 * A * max(0.0, sw_))
        talking = any(l["who"] == talk_who and l["t0"] <= t <= l["t1"] for l in LINES)
        a_.key("hips", f, 0.025 * A * abs(math.cos(ph)) + 0.006 * math.sin(2 * math.pi * 0.3 * t))
        a_.key("spine", f, 2.5 * A * math.sin(ph) + 1.2 * math.sin(2 * math.pi * 0.3 * t + seed) + (2.0 * math.sin(2 * math.pi * 2.1 * t) if talking else 0))
        a_.key("head", f, -1.5 * math.sin(2 * math.pi * 0.25 * t + seed) + (3.0 * math.sin(2 * math.pi * 2.6 * t + 1) if talking else 0))
        for sd, s_, sw in (("L", -1, sR), ("R", 1, sL)):
            held = hold and sd in hold
            x, zz, fg = (s_ * 0.24, 0.62, -90.0)
            if held: x, zz, fg = hold[sd]
            wmax = 0.0
            for (g0, g1, gs, gx, gz, gf, ez) in gest:
                if gs != sd: continue
                w_ = (1.0 if g0 <= 0 else sstep((t - g0) / ez)) * (1 - sstep((t - g1) / ez))
                if w_ > 0:
                    wmax = max(wmax, w_); gx_ = gx(t) if callable(gx) else gx
                    x, zz = x + (gx_ - x) * w_, zz + (gz - zz) * w_; fg = fg + w_ * (((gf - fg) + 180) % 360 - 180)
            a_.key(f"hand.{sd}", f, x, zz); a_.key(f"fingers.{sd}", f, fg)
            swing = (1 - wmax) * min(1.0, 3 * A) * (0.3 if held else 1.0)
            a_.key(f"hand3.{sd}", f, s_ * 0.2, 0.17 * sw, 0.66 + 0.05 * sw); a_.key(f"w3.{sd}", f, swing)
    a_.bake(1, NFR, bend={"arm.L": -1, "arm.R": 1})
    for sd, ks in kinds.items():
        for t, k in ks: rig2.set_hand(r, sd, k, max(1, F(t)))
    return a_

# Kayla: Frappuccino in the LEFT hand (fingers +x keep it upright), roasts with the right
GK = [(T_BUMP, T_BUMP + 0.4, "L", -0.42, 1.15, 0, 0.15),                                       # drink jolts up on the bump
      (T_BUMP + 0.2, Le[0] + 0.15, "R", 0.56, 1.15, 10, 0.15),                                 # "Watch where you're f*cking walking!"
      (Lt[2] + 0.3, Le[2] + 0.1, "R", 0.55, 1.32, 30, 0.2),                                    # "your face is puffier and bumpier..."
      (Lt[6], Le[6] + 0.1, "R", 0.42, 0.98, 30, 0.2),                                          # "The hell does that mean?"
      (Lt[7] - 0.2, Le[7] + 0.2, "L", -0.32, 1.02, 0, 0.3),                                    # holds the drink out for the scan
      (Lt[10], Le[10] + 0.2, "R", 0.32, 1.1, 60, 0.25)]                                        # "send me that Cubey sh*t"
KK = {"L": [(0, "grip")], "R": [(0, "fist"), (T_BUMP + 0.2, "point"), (Le[0] + 0.3, "fist"), (Lt[2] + 0.3, "point"), (Le[2] + 0.3, "fist"), (Lt[6], "open"), (Le[6] + 0.3, "fist"), (Lt[10], "palm"), (Le[10] + 0.3, "fist")]}
# Tasha: boba in the RIGHT hand, roasts with the left
GT = [(T_BUMP, T_BUMP + 0.4, "R", 0.42, 1.15, 0, 0.15),
      (Lt[1] + 0.4, Le[1], "L", -0.55, 1.08, 170, 0.2),                                        # "You take up the whole crosswalk."
      (Lt[3], Le[3] + 0.1, "L", -0.2, 1.42, 120, 0.25),                                        # "At least my face fits in the photo." frames her face
      (Lt[7] - 0.2, Le[7] + 0.2, "R", 0.32, 1.02, 0, 0.3),                                     # holds the boba out for the scan
      (Lt[8], Le[8] + 0.3, "R", 0.3, 1.22, 0, 0.25),                                           # "...and the limit?" stares at it
      (Lt[11], Le[11] + 0.3, "L", -0.32, 1.38, 110, 0.15)]                                     # "Me too." hand up
KT = {"R": [(0, "grip")], "L": [(0, "fist"), (Lt[1] + 0.4, "point"), (Le[1] + 0.2, "fist"), (Lt[3], "open"), (Le[3] + 0.3, "fist"), (Lt[11], "open"), (Le[11] + 0.4, "fist")]}
# Josh: placating, then panic at the taxi
GJ = [(Lt[4], Le[4] + 0.2, "L", -0.42, 1.1, 150, 0.2), (Lt[4], Le[4] + 0.2, "R", 0.42, 1.1, 30, 0.2),
      (Lt[12], T_GO, "L", -0.5, 1.45, 120, 0.12), (Lt[12], T_GO, "R", 0.55, 1.4, 60, 0.12)]
KJ = {"L": [(0, "fist"), (Lt[4], "open"), (Le[4] + 0.4, "fist"), (Lt[12], "open")], "R": [(0, "fist"), (Lt[4], "open"), (Le[4] + 0.4, "fist"), (Lt[12], "point")]}
# Devin: phone in the right hand, chill
GD = [(Lt[5], Le[5], "L", -0.36, 0.96, 160, 0.25),
      (Lt[5] - 0.6, Lt[7] - 0.3, "R", 0.3, 1.0, 90, 0.3),
      (Le[7], Le[9] + 0.3, "R", -0.05, 1.22, 90, 0.35)]                                        # shows them the app
KD = {"L": [(0, "fist"), (Lt[5], "open"), (Le[5] + 0.3, "fist")], "R": [(0, "fist"), (Lt[5] - 0.6, "palm")]}
ka = build_anim(kayla, "kayla", GK, KK, "kayla", seed=1, hold={"L": (-0.34, 1.0, 0)})
ta = build_anim(tasha, "tasha", GT, KT, "tasha", seed=2, hold={"R": (0.34, 1.0, 0)})
ja = build_anim(josh, "josh", GJ, KJ, "josh", seed=3)
da = build_anim(devin, "devin", GD, KD, "devin", seed=4)

# ------------------------------------------------------------ props: the two drinks, Devin's phone, the splash, the taxi
CUPM = mmat("cup_m", (0.95, 0.95, 0.95), 0.15)
def frappuccino(name):
    c = obj_from(bpy.ops.mesh.primitive_cone_add, name, radius1=0.042, radius2=0.055, depth=0.16, vertices=40, location=(0, 0, 0.08)); smooth(c)
    for v in c.data.vertices: v.co.z += 0.08
    c.location = (0, 0, 0); c.data.materials.append(mmat("frap_m", hexc("#c98a52"), 0.35))
    band = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_band", radius=0.05, depth=0.03, vertices=40, location=(0, 0, 0.1)); band.data.materials.append(mmat("sleeve_m", hexc("#50312f"), 0.6)); band.parent = c
    dome = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, name + "_whip", radius=0.055, segments=24, ring_count=12, location=(0, 0, 0.165)); dome.scale = (1, 1, 0.75); smooth(dome); dome.data.materials.append(mmat("whip_m", hexc("#fdf3d0"), 0.6)); dome.parent = c
    dr = obj_from(bpy.ops.mesh.primitive_torus_add, name + "_drizzle", major_radius=0.035, minor_radius=0.006, location=(0, 0, 0.195)); dr.data.materials.append(mmat("drizzle_m", hexc("#b5651d"), 0.2)); dr.parent = c
    st = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_straw", radius=0.007, depth=0.14, location=(0.012, 0, 0.24)); st.rotation_euler = (0, R(10), 0); st.data.materials.append(mmat("strawg_m", hexc("#2a9d8f"), 0.4)); st.parent = c
    return c
def boba(name):
    c = obj_from(bpy.ops.mesh.primitive_cone_add, name, radius1=0.042, radius2=0.052, depth=0.17, vertices=40, location=(0, 0, 0)); smooth(c)
    for v in c.data.vertices: v.co.z += 0.085
    c.data.materials.append(mmat("milktea_m", hexc("#d9b48a"), 0.3))
    for i in range(14):
        a = i / 14 * 2 * math.pi; p_ = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, f"{name}_pearl{i}", radius=0.011, segments=10, ring_count=6, location=(0.044 * math.cos(a), 0.044 * math.sin(a), 0.018 + 0.012 * (i % 2)))
        p_.data.materials.append(mmat("pearl_m", hexc("#2a1810"), 0.15)); p_.parent = c
    lid = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_lid", radius=0.054, depth=0.006, vertices=40, location=(0, 0, 0.172)); lid.data.materials.append(mmat("seal_m", hexc("#f4c3d0"), 0.4)); lid.parent = c
    st = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_straw", radius=0.011, depth=0.16, location=(-0.01, 0, 0.24)); st.rotation_euler = (0, R(-8), 0); st.data.materials.append(mmat("strawb_m", hexc("#1f2833"), 0.3)); st.parent = c
    return c
def join_all(o):          # one mesh per prop: a held prop is safest as a single object (no child transforms to go astray)
    bpy.context.view_layer.update(); kids = list(o.children_recursive)
    for k_ in kids: mw = k_.matrix_world.copy(); k_.parent = None; k_.matrix_world = mw
    bpy.ops.object.select_all(action="DESELECT")
    for k_ in [o] + kids: k_.select_set(True)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.join(); return o
frap = join_all(frappuccino("frap")); bob = join_all(boba("boba"))
for o_ in (frap, bob):
    o_.scale = (1.6, 1.6, 1.6); bpy.context.view_layer.update(); bpy.ops.object.select_all(action="DESELECT"); o_.select_set(True); bpy.context.view_layer.objects.active = o_
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
tag(frap, "frap"); tag(bob, "boba")
holders(frap, [(kayla, "L", -90, 0, 99)]); holders(bob, [(tasha, "R", 90, 0, 99)])
ph_d, scr_d = phone("phone_devin")
holders(ph_d, [(devin, "R", 0, Lt[5] - 0.6, 99)]); pop(ph_d, Lt[5] - 0.6)
# splash on the bump: droplets fly and fade
rs = random.Random(11); SPL = mmat("splash_m", hexc("#c98a52"), 0.2); SPL2 = mmat("splash2_m", hexc("#e8cfa8"), 0.2)
for i in range(18):
    d = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, f"drop{i}", radius=rs.uniform(0.012, 0.024), segments=10, ring_count=6, location=(0, 0, 0)); smooth(d); d.data.materials.append(SPL if i % 2 else SPL2)
    p0 = V3(rs.uniform(-0.12, 0.12), -0.05, 1.25 * 1.3 / 1.3 + rs.uniform(-0.05, 0.1)); v = V3(rs.uniform(-1.2, 1.2), rs.uniform(-0.8, -0.2), rs.uniform(1.0, 2.6))
    for f in range(1, F(T_BUMP + 0.9)):
        t = (f - 1) / FPS - T_BUMP
        if t < 0: d.scale = (0, 0, 0); d.location = p0
        else: d.location = p0 + v * t + V3(0, 0, -4.9 * t * t); s_ = max(0.0, 1 - t / 0.6); d.scale = (s_, s_, s_ * 1.3)
        d.keyframe_insert("location", frame=f); d.keyframe_insert("scale", frame=f)
    d.scale = (0, 0, 0); d.keyframe_insert("scale", frame=F(T_BUMP + 0.9))
# the taxi rolls up and honks
for f in range(1, NFR + 1):
    t = (f - 1) / FPS; u = sstep((t - (Lt[12] - 1.6)) / 1.5); key(taxi, "location", Vector((1.6, 30 - 26.6 * (1 - (1 - u) ** 2), 0.25)), f)

# ------------------------------------------------------------ Devin's POV: hide him, show his hand + phone under the camera
def tree_(o):
    yield o
    for c in o.children: yield from tree_(c)
def vis(o, frames):
    for f, h in frames: o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
dobjs = set(tree_(devin["arm"])) | set(tree_(ph_d)) | {o for o in bpy.data.objects if o.name.startswith("devin_")}
for o in dobjs: vis(o, [(1, False), (F(T0 - 0.35), True), (F(T1), False)])
root = bpy.data.objects.new("pov_root", None); S.collection.objects.link(root); root.parent = cam
root.location = (0.05, -0.075, -0.30); root.rotation_euler = (R(-90 + 9), R(-4), R(2))
pv, scr_pov = phone("phone_pov"); pv.parent = root
ART = os.path.join(ARTD, "devin"); HJ = json.load(open(os.path.join(ART, "pov_hand.json")))
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
SCREENS = [ph_d, pv]
TIMES = {"POV": [T0, T1], "scan": Lt[7] + 0.1, "bump": T_BUMP, "honk": Lt[12] - 0.15}
json.dump(TIMES, open(OUT.replace(".blend", "_times.json"), "w"))
