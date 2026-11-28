# Ep1 keys. Times in seconds (from the dialogue), positions in each character's own units (x right, z up, feet at 0).
import math
SC = 1.3
def loc(r, wx, wz):            # a world point on the table -> this character's card-plane units (approximate, camera roughly along +y)
    return ((wx - r["arm"].location.x) / SC, wz / SC)
TOPL = TOP / SC
def A(r): return rig2.Anim(r)

# ---------------- SON: sipping when she yanks the can, complains, points at Grandpa, later steals it back
a = A(son); z = son["z"]
for sd, s in (("L", -1), ("R", 1)): a.key(f"foot.{sd}", 1, s * son["S"]["hipW"], z["ank"])
a.key("hand.L", 1, -0.13, 0.5).key("hand.L", F(1.2), -0.2, 0.62).key("hand.L", F(2.2), -0.14, 0.5)
a.key("hand.R", 1, 0.17, 1.0).key("hand.R", F(0.32), 0.17, 1.0).key("hand.R", F(0.55), 0.22, 0.86).key("hand.R", F(1.1), 0.24, 0.68).key("hand.R", F(2.0), 0.2, 0.56)
a.key("fingers.R", 1, 62).key("fingers.R", F(0.5), 40).key("fingers.R", F(1.0), -60).key("fingers.L", 1, -95)
# "That's literally the same thing." open palm
a.key("hand.R", F(4.3), 0.2, 0.56).key("hand.R", F(4.7), 0.32, 0.86).key("hand.R", F(5.9), 0.3, 0.84).key("hand.R", F(6.4), 0.2, 0.56)
a.key("fingers.R", F(4.3), -60).key("fingers.R", F(4.7), 30).key("fingers.R", F(6.4), -70)
# "Ask Grandpa." point right
a.key("hand.R", F(7.7), 0.2, 0.56).key("hand.R", F(8.1), 0.55, 0.98).key("hand.R", F(9.8), 0.53, 0.96).key("hand.R", F(10.3), 0.2, 0.56)
a.key("fingers.R", F(7.7), -70).key("fingers.R", F(8.1), 8).key("fingers.R", F(10.3), -80)
# 37.6: steps right to the table, grabs the can, sips on his last line
X0s, X1s = POS["son"][0], -1.95
for f in range(F(37.5), F(38.4) + 1):
    u = (f - F(37.5)) / (F(38.4) - F(37.5)); u = u * u * (3 - 2 * u)
    key(son["arm"], "location", Vector((X0s + (X1s - X0s) * u, POS["son"][1], 0)), f)
    ph = u * 2 * math.pi
    for sd, s, off in (("L", -1, 0), ("R", 1, math.pi)):
        a.key(f"foot.{sd}", f, s * son["S"]["hipW"], z["ank"] + 0.05 * max(0, math.sin(ph + off)))
key(son["arm"], "location", Vector((X0s, POS["son"][1], 0)), 1)
cx, cz = loc(son, CAN_T[0], TOP + 0.1); cx = (CAN_T[0] - X1s) / SC
a.key("hand.R", F(37.6), 0.2, 0.56).key("hand.R", F(38.5), cx - 0.02, cz).key("hand.R", F(38.75), cx - 0.02, cz).key("hand.R", F(39.6), 0.17, 1.0).key("hand.R", F(40.9), 0.17, 1.0)
a.key("fingers.R", F(37.6), -70).key("fingers.R", F(38.5), 0).key("fingers.R", F(39.6), 60).key("fingers.R", F(40.6), 70)
a.key("head", 1, -6).key("head", F(0.5), 5).key("head", F(2.0), 3).key("head", F(6.0), -4).key("head", F(7.6), 0).key("head", F(18.2), 6).key("head", F(20), 2).key("head", F(39.6), -7).key("head", F(41), -5)
a.key("spine", 1, -2).key("spine", F(0.5), 2).key("spine", F(5.0), -1).key("spine", F(18.2), 2).key("spine", F(20), 0).key("spine", F(39.6), -3)
a.key("hips", 1, 0).key("hips", F(18.1), 0).key("hips", F(18.3), 0.03).key("hips", F(18.6), 0)
a.bake(1, NFR)
rig2.set_hand(son, "R", "grip", 1); rig2.set_hand(son, "R", "open", F(0.5)); rig2.set_hand(son, "R", "point", F(8.0)); rig2.set_hand(son, "R", "open", F(10.2))
rig2.set_hand(son, "R", "grip", F(38.6)); rig2.set_hand(son, "L", "open", 1)

# ---------------- MOM: yanks the can (L), holds the juice up (R), sets both down for Grandpa, points at her own breakfast, phone
b = A(mom); z = mom["z"]
for sd, s in (("L", -1), ("R", 1)): b.key(f"foot.{sd}", 1, s * mom["S"]["hipW"], z["ank"])
sonmouth = ((POS["son"][0] + 0.17 * SC - POS["mom"][0]) / SC, 1.0)
b.key("hand.L", 1, -0.25, 0.75).key("hand.L", F(0.28), sonmouth[0] + 0.06, sonmouth[1]).key("hand.L", F(0.4), sonmouth[0] + 0.06, sonmouth[1]).key("hand.L", F(0.9), -0.3, 0.8)
b.key("hand.L", F(4.0), -0.28, 0.78).key("hand.L", F(10.2), -0.28, 0.78)
canx = (CAN_T[0] - POS["mom"][0]) / SC; glx = (GLASS_T[0] - POS["mom"][0]) / SC; tz = (TOP + 0.1) / SC
b.key("hand.L", F(10.75), canx, tz).key("hand.L", F(10.95), canx, tz).key("hand.L", F(11.5), -0.2, 0.62)
b.key("fingers.L", 1, 180).key("fingers.L", F(10.95), 180).key("fingers.L", F(11.5), -95)
b.key("hand.R", 1, 0.22, 0.62).key("hand.R", F(1.7), 0.22, 0.62).key("hand.R", F(2.3), 0.3, 1.0).key("hand.R", F(4.2), 0.28, 0.98)
b.key("hand.R", F(6.0), 0.3, 1.02).key("hand.R", F(7.6), 0.29, 1.0).key("hand.R", F(11.1), 0.27, 0.96).key("hand.R", F(11.6), glx, tz).key("hand.R", F(11.8), glx, tz).key("hand.R", F(12.4), 0.22, 0.62)
b.key("fingers.R", 1, 0).key("fingers.R", F(11.8), 0).key("fingers.R", F(12.4), -85)
# "Thank you." hands on hips
b.key("hand.L", F(15.4), -0.2, 0.62).key("hand.L", F(15.7), -0.24, 0.66).key("hand.R", F(15.4), 0.22, 0.62).key("hand.R", F(15.7), 0.24, 0.66)
# "Eight? It's fruit." hands up
b.key("hand.L", F(18.0), -0.24, 0.66).key("hand.L", F(18.3), -0.28, 1.15).key("hand.R", F(18.0), 0.24, 0.66).key("hand.R", F(18.3), 0.28, 1.15)
b.key("fingers.L", F(18.0), -95).key("fingers.L", F(18.3), 110).key("fingers.R", F(18.0), -85).key("fingers.R", F(18.3), 70)
b.key("hand.L", F(19.8), -0.27, 1.12).key("hand.L", F(20.4), -0.2, 0.62).key("hand.R", F(19.8), 0.27, 1.12).key("hand.R", F(20.4), 0.22, 0.62)
b.key("fingers.L", F(20.4), -95).key("fingers.R", F(20.4), -85)
# "What about my smoothie? The granola bars? The yogurt?" points at each, arm out toward the table
for t, item in ((27.9, "smoothie"), (29.0, "granola"), (30.1, "yogurt")):
    ix = (ITEMS[item][0] - POS["mom"][0]) / SC
    if t < 28: b.key("hand.R", F(t - 0.35), 0.24, 0.66)
    b.key("hand.R", F(t), min(ix, 0.62), 0.92)
    b.key("fingers.R", F(t), -20)
b.key("hand.R", F(31.0), 0.6, 0.92)
# "Sugar. Sugar. Also sugar." hands to cheeks
b.key("hand.R", F(31.4), 0.27, 1.12).key("hand.L", F(31.0), -0.2, 0.62).key("hand.L", F(31.4), -0.27, 1.12)
b.key("fingers.R", F(31.4), 75).key("fingers.L", F(31.0), -95).key("fingers.L", F(31.4), 105)
# "How do you know all this?" hands on hips
b.key("hand.R", F(33.9), 0.27, 1.1).key("hand.R", F(34.2), 0.24, 0.66).key("hand.L", F(33.9), -0.27, 1.1).key("hand.L", F(34.2), -0.24, 0.66)
b.key("fingers.R", F(34.2), -85).key("fingers.L", F(34.2), -95)
# "Downloading it." walks off right along the table front, phone up
X0m, X1m = POS["mom"][0], -0.55
for f in range(F(37.5), F(38.7) + 1):
    u = (f - F(37.5)) / (F(38.7) - F(37.5)); u = u * u * (3 - 2 * u)
    key(mom["arm"], "location", Vector((X0m + (X1m - X0m) * u, POS["mom"][1], 0)), f)
    ph = u * 3 * math.pi
    for sd, s_, off in (("L", -1, 0), ("R", 1, math.pi)):
        b.key(f"foot.{sd}", f, s_ * mom["S"]["hipW"], z["ank"] + 0.05 * max(0, math.sin(ph + off)))
key(mom["arm"], "location", Vector((X0m, POS["mom"][1], 0)), 1)
b.key("hand.R", F(37.3), 0.24, 0.66).key("hand.R", F(37.8), 0.1, 1.02).key("hand.R", F(41.3), 0.1, 1.02).key("fingers.R", F(37.3), -85).key("fingers.R", F(37.8), 95)
b.key("head", 1, 4).key("head", F(0.6), -5).key("head", F(2.4), 4).key("head", F(6.0), 6).key("head", F(10.0), -3).key("head", F(15.6), 8).key("head", F(18.2), -6).key("head", F(20), 0)
b.key("head", F(27.5), 4).key("head", F(31.4), -6).key("head", F(34.0), 6).key("head", F(37.8), -8).key("head", F(41), -8)
b.key("spine", 1, 0).key("spine", F(0.3), -6).key("spine", F(1.0), 0).key("spine", F(10.8), -4).key("spine", F(12.4), 0).key("spine", F(15.6), 3).key("spine", F(18.2), -4).key("spine", F(20), 0).key("spine", F(37.8), -3)
b.key("hips", 1, 0).key("hips", F(18.1), 0).key("hips", F(18.3), 0.05).key("hips", F(18.6), 0).key("hips", F(31.3), 0).key("hips", F(31.5), 0.04).key("hips", F(31.8), 0)
b.bake(1, NFR)
rig2.set_hand(mom, "L", "open", 1); rig2.set_hand(mom, "L", "grip", F(0.35)); rig2.set_hand(mom, "L", "open", F(10.95)); rig2.set_hand(mom, "L", "wave", F(18.2)); rig2.set_hand(mom, "L", "open", F(20.3))
rig2.set_hand(mom, "L", "wave", F(31.3)); rig2.set_hand(mom, "L", "fist", F(34.1))
rig2.set_hand(mom, "R", "grip", 1); rig2.set_hand(mom, "R", "open", F(11.8)); rig2.set_hand(mom, "R", "fist", F(15.5)); rig2.set_hand(mom, "R", "wave", F(18.2)); rig2.set_hand(mom, "R", "open", F(20.3))
rig2.set_hand(mom, "R", "point", F(27.6)); rig2.set_hand(mom, "R", "wave", F(31.3)); rig2.set_hand(mom, "R", "fist", F(34.1)); rig2.set_hand(mom, "R", "palm", F(37.6))

# ---------------- GRANDPA: leans on the table, looks up, points at the can and the glass, holds an orange, phone
c = A(gpa); z = gpa["z"]
for sd, s in (("L", -1), ("R", 1)): c.key(f"foot.{sd}", 1, s * gpa["S"]["hipW"], z["ank"])
rest = {"L": (-0.3, TOPL), "R": (0.2, 0.56)}
c.key("hand.L", 1, *rest["L"]).key("fingers.L", 1, -90).key("hand.R", 1, *rest["R"]).key("fingers.R", 1, -80)
c.key("spine", 1, 3).key("spine", F(9.2), 3).key("spine", F(10.0), 0)
cpt = ((CAN_T[0] - POS["grandpa"][0]) / SC, TOPL + 0.05); gpt = ((GLASS_T[0] - POS["grandpa"][0]) / SC, TOPL + 0.05)
# "One can of soda... ten sugar cubes." left hand points at the can
c.key("hand.L", F(12.7), *rest["L"]).key("hand.L", F(13.1), -0.62, 0.98).key("hand.L", F(15.3), -0.62, 0.98).key("fingers.L", F(12.7), -90).key("fingers.L", F(13.1), 200)
# "Same glass of juice... eight." points at the glass
c.key("hand.L", F(16.1), -0.6, 1.0).key("hand.L", F(18.0), -0.6, 1.0).key("fingers.L", F(16.1), 195).key("hand.L", F(19.0), *rest["L"]).key("fingers.L", F(19.0), -90)
# explanation: orange held up in the right hand, then the left hand opens on "no fiber"
c.key("hand.R", F(19.4), *rest["R"]).key("hand.R", F(19.9), 0.2, 1.15).key("hand.R", F(26.8), 0.2, 1.12).key("hand.R", F(27.4), *rest["R"])
c.key("fingers.R", F(19.4), -80).key("fingers.R", F(19.9), 90).key("fingers.R", F(27.4), -80)
c.key("hand.L", F(23.6), *rest["L"]).key("hand.L", F(24.0), -0.3, 1.02).key("hand.L", F(26.5), -0.3, 1.0).key("hand.L", F(27.0), *rest["L"])
c.key("fingers.L", F(23.6), -90).key("fingers.L", F(24.0), 120).key("fingers.L", F(27.0), -90)
# "Sugar. Sugar. Also sugar." points at each item in turn
for t, item in ((31.35, "smoothie"), (32.05, "granola"), (33.35, "yogurt")):
    ix = (ITEMS[item][0] + 0.12 - POS["grandpa"][0]) / SC
    c.key("hand.L", F(t), max(ix, -0.62), 0.95).key("fingers.L", F(t), 205)
c.key("hand.L", F(31.0), *rest["L"]).key("hand.L", F(34.2), -0.45, 0.95).key("hand.L", F(34.6), *rest["L"]).key("fingers.L", F(34.6), -90)
# phone: up in the right hand, screen to camera
c.key("hand.R", F(34.8), *rest["R"]).key("hand.R", F(35.3), 0.32, 1.08).key("hand.R", F(37.9), 0.32, 1.08).key("hand.R", F(38.5), *rest["R"])
c.key("fingers.R", F(34.8), -80).key("fingers.R", F(35.3), 90).key("fingers.R", F(37.9), 90).key("fingers.R", F(38.5), -80)
c.key("head", 1, 0).key("head", F(9.0), -3).key("head", F(10.2), 4).key("head", F(13.0), -4).key("head", F(16.0), 3).key("head", F(19.7), 0).key("head", F(23), -3).key("head", F(27), 3)
c.key("head", F(31.3), -4).key("head", F(35.3), 2).key("head", F(39.0), -6).key("head", F(41.3), -6)
c.bake(1, NFR)
for sd in "LR": rig2.set_hand(gpa, sd, "open", 1)
rig2.set_hand(gpa, "L", "point", F(13.0)); rig2.set_hand(gpa, "L", "open", F(18.9)); rig2.set_hand(gpa, "L", "point", F(31.2)); rig2.set_hand(gpa, "L", "open", F(34.5))
rig2.set_hand(gpa, "R", "grip", F(19.6)); rig2.set_hand(gpa, "R", "open", F(27.3)); rig2.set_hand(gpa, "R", "palm", F(35.0)); rig2.set_hand(gpa, "R", "open", F(38.2))

# ---------------- props changing hands
holders(can, [(son, "R", 90, 0, 0.32), (mom, "L", 90, 0.33, 10.95), (son, "R", 90, 38.75, 41.5)])
holders(glass, [(mom, "R", 90, 0, 11.8)])
org.scale = (1, 1, 0.94); holders(org, [(gpa, "R", 0, 19.6, 27.4)]); pop(org, 19.6, 27.2)
holders(ph_g, [(gpa, "R", 0, 34.9, 38.4)]); pop(ph_g, 34.9, 38.2)
holders(ph_m, [(mom, "R", 0, 37.4, 41.5)]); pop(ph_m, 37.5)

# ---------------- sugar cubes: ten by the can, eight by the glass, a little pile by each breakfast item
def tower(xy, n, t0, dt):
    for i in range(n):
        cu = sugar_cube(f"cube_{xy[0]:.2f}_{i}", (xy[0], xy[1], TOP + 0.035 + 0.004 + i * 0.071)); z0 = cu.location.z; t = t0 + i * dt
        cu.rotation_euler.z = R((i * 37) % 23 - 11)
        key(cu, "location", Vector((xy[0], xy[1], z0 + 0.35)), max(1, F(t) - 1)); key(cu, "location", Vector((xy[0], xy[1], z0)), F(t) + 3)
        pop(cu, t, None, 0.12)
tower(TOW10, 10, 13.55, 0.16)
tower(TOW8, 8, 16.6, 0.17)
for t, item in ((31.35, "smoothie"), (32.05, "granola"), (33.35, "yogurt")):
    x, y = ITEMS[item][0] + 0.13, ITEMS[item][1]
    for i, (dx, dy, dz) in enumerate(((0, 0, 0), (0.072, 0, 0), (0.036, 0, 0.071))):
        cu = sugar_cube(f"pile_{item}_{i}", (x + dx, y + dy, TOP + 0.039 + dz)); pop(cu, t + i * 0.08, None, 0.14)

# ---------------- camera: one continuous move
CK = [(0.0, (-2.9, -4.6, 1.85), (-2.2, -1.9, 1.55)), (4.0, (-2.6, -4.9, 1.9), (-2.0, -1.9, 1.55)), (7.8, (-2.4, -4.8, 1.9), (-1.9, -1.9, 1.55)),
      (8.7, (1.3, -4.5, 1.85), (1.75, -1.1, 1.65)), (12.6, (1.2, -4.6, 1.85), (1.7, -1.1, 1.65)),
      (13.8, (-0.4, -3.6, 1.6), (-1.05, -1.86, 1.25)), (18.0, (-0.35, -3.5, 1.6), (-1.0, -1.86, 1.28)),
      (19.0, (-1.4, -4.4, 1.8), (-1.5, -2.2, 1.8)), (21.0, (1.2, -4.6, 1.85), (1.75, -1.1, 1.7)), (26.6, (1.5, -4.3, 1.8), (1.8, -1.1, 1.7)),
      (28.0, (-0.7, -3.7, 1.6), (-0.3, -1.72, 1.3)), (31.0, (0.4, -4.1, 1.7), (0.5, -1.5, 1.35)), (33.6, (0.5, -4.2, 1.7), (0.6, -1.4, 1.4)),
      (34.4, (0.6, -4.6, 1.85), (1.4, -1.1, 1.6)), (34.95, (1.2, -3.2, 1.8), (1.0, -1.4, 1.5)),
      (38.6, (-1.5, -4.7, 1.85), (-1.4, -1.8, 1.5)), (41.3, (-1.8, -4.4, 1.8), (-1.7, -1.8, 1.55))]
for t, cp, tp in CK:
    key(cam, "location", Vector(cp), F(t)); key(tgt, "location", Vector(tp), F(t))
for f0 in (F(18.1),):
    base = cam.location.copy()
    for i in range(12):
        f = f0 + i; S.frame_set(f); bpy.context.view_layer.update(); p = cam.location.copy(); a_ = 0.03 * (1 - i / 12)
        key(cam, "location", p + Vector((math.sin(i * 2.7) * a_, 0, math.cos(i * 3.3) * a_)), f)

# ---------------- POV: Grandpa's own eyes, his hand holding the phone up at the juice (35.3 - 37.6)
T0, T1 = 35.3, 37.6
EYE = Vector((1.85, -1.18, 1.9)); LOOK = (Vector((-1.0, -1.86, 1.05)) - EYE).normalized()
def pov_key(t, off=Vector((0, 0, 0)), look_off=Vector((0, 0, 0))):
    key(cam, "location", EYE + off, F(t)); key(tgt, "location", EYE + off + (LOOK + look_off).normalized() * 0.30, F(t))
pov_key(T0); 
import random; rnd = random.Random(7)
t = T0 + 0.13
while t < T1:
    pov_key(t, Vector((rnd.uniform(-1, 1) * 0.006, 0, rnd.uniform(-1, 1) * 0.005)), Vector((rnd.uniform(-1, 1) * 0.01, 0, rnd.uniform(-1, 1) * 0.008))); t += 0.13
pov_key(T1, Vector((0.004, 0, -0.01)))
# hide Grandpa while we are inside his head
def tree(o):
    yield o
    for c in o.children: yield from tree(c)
gobjs = set(tree(gpa["arm"])) | set(tree(ph_g)) | {o for o in bpy.data.objects if o.name.startswith("grandpa")}
def vis(o, on_frames):
    for f, h in on_frames:
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
for o in gobjs: vis(o, [(1, False), (F(T0), True), (F(T1), False)])
# the POV hand: forearm from the bottom right, open palm behind the phone, phone screen to the eye
pv, scr_pov = phone("phone_pov")
pv.parent = cam; pv.location = (0.0, -0.035, -0.30); pv.rotation_euler = (R(-90 + 6), R(-4), 0)
ART = os.path.join(ARTD, "grandpa")
def card(name, img, w, h, u0, u1, v0, v1, loc, rot):
    me = bpy.data.meshes.new(name); me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)]); me.update()
    uv = me.uv_layers.new(); [setattr(uv.data[i], "uv", c) for i, c in enumerate([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])]
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.parent = cam; o.location = loc; o.rotation_euler = (0, 0, R(rot))
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(ART, img)); tx.extension = "CLIP"
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], b.inputs["Alpha"]); b.inputs["Roughness"].default_value = 0.8; nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.55
    o.data.materials.append(m); o.visible_shadow = False; return o
hand_pov = card("pov_hand", "hands.png", 0.34, 0.34, 1 / 6, 0.0, 1.0, 0.0, (0.004, -0.02, -0.312), 4)     # open hand turned upside down: fingers up behind the phone
arm_pov = card("pov_arm", "arm.png", 0.085, 0.36, 0, 1, 0.0, 0.62, (0.075, -0.26, -0.318), 24)
for o in (pv, scr_pov, hand_pov, arm_pov): vis(o, [(1, True), (F(T0), False), (F(T1), True)])
SCREENS = [scr_g, scr_pov]
