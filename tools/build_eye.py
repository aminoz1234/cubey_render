"""Cat-scratch eye video: "This is what happens when your cat scratches your eye while you're playing".
Opens scenes/real/man.blend, lays him on a sofa (cat only as a furry paw), builds the macro eye set (10x, x=50),
the bacteria micro set (x=80), cameras and cuts. Saves scenes/eye/eye.blend.  Blender 5.2+, Cycles."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

ROOT = os.environ.get("CUBEY_ROOT") or os.getcwd()
for f_ in ("realism.py", "common_build.py", "eye_macro.py", "paw.py"):
    exec(open(os.path.join(ROOT, "tools", f_)).read())
random.seed(5)
FPS = 30
T_END = 40.55


def F(t):
    return int(round(t * FPS)) + 1


S = bpy.context.scene
S.render.fps = FPS; S.frame_start, S.frame_end = 1, F(T_END)
cycles_quality(S, samples=24, res=(720, 1280))
S.view_settings.look = "AgX - Medium High Contrast"
S.timeline_markers.clear()
for o in list(bpy.data.objects):
    if o.type in ("CAMERA", "LIGHT") or (o.type == "EMPTY" and o.name != "Man"):
        bpy.data.objects.remove(o)

T = dict(wide=0.0, paw=3.25, claw=4.4, cornea=6.6, burn=12.0, heal=15.7, bact=19.8, ulcer=23.25,
         pierce=26.1, surgery=29.6, ohio=33.3, end=37.9)
FR = {k: F(v) for k, v in T.items()}
order = list(T)
RANGE = {k: (FR[k], (FR[order[i + 1]] - 1) if i + 1 < len(order) else F(T_END)) for i, k in enumerate(order)}

# ================================================================ THE MAN: lying on his back on the sofa
rig = bpy.data.objects["Man"]; body = bpy.data.objects["Man.body"]; pb = rig.pose.bones
SEAT = 0.41
rig.rotation_euler = (math.radians(-90), 0, math.radians(90))
rig.location = (1.05, -0.08, SEAT + 0.105)
bpy.context.view_layer.update()


def aim_bone(name, direction):
    p = pb[name]; M = p.matrix.copy(); cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    Rm = q.to_matrix().to_4x4()
    p.matrix = Matrix.Translation(M.translation) @ Rm @ Matrix.Translation(-M.translation) @ M
    bpy.context.view_layer.update()


aim_bone("upperarm01.L", (0.15, 0.05, -1.0)); aim_bone("lowerarm01.L", (0.05, -0.35, -1.0))
aim_bone("upperarm01.R", (-0.15, 0.05, -1.0)); aim_bone("lowerarm01.R", (-0.05, -0.35, -1.0))
for side in ("L", "R"):
    for b in ("upperarm01", "lowerarm01"):
        p = pb[b + "." + side]; p.rotation_mode = "QUATERNION"; p.keyframe_insert("rotation_quaternion", frame=1)
pb["head"].rotation_mode = "XYZ"; pb["head"].rotation_euler = (math.radians(-14), 0, 0)
pb["head"].keyframe_insert("rotation_euler", frame=1)
bpy.context.view_layer.update()
LID_SIGN = -1.0
for nm in ("orbicularis03.L", "orbicularis03.R", "orbicularis04.L", "orbicularis04.R"):
    pb[nm].rotation_mode = "XYZ"


def lids(f, closed):
    up = math.radians(26) * closed * LID_SIGN; lo = math.radians(-9) * closed * LID_SIGN
    for s_ in ("L", "R"):
        pb["orbicularis03." + s_].rotation_euler = (up, 0, 0); pb["orbicularis03." + s_].keyframe_insert("rotation_euler", frame=f)
        pb["orbicularis04." + s_].rotation_euler = (lo, 0, 0); pb["orbicularis04." + s_].keyframe_insert("rotation_euler", frame=f)


lids(1, 0.0)
# rapid blinking on "can't stop blinking"
for t0 in (14.5, 14.95, 15.35):
    f0 = F(t0); lids(f0, 0.0); lids(f0 + 2, 1.0); lids(f0 + 5, 0.0)
# Ohio: asleep, then wakes up on "woke up"
lids(RANGE["ohio"][0], 1.0); lids(F(36.35), 1.0); lids(F(36.6), -0.1); lids(RANGE["ohio"][1], -0.1); lids(RANGE["end"][0], 0.0)
set_interp(rig, "BEZIER", 'pose.bones["orbicularis')

HEAD = rig.matrix_world @ Vector((0, -0.05, 1.66))
EYE_L = rig.matrix_world @ Vector((0.032, -0.125, 1.663))
EYE_R = rig.matrix_world @ Vector((-0.032, -0.125, 1.663))
CHEST = rig.matrix_world @ Vector((0.0, -0.13, 1.3))
print("HEAD", HEAD, "EYE_L", EYE_L, "CHEST", CHEST)

# ---------------------------------------------------------------- his eyes: redness (burning) and a cloudy left cornea (Ohio)
eyes_ob = bpy.data.objects.get("Man.high-poly")
em0 = eyes_ob.data.materials[0]; ent = em0.node_tree
red_mix = ent.nodes.new("ShaderNodeMix"); red_mix.data_type = "RGBA"; red_mix.blend_type = "MULTIPLY"
red_mix.inputs["B"].default_value = (1.0, 0.3, 0.27, 1)
src = ent.nodes["diffuseIntensity"]; bsdf = ent.nodes["Principled BSDF"]
ent.links.new(src.outputs[0], red_mix.inputs["A"]); ent.links.new(red_mix.outputs["Result"], bsdf.inputs["Base Color"])
RF = red_mix.inputs["Factor"]
for f, v in ((1, 0.0), (FR["burn"], 0.15), (F(13.3), 1.0), (RANGE["burn"][1], 1.0), (RANGE["burn"][1] + 1, 0.0),
             (RANGE["ohio"][0], 0.35), (RANGE["ohio"][1] + 1, 0.0)):
    RF.default_value = v; RF.keyframe_insert("default_value", frame=f)
set_interp(ent, "LINEAR")
# cloudy cornea on his left eye (material slot 2 on that eye's cornea)
cloudy_mat = bpy.data.materials.new("cornea_cloudy"); cloudy_mat.use_nodes = True; cn = cloudy_mat.node_tree.nodes; ck = cloudy_mat.node_tree.links
cn.remove(cn["Principled BSDF"])
tr_ = cn.new("ShaderNodeBsdfTransparent"); gl = cn.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.0
fr = cn.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.376; clr = cn.new("ShaderNodeMixShader")
ck.new(fr.outputs[0], clr.inputs[0]); ck.new(tr_.outputs[0], clr.inputs[1]); ck.new(gl.outputs[0], clr.inputs[2])
milk = cn.new("ShaderNodeBsdfPrincipled"); milk.inputs["Base Color"].default_value = (0.8, 0.82, 0.8, 1); milk.inputs["Roughness"].default_value = 0.35
milk.inputs["Subsurface Weight"].default_value = 0.5; milk.inputs["Subsurface Scale"].default_value = 0.002
mixc = cn.new("ShaderNodeMixShader"); ck.new(clr.outputs[0], mixc.inputs[1]); ck.new(milk.outputs[0], mixc.inputs[2])
ck.new(mixc.outputs[0], cn["Material Output"].inputs["Surface"])
CF = mixc.inputs[0]
for f, v in ((1, 0.0), (RANGE["ohio"][0], 0.85), (RANGE["ohio"][1] + 1, 0.0)):
    CF.default_value = v; CF.keyframe_insert("default_value", frame=f)
set_interp(cloudy_mat.node_tree, "CONSTANT")
# tears: drops running from the outer corner of his left eye toward the temple (he lies on his back)
m_tear = liquid("tear", tint=(0.95, 0.97, 1.0), density=0.2, rough=0.0)
dg = bpy.context.evaluated_depsgraph_get()
for k in range(3):
    t0 = 12.9 + k * 0.85
    d = link(bpy.data.objects.new(f"tear{k}", bpy.data.meshes.new(f"tear{k}")))
    bmd = bmesh.new(); bmesh.ops.create_uvsphere(bmd, u_segments=20, v_segments=10, radius=1.0); bmd.to_mesh(d.data); bmd.free()
    for p in d.data.polygons:
        p.use_smooth = True
    d.data.materials.append(m_tear); d.scale = (0.0028, 0.0028, 0.0016)
    pts = []
    for s_ in range(6):
        lp = rig.matrix_world @ Vector((0.058 + 0.006 * s_, -0.105 + 0.012 * s_, 1.655 - 0.004 * s_))
        hit, loc, nrm, *_ = S.ray_cast(dg, lp + Vector((0, 0, 0.2)), Vector((0, 0, -1)))
        pts.append(loc + nrm * 0.0012 if hit else lp)
    for s_, p in enumerate(pts):
        d.location = p; d.keyframe_insert("location", frame=F(t0) + s_ * 6)
    show_only(d, [(F(t0), RANGE["burn"][1])])

# skin pores, clear corneas (shared fix)
# skin pores + no coat streaks; clear eyes (same fixes as the bite shot)
for ms in body.material_slots:
    mt = ms.material
    if not mt or not mt.use_nodes:
        continue
    for n in mt.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            nt = mt.node_tree
            nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 4
            vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1400
            mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"
            nt.links.new(nz.outputs["Fac"], mx.inputs[0]); nt.links.new(vor.outputs["Distance"], mx.inputs[1])
            bp_ = nt.nodes.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = 0.12; bp_.inputs["Distance"].default_value = 0.0005
            nt.links.new(mx.outputs["Value"], bp_.inputs["Height"])
            if not n.inputs["Normal"].is_linked:
                nt.links.new(bp_.outputs["Normal"], n.inputs["Normal"])
            n.inputs["Coat Weight"].default_value = 0.0
            if not n.inputs["Roughness"].is_linked:
                n.inputs["Roughness"].default_value = 0.5
eyes = bpy.data.objects.get("Man.high-poly")
if eyes and len(eyes.data.materials) < 2:
    c = bpy.data.materials.new("eye_cornea"); c.use_nodes = True; cn = c.node_tree.nodes; cl = c.node_tree.links
    cn.remove(cn["Principled BSDF"])
    tr_ = cn.new("ShaderNodeBsdfTransparent"); gl = cn.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.0
    fr = cn.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.376; mx_ = cn.new("ShaderNodeMixShader")
    cl.new(fr.outputs[0], mx_.inputs[0]); cl.new(tr_.outputs[0], mx_.inputs[1]); cl.new(gl.outputs[0], mx_.inputs[2])
    cl.new(mx_.outputs[0], cn["Material Output"].inputs["Surface"])
    me = eyes.data; me.materials.append(c)
    bm = bmesh.new(); bm.from_mesh(me); seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]; comp = []; seen.add(f.index)
        while stack:
            x = stack.pop(); comp.append(x)
            for e in x.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index); stack.append(g)
        vs = {v for q in comp for v in q.verts}
        for q in comp:
            q.material_index = 1 if len(vs) == 256 else 0
    bm.to_mesh(me); bm.free()



me_ = eyes_ob.data; me_.materials.append(cloudy_mat)
bm = bmesh.new(); bm.from_mesh(me_)
for f in bm.faces:
    if f.material_index == 1 and f.calc_center_median().x > 0:
        f.material_index = 2
bm.to_mesh(me_); bm.free()


# ================================================================ LIVING ROOM
def import_model(mid, loc, rot_z=0.0, scale=1.0):
    path = os.path.join(ROOT, "assets", "models", mid, mid + "_1k.gltf")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = link(bpy.data.objects.new(mid + "_root", None))
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot_z)); root.scale = (scale,) * 3
    return root


sofa = import_model("sofa_02", Vector((-0.1, 0.0, 0.0)))
plant = import_model("potted_plant_01", Vector((-1.35, 0.6, 0.0)), 20)
COT = os.path.join(ROOT, "assets", "tex", "cotton_jersey")
m_cush, _ = img_mat("cushion", COT, tint=(0.75, 0.55, 0.35), scale=6, bump=0.6)
cush = soft_box("cushion", (HEAD.x - 0.05, HEAD.y + 0.0, SEAT + 0.03), (0.2, 0.2, 0.06), m_cush, levels=3, cast=0.25, wrinkle=0.006, wscale=0.05)
m_rug = mat("floor", (0.18, 0.11, 0.06), rough=0.45)
floor_ = soft_box("floor", (0, 0, -0.01), (5, 5, 0.01), m_rug, levels=1, cast=0, wrinkle=0)
W = bpy.data.worlds.new("world"); S.world = W; W.use_nodes = True; wn = W.node_tree.nodes; wl = W.node_tree.links
env = wn.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(ROOT, "assets", "hdri", "lythwood_lounge_2k.hdr")); env.image.pack()
wl.new(env.outputs["Color"], wn["Background"].inputs["Color"]); wn["Background"].inputs["Strength"].default_value = 0.6
key_l = area("key", HEAD + Vector((0.6, -0.9, 1.1)), HEAD, 22, 1.0, (1.0, 0.85, 0.7))
rim_l = area("rim", HEAD + Vector((-0.5, 0.8, 0.7)), HEAD, 10, 0.8, (0.7, 0.8, 1.0))
lamp_l = point("lamp", Vector((-1.2, 0.5, 1.1)), 25, (1.0, 0.65, 0.35), r=0.08)
# Ohio: early-morning cool light instead of the warm evening
for lt, warm, cool in ((key_l, 22, 6), (lamp_l, 25, 0)):
    key_energy(lt, [(1, warm), (RANGE["ohio"][0], cool), (RANGE["ohio"][1] + 1, warm)])
dawn = area("dawn", HEAD + Vector((0.3, -0.7, 1.2)), HEAD, 0.0, 1.5, (0.6, 0.75, 1.0))
key_energy(dawn, [(1, 0.0), (RANGE["ohio"][0], 18), (RANGE["ohio"][1] + 1, 0.0)])

# throw blanket over his legs (ray-cast drape)
import numpy as np
dg = bpy.context.evaluated_depsgraph_get()
NX, NY = 70, 50; X0b, X1b, Y0b, Y1b = 0.02, 1.25, -0.48, 0.32
H = np.full((NX, NY), SEAT + 0.01)
for i in range(NX):
    for j in range(NY):
        x = X0b + (X1b - X0b) * i / (NX - 1); y = Y0b + (Y1b - Y0b) * j / (NY - 1)
        hit, loc, *_, ob, _m = S.ray_cast(dg, Vector((x, y, 2.0)), Vector((0, 0, -1)))
        if hit and ob and ob.name.startswith("Man"):
            H[i, j] = max(H[i, j], loc.z + 0.02)
def _maxf(A, r):
    P = np.pad(A, r, mode="edge"); out = A.copy()
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            out = np.maximum(out, P[r + di:r + di + A.shape[0], r + dj:r + dj + A.shape[1]])
    return out
def _blur(A, sig):
    r = int(sig * 3); k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sig * sig)); k /= k.sum()
    P = np.pad(A, r, mode="edge")
    P = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 0, P)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 1, P)
H = _blur(_maxf(H, 2), 2.0)
bm = bmesh.new()
vs = [[bm.verts.new((X0b + (X1b - X0b) * i / (NX - 1), Y0b + (Y1b - Y0b) * j / (NY - 1), H[i, j])) for j in range(NY)] for i in range(NX)]
for i in range(NX - 1):
    for j in range(NY - 1):
        bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
for i in range(NX):
    vs[i][0].co.z = SEAT - 0.15; vs[i][0].co.y -= 0.05
me = bpy.data.meshes.new("throw"); bm.to_mesh(me); bm.free()
throw = link(bpy.data.objects.new("throw", me))
for p in me.polygons:
    p.use_smooth = True
throw.modifiers.new("thick", "SOLIDIFY").thickness = 0.02
tx = bpy.data.textures.new("throw_w", "CLOUDS"); tx.noise_scale = 0.07; tx.noise_depth = 4
dd = throw.modifiers.new("folds", "DISPLACE"); dd.texture = tx; dd.strength = 0.06; dd.texture_coords = "GLOBAL"
throw.modifiers.new("sub", "SUBSURF").levels = 2
m_throw, _ = img_mat("throw", COT, tint=(0.35, 0.42, 0.32), scale=5, bump=0.8)
me.materials.append(m_throw)

# ================================================================ THE PAW (cat stays off-screen)
pw = paw("paw")
pw.scale = (1.0, 1.0, 1.0)
# wide: paw reaches in from the top right, batting at his face; claws come out on the swipe
PAW_REST = HEAD + Vector((0.22, -0.16, 0.22))
pw.rotation_mode = "XYZ"


def paw_key(f, loc, rot, claw):
    pw.location = loc; pw.keyframe_insert("location", frame=f)
    pw.rotation_euler = rot; pw.keyframe_insert("rotation_euler", frame=f)
    keyp(pw, "claw", f, claw)


r0 = (math.radians(-60), math.radians(10), math.radians(40))
paw_key(1, PAW_REST + Vector((0.12, -0.05, 0.1)), r0, 0.0)
paw_key(F(1.3), PAW_REST + Vector((0.03, 0.0, 0.03)), r0, 0.0)
paw_key(F(1.9), PAW_REST + Vector((0.08, -0.02, 0.08)), r0, 0.0)
paw_key(F(2.6), PAW_REST, (math.radians(-70), math.radians(5), math.radians(35)), 0.3)
paw_key(RANGE["wide"][1], PAW_REST + Vector((0.02, 0.0, 0.02)), r0, 0.4)
# POV swipe (slow motion): passes right in front of his left eye, claws fully out
E = EYE_L
paw_key(RANGE["paw"][0], E + Vector((0.2, -0.05, 0.2)), (math.radians(-35), math.radians(-20), math.radians(60)), 0.6)
paw_key(F(3.9), E + Vector((0.05, -0.02, 0.13)), (math.radians(-45), math.radians(-10), math.radians(45)), 1.0)
paw_key(RANGE["paw"][1], E + Vector((-0.12, 0.03, 0.12)), (math.radians(-50), 0, math.radians(30)), 1.0)
# ending: resting on his chest, claws slowly flexing out (loops back to the start)
END_P = CHEST + Vector((0.02, -0.02, 0.06))
paw_key(RANGE["end"][0], END_P, (math.radians(-10), 0, math.radians(100)), 0.0)
paw_key(F(39.2), END_P, (math.radians(-10), 0, math.radians(100)), 1.0)
paw_key(RANGE["end"][1], END_P + Vector((0, 0, 0.005)), (math.radians(-12), 0, math.radians(100)), 0.7)
set_interp(pw, "BEZIER")
hide_tree(pw, [RANGE["paw"], RANGE["end"]])

exec(open(os.path.join(ROOT, "tools", "cat.py")).read())
fg_cat = cat(ROOT, scale=1.45, name="fgcat")
fg_cat.location = HEAD + Vector((0.55, -0.62, -0.08)); fg_cat.rotation_euler = (0, 0, math.radians(150))
hide_tree(fg_cat, [RANGE["wide"]])

# ================================================================ MACRO EYE SET (10x at x=50)
X0 = 50.0
skin = tissue("lid_skin", base=(0.62, 0.4, 0.32), crease=(0.4, 0.2, 0.16), sss=0.4, wet=0.15, bump=0.2, scale=25, veins=0.0)
EY = eye_set(X0, skin)
C0 = Vector((X0, 0, 0))
NL, NW, NU, NN, NRED = (EY[k].outputs[0] for k in ("N_L", "N_W", "N_U", "N_NERVE", "N_RED"))


def kv(sock, pairs, interp="LINEAR"):
    for f, v in pairs:
        sock.default_value = v; sock.keyframe_insert("default_value", frame=f)


f_cut0, f_cut1 = F(4.9), F(6.2)
kv(NL, [(1, 0.0), (f_cut0, 0.0), (f_cut1, 1.0), (RANGE["pierce"][0] - 1, 1.0), (RANGE["pierce"][0], 0.0),
        (RANGE["pierce"][1], 0.0), (RANGE["surgery"][0], 1.0)])
kv(NW, [(1, 0.035), (F(16.8), 0.035), (F(19.3), 0.0), (RANGE["bact"][0], 0.0), (RANGE["ulcer"][0], 0.03)])
kv(NU, [(1, 0.0), (RANGE["ulcer"][0], 0.0), (F(23.7), 0.02), (F(26.0), 0.34), (RANGE["pierce"][0] - 1, 0.34),
        (RANGE["pierce"][0], 0.0), (RANGE["pierce"][1], 0.0), (RANGE["surgery"][0], 0.3)])
kv(NN, [(1, 0.0)])
kv(NRED, [(1, 0.1), (RANGE["heal"][0], 0.45), (RANGE["ulcer"][0], 0.85), (RANGE["pierce"][0], 0.5), (RANGE["surgery"][0], 0.9)])
for mt in (EY["cornea"].data.materials[0], EY["ball"].data.materials[0]):
    set_interp(mt.node_tree, "CONSTANT")
# smooth only the growth curves
for fc in fcurves(EY["cornea"].data.materials[0].node_tree):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
for fc in fcurves(EY["cornea"].data.materials[0].node_tree):
    pts = fc.keyframe_points
    for i in range(1, len(pts)):           # jumps between shots stay hard cuts
        if pts[i].co.x - pts[i - 1].co.x <= 1.5:
            pts[i - 1].interpolation = "CONSTANT"


def on_cornea(x, z):
    """World point on the cornea surface for normalised (x, z)."""
    r2 = x * x + z * z
    y = -math.sqrt(max(0.0, 1 - r2)); y -= 0.17 * max(0.0, 1 - r2 / 0.26)
    return C0 + Vector((x, y, z)) * 1.012 * R


# the claw (10x): slides across the cornea along the scratch line
claw_tip = link(bpy.data.objects.new("claw_tip", None))
cm_ = claw_mesh("big_claw", length=0.03, base_r=0.0026, curl=0.7); cm_.parent = claw_tip; cm_.scale = (10, 10, 10)
curl = 0.7; Lc = 0.03
tip_local = Vector((0, -math.sin(curl) * Lc / curl, -(1 - math.cos(curl)) * Lc / curl)) * 10
cm_.location = -tip_local
claw_tip.rotation_euler = (math.radians(-15), 0, math.radians(200))
A2 = Vector((-0.42, 0.3)); D2 = Vector((0.8, -0.55))
for f, t in ((RANGE["claw"][0], -0.25), (f_cut0, 0.0), (f_cut1, 1.0), (RANGE["claw"][1], 1.25)):
    tt = max(0.0, min(1.0, t)); p2 = A2 + D2 * tt
    lift = 0.0 if 0 <= t <= 1 else 0.05
    claw_tip.location = on_cornea(p2.x, p2.y) + Vector((0, -lift, 0)); claw_tip.keyframe_insert("location", frame=f)
# pierce: straight in through the middle of the cornea
mid = on_cornea(0.05, 0.05)
for f, depth in ((RANGE["pierce"][0], -0.12), (F(27.5), 0.0), (F(28.6), 0.07), (RANGE["pierce"][1], 0.08)):
    claw_tip.location = mid + Vector((0, depth, 0)); claw_tip.keyframe_insert("location", frame=f)
claw_tip.rotation_euler = (math.radians(-15), 0, math.radians(200)); claw_tip.keyframe_insert("rotation_euler", frame=RANGE["claw"][0])
claw_tip.rotation_euler = (math.radians(25), 0, math.radians(180)); claw_tip.keyframe_insert("rotation_euler", frame=RANGE["pierce"][0])
set_interp(claw_tip, "LINEAR")
hide_tree(claw_tip, [RANGE["claw"], RANGE["pierce"]])
# fluid welling around the pierce
m_aq = liquid("aqueous", tint=(0.95, 0.9, 0.85), density=0.3, rough=0.02)
well = link(bpy.data.objects.new("well", bpy.data.meshes.new("well")))
bmw = bmesh.new(); bmesh.ops.create_uvsphere(bmw, u_segments=24, v_segments=12, radius=1.0); bmw.to_mesh(well.data); bmw.free()
for p in well.data.polygons:
    p.use_smooth = True
well.data.materials.append(m_aq); well.location = mid + Vector((0, -0.002, 0))
for f, s_ in ((F(27.6), 0.001), (F(29.0), 0.018)):
    well.scale = (s_, s_ * 0.5, s_); well.keyframe_insert("scale", frame=f)
show_only(well, [(F(27.6), RANGE["pierce"][1])])
# surgery: green drape with a hole, wire speculum, cannula
m_drape, _ = img_mat("drape", COT, tint=(0.05, 0.2, 0.17), scale=1.0, bump=0.8)
bm = bmesh.new(); NA_, NR_ = 64, 10
rings = [[bm.verts.new((C0.x + (0.24 + 1.2 * (k / NR_) ** 1.5) * math.cos(2 * math.pi * a / NA_), -0.16 - 0.02 * k,
                        (0.2 + 1.2 * (k / NR_) ** 1.5) * math.sin(2 * math.pi * a / NA_))) for a in range(NA_)] for k in range(NR_ + 1)]
for k in range(NR_):
    for a in range(NA_):
        bm.faces.new((rings[k][a], rings[k][(a + 1) % NA_], rings[k + 1][(a + 1) % NA_], rings[k + 1][a]))
me = bpy.data.meshes.new("drape"); bm.to_mesh(me); bm.free(); me.materials.append(m_drape)
drape = link(bpy.data.objects.new("drape", me))
for p in me.polygons:
    p.use_smooth = True
tx2 = bpy.data.textures.new("drape_w", "CLOUDS"); tx2.noise_scale = 0.15
d2 = drape.modifiers.new("folds", "DISPLACE"); d2.texture = tx2; d2.strength = 0.05; d2.texture_coords = "GLOBAL"; d2.direction = "Y"
drape.modifiers.new("sub", "SUBSURF").levels = 1
show_only(drape, [RANGE["surgery"]])
m_steel = mat("steel", (0.75, 0.75, 0.77), rough=0.18, metal=1.0)
for s_ in (-1, 1):
    cu = bpy.data.curves.new(f"spec{s_}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.004; cu.bevel_resolution = 3
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(3)
    pts = [C0 + Vector((-0.1, -0.15, s_ * 0.075)), C0 + Vector((0.0, -0.16, s_ * 0.095)), C0 + Vector((0.1, -0.15, s_ * 0.075)), C0 + Vector((0.3, -0.25, s_ * 0.2))]
    for bp_, p in zip(sp.bezier_points, pts):
        bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
    cu.materials.append(m_steel); so = link(bpy.data.objects.new(f"speculum{s_}", cu)); show_only(so, [RANGE["surgery"]])
can = link(bpy.data.objects.new("cannula", bpy.data.meshes.new("cannula")))
bmc = bmesh.new(); bmesh.ops.create_cone(bmc, cap_ends=True, segments=16, radius1=0.006, radius2=0.004, depth=0.5); bmc.to_mesh(can.data); bmc.free()
can.data.materials.append(m_steel)
can.rotation_euler = (math.radians(70), 0, math.radians(55))
for f, off in ((RANGE["surgery"][0], 0.25), (F(31.5), 0.02), (RANGE["surgery"][1], 0.0)):
    can.location = on_cornea(0.2, -0.1) + Vector((0.2, -0.12, -0.15)).normalized() * (0.25 + off); can.keyframe_insert("location", frame=f)
show_only(can, [RANGE["surgery"]])
# macro lights: soft key + catch-light ring; surgical ring light only in surgery
mk = area("macro_key", C0 + Vector((0.5, -0.9, 0.7)), C0, 9, 0.8, (1.0, 0.93, 0.85))
mf = area("macro_fill", C0 + Vector((-0.7, -0.6, -0.1)), C0, 3, 1.0, (0.8, 0.88, 1.0))
ring = area("ring_light", C0 + Vector((0, -0.75, 0.05)), C0, 0.0, 0.25, (1, 1, 1))
key_energy(ring, [(1, 0.0), (RANGE["surgery"][0], 7), (RANGE["surgery"][1] + 1, 0.0)])
key_energy(mk, [(1, 9), (RANGE["surgery"][0], 2), (RANGE["surgery"][1] + 1, 9)])
# dark backdrop around the macro set so the living room HDRI does not show
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=3.0); bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("macro_bg"); bm.to_mesh(me); bm.free(); me.materials.append(mat("macro_bg", (0.03, 0.02, 0.018), rough=0.9))
link(bpy.data.objects.new("macro_bg", me)).location = C0

# ================================================================ BACTERIA ON THE CLAW (micro set at x=80)
XB = 80.0; CB = Vector((XB, 0, 0))
ker = soft_box("keratin", (XB, 0, -0.05), (1.5, 1.5, 0.05), mat("keratin", (0.35, 0.28, 0.2), rough=0.4, sss=0.3), levels=2, cast=0, wrinkle=0.0)
tkx = bpy.data.textures.new("ridges", "WOOD"); tkx.wood_type = "BANDNOISE"; tkx.noise_scale = 0.4; tkx.turbulence = 8
dk = ker.modifiers.new("ridges", "DISPLACE"); dk.texture = tkx; dk.strength = 0.03; dk.texture_coords = "GLOBAL"
ker.modifiers.new("sub2", "SUBSURF").levels = 2
m_bac = bpy.data.materials.new("bacteria"); m_bac.use_nodes = True; bb_ = m_bac.node_tree.nodes["Principled BSDF"]
bb_.inputs["Base Color"].default_value = (0.3, 0.06, 0.25, 1); bb_.inputs["Roughness"].default_value = 0.3
bb_.inputs["Subsurface Weight"].default_value = 0.6; bb_.inputs["Subsurface Scale"].default_value = 0.02
bb_.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.9); bb_.inputs["Coat Weight"].default_value = 0.5
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
for v in bm.verts:
    v.co.z = v.co.z * 1.0 + (2.0 if v.co.z > 0 else -2.0)      # capsule along z
bac_me = bpy.data.meshes.new("bac"); bm.to_mesh(bac_me); bm.free(); bac_me.materials.append(m_bac)
for p in bac_me.polygons:
    p.use_smooth = True
rnd = random.Random(9)
for k in range(160):
    b = link(bpy.data.objects.new(f"bac{k}", bac_me))
    r_ = rnd.uniform(0.008, 0.012); b.scale = (r_, r_, r_ * rnd.uniform(0.8, 1.3))
    b.location = CB + Vector((rnd.uniform(-0.45, 0.45), rnd.uniform(-0.35, 0.45), 0.012 + rnd.uniform(0, 0.02)))
    b.rotation_euler = (math.radians(90 + rnd.uniform(-15, 15)), 0, rnd.uniform(0, 6.28))
    b.keyframe_insert("rotation_euler", frame=1); b.keyframe_insert("location", frame=1)
    for fc in fcurves(b):
        nm_ = fc.modifiers.new("NOISE"); nm_.scale = rnd.uniform(6, 14); nm_.strength = 0.06 if "rotation" in fc.data_path else 0.01
        nm_.phase = rnd.uniform(0, 100)
mbk = area("bac_key", CB + Vector((0.6, -0.7, 0.8)), CB, 14, 0.8, (1.0, 0.9, 0.85))
mbr = area("bac_rim", CB + Vector((-0.6, 0.8, 0.25)), CB, 60, 0.6, (0.5, 0.75, 1.0))
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=4.0); bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("bac_bg"); bm.to_mesh(me); bm.free(); me.materials.append(mat("bac_bg", (0.02, 0.02, 0.03), rough=0.9))
link(bpy.data.objects.new("bac_bg", me)).location = CB

# ================================================================ CAMERAS + CUTS
c1, a1 = camera("C01_wide", HEAD + Vector((0.75, -1.1, 0.55)), HEAD + Vector((0.3, 0, -0.08)), lens=30, fstop=1.8)
key(c1, "location", RANGE["wide"][0], c1.location.copy()); key(c1, "location", RANGE["wide"][1], HEAD + Vector((0.5, -0.8, 0.45)))
key(a1, "location", RANGE["wide"][0], a1.location.copy()); key(a1, "location", RANGE["wide"][1], HEAD + Vector((0.15, 0, 0.0)))
# POV from his eye, looking up at the swipe
c2, a2 = camera("C02_paw", E + Vector((0.0, -0.01, 0.015)), E + Vector((0.12, -0.02, 0.4)), lens=24, fstop=5.6, focus=pw)
c2.data.dof.focus_object = pw
look_up = (E + Vector((0.12, -0.02, 0.4)) - c2.location)
# macro: claw across the cornea
c3, a3 = camera("C03_claw", C0 + Vector((0.08, -0.55, 0.18)), C0 + Vector((0, -0.12, 0)), lens=50, fstop=8, clip=0.01)
key(c3, "location", RANGE["claw"][0], c3.location.copy()); key(c3, "location", RANGE["claw"][1], C0 + Vector((0.06, -0.45, 0.14)))
# cornea: arc from the front to the side profile
c4, a4 = camera("C04_cornea", C0 + Vector((0.05, -0.5, 0.1)), C0 + Vector((0, -0.1, 0)), lens=45, fstop=8, clip=0.01)
for f, ang in ((RANGE["cornea"][0], 0), (F(9.2), 40), (RANGE["cornea"][1], 55)):
    a = math.radians(ang); c4.location = C0 + Vector((-0.5 * math.sin(a), -0.5 * math.cos(a), 0.08)); c4.keyframe_insert("location", frame=f)
# his face: burning, watering, blinking (camera rolled so his face reads upright)
def look_at(cam, target, up):
    z = (cam.location - target).normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x)
    cam.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
c5, a5 = camera("C05_burn", E + Vector((0.0, -0.06, 0.3)), E, lens=60, fstop=2.8)
c5.constraints.remove(c5.constraints["Track To"]); c5.data.dof.focus_object = a5
look_at(c5, (E + EYE_R) / 2 + Vector((0.01, 0, 0)), (-1, 0, 0))
key(c5, "location", RANGE["burn"][0], c5.location.copy()); key(c5, "location", RANGE["burn"][1], E + Vector((0.0, -0.05, 0.24)))
# healing: front macro
c6, a6 = camera("C06_heal", C0 + Vector((0.0, -0.42, 0.06)), C0 + Vector((0, -0.12, 0)), lens=55, fstop=8, clip=0.01)
key(c6, "location", RANGE["heal"][0], c6.location.copy()); key(c6, "location", RANGE["heal"][1], C0 + Vector((0.0, -0.36, 0.05)))
# bacteria
c7, a7 = camera("C07_bact", CB + Vector((0.25, -0.65, 0.35)), CB + Vector((0, 0, 0.02)), lens=55, fstop=2.0, clip=0.01)
key(c7, "location", RANGE["bact"][0], c7.location.copy()); key(c7, "location", RANGE["bact"][1], CB + Vector((0.15, -0.45, 0.22)))
# ulcer spreading
c8, a8 = camera("C08_ulcer", C0 + Vector((-0.04, -0.45, 0.08)), C0 + Vector((0, -0.12, 0)), lens=55, fstop=8, clip=0.01)
key(c8, "location", RANGE["ulcer"][0], c8.location.copy()); key(c8, "location", RANGE["ulcer"][1], C0 + Vector((-0.03, -0.37, 0.07)))
# pierce: side view
c9, a9 = camera("C09_pierce", C0 + Vector((-0.45, -0.3, 0.05)), C0 + Vector((0, -0.1, 0)), lens=45, fstop=8, clip=0.01)
# surgery microscope: straight on, bright ring light
c10, a10 = camera("C10_surgery", C0 + Vector((0.0, -0.75, 0.04)), C0 + Vector((0, -0.12, 0)), lens=40, fstop=11, clip=0.01)
key(c10, "location", RANGE["surgery"][0], c10.location.copy()); key(c10, "location", RANGE["surgery"][1], C0 + Vector((0.0, -0.6, 0.03)))
# Ohio: his face at dawn, wakes up blind in one eye
c11, a11 = camera("C11_ohio", E + Vector((0.0, -0.06, 0.32)), E, lens=55, fstop=2.8)
c11.constraints.remove(c11.constraints["Track To"]); c11.data.dof.focus_object = a11
look_at(c11, (E + EYE_R) / 2, (-1, 0, 0))
key(c11, "location", RANGE["ohio"][0], c11.location.copy()); key(c11, "location", RANGE["ohio"][1], E + Vector((0.0, -0.05, 0.25)))
# end: the paw on his chest, claws flexing; his face soft behind
c12, a12 = camera("C12_end", END_P + Vector((0.18, -0.25, 0.1)), END_P + Vector((0, 0, -0.005)), lens=60, fstop=2.8, focus=pw)
key(c12, "location", RANGE["end"][0], c12.location.copy()); key(c12, "location", RANGE["end"][1], END_P + Vector((0.13, -0.18, 0.07)))

for nm, cam in (("wide", c1), ("paw", c2), ("claw", c3), ("cornea", c4), ("burn", c5), ("heal", c6), ("bact", c7),
                ("ulcer", c8), ("pierce", c9), ("surgery", c10), ("ohio", c11), ("end", c12)):
    cut(T[nm], cam)
S.camera = c1
for cam in CAMS.values():
    set_interp(cam, "BEZIER")
out = os.path.join(ROOT, "scenes", "eye", "eye.blend")
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("EYE READY", out, S.frame_end, RANGE)
