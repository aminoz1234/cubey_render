"""Knoxville video: 3D map zoom (Tennessee -> Knoxville), mono dark blue with glowing roads/rivers.
Data: Natural Earth 10m (public domain), pre-projected to assets/knox/tn_map.json (1 unit = 10 km, origin = Knoxville).
Shot M1 1-240: roads draw on over the state, camera dives from a state-wide view to Knoxville, pin + pulse rings."""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
ROOT = os.getcwd(); S = bpy.context.scene
exec(open("tools/realism.py").read()); exec(open("tools/common_build.py").read())
cycles_quality(S, samples=32, res=(1280, 720)); S.view_settings.look = "AgX - Medium High Contrast"
S.frame_start, S.frame_end = 1, 240; S.render.fps = 30
D = json.load(open(os.path.join(ROOT, "assets/knox/tn_map.json")))
w = bpy.data.worlds.new("w"); S.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.002, 0.004, 0.009, 1)
FONT = bpy.data.fonts.load(os.path.join(ROOT, "assets", "fonts", "BebasNeue-Regular.ttf"))


def emis(name, col, s):
    return mat(name, col, emit=s, rough=0.6)


M_TN = mat("m_tn", (0.1, 0.2, 0.42), rough=0.7)
M_OTHER = mat("m_other", (0.012, 0.016, 0.026), rough=0.9)
M_URBAN = emis("m_urban", (0.12, 0.22, 0.45), 0.6)
M_WATER = emis("m_water", (0.05, 0.75, 1.0), 3.0)
M_ROAD = emis("m_road", (1.0, 0.55, 0.1), 5.0)
M_ROAD2 = emis("m_road2", (0.18, 0.22, 0.3), 1.0)
M_BORDER = emis("m_border", (0.85, 0.92, 1.0), 4.0)
M_TEXT = emis("m_text", (0.75, 0.88, 1.0), 4.0)
M_PIN = emis("m_pin", (1.0, 0.06, 0.03), 5.0)


def fill(name, rings, z, m, thick=0.0):
    bm = bmesh.new()
    for ring in rings:
        vs = [bm.verts.new((x, y, z)) for x, y in ring]
        if len(vs) < 3:
            continue
        es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs)) if vs[i] is not vs[(i + 1) % len(vs)]]
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me))
    if thick:
        o.modifiers.new("sol", "SOLIDIFY").thickness = thick
    return o


def polylines(name, lines, z, m, depth, cyclic=False):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = 1
    for pts in lines:
        if len(pts) < 2:
            continue
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1); sp.use_cyclic_u = cyclic
        for p, (x, y) in zip(sp.points, pts):
            p.co = (x, y, z, 1)
    cu.materials.append(m)
    return link(bpy.data.objects.new(name, cu))


def text(t, loc, size, m=M_TEXT, align="CENTER"):
    cu = bpy.data.curves.new("t_" + t, "FONT"); cu.body = t; cu.font = FONT; cu.size = size; cu.align_x = align; cu.align_y = "CENTER"
    cu.materials.append(m)
    o = link(bpy.data.objects.new("t_" + t, cu)); o.location = loc
    return o


# ground + states
fill("ocean", [[(-120, -80), (120, -80), (120, 80), (-120, 80)]], -0.02, mat("m_bg", (0.008, 0.012, 0.024), rough=0.9))
tn = [s["pts"] for s in D["states"] if s["name"] == "Tennessee"]
other = [s["pts"] for s in D["states"] if s["name"] != "Tennessee"]
fill("tn", tn, 0.0, M_TN)
bpy.data.objects["tn"].location.z = 0.25
fill("others", other, 0.0, M_OTHER)
b_tn = polylines("tn_border", tn, 0.26, M_BORDER, 0.06, cyclic=True)
b_ot = polylines("state_borders", other, 0.01, M_ROAD2, 0.03, cyclic=True)
riv = polylines("rivers", [r["pts"] for r in D["rivers"] if r["name"] in ("Tennessee", "Mississippi", "Cumberland")], 0.265, M_WATER, 0.05)
maj = polylines("roads_major", [r["pts"] for r in D["roads"] if r["t"] == "Major Highway"], 0.27, M_ROAD, 0.05)
# line widths shrink as the camera dives in; roads draw on at the start
for ob, d0, d1 in ((riv, 0.09, 0.012), (maj, 0.1, 0.01), (b_tn, 0.14, 0.02), (b_ot, 0.05, 0.01)):
    for f, d in ((1, d0), (60, d0), (200, d1)):
        ob.data.bevel_depth = d; ob.data.keyframe_insert("bevel_depth", frame=f)
for ob in (maj, riv):
    ob.data.bevel_factor_end = 0.0; ob.data.keyframe_insert("bevel_factor_end", frame=5)
    ob.data.bevel_factor_end = 1.0; ob.data.keyframe_insert("bevel_factor_end", frame=70)
# cities
for c in D["cities"]:
    x, y = c["p"]
    if c["name"] not in ("Nashville", "Memphis", "Chattanooga"):
        continue
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.25, depth=0.05, location=(x, y, 0.29)); bpy.context.active_object.data.materials.append(M_TEXT)
    t = text(c["name"].upper(), (x, y - 1.6, 0.3), 2.0)
    for f, s in ((1, 1.0), (110, 1.0), (140, 0.0)):
        t.scale = (s,) * 3; t.keyframe_insert("scale", frame=f)
t = text("TENNESSEE", (-28, -4.5, 0.3), 3.2)
for f, s in ((1, 0.0), (12, 1.0), (90, 1.0), (115, 0.0)):
    t.scale = (s,) * 3; t.keyframe_insert("scale", frame=f)
# Knoxville pin: beam + pulse rings + label
kx, ky = D["cities"][[c["name"] for c in D["cities"]].index("Knoxville")]["p"]
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.015, depth=6, location=(kx, ky, 3.27)); beam = bpy.context.active_object; beam.data.materials.append(M_PIN)
for f, s in ((1, 0.0), (90, 0.0), (120, 1.0)):
    beam.scale = (1, 1, s); beam.keyframe_insert("scale", frame=f)
beam.location.z = 0.27; beam.data.transform(__import__("mathutils").Matrix.Translation((0, 0, 3)))
for i in range(3):
    cu = bpy.data.curves.new(f"pulse{i}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.012
    sp = cu.splines.new("NURBS"); sp.points.add(7); sp.use_cyclic_u = True; sp.order_u = 3
    for k, p in enumerate(sp.points):
        a = k / 8 * 2 * math.pi; p.co = (math.cos(a), math.sin(a), 0, 1)
    cu.materials.append(M_PIN); r = link(bpy.data.objects.new(f"pulse{i}", cu)); r.location = (kx, ky, 0.28)
    for cyc in range(4):
        f0 = 120 + i * 10 + cyc * 30
        r.scale = (0.02,) * 3; r.keyframe_insert("scale", frame=f0)
        r.scale = (0.6,) * 3; r.keyframe_insert("scale", frame=f0 + 29)
    r.scale = (0,) * 3; r.keyframe_insert("scale", frame=1); r.keyframe_insert("scale", frame=119 + i * 10)
kl = text("KNOXVILLE, TN", (kx + 0.15, ky + 0.42, 0.3), 0.32, align="LEFT")
for f, s in ((1, 0.0), (125, 0.0), (132, 1.15), (138, 1.0)):
    kl.scale = (s,) * 3; kl.keyframe_insert("scale", frame=f)
# light + camera dive
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 1.2; sun.color = (0.55, 0.7, 1.0); so = link(bpy.data.objects.new("sun", sun)); so.rotation_euler = (math.radians(40), 0, math.radians(30))
cam, aim = camera("cam", Vector((-22, -60, 70)), Vector((-20, -2, 0)), lens=35)
cam.data.clip_end = 500
for f, cl, al in ((1, (-22, -60, 70), (-20, -2, 0)), (60, (-14, -46, 52), (-14, -1, 0)), (175, (kx + 0.6, ky - 3.2, 3.2), (kx, ky + 0.2, 0.27)),
                  (240, (kx + 1.1, ky - 2.4, 2.4), (kx + 0.1, ky + 0.2, 0.27))):
    cam.location = cl; cam.keyframe_insert("location", frame=f); aim.location = al; aim.keyframe_insert("location", frame=f)
for o in (cam, aim):
    for fc in fcurves(o):
        for k in fc.keyframe_points:
            k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"
S.camera = cam
os.makedirs("scenes/knox_map", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes/knox_map/map.blend"))
if "--still" in sys.argv:
    S.cycles.samples = 12
    for f in map(int, sys.argv[sys.argv.index("--still") + 1].split(",")):
        S.frame_set(f); S.render.filepath = f"/tmp/et/map_{f}.png"; bpy.ops.render.render(write_still=True)
