"""Cubey ep1 kitchen + paper-puppet characters + shot 1 camera.
python3 build_ep1.py OUT.blend PUPDIR [preview]"""
import bpy, math, os, sys, json, itertools
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT, PUP = os.path.abspath(sys.argv[-2]), os.path.abspath(sys.argv[-1])
RB = "/home/claude/work/kit/KayKit-Restaurant-Bits-1.0/addons/kaykit_restaurant_bits/Assets/gltf"
FB = "/home/claude/work/kit/KayKit-Furniture-Bits-1.0/addons/kaykit_furniture_bits/Assets/gltf"
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
R = math.radians

def imp(name, loc=(0, 0, 0), rot=0.0, scale=1.0):
    p = f"{RB}/{name}.gltf" if os.path.exists(f"{RB}/{name}.gltf") else f"{FB}/{name}.gltf"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    root = [o for o in new if o.parent not in new][0]
    if len([o for o in new if o.parent not in new]) > 1:
        e = bpy.data.objects.new(name, None); S.collection.objects.link(e)
        for o in new:
            if o.parent not in new: o.parent = e
        root = e
    root.location = Vector(loc); root.rotation_mode = "XYZ"; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
    root.name = name; root["kit"] = name
    for o in new:
        if o.type == "MESH": o["kit"] = name
    bpy.context.view_layer.update()
    return root

def meshes(o): return [m for m in [o] + list(o.children_recursive) if m.type == "MESH"]
def bb(o):
    bpy.context.view_layer.update()
    pts = [m.matrix_world @ Vector(c) for m in meshes(o) for c in m.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def put(name, rot=0, scale=1.0, **edge):
    """Place a kit piece by its measured bounds: xmin/xmax/xc, ymin/ymax/yc, zmin/zc."""
    o = imp(name, (0, 0, 0), rot, scale); mn, mx = bb(o)
    for ax, i in (("x", 0), ("y", 1), ("z", 2)):
        if f"{ax}min" in edge: o.location[i] += edge[f"{ax}min"] - mn[i]
        elif f"{ax}max" in edge: o.location[i] += edge[f"{ax}max"] - mx[i]
        elif f"{ax}c" in edge: o.location[i] += edge[f"{ax}c"] - (mn[i] + mx[i]) / 2
    bpy.context.view_layer.update()
    return o

def drop(name, x, y, rot=0, scale=1.0, lift=0.004):
    """Raycast down at (x, y) and rest the piece on whatever surface is there."""
    o = imp(name, (0, 0, 0), rot, scale); mn, mx = bb(o)
    o.location.x += x - (mn.x + mx.x) / 2; o.location.y += y - (mn.y + mx.y) / 2
    for m in meshes(o): m.hide_set(True)
    dg = bpy.context.evaluated_depsgraph_get()
    zs = []
    for dx in (-0.4, 0, 0.4):
        for dy in (-0.4, 0, 0.4):
            px, py = x + dx * (mx.x - mn.x), y + dy * (mx.y - mn.y)
            hit, loc, *_ = S.ray_cast(dg, Vector((px, py, 6)), Vector((0, 0, -1)))
            zs.append(loc.z if hit else 0.0)
    for m in meshes(o): m.hide_set(False)
    o.location.z += max(zs) + lift - mn.z
    bpy.context.view_layer.update()
    return o

# ------------------------------------------------------------ room. Back wall inner face y = 4.0, side walls x = -9 / +7
for x in range(-8, 7, 2):
    for y in range(-7, 4, 2):
        put("floor_kitchen", scale=0.5, xc=x, yc=y, zmax=0.0)
for yc in (2, -2, -6):
    for z in (0, 4):
        put("wall", rot=90, xmax=-9.0, yc=yc, zmin=z); put("wall", rot=90, xmin=7.0, yc=yc, zmin=z)

# back counter run, measured, left to right, small gaps so nothing touches
cur = -8.97
centers = []
for n in ("fridge_A_decorated", "kitchencounter_straight_A_backsplash", "kitchencounter_straight_A", "kitchencounter_straight_A_backsplash",
          "kitchencounter_sink_backsplash", "kitchencounter_straight_B_backsplash", "kitchencounter_straight_A_backsplash"):
    o = put(n, xmin=cur, ymax=3.97, zmin=0); cur = bb(o)[1].x + 0.01
    if n == "kitchencounter_straight_A": stove_x = (bb(o)[0].x + bb(o)[1].x) / 2
    centers.append((bb(o)[0].x + bb(o)[1].x) / 2)
    if n == "kitchencounter_sink_backsplash": sink_x = (bb(o)[0].x + bb(o)[1].x) / 2
for k in range(-2, 3):                                                   # back wall, window centred over the sink
    xc = sink_x + 4 * k
    put("wall_window_open" if k == 0 else "wall", xc=xc, ymin=4.0, zmin=0); put("wall", xc=xc, ymin=4.0, zmin=4.0)
put("stove_multi_countertop", xc=stove_x, ymax=3.6, zmin=1.003)          # cooktop insert on the plain counter
put("extractorhood", xc=stove_x, ymax=3.99, zmin=2.45)
put("shelf_papertowel_decorated", xc=centers[1], ymax=3.99, zmin=2.0)
put("shelf_B_large_decorated", xc=centers[5], ymax=3.99, zmin=2.2)
put("pictureframe_large_A", rot=-90, xmin=-8.99, yc=0.2, zc=2.4)
put("pictureframe_medium", xc=centers[6], ymax=3.99, zc=2.9)
put("lamp_standing", xmax=6.9, yc=1.2, zmin=0)
rug = put("rug_rectangle_stripes_A", xc=0.0, yc=-1.0, zmin=0.0)
tab = put("kitchentable_A_large", xc=0.0, yc=-1.0, zmin=bb(rug)[1].z + 0.002)
tmn, tmx = bb(tab)
TOP = tmx.z
# chairs: backrest is the chair's +y side; turn each so it faces the table and keep it fully outside the table footprint
put("chair_A_wood", rot=90, xmax=tmn.x - 0.06, yc=-1.0, zmin=0)       # left of table, faces +x
put("chair_A_wood", rot=-90, xmin=tmx.x + 0.06, yc=-1.0, zmin=0)      # right of table, faces -x
put("chair_A_wood", rot=0, ymin=tmx.y + 0.06, xc=0.0, zmin=0)          # behind table, faces the camera
# clutter resting on real surfaces
drop("jar_A_medium", centers[1] - 0.6, 3.45, 0, 0.8); drop("jar_B_small", centers[1] - 0.05, 3.5, 0, 0.8); drop("jar_C_small", centers[1] + 0.5, 3.5, 20, 0.8)
drop("pot_A", stove_x - 0.42, 3.15, 0, 0.8); drop("pan_A", stove_x + 0.45, 3.0, 30, 0.75)
board = bx = centers[5]
drop("cuttingboard", bx, 3.0, 8, 0.8)
drop("food_ingredient_tomato", bx - 0.3, 3.0, 0, 0.4); drop("food_ingredient_onion", bx + 0.25, 3.05, 0, 0.4); drop("food_ingredient_carrot", bx, 2.75, 70, 0.4)
drop("cactus_medium_A", centers[6] + 0.3, 3.3, 0, 0.7); drop("cactus_small_B", centers[6] - 0.55, 3.45, 0, 0.6)

def mat(name, col, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    return m
def prop_cyl(name, r, h, m, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=48, location=(x, y, TOP + h / 2 + 0.004))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = r * 0.08; bv.segments = 3
    return o
gm = mat("glass_m", (0.9, 0.95, 1.0), 0.05); gm.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.9
prop_cyl("glass", 0.07, 0.2, gm, 0.5, -1.1)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.45, -1.0, TOP + 0.17 + 0.004)); car = bpy.context.active_object; car.name = "juice_carton"
car.scale = (0.16, 0.16, 0.34); car.data.materials.append(mat("carton_m", (1.0, 0.6, 0.08), 0.5)); car.modifiers.new("bev", "BEVEL").width = 0.015

# ------------------------------------------------------------ collision check (real triangles, not boxes)
def bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh()
    mw = o.matrix_world; v = [mw @ x.co for x in me.vertices]; f = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(v, f)
def clash_report():
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.get("kit", o.name) and not str(o.get("kit", "")).startswith("floor")]
    boxes = {o: bb(o) for o in objs}; trees = {}; bad = []
    for a, b in itertools.combinations(objs, 2):
        ka, kb = a.get("kit", a.name), b.get("kit", b.name)
        if (a.parent is not None and a.parent == b.parent) or ka == kb: continue
        if str(ka).startswith("wall") and str(kb).startswith("wall"): continue
        (amn, amx), (bmn, bmx) = boxes[a], boxes[b]
        if any(min(amx[i], bmx[i]) - max(amn[i], bmn[i]) <= 0.002 for i in range(3)): continue
        ta = trees.setdefault(a, bvh(a)); tb = trees.setdefault(b, bvh(b))
        if ta.overlap(tb): bad.append((a.name, b.name))
    return bad
bad = clash_report()
print("CLASHES", len(bad)); [print("  ", a, "x", b) for a, b in bad]

# ------------------------------------------------------------ light
w = S.world = bpy.data.worlds.new("sky"); w.use_nodes = True
sky = w.node_tree.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA" if "NISHITA" in [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items] else sky.sky_type
w.node_tree.links.new(sky.outputs[0], w.node_tree.nodes["Background"].inputs[0]); w.node_tree.nodes["Background"].inputs[1].default_value = 0.12
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); S.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.color = (1.0, 0.84, 0.62); sun.data.angle = R(2); sun.rotation_euler = (R(52), 0, R(165))
def area(name, loc, rot, size, e, col):
    a = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); S.collection.objects.link(a)
    a.data.size = size; a.data.energy = e; a.data.color = col; a.location = loc; a.rotation_euler = [R(v) for v in rot]; return a
area("key_warm", (-3.2, -1.0, 5.2), (38, 0, -55), 2.5, 1600, (1.0, 0.72, 0.45))
area("fill_front", (-3, -7, 3.5), (75, 0, -10), 6, 160, (0.75, 0.82, 1.0))
area("rim_cool", (-6.2, 3.0, 3.8), (-55, 0, 10), 2.5, 600, (0.55, 0.7, 1.0))
area("ceiling", (-1, 0, 7.6), (0, 0, 0), 10, 350, (1.0, 0.8, 0.6))

# ------------------------------------------------------------ paper puppets
rig = json.load(open(f"{PUP}/rig.json")); U = 1000.0
def card(name, png, meta, pivot, seq=False, frames=150):
    Wp, Hp = meta["W"], meta["H"]; px, py = pivot
    vs = [((0 - px) / U, 0, -(Hp - py) / U), ((Wp - px) / U, 0, -(Hp - py) / U), ((Wp - px) / U, 0, -(0 - py) / U), ((0 - px) / U, 0, -(0 - py) / U)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], [(0, 1, 2, 3)]); me.update()
    uv = me.uv_layers.new(); [setattr(uv.data[i], "uv", c) for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); img = bpy.data.images.load(png); tex.image = img; tex.interpolation = "Cubic"
    if seq:
        img.source = "SEQUENCE"; tex.image_user.frame_duration = frames; tex.image_user.frame_start = 1; tex.image_user.use_auto_refresh = True
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.22
    b.inputs["Roughness"].default_value = 0.85; b.inputs["Specular IOR Level"].default_value = 0.2
    m.surface_render_method = "DITHERED" if hasattr(m, "surface_render_method") else None
    o.data.materials.append(m); o.visible_shadow = True
    return o
def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); S.collection.objects.link(e); e.empty_display_size = 0.05
    if parent: e.parent = parent
    e.location = loc; return e
def pt(meta, key):  # attach point relative to the part's pivot, in world units on the card plane
    (x, y), (px, py) = meta[key], meta["pivot"]; return ((x - px) / U, 0, -(y - py) / U)

PUPPETS = {}
PSCALE = 1.3
def puppet(who, x, y):
    P, D = rig[who]["parts"], f"{PUP}/{who}"
    root = empty(f"{who}_root", None, (x, y, 0)); root.rotation_mode = "XYZ"; root.scale = (PSCALE,) * 3
    lt = root.constraints.new("LOCKED_TRACK"); lt.target = S.camera; lt.track_axis = "TRACK_NEGATIVE_Y"; lt.lock_axis = "LOCK_Z"
    T, L = P["torso"], P["leg"]
    leg_len = (L["foot"][1] - L["pivot"][1]) / U
    hip_off = -(T["hipL"][1] - T["pivot"][1]) / U
    hips = empty(f"{who}_hips", root, (0, 0, leg_len - hip_off))
    torso = card(f"{who}_torso", f"{D}/torso.png", T, T["pivot"]); torso.parent = hips
    parts = {"root": root, "hips": hips, "torso": torso}
    for side, key, dy in (("L", "hipL", 0.006), ("R", "hipR", 0.004)):
        lg = card(f"{who}_leg{side}", f"{D}/leg.png", L, L["pivot"]); lg.parent = hips; lx, _, lz = pt(T, key); lg.location = (lx, dy, lz)
        if side == "L": lg.scale.x = -1                         # mirror so the shoe points outward on both sides
        parts["leg" + side] = lg
    Hd = P["head"]
    hd = card(f"{who}_head", f"{D}/head/0001.webp", Hd, Hd["pivot"], seq=True); hd.parent = torso
    nx, _, nz = pt(T, "neck"); hd.location = (nx, -0.008, nz); parts["head"] = hd
    Up, Fo = P["upper"], P["fore"]
    for side, key, s in (("L", "shL", -1), ("R", "shR", 1)):
        ua = card(f"{who}_upper{side}", f"{D}/upper.png", Up, Up["pivot"]); ua.parent = torso; sx, _, sz = pt(T, key); ua.location = (sx, -0.016, sz)
        fa = card(f"{who}_fore{side}", f"{D}/fore.png", Fo, Fo["pivot"]); fa.parent = ua; ex, _, ez = pt(Up, "end"); fa.location = (ex, -0.003, ez)
        if side == "L": fa.scale.x = -1
        hand = empty(f"{who}_hand{side}", fa, pt(Fo, "hand"))
        parts.update({"upper" + side: ua, "fore" + side: fa, "hand" + side: hand})
    # soft contact shadow that follows the feet on the floor
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.32, fill_type="NGON", location=(x, y, 0.004)); sh = bpy.context.active_object; sh.name = f"{who}_contact"
    sh.scale = (PSCALE, 0.45 * PSCALE, 1); cl = sh.constraints.new("COPY_LOCATION"); cl.target = root; cl.use_z = False
    sm = bpy.data.materials.new(f"{who}_contact_m"); sm.use_nodes = True; nt = sm.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial"); mx = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs[0].default_value = (0.02, 0.015, 0.02, 1); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3.2, 3.2, 3.2)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0, 0, 0, 1); ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], gr.inputs[0]); nt.links.new(gr.outputs[1], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(df.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs[0])
    sh.data.materials.append(sm); sh.visible_shadow = False
    PUPPETS[who] = parts
    return parts

# ------------------------------------------------------------ camera (continuous move, no cuts)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); S.collection.objects.link(cam); S.camera = cam
cam.data.lens = 26; cam.data.sensor_width = 36; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.4
tgt = empty("cam_target"); tc_ = cam.constraints.new("TRACK_TO"); tc_.target = tgt; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
cam.data.dof.focus_object = tgt
S.render.resolution_x, S.render.resolution_y = 1080, 1920
S.render.fps = 30; S.frame_start = 1; S.frame_end = 150
S.view_settings.view_transform = "AgX"; S.view_settings.look = "AgX - Punchy"
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5

son = puppet("son", -7.05, 1.25)
mom = puppet("mom", -3.9, 0.85)

# can in the son's real hand
can = prop_cyl("soda_can", 0.062, 0.2, mat("can_m", (0.78, 0.04, 0.05), 0.25), 0, 0)
lab = can.modifiers.new("bev2", "BEVEL")
can.parent = son["handR"]; can.location = (0.0, -0.05, 0.02); can.rotation_euler = (0, R(-20), 0)

# ------------------------------------------------------------ animation from the pose timeline
def key(o, path, val, f):
    setattr(o, path, val); o.keyframe_insert(path, frame=f)
for who, parts in PUPPETS.items():
    for i, p in enumerate(rig[who]["frames"]):
        f = i + 1
        r = parts["root"]; loc = r.location.copy()
        if "x" in p: loc.x = p["x"]
        loc.z = p.get("bounce", 0); key(r, "location", loc, f)
        key(parts["torso"], "rotation_euler", (0, R(-p.get("lean", 0)), 0), f)
        key(parts["head"], "rotation_euler", (0, R(p.get("tilt", 0)), 0), f)
        for side, s in (("L", -1), ("R", 1)):
            sh_, el = p["arm" + side]
            key(parts["upper" + side], "rotation_euler", (0, R(-s * sh_), 0), f)
            key(parts["fore" + side], "rotation_euler", (0, R(-s * el) * (-1 if side == "L" else 1), 0), f)
            key(parts["leg" + side], "rotation_euler", (0, R(p["leg" + side][0]), 0), f)
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# camera path: glide in on the son sipping, drift right as Mom arrives, settle on the two-shot; shake on her outburst
CK = [(1, (-4.6, -2.0, 2.5), (-7.0, 1.25, 1.75)), (45, (-5.3, -1.9, 2.2), (-6.75, 1.2, 1.75)),
      (75, (-5.65, -2.25, 2.0), (-6.2, 1.05, 1.8)), (150, (-5.75, -2.05, 1.92), (-6.2, 1.05, 1.85))]
for f, c, t in CK:
    key(cam, "location", Vector(c), f); key(tgt, "location", Vector(t), f)
for f in range(59, 75):
    a = 0.035 * (1 - (f - 59) / 16); cam.location = Vector(CK[2][1]) + Vector((math.sin(f * 2.7) * a, 0, math.cos(f * 3.3) * a)); cam.keyframe_insert("location", frame=f)

S.frame_set(1)
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file: im.pack()
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("saved", OUT, "clashes", len(bad))
