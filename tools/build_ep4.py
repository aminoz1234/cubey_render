"""Episode 4 'Crosswalk': two couples, the girls collide mid-crosswalk and roast each other; Devin scans both drinks with Cubey.
OLD: Episode 3 'Plate Three': Thanksgiving dinner. Two big uncles eat, Marcus (the tall gym nephew) scans their plates with Cubey.
python3 build_ep3.py OUT.blend PUPDIR   (PUPDIR holds <who>/head/####.webp + headmeta.json; rig art in kit/ep3/rig; timing from ep3vo/lines.json)"""
import bpy, math, os, sys, json, random, itertools, bmesh
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig2, iphone
OUT, PUPA = os.path.abspath(sys.argv[-2]), os.path.abspath(sys.argv[-1])
RB = f"{HERE}/KayKit-Restaurant-Bits-1.0/addons/kaykit_restaurant_bits/Assets/gltf"
FB = f"{HERE}/KayKit-Furniture-Bits-1.0/addons/kaykit_furniture_bits/Assets/gltf"
CB = f"{HERE}/KayKit-City-Builder-Bits-1.0/addons/kaykit_city_builder_bits/Assets/gltf"
LINES = json.load(open("/home/claude/work/ep4vo/lines.json"))["lines"]
FPS = 30; NFR = int(math.ceil((LINES[-1]["t1"] + 0.7) * FPS))
F = lambda t: int(round(t * FPS)) + 1
R = math.radians
bpy.ops.wm.read_factory_settings(use_empty=True); S = bpy.context.scene
def key(o, path, val, f): setattr(o, path, val); o.keyframe_insert(path, frame=f)
def word_t(who, needle, which=0):
    hits = [w for l in LINES if l["who"] == who for w in l["words"] if needle in w[2].lower()]; return hits[which]

def mmat(name, col, rough=0.5, emit=0.0, alpha=None, spec=None, sss=None):
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
def tag(o, k):
    for m in [o] + list(o.children_recursive): m["kit"] = k
    return o
def imp(path, name, loc=(0, 0, 0), rot=0.0, scale=(1, 1, 1)):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; roots = [o for o in new if o.parent not in new]
    if len(roots) > 1:
        e = bpy.data.objects.new(name, None); S.collection.objects.link(e)
        for o in roots: o.parent = e
        root = e
    else: root = roots[0]
    root.name = name; root.location = Vector(loc); root.rotation_mode = "XYZ"; root.rotation_euler = (0, 0, R(rot)); root.scale = scale
    tag(root, name); return root

# ------------------------------------------------------------ golden-hour street (camera on -y, road runs along y, the crosswalk crosses it along x)
# palette: amber #f8a51a, peach #ffcf73, espresso #50312f, navy #1f2833, cream #fdf3d0, teal #2a9d8f, dusty rose #d97b8f, lavender #b8a1d9
def hexc(h): h = h.lstrip("#"); return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))
ASPH = bpy.data.materials.new("asphalt"); ASPH.use_nodes = True; nt = ASPH.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.85
ns = nt.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 60; rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (*hexc("#2b2f3a"), 1); rp.color_ramp.elements[1].color = (*hexc("#454a57"), 1); nt.links.new(ns.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], b.inputs["Base Color"])
road = obj_from(bpy.ops.mesh.primitive_plane_add, "road", size=1, location=(0, 8, 0)); road.scale = (7.0, 60, 1); road.data.materials.append(ASPH); road["kit"] = "floor_road"
WALKM = mmat("sidewalk_m", hexc("#cdbfae"), 0.8); CURB = mmat("curb_m", hexc("#e6dccd"), 0.7)
for sx in (-1, 1):
    sw = obj_from(bpy.ops.mesh.primitive_cube_add, f"sidewalk{sx}", size=1, location=(sx * 6.0, 8, 0.07)); sw.scale = (5.0, 60, 0.14); sw.data.materials.append(WALKM); sw["kit"] = "floor_sw"
    cb = obj_from(bpy.ops.mesh.primitive_cube_add, f"curb{sx}", size=1, location=(sx * 3.55, 8, 0.08)); cb.scale = (0.12, 60, 0.16); cb.data.materials.append(CURB); cb["kit"] = "floor_curb"
    for i in range(22):     # sidewalk slab joints
        j = obj_from(bpy.ops.mesh.primitive_cube_add, f"joint{sx}_{i}", size=1, location=(sx * 6.0, -6 + i * 1.4, 0.141)); j.scale = (5.0, 0.03, 0.002); j.data.materials.append(mmat("joint_m", hexc("#a99a88"), 0.9)); j["kit"] = "floor_joint"
PAINT = mmat("paint_m", hexc("#f4efe4"), 0.6)
for i in range(12):        # zebra bars, long in the direction of traffic
    x = -3.05 + i * 0.555; z = obj_from(bpy.ops.mesh.primitive_cube_add, f"zebra{i}", size=1, location=(x, 0.25, 0.004)); z.scale = (0.32, 2.4, 0.006); z.data.materials.append(PAINT); z["kit"] = "floor_zebra"
for sx in (-1, 1):
    ln = obj_from(bpy.ops.mesh.primitive_cube_add, f"stopline{sx}", size=1, location=(sx * 1.6, 1.85 if sx > 0 else -1.35, 0.004)); ln.scale = (3.2, 0.18, 0.006); ln.data.materials.append(PAINT); ln["kit"] = "floor_line"
for i in range(10):
    d = obj_from(bpy.ops.mesh.primitive_cube_add, f"dash{i}", size=1, location=(0, 4 + i * 4.0, 0.004)); d.scale = (0.12, 1.8, 0.006); d.data.materials.append(mmat("yellow_m", hexc("#f8c64a"), 0.6)); d["kit"] = "floor_dash"
# buildings: two rows facing the street, plus a far wall of them down the road
BLD = ["building_A", "building_B", "building_C", "building_D", "building_E", "building_F", "building_G", "building_H"]
rnd = random.Random(4)
for sx in (-1, 1):
    for i in range(4):
        n = BLD[(i * 3 + (sx > 0) * 2) % len(BLD)]; y = -4 + i * 11.0
        imp(f"{CB}/{n}_withoutBase.gltf", f"bld{sx}_{i}", (sx * 12.6, y, 0.14), 90 if sx < 0 else -90, (5.4, 5.4, 5.4 * rnd.uniform(0.95, 1.2)))
for i, x in enumerate((-12.5, -0.3, 12.0)):
    imp(f"{CB}/{BLD[(i * 5) % 8]}_withoutBase.gltf", f"bldfar{i}", (x, 46, 0.0), 180, (6, 6, 7))
for sx in (-1, 1):
    for i in range(5):
        imp(f"{CB}/streetlight.gltf", f"streetlight{sx}_{i}", (sx * 4.0, 5.5 + i * 7.5, 0.14), 0 if sx < 0 else 180, (5, 5, 5))
    imp(f"{CB}/trafficlight_A.gltf", f"trafficlight{sx}", (sx * 3.95, 2.3 if sx > 0 else -1.6, 0.14), 90 if sx < 0 else -90, (4.6, 4.6, 4.6))
    for i in range(6): imp(f"{CB}/bush.gltf", f"bush{sx}_{i}", (sx * 6.6, 3 + i * 3.7, 0.14), rnd.uniform(0, 360), (4, 4, 4))
imp(f"{CB}/firehydrant.gltf", "hydrant", (4.3, -0.9, 0.14), 0, (3.4, 3.4, 3.4))
taxi = imp(f"{CB}/car_taxi.gltf", "taxi", (1.6, 30, 0.25), 180, (4.8, 4.8, 4.8))
for i, (n, x, y) in enumerate((("car_sedan", -1.7, 14), ("car_hatchback", -1.7, 22), ("car_stationwagon", 1.6, 40))):
    imp(f"{CB}/{n}.gltf", f"car{i}", (x, y, 0.25), 0 if x < 0 else 180, (4.8, 4.8, 4.8))

# ------------------------------------------------------------ golden hour: low warm sun behind-left, teal sky fill from the right, peach-to-lavender sky
w = S.world = bpy.data.worlds.new("sky"); w.use_nodes = True; nt = w.node_tree; bg = nt.nodes["Background"]
sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA" if "NISHITA" in [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items] else sky.bl_rna.properties["sky_type"].enum_items[0].identifier
try:
    sky.sun_elevation = R(4.5); sky.sun_rotation = R(140); sky.air_density = 1.6; sky.dust_density = 2.5
except Exception: pass
grd = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
# world Generated Z runs 0 (straight down) .. 1 (straight up): the horizon is at 0.5
ramp.color_ramp.elements[0].position = 0.5; ramp.color_ramp.elements[0].color = (*hexc("#ffc27a"), 1); ramp.color_ramp.elements[1].position = 0.92; ramp.color_ramp.elements[1].color = (*hexc("#6f9fd0"), 1)
for pos, col in ((0.55, "#ff9e7a"), (0.63, "#f29aa8"), (0.74, "#b8a1d9")): e3 = ramp.color_ramp.elements.new(pos); e3.color = (*hexc(col), 1)
nt.links.new(grd.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["Factor"].default_value = 0.85
nt.links.new(sky.outputs["Color"], mix.inputs["A"]); nt.links.new(ramp.outputs["Color"], mix.inputs["B"]); nt.links.new(mix.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
def light(name, kind, loc, energy, col, size=None, rot=(0, 0, 0)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); S.collection.objects.link(l); l.location = loc; l.rotation_euler = rot; l.data.energy = energy; l.data.color = col
    if size is not None:
        if kind == "AREA": l.data.size = size
        elif kind == "SUN": l.data.angle = size
        else: l.data.shadow_soft_size = size
    return l
sun = light("sun", "SUN", (0, 0, 10), 4.2, (1.0, 0.68, 0.38), R(2.5), (R(82), 0, R(-140)))     # low, warm, from behind-left: long shadows + warm rims
light("teal_fill", "AREA", (5.5, -5.0, 3.0), 650, (0.42, 0.78, 0.86), 6.0, (R(65), 0, R(48)))    # cool fill from the sky side
light("face_fill", "AREA", (-2.5, -5.5, 2.4), 420, (1.0, 0.8, 0.62), 4.0, (R(70), 0, R(-25)))    # soft warm bounce on faces

def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); S.collection.objects.link(e); e.location = loc; e.empty_display_size = 0.05; return e
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); S.collection.objects.link(cam); S.camera = cam
cam.data.lens = 26; cam.data.sensor_width = 36; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.4
tgt = empty("cam_target"); tc_ = cam.constraints.new("TRACK_TO"); tc_.target = tgt; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
cam.data.dof.focus_object = tgt; cam.data.clip_end = 200; cam.data.clip_start = 0.02
S.render.resolution_x, S.render.resolution_y = 1080, 1920; S.render.fps = FPS; S.frame_start = 1; S.frame_end = NFR
S.view_settings.view_transform = "AgX"; S.view_settings.look = "AgX - Punchy"; S.view_settings.exposure = 0.0
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5; S.render.engine = "CYCLES"
# ------------------------------------------------------------ clash check for the set (real triangles)
def bb(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]; return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
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
HM = json.load(open(f"{PUPA}/headmeta.json")); ARTD = os.path.join(HERE, "ep4", "rig")
WHO = ("kayla", "tasha", "devin", "josh")
POS = {"kayla": (-0.42, 0.05, 0.0), "tasha": (0.42, 0.12, 0.0), "josh": (-1.05, 0.55, 0.0), "devin": (1.05, 0.6, 0.0)}
SCALE = {"kayla": 1.3, "tasha": 1.3, "devin": 1.33, "josh": 1.33}
RIG = {w_: rig2.build(w_, POS[w_], ARTD, f"{PUPA}/{w_}/head", HM[w_], cam, scale=SCALE[w_], frames=NFR) for w_ in WHO}
kayla, tasha, devin, josh = (RIG[w_] for w_ in WHO)
SHAD = {}
for who in WHO:
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.28, fill_type="NGON", location=(0, 0, 0.006)); sh = bpy.context.active_object; sh.name = f"{who}_contact"
    sh.scale = (1.3, 0.6, 1); cl = sh.constraints.new("COPY_LOCATION"); cl.target = RIG[who]["arm"]; cl.use_z = False
    sh.data.materials.append(mmat(f"contact_{who}", (0.02, 0.015, 0.03), 0.9, alpha=0.4)); sh.visible_shadow = False; SHAD[who] = sh

def grip_world(r, sd, axis_deg):
    arm = r["arm"]; g = r["grip"][sd]
    return arm.matrix_world @ (Matrix.Translation(g) @ Euler((0, R(axis_deg), 0)).to_matrix().to_4x4() @ Matrix.Diagonal((1, 0.08, 1, 1)))
def holders(obj, spans):
    bpy.context.view_layer.update(); T = obj.matrix_world.copy()
    for i, (r, sd, axis, t0, t1) in enumerate(spans):
        S.frame_set(max(1, F(t0))); bpy.context.view_layer.update()
        arm = r["arm"]; c = obj.constraints.new("CHILD_OF"); c.name = f"hold{i}"; c.target = arm; c.subtarget = f"hand.{sd}"
        bone_rest = arm.matrix_world @ arm.data.bones[f"hand.{sd}"].matrix_local
        c.inverse_matrix = bone_rest.inverted() @ grip_world(r, sd, axis) @ T.inverted(); c.set_inverse_pending = False
        for f, v in ((1, 0.0), (F(t0) - 1, 0.0), (F(t0), 1.0), (F(t1), 1.0), (F(t1) + 1, 0.0)):
            if f < 1: continue
            c.influence = v; c.keyframe_insert("influence", frame=f)
    for fc in rig2.all_fcurves(obj.animation_data.action):
        if "influence" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
    S.frame_set(1)
def pop(o, t_in=None, t_out=None, dur=0.18):
    s1 = o.scale.copy()
    if t_in is not None: key(o, "scale", s1 * 0.0, max(1, F(t_in) - 1)); key(o, "scale", s1 * 0.0, F(t_in)); key(o, "scale", s1 * 1.15, F(t_in + dur * 0.6)); key(o, "scale", s1, F(t_in + dur))
    if t_out is not None: key(o, "scale", s1, F(t_out)); key(o, "scale", s1 * 0.0, F(t_out + dur))
def phone(name, screen_col=(0.0, 1.0, 0.0), emit=1.0): return iphone.build(name, screen_col=screen_col, screen_emit=emit)

bpy.context.view_layer.update()
bad = clash_report(); print("CLASHES (set)", len(bad)); [print("  ", a, "x", b_) for a, b_ in bad[:20]]
exec(open(os.path.join(HERE, "ep4_keys.py")).read())

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
