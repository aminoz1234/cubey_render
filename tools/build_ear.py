"""Ear video: "This is what happens when a bug crawls into your ear while you sleep".
Opens scenes/real/man.blend (MPFB2 human, CC0), lays him in a night-time bed, and builds every set, prop,
camera and cut (timeline markers), timed to the voiceover. Interiors sit far away at x=50 (10x scale).
Run: blender -b scenes/real/man.blend --python tools/build_ear.py   (CUBEY_ROOT = repo root)
Saves scenes/ear/ear.blend. Blender 5.2+, Cycles."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler
from bpy_extras import anim_utils

ROOT = os.environ.get("CUBEY_ROOT") or (os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else os.getcwd())
exec(open(os.path.join(ROOT, "tools", "realism.py")).read())
exec(open(os.path.join(ROOT, "tools", "roach.py")).read())
random.seed(11)
FPS = 30
T_END = 31.8


def F(t):
    return int(round(t * FPS)) + 1


S = bpy.context.scene
S.render.fps = FPS
S.frame_start, S.frame_end = 1, F(T_END)
cycles_quality(S, samples=40, res=(720, 1280))
S.view_settings.look = "AgX - Medium High Contrast"
S.timeline_markers.clear()
for o in list(bpy.data.objects):
    if o.type in ("CAMERA", "LIGHT") or (o.type == "EMPTY" and o.name != "Man"):
        bpy.data.objects.remove(o)


# ---------------------------------------------------------------- helpers
def link(ob):
    S.collection.objects.link(ob); return ob


def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if getattr(act, "is_action_layered", False) or not hasattr(act, "fcurves"):
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    return list(act.fcurves)


def set_interp(idb, interp="LINEAR", path=None):
    for fc in fcurves(idb):
        if path is None or fc.data_path.startswith(path):
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def key(ob, path, f, val):
    setattr(ob, path, val); ob.keyframe_insert(path, frame=f)


def keyp(ob, prop, f, val):
    ob[prop] = val; ob.keyframe_insert(f'["{prop}"]', frame=f)


def mat(name, col, rough=0.5, metal=0.0, coat=0.0, sss=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m


def img_mat(name, folder, tint=(1, 1, 1), scale=4.0, rough_mul=1.0, bump=0.4):
    """Poly Haven texture set (Diffuse / Rough / nor_gl) on object coords; images packed into the .blend."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    def tex(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(folder, fn), check_existing=True)
        t.image.pack()
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        t.projection = "BOX"; t.projection_blend = 0.3
        L.new(mp.outputs[0], t.inputs["Vector"]); return t
    d = tex("Diffuse.jpg"); mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0; L.new(d.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (*tint, 1)
    L.new(mx.outputs["Result"], b.inputs["Base Color"])
    r = tex("Rough.jpg", True); rm = N.new("ShaderNodeMath"); rm.operation = "MULTIPLY"; rm.inputs[1].default_value = rough_mul
    L.new(r.outputs["Color"], rm.inputs[0]); L.new(rm.outputs[0], b.inputs["Roughness"])
    n = tex("nor_gl.jpg", True); nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump
    L.new(n.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = 0.4; b.inputs["Sheen Tint"].default_value = (1, 1, 1, 1)
    return m, mx


def area(name, loc, target, energy, size, col=(1, 1, 1), shape="DISK"):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size; d.color = col; d.shape = shape
    ob = link(bpy.data.objects.new(name, d)); ob.location = loc
    e = link(bpy.data.objects.new(name + "_t", None)); e.location = target
    tr = ob.constraints.new("TRACK_TO"); tr.target = e; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    return ob


def point(name, loc, energy, col=(1, 1, 1), r=0.01, parent=None):
    d = bpy.data.lights.new(name, "POINT"); d.energy = energy; d.color = col; d.shadow_soft_size = r
    ob = link(bpy.data.objects.new(name, d)); ob.location = loc
    if parent:
        ob.parent = parent
    return ob


CAMS = {}


def camera(name, loc, target, lens=35, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = clip; d.sensor_width = 36
    ob = link(bpy.data.objects.new(name, d)); ob.location = loc
    aim = link(bpy.data.objects.new(name + "_aim", None)); aim.location = target
    tr = ob.constraints.new("TRACK_TO"); tr.target = aim; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = focus or aim
    CAMS[name] = ob
    return ob, aim


def cut(t, cam):
    mk = S.timeline_markers.new(cam.name, frame=F(t)); mk.camera = cam


def shake(cam, f0, f1, amp, seed=3):
    rnd = random.Random(seed); base = cam.location.copy()
    for f in range(f0, f1 + 1):
        a = amp * max(0.0, 1 - (f - f0) / max(1, f1 - f0))
        cam.location = base + Vector((rnd.uniform(-a, a), rnd.uniform(-a, a), rnd.uniform(-a, a))); cam.keyframe_insert("location", frame=f)
    cam.location = base; cam.keyframe_insert("location", frame=f1 + 1)


def show_only(ob, frames_on):
    """hide_render keyed: visible only inside the given (f0, f1) frame ranges."""
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1)
    for f0, f1 in frames_on:
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0)
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1 + 1)


def hide_tree(root, frames_on):
    for o in [root] + list(root.children_recursive):
        show_only(o, frames_on)


def key_energy(lt, pairs):
    for f, e in pairs:
        lt.data.energy = e; lt.data.keyframe_insert("energy", frame=f)
    set_interp(lt.data, "CONSTANT")


# ---------------------------------------------------------------- shot times (seconds) -> cuts
T = dict(wide=0.0, pillow=3.55, ear=5.2, canal=7.8, stuck=11.35, drum=13.2, eyes=16.35, scope=17.95,
         oil=19.55, dark=21.55, tweez=23.1, pull=25.5, tray=27.6, end=29.3)
FR = {k: F(v) for k, v in T.items()}
order = list(T)
RANGE = {k: (FR[k], (FR[order[i + 1]] - 1) if i + 1 < len(order) else F(T_END)) for i, k in enumerate(order)}
LOUD = F(17.14)

# ================================================================ THE MAN: asleep on his right side, left ear up
rig = bpy.data.objects["Man"]; body = bpy.data.objects["Man.body"]; pb = rig.pose.bones
MT = 0.5                                  # mattress top
PILLOW_TOP = MT + 0.12
tz = PILLOW_TOP + 0.087 - 0.014
rig.rotation_euler = (0, math.radians(-90), 0)
rig.location = (1.65, 0, tz)
bpy.context.view_layer.update()
EAR_L = Vector((0.0675, -0.050, 1.637))   # canal entrance (concha floor), rest pose, rig space
EAR = rig.matrix_world @ EAR_L
CANAL_DIR = (rig.matrix_world.to_3x3() @ Vector((-1.0, -0.35, 0.0))).normalized()   # into the head
print("EAR", tuple(round(x, 4) for x in EAR))


def aim_bone(name, direction):
    """Point a bone (armature space) along direction, keeping its head."""
    p = pb[name]; M = p.matrix.copy(); cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    R = q.to_matrix().to_4x4()
    p.matrix = Matrix.Translation(M.translation) @ R @ Matrix.Translation(-M.translation) @ M
    bpy.context.view_layer.update()


aim_bone("upperarm01.L", (0.12, -0.45, -1.0)); aim_bone("lowerarm01.L", (-0.1, -1.0, -0.25))
aim_bone("upperarm01.R", (-0.05, -0.75, -0.65)); aim_bone("lowerarm01.R", (0.05, -1.0, 0.25))
for side in ("L", "R"):
    for b in ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "clavicle", "shoulder01"):
        if b + "." + side in pb:
            p = pb[b + "." + side]; p.rotation_mode = "QUATERNION"
            p.keyframe_insert("rotation_quaternion", frame=1)
# head resting, slight tilt into the pillow
pb["head"].rotation_mode = "XYZ"; pb["neck01"].rotation_mode = "XYZ"


def head_key(f, rx=0.0, ry=0.0, rz=0.0):
    pb["head"].rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz)); pb["head"].keyframe_insert("rotation_euler", frame=f)


head_key(1, 4, 0, 0)

# eyelids: closed while asleep, snap open on LOUD
LID_SIGN = float(os.environ.get("LID_SIGN", "-1"))
for nm in ("orbicularis03.L", "orbicularis03.R", "orbicularis04.L", "orbicularis04.R"):
    pb[nm].rotation_mode = "XYZ"


def lids(f, closed):
    up = math.radians(26) * closed * LID_SIGN; lo = math.radians(-9) * closed * LID_SIGN
    for s in ("L", "R"):
        pb["orbicularis03." + s].rotation_euler = (up, 0, 0); pb["orbicularis03." + s].keyframe_insert("rotation_euler", frame=f)
        pb["orbicularis04." + s].rotation_euler = (lo, 0, 0); pb["orbicularis04." + s].keyframe_insert("rotation_euler", frame=f)


lids(1, 1.0); lids(LOUD - 2, 1.0); lids(LOUD + 1, -0.25); lids(RANGE["eyes"][1], -0.25)
lids(RANGE["eyes"][1] + 1, 1.0)                        # asleep again for the later bed shots
lids(RANGE["tweez"][0], -0.1); lids(RANGE["pull"][1], -0.1); lids(RANGE["pull"][1] + 1, 1.0)
head_key(LOUD - 1, 4, 0, 0); head_key(LOUD + 2, 4, 0, -7); head_key(LOUD + 12, 4, 0, -4); head_key(RANGE["eyes"][1] + 1, 4, 0, 0)
set_interp(rig, "CONSTANT", 'pose.bones["orbicularis')

# ear canal pit: push the concha floor inward so the bug can disappear into a real dark hole
pts = body.data.vertices
saved = [m.show_render for m in body.modifiers]
for m in body.modifiers:
    m.show_viewport = False
bpy.context.view_layer.update()
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
vg = body.vertex_groups.new(name="ear_pit")
for v in ev.vertices:
    d = (v.co - EAR_L).length
    if d < 0.0075 and v.co.x > 0.05:
        w = (1 - d / 0.0075) ** 1.5
        vg.add([v.index], w, "REPLACE")
body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
for m in body.modifiers:
    m.show_viewport = True
dp = body.modifiers.new("ear_pit", "DISPLACE"); dp.direction = "X"; dp.mid_level = 0.0; dp.strength = -0.011
dp.vertex_group = "ear_pit"; dp.space = "LOCAL"
with bpy.context.temp_override(object=body):
    bpy.ops.object.modifier_move_to_index(modifier="ear_pit", index=0)

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

# ================================================================ BEDROOM
COT = os.path.join(ROOT, "assets", "tex", "cotton_jersey")
m_sheet, sheet_tint = img_mat("sheet", COT, tint=(0.62, 0.68, 0.8), scale=6, bump=0.5)
m_duvet, _ = img_mat("duvet", COT, tint=(0.22, 0.26, 0.38), scale=5, bump=0.8)
m_pillow, pillow_tint = img_mat("pillowcase", COT, tint=(0.85, 0.86, 0.9), scale=6, bump=0.5)
# clinical look for the hospital shots: pillowcase turns into pale blue exam paper
pillow_tint.inputs["B"].default_value = (0.85, 0.86, 0.9, 1)
pillow_tint.inputs["B"].keyframe_insert("default_value", frame=1)
pillow_tint.inputs["B"].default_value = (0.55, 0.72, 0.85, 1); pillow_tint.inputs["B"].keyframe_insert("default_value", frame=RANGE["tweez"][0])
pillow_tint.inputs["B"].default_value = (0.85, 0.86, 0.9, 1); pillow_tint.inputs["B"].keyframe_insert("default_value", frame=RANGE["pull"][1] + 1)
set_interp(m_pillow.node_tree, "CONSTANT")


def soft_box(name, center, half, m, levels=3, cast=0.35, wrinkle=0.006, wscale=0.08):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); ob.location = center; ob.scale = half
    sb = ob.modifiers.new("sub", "SUBSURF"); sb.levels = sb.render_levels = levels
    cs = ob.modifiers.new("cast", "CAST"); cs.factor = cast; cs.use_z = True
    if wrinkle:
        tx = bpy.data.textures.new(name + "_w", "CLOUDS"); tx.noise_scale = wscale; tx.noise_depth = 3
        d = ob.modifiers.new("wrinkle", "DISPLACE"); d.texture = tx; d.strength = wrinkle; d.texture_coords = "GLOBAL"
        sb2 = ob.modifiers.new("sub2", "SUBSURF"); sb2.levels = sb2.render_levels = 1
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    return ob


mattress = soft_box("mattress", (0.7, 0.05, MT - 0.13), (1.25, 0.8, 0.13), m_sheet, cast=0.05, wrinkle=0.004, wscale=0.15)
def pillow_mesh(name, center, half, m):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 2 * half[0], v.co.y * 2 * half[1], v.co.z * 2 * half[2]))
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6], offset=0.07, segments=5, affect="EDGES")
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); ob.location = center
    sb = ob.modifiers.new("sub", "SUBSURF"); sb.levels = sb.render_levels = 3
    cs = ob.modifiers.new("puff", "CAST"); cs.factor = 0.35; cs.use_x = cs.use_y = False
    tx = bpy.data.textures.new(name + "_w", "CLOUDS"); tx.noise_scale = 0.05; tx.noise_depth = 3
    d = ob.modifiers.new("wrinkle", "DISPLACE"); d.texture = tx; d.strength = 0.008; d.texture_coords = "GLOBAL"
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    return ob
pillow = pillow_mesh("pillow", (-0.17, 0.0, MT + 0.055), (0.31, 0.25, 0.065), m_pillow)
pillow2 = pillow_mesh("pillow2", (-0.2, 0.62, MT + 0.07), (0.31, 0.25, 0.07), m_pillow)
pillow2.rotation_euler = (0.12, 0, 0.15)
m_wood = mat("headboard", (0.16, 0.09, 0.05), rough=0.45, coat=0.2)
hb = soft_box("headboard", (-0.6, 0.05, MT + 0.3), (0.035, 0.85, 0.45), m_wood, levels=1, cast=0.0, wrinkle=0)
hb.modifiers.remove(hb.modifiers["sub"]); _bv = hb.modifiers.new("bev", "BEVEL"); _bv.width = 0.01; _bv.segments = 3
m_wall = mat("wall", (0.42, 0.45, 0.5), rough=0.85)
wtx = bpy.data.textures.new("plaster", "CLOUDS"); wtx.noise_scale = 0.03
wall = soft_box("wall_back", (0.5, 1.6, 1.2), (3.0, 0.05, 1.6), m_wall, levels=1, cast=0, wrinkle=0)
wall2 = soft_box("wall_head", (-0.7, 0.0, 1.2), (0.05, 3.0, 1.6), m_wall, levels=1, cast=0, wrinkle=0)
floor_ = soft_box("floor", (0.5, 0.0, -0.01), (4.0, 4.0, 0.01), mat("floor", (0.12, 0.08, 0.05), rough=0.4), levels=1, cast=0, wrinkle=0)

# duvet: height field draped over the sleeping body (ray-cast + dilate + blur), from the shoulders down
dg = bpy.context.evaluated_depsgraph_get()
NX, NY = 90, 70
X0, X1, Y0, Y1 = 0.16, 1.95, -0.62, 0.72
import numpy as np
H = np.full((NX, NY), MT + 0.004)
for i in range(NX):
    for j in range(NY):
        x = X0 + (X1 - X0) * i / (NX - 1); y = Y0 + (Y1 - Y0) * j / (NY - 1)
        hit, loc, *_ , ob, _m = S.ray_cast(dg, Vector((x, y, 2.0)), Vector((0, 0, -1)))
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
H = _blur(_maxf(H, 2), 2.2)
bm = bmesh.new()
vs = [[bm.verts.new((X0 + (X1 - X0) * i / (NX - 1), Y0 + (Y1 - Y0) * j / (NY - 1), H[i, j])) for j in range(NY)] for i in range(NX)]
for i in range(NX - 1):
    for j in range(NY - 1):
        bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
# hang the front edge over the side of the mattress
for i in range(NX):
    v = vs[i][0]; v.co.z = MT - 0.18; v.co.y -= 0.06
    vs[i][1].co.z = (vs[i][1].co.z + MT) / 2
me = bpy.data.meshes.new("duvet"); bm.to_mesh(me); bm.free()
duvet = link(bpy.data.objects.new("duvet", me))
for p in me.polygons:
    p.use_smooth = True
sol = duvet.modifiers.new("thick", "SOLIDIFY"); sol.thickness = 0.03; sol.offset = 0
tx = bpy.data.textures.new("duvet_w", "CLOUDS"); tx.noise_scale = 0.07; tx.noise_depth = 4
dd = duvet.modifiers.new("folds", "DISPLACE"); dd.texture = tx; dd.strength = 0.08; dd.texture_coords = "GLOBAL"
sb = duvet.modifiers.new("sub", "SUBSURF"); sb.levels = sb.render_levels = 2
me.materials.append(m_duvet)


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
    bpy.context.view_layer.update()
    top = max((o.matrix_world @ Vector(c)).z for o in new if o.type == "MESH" for c in o.bound_box)
    return root, top


ns, ns_top = import_model("painted_wooden_nightstand", Vector((-0.45, 1.05, 0)), 90)
lamp, _ = import_model("vintage_oil_lamp", Vector((-0.45, 1.05, ns_top)), 30, 0.9)

# chips bag + spilled chips by his face (the reason the bug came)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=14, use_grid_fill=True)
for v in bm.verts:
    x, y, z = v.co.x * 0.17, v.co.y * 0.25, v.co.z
    pinch = max(0.0, (abs(y) - 0.09) / 0.035)          # crimped seals at both ends
    z = z * 0.07 * max(0.03, 1 - pinch) * (1 - 0.5 * (2 * x / 0.17) ** 2)
    v.co = Vector((x * (1 + 0.15 * pinch), y, z))
me = bpy.data.meshes.new("chipbag"); bm.to_mesh(me); bm.free()
bag = link(bpy.data.objects.new("chip_bag", me))
for p in me.polygons:
    p.use_smooth = True
ctx = bpy.data.textures.new("crinkle", "VORONOI"); ctx.noise_scale = 0.018
cd_ = bag.modifiers.new("crinkle", "DISPLACE"); cd_.texture = ctx; cd_.strength = 0.004; cd_.texture_coords = "GLOBAL"
bag.location = (-0.12, -0.37, MT + 0.035); bag.rotation_euler = (0.08, 0.05, math.radians(68))
m_bag = bpy.data.materials.new("bag_print"); m_bag.use_nodes = True
nt = m_bag.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.6; wv.inputs["Distortion"].default_value = 1.5
L.new(tc.outputs["Object"], wv.inputs["Vector"])
rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.55, 0.02, 0.02, 1); rp.color_ramp.elements[0].position = 0.55
rp.color_ramp.elements[1].color = (0.95, 0.65, 0.04, 1); rp.color_ramp.elements[1].position = 0.6
L.new(wv.outputs["Fac"], rp.inputs[0]); L.new(rp.outputs["Color"], b.inputs["Base Color"])
b.inputs["Metallic"].default_value = 0.55; b.inputs["Roughness"].default_value = 0.22; b.inputs["Coat Weight"].default_value = 0.6
me.materials.append(m_bag)
m_chip = mat("chip", (0.85, 0.55, 0.16), rough=0.45, coat=0.3, sss=0.15)
ctex = bpy.data.textures.new("chipbump", "CLOUDS"); ctex.noise_scale = 0.008
for k in range(9):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)
    for v in bm.verts:
        v.co.z = v.co.z * 0.06 + 0.25 * (v.co.x ** 2 - v.co.y ** 2) * 0.5
    me = bpy.data.meshes.new(f"chip{k}"); bm.to_mesh(me); bm.free(); me.materials.append(m_chip)
    for p in me.polygons:
        p.use_smooth = True
    ch = link(bpy.data.objects.new(f"chip{k}", me)); r = random.uniform(0.018, 0.026)
    ch.scale = (r, r * random.uniform(0.75, 0.95), r)
    ch.location = (-0.12 + random.uniform(-0.05, 0.12), -0.28 + random.uniform(-0.05, 0.04), MT + 0.006)
    if k < 3:
        ch.location = (-0.17 + 0.03 * k, -0.22 + 0.02 * k, PILLOW_TOP - 0.004)
    ch.rotation_euler = (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(0, 6.28))
    d = ch.modifiers.new("bump", "DISPLACE"); d.texture = ctex; d.strength = 0.08
crumbs = bmesh.new()
for k in range(70):
    c0 = Vector((-0.1 + random.gauss(0, 0.07), -0.28 + random.gauss(0, 0.06), MT + 0.004))
    if k < 20:
        c0 = Vector((-0.16 + random.gauss(0, 0.05), -0.18 + random.gauss(0, 0.03), PILLOW_TOP - 0.006))
    r = random.uniform(0.0015, 0.004)
    bmesh.ops.create_icosphere(crumbs, subdivisions=1, radius=r, matrix=Matrix.Translation(c0) @ Euler((random.random() * 3,) * 3).to_matrix().to_4x4())
me = bpy.data.meshes.new("crumbs"); crumbs.to_mesh(me); crumbs.free(); me.materials.append(m_chip)
link(bpy.data.objects.new("crumbs", me))

# ---------------------------------------------------------------- world: hotel room (night, dim blue) / hospital (clinical)
W = bpy.data.worlds.new("world"); S.world = W; W.use_nodes = True; wn = W.node_tree.nodes; wl = W.node_tree.links
envA = wn.new("ShaderNodeTexEnvironment"); envA.image = bpy.data.images.load(os.path.join(ROOT, "assets", "hdri", "hotel_room_2k.hdr")); envA.image.pack()
envB = wn.new("ShaderNodeTexEnvironment"); envB.image = bpy.data.images.load(os.path.join(ROOT, "assets", "hdri", "hospital_room_2k.hdr")); envB.image.pack()
tint = wn.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs["Factor"].default_value = 1.0
tint.inputs["B"].default_value = (0.35, 0.5, 1.0, 1)
wl.new(envA.outputs["Color"], tint.inputs["A"])
mixw = wn.new("ShaderNodeMix"); mixw.data_type = "RGBA"
wl.new(tint.outputs["Result"], mixw.inputs["A"]); wl.new(envB.outputs["Color"], mixw.inputs["B"])
wl.new(mixw.outputs["Result"], wn["Background"].inputs["Color"])
bg = wn["Background"].inputs["Strength"]
for f, fac, st in ((1, 0, 0.12), (RANGE["tweez"][0], 1, 0.6), (RANGE["pull"][1] + 1, 0, 0.12)):
    mixw.inputs["Factor"].default_value = fac; mixw.inputs["Factor"].keyframe_insert("default_value", frame=f)
    bg.default_value = st; bg.keyframe_insert("default_value", frame=f)
set_interp(W.node_tree, "CONSTANT")

# ---------------------------------------------------------------- bedroom lights (night) and clinic lights
head_c = rig.matrix_world @ Vector((0, -0.05, 1.66))
moon = area("moon", head_c + Vector((0.9, 0.5, 1.4)), head_c, 9.0, 1.2, (0.55, 0.68, 1.0), "SQUARE")
warm = point("nightlight", Vector((-0.4, 1.0, MT + 0.45)), 2.5, (1.0, 0.62, 0.32), r=0.05)
facefill = area("facefill", head_c + Vector((0.3, -0.9, 0.35)), head_c, 1.6, 0.8, (0.6, 0.72, 1.0))
clinic = area("clinic_key", EAR + Vector((0.15, -0.25, 0.6)), EAR, 0.0, 0.6, (1.0, 0.98, 0.95))
clinic2 = area("clinic_fill", EAR + Vector((-0.4, 0.3, 0.3)), EAR, 0.0, 0.8, (0.85, 0.92, 1.0))
on_cl, off_cl = RANGE["tweez"][0], RANGE["pull"][1] + 1
key_energy(moon, [(1, 9.0), (on_cl, 0.0), (off_cl, 9.0)])
key_energy(warm, [(1, 2.5), (on_cl, 0.0), (off_cl, 2.5)])
key_energy(facefill, [(1, 1.6), (on_cl, 0.0), (off_cl, 1.6)])
key_energy(clinic, [(1, 0.0), (on_cl, 9.0), (off_cl, 0.0)])
key_energy(clinic2, [(1, 0.0), (on_cl, 5.0), (off_cl, 0.0)])
for o in [duvet, bag, ns, lamp, hb, pillow2] + list(ns.children_recursive) + list(lamp.children_recursive):
    o.hide_render = False; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=on_cl)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=off_cl)

# ================================================================ THE BUG in the bedroom (real size: 2 cm)
dg = bpy.context.evaluated_depsgraph_get()


def surf(x, y, lift=0.0015, z0=1.5):
    hit, loc, nrm, *_ = S.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
    z = loc.z if hit and loc.z > MT - 0.05 else MT
    return Vector((x, y, z + lift))


def curve_from(name, pts):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp_, co in zip(sp.bezier_points, pts):
        bp_.co = co; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
    cu.path_duration = 100
    return link(bpy.data.objects.new(name, cu))


def walk(ob, curve, keys):
    """keys: [(frame, offset 0..1)] along the curve (linear)."""
    ob.location = (0, 0, 0)
    c = ob.constraints.new("FOLLOW_PATH"); c.target = curve; c.use_fixed_location = True; c.use_curve_follow = True
    c.forward_axis = "FORWARD_Y"; c.up_axis = "UP_Z"
    for f, o in keys:
        c.offset_factor = o; c.keyframe_insert("offset_factor", frame=f)
    set_interp(ob, "LINEAR", "constraints")
    return c


# waypoints: pillow corner -> along the pillow -> up over the hair -> onto the ear -> down into the pit
E = EAR
wp = [surf(-0.36, 0.15), surf(-0.3, 0.11), surf(-0.22, 0.07), surf(-0.12, 0.02, 0.002), surf(-0.05, -0.02, 0.002),
      surf(E.x - 0.025, E.y + 0.012, 0.002), surf(E.x - 0.008, E.y + 0.004, 0.0015), E + Vector((0, 0, 0.001)),
      E + CANAL_DIR * 0.012, E + CANAL_DIR * 0.03]
bug_path = curve_from("bug_path", wp)
bug = roach("bug", 0.022, seed=4)
bug["spd"] = 0.75
f_ear_in = F(7.3)
walk(bug, bug_path, [(1, 0.0), (FR["pillow"], 0.12), (FR["ear"], 0.45), (FR["ear"] + 28, 0.8), (FR["ear"] + 48, 0.9), (FR["ear"] + 71, 1.0)])
hide_tree(bug, [(1, RANGE["ear"][1])])
# second bug peeking out of the chips bag at the end (the loop)
bug2 = roach("bug2", 0.03, seed=9); bug2.parent = bag
bug2.location = (0.0, 0.2, 0.005); bug2.rotation_euler = (0.05, 0, 0); bug2.scale = (1 / 1,) * 3
bug2["spd"] = 0.0; bug2["amp"] = 0.0
hide_tree(bug2, [RANGE["end"]])
bug2.rotation_euler = (0, 0, math.radians(200))
bug2.location = (0.01, 0.06, 0.036); bug2.keyframe_insert("location", frame=RANGE["end"][0])
bug2.location = (0.02, 0.0, 0.037); bug2.keyframe_insert("location", frame=RANGE["end"][1])
bug2["spd"] = 0.7; bug2["amp"] = 1.0
bug_fill = area("bug_fill", wp[2] + Vector((0.12, -0.22, 0.25)), wp[3], 1.2, 0.5, (0.8, 0.85, 1.0))
key_energy(bug_fill, [(1, 1.2), (RANGE["ear"][1] + 1, 0.0), (RANGE["end"][0], 0.6)])
# ================================================================ TWEEZERS (clinic): grab the bug out of the canal
m_steel = mat("steel", (0.72, 0.72, 0.74), rough=0.22, metal=1.0)
tw = link(bpy.data.objects.new("tweezers", None))
for s in (-1, 1):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        t = v.co.y + 0.5                         # 0 tip .. 1 back
        w = 0.0018 + 0.0032 * t; th = 0.0009
        v.co = Vector((v.co.x * w + s * (0.0015 + 0.004 * t), -0.055 + t * 0.11, v.co.z * th))
    me = bpy.data.meshes.new(f"blade{s}"); bm.to_mesh(me); bm.free(); me.materials.append(m_steel)
    bl = link(bpy.data.objects.new(f"blade{s}", me)); bl.parent = tw
    bv = bl.modifiers.new("bev", "BEVEL"); bv.width = 0.0004; bv.segments = 2
tw_out = E - CANAL_DIR * 0.05 + Vector((0.0, -0.01, 0.06))
tw_in = E + CANAL_DIR * 0.012
look = (E - tw_out).normalized()


def tw_key(f, pos):
    tw.location = pos; tw.keyframe_insert("location", frame=f)


tw.rotation_euler = (Vector((0, -1, 0))).rotation_difference(look).to_euler()
tw.rotation_euler.rotate_axis("Y", math.radians(90))
tip_off = -look * 0.055
tw_key(RANGE["tweez"][0], tw_out + Vector((0, 0, 0.05)) + tip_off)
tw_key(F(24.6), E - look * 0.004 + tip_off)
tw_key(F(25.3), tw_in + tip_off)
tw_key(F(26.0), tw_in + tip_off)
tw_key(F(27.4), tw_out + tip_off + Vector((0, -0.02, 0.03)))
hide_tree(tw, [(RANGE["tweez"][0], RANGE["pull"][1])])
# the pulled bug: hangs from the tweezer tip, legs kicking
pulled = roach("pulled", 0.022, seed=6); pulled["spd"] = 1.4; pulled["amp"] = 1.2; pulled["ant"] = 1.4
pulled.parent = tw; pulled.location = (0, -0.06, -0.002); pulled.rotation_euler = (math.radians(-90), 0, math.radians(180))
hide_tree(pulled, [(F(25.6), RANGE["pull"][1])])

# ================================================================ CANAL INTERIOR (10x scale, at x=50)
X0C = 50.0; LEN = 0.6; RC = 0.055
canal_pts = [Vector((X0C - 0.05, 0, 0)), Vector((X0C + 0.15, 0.01, 0.012)), Vector((X0C + 0.35, -0.012, 0.0)), Vector((X0C + LEN, 0, -0.006))]
canal_curve = curve_from("canal_axis", canal_pts)
cu = canal_curve.data.copy(); cu.bevel_depth = RC; cu.bevel_resolution = 12; cu.resolution_u = 32; cu.use_fill_caps = False
canal = link(bpy.data.objects.new("canal", cu))
bpy.context.view_layer.objects.active = canal
for o in bpy.context.selected_objects:
    o.select_set(False)
canal.select_set(True); bpy.ops.object.convert(target="MESH"); canal = bpy.context.object
for p in canal.data.polygons:
    p.use_smooth = True
ctx = bpy.data.textures.new("canal_n", "CLOUDS"); ctx.noise_scale = 0.03; ctx.noise_depth = 2
d = canal.modifiers.new("bumps", "DISPLACE"); d.texture = ctx; d.texture_coords = "GLOBAL"; d.strength = -0.012; d.mid_level = 0.5
canal.modifiers.new("sub", "SUBSURF").levels = 1
m_canal = tissue("canal_skin", base=(0.62, 0.34, 0.27), crease=(0.3, 0.12, 0.1), sss=0.4, wet=0.35, bump=0.25, scale=30, veins=0.07)
canal.data.materials.append(m_canal)
# dark flesh shell around the interior set, so no room light leaks into the canal
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.2)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("shell"); bm.to_mesh(me); bm.free(); me.materials.append(mat("shell", (0.02, 0.008, 0.006), rough=0.8))
link(bpy.data.objects.new("canal_shell", me)).location = (X0C + 0.3, 0, 0)
# eardrum: translucent pearly cone closing the canal, umbo pulled inward
bm = bmesh.new()
ctr = bm.verts.new((0.016, 0, 0)); rings = []
for r_i in range(1, 9):
    rr = 0.075 * r_i / 8; ring = []
    for a_i in range(48):
        a = 2 * math.pi * a_i / 48
        ring.append(bm.verts.new((0.016 * (1 - r_i / 8) ** 0.8, rr * math.cos(a), rr * math.sin(a))))
    rings.append(ring)
for a_i in range(48):
    bm.faces.new((ctr, rings[0][a_i], rings[0][(a_i + 1) % 48]))
for k in range(7):
    for a_i in range(48):
        bm.faces.new((rings[k][a_i], rings[k + 1][a_i], rings[k + 1][(a_i + 1) % 48], rings[k][(a_i + 1) % 48]))
me = bpy.data.meshes.new("eardrum"); bm.to_mesh(me); bm.free()
drum = link(bpy.data.objects.new("eardrum", me)); drum.location = canal_pts[-1] + Vector((-0.004, 0, 0))
for p in me.polygons:
    p.use_smooth = True
drum.modifiers.new("sub", "SUBSURF").levels = 2
m_drum = bpy.data.materials.new("eardrum"); m_drum.use_nodes = True; nt = m_drum.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(sp.outputs["Y"], ab.inputs[0])
st = N.new("ShaderNodeMapRange"); st.inputs["From Min"].default_value = 0.006; st.inputs["From Max"].default_value = 0.0
L.new(ab.outputs[0], st.inputs["Value"])                                       # malleus handle: pale streak
zmask = N.new("ShaderNodeMapRange"); zmask.inputs["From Min"].default_value = -0.005; zmask.inputs["From Max"].default_value = 0.03
L.new(sp.outputs["Z"], zmask.inputs["Value"])
mlm = N.new("ShaderNodeMath"); mlm.operation = "MULTIPLY"; L.new(st.outputs["Result"], mlm.inputs[0]); L.new(zmask.outputs["Result"], mlm.inputs[1])
vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = 30
L.new(tc.outputs["Object"], vor.inputs["Vector"])
vr = N.new("ShaderNodeValToRGB"); vr.color_ramp.elements[0].color = (0.5, 0.12, 0.1, 1); vr.color_ramp.elements[1].position = 0.04
vr.color_ramp.elements[1].color = (0.62, 0.58, 0.56, 1); L.new(vor.outputs["Distance"], vr.inputs[0])
cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(mlm.outputs[0], cm.inputs["Factor"]); L.new(vr.outputs["Color"], cm.inputs["A"])
cm.inputs["B"].default_value = (0.92, 0.88, 0.8, 1); L.new(cm.outputs["Result"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.22; b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.08
b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.45)
b.inputs["Subsurface Scale"].default_value = 0.02; b.inputs["Transmission Weight"].default_value = 0.15
me.materials.append(m_drum)
# drum ripples (scratching; big pulse on LOUD)
wvm = drum.modifiers.new("ripple", "WAVE"); wvm.use_x = True; wvm.use_y = False; wvm.use_normal = False
wvm.narrowness = 1.2; wvm.width = 0.02; wvm.speed = 0.004; wvm.use_cyclic = True
wvm.height = 0.0; wvm.keyframe_insert("height", frame=1)
wvm.height = 0.0; wvm.keyframe_insert("height", frame=RANGE["drum"][0])
wvm.height = 0.0025; wvm.keyframe_insert("height", frame=RANGE["drum"][0] + 8)
wvm.height = 0.0025; wvm.keyframe_insert("height", frame=LOUD - 4)
wvm.height = 0.008; wvm.keyframe_insert("height", frame=LOUD)
wvm.height = 0.0; wvm.keyframe_insert("height", frame=LOUD + 20)
# drum backlight (dark shot: red glow through the membrane)
red = point("drum_back", canal_pts[-1] + Vector((0.08, 0, 0)), 0.0, (1.0, 0.1, 0.05), r=0.03)
key_energy(red, [(1, 0.0), (RANGE["dark"][0], 2.5), (RANGE["dark"][1] + 1, 0.0)])
# hairs near the entrance and earwax blobs
hb_ = bmesh.new()
for k in range(420):
    u = random.uniform(0.0, 0.42) ** 1.3
    x = X0C + u * LEN * 0.9; a = random.uniform(0, 2 * math.pi)
    base = Vector((x, (RC - 0.002) * math.cos(a), (RC - 0.002) * math.sin(a)))
    inward = Vector((0, -math.cos(a), -math.sin(a)))
    dirv = (inward * 0.8 + Vector((-0.7, 0, 0)) + Vector([random.uniform(-0.3, 0.3) for _ in range(3)])).normalized()
    ln = random.uniform(0.012, 0.038)
    mtx = Matrix.Translation(base + dirv * ln / 2) @ dirv.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_cone(hb_, cap_ends=False, segments=4, radius1=0.0007, radius2=0.0001, depth=ln, matrix=mtx)
me = bpy.data.meshes.new("canal_hair"); hb_.to_mesh(me); hb_.free()
hair_mat = mat("canal_hair", (0.12, 0.08, 0.05), rough=0.4, coat=0.3, sss=0.2)
me.materials.append(hair_mat); link(bpy.data.objects.new("canal_hair", me))
m_wax = bpy.data.materials.new("earwax"); m_wax.use_nodes = True; bw = m_wax.node_tree.nodes["Principled BSDF"]
bw.inputs["Base Color"].default_value = (0.32, 0.16, 0.035, 1); bw.inputs["Roughness"].default_value = 0.45
bw.inputs["Subsurface Weight"].default_value = 0.6; bw.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.2)
bw.inputs["Subsurface Scale"].default_value = 0.01; bw.inputs["Coat Weight"].default_value = 0.7; bw.inputs["Coat Roughness"].default_value = 0.1
wtx = bpy.data.textures.new("wax_n", "CLOUDS"); wtx.noise_scale = 0.01; wtx.noise_depth = 3
for k in range(9):
    x = X0C + random.uniform(0.06, 0.33); a = random.choice([random.uniform(0.5, 2.6), random.uniform(3.6, 5.8)])
    r = random.uniform(0.008, 0.017)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    me = bpy.data.meshes.new(f"wax{k}"); bm.to_mesh(me); bm.free(); me.materials.append(m_wax)
    for p in me.polygons:
        p.use_smooth = True
    wx = link(bpy.data.objects.new(f"wax{k}", me))
    wx.location = (x, (RC - 0.009) * math.cos(a), (RC - 0.009) * math.sin(a)); wx.scale = (r * 2.2, r * 1.3, r * 0.35)
    wx.rotation_euler = (a + math.pi / 2, 0, 0)
    d = wx.modifiers.new("lumps", "DISPLACE"); d.texture = wtx; d.strength = 1.4; d.texture_coords = "GLOBAL"

# the bug inside (10x: 22 cm)
ib = roach("bug_in", 0.22, seed=4)
ib_path = curve_from("bug_in_path", [p + Vector((0, 0, -RC + 0.01)) for p in canal_pts])
DRUM_OFF = 0.8
walk(ib, ib_path, [(1, 0.0), (RANGE["canal"][0], 0.0), (F(10.6), DRUM_OFF), (RANGE["stuck"][0], DRUM_OFF)])
ib["spd"] = 0.7
keyp(ib, "spd", RANGE["canal"][0], 0.7); keyp(ib, "spd", RANGE["stuck"][0], 1.5); keyp(ib, "spd", RANGE["oil"][0] + 10, 1.5)
keyp(ib, "amp", RANGE["oil"][0] + 18, 1.0); keyp(ib, "amp", RANGE["oil"][1], 0.05)
keyp(ib, "ant", RANGE["stuck"][0], 1.6); keyp(ib, "ant", RANGE["oil"][0] + 18, 1.6); keyp(ib, "ant", RANGE["oil"][1], 0.1)
# small forward-back struggling jitter at the drum
cfp = ib.constraints["Follow Path"]
for f in range(RANGE["stuck"][0], RANGE["scope"][1], 5):
    cfp.offset_factor = DRUM_OFF + random.uniform(-0.012, 0.004); cfp.keyframe_insert("offset_factor", frame=f)
hide_tree(ib, [(RANGE["canal"][0], RANGE["oil"][1])])

# golden oil flooding in from the entrance
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
for v in bm.verts:
    if v.co.x < 0:
        v.co.x = -1.0 - (1 - (v.co.y ** 2 + v.co.z ** 2) ** 0.5) * 0.0     # flat back
me = bpy.data.meshes.new("oil"); bm.to_mesh(me); bm.free()
oil = link(bpy.data.objects.new("oil", me))
for p in me.polygons:
    p.use_smooth = True
oil.scale = (0.3, RC + 0.01, RC + 0.01)
otx = bpy.data.textures.new("oil_w", "CLOUDS"); otx.noise_scale = 0.02
od = oil.modifiers.new("wobble", "DISPLACE"); od.texture = otx; od.strength = 0.01; od.texture_coords = "GLOBAL"
oil.modifiers.new("sub", "SUBSURF").levels = 1
m_oil = liquid("olive_oil", tint=(0.95, 0.62, 0.08), density=3.5, rough=0.03)
m_oil.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.47
me.materials.append(m_oil)
o0, o1 = F(19.9), F(21.0)
for f, xc, sx in ((1, X0C - 0.4, 0.3), (o0, X0C - 0.32, 0.3), (o1, X0C + 0.18, 0.36), (RANGE["oil"][1], X0C + 0.22, 0.36)):
    oil.location = (xc, 0, 0); oil.keyframe_insert("location", frame=f)
    oil.scale = (sx, RC + 0.01, RC + 0.01); oil.keyframe_insert("scale", frame=f)
hide_tree(oil, [RANGE["oil"]])
m_bub = bubble_mat("oil_bubble")
for k in range(16):
    bb = link(bpy.data.objects.new(f"bubble{k}", bpy.data.meshes.new(f"bubble{k}")))
    bmb = bmesh.new(); bmesh.ops.create_uvsphere(bmb, u_segments=16, v_segments=8, radius=1.0); bmb.to_mesh(bb.data); bmb.free()
    for p in bb.data.polygons:
        p.use_smooth = True
    bb.data.materials.append(m_bub); r = random.uniform(0.002, 0.006); bb.scale = (r,) * 3
    st_ = X0C + LEN * DRUM_OFF + random.uniform(-0.08, 0.03)
    p0 = Vector((st_, random.uniform(-0.02, 0.02), -RC + 0.04)); f0 = o1 - 10 + random.randint(0, 30)
    bb.location = p0; bb.keyframe_insert("location", frame=f0)
    bb.location = p0 + Vector((random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01), 0.05)); bb.keyframe_insert("location", frame=f0 + 25)
    show_only(bb, [(max(f0, RANGE["oil"][0]), RANGE["oil"][1])])

# endoscope-style light that travels with each interior camera
def cam_light(cam, energy, col=(1.0, 0.92, 0.85), shot=None):
    lt = point(cam.name + "_lamp", Vector((0.0, 0.01, 0.0)), energy, col, r=0.006, parent=cam)
    if shot:
        key_energy(lt, [(1, 0.0), (RANGE[shot][0], energy), (RANGE[shot][1] + 1, 0.0)])
    return lt


canal_mid = lambda o: ib_path.matrix_world @ Vector((0, 0, 0))

# ================================================================ TRAY (10x, at x=80): mother + babies after removal
X0T = 80.0
bm = bmesh.new()
ring_top = []; ring_bot = []
for i in range(64):
    a = 2 * math.pi * i / 64
    rx = 0.95 * (1 + 0.12 * math.cos(a)); ry = 0.5 * (1 - 0.25 * max(0, math.sin(a)))   # kidney: pinched on one side
    ring_top.append(bm.verts.new((rx * math.cos(a), ry * math.sin(a), 0.14)))
    ring_bot.append(bm.verts.new((rx * 0.82 * math.cos(a), ry * 0.78 * math.sin(a), 0.0)))
for i in range(64):
    j = (i + 1) % 64
    bm.faces.new((ring_bot[i], ring_bot[j], ring_top[j], ring_top[i]))
bm.faces.new(ring_bot[::-1])
me = bpy.data.meshes.new("tray"); bm.to_mesh(me); bm.free()
tray = link(bpy.data.objects.new("kidney_tray", me)); tray.location = (X0T, 0, 0)
sl = tray.modifiers.new("thick", "SOLIDIFY"); sl.thickness = 0.012
bvm = tray.modifiers.new("bev", "BEVEL"); bvm.width = 0.01; bvm.segments = 3
tray.modifiers.new("sub", "SUBSURF").levels = 2
for p in me.polygons:
    p.use_smooth = True
m_tray = mat("tray_steel", (0.75, 0.76, 0.78), rough=0.18, metal=1.0)
m_tray.node_tree.nodes["Principled BSDF"].inputs["Anisotropic"].default_value = 0.6
me.materials.append(m_tray)
drape, _ = img_mat("drape", COT, tint=(0.25, 0.55, 0.55), scale=0.6, bump=0.8)
dr = soft_box("drape", (X0T, 0, -0.02), (4.0, 4.0, 0.02), drape, levels=2, cast=0, wrinkle=0.04, wscale=0.6)
# oil smears in the tray
for k in range(4):
    sm = soft_box(f"smear{k}", (X0T + random.uniform(-0.35, 0.35), random.uniform(-0.15, 0.15), 0.004),
                  (random.uniform(0.08, 0.2), random.uniform(0.05, 0.12), 0.003), m_oil, levels=2, cast=0.6, wrinkle=0)
mom = roach("mother", 0.25, seed=21); mom.location = (X0T + 0.05, 0.02, 0.006); mom.rotation_euler = (0, 0, math.radians(120))
mom["spd"] = 0.35; mom["amp"] = 0.45; mom["ant"] = 0.8
babies = []
for k in range(11):
    nb = roach(f"baby{k}", random.uniform(0.07, 0.095), nymph=True, seed=100 + k)
    a = 2 * math.pi * k / 11 + random.uniform(-0.2, 0.2); r0 = random.uniform(0.12, 0.3)
    p0 = Vector((X0T + 0.05 + r0 * math.cos(a) * 1.4, r0 * math.sin(a) * 0.8, 0.006))
    heading = a + random.uniform(-0.6, 0.6)
    p1 = p0 + Vector((math.cos(heading), math.sin(heading), 0)) * random.uniform(0.12, 0.25)
    nb.rotation_euler = (0, 0, heading - math.pi / 2)
    key(nb, "location", RANGE["tray"][0], p0); key(nb, "location", RANGE["tray"][1], p1)
    set_interp(nb, "LINEAR", "location")
    nb["spd"] = random.uniform(0.9, 1.3)
    babies.append(nb)
area("tray_key", Vector((X0T - 0.3, -0.6, 2.2)), Vector((X0T, 0, 0)), 110, 1.6, (1.0, 0.98, 0.95))
area("tray_rim", Vector((X0T + 1.4, 1.0, 0.8)), Vector((X0T, 0, 0)), 35, 1.2, (0.8, 0.9, 1.0))

# ================================================================ CAMERAS + CUTS
# 1 wide: asleep in bed, bug on the pillow; slow push toward the ear
c1, a1 = camera("C01_wide", head_c + Vector((0.55, -0.95, 0.75)), head_c + Vector((-0.08, -0.05, -0.04)), lens=32, fstop=4.0)
key(c1, "location", RANGE["wide"][0], c1.location.copy()); key(c1, "location", RANGE["wide"][1], head_c + Vector((0.32, -0.62, 0.5)))
# 2 macro on the pillow: bug in focus, the sleeping head soft behind it
c2, a2 = camera("C02_pillow", wp[1] + Vector((-0.07, 0.07, 0.03)), wp[2], lens=60, fstop=4.0, focus=bug)
c2.constraints["Track To"].target = bug
key(c2, "location", RANGE["pillow"][0], c2.location.copy()); key(c2, "location", RANGE["pillow"][1], wp[3] + Vector((-0.07, 0.06, 0.03)))
# 3 ear macro: bug crosses the ear and disappears into the canal
c3, a3 = camera("C03_ear", E + Vector((0.07, -0.09, 0.1)), E + Vector((-0.01, 0, 0)), lens=60, fstop=8.0)
key(c3, "location", RANGE["ear"][0], c3.location.copy()); key(c3, "location", RANGE["ear"][1], E + Vector((0.045, -0.06, 0.07)))
# 4 inside the canal, riding behind the bug
c4, a4 = camera("C04_canal", Vector((0, 0, 0)), Vector((0, 0, 0)), lens=18, fstop=5.6, focus=ib, clip=0.002)
c4.constraints.remove(c4.constraints["Track To"])
c4.parent = ib; c4.location = (0, -0.21, 0.052); c4.rotation_euler = (math.radians(80), 0, 0)
cam_light(c4, 0.05, shot='canal')
# 5 stuck: face to face with the bug, from the eardrum
dpos = canal_pts[-1]
c5, a5 = camera("C05_stuck", dpos + Vector((-0.022, 0.012, 0.034)), dpos + Vector((-0.2, -0.005, -0.04)), lens=16, fstop=5.6, focus=ib, clip=0.002)
cam_light(c5, 0.03, shot='stuck')
# 6 scratching the drum
c6, a6 = camera("C06_drum", dpos + Vector((-0.17, -0.028, 0.03)), dpos + Vector((-0.01, 0.005, -0.022)), lens=20, fstop=5.6, clip=0.002)
key(c6, "location", RANGE["drum"][0], c6.location.copy()); key(c6, "location", RANGE["drum"][1], dpos + Vector((-0.14, -0.025, 0.025)))
cam_light(c6, 0.04, shot='drum')
shake(c6, LOUD - 1, RANGE["drum"][1], 0.0)
# 7 his eyes snap open
eye_c = rig.matrix_world @ Vector((0.0, -0.13, 1.66))
c7, a7 = camera("C07_eyes", eye_c + Vector((0.01, -0.34, 0.03)), eye_c, lens=55, fstop=2.8)
key(c7, "location", RANGE["eyes"][0], c7.location.copy()); key(c7, "location", LOUD - 1, eye_c + Vector((0.01, -0.31, 0.03)))
c7.constraints.remove(c7.constraints["Track To"])
def look_at(cam, target, up):
    z = (cam.location - target).normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x)
    cam.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
look_at(c7, eye_c, (-1, 0, 0)); c7.data.dof.focus_object = a7
shake(c7, LOUD, LOUD + 14, 0.008)
# 8 otoscope: looking down the canal from the entrance, bright ring light
c8, a8 = camera("C08_scope", Vector((X0C - 0.02, 0, 0.004)), dpos, lens=24, fstop=8, clip=0.002)
cam_light(c8, 0.05, (0.95, 0.97, 1.0), shot='scope')
key(c8, "location", RANGE["scope"][0], c8.location.copy()); key(c8, "location", RANGE["scope"][1], Vector((X0C + 0.05, 0, 0.004)))
# 9 oil floods in, seen from the drum
c9, a9 = camera("C09_oil", dpos + Vector((-0.022, -0.012, 0.034)), Vector((X0C + 0.15, 0, -0.03)), lens=16, fstop=8, clip=0.002)
cam_light(c9, 0.03, shot='oil')
key_energy(point("oil_glow", Vector((X0C + 0.02, 0, 0)), 0.15, (1.0, 0.85, 0.6), r=0.02), [(1, 0.0), (RANGE["oil"][0], 0.15), (RANGE["oil"][1] + 1, 0.0)])
# 10 "not even the worst": slow push into the dark canal, drum glowing red
c10, a10 = camera("C10_dark", Vector((X0C + 0.02, 0, 0.0)), dpos, lens=24, fstop=8, clip=0.002)
key(c10, "location", RANGE["dark"][0], c10.location.copy()); key(c10, "location", RANGE["dark"][1], Vector((X0C + 0.25, 0, 0)))
# 11-12 clinic: tweezers go in, pull the bug out
c11, a11 = camera("C11_tweez", E + Vector((0.05, -0.12, 0.11)), E + Vector((0.0, -0.005, 0.01)), lens=50, fstop=4.0)
key(c11, "location", RANGE["tweez"][0], c11.location.copy()); key(c11, "location", RANGE["tweez"][1], E + Vector((0.04, -0.1, 0.09)))
c12, a12 = camera("C12_pull", E + Vector((0.09, -0.16, 0.12)), E + Vector((0.0, -0.02, 0.035)), lens=40, fstop=4.0, focus=pulled)
c12.constraints["Track To"].target = pulled
# 13 the tray
c13, a13 = camera("C13_tray", Vector((X0T - 0.2, -0.75, 0.6)), Vector((X0T + 0.05, 0.0, 0.02)), lens=45, fstop=2.8)
key(c13, "location", RANGE["tray"][0], c13.location.copy()); key(c13, "location", RANGE["tray"][1], Vector((X0T - 0.15, -0.6, 0.48)))
# 14 back in bed: chips by his face, a bug peeking out of the bag; settles into shot 1's framing
c14, a14 = camera("C14_end", head_c + Vector((0.2, -0.75, 0.45)), Vector((-0.1, -0.3, MT + 0.05)), lens=40, fstop=3.5)
key(c14, "location", RANGE["end"][0], c14.location.copy()); key(c14, "location", RANGE["end"][1], head_c + Vector((0.42, -0.85, 0.62)))
key(a14, "location", RANGE["end"][0], a14.location.copy()); key(a14, "location", RANGE["end"][1], head_c + Vector((-0.06, -0.08, -0.02)))

for nm, cam in (("wide", c1), ("pillow", c2), ("ear", c3), ("canal", c4), ("stuck", c5), ("drum", c6), ("eyes", c7),
                ("scope", c8), ("oil", c9), ("dark", c10), ("tweez", c11), ("pull", c12), ("tray", c13), ("end", c14)):
    cut(T[nm], cam)
S.camera = c1
for cam in CAMS.values():
    set_interp(cam, "BEZIER")

out = os.path.join(ROOT, "scenes", "ear", "ear.blend")
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("EAR READY", out, "frames", S.frame_end, {k: RANGE[k] for k in RANGE})
