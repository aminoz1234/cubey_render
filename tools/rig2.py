"""Cut-out character rig for Blender, done the way Spine/Moho/Toon Boom rigs work:
armature with real bones, limbs = one straight drawing on a mesh skinned to two bones (smooth bend at the joint),
IK hand/foot targets with poles, rigid parts on single bones, a hand-drawing library swapped by UV offset,
props held with a Child Of constraint on the hand bone. Everything lives in the character's card plane (x right, z up)."""
import bpy, math, json, os
from mathutils import Vector, Matrix

U = 1000.0
SKEL = {
    "mom": dict(hip=0.62, sh=1.1, neck=1.15, shW=0.165, hipW=0.07, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.0, ank=0.05, headR=0.36),
    "son": dict(hip=0.5, sh=0.9, neck=0.95, shW=0.14, hipW=0.07, up=0.21, fo=0.195, th=0.25, sn=0.235, hand=0.9, ank=0.045, headR=0.34),
    "nora": dict(hip=0.62, sh=1.1, neck=1.15, shW=0.16, hipW=0.07, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.0, ank=0.05, headR=0.36),
    "jess": dict(hip=0.62, sh=1.1, neck=1.15, shW=0.165, hipW=0.07, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.0, ank=0.05, headR=0.36),
    "ray": dict(hip=0.62, sh=1.12, neck=1.17, shW=0.21, hipW=0.09, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.08, ank=0.05, headR=0.39),
    "dale": dict(hip=0.62, sh=1.12, neck=1.17, shW=0.21, hipW=0.09, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.08, ank=0.05, headR=0.39),
    "marcus": dict(hip=0.66, sh=1.2, neck=1.25, shW=0.205, hipW=0.075, up=0.27, fo=0.25, th=0.33, sn=0.31, hand=1.08, ank=0.05, headR=0.34),
    "grandpa": dict(hip=0.62, sh=1.1, neck=1.15, shW=0.17, hipW=0.075, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.0, ank=0.05, headR=0.35),
}
HANDS = ["open", "fist", "point", "gripBack", "gripFront", "wave"]
EMPTY_CELL = 7          # past the end of the atlas = transparent (CLIP extension)

def all_fcurves(action):
    """every F-curve of an action, Blender 4 (action.fcurves) and 5 (layers > strips > channelbags)"""
    if action is None: return []
    if hasattr(action, "fcurves"): return list(action.fcurves)
    out = []
    for ly in getattr(action, "layers", []):
        for st in ly.strips:
            for cb in getattr(st, "channelbags", []): out += list(cb.fcurves)
    return out

def _mat(name, img_path, seq=False, frames=150, atlas=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); img = bpy.data.images.load(img_path); tex.image = img; tex.interpolation = "Cubic"; tex.extension = "CLIP"
    if seq:
        img.source = "SEQUENCE"; tex.image_user.frame_duration = frames; tex.image_user.frame_start = 1; tex.image_user.use_auto_refresh = True
    if atlas:
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "cell"
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.22
    b.inputs["Roughness"].default_value = 0.85; b.inputs["Specular IOR Level"].default_value = 0.2
    return m

def _plane(name, x0, z0, x1, z1, y, mat, nseg=1, u0=0.0, u1=1.0, flip=False):
    """Quad strip from (x0,z0) bottom-left to (x1,z1) top-right at depth y, subdivided nseg times along z."""
    vs, fs, uvs = [], [], []
    for i in range(nseg + 1):
        t = i / nseg; z = z0 + (z1 - z0) * t
        vs += [(x0, y, z), (x1, y, z)]
    for i in range(nseg): a = 2 * i; fs.append((a, a + 1, a + 3, a + 2))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    uv = me.uv_layers.new()
    for p in me.polygons:
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; t = (v.z - z0) / (z1 - z0); s = 0 if v.x < (x0 + x1) / 2 else 1
            if flip: s = 1 - s
            uv.data[li].uv = (u0 + (u1 - u0) * s, t)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(mat)
    return o

def _pitch_axis(arm, bname):
    """Local axis that swings this bone toward/away from the camera (world X in rig space)."""
    ml = arm.data.bones[bname].matrix_local.to_3x3()
    j = max(range(3), key=lambda k: abs(ml.col[k].x)); return j, (1 if ml.col[j].x > 0 else -1)

def _bone_axis(arm, bname):
    """Which local rotation axis of this bone turns it inside the card plane (world Y), and its sign."""
    ml = arm.data.bones[bname].matrix_local.to_3x3()
    i = max(range(3), key=lambda k: abs(ml.col[k].y)); return i, (1 if ml.col[i].y > 0 else -1)

HOSE = True        # rubber-hose bendy limbs (Nov 28); False = the old hinge limbs
_DBG = {}
TUBE = True        # limb cards turn around their own length to face the camera (no edge-on slivers)
LIFE = True        # drag / overshoot / arcs / anticipation / breathing on baked motion

def build(who, loc, art_dir, head_dir, head_meta, cam, scale=1.3, frames=150):
    S = SKEL[who]; art = json.load(open(f"{art_dir}/art.json"))[who]; D = f"{art_dir}/{who}"; sc = bpy.context.scene
    ank = S["ank"] * S["hand"] if who == "son" else S["ank"]
    hipZ = ank + S["th"] + S["sn"]; shZ = hipZ + (S["sh"] - S["hip"]); neckZ = hipZ + (S["neck"] - S["hip"])
    elZ, wrZ = shZ - 0.02 - S["up"], shZ - 0.02 - S["up"] - S["fo"]; knZ = hipZ - S["th"]
    # ---------------- armature
    ad = bpy.data.armatures.new(f"{who}_rig"); arm = bpy.data.objects.new(f"{who}_rig", ad); sc.collection.objects.link(arm)
    arm.location = loc; arm.scale = (scale,) * 3; arm.rotation_mode = "XYZ"; ad.display_type = "STICK"
    lt = arm.constraints.new("LOCKED_TRACK"); lt.target = cam; lt.track_axis = "TRACK_NEGATIVE_Y"; lt.lock_axis = "LOCK_Z"
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT"); eb = ad.edit_bones
    def B(n, h, t, parent=None, conn=False, deform=True):
        b = eb.new(n); b.head = (h[0], 0, h[1]); b.tail = (t[0], 0, t[1]); b.roll = 0
        if parent: b.parent = eb[parent]; b.use_connect = conn
        b.use_deform = deform; return b
    B("root", (0, 0), (0, 0.15), deform=False)
    B("hips", (0, hipZ), (0, hipZ + 0.08), "root")
    B("spine", (0, hipZ), (0, shZ), "hips")
    B("head", (0, neckZ), (0, neckZ + 0.3), "spine")
    for sd, s in (("L", -1), ("R", 1)):
        x = s * S["shW"]; B(f"upper.{sd}", (x, shZ - 0.02), (x, elZ), "spine"); B(f"fore.{sd}", (x, elZ), (x, wrZ), f"upper.{sd}", True)
        B(f"hand.{sd}", (x, wrZ), (x, wrZ - 0.1), f"fore.{sd}", True)
        hx = s * S["hipW"]; B(f"thigh.{sd}", (hx, hipZ), (hx, knZ), "hips"); B(f"shin.{sd}", (hx, knZ), (hx, ank), f"thigh.{sd}", True)
        B(f"foot.{sd}", (hx, ank), (hx + s * 0.1, ank), f"shin.{sd}", True)
    if HOSE:
        for sd in "LR":
            for n_ in ("upper", "fore", "thigh", "shin"):
                b = eb[f"{n_}.{sd}"]; b.bbone_segments = 16; b.bbone_easein = 0.45; b.bbone_easeout = 0.45
                b.bbone_handle_type_start = "AUTO"; b.bbone_handle_type_end = "AUTO"
    bpy.ops.object.mode_set(mode="OBJECT")
    for sd in "LR": ad.bones[f"foot.{sd}"].use_inherit_rotation = False
    for pb in arm.pose.bones: pb.rotation_mode = "XYZ"
    T = {}
    # ---------------- meshes
    parts = {}
    def skin(o, groups):
        for g in groups: o.vertex_groups.new(name=g)
        md = o.modifiers.new("rig", "ARMATURE"); md.object = arm; o.parent = arm
    def rigid(o, bone):
        skin(o, [bone]); o.vertex_groups[bone].add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    def px(meta, key, ox, oz, flipx=False):   # art pixel -> plane coords given an anchor pixel placed at (ox, oz)
        ax, ay = meta[key]; return lambda X, Y: (ox + ((ax - X) if flipx else (X - ax)) / U, oz + (ay - Y) / U)
    # torso
    tm = art["torso"]; f = px(tm, "hip", 0, hipZ); x0, z0 = f(0, tm["H"]); x1, z1 = f(tm["W"], 0)
    o = _plane(f"{who}_torso", x0, z0, x1, z1, 0.0, _mat(f"{who}_torso_m", f"{D}/torso.png")); rigid(o, "spine"); parts["torso"] = o
    # head (image sequence, pivot at the neck)
    hm = head_meta; R = S["headR"]; f = lambda X, Y: ((X - hm["pivot"][0]) / U, neckZ + (hm["pivot"][1] - Y) / U)
    x0, z0 = f(0, hm["H"]); x1, z1 = f(hm["W"], 0)
    o = _plane(f"{who}_head", x0, z0, x1, z1, -0.004, _mat(f"{who}_head_m", f"{head_dir}/0001.webp", seq=True, frames=frames)); rigid(o, "head"); parts["head"] = o
    for sd, s in (("L", -1), ("R", 1)):
        fl = s < 0
        # arm: one drawing, skinned to upper + fore with a soft blend at the elbow
        am = art["arm"]; f = px(am, "shoulder", s * S["shW"], shZ - 0.02, fl); x0, z0 = f(0 if not fl else am["W"], am["H"]); x1, z1 = f(am["W"] if not fl else 0, 0)
        o = _plane(f"{who}_arm.{sd}", min(x0, x1), z0, max(x0, x1), z1, -0.01, _mat(f"{who}_arm_m.{sd}", f"{D}/arm.png"), nseg=40); skin(o, [f"upper.{sd}", f"fore.{sd}"])
        for v in o.data.vertices:
            bw = 0.11 if HOSE else 0.09
            w = max(0.0, min(1.0, (elZ + bw / 2 - v.co.z) / bw)); w = w * w * (3 - 2 * w)
            o.vertex_groups[f"fore.{sd}"].add([v.index], w, "REPLACE"); o.vertex_groups[f"upper.{sd}"].add([v.index], 1 - w, "REPLACE")
            v.co.y -= 0.004 * w                                   # forearm sits a hair in front of the upper arm: no coplanar overlap when folded
        parts[f"arm.{sd}"] = o
        lm = art["leg"]; f = px(lm, "hip", s * S["hipW"], hipZ, fl); x0, z0 = f(0, lm["H"]); x1, z1 = f(lm["W"], 0)
        o = _plane(f"{who}_leg.{sd}", min(x0, x1), z0, max(x0, x1), z1, 0.02, _mat(f"{who}_leg_m.{sd}", f"{D}/leg.png"), nseg=40); skin(o, [f"thigh.{sd}", f"shin.{sd}"])
        for v in o.data.vertices:
            bw = 0.1 if HOSE else 0.08
            w = max(0.0, min(1.0, (knZ + bw / 2 - v.co.z) / bw)); w = w * w * (3 - 2 * w)
            o.vertex_groups[f"shin.{sd}"].add([v.index], w, "REPLACE"); o.vertex_groups[f"thigh.{sd}"].add([v.index], 1 - w, "REPLACE")
            v.co.y -= 0.004 * w
        parts[f"leg.{sd}"] = o
        fm = art["foot"]; f = px(fm, "ankle", s * S["hipW"], ank, fl); x0, z0 = f(0, fm["H"]); x1, z1 = f(fm["W"], 0)
        o = _plane(f"{who}_foot.{sd}", min(x0, x1), z0, max(x0, x1), z1, 0.012, _mat(f"{who}_foot_m.{sd}", f"{D}/foot.png"), flip=fl); rigid(o, f"foot.{sd}"); parts[f"foot.{sd}"] = o
        # hands: palm layer behind the prop, finger layer in front; both read one cell of the hand atlas
        hm2 = art["hands"]; cw = hm2["cell"]; n = len(HANDS); wx, wy = hm2["wrist"]
        x0, x1 = s * S["shW"] - (wx / U) * (-1 if fl else 1), s * S["shW"] + ((cw - wx) / U) * (-1 if fl else 1); z1, z0 = wrZ + wy / U, wrZ - (cw - wy) / U
        for lay, y in (("back", -0.0115), ("front", -0.024)):
            m = _mat(f"{who}_hand{lay}_m.{sd}", f"{D}/hands.png", atlas=True)
            o = _plane(f"{who}_hand{lay}.{sd}", min(x0, x1), z0, max(x0, x1), z1, y, m, u0=0, u1=1 / n, flip=fl); rigid(o, f"hand.{sd}"); parts[f"hand{lay}.{sd}"] = o
    # grip point (where a held prop's centre goes) in rest pose, per side
    gx, gy = art["hands"]["grip"]; wx, wy = art["hands"]["wrist"]
    grip = {sd: Vector((s * S["shW"] + (gx - wx) / U * s, -0.018, wrZ - (gy - wy) / U)) for sd, s in (("L", -1), ("R", 1))}
    return dict(arm=arm, T=T, parts=parts, grip=grip, S=S, z=dict(hip=hipZ, sh=shZ, neck=neckZ, el=elZ, wr=wrZ, kn=knZ, ank=ank), n=len(HANDS))

def set_hand(rig, sd, kind, frame):
    """Swap the hand drawing (constant keys). grip = palm behind + fingers in front."""
    n = rig["n"]; P = rig["parts"]
    back = HANDS.index("gripBack") if kind == "grip" else HANDS.index("open") if kind == "palm" else HANDS.index(kind)
    front = HANDS.index("gripFront") if kind == "grip" else EMPTY_CELL
    for lay, cell in (("back", back), ("front", front)):
        mp = P[f"hand{lay}.{sd}"].data.materials[0].node_tree.nodes["cell"]
        mp.inputs["Location"].default_value[0] = cell / n
        mp.inputs["Location"].keyframe_insert("default_value", index=0, frame=frame)
        fc = P[f"hand{lay}.{sd}"].data.materials[0].node_tree.animation_data.action
        for c in all_fcurves(fc):
            for k in c.keyframe_points: k.interpolation = "CONSTANT"

def rotate_bone(rig, bname, deg, frame):   # (kept for one-off keys)
    arm = rig["arm"]; i, sgn = _bone_axis(arm, bname); pb = arm.pose.bones[bname]
    r = [0.0, 0.0, 0.0]; r[i] = math.radians(deg) * sgn; pb.rotation_euler = r; pb.keyframe_insert("rotation_euler", frame=frame)

def hold(rig, sd, obj, axis_deg=90):
    """Child Of the hand bone: obj sits at the grip point, its long axis along the hand's x (across the palm)."""
    arm = rig["arm"]; bpy.context.view_layer.update()
    obj.parent = None; obj.rotation_mode = "XYZ"; obj.scale = (1, 0.08, 1)          # props held in a hand are squashed in depth so palm/fingers layers wrap them
    gw = arm.matrix_world @ rig["grip"][sd]
    obj.location = gw; obj.rotation_euler = (0, math.radians(axis_deg), 0); obj.rotation_euler.rotate(arm.matrix_world.to_euler())
    c = obj.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = f"hand.{sd}"
    bpy.context.view_layer.update()
    pb = arm.pose.bones[f"hand.{sd}"]; c.inverse_matrix = (arm.matrix_world @ pb.matrix).inverted()
    return c


# ---------------------------------------------------------------- animation: eased keys, analytic 2-bone IK, baked to FK
def _ease(u): return u * u * u * (u * (u * 6 - 15) + 10)          # smootherstep: ease out of and into every key
class Track:
    def __init__(self): self.k = []
    def add(self, f, *v): self.k.append((f, v)); self.k.sort(key=lambda t: t[0]); return self
    def at(self, f):
        k = self.k
        if f <= k[0][0]: return k[0][1]
        if f >= k[-1][0]: return k[-1][1]
        for (f0, v0), (f1, v1) in zip(k, k[1:]):
            if f0 <= f <= f1:
                u = _ease((f - f0) / (f1 - f0)) if f1 > f0 else 1; return tuple(a + (b - a) * u for a, b in zip(v0, v1))

def _ccw_sign(arm, bname):
    """+1 if rotate_bone(+deg) turns this bone counter-clockwise as seen from the camera (x right, z up)."""
    pb = arm.pose.bones[bname]; i, sgn = _bone_axis(arm, bname); old = tuple(pb.rotation_euler)
    r = [0.0, 0.0, 0.0]; r[i] = 0.3 * sgn; pb.rotation_euler = r; bpy.context.view_layer.update()
    d1 = (pb.tail - pb.head); pb.rotation_euler = old; bpy.context.view_layer.update(); d0 = (arm.data.bones[bname].tail_local - arm.data.bones[bname].head_local)
    cross = d0.x * d1.z - d0.z * d1.x; return 1 if cross > 0 else -1

def _spring(xs, hz=3.0, zeta=0.5, fps=30.0):
    """critically-under-damped follower: the part lags the driver (drag) and overshoots, then settles (follow-through)"""
    w = 2 * math.pi * hz; dt = 1.0 / fps; x = xs[0]; v = 0.0; out = []
    for tgt in xs:
        for _ in range(4):        # substeps for stability
            a = w * w * (tgt - x) - 2 * zeta * w * v; v += a * dt / 4; x += v * dt / 4
        out.append(x)
    return out
def _life(anim, f0, f1, S, z):
    """Animation principles applied automatically on top of the keyed poses (Disney's 12, as cut-out riggers apply them):
    anticipation (a small wind-up opposite each move), arcs (moves bow outward instead of travelling in straight lines),
    drag + follow-through (hands lag the arm and overshoot, wrists flop, heads settle after the body), idle breathing."""
    fr = list(range(f0, f1 + 1)); OV = {}
    for sd, s_ in (("L", -1), ("R", 1)):
        n = f"hand.{sd}"
        if n not in anim.t: continue
        P = [anim.tr(n).at(f) for f in fr]; L_ = len(P); look = 4
        X, Z = [], []
        for i in range(L_):
            p = P[i]; q = P[min(L_ - 1, i + look)]; d = (q[0] - p[0], q[1] - p[1])
            ax, az = p[0] - 0.2 * d[0], p[1] - 0.2 * d[1]                       # anticipation: lean back before going
            pv = P[max(0, i - 1)]; vx, vz = p[0] - pv[0], p[1] - pv[1]; sp = math.hypot(vx, vz)
            if sp > 1e-5:                                                         # arc: bow the path outward / upward
                nx, nz = -vz / sp, vx / sp
                if nx * s_ + nz < 0: nx, nz = -nx, -nz
                ax += nx * min(0.015, sp * 0.6); az += nz * min(0.015, sp * 0.6)
            X.append(ax); Z.append(az)
        X = _spring(X, 4.5, 0.72); Z = _spring(Z, 4.5, 0.72)
        OV[n] = {f: (X[i], Z[i]) for i, f in enumerate(fr)}
        fn = f"fingers.{sd}"
        if fn in anim.t:
            A = [anim.tr(fn).at(f)[0] for f in fr]
            for i in range(1, len(A)): A[i] = A[i - 1] + ((A[i] - A[i - 1] + 180) % 360 - 180)
            # the hand trails the arm: add a little of the arm's own motion, delayed, then spring it
            A = _spring([a - 0.25 * ((X[i] - X[max(0, i - 2)]) * 400 * s_) for i, a in enumerate(A)], 4.0, 0.7)
            OV[fn] = {f: (A[i],) for i, f in enumerate(fr)}
    for sd in "LR":
        n = f"hand3.{sd}"
        if n in anim.t:
            P3 = [anim.tr(n).at(f) for f in fr]
            cols = [_spring([p[k] for p in P3], 4.5, 0.72) for k in range(3)]
            OV[n] = {f: (cols[0][i], cols[1][i], cols[2][i]) for i, f in enumerate(fr)}
    hb = [anim.tr("hips").at(f)[0] if "hips" in anim.t else 0.0 for f in fr]
    sp = [(anim.tr("spine").at(f)[0] if "spine" in anim.t else 0.0) + 1.1 * math.sin(2 * math.pi * 0.27 * f / 30.0) for f in fr]   # breathing
    hd = [(anim.tr("head").at(f)[0] if "head" in anim.t else 0.0) for f in fr]
    hd = _spring([h - 0.4 * s for h, s in zip(hd, sp)], 3.0, 0.6)                # head settles after the body
    OV["spine"] = {f: (sp[i],) for i, f in enumerate(fr)}; OV["head"] = {f: (hd[i] + 0.5 * sp[i],) for i, f in enumerate(fr)}
    return OV

def sub3(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def norm(v):
    l = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0; return (v[0] / l, v[1] / l, v[2] / l)
def rz(v, deg):      # turn inside the card plane (CCW seen from the camera)
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg)); return (v[0] * c - v[2] * s_, v[1], v[0] * s_ + v[2] * c)
def rx(v, deg):      # tip toward the camera
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg)); return (v[0], v[1] * c - v[2] * s_, v[1] * s_ + v[2] * c)
def tp(v):           # direction -> (in-plane angle from straight down, pitch toward camera), the bone's Euler (X then Z)
    v = norm(v); return math.degrees(math.atan2(v[0], -v[2])), math.degrees(math.asin(max(-1.0, min(1.0, v[1]))))
def ik3(a, t, l1, l2, pole, mem=None, key=None):
    """two-bone IK in 3D: the joint bends toward 'pole' (a direction). With mem/key the bend direction is kept
    continuous: when the pole lines up with the limb (its useful part gets small) the joint keeps last frame's bend
    instead of flipping to the other side."""
    d = sub3(t, a); D = math.sqrt(sum(c * c for c in d)); D = max(min(D, (l1 + l2) * 0.999), abs(l1 - l2) + 1e-4); n = norm(d)
    pd = sum(pole[i] * n[i] for i in range(3)); pr = tuple(pole[i] - pd * n[i] for i in range(3))
    L = math.sqrt(sum(c * c for c in pr)) / (math.sqrt(sum(c * c for c in pole)) or 1.0)
    if mem is not None and key in mem:
        q = mem[key]; qd = sum(q[i] * n[i] for i in range(3)); q = norm(tuple(q[i] - qd * n[i] for i in range(3)))
        w = max(0.0, min(1.0, (L - 0.15) / 0.35))           # strong pole -> follow it; weak pole -> keep the old bend
        if L > 1e-6:
            pn = norm(pr); pr = tuple(pn[i] * w + q[i] * (1 - w) for i in range(3))
        else: pr = q
    p = norm(pr)
    if abs(sum(c * c for c in p) - 1) > 0.5: p = (0.0, 0.0, 1.0)
    if mem is not None: mem[key] = p
    ca = (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D); al = math.acos(max(-1.0, min(1.0, ca)))
    E = tuple(a[i] + l1 * (math.cos(al) * n[i] + math.sin(al) * p[i]) for i in range(3)); W = tuple(a[i] + D * n[i] for i in range(3))
    return E, W

class Anim:
    """Keys per control; bake() solves IK every frame and writes bone rotations.
    hand/foot targets: ('hand.R', f, x, z). angles in degrees CCW: spine, head, hand.L/R (relative to forearm). hips: bounce (up)."""
    def __init__(self, rig, fwd=None):
        self.r = rig; self.t = {}
        self.fwd = fwd or (lambda f: (0.0, 1.0))   # body forward in card coords; (0, 1) = facing the camera
    def tr(self, n): return self.t.setdefault(n, Track())
    def key(self, n, f, *v): self.tr(n).add(f, *v); return self
    def bake(self, f0, f1, bend=None):
        r = self.r; arm = r["arm"]; S = r["S"]; z = r["z"]; bend = bend or {}
        sgn = {b.name: _ccw_sign(arm, b.name) for b in arm.data.bones}
        # angle keys take the short way round (a -90 -> 200 key is a 70 degree turn, not 290)
        for n, t in self.t.items():
            if n.startswith("fingers") or n.startswith("handrot") or n in ("spine", "head"):
                for i in range(1, len(t.k)):
                    prev = t.k[i - 1][1][0]; v = t.k[i][1][0]
                    v = prev + ((v - prev + 180) % 360 - 180); t.k[i] = (t.k[i][0], (v,) + tuple(t.k[i][1][1:]))
        last = {}
        pax = {b.name: _pitch_axis(arm, b.name) for b in arm.data.bones}
        def rot(b, deg, f, pitch=0.0):
            if b in last: deg = last[b] + ((deg - last[b] + 180) % 360 - 180)      # never jump a full turn between frames
            last[b] = deg
            pb = arm.pose.bones[b]; i, sg = _bone_axis(arm, b); v = [0.0, 0.0, 0.0]; v[i] = math.radians(deg) * sg * sgn[b] * (1 if sg > 0 else -1)
            if pitch: j, sj = pax[b]; v[j] = -math.radians(pitch) * sj         # + = toward the camera
            pb.rotation_euler = v; pb.keyframe_insert("rotation_euler", frame=f)
        def ang(v): return math.degrees(math.atan2(v[1], v[0]))
        # ---- tube orientation: every limb card turns around its own length so its face points at the camera as much as it can
        #      (a flat cut-out seen edge-on becomes a sliver; this keeps forearms/shins readable at any pitch, any camera)
        from mathutils import Matrix, Vector as _V, Quaternion as _Q
        C_ = _V((0.0, -1.0, 0.0))                     # armature -Y looks at the camera (Locked Track) ...
        CAMD = {}                                     # ... but the camera also sits higher/lower: use the real direction per frame
        if TUBE:
            sc_ = bpy.context.scene; cam_ = sc_.camera; chest = _V((0.0, 0.0, z["sh"]))
            for f_ in range(f0, f1 + 1):
                sc_.frame_set(f_); mw = arm.matrix_world
                CAMD[f_] = (mw.inverted().to_3x3() @ (cam_.matrix_world.translation - mw @ chest)).normalized()
        R0 = {b.name: b.matrix_local.to_3x3() for b in arm.data.bones}
        def nrest(bn):                                # rest-pose card normal expressed in the bone's local frame
            return (R0[bn].inverted() @ C_).normalized()
        NR = {bn: nrest(bn) for bn in R0}
        PR = {}                                       # posed armature-space rotation of each bone this frame
        def card2arm(v): return _V((v[0], -v[1], v[2]))
        def orient(bn, d_card, f):
            Cf = CAMD.get(f, C_); D = card2arm(d_card).normalized(); N = Cf - D * Cf.dot(D)
            if N.length < 0.2:                       # pointing (almost) straight at the camera: keep last frame's face
                Np = last.get("N" + bn, Cf); N2 = Np - D * Np.dot(D); N = N2 if N2.length > 1e-4 else N
            N.normalize(); last["N" + bn] = N.copy()
            Yr = (R0[bn] @ _V((0, 1, 0))); Nr = (R0[bn] @ NR[bn]).normalized()
            A = Matrix((Yr, Nr, Yr.cross(Nr))).transposed(); B = Matrix((D, N, D.cross(N))).transposed()
            Rarm = B @ A.inverted()                   # rest -> posed, armature space
            P = Rarm @ R0[bn]; PR[bn] = P
            par = arm.data.bones[bn].parent
            if par is not None:
                pP = PR.get(par.name) or (R0[par.name] @ arm.pose.bones[par.name].rotation_euler.to_matrix())
                basis = (R0[par.name].inverted() @ R0[bn]).inverted() @ pP.inverted() @ P
            else: basis = R0[bn].inverted() @ P
            q = basis.to_quaternion()
            qp = last.get("q" + bn)
            if qp is not None and qp.dot(q) < 0: q.negate()
            last["q" + bn] = q.copy()
            pb = arm.pose.bones[bn]; pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f)
        def ik2(a, t, l1, l2, side):
            dx, dz = t[0] - a[0], t[1] - a[1]; D = max(min(math.hypot(dx, dz), (l1 + l2) * 0.999), abs(l1 - l2) + 1e-4)
            base = math.atan2(dz, dx); c = (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D); off = math.acos(max(-1, min(1, c)))
            a1 = base + side * off; e = (a[0] + l1 * math.cos(a1), a[1] + l1 * math.sin(a1)); return e, (a[0] + D * math.cos(base), a[1] + D * math.sin(base))
        OV = {}
        if LIFE:
            OV = _life(self, f0, f1, S, z)
        def at(n, f):
            return OV[n][f] if n in OV else self.tr(n).at(f)
        for f in range(f0, f1 + 1):
            bo = self.tr("hips").at(f)[0] if "hips" in self.t else 0.0
            hb = arm.pose.bones["hips"]; hb.location = (0, bo, 0); hb.keyframe_insert("location", frame=f)
            sp = at("spine", f)[0] if "spine" in self.t or "spine" in OV else 0.0; rot("spine", sp, f); PR.clear(); PR["spine"] = R0["spine"] @ arm.pose.bones["spine"].rotation_euler.to_matrix(); PR["hips"] = R0["hips"]
            hd = at("head", f)[0] if "head" in self.t or "head" in OV else 0.0; rot("head", hd, f)
            hip = (0.0, z["hip"] + bo); spr = math.radians(sp)
            def spin(p): x, y = p[0] - hip[0], p[1] - hip[1]; return (hip[0] + x * math.cos(spr) - y * math.sin(spr), hip[1] + x * math.sin(spr) + y * math.cos(spr))
            for sd, s in (("L", -1), ("R", 1)):
                fwd = self.fwd(f)                                        # body forward in card coords (x, d=toward camera)
                side3 = (fwd[1], -fwd[0])                               # body 'screen-right' axis in card coords
                def body(p3):  # body space (side, forward, up) -> card space (x, depth toward camera, z)
                    return (p3[0] * side3[0] + p3[1] * fwd[0], p3[0] * side3[1] + p3[1] * fwd[1], p3[2])
                # ---- arm
                has2, has3 = f"hand.{sd}" in self.t, f"hand3.{sd}" in self.t
                if has2 or has3:
                    shx, shz = spin((s * S["shW"], z["sh"] - 0.02 + bo)); S3 = (shx, 0.0, shz)
                    # the shoulder where the spine bone REALLY puts it (spin() could disagree with the bone's sign convention)
                    Pr = PR["spine"] @ R0["spine"].inverted(); hd0 = _V((0.0, 0.0, z["hip"]))
                    sa = _V((0.0, 0.0, z["hip"] + bo)) + Pr @ (_V((s * S["shW"], 0.0, z["sh"] - 0.02)) - hd0); S3 = (sa.x, -sa.y, sa.z)
                    w3 = (at(f"w3.{sd}", f)[0] if (f"w3.{sd}" in self.t or f"w3.{sd}" in OV) else 1.0) if has3 else 0.0
                    T2 = at(f"hand.{sd}", f) if has2 else (s * 0.22, 0.6)
                    T = (T2[0], 0.0, T2[1]); side2 = bend.get(f"arm.{sd}", -s)
                    # 2D gestures: bend to a fixed SIDE of the shoulder->hand line (like a 2D rig's bend sign), so the
                    # elbow can never flip, whatever the line's direction. bend arm.L=-1 / arm.R=+1 = outward.
                    nT = norm(sub3(T, S3)); perp = (-nT[2], 0.0, nT[0])
                    dpr = perp[0] * s - perp[2]                      # which side of the line is "out and down" for this arm
                    sdv = last.get("side" + sd, 1.0 if dpr >= 0 else -1.0)
                    if dpr * sdv < -0.35: sdv = -sdv                 # hysteresis: only switch sides when clearly needed
                    last["side" + sd] = sdv
                    ph_t = 0.0 if sdv > 0 else 180.0; ph = last.get("phi" + sd, ph_t)
                    ph += max(-22.0, min(22.0, ph_t - ph)); last["phi" + sd] = ph   # a side switch swings the elbow round the back over a few frames
                    cph, sph = math.cos(math.radians(ph)), math.sin(math.radians(ph))
                    pole = (perp[0] * cph, -sph, perp[2] * cph)
                    if has3:
                        b3 = at(f"hand3.{sd}", f); c3 = body(b3); T3 = (c3[0], c3[1], c3[2])
                        T = tuple(T[i] + (T3[i] - T[i]) * w3 for i in range(3))
                        back = body((0.0, -1.0, 0.0)); pole = tuple(pole[i] * (1 - w3) + (s * 0.5, back[1] * 0.25, -1.0)[i] * w3 for i in range(3))
                    E, W = ik3(S3, T, S["up"], S["fo"], pole)
                    du = norm(sub3(E, S3)); dfo = norm(sub3(W, E))
                    tu, pu = tp(rz(du, -sp)); tf, pf = tp(rx(rz(rz(dfo, -sp), -tu), -pu))
                    if TUBE: orient(f"upper.{sd}", du, f); orient(f"fore.{sd}", dfo, f)
                    else: rot(f"upper.{sd}", tu, f, pu); rot(f"fore.{sd}", tf, f, pf)
                    a_fo = math.degrees(math.atan2(dfo[2], dfo[0])) + 90
                    flat = math.hypot(dfo[0], dfo[2])                    # how much of the forearm lies in the card plane
                    if f"fingers.{sd}" in self.t:
                        fg = at(f"fingers.{sd}", f)[0]
                        # a wrist bends, it doesn't spin: clamp what the camera sees. The clamp fades in with how flat the
                        # forearm lies in the card (a hard on/off threshold made the hand jump when the forearm crossed it).
                        pi_ = last.get("fgi" + sd, fg); fg = pi_ + max(-18.0, min(18.0, ((fg - pi_) + 180) % 360 - 180)); last["fgi" + sd] = fg
                        fg0 = fg; fa = a_fo - 90; rl = (fg - fa + 180) % 360 - 180
                        pr = last.get("vis" + sd, rl); rl = pr + ((rl - pr + 180) % 360 - 180); last["vis" + sd] = rl
                        cw = max(0.0, min(1.0, (flat - 0.35) / 0.35)); cw = cw * cw * (3 - 2 * cw)
                        fgc = fa + max(-62.0, min(62.0, rl)); fg = fg + cw * (((fgc - fg) + 180) % 360 - 180)
                        po = last.get("fgo" + sd, fg); lim = 18.0 + 40.0 * cw
                        fg = po + max(-lim, min(lim, ((fg - po) + 180) % 360 - 180)); last["fgo" + sd] = fg   # while the clamp fades, the hand can't whip round
                        hd = (math.cos(math.radians(fg)), 0.0, math.sin(math.radians(fg)))   # hands face the camera: no depth
                        th, ph = tp(rx(rz(rx(rz(rz(hd, -sp), -tu), -pu), -tf), -pf))
                        pr = last.get("rel" + sd, th); th = pr + ((th - pr + 180) % 360 - 180); last["rel" + sd] = th
                        lim = 180.0
                        if TUBE: orient(f"hand.{sd}", hd, f)
                        else: rot(f"hand.{sd}", max(-lim, min(lim, th)), f, ph)
                    elif f"handrot.{sd}" in self.t: rot(f"hand.{sd}", self.tr(f"handrot.{sd}").at(f)[0], f)
                # ---- leg
                has2, has3 = f"foot.{sd}" in self.t, f"foot3.{sd}" in self.t
                if has2 or has3:
                    H3 = (s * S["hipW"], 0.0, z["hip"] + bo)
                    if has3: c3 = body(at(f"foot3.{sd}", f)); T = (c3[0], c3[1], c3[2])
                    else: t2 = self.tr(f"foot.{sd}").at(f); T = (t2[0], 0.0, t2[1])
                    kf = body((0.0, 1.0, 0.0)); pole = (kf[0] + s * 0.25, kf[1], 0.0) if has3 else (s * (1 if bend.get(f"leg.{sd}", s) * s > 0 else -1), 0.0, 0.0)
                    E, W = ik3(H3, T, S["th"], S["sn"], pole)
                    dt = norm(sub3(E, H3)); ds = norm(sub3(W, E))
                    tt, pt = tp(dt); ts, ps = tp(rx(rz(ds, -tt), -pt))
                    if TUBE: orient(f"thigh.{sd}", dt, f); orient(f"shin.{sd}", ds, f)
                    else: rot(f"thigh.{sd}", tt, f, pt); rot(f"shin.{sd}", ts, f, ps)
