"""Knoxville sky-view explainers on the detailed bodycam-based layout (tools/knox_apt.py). Five shots, one blend:
  K1 overview   1-150    camera drifts over the whole unit, room labels pop in
  K2 stairs   151-330    the SOS stack waits on the curved stair, then climbs; route line draws up the stair
  K3 route    331-540    stack crosses the living room and hallway to the bedroom door; route line + door ring
  K4 gun      541-720    Crowe steps in, Melendez (glowing) with the gun; scene holds, camera orbits the frozen moment
  K5 knife    721-900    the girl (glowing) with the knife, ring on Crowe's helmet
Mono dark blue, sculptural mannequins. Layout approximate."""
import bpy, math, os, sys
from mathutils import Vector, Matrix
bpy.ops.wm.open_mainfile(filepath="scenes/real/man.blend")
ROOT = os.getcwd(); S = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)
for f in ("realism", "common_build", "mannequin", "knox_apt"):
    exec(open(f"tools/{f}.py").read())
cycles_quality(S, samples=32, res=(1280, 720)); S.view_settings.look = "AgX - Medium High Contrast"
S.render.fps = 30
SHOTS = {"K1_overview": (1, 150), "K2_stairs": (151, 330), "K3_route": (331, 540), "K4_gun": (541, 720), "K5_knife": (721, 900)}
S.frame_start, S.frame_end = 1, 900
rig0, body0 = strip_man(); rig0.location = (0, 0, -50)
w = bpy.data.worlds.new("w"); S.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.003, 0.005, 0.01, 1)
P = apt_set()
FONT = bpy.data.fonts.load(os.path.join(ROOT, "assets", "fonts", "BebasNeue-Regular.ttf"))
GLOW_LINE = mat("route_glow", (0.55, 0.8, 1.0), emit=12)
stone = stone_mat("stone2", col=(0.16, 0.2, 0.3)); glow = glow_mat()
crowe_m = stone_mat("stone_crowe", col=(0.24, 0.3, 0.42))
girl_glow = glow_mat("girl_glow", col=(0.55, 0.75, 1.0), strength=2.4)


def rng(k):
    return SHOTS[k]


def label3d(text, loc, size, f_in, f_out, rot_z=0.0):
    cu = bpy.data.curves.new("lbl_" + text, "FONT"); cu.body = text; cu.font = FONT; cu.size = size
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.005; cu.materials.append(mat("lbl_m", (0.7, 0.85, 1.0), emit=5))
    o = link(bpy.data.objects.new("lbl_" + text, cu)); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    for f, s in ((f_in, 0.0), (f_in + 6, 1.12), (f_in + 10, 1.0), (f_out - 6, 1.0), (f_out, 0.0)):
        o.scale = (s,) * 3; o.keyframe_insert("scale", frame=f)
    return o


def curve(name, pts, visible=True, depth=0.03, m=GLOW_LINE):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1); sp.order_u = 3; sp.use_endpoint_u = True
    for p, (x, y, z) in zip(sp.points, pts):
        p.co = (x, y, z, 1)
    if visible:
        cu.bevel_depth = depth; cu.bevel_resolution = 3; cu.materials.append(m)
    return link(bpy.data.objects.new(name, cu))


def draw_line(ob, f0, f1, f_off):
    ob.data.bevel_factor_end = 0.0; ob.data.keyframe_insert("bevel_factor_end", frame=f0)
    ob.data.bevel_factor_end = 1.0; ob.data.keyframe_insert("bevel_factor_end", frame=f1)
    hide_tree(ob, [(f0 - 1, f_off)])


def ring(name, loc, r, f0, f_off, m=None):
    o = curve(name, [(r * math.cos(a), r * math.sin(a), 0) for a in [k / 8 * 2 * math.pi for k in range(8)]], m=m or mat("ring_glow", (0.55, 0.8, 1.0), emit=10))
    o.data.splines[0].use_cyclic_u = True; o.data.bevel_depth = 0.022; o.location = loc
    for f, sc in ((f0, 0.0), (f0 + 12, 1.2), (f0 + 22, 1.0), (f0 + 40, 1.08), (f0 + 58, 1.0)):
        o.scale = (sc,) * 3; o.keyframe_insert("scale", frame=f)
    hide_tree(o, [(f0, f_off)])
    return o


def helmet(rig, m):
    import bmesh
    pb = rig.pose.bones; bpy.context.view_layer.update()
    hd = rig.matrix_world @ pb["head"].head; tl = rig.matrix_world @ pb["head"].tail
    c = hd + (tl - hd) * 0.55
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.135)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.035], context="VERTS")
    me = bpy.data.meshes.new(rig.name + "_helmet"); bm.to_mesh(me); bm.free(); me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    h = link(bpy.data.objects.new(rig.name + "_helmet", me)); h.modifiers.new("sol", "SOLIDIFY").thickness = 0.015
    h.matrix_world = Matrix.Translation(c) @ rig.matrix_world.to_3x3().to_4x4()
    h.parent = rig; h.matrix_parent_inverse = rig.matrix_world.inverted()
    return h


def officer(name, pose, m, loc, rot_z, frames_on):
    rig, _ = mannequin(name, pose, m, loc, rot_z=rot_z, rifle=(pose == "rifle"))
    helmet(rig, m)
    hide_tree(rig, frames_on)
    return rig


def follow(rig, path, f0, f1, end, start=0.0):
    c = rig.constraints.new("FOLLOW_PATH"); c.target = path; c.use_curve_follow = True; c.use_fixed_location = True
    c.forward_axis = "TRACK_NEGATIVE_Y"; c.up_axis = "UP_Z"
    c.offset_factor = start; c.keyframe_insert("offset_factor", frame=f0)
    c.offset_factor = end; c.keyframe_insert("offset_factor", frame=f1)
    for fc in fcurves(rig):
        if "offset_factor" in fc.data_path:
            for k in fc.keyframe_points:
                k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"


# ---------------- K1 overview: room labels ----------------
a, b = rng("K1_overview")
for i, (t, loc) in enumerate((("STAIRWELL", (-1.45, 1.5, 2.35)), ("LIVING ROOM", (2.75, 1.0, 2.35)), ("HALLWAY", (7.55, 2.0, 2.35)),
                              ("SIDE ROOM", (7.55, 3.5, 2.35)), ("BEDROOM", (11.1, 1.0, 2.35)))):
    label3d(t, loc, 0.42, a + 20 + i * 14, b)
mel_k1 = mannequin("mel_k1", "stand", glow, P["mel"], rot_z=-45)[0]; hide_tree(mel_k1, [(a, b)])
girl_k1 = mannequin("girl_k1", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0]; hide_tree(girl_k1, [(a, b)])

# ---------------- K2 stairs: stack waits, then climbs ----------------
a, b = rng("K2_stairs")
sp = P["stair_pts"]
stair_path = curve("stair_walk", [(p[0], p[1], p[2] - 0.0) for p in sp] + [(0.35, 1.7, 0.0), (1.2, 1.75, 0.0)], visible=False); stair_path.hide_render = True
stair_line = curve("stair_line", [(p[0], p[1], p[2] + 0.03) for p in sp] + [(0.35, 1.7, 0.03), (1.2, 1.75, 0.03)])
draw_line(stair_line, a + 70, a + 150, b)
for i in range(4):
    r = officer(f"st{i}", "rifle", stone, Vector((0, 0, 0)), 0, [(a, b)])
    start = max(0.0, 0.42 - 0.11 * i)            # waiting spread up the stair
    follow(r, stair_path, a + 75 + 8 * i, b - 10, min(1.0, 0.98 - 0.1 * i), start=start)
    c = r.constraints["Follow Path"]; c.offset_factor = start; c.keyframe_insert("offset_factor", frame=a)
    walk(r, a + 75 + 8 * i, b - 10, period=18)
label3d("10:25 AM", (-1.45, -0.6, 2.4), 0.35, a + 8, a + 70)

# ---------------- K3 route: through the unit to the bedroom door ----------------
a, b = rng("K3_route")
RPTS = [(0.3, 1.7, 0.0), (1.6, 1.8, 0), (3.3, 1.45, 0), (4.8, 1.9, 0), (6.0, 2.0, 0), (7.6, 2.0, 0), (9.0, 2.0, 0)]
route_walk = curve("route_walk", RPTS, visible=False); route_walk.hide_render = True
route_line = curve("route_line", [(x, y, z + 0.03) for x, y, z in RPTS])
draw_line(route_line, a + 10, a + 150, b)
for i in range(4):
    r = officer(f"rt{i}", "rifle", stone, Vector((0, 0, 0)), 0, [(a, b)])
    follow(r, route_walk, a + 15 + 10 * i, a + 165, 1.0 - 0.1 * i)
    walk(r, a + 15 + 10 * i, a + 165, period=18)
ring("door_ring", (9.6, 2.0, 0.05), 0.5, a + 150, b)
mel_k3 = mannequin("mel_k3", "stand", glow, P["mel"], rot_z=-45)[0]; hide_tree(mel_k3, [(a, b)])
girl_k3 = mannequin("girl_k3", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0]; hide_tree(girl_k3, [(a, b)])
label3d("10:26 AM", (4.8, 3.2, 2.4), 0.35, a + 10, a + 90)

# ---------------- K4 gun: Crowe steps in, the gun ----------------
a, b = rng("K4_gun")
crowe = officer("crowe", "rifle", crowe_m, Vector((9.1, 1.95, 0)), 90, [(a, b)])
crowe.location = (9.1, 1.95, 0); crowe.keyframe_insert("location", frame=a)
crowe.location = (10.15, 1.95, 0); crowe.keyframe_insert("location", frame=a + 45)
walk(crowe, a, a + 45, period=18)
for i, (x, y) in enumerate(((9.15, 2.15), (8.55, 1.9))):
    officer(f"door{i}", "rifle", stone, Vector((x, y, 0)), 90, [(a, b)])
mel = mannequin("mel_gun", "point_gun", glow, P["mel"], rot_z=-45)[0]; hide_tree(mel, [(a, b)])
bpy.context.view_layer.update()
hand = mel.matrix_world @ mel.pose.bones["lowerarm01.R"].tail
gun = cuboid("mel_gunobj", (hand.x, hand.y, hand.z), (0.03, 0.11, 0.06), mat("gun_glow", (0.8, 0.92, 1.0), emit=14), rot_z=math.radians(-45))
hide_tree(gun, [(a, b)])
girl_k4 = mannequin("girl_k4", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0]; hide_tree(girl_k4, [(a, b)])
g_ring = ring("gun_ring", (hand.x, hand.y, hand.z), 0.22, a + 62, b); g_ring.rotation_euler = (math.radians(90), 0, math.radians(45))
label3d("GUN", (hand.x - 0.25, hand.y - 0.25, hand.z + 0.45), 0.28, a + 66, b)
fire_line = curve("fire_line", [(hand.x, hand.y, hand.z), ((hand.x + 10.4) / 2, (hand.y + 2.05) / 2, (hand.z + 1.45) / 2 + 0.02), (10.4, 2.05, 1.45)],
                  m=mat("fire_glow", (0.9, 0.95, 1.0), emit=8), depth=0.01)
draw_line(fire_line, a + 70, a + 90, b)

# ---------------- K5 knife: the girl, Crowe's helmet ----------------
a, b = rng("K5_knife")
crowe5 = officer("crowe5", "rifle", crowe_m, Vector((10.15, 1.95, 0)), 90, [(a, b)])
for i, (x, y) in enumerate(((9.15, 2.15), (8.55, 1.9))):
    officer(f"door5_{i}", "rifle", stone, Vector((x, y, 0)), 90, [(a, b)])
mel_down = mannequin("mel_down", "stand", stone, Vector((11.15, 2.75, 0.14)), rot_z=-45)[0]
mel_down.rotation_euler = (math.radians(-90), 0, math.radians(-45 + 180)); hide_tree(mel_down, [(a, b)])
girl_sit = mannequin("girl_k5s", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0]; hide_tree(girl_sit, [(a, a + 59)])
girl_up = mannequin("girl_k5", "swing", girl_glow, Vector((10.75, 1.75, 0)), rot_z=-122, scale=0.88)[0]; hide_tree(girl_up, [(a + 60, b)])
bpy.context.view_layer.update()
kh = girl_up.matrix_world @ girl_up.pose.bones["lowerarm01.R"].tail
knife = cuboid("knife", (kh.x, kh.y, kh.z + 0.12), (0.012, 0.03, 0.14), mat("knife_glow", (0.9, 0.95, 1.0), emit=16))
hide_tree(knife, [(a + 60, b)])
hpos = crowe5.matrix_world @ crowe5.pose.bones["head"].tail
h_ring = ring("helmet_ring", (hpos.x, hpos.y, hpos.z + 0.02), 0.25, a + 72, b)
label3d("KNIFE", (kh.x + 0.55, kh.y - 0.7, kh.z + 0.3), 0.26, a + 66, b)

# ---------------- lights ----------------
sun = bpy.data.lights.new("moon", "SUN"); sun.energy = 0.5; sun.color = (0.5, 0.65, 1.0)
so = link(bpy.data.objects.new("moon", sun)); so.rotation_euler = (math.radians(30), 0, math.radians(25))
for k, (x, y, z) in enumerate(((-1.4, 1.5, 3.6), (-1.4, 1.5, -0.8), (1.5, 1.8, 3.6), (3.6, 1.9, 3.6), (7.5, 2.0, 3.6), (11.0, 1.9, 3.6), (7.5, 3.5, 3.6))):
    l = point(f"pool{k}", Vector((x, y, z)), 160 if z > 0 else 60, (0.55, 0.7, 1.0), r=0.6); l.visible_camera = False

# ---------------- cameras ----------------
def shot_cam(name, keys, lens=26, fstop=11):
    cam, aim = camera(name, Vector(keys[0][1]), Vector(keys[0][2]), lens=lens, fstop=fstop)
    for f, cl, al in keys:
        cam.location = cl; cam.keyframe_insert("location", frame=f); aim.location = al; aim.keyframe_insert("location", frame=f)
    for o in (cam, aim):
        for fc in fcurves(o):
            for k in fc.keyframe_points:
                k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"
    return cam


cams = {
    "K1_overview": shot_cam("cam_k1", [(1, (3.6, -3.4, 12.5), (4.4, 1.7, -0.6)), (150, (7.0, -2.4, 11.5), (6.6, 1.8, -0.4))], lens=24),
    "K2_stairs": shot_cam("cam_k2", [(151, (-1.0, -1.6, 5.6), (-1.45, 1.45, -1.6)), (330, (0.6, -1.4, 5.8), (0.0, 1.6, -0.6))], lens=24),
    "K3_route": shot_cam("cam_k3", [(331, (1.6, 0.3, 11.0), (1.8, 1.9, 0.0)), (540, (8.6, 0.8, 10.0), (8.8, 2.0, 0.0))], lens=26),
    "K4_gun": shot_cam("cam_k4", [(541, (8.6, -1.6, 6.0), (10.4, 2.1, 0.6)), (620, (9.0, -1.0, 5.2), (10.5, 2.1, 0.8)),
                                   (720, (12.6, -0.9, 4.9), (10.6, 2.2, 0.9))], lens=28),
    "K5_knife": shot_cam("cam_k5", [(721, (12.8, -0.5, 5.2), (10.6, 1.9, 0.8)), (900, (12.1, 0.2, 3.9), (10.4, 1.9, 1.3))], lens=30),
}
for k, (f0, f1) in SHOTS.items():
    mk = S.timeline_markers.new(k, frame=f0); mk.camera = cams[k]
S.camera = cams["K1_overview"]
os.makedirs("scenes/knox_sky", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes/knox_sky/sky_main.blend"))
if "--still" in sys.argv:
    S.cycles.samples = 12
    for f in map(int, sys.argv[sys.argv.index("--still") + 1].split(",")):
        S.frame_set(f); S.camera = cams[[k for k, (f0, f1) in SHOTS.items() if f0 <= f <= f1][0]]
        S.render.filepath = f"/tmp/et/sky2_{f}.png"; bpy.ops.render.render(write_still=True)
