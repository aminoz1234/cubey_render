"""Cut-out character rig for Blender, done the way Spine/Moho/Toon Boom rigs work:
armature with real bones, limbs = one straight drawing on a mesh skinned to two bones (smooth bend at the joint),
IK hand/foot targets with poles, rigid parts on single bones, a hand-drawing library swapped by UV offset,
props held with a Child Of constraint on the hand bone. Everything lives in the character's card plane (x right, z up)."""
import bpy, math, json
from mathutils import Vector, Matrix

U = 1000.0
SKEL = {
    "mom": dict(hip=0.62, sh=1.1, neck=1.15, shW=0.165, hipW=0.07, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.0, ank=0.05, headR=0.36),
    "son": dict(hip=0.5, sh=0.9, neck=0.95, shW=0.14, hipW=0.07, up=0.21, fo=0.195, th=0.25, sn=0.235, hand=0.9, ank=0.045, headR=0.34),
    "grandpa": dict(hip=0.62, sh=1.1, neck=1.15, shW=0.17, hipW=0.075, up=0.25, fo=0.235, th=0.31, sn=0.29, hand=1.0, ank=0.05, headR=0.35),
}
HANDS = ["open", "fist", "point", "gripBack", "gripFront", "wave"]
EMPTY_CELL = 7          # past the end of the atlas = transparent (CLIP extension)

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

def _bone_axis(arm, bname):
    """Which local rotation axis of this bone turns it inside the card plane (world Y), and its sign."""
    ml = arm.data.bones[bname].matrix_local.to_3x3()
    i = max(range(3), key=lambda k: abs(ml.col[k].y)); return i, (1 if ml.col[i].y > 0 else -1)

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
            w = max(0.0, min(1.0, (elZ + 0.045 - v.co.z) / 0.09)); w = w * w * (3 - 2 * w)
            o.vertex_groups[f"fore.{sd}"].add([v.index], w, "REPLACE"); o.vertex_groups[f"upper.{sd}"].add([v.index], 1 - w, "REPLACE")
            v.co.y -= 0.004 * w                                   # forearm sits a hair in front of the upper arm: no coplanar overlap when folded
        parts[f"arm.{sd}"] = o
        lm = art["leg"]; f = px(lm, "hip", s * S["hipW"], hipZ, fl); x0, z0 = f(0, lm["H"]); x1, z1 = f(lm["W"], 0)
        o = _plane(f"{who}_leg.{sd}", min(x0, x1), z0, max(x0, x1), z1, 0.02, _mat(f"{who}_leg_m.{sd}", f"{D}/leg.png"), nseg=40); skin(o, [f"thigh.{sd}", f"shin.{sd}"])
        for v in o.data.vertices:
            w = max(0.0, min(1.0, (knZ + 0.04 - v.co.z) / 0.08)); w = w * w * (3 - 2 * w)
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
        for c in (fc.fcurves if hasattr(fc, "fcurves") else []):
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

class Anim:
    """Keys per control; bake() solves IK every frame and writes bone rotations.
    hand/foot targets: ('hand.R', f, x, z). angles in degrees CCW: spine, head, hand.L/R (relative to forearm). hips: bounce (up)."""
    def __init__(self, rig): self.r = rig; self.t = {}
    def tr(self, n): return self.t.setdefault(n, Track())
    def key(self, n, f, *v): self.tr(n).add(f, *v); return self
    def bake(self, f0, f1, bend=None):
        r = self.r; arm = r["arm"]; S = r["S"]; z = r["z"]; bend = bend or {}
        sgn = {b.name: _ccw_sign(arm, b.name) for b in arm.data.bones}
        def rot(b, deg, f):
            pb = arm.pose.bones[b]; i, sg = _bone_axis(arm, b); v = [0.0, 0.0, 0.0]; v[i] = math.radians(deg) * sg * sgn[b] * (1 if sg > 0 else -1)
            pb.rotation_euler = v; pb.keyframe_insert("rotation_euler", frame=f)
        def ang(v): return math.degrees(math.atan2(v[1], v[0]))
        def ik2(a, t, l1, l2, side):
            dx, dz = t[0] - a[0], t[1] - a[1]; D = max(min(math.hypot(dx, dz), (l1 + l2) * 0.999), abs(l1 - l2) + 1e-4)
            base = math.atan2(dz, dx); c = (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D); off = math.acos(max(-1, min(1, c)))
            a1 = base + side * off; e = (a[0] + l1 * math.cos(a1), a[1] + l1 * math.sin(a1)); return e, (a[0] + D * math.cos(base), a[1] + D * math.sin(base))
        for f in range(f0, f1 + 1):
            bo = self.tr("hips").at(f)[0] if "hips" in self.t else 0.0
            hb = arm.pose.bones["hips"]; hb.location = (0, bo, 0); hb.keyframe_insert("location", frame=f)
            sp = self.tr("spine").at(f)[0] if "spine" in self.t else 0.0; rot("spine", sp, f)
            hd = self.tr("head").at(f)[0] if "head" in self.t else 0.0; rot("head", hd, f)
            hip = (0.0, z["hip"] + bo); spr = math.radians(sp)
            def spin(p): x, y = p[0] - hip[0], p[1] - hip[1]; return (hip[0] + x * math.cos(spr) - y * math.sin(spr), hip[1] + x * math.sin(spr) + y * math.cos(spr))
            for sd, s in (("L", -1), ("R", 1)):
                # arm: shoulder moves with the spine
                if f"hand.{sd}" in self.t:
                    sh = spin((s * S["shW"], z["sh"] - 0.02 + bo)); tx, tz = self.tr(f"hand.{sd}").at(f)
                    side = bend.get(f"arm.{sd}", -s)                     # elbow bends outward by default
                    e, w = ik2(sh, (tx, tz), S["up"], S["fo"], side)
                    a_up = ang((e[0] - sh[0], e[1] - sh[1])) + 90; a_fo = ang((w[0] - e[0], w[1] - e[1])) + 90     # 0 = hanging straight down
                    rot(f"upper.{sd}", a_up - sp, f); rot(f"fore.{sd}", a_fo - a_up, f)
                if f"fingers.{sd}" in self.t and f"hand.{sd}" in self.t:      # world direction the fingers point (deg CCW from +x)
                    phi = a_fo - 90; rot(f"hand.{sd}", self.tr(f"fingers.{sd}").at(f)[0] - phi, f)
                elif f"handrot.{sd}" in self.t: rot(f"hand.{sd}", self.tr(f"handrot.{sd}").at(f)[0], f)
                if f"foot.{sd}" in self.t:
                    hp = (s * S["hipW"], z["hip"] + bo); tx, tz = self.tr(f"foot.{sd}").at(f)
                    e, w = ik2(hp, (tx, tz), S["th"], S["sn"], bend.get(f"leg.{sd}", s))
                    a_th = ang((e[0] - hp[0], e[1] - hp[1])) + 90; a_sn = ang((w[0] - e[0], w[1] - e[1])) + 90
                    rot(f"thigh.{sd}", a_th, f); rot(f"shin.{sd}", a_sn - a_th, f)
