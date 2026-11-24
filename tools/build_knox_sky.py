"""Knoxville sky-view explainer, test shot: the SOS stack climbs the stairs, crosses the living room and stops at
the bedroom door while a glowing route line draws itself. Mono dark blue, sculptural mannequins."""
import bpy, math, os, sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="scenes/real/man.blend")
ROOT = os.getcwd(); S = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ("CAMERA", "LIGHT"): bpy.data.objects.remove(o)
for f in ("realism", "common_build", "mannequin", "knox_plan"):
    exec(open(f"tools/{f}.py").read())
cycles_quality(S, samples=32, res=(1280, 720)); S.view_settings.look = "AgX - Medium High Contrast"
S.frame_start, S.frame_end = 1, 210; S.render.fps = 30
rig0, body0 = strip_man(); rig0.location = (0, 0, -50)
w = bpy.data.worlds.new("w"); S.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.003, 0.005, 0.01, 1)
mono = lambda n, v: mat(n, (0.05 * v, 0.07 * v, 0.11 * v), rough=0.6)
M_FLOOR, M_CARPET, M_WALL, M_FURN, M_MATT = (mono("mono_" + n, v) for n, v in (("floor", 1.0), ("carpet", 0.8), ("wall", 1.6), ("furn", 1.2), ("matt", 2.0)))
M_CUT = mat("mono_cut", (0.25, 0.45, 0.9), emit=1.5)
P = plan_set(0)
for o in bpy.data.objects:
    if o.name.startswith("plan_") and o.type == "MESH" and o.data.materials and not o.data.materials[0].name.startswith("mono"):
        o.data.materials[0] = M_FURN

# route (stairs -> front door -> living room -> hallway -> bedroom door)
PTS = [(0.6, -1.9, -1.0), (0.6, -0.9, -0.35), (0.6, 0.2, 0.0), (1.6, 1.3, 0), (3.6, 2.6, 0), (4.8, 3.05, 0), (5.55, 3.0, 0), (5.6, 2.7, 0)]
def route(name, z_off, visible):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("NURBS"); sp.points.add(len(PTS) - 1); sp.order_u = 3; sp.use_endpoint_u = True
    for p, (x, y, z) in zip(sp.points, PTS): p.co = (x, y, z + z_off, 1)
    if visible:
        cu.bevel_depth = 0.03; cu.bevel_resolution = 3; cu.materials.append(mat("route_glow", (0.55, 0.8, 1.0), emit=12))
    return link(bpy.data.objects.new(name, cu))
line = route("route_line", 0.04, True); walkp = route("route_walk", 0.0, False); walkp.hide_render = True
line.data.bevel_factor_end = 0.0; line.data.keyframe_insert("bevel_factor_end", frame=10)
line.data.bevel_factor_end = 1.0; line.data.keyframe_insert("bevel_factor_end", frame=110)
# arrow head + pulsing door marker
ring = link(bpy.data.objects.new("door_ring", bpy.data.curves.new("door_ring", "CURVE")))
ring.data.dimensions = "3D"; sp = ring.data.splines.new("NURBS"); sp.points.add(7); sp.use_cyclic_u = True; sp.order_u = 3
for k, p in enumerate(sp.points): a = k / 8 * 2 * math.pi; p.co = (0.45 * math.cos(a), 0.45 * math.sin(a), 0, 1)
ring.data.bevel_depth = 0.025; ring.data.materials.append(mat("ring_glow", (0.55, 0.8, 1.0), emit=10)); ring.location = (6.2, 2.65, 0.05)
for f, sc in ((1, 0.0), (110, 0.0), (125, 1.15), (140, 1.0)): ring.scale = (sc,) * 3; ring.keyframe_insert("scale", frame=f)

stone = stone_mat("stone2", col=(0.16, 0.2, 0.3)); glow = glow_mat()
WALK0, WALK1 = 20, 150
for i in range(4):
    rig, _ = mannequin(f"cop{i}", "rifle", stone, Vector((0, 0, 0)), rot_z=0, rifle=True)
    c = rig.constraints.new("FOLLOW_PATH"); c.target = walkp; c.use_curve_follow = True; c.use_fixed_location = True
    c.forward_axis = "TRACK_NEGATIVE_Y"; c.up_axis = "UP_Z"
    gap = 0.085 * i
    c.offset_factor = 0.0; c.keyframe_insert("offset_factor", frame=WALK0 + 9 * i)
    c.offset_factor = 1.0 - gap; c.keyframe_insert("offset_factor", frame=WALK1)
    walk(rig, WALK0, WALK1, period=20)
mannequin("mel", "point_gun", glow, Vector((7.05, 2.55, 0)), rot_z=-90)
mannequin("girl", "sit", mat("girlm", (0.7, 0.78, 0.9), rough=0.5, emit=0.6), Vector((8.1, 3.4, 0.24)), rot_z=250, scale=0.85)
# linear offset on every cop
for o in bpy.data.objects:
    if o.name.startswith("cop") and o.type == "ARMATURE":
        for fc in fcurves(o):
            if "offset_factor" in fc.data_path:
                for k in fc.keyframe_points: k.interpolation = "LINEAR"

sun = bpy.data.lights.new("moon", "SUN"); sun.energy = 0.6; sun.color = (0.5, 0.65, 1.0)
so = link(bpy.data.objects.new("moon", sun)); so.rotation_euler = (math.radians(35), 0, math.radians(25))
for k, (x, y) in enumerate(((1.2, 0.6), (3.0, 2.2), (5.6, 2.2), (7.6, 3.0))):
    l = point(f"pool{k}", Vector((x, y, 3.4)), 110, (0.55, 0.7, 1.0), r=0.5); l.visible_camera = False
cam, aim = camera("cam", Vector((0.5, -7.5, 9.5)), Vector((2.6, 0.8, 0.0)), lens=30, fstop=8)
S.camera = cam
for f, cl, al in ((1, (1.6, -4.6, 12.5), (2.8, 1.2, 0.0)), (210, (5.0, -2.2, 10.0), (5.9, 2.5, 0.2))):
    cam.location = cl; cam.keyframe_insert("location", frame=f); aim.location = al; aim.keyframe_insert("location", frame=f)
os.makedirs("scenes/knox_sky", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes/knox_sky/sky_route.blend"))
if "--still" in sys.argv:
    for f in map(int, sys.argv[sys.argv.index("--still") + 1].split(",")):
        S.frame_set(f); S.render.filepath = f"/tmp/et/route_{f}.png"; bpy.ops.render.render(write_still=True)
