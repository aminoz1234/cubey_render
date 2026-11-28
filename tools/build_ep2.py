"""Episode 2 'The Balloon': two friends on a morning run in a park. python3 build_ep2.py OUT.blend PUPDIR
PUPDIR holds <who>/head/####.webp and headmeta.json; rig art from kit/ep2/rig. Dialogue timing from ep2vo/lines.json."""
import bpy, math, os, sys, json, random, itertools
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig2, iphone
OUT, PUPA = os.path.abspath(sys.argv[-2]), os.path.abspath(sys.argv[-1])
CITY = f"{HERE}/KayKit-City-Builder-Bits-1.0/addons/kaykit_city_builder_bits/Assets/gltf"
LINES = json.load(open("/home/claude/work/ep2vo/lines.json"))["lines"]
FPS = 30; NFR = int(math.ceil((LINES[-1]["t1"] + 0.7) * FPS))
F = lambda t: int(round(t * FPS)) + 1
R = math.radians
bpy.ops.wm.read_factory_settings(use_empty=True); S = bpy.context.scene
def key(o, path, val, f): setattr(o, path, val); o.keyframe_insert(path, frame=f)
def word_t(who, needle, which=0):
    hits = [w for l in LINES if l["who"] == who for w in l["words"] if needle in w[2].lower()]; return hits[which]

# ------------------------------------------------------------ materials / helpers
def mmat(name, col, rough=0.5, emit=0.0, alpha=None, spec=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    if alpha is not None: b.inputs["Alpha"].default_value = alpha
    if spec is not None: b.inputs["Specular IOR Level"].default_value = spec
    return m
def obj_from(op, name, **kw): op(**kw); o = bpy.context.active_object; o.name = name; return o
def smooth(o):
    for p in o.data.polygons: p.use_smooth = True
    return o
def imp(name, loc=(0, 0, 0), rot=0.0, scale=1.0):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f"{CITY}/{name}.gltf")
    new = [o for o in bpy.data.objects if o not in before]; roots = [o for o in new if o.parent not in new]
    if len(roots) > 1:
        e = bpy.data.objects.new(name, None); S.collection.objects.link(e)
        for o in roots: o.parent = e
        root = e
    else: root = roots[0]
    root.location = Vector(loc); root.rotation_mode = "XYZ"; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3; root["kit"] = f"{name}_{len(bpy.data.objects)}"
    for o in new:
        if o.type == "MESH": o["kit"] = root["kit"]
    return root

# ------------------------------------------------------------ the park (path runs along y; the friends run toward -y, the camera leads them)
Y0, Y1 = 22.0, -95.0
grass = obj_from(bpy.ops.mesh.primitive_plane_add, "grass", size=1, location=(0, (Y0 + Y1) / 2, 0)); grass.scale = (80, Y0 - Y1 + 60, 1)
gm = bpy.data.materials.new("grass_m"); gm.use_nodes = True; nt = gm.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.9
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (0.16, 0.42, 0.12, 1); rp.color_ramp.elements[1].color = (0.36, 0.62, 0.2, 1); tc = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], b.inputs["Base Color"])
grass.data.materials.append(gm); grass["kit"] = "floor_grass"
PW = 2.8
path = obj_from(bpy.ops.mesh.primitive_plane_add, "path", size=1, location=(0, (Y0 + Y1) / 2, 0.006)); path.scale = (PW, Y0 - Y1, 1)
pm = bpy.data.materials.new("path_m"); pm.use_nodes = True; nt = pm.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.85
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (0.62, 0.5, 0.36, 1); rp.color_ramp.elements[1].color = (0.8, 0.69, 0.52, 1); tc = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], b.inputs["Base Color"])
path.data.materials.append(pm); path["kit"] = "floor_path"
for sx in (-1, 1):   # low stone edging along the path
    ed = obj_from(bpy.ops.mesh.primitive_cube_add, f"edge{sx}", size=1, location=(sx * (PW / 2 + 0.05), (Y0 + Y1) / 2, 0.04)); ed.scale = (0.1, Y0 - Y1, 0.08)
    ed.data.materials.append(mmat("edge_m", (0.72, 0.7, 0.66), 0.8)); ed["kit"] = "floor_edge"

LEAF = [mmat(f"leaf{i}", c, 0.8) for i, c in enumerate(((0.17, 0.48, 0.16), (0.24, 0.58, 0.18), (0.32, 0.66, 0.2), (0.86, 0.55, 0.22)))]
BARK = mmat("bark", (0.36, 0.22, 0.13), 0.85)
rnd = random.Random(4)
def tree(name, x, y, s=1.0, autumn=False):
    e = bpy.data.objects.new(name, None); S.collection.objects.link(e); e.location = (x, y, 0); e["kit"] = "trees"; name_kit = "trees"
    h = (2.0 + rnd.uniform(0, 0.9)) * s
    t = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_trunk", radius=0.16 * s, depth=h, vertices=10, location=(x, y, h / 2)); t.data.materials.append(BARK); t.parent = e
    t.matrix_parent_inverse = e.matrix_world.inverted(); t["kit"] = "trees"
    for i in range(rnd.randint(3, 4)):
        r = (0.9 + rnd.uniform(0, 0.5)) * s; dx, dy = rnd.uniform(-0.5, 0.5) * s, rnd.uniform(-0.5, 0.5) * s; dz = h + rnd.uniform(-0.2, 0.9) * s
        b_ = obj_from(bpy.ops.mesh.primitive_ico_sphere_add, f"{name}_crown{i}", radius=r, subdivisions=2, location=(x + dx, y + dy, dz))
        b_.data.materials.append(LEAF[3] if (autumn and i == 0) else LEAF[rnd.randint(0, 2)]); b_.parent = e; b_.matrix_parent_inverse = e.matrix_world.inverted(); b_["kit"] = "trees"
    return e
# trees both sides, clear of the path; denser near the camera's travel
for side in (-1, 1):
    y = Y0
    while y > Y1:
        x = side * (PW / 2 + rnd.uniform(2.2, 7.5)); tree(f"tree_{side}_{int(y*10)}", x, y, rnd.uniform(0.9, 1.25), autumn=rnd.random() < 0.18)
        if rnd.random() < 0.5: tree(f"treeb_{side}_{int(y*10)}", side * (PW / 2 + rnd.uniform(9, 16)), y + rnd.uniform(-2, 2), rnd.uniform(1.1, 1.5))
        y -= rnd.uniform(3.5, 6.5)
# bushes hugging the edging, streetlights, benches
LAMP_Y = [(1 if i % 2 else -1, y) for i, y in enumerate(range(9, int(Y1), -14))]
BENCHES = [(1, 0.6), (-1, -26), (-1, -58)]
for side in (-1, 1):
    y = Y0 - 1
    while y > Y1:
        if any(sd == side and abs(y - yy) < 1.6 for sd, yy in LAMP_Y + BENCHES): y -= 1.0; continue
        bu = imp("bush", (side * (PW / 2 + 0.55 + rnd.uniform(0, 0.3)), y, 0), rnd.uniform(0, 360), rnd.uniform(2.6, 3.4)); y -= rnd.uniform(2.5, 5)
        for o in [bu] + list(bu.children_recursive): o["kit"] = "bushes"
for i, y in enumerate(range(9, int(Y1), -14)):
    sd = 1 if i % 2 else -1; imp("streetlight", (sd * (PW / 2 + 0.45), y, 0), 90 if sd > 0 else -90, 3.4)
BENCH_Y = 0.6
imp("bench", (PW / 2 + 0.75, BENCH_Y, 0), 90, 3.6)
for y in (-26, -58): imp("bench", (-(PW / 2 + 0.75), y, 0), -90, 3.6)
# distant city behind the park (the camera looks back along +y)
for i, x in enumerate(range(-36, 40, 12)):
    imp(rnd.choice(["building_A", "building_B", "building_C", "building_E", "building_F", "building_G", "building_H"]), (x, Y0 + 26 + (i % 2) * 7, 0), 180, rnd.uniform(4.0, 5.2))

# ------------------------------------------------------------ the bin Jess dumps the smoothie in
def bin_(name, x, y):
    g = obj_from(bpy.ops.mesh.primitive_cylinder_add, name, radius=0.3, depth=0.95, vertices=40, location=(x, y, 0.475)); smooth(g)
    import bmesh; bm = bmesh.new(); bm.from_mesh(g.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context="FACES"); bm.to_mesh(g.data); bm.free()
    sol = g.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.03
    g.data.materials.append(mmat("bin_m", (0.13, 0.36, 0.22), 0.45)); g["kit"] = name
    rim = obj_from(bpy.ops.mesh.primitive_torus_add, name + "_rim", major_radius=0.3, minor_radius=0.035, location=(x, y, 0.95)); rim.data.materials.append(mmat("bin_rim", (0.08, 0.2, 0.12), 0.4)); rim["kit"] = name
    inner = obj_from(bpy.ops.mesh.primitive_circle_add, name + "_in", vertices=40, radius=0.27, fill_type="NGON", location=(x, y, 0.8)); inner.data.materials.append(mmat("bin_in", (0.02, 0.03, 0.02), 0.9)); inner["kit"] = name
    return g

# ------------------------------------------------------------ props
def smoothie_cup(name):
    c = obj_from(bpy.ops.mesh.primitive_cone_add, name, radius1=0.052, radius2=0.07, depth=0.19, vertices=40, location=(0, 0, 0)); smooth(c)
    nt_ = (m := bpy.data.materials.new("smoothie_m")); m.use_nodes = True; bb_ = m.node_tree.nodes["Principled BSDF"]
    gr_ = m.node_tree.nodes.new("ShaderNodeTexGradient"); tcc = m.node_tree.nodes.new("ShaderNodeTexCoord"); rr = m.node_tree.nodes.new("ShaderNodeValToRGB"); sep = m.node_tree.nodes.new("ShaderNodeSeparateXYZ")
    m.node_tree.links.new(tcc.outputs["Generated"], sep.inputs[0]); m.node_tree.links.new(sep.outputs["Z"], rr.inputs[0])
    rr.color_ramp.elements[0].color = (0.98, 0.52, 0.03, 1); rr.color_ramp.elements[1].color = (1.0, 0.78, 0.2, 1); m.node_tree.links.new(rr.outputs[0], bb_.inputs["Base Color"]); bb_.inputs["Roughness"].default_value = 0.35
    c.data.materials.append(m)
    lid = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, name + "_lid", radius=0.071, segments=32, ring_count=12, location=(0, 0, 0.095)); smooth(lid)
    import bmesh; bm = bmesh.new(); bm.from_mesh(lid.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS"); bm.to_mesh(lid.data); bm.free()
    lid.scale = (1, 1, 0.55); lid.data.materials.append(mmat("lid_m", (0.95, 0.97, 1.0), 0.1, alpha=0.35, spec=0.6)); lid.parent = c
    ring = obj_from(bpy.ops.mesh.primitive_torus_add, name + "_ring", major_radius=0.071, minor_radius=0.006, location=(0, 0, 0.095)); ring.data.materials.append(mmat("ring_m", (1, 1, 1), 0.3)); ring.parent = c
    st = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_straw", radius=0.009, depth=0.2, vertices=12, location=(0.012, 0, 0.17)); st.rotation_euler = (0, R(10), 0)
    st.data.materials.append(mmat("straw_m", (1.0, 0.3, 0.55), 0.4)); st.parent = c
    band = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_sleeve", radius=0.0625, depth=0.06, vertices=40, location=(0, 0, 0.0)); smooth(band); band.scale = (1, 1, 1)
    band.data.materials.append(mmat("sleeve_m", (0.98, 0.95, 0.88), 0.6)); band.parent = c
    return c

def phone(name, screen_col=(0.0, 1.0, 0.0), emit=1.0): return iphone.build(name, screen_col=screen_col, screen_emit=emit)

# ------------------------------------------------------------ light: low morning sun in front of the runners, warm sky
w = S.world = bpy.data.worlds.new("sky"); w.use_nodes = True; wn = w.node_tree
sky = wn.nodes.new("ShaderNodeTexSky")
try: sky.sky_type = "NISHITA"; sky.sun_elevation = R(14); sky.sun_rotation = R(200)
except Exception: pass
wn.links.new(sky.outputs[0], wn.nodes["Background"].inputs[0]); wn.nodes["Background"].inputs[1].default_value = 0.35
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); S.collection.objects.link(sun)
sun.data.energy = 3.4; sun.data.color = (1.0, 0.8, 0.58); sun.data.angle = R(3); sun.rotation_euler = (R(70), 0, R(20))
fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN")); S.collection.objects.link(fill)
fill.data.energy = 0.6; fill.data.color = (0.7, 0.8, 1.0); fill.rotation_euler = (R(60), 0, R(200)); fill.data.angle = R(20)

def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); S.collection.objects.link(e); e.location = loc; e.empty_display_size = 0.05; return e
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); S.collection.objects.link(cam); S.camera = cam
cam.data.lens = 26; cam.data.sensor_width = 36; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8
tgt = empty("cam_target"); tc_ = cam.constraints.new("TRACK_TO"); tc_.target = tgt; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
cam.data.dof.focus_object = tgt; cam.data.clip_end = 300
S.render.resolution_x, S.render.resolution_y = 1080, 1920; S.render.fps = FPS; S.frame_start = 1; S.frame_end = NFR
S.view_settings.view_transform = "AgX"; S.view_settings.look = "AgX - Punchy"
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5; S.render.engine = "CYCLES"

# ------------------------------------------------------------ clash check for the set (real triangles)
def bb(o):
    pts = [m.matrix_world @ Vector(c) for m in [o] for c in m.bound_box]; return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
def bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
    v = [mw @ x.co for x in me.vertices]; f = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear(); return BVHTree.FromPolygons(v, f)
def clash_report():
    bpy.context.view_layer.update()
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.get("kit") and not str(o["kit"]).startswith("floor")]
    boxes = {o: bb(o) for o in objs}; trees = {}; bad = []
    for a, b_ in itertools.combinations(objs, 2):
        if a["kit"] == b_["kit"]: continue
        (amn, amx), (bmn, bmx) = boxes[a], boxes[b_]
        if any(min(amx[i], bmx[i]) - max(amn[i], bmn[i]) <= 0.002 for i in range(3)): continue
        ta = trees.setdefault(a, bvh(a)); tb = trees.setdefault(b_, bvh(b_))
        if ta.overlap(tb): bad.append((a.name, b_.name))
    return bad

# ------------------------------------------------------------ characters
HM = json.load(open(f"{PUPA}/headmeta.json")); ARTD = os.path.join(HERE, "ep2", "rig")
X = {"nora": 0.55, "jess": -0.55}
RIG = {w_: rig2.build(w_, (X[w_], 0, 0), ARTD, f"{PUPA}/{w_}/head", HM[w_], cam, frames=NFR) for w_ in ("nora", "jess")}
nora, jess = RIG["nora"], RIG["jess"]
for who, r in RIG.items():
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.3, fill_type="NGON", location=(0, 0, 0.012)); sh = bpy.context.active_object; sh.name = f"{who}_contact"
    sh.scale = (1.2, 0.6, 1); cl = sh.constraints.new("COPY_LOCATION"); cl.target = r["arm"]; cl.use_z = False
    sm = bpy.data.materials.new(f"{who}_contact_m"); sm.use_nodes = True; nt = sm.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial"); mx = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs[0].default_value = (0.02, 0.015, 0.02, 1); grd = nt.nodes.new("ShaderNodeTexGradient"); grd.gradient_type = "SPHERICAL"; tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3.3, 3.3, 3.3)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], grd.inputs[0]); nt.links.new(grd.outputs[1], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(df.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs[0])
    sh.data.materials.append(sm); sh.visible_shadow = False

def grip_world(r, sd, axis_deg):
    arm = r["arm"]; g = r["grip"][sd]
    return arm.matrix_world @ (Matrix.Translation(g) @ Euler((0, R(axis_deg), 0)).to_matrix().to_4x4() @ Matrix.Diagonal((1, 0.08, 1, 1)))
def holders(obj, spans):
    bpy.context.view_layer.update(); T = obj.matrix_world.copy()
    for i, (r, sd, axis, t0, t1) in enumerate(spans):
        arm = r["arm"]; c = obj.constraints.new("CHILD_OF"); c.name = f"hold{i}"; c.target = arm; c.subtarget = f"hand.{sd}"
        bone_rest = arm.matrix_world @ arm.data.bones[f"hand.{sd}"].matrix_local
        c.inverse_matrix = bone_rest.inverted() @ grip_world(r, sd, axis) @ T.inverted(); c.set_inverse_pending = False
        for f, v in ((1, 0.0), (F(t0) - 1, 0.0), (F(t0), 1.0), (F(t1), 1.0), (F(t1) + 1, 0.0)):
            if f < 1: continue
            c.influence = v; c.keyframe_insert("influence", frame=f)
    for fc in rig2.all_fcurves(obj.animation_data.action):
        if "influence" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
def pop(o, t_in=None, t_out=None, dur=0.18):
    s1 = o.scale.copy()
    if t_in is not None: key(o, "scale", s1 * 0.0, max(1, F(t_in) - 1)); key(o, "scale", s1 * 0.0, F(t_in)); key(o, "scale", s1 * 1.15, F(t_in + dur * 0.6)); key(o, "scale", s1, F(t_in + dur))
    if t_out is not None: key(o, "scale", s1, F(t_out)); key(o, "scale", s1 * 0.0, F(t_out + dur))

bpy.context.view_layer.update()
exec(open(os.path.join(HERE, "ep2_keys.py")).read())

bad = clash_report(); print("CLASHES", len(bad)); [print("  ", a, "x", b_) for a, b_ in bad[:20]]

# ------------------------------------------------------------ phone screen corners per frame (real Cubey screens are composited locally)
from bpy_extras.object_utils import world_to_camera_view
corners = {}
for f in range(1, NFR + 1):
    S.frame_set(f)
    for body in SCREENS:
        if body.hide_render or body.matrix_world.to_scale().length < 1e-3: continue
        pts = []
        for wp in iphone.screen_rect_world(body):
            p = world_to_camera_view(S, cam, wp); pts.append((round(p.x * 1080, 2), round((1 - p.y) * 1920, 2), round(p.z, 3)))
        mw = body.matrix_world; n = (mw.to_3x3() @ Vector((0, -1, 0))).normalized(); facing = n.dot((cam.matrix_world.translation - mw.translation).normalized())
        if facing > 0.1 and all(z > 0 for *_, z in pts): corners[f] = [q[:2] for q in pts]; break
json.dump(corners, open(OUT.replace(".blend", "_phone_corners.json"), "w")); print("phone frames", len(corners))
S.frame_set(1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True); print("saved", OUT)
import subprocess
rc = subprocess.run([sys.executable, os.path.join(HERE, "motion_check.py"), OUT]).returncode
print("MOTION CHECK", "PASSED" if rc == 0 else "FAILED: do not render")
