"""Episode 3 'Plate Three': Thanksgiving dinner. Two big uncles eat, Marcus (the tall gym nephew) scans their plates with Cubey.
python3 build_ep3.py OUT.blend PUPDIR   (PUPDIR holds <who>/head/####.webp + headmeta.json; rig art in kit/ep3/rig; timing from ep3vo/lines.json)"""
import bpy, math, os, sys, json, random, itertools, bmesh
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig2, iphone
OUT, PUPA = os.path.abspath(sys.argv[-2]), os.path.abspath(sys.argv[-1])
RB = f"{HERE}/KayKit-Restaurant-Bits-1.0/addons/kaykit_restaurant_bits/Assets/gltf"
FB = f"{HERE}/KayKit-Furniture-Bits-1.0/addons/kaykit_furniture_bits/Assets/gltf"
LINES = json.load(open("/home/claude/work/ep3vo/lines.json"))["lines"]
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

# ------------------------------------------------------------ the dining room (camera on -y looking +y; table along x)
TOP = 0.78                     # table top height
TY = 0.75                      # table centre y
floor = obj_from(bpy.ops.mesh.primitive_plane_add, "floor", size=1, location=(0, 0.5, 0)); floor.scale = (9, 8, 1)
fm = bpy.data.materials.new("floor_m"); fm.use_nodes = True; nt = fm.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.45
wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.2; wv.inputs["Distortion"].default_value = 6; rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (0.28, 0.15, 0.07, 1); rp.color_ramp.elements[1].color = (0.48, 0.29, 0.14, 1); tc = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], b.inputs["Base Color"])
floor.data.materials.append(fm); floor["kit"] = "floor_wood"
WALL = mmat("wallpaper", (0.42, 0.24, 0.14), 0.8)
def wall_plane(name, loc, rot, size):
    w = obj_from(bpy.ops.mesh.primitive_plane_add, name, size=1, location=loc); w.rotation_euler = rot; w.scale = (size[0], size[1], 1); w.data.materials.append(WALL); w["kit"] = "floor_" + name; return w
wall_plane("backwall", (0, 2.55, 2.5), (R(90), 0, 0), (9, 5.0))
wall_plane("leftwall", (-3.2, 0.5, 2.5), (R(90), 0, R(90)), (6, 5.0))
wall_plane("rightwall", (3.6, 0.5, 2.5), (R(90), 0, R(90)), (6, 5.0))
cl_ = obj_from(bpy.ops.mesh.primitive_plane_add, "ceiling", size=1, location=(0, 0.5, 3.4)); cl_.scale = (9, 8, 1); cl_.data.materials.append(mmat("ceil_m", (0.85, 0.8, 0.72), 0.9)); cl_["kit"] = "floor_ceiling"
# wainscot strip and a window on the back wall
ws = obj_from(bpy.ops.mesh.primitive_cube_add, "wainscot", size=1, location=(0, 2.53, 0.45)); ws.scale = (9, 0.04, 0.9); ws.data.materials.append(mmat("wainscot_m", (0.85, 0.78, 0.66), 0.5)); ws["kit"] = "floor_wainscot"
win = obj_from(bpy.ops.mesh.primitive_cube_add, "window", size=1, location=(-1.2, 2.535, 1.65)); win.scale = (1.1, 0.02, 1.0)
win.data.materials.append(mmat("night_m", (0.06, 0.1, 0.24), 0.2, emit=0.8)); win["kit"] = "floor_window"
for nm, (x, z, sx, sz) in {"wf_t": (-1.2, 2.17, 1.22, 0.07), "wf_b": (-1.2, 1.13, 1.22, 0.07), "wf_l": (-1.79, 1.65, 0.07, 1.1), "wf_r": (-0.61, 1.65, 0.07, 1.1), "wf_m": (-1.2, 1.65, 0.04, 1.0)}.items():
    o = obj_from(bpy.ops.mesh.primitive_cube_add, nm, size=1, location=(x, 2.51, z)); o.scale = (sx, 0.05, sz); o.data.materials.append(mmat("frame_m", (0.92, 0.9, 0.85), 0.4)); o["kit"] = "floor_" + nm
imp(f"{FB}/pictureframe_large_A.gltf", "picture1", (0.9, 2.5, 1.85), 0, (0.6, 0.6, 0.6))
imp(f"{FB}/pictureframe_medium.gltf", "picture2", (1.75, 2.5, 1.7), 0, (0.6, 0.6, 0.6))
imp(f"{FB}/shelf_B_large_decorated.gltf", "sideboard", (2.3, 2.45, 0.1), 0, (0.75, 0.75, 0.75))
imp(f"{FB}/lamp_standing.gltf", "floorlamp", (-2.6, 2.05, 0), 0, (0.7, 0.7, 0.7))
imp(f"{FB}/rug_rectangle_A.gltf", "rug", (0, TY, 0.002), 0, (1.25, 1.2, 0.2)); tag(bpy.data.objects["rug"], "floor_rug")

# table + chairs
table = imp(f"{FB}/table_medium_long.gltf", "table", (0, TY, 0), 0, (0.82, 0.5, TOP))
for i, x in enumerate((-0.6, 0.6)): imp(f"{FB}/chair_A_wood.gltf", f"chair{i}", (x, TY + 0.95, 0), 0, (0.72, 0.72, 0.72))
# tablecloth runner
run = obj_from(bpy.ops.mesh.primitive_cube_add, "runner", size=1, location=(0, TY, TOP + 0.003)); run.scale = (2.2, 0.36, 0.006); run.data.materials.append(mmat("runner_m", (0.62, 0.18, 0.08), 0.8)); run["kit"] = "table"

Z0 = TOP + 0.009          # everything on the table rests a hair above the runner (no coplanar contact)
# ------------------------------------------------------------ the food (procedural, each its own clash tag)
GLOSS = lambda n, c, r=0.3: mmat(n, c, r)
PLATE = mmat("plate_m", (0.95, 0.94, 0.9), 0.25)
def plate(name, x, y, r=0.14):
    p = obj_from(bpy.ops.mesh.primitive_cylinder_add, name, radius=r, depth=0.018, vertices=48, location=(x, y, Z0 + 0.009)); smooth(p); p.data.materials.append(PLATE)
    rim = obj_from(bpy.ops.mesh.primitive_torus_add, name + "_rim", major_radius=r * 0.93, minor_radius=0.008, location=(x, y, Z0 + 0.017)); rim.data.materials.append(PLATE); rim.parent = p; rim.matrix_parent_inverse = p.matrix_world.inverted()
    return tag(p, name)
def blob(name, loc, rad, scale, mat, parent=None, k=None):
    o = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, name, radius=rad, segments=24, ring_count=12, location=loc); o.scale = scale; smooth(o); o.data.materials.append(mat)
    if parent: o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    if k: o["kit"] = k
    return o
TURKEY = GLOSS("turkey_m", (0.55, 0.26, 0.08), 0.28); MASH = mmat("mash_m", (0.93, 0.86, 0.66), 0.6); GRAVY = GLOSS("gravy_m", (0.3, 0.15, 0.05), 0.2)
SWEET = mmat("sweet_m", (0.92, 0.45, 0.1), 0.5); MALLOW = mmat("mallow_m", (0.97, 0.9, 0.75), 0.6); TOAST = mmat("toast_m", (0.72, 0.42, 0.16), 0.6)
CRAN = GLOSS("cran_m", (0.5, 0.0, 0.035), 0.12); GREEN = mmat("beans_m", (0.25, 0.45, 0.12), 0.5); CRUST = mmat("crust_m", (0.82, 0.58, 0.3), 0.6); PECAN = GLOSS("pecan_m", (0.33, 0.14, 0.04), 0.25)
# turkey on a platter, centre
plat = plate("platter", 0.0, TY + 0.05, 0.2); plat.scale = (1.25, 1.0, 1.0)
tk = blob("turkey", (0.0, TY + 0.05, Z0 + 0.1), 0.15, (1.25, 0.95, 0.62), TURKEY, k="platter")
for sx in (-1, 1):
    d = blob(f"drum{sx}", (sx * 0.15, TY - 0.03, Z0 + 0.09), 0.055, (1.4, 0.8, 0.8), TURKEY, k="platter"); d.rotation_euler = (0, 0, R(sx * -30))
    bone = obj_from(bpy.ops.mesh.primitive_cylinder_add, f"bone{sx}", radius=0.012, depth=0.07, location=(sx * 0.22, TY - 0.07, Z0 + 0.1)); bone.rotation_euler = (0, R(90), R(sx * -30)); bone.data.materials.append(MALLOW); bone["kit"] = "platter"
# sweet potato casserole (white dish, orange mash, toasted marshmallows) in front of Ray
CAS = (0.42, TY - 0.13)
dish = obj_from(bpy.ops.mesh.primitive_cube_add, "cas_dish", size=1, location=(CAS[0], CAS[1], Z0 + 0.04)); dish.scale = (0.32, 0.22, 0.08)
bv = dish.modifiers.new("bev", "BEVEL"); bv.width = 0.02; bv.segments = 3; dish.data.materials.append(mmat("dish_m", (0.96, 0.96, 0.94), 0.2)); dish["kit"] = "casserole"
fillc = obj_from(bpy.ops.mesh.primitive_cube_add, "cas_fill", size=1, location=(CAS[0], CAS[1], Z0 + 0.082)); fillc.scale = (0.29, 0.19, 0.01); fillc.data.materials.append(SWEET); fillc["kit"] = "casserole"
rnd = random.Random(7)
for i in range(34):
    x = CAS[0] + rnd.uniform(-0.13, 0.13); y = CAS[1] + rnd.uniform(-0.08, 0.08)
    blob(f"mallow{i}", (x, y, Z0 + 0.095), 0.018, (1, 1, 0.75), TOAST if rnd.random() < 0.45 else MALLOW, k="casserole")
# Ray's plate three: a mountain
RP = (-0.88, TY + 0.25)
plate("ray_plate", RP[0], RP[1], 0.15)
blob("ray_mash", (RP[0] - 0.03, RP[1], Z0 + 0.05), 0.08, (1, 1, 0.75), MASH, k="ray_plate")
blob("ray_gravy", (RP[0] - 0.03, RP[1], Z0 + 0.1), 0.045, (1.1, 1.1, 0.35), GRAVY, k="ray_plate")
blob("ray_sweet", (RP[0] + 0.07, RP[1] - 0.03, Z0 + 0.045), 0.055, (1, 1, 0.7), SWEET, k="ray_plate")
for i in range(5): blob(f"ray_m{i}", (RP[0] + 0.05 + rnd.uniform(-0.03, 0.03), RP[1] - 0.03 + rnd.uniform(-0.03, 0.03), Z0 + 0.08), 0.014, (1, 1, 0.75), MALLOW, k="ray_plate")
blob("ray_beans", (RP[0] - 0.02, RP[1] + 0.07, Z0 + 0.035), 0.05, (1.2, 0.7, 0.45), GREEN, k="ray_plate")
# Dale's plate
DP = (0.6, TY + 0.25)
plate("dale_plate", DP[0], DP[1], 0.15)
blob("dale_mash", (DP[0] + 0.02, DP[1], Z0 + 0.04), 0.06, (1, 1, 0.7), MASH, k="dale_plate")
blob("dale_gravy", (DP[0] + 0.02, DP[1], Z0 + 0.075), 0.035, (1.1, 1.1, 0.35), GRAVY, k="dale_plate")
blob("dale_beans", (DP[0] - 0.06, DP[1] + 0.03, Z0 + 0.03), 0.045, (1.2, 0.7, 0.45), GREEN, k="dale_plate")
# canned cranberry log (ridges and all) on a saucer, near Dale
def cranberry(name):      # origin under the saucer, so a hand holding it shows the whole log above the fingers
    c = obj_from(bpy.ops.mesh.primitive_cylinder_add, name, radius=0.05, depth=0.12, vertices=40, location=(0, 0, 0)); smooth(c); c.data.materials.append(CRAN)
    for v in c.data.vertices: v.co.z += 0.075
    for i, z in enumerate((0.04, 0.075, 0.11)):
        r_ = obj_from(bpy.ops.mesh.primitive_torus_add, f"{name}_ridge{i}", major_radius=0.05, minor_radius=0.005, location=(0, 0, z)); r_.data.materials.append(CRAN); r_.parent = c
    sc = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_saucer", radius=0.095, depth=0.012, vertices=40, location=(0, 0, 0.006)); smooth(sc); sc.data.materials.append(PLATE); sc.parent = c
    return c
cran = cranberry("cranberry"); CR = (0.86, TY + 0.02); cran.location = (CR[0], CR[1], Z0 + 0.001); tag(cran, "cranberry")
# pecan pie next to Ray (he slides it to Dale at the end)
def pie(name):
    p = obj_from(bpy.ops.mesh.primitive_cylinder_add, name, radius=0.14, depth=0.045, vertices=48, location=(0, 0, 0)); smooth(p); p.data.materials.append(CRUST)
    t = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_top", radius=0.125, depth=0.01, vertices=48, location=(0, 0, 0.022)); t.data.materials.append(PECAN); t.parent = p
    for i in range(14):
        a = i / 14 * 2 * math.pi; rr = 0.09 if i % 2 else 0.05
        n_ = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, f"{name}_pecan{i}", radius=0.018, segments=10, ring_count=6, location=(rr * math.cos(a), rr * math.sin(a), 0.03)); n_.scale = (1.4, 0.8, 0.45); n_.rotation_euler = (0, 0, a)
        n_.data.materials.append(PECAN); n_.parent = p
    return p
pie_ = pie("pie"); PIE0 = (-0.42, TY - 0.05); pie_.location = (PIE0[0], PIE0[1], Z0 + 0.023); tag(pie_, "pie")
# gravy boat, bottles, roll basket
gb = imp(f"{RB}/bowl.gltf", "gravyboat", (0.0, TY + 0.47, Z0), 0, (0.22, 0.32, 0.25))
for i, (x, y) in enumerate(((-1.12, TY + 0.48), (1.0, TY + 0.4))):
    bt = obj_from(bpy.ops.mesh.primitive_cylinder_add, f"bottle{i}", radius=0.032, depth=0.2, vertices=24, location=(x, y, Z0 + 0.1)); smooth(bt); bt.data.materials.append(GLOSS("bottle_m", (0.22, 0.1, 0.02), 0.1)); bt["kit"] = f"bottle{i}"
    nk = obj_from(bpy.ops.mesh.primitive_cone_add, f"bottle{i}_neck", radius1=0.032, radius2=0.012, depth=0.08, vertices=24, location=(x, y, Z0 + 0.24)); smooth(nk); nk.data.materials.append(bt.data.materials[0]); nk["kit"] = f"bottle{i}"
imp(f"{RB}/food_dinner.gltf", "rolls", (0.75, TY - 0.15, Z0), 0, (0.2, 0.2, 0.2))
# held props
def drumstick(name):
    d = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, name, radius=0.05, segments=20, ring_count=10, location=(0, 0, 0)); d.scale = (1.5, 0.85, 0.85); smooth(d); d.data.materials.append(TURKEY)
    bn = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_bone", radius=0.011, depth=0.07, location=(0.09, 0, 0)); bn.rotation_euler = (0, R(90), 0); bn.data.materials.append(MALLOW); bn.parent = d
    return d
drum = drumstick("drumstick")
def pie_slice(name):
    me = bpy.data.meshes.new(name); r = 0.12; a = R(40)
    vs = [(0, 0, 0), (r * math.cos(-a / 2), r * math.sin(-a / 2), 0), (r * math.cos(a / 2), r * math.sin(a / 2), 0), (0, 0, 0.045), (r * math.cos(-a / 2), r * math.sin(-a / 2), 0.045), (r * math.cos(a / 2), r * math.sin(a / 2), 0.045)]
    me.from_pydata(vs, [], [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]); me.update()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.data.materials.append(CRUST); o.data.materials.append(PECAN)
    o.data.polygons[1].material_index = 1; return o
slice_ = pie_slice("pie_slice")
def coke(name):           # 12 oz can, red with a white swoosh band; origin at the bottom
    c = obj_from(bpy.ops.mesh.primitive_cylinder_add, name, radius=0.033, depth=0.122, vertices=40, location=(0, 0, 0)); smooth(c)
    for v in c.data.vertices: v.co.z += 0.061
    c.data.materials.append(GLOSS("coke_m", (0.75, 0.02, 0.03), 0.25))
    band = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_band", radius=0.0335, depth=0.02, vertices=40, location=(0, 0, 0.07)); band.data.materials.append(mmat("cokeband_m", (0.95, 0.95, 0.95), 0.3)); band.parent = c
    lid = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_lid", radius=0.029, depth=0.006, vertices=40, location=(0, 0, 0.124)); lid.data.materials.append(mmat("alu_m", (0.8, 0.8, 0.82), 0.25)); lid.parent = c
    return c
can = coke("coke"); CK = (-0.7, TY - 0.08); can.location = (CK[0], CK[1], Z0 + 0.001); tag(can, "coke")

# ------------------------------------------------------------ light: warm dinner light from a pendant over the table, cool night window, soft fill from the camera side
w = S.world = bpy.data.worlds.new("room"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.08, 0.06, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.2
def light(name, kind, loc, energy, col, size=None, rot=(0, 0, 0)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); S.collection.objects.link(l); l.location = loc; l.rotation_euler = rot; l.data.energy = energy; l.data.color = col
    if size is not None:
        if kind == "AREA": l.data.size = size
        else: l.data.shadow_soft_size = size
    return l
light("pendant", "POINT", (0, TY, 2.35), 170, (1.0, 0.72, 0.45), 0.35)
light("key", "AREA", (-1.6, -1.6, 2.6), 230, (1.0, 0.86, 0.7), 2.0, (R(50), 0, R(-35)))
light("fill", "AREA", (2.2, -1.2, 1.8), 80, (0.85, 0.85, 1.0), 2.5, (R(65), 0, R(50)))
light("rim", "AREA", (0.5, 2.3, 2.4), 120, (0.7, 0.8, 1.0), 2.0, (R(-60), 0, R(180)))
shade_ = obj_from(bpy.ops.mesh.primitive_cone_add, "pendant_shade", radius1=0.28, radius2=0.08, depth=0.22, vertices=40, location=(0, TY, 2.5)); smooth(shade_)
shade_.data.materials.append(mmat("shade_m", (0.95, 0.75, 0.4), 0.5, emit=1.2)); shade_["kit"] = "pendant"
cord = obj_from(bpy.ops.mesh.primitive_cylinder_add, "pendant_cord", radius=0.008, depth=0.8, location=(0, TY, 3.0)); cord.data.materials.append(mmat("cord_m", (0.05, 0.05, 0.05), 0.5)); cord["kit"] = "pendant"

def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); S.collection.objects.link(e); e.location = loc; e.empty_display_size = 0.05; return e
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); S.collection.objects.link(cam); S.camera = cam
cam.data.lens = 26; cam.data.sensor_width = 36; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8
tgt = empty("cam_target"); tc_ = cam.constraints.new("TRACK_TO"); tc_.target = tgt; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
cam.data.dof.focus_object = tgt; cam.data.clip_end = 100; cam.data.clip_start = 0.02
S.render.resolution_x, S.render.resolution_y = 1080, 1920; S.render.fps = FPS; S.frame_start = 1; S.frame_end = NFR
S.view_settings.view_transform = "AgX"; S.view_settings.look = "AgX - Punchy"; S.view_settings.exposure = -0.25
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
# things resting on the table touch it by design: count only real interpenetration among table-top items and furniture
TABLE_TOUCH = {"table"}

# ------------------------------------------------------------ characters
HM = json.load(open(f"{PUPA}/headmeta.json")); ARTD = os.path.join(HERE, "ep3", "rig")
SEAT = 0.47
POS = {"ray": (-0.6, TY + 0.62, SEAT - 0.62 * 1.3), "dale": (0.6, TY + 0.62, SEAT - 0.62 * 1.3), "marcus": (1.58, TY + 0.05, 0.0)}
SCALE = {"ray": 1.3, "dale": 1.3, "marcus": 1.42}
RIG = {w_: rig2.build(w_, POS[w_], ARTD, f"{PUPA}/{w_}/head", HM[w_], cam, scale=SCALE[w_], frames=NFR) for w_ in ("ray", "dale", "marcus")}
ray, dale, marcus = RIG["ray"], RIG["dale"], RIG["marcus"]
for who in ("ray", "dale"):                      # seated behind the table: legs never show
    for k_, o in RIG[who]["parts"].items():
        if k_.startswith(("leg", "foot")): o.hide_render = True; o.hide_viewport = True
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.3, fill_type="NGON", location=(0, 0, 0.004)); sh = bpy.context.active_object; sh.name = "marcus_contact"
sh.scale = (1.3, 0.6, 1); cl = sh.constraints.new("COPY_LOCATION"); cl.target = marcus["arm"]; cl.use_z = False
sm = mmat("contact_m", (0.02, 0.015, 0.02), 0.9, alpha=0.45); sh.data.materials.append(sm); sh.visible_shadow = False

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
exec(open(os.path.join(HERE, "ep3_keys.py")).read())

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
