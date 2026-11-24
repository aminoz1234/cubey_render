"""v3: fixed shots 2-5 (upright walkers, rifles held with IK, props in hands, billboard labels, oblique cameras).
Knoxville sky-view explainers on the detailed bodycam-based layout (tools/knox_apt.py). Five shots, one blend:
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


def label3d(text, loc, size, f_in, f_out, rot_z=0.0, face=None):
    cu = bpy.data.curves.new("lbl_" + text, "FONT"); cu.body = text; cu.font = FONT; cu.size = size
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.005; cu.materials.append(mat("lbl_m", (0.7, 0.85, 1.0), emit=5))
    o = link(bpy.data.objects.new("lbl_" + text, cu)); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    if face is not None:   # billboard toward the shot's camera
        c = o.constraints.new("TRACK_TO"); c.target = face; c.track_axis = "TRACK_Z"; c.up_axis = "UP_Y"
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
    rig, _ = mannequin(name, "stand", m, loc, rot_z=rot_z, rifle=True)
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


# ---------------- cameras first (labels face them) ----------------
sun = bpy.data.lights.new("moon", "SUN"); sun.energy = 0.5; sun.color = (0.5, 0.65, 1.0)
so = link(bpy.data.objects.new("moon", sun)); so.rotation_euler = (math.radians(30), 0, math.radians(25))
for k, (x, y, z, e) in enumerate(((-1.4, 1.5, 3.6, 160), (-1.4, 1.5, -1.2, 140), (-0.6, 0.4, -0.4, 60), (1.5, 1.8, 3.6, 160), (3.6, 1.9, 3.6, 160),
                                  (7.5, 2.0, 3.6, 160), (11.0, 1.9, 3.6, 170), (7.5, 3.5, 3.6, 120))):
    l = point(f"pool{k}", Vector((x, y, z)), e, (0.55, 0.7, 1.0), r=0.6); l.visible_camera = False


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
    "K2_stairs": shot_cam("cam_k2", [(151, (-3.9, -1.9, 3.6), (-1.3, 1.4, -1.4)), (330, (-3.0, -1.3, 4.0), (0.0, 1.6, -0.4))], lens=24),
    "K3_route": shot_cam("cam_k3", [(331, (1.0, -1.7, 7.4), (1.5, 1.9, 0.5)), (540, (8.2, -1.4, 7.0), (8.6, 2.0, 0.6))], lens=28),
    "K4_gun": shot_cam("cam_k4", [(541, (9.6, -1.2, 5.0), (10.2, 2.1, 0.8)), (620, (10.3, -0.9, 4.6), (10.5, 2.2, 1.0)), (720, (11.4, -0.8, 4.3), (10.6, 2.2, 1.0))], lens=26),
    "K5_knife": shot_cam("cam_k5", [(721, (10.9, -1.0, 4.6), (10.5, 2.0, 1.0)), (900, (10.6, -0.5, 3.6), (10.45, 1.9, 1.2))], lens=28),
}
for k, (f0, f1) in SHOTS.items():
    mk = S.timeline_markers.new(k, frame=f0); mk.camera = cams[k]
S.camera = cams["K1_overview"]


def ring_face(name, loc, r, f0, f_off, cam):
    o = ring(name, loc, r, f0, f_off)
    c = o.constraints.new("TRACK_TO"); c.target = cam; c.track_axis = "TRACK_Z"; c.up_axis = "UP_Y"
    return o


# ---------------- K1 overview (unchanged, already rendered) ----------------
a, b = rng("K1_overview")
for i, (t, loc) in enumerate((("STAIRWELL", (-1.45, 1.5, 2.35)), ("LIVING ROOM", (2.75, 1.0, 2.35)), ("HALLWAY", (7.55, 2.0, 2.35)),
                              ("SIDE ROOM", (7.55, 3.5, 2.35)), ("BEDROOM", (11.1, 1.0, 2.35)))):
    label3d(t, loc, 0.42, a + 20 + i * 14, b)
hide_tree(mannequin("mel_k1", "stand", glow, P["mel"], rot_z=-45)[0], [(a, b)])
hide_tree(mannequin("girl_k1", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0], [(a, b)])

# ---------------- K2 stairs: the stack waits on the stair, then climbs into the unit ----------------
a, b = rng("K2_stairs")
sp = P["stair_pts"]
SP = [(p[0], p[1], p[2]) for p in sp] + [(0.35, 1.7, 0.0), (1.2, 1.75, 0.0)]
stair_path = curve("stair_walk", SP, visible=False); stair_path.hide_render = True
stair_line = curve("stair_line", [(x, y, z + 0.03) for x, y, z in SP]); draw_line(stair_line, a + 65, a + 160, b)
for i in range(4):
    r = officer(f"st{i}", "rifle", stone, Vector((0, 0, 0)), 0, [(a, b)])
    wait, top = 0.55 - 0.16 * i, 1.0 - 0.16 * i
    move_along(r, stair_path, [(a, wait), (a + 60 + 6 * i, wait), (b - 12, top), (b, top)])
    walk(r, a + 60 + 6 * i, b - 12, period=16, key_z=False)
label3d("10:25 AM", (-1.45, -0.3, 0.9), 0.3, a + 6, a + 70, face=cams["K2_stairs"])

# ---------------- K3 route: through the unit to the bedroom door ----------------
a, b = rng("K3_route")
RPTS = [(0.3, 1.7, 0.0), (1.6, 1.8, 0), (3.3, 1.45, 0), (4.8, 1.9, 0), (6.0, 2.0, 0), (7.6, 2.0, 0), (9.0, 2.0, 0)]
route_walk = curve("route_walk", RPTS, visible=False); route_walk.hide_render = True
route_line = curve("route_line", [(x, y, z + 0.03) for x, y, z in RPTS]); draw_line(route_line, a + 10, a + 150, b)
for i in range(4):
    r = officer(f"rt{i}", "rifle", stone, Vector((0, 0, 0)), 0, [(a, b)])
    move_along(r, route_walk, [(a, 0.0), (a + 12 + 10 * i, 0.0), (a + 165, 1.0 - 0.095 * i), (b, 1.0 - 0.095 * i)])
    walk(r, a + 12 + 10 * i, a + 165, period=16, key_z=False)
ring("door_ring", (9.6, 2.0, 0.05), 0.5, a + 150, b)
hide_tree(mannequin("mel_k3", "stand", glow, P["mel"], rot_z=-45)[0], [(a, b)])
hide_tree(mannequin("girl_k3", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0], [(a, b)])
label3d("10:26 AM", (4.8, 1.2, 2.5), 0.32, a + 10, a + 90, face=cams["K3_route"])

# ---------------- K4 gun: Crowe steps in, Melendez with the pistol ----------------
a, b = rng("K4_gun")
crowe = officer("crowe", "rifle", crowe_m, Vector((0, 0, 0)), 0, [(a, b)])
cpath = curve("crowe_path", [(8.9, 1.95, 0), (9.5, 1.95, 0), (10.15, 1.95, 0)], visible=False); cpath.hide_render = True
move_along(crowe, cpath, [(a, 0.0), (a + 45, 1.0), (b, 1.0)]); walk(crowe, a, a + 45, period=16, key_z=False)
for i, (x, y) in enumerate(((9.15, 2.2), (8.55, 1.9))):
    officer(f"door{i}", "rifle", stone, Vector((x, y, 0)), 90, [(a, b)])
mel = mannequin("mel_gun", "point_gun", glow, P["mel"], rot_z=-45)[0]; hide_tree(mel, [(a, b)])
gun = pistol_in_hand(mel, mat("gun_glow", (0.85, 0.94, 1.0), emit=14)); hide_tree(gun, [(a, b)])
bpy.context.view_layer.update(); gp = gun.matrix_world.translation.copy()
ring_face("gun_ring", (gp.x, gp.y, gp.z), 0.2, a + 62, b, cams["K4_gun"])
label3d("GUN", (gp.x, gp.y + 0.15, gp.z + 0.42), 0.26, a + 66, b, face=cams["K4_gun"])
hide_tree(mannequin("girl_k4", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0], [(a, b)])

# ---------------- K5 knife: the girl, Crowe's helmet ----------------
a, b = rng("K5_knife")
crowe5 = officer("crowe5", "rifle", crowe_m, Vector((10.15, 1.95, 0)), 90, [(a, b)])
for i, (x, y) in enumerate(((9.15, 2.2), (8.55, 1.9))):
    officer(f"door5_{i}", "rifle", stone, Vector((x, y, 0)), 90, [(a, b)])
mel_down = mannequin("mel_down", "stand", stone, Vector((10.3, 3.05, 0.14)), rot_z=-45)[0]
mel_down.rotation_euler = (math.radians(-90), 0, math.radians(-90)); hide_tree(mel_down, [(a, b)])
hide_tree(mannequin("girl_k5s", "sit", girl_glow, P["girl"], rot_z=200, scale=0.85)[0], [(a, a + 59)])
girl_up = mannequin("girl_k5", "swing", girl_glow, Vector((10.72, 1.7, 0)), rot_z=-122, scale=0.86)[0]; hide_tree(girl_up, [(a + 60, b)])
kn = knife_in_hand(girl_up, mat("knife_glow", (0.92, 0.96, 1.0), emit=16)); hide_tree(kn, [(a + 60, b)])
bpy.context.view_layer.update(); kp = kn.matrix_world.translation.copy()
hp = crowe5.matrix_world @ crowe5.pose.bones["head"].tail
ring_face("helmet_ring", (hp.x, hp.y, hp.z + 0.03), 0.24, a + 72, b, cams["K5_knife"])
label3d("KNIFE", (kp.x + 0.1, kp.y - 0.1, kp.z + 0.45), 0.24, a + 66, b, face=cams["K5_knife"])

os.makedirs("scenes/knox_sky", exist_ok=True)
for f in bpy.data.fonts:
    if f.filepath and f.filepath != "<builtin>" and not f.packed_file:
        f.pack()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes/knox_sky/sky_v3.blend"))
if "--still" in sys.argv:
    S.cycles.samples = 10
    for f in map(int, sys.argv[sys.argv.index("--still") + 1].split(",")):
        S.frame_set(f); S.camera = cams[[k for k, (f0, f1) in SHOTS.items() if f0 <= f <= f1][0]]
        S.render.filepath = f"/tmp/et/v3_{f}.png"; bpy.ops.render.render(write_still=True)
