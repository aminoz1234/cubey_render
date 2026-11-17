"""Seed video: "This is what happens when a seed grows inside your body".
Builds every set, prop, camera and cut (timeline markers) in one scene, timed to the voiceover.
Run inside Blender (5.2+). Safe to re-run: it starts from an empty scene.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Euler

FPS = 30
T_END = 36.2


def F(t):  # seconds -> frame
    return int(round(t * FPS)) + 1


random.seed(7)
if bpy.app.background:
    bpy.ops.wm.read_factory_settings(use_empty=True)
else:  # live session (Blender MCP): wipe the scene data but keep the user's preferences and add-ons
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.curves, bpy.data.lights, bpy.data.cameras,
                 bpy.data.materials, bpy.data.textures, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
S = bpy.context.scene
S.timeline_markers.clear()
S.render.fps = FPS
S.frame_start, S.frame_end = 1, F(T_END)
S.render.resolution_x, S.render.resolution_y = 720, 1280
S.render.engine = "CYCLES"
S.cycles.samples = 24
S.cycles.use_denoising = True
S.view_settings.view_transform = "Standard"
S.view_settings.look = "None"
S.view_settings.exposure = -1.0
W = bpy.data.worlds.new("world"); S.world = W
W.use_nodes = True
W.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.03, 1)
W.node_tree.nodes["Background"].inputs[1].default_value = 0.4

# ---------------------------------------------------------------- helpers
MATS = {}


def mat(name, col, rough=0.5, emit=0.0, coat=0.0, trans=0.0, metal=0.0, alpha=1.0, ecol=None):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*(ecol or col), 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    MATS[name] = m
    return m


def link(ob, coll=None):
    (coll or S.collection).objects.link(ob)
    return ob


def smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def sphere(name, loc, r, m, seg=32, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    ob = bpy.context.object; ob.name = name; ob.scale = scale
    smooth(ob); ob.data.materials.append(m)
    if parent:
        ob.parent = parent; ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def box(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object; ob.name = name; ob.scale = size
    ob.data.materials.append(m)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = 3
    return ob


def cyl(name, loc, r, depth, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.data.materials.append(m)
    return ob


def key(ob, path, f, val, interp="BEZIER"):
    setattr(ob, path, val) if not isinstance(val, (tuple, list)) else setattr(ob, path, val)
    ob.keyframe_insert(path, frame=f)
    act = ob.animation_data.action
    for fc in getattr(act, "fcurves", []):
        for kp in fc.keyframe_points:
            if int(kp.co.x) == f:
                kp.interpolation = interp


def keyd(datablock, path, f, val):
    setattr(datablock, path, val)
    datablock.keyframe_insert(path, frame=f)


def light(name, kind, loc, energy, col=(1, 1, 1), size=0.5, rot=(0, 0, 0)):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
    if kind == "AREA":
        d.size = size
    else:
        d.shadow_soft_size = size
    ob = bpy.data.objects.new(name, d); ob.location = loc; ob.rotation_euler = rot
    return link(ob)


CAMS = []


def camera(name, loc, target=None, lens=35, rot=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = 0.01
    ob = link(bpy.data.objects.new(name, d)); ob.location = loc
    if rot:
        ob.rotation_euler = rot
    if target is not None:
        e = bpy.data.objects.new(name + "_aim", None); e.location = target; link(e)
        c = ob.constraints.new("TRACK_TO"); c.target = e; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
        ob["aim"] = e.name
    CAMS.append(ob)
    return ob


def cut(t, cam):
    mk = S.timeline_markers.new(cam.name, frame=F(t)); mk.camera = cam


def path_curve(name, pts, closed=False):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for p, co in zip(sp.bezier_points, pts):
        p.co = co; p.handle_left_type = p.handle_right_type = "AUTO"
    ob = link(bpy.data.objects.new(name, cu))
    return ob


def tube_from(curve_ob, radius, m, name, bumps=0.2, noise=0.6, rings=0.0):
    """Hollow fleshy tunnel along a curve (camera goes inside)."""
    cu = curve_ob.data.copy(); cu.bevel_depth = radius; cu.bevel_resolution = 10
    cu.resolution_u = 24; cu.use_fill_caps = False
    ob = link(bpy.data.objects.new(name, cu))
    ob.matrix_world = curve_ob.matrix_world
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.object; ob.name = name
    smooth(ob)
    if bumps:
        d = ob.modifiers.new("bumps", "DISPLACE")
        tx = bpy.data.textures.new(name + "_n", "CLOUDS"); tx.noise_scale = noise
        d.texture = tx; d.texture_coords = "GLOBAL"; d.strength = -bumps; d.mid_level = 0.5
    if rings:  # cartilage rings for the windpipe
        tx2 = bpy.data.textures.new(name + "_r", "WOOD"); tx2.wood_type = "RINGS"; tx2.noise_basis_2 = "SAW"
        tx2.turbulence = 0.0
        d2 = ob.modifiers.new("rings", "DISPLACE"); d2.texture = tx2; d2.texture_coords = "GLOBAL"
        d2.strength = -rings
    ob.data.materials.append(m)
    return ob


def follow(ob, curve_ob, f0, f1, o0, o1, cam=False):
    ob.location = (0, 0, 0)
    c = ob.constraints.new("FOLLOW_PATH"); c.target = curve_ob
    c.use_fixed_location = True; c.use_curve_follow = True
    if cam:
        c.forward_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    else:
        c.forward_axis = "FORWARD_Y"; c.up_axis = "UP_Z"
    c.offset_factor = o0; c.keyframe_insert("offset_factor", frame=f0)
    c.offset_factor = o1; c.keyframe_insert("offset_factor", frame=f1)
    return c


def sprout(name, base, pts, m_stem, m_leaf, f0, f1, thick=0.035, leaf=0.18):
    """Green stem that grows along pts between frames f0..f1, with two leaves that unfold at the end."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = thick
    cu.bevel_resolution = 6; cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for p, co in zip(sp.bezier_points, pts):
        p.co = co; p.handle_left_type = p.handle_right_type = "AUTO"
    ob = link(bpy.data.objects.new(name, cu)); ob.location = base
    cu.materials.append(m_stem)
    keyd(cu, "bevel_factor_end", f0, 0.0); keyd(cu, "bevel_factor_end", f1, 1.0)
    tip = Vector(pts[-1]) + Vector(base)
    leaves = []
    for i, ang in enumerate((-0.7, 0.7)):
        lf = sphere(f"{name}_leaf{i}", tip, leaf, m_leaf, seg=24, scale=(1, 0.42, 0.12))
        lf.rotation_euler = (0.3, ang, 0.6 if i else -0.6)
        lf.location = tip + Vector((0.12 * (1 if i else -1), 0, 0.02))
        key(lf, "scale", f0, (0.001, 0.001, 0.001)); key(lf, "scale", f1 - 6, (0.001, 0.001, 0.001))
        key(lf, "scale", f1 + 6, (1, 0.42, 0.12))
        leaves.append(lf)
    return ob, leaves


# ---------------------------------------------------------------- materials
SKIN = mat("skin", (0.9, 0.48, 0.3), 0.45, coat=0.15)
SHIRT = mat("shirt", (0.95, 0.95, 0.92), 0.6)
PANTS = mat("pants", (0.15, 0.22, 0.45), 0.7)
WHITE = mat("eye_white", (0.98, 0.98, 0.98), 0.2, coat=0.6)
BLACK = mat("pupil", (0.01, 0.01, 0.01), 0.15, coat=0.8)
BROW = mat("brow", (0.12, 0.07, 0.04), 0.7)
MOUTH = mat("mouth", (0.35, 0.03, 0.04), 0.5)
FLESH = mat("flesh", (0.62, 0.11, 0.10), 0.22, coat=0.5)
GUT = mat("gut", (0.55, 0.12, 0.1), 0.22, coat=0.7)
LUNG = mat("lung", (0.85, 0.3, 0.35), 0.25, coat=0.8)
ACID = mat("acid", (0.25, 0.7, 0.05), 0.05, emit=0.45, coat=1.0, ecol=(0.3, 0.9, 0.05))
BUB = mat("bubble", (0.7, 1.0, 0.4), 0.05, emit=0.6, trans=0.6, ecol=(0.5, 1.0, 0.2))
SEED = mat("seed", (0.03, 0.025, 0.02), 0.25, coat=0.8)
PEA = mat("pea", (0.12, 0.42, 0.03), 0.3, coat=0.4)
STEM = mat("stem", (0.06, 0.32, 0.02), 0.45)
LEAF = mat("leaf", (0.04, 0.38, 0.03), 0.35, coat=0.3)
RIND = mat("rind", (0.05, 0.35, 0.06), 0.4)
MELON = mat("melon", (0.9, 0.05, 0.08), 0.35, coat=0.3)
WALL = mat("wall", (0.08, 0.35, 0.42), 0.8)
FLOOR = mat("floor", (0.85, 0.75, 0.6), 0.6)
TABLE = mat("table", (0.55, 0.32, 0.16), 0.5)
PLATE = mat("plate", (0.95, 0.95, 0.95), 0.2, coat=0.6)
METAL = mat("metal", (0.8, 0.8, 0.82), 0.25, metal=1.0)
WATER = mat("droplet", (0.9, 0.95, 1.0), 0.02, trans=0.95, coat=1.0)
XBG = mat("xray_bg", (0.02, 0.05, 0.1), 0.6, emit=1.2, ecol=(0.05, 0.15, 0.3))
XBONE = mat("xray_bone", (0.8, 0.9, 1.0), 0.5, emit=6.0, ecol=(0.7, 0.85, 1.0))
XLUNG = mat("xray_lung", (0.1, 0.18, 0.3), 0.6, emit=2.0, ecol=(0.15, 0.3, 0.5))
XSPOT = mat("xray_spot", (0.0, 0.0, 0.0), 0.6, emit=0.0)
RED = mat("alarm_red", (1, 0.05, 0.05), 0.4, emit=12.0)


# ---------------------------------------------------------------- the guy
def build_guy(o, name):
    """Cartoony bald guy (Zack D. Films style), facing -Y. Returns dict of parts."""
    o = Vector(o)
    body = sphere(name + "_body", o + Vector((0, 0, 0.95)), 0.42, SHIRT, scale=(1, 0.8, 1.25))
    sphere(name + "_hips", o + Vector((0, 0, 0.45)), 0.36, PANTS, scale=(1.05, 0.82, 0.7))
    for s in (-1, 1):
        cyl(name + f"_leg{s}", o + Vector((0.16 * s, 0, 0.18)), 0.12, 0.45, PANTS)
        sphere(name + f"_arm{s}", o + Vector((0.5 * s, -0.02, 0.95)), 0.11, SHIRT, scale=(1, 1, 3.2))
        sphere(name + f"_hand{s}", o + Vector((0.53 * s, -0.05, 0.6)), 0.1, SKIN)
    neck = cyl(name + "_neck", o + Vector((0, 0, 1.47)), 0.12, 0.2, SKIN)
    head = sphere(name + "_head", o + Vector((0, 0, 1.85)), 0.38, SKIN, seg=48, scale=(1, 0.95, 1.08))
    parts = {"body": body, "head": head}
    for s in (-1, 1):
        sphere(name + f"_ear{s}", head.location + Vector((0.37 * s, 0.02, 0.0)), 0.08, SKIN, parent=head, scale=(0.6, 1, 1.2))
        ew = sphere(name + f"_eye{s}", head.location + Vector((0.13 * s, -0.31, 0.08)), 0.1, WHITE, parent=head, scale=(1, 0.6, 1.25))
        pu = sphere(name + f"_pupil{s}", head.location + Vector((0.13 * s, -0.37, 0.07)), 0.045, BLACK, parent=head, scale=(1, 0.5, 1.2))
        br = sphere(name + f"_brow{s}", head.location + Vector((0.14 * s, -0.33, 0.24)), 0.07, BROW, parent=head, scale=(1.4, 0.4, 0.35))
        br.rotation_euler = (0, 0.25 * s, 0)
        parts[f"eye{s}"], parts[f"pupil{s}"], parts[f"brow{s}"] = ew, pu, br
    nose = sphere(name + "_nose", head.location + Vector((0, -0.38, -0.04)), 0.07, SKIN, parent=head, scale=(1, 0.9, 1.1))
    mouth = sphere(name + "_mouth", head.location + Vector((0, -0.33, -0.2)), 0.1, MOUTH, parent=head, scale=(1.3, 0.4, 0.25))
    parts["mouth"] = mouth
    return parts


def mouth_open(p, f, amount):  # 0 closed .. 1 wide
    key(p["mouth"], "scale", f, (1.3 + 0.2 * amount, 0.4, 0.25 + 0.9 * amount))


def eyes(p, f, wide=1.0, squint=False, pupil=1.0):
    for s in (-1, 1):
        key(p[f"eye{s}"], "scale", f, (1, 0.6, 0.35 if squint else 1.25 * wide))
        key(p[f"pupil{s}"], "scale", f, (pupil, 0.5, (0.3 if squint else 1.2 * pupil)))


def brows(p, f, up=0.0):
    for s in (-1, 1):
        b = p[f"brow{s}"]
        key(b, "location", f, (b.location.x, b.location.y, b.location.z) if up == 0 else (b.location.x, b.location.y, b.location.z))
        key(b, "rotation_euler", f, (0, (0.25 - 0.55 * up) * s, 0))


def room(o, wall=WALL):
    o = Vector(o)
    fl = box("floor", o + Vector((0, 0, -0.05)), (12, 12, 0.1), FLOOR)
    wl = box("wall", o + Vector((0, 2.5, 3)), (12, 0.1, 6), wall)
    return fl, wl


# ============================================================ SET A: guy (hook, watermelon, relief)
A = Vector((0, 0, 0))
room(A)
guy = build_guy(A, "guy")
light("A_key", "AREA", A + Vector((-2.2, -3, 3.5)), 900, (1, 0.93, 0.85), size=3, rot=(math.radians(50), 0, math.radians(-35)))
light("A_rim", "AREA", A + Vector((2.5, 1.5, 3)), 500, (0.6, 0.8, 1), size=2, rot=(math.radians(-50), math.radians(30), 0))
light("A_fill", "AREA", A + Vector((2, -3, 1.5)), 200, (1, 0.9, 1), size=3, rot=(math.radians(70), 0, math.radians(30)))
H = guy["head"].location
# hook: vine curling out of his mouth
vine, vleaves = sprout("hook_vine", H + Vector((0, -0.36, -0.2)),
                       [(0, 0, 0), (0, -0.2, -0.02), (0.15, -0.35, 0.12), (0.3, -0.4, 0.38), (0.22, -0.42, 0.62)],
                       STEM, LEAF, F(0.0), F(1.6), thick=0.045, leaf=0.15)
for ob in [vine] + vleaves:
    key(ob, "hide_render", F(0), False); key(ob, "hide_render", F(3.0), True)
mouth_open(guy, F(0), 0.9); eyes(guy, F(0), wide=1.25, pupil=0.7); brows(guy, F(0), 1.0)
mouth_open(guy, F(3.0), 0.9)
# watermelon slice in right hand, bite at 3.4
hand = bpy.data.objects["guy_hand-1"]
slice_o = H + Vector((0.0, -0.62, -0.3))
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.24, depth=0.07, location=(0, 0, 0))
rind = bpy.context.object; rind.name = "melon_rind"; rind.data.materials.append(RIND)
bm = bmesh.new(); bm.from_mesh(rind.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_inner=True)
bmesh.ops.contextual_create(bm, geom=[e for e in bm.edges if e.is_boundary])
bm.to_mesh(rind.data); bm.free()
fleshm = rind.copy(); fleshm.data = rind.data.copy(); link(fleshm); fleshm.name = "melon_flesh"
fleshm.data.materials[0] = MELON; fleshm.scale = (0.86, 0.86, 1.15)
for ob in (rind, fleshm):
    ob.rotation_euler = (math.radians(90), 0, 0); ob.location = slice_o
seeds = []
for i in range(7):
    a = math.radians(25 + i * 20); r = 0.17
    sd = sphere(f"melon_seed{i}", slice_o + Vector((r * math.cos(a), -0.06, r * math.sin(a))), 0.022, SEED, seg=16, scale=(0.6, 0.3, 1))
    seeds.append(sd)
for ob in [rind, fleshm] + seeds:
    key(ob, "hide_render", F(0), True); key(ob, "hide_render", F(3.0), False); key(ob, "hide_render", F(4.75), True)
# slice moves to the mouth (bite) and the hero seed pops at the camera
for ob in [rind, fleshm] + seeds:
    l0 = ob.location.copy()
    key(ob, "location", F(3.05), l0 + Vector((0, -0.15, -0.15)))
    key(ob, "location", F(3.55), l0 + Vector((0, 0.18, 0.02)))
    key(ob, "location", F(3.85), l0 + Vector((0, -0.05, -0.05)))
mouth_open(guy, F(3.3), 1.0); mouth_open(guy, F(3.6), 0.1); mouth_open(guy, F(4.0), 0.35)
eyes(guy, F(3.05), 1.0, pupil=1.0); eyes(guy, F(3.6), squint=True); eyes(guy, F(4.2), 1.1)
brows(guy, F(3.05), 0.0)
hero = seeds[3]
key(hero, "location", F(3.85), hero.location.copy())
key(hero, "location", F(4.6), H + Vector((0, -0.34, -0.2)))
# relief beat ("out it goes") 15.6-16.45: big grin, brows up
mouth_open(guy, F(15.55), 0.15); eyes(guy, F(15.55), 1.0); brows(guy, F(15.55), 0.0)
mouth_open(guy, F(15.8), 0.55); eyes(guy, F(15.8), squint=True); brows(guy, F(15.8), 0.8)
key(guy["head"], "rotation_euler", F(15.6), (0, 0, 0)); key(guy["head"], "rotation_euler", F(16.0), (0.15, 0, 0.1))
camA1 = camera("cam01_hook", H + Vector((0.25, -2.6, 0.15)), H + Vector((0, 0, 0.12)), lens=40)
key(camA1, "location", F(0), H + Vector((0.25, -2.6, 0.15))); key(camA1, "location", F(3.05), H + Vector((0.1, -1.9, 0.1)))
camA2 = camera("cam02_bite", H + Vector((-1.0, -1.9, 0.0)), H + Vector((0, -0.4, -0.2)), lens=45)
key(camA2, "location", F(3.05), H + Vector((-1.0, -2.0, 0.05))); key(camA2, "location", F(4.7), H + Vector((-0.7, -1.6, -0.05)))
camA3 = camera("cam08_relief", H + Vector((0.3, -2.2, -0.1)), H + Vector((0, 0, -0.2)), lens=35)
key(camA3, "location", F(15.6), H + Vector((0.4, -2.3, -0.15))); key(camA3, "location", F(16.45), H + Vector((0.2, -1.9, -0.05)))

# ============================================================ SET B: throat slide
B = Vector((100, 0, 0))
thr = path_curve("throat_path", [B + Vector(p) for p in [(0, 0, 6), (0.3, 0, 4), (-0.2, 0, 2), (0, 0, 0), (0, 0, -1.5)]])
tube_from(thr, 0.9, FLESH, "throat", bumps=0.25)
seedB = sphere("throat_seed", B, 0.12, SEED, seg=24, scale=(0.6, 0.3, 1))
follow(seedB, thr, F(4.7), F(7.4), 0.14, 0.86)
camB = camera("cam03_throat", B, lens=22)
follow(camB, thr, F(4.7), F(7.4), 0.0, 0.7, cam=True)
lb = light("B_key", "POINT", (0, 0, 0), 12, (1, 0.85, 0.75), size=0.3); lb.parent = camB
light("B_end", "POINT", B + Vector((0, 0, -0.6)), 60, (0.4, 1, 0.2), size=0.5)
sphere("throat_exit_glow", B + Vector((0, 0, -1.6)), 1.3, mat("acid_glow", (0.3, 0.9, 0.1), 0.5, emit=0.9, ecol=(0.35, 1.0, 0.1)))

# ============================================================ SET C: stomach acid
C = Vector((200, 0, 0))
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=5, location=C)
stom = bpy.context.object; stom.name = "stomach"; smooth(stom); stom.data.materials.append(GUT)
d = stom.modifiers.new("folds", "DISPLACE"); tx = bpy.data.textures.new("folds", "STUCCI"); tx.noise_scale = 1.2
d.texture = tx; d.strength = 0.5
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=4.6, fill_type="NGON", location=C + Vector((0, 0, -1.6)))
pool = bpy.context.object; pool.name = "acid_pool"; pool.data.materials.append(ACID)
wv = pool.modifiers.new("sub", "SUBSURF"); wv.levels = 3; wv.subdivision_type = "SIMPLE"
wave = pool.modifiers.new("waves", "WAVE"); wave.height = 0.06; wave.width = 0.6; wave.speed = 0.02
light("C_glow", "AREA", C + Vector((0, 0, -1.0)), 120, (0.5, 1, 0.2), size=6, rot=(math.radians(180), 0, 0))
light("C_top", "POINT", C + Vector((1.5, -2, 2.5)), 250, (1, 0.6, 0.45), size=1)
seedC = sphere("acid_seed", C + Vector((0, 0, 3.5)), 0.14, SEED, seg=24, scale=(0.6, 0.3, 1))
key(seedC, "location", F(7.55), C + Vector((0, 0, 3.5)))
key(seedC, "location", F(7.95), C + Vector((0, 0, -1.5)), "LINEAR")
key(seedC, "location", F(12.9), C + Vector((0.1, 0, -1.6)))
key(seedC, "rotation_euler", F(7.55), (0, 0, 0)); key(seedC, "rotation_euler", F(12.9), (0.4, 2.5, 1.2))
# splash droplets + rising bubbles
for i in range(14):
    a = i / 14 * math.tau; dr = sphere(f"splash{i}", C + Vector((0, 0, -1.55)), 0.05, ACID, seg=12)
    key(dr, "location", F(7.95), C + Vector((0, 0, -1.55)))
    key(dr, "location", F(8.25), C + Vector((0.6 * math.cos(a), 0.6 * math.sin(a), -0.9)))
    key(dr, "location", F(8.6), C + Vector((0.9 * math.cos(a), 0.9 * math.sin(a), -1.7)))
    key(dr, "hide_render", F(7.9), True); key(dr, "hide_render", F(7.95), False); key(dr, "hide_render", F(8.62), True)
for i in range(40):
    p = C + Vector((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), -1.6))
    bb = sphere(f"bubble{i}", p, random.uniform(0.02, 0.07), BUB, seg=12)
    t0 = random.uniform(7.5, 12.5)
    key(bb, "location", F(t0), p); key(bb, "location", F(t0 + 1.4), p + Vector((random.uniform(-.1, .1), random.uniform(-.1, .1), 0.25)))
    key(bb, "hide_render", F(7.0), True); key(bb, "hide_render", F(t0), False); key(bb, "hide_render", F(t0 + 1.45), True)
camC1 = camera("cam04_stomach", C + Vector((1.8, -3.2, 1.2)), C + Vector((0, 0, -1.2)), lens=24)
key(camC1, "location", F(7.55), C + Vector((1.8, -3.2, 1.4))); key(camC1, "location", F(9.75), C + Vector((1.2, -2.6, 0.6)))
camC2 = camera("cam05_fizz", C + Vector((0.6, -0.9, -1.2)), C + Vector((0.05, 0, -1.55)), lens=55)
key(camC2, "location", F(9.75), C + Vector((0.6, -0.95, -1.15))); key(camC2, "location", F(11.8), C + Vector((0.4, -0.7, -1.3)))
camC3 = camera("cam06_cantgrow", C + Vector((0, -1.1, -1.0)), C + Vector((0.1, 0, -1.58)), lens=45)
key(camC3, "location", F(11.8), C + Vector((0, -1.1, -0.9))); key(camC3, "location", F(12.95), C + Vector((0, -1.5, -0.6)))

# ============================================================ SET D: gut ride
D = Vector((300, 0, 0))
gut_pts = [D + Vector((math.sin(i * 0.9) * 2.0, i * 3.0, math.cos(i * 0.7) * 1.5)) for i in range(9)]
gut = path_curve("gut_path", gut_pts)
tube_from(gut, 1.0, GUT, "gut", bumps=0.35, noise=0.4)
seedD = sphere("gut_seed", D, 0.14, SEED, seg=24, scale=(0.6, 0.3, 1))
follow(seedD, gut, F(12.95), F(15.6), 0.05, 0.92)
camD = camera("cam07_gut", D, lens=20)
follow(camD, gut, F(12.95), F(15.6), 0.0, 0.8, cam=True)
sphere("gut_end_glow", gut_pts[-1], 1.3, mat("gut_glow", (0.6, 0.15, 0.1), 0.5, emit=1.5, ecol=(0.8, 0.25, 0.15)))
ld = light("D_key", "POINT", (0, 0, 0), 25, (1, 0.8, 0.7), size=0.3); ld.parent = camD

# ============================================================ SET E: dinner table (scary part + ending)
E = Vector((20, 0, 0))
room(E, mat("wall_dark", (0.25, 0.2, 0.35), 0.8))
guy2 = build_guy(E, "diner")
box("table_top", E + Vector((0, -0.75, 0.95)), (1.6, 0.9, 0.07), TABLE, bevel=0.02)
for sx in (-0.7, 0.7):
    for sy in (-1.1, -0.4):
        box("table_leg", E + Vector((sx, sy, 0.47)), (0.06, 0.06, 0.95), TABLE)
cyl("plate", E + Vector((0, -0.75, 1.0)), 0.28, 0.03, PLATE, verts=48)
for i in range(26):
    a = random.uniform(0, math.tau); r = random.uniform(0, 0.2)
    sphere(f"pea{i}", E + Vector((r * math.cos(a), -0.75 + r * math.sin(a), 1.04)), 0.03, PEA, seg=12)
fork = box("fork", E + Vector((0.35, -0.55, 1.3)), (0.025, 0.025, 0.42), METAL)
fork.rotation_euler = (math.radians(-40), 0, math.radians(15))
forkpea = sphere("fork_pea", fork.location + Vector((-0.06, -0.1, 0.2)), 0.035, PEA, seg=12)
lE = light("E_key", "AREA", E + Vector((-1.8, -2.5, 3)), 700, (1, 0.9, 0.8), size=2.5, rot=(math.radians(45), 0, math.radians(-35)))
keyd(lE.data, "energy", F(16.45), 1100); keyd(lE.data, "energy", F(17.6), 300)
keyd(lE.data, "color", F(16.45), (1, 0.9, 0.8)); keyd(lE.data, "color", F(17.6), (1, 0.35, 0.3))
light("E_rim", "AREA", E + Vector((2, 1.5, 2.6)), 400, (0.5, 0.7, 1), size=2, rot=(math.radians(-50), math.radians(30), 0))
H2 = guy2["head"].location
eyes(guy2, F(16.45), 1.0); mouth_open(guy2, F(16.45), 0.0); brows(guy2, F(16.45), 0.0)
eyes(guy2, F(17.3), 1.3, pupil=0.6); brows(guy2, F(17.3), 1.0)
camE1 = camera("cam09_scary", E + Vector((0, -3.6, 1.8)), H2 + Vector((0, 0, -0.35)), lens=35)
key(camE1, "location", F(16.45), E + Vector((0, -3.6, 1.8))); key(camE1, "location", F(17.85), E + Vector((0, -2.6, 1.85)))
# ending: laughing with peas, then freezes on "don't laugh"
for t in (33.3, 33.6, 33.9, 34.2, 34.5, 34.8):
    up = (t * 10) % 6 < 3
    mouth_open(guy2, F(t), 0.95 if up else 0.55)
    key(guy2["head"], "rotation_euler", F(t), (-0.22 if up else -0.08, 0, 0.05 if up else -0.05))
    eyes(guy2, F(t), squint=True)
brows(guy2, F(33.3), 0.6)
mouth_open(guy2, F(34.96), 0.5); mouth_open(guy2, F(35.15), 0.15)
key(guy2["head"], "rotation_euler", F(34.96), (-0.1, 0, 0)); key(guy2["head"], "rotation_euler", F(35.15), (0.05, 0, 0))
eyes(guy2, F(34.96), squint=True); eyes(guy2, F(35.12), 1.35, pupil=0.45); brows(guy2, F(35.12), 1.0)
camE2 = camera("cam15_laugh", H2 + Vector((0.6, -3.0, -0.3)), H2 + Vector((0, 0, -0.45)), lens=35)
key(camE2, "location", F(33.3), H2 + Vector((0.6, -3.1, -0.3))); key(camE2, "location", F(34.96), H2 + Vector((0.5, -2.8, -0.3)))
key(camE2, "location", F(35.2), H2 + Vector((0.2, -1.8, -0.15)))

# ============================================================ SET F: wrong pipe (windpipe with rings)
Fp = Vector((400, 0, 0))
wp = path_curve("windpipe_path", [Fp + Vector(p) for p in [(0, 0, 7), (0.2, 0, 5), (-0.2, 0, 3), (0.1, 0, 1), (0.6, 0.3, -0.8)]])
tube_from(wp, 0.85, mat("trachea", (0.85, 0.55, 0.55), 0.25, coat=0.6), "windpipe", bumps=0.08, rings=0.18)
peaF = sphere("pipe_pea", Fp, 0.13, PEA, seg=24)
follow(peaF, wp, F(17.85), F(20.5), 0.12, 0.86)
camF = camera("cam10_wrongpipe", Fp, lens=22)
follow(camF, wp, F(17.85), F(20.5), 0.0, 0.7, cam=True)
lf_ = light("F_key", "POINT", (0, 0, 0), 15, (1, 0.9, 0.85), size=0.3); lf_.parent = camF
sphere("lung_glow", Fp + Vector((0.6, 0.3, -0.85)), 1.2, mat("lung_glow", (1, 0.45, 0.5), 0.5, emit=0.6, ecol=(1, 0.5, 0.55)))
alarm = light("F_alarm", "POINT", Fp + Vector((0, 0, 0.5)), 0, (1, 0.1, 0.1), size=1)
for i, t in enumerate((18.9, 19.2, 19.5, 19.8, 20.1)):
    keyd(alarm.data, "energy", F(t), 400 if i % 2 == 0 else 0)

# ============================================================ SET G: lung (warm, wet) + sprouting hero
G = Vector((500, 0, 0))
for i in range(90):  # spongy alveoli on a dome behind and around the pea (camera side left open)
    a = random.uniform(math.radians(10), math.radians(170)); b = random.uniform(-0.3, 1.1); r = random.uniform(1.6, 2.6)
    p = G + Vector((r * math.cos(a) * math.cos(b), r * math.sin(a) * math.cos(b) + 0.3, r * math.sin(b) * 0.9))
    sphere(f"alv{i}", p, random.uniform(0.4, 0.8), LUNG, seg=24)
box("lung_floor", G + Vector((0, 0.5, -0.55)), (4, 4, 0.5), LUNG, bevel=0.2).modifiers.new("sub", "SUBSURF").levels = 2
peaG = sphere("lung_pea", G + Vector((0, 0.3, -0.12)), 0.18, PEA, seg=32)
key(peaG, "location", F(20.55), G + Vector((0, 0.3, 1.6)))
key(peaG, "location", F(21.0), G + Vector((0, 0.3, -0.12)), "LINEAR")
key(peaG, "location", F(21.15), G + Vector((0, 0.3, -0.05))); key(peaG, "location", F(21.3), G + Vector((0, 0.3, -0.12)))
drops = []
for i in range(18):  # wet: droplets beading and dripping
    p = G + Vector((random.uniform(-1.3, 1.3), random.uniform(-0.3, 1.5), random.uniform(0.6, 1.4)))
    dr = sphere(f"drop{i}", p, random.uniform(0.04, 0.09), WATER, seg=16, scale=(1, 1, 1.25))
    t0 = random.uniform(21.2, 24.2)
    key(dr, "location", F(t0), p); key(dr, "location", F(t0 + 0.6), p + Vector((0, 0, -1.0)), "LINEAR")
for i in range(12):  # beads on the pea
    a = random.uniform(0, math.tau); b = random.uniform(-0.2, 1.2)
    sphere(f"bead{i}", peaG.location + Vector((0.19 * math.cos(a) * math.cos(b), 0.19 * math.sin(a) * math.cos(b), 0.19 * math.sin(b))),
           0.025, WATER, seg=10, parent=peaG)
warm = light("G_warm", "AREA", G + Vector((-1, -1.5, 1.4)), 300, (1, 0.6, 0.35), size=1.5, rot=(math.radians(55), 0, math.radians(-30)))
keyd(warm.data, "energy", F(21.2), 150); keyd(warm.data, "energy", F(22.2), 450)
light("G_rim", "POINT", G + Vector((0.8, 1.6, 0.6)), 120, (0.7, 0.8, 1), size=0.6)
camG1 = camera("cam11_lung", G + Vector((0.9, -1.6, 0.7)), G + Vector((0, 0.3, -0.1)), lens=30)
key(camG1, "location", F(20.55), G + Vector((0.9, -1.7, 0.8))); key(camG1, "location", F(24.9), G + Vector((0.5, -1.1, 0.45)))
# hero sprout: pea splits, stem curls up, leaves unfold (30.3 -> 33.3)
half = sphere("pea_shell", peaG.location, 0.185, PEA, seg=32, scale=(1, 1, 0.5))
key(half, "hide_render", F(0), True); key(half, "hide_render", F(30.3), False)
key(half, "location", F(30.4), peaG.location.copy()); key(half, "location", F(31.0), peaG.location + Vector((0.12, 0, 0.1)))
key(half, "rotation_euler", F(30.4), (0, 0, 0)); key(half, "rotation_euler", F(31.0), (0, 0.9, 0))
hs, hl = sprout("hero_sprout", peaG.location + Vector((0, 0, 0.08)),
                [(0, 0, 0), (0.05, 0, 0.18), (-0.08, 0.02, 0.38), (0.06, -0.02, 0.58), (0.0, 0.0, 0.72)],
                STEM, LEAF, F(30.5), F(32.6), thick=0.028, leaf=0.14)
root = bpy.data.curves.new("roots", "CURVE"); root.dimensions = "3D"; root.bevel_depth = 0.012
for k in range(3):
    sp = root.splines.new("BEZIER"); sp.bezier_points.add(2)
    ang = k * 2.1
    for j, p in enumerate(sp.bezier_points):
        p.co = (0.12 * j * math.cos(ang), 0.12 * j * math.sin(ang), -0.07 * j)
        p.handle_left_type = p.handle_right_type = "AUTO"
root.materials.append(STEM); ro = link(bpy.data.objects.new("roots", root)); ro.location = peaG.location
keyd(root, "bevel_factor_end", F(30.6), 0.0); keyd(root, "bevel_factor_end", F(31.8), 1.0)
camG2 = camera("cam14_sprout", peaG.location + Vector((0.35, -0.9, 0.35)), peaG.location + Vector((0, 0, 0.3)), lens=50)
key(camG2, "location", F(30.3), peaG.location + Vector((0.35, -0.9, 0.25))); key(camG2, "location", F(33.3), peaG.location + Vector((0.2, -1.2, 0.55)))
aimG2 = bpy.data.objects[camG2["aim"]]
key(aimG2, "location", F(30.3), peaG.location + Vector((0, 0, 0.1))); key(aimG2, "location", F(33.3), peaG.location + Vector((0, 0, 0.45)))

# ============================================================ SET H: X-ray lightbox (2010, "lung cancer")
Hx = Vector((600, 0, 0))
box("xray_board", Hx + Vector((0, 0.05, 1.6)), (2.0, 0.05, 2.6), XBG)
spine = []
for i in range(14):
    spine.append(box(f"vert{i}", Hx + Vector((0, 0, 0.5 + i * 0.16)), (0.12, 0.02, 0.1), XBONE, bevel=0.02))
for side in (-1, 1):
    sphere(f"xlung{side}", Hx + Vector((0.42 * side, -0.01, 1.75)), 0.4, XLUNG, scale=(0.9, 0.05, 1.5))
    for i in range(7):
        cu = bpy.data.curves.new(f"rib{side}{i}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.022
        sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
        z = 2.45 - i * 0.2
        for p, co in zip(sp.bezier_points, [(0.07 * side, -0.03, z), (0.6 * side, -0.03, z + 0.05), (0.85 * side, -0.03, z - 0.25)]):
            p.co = co; p.handle_left_type = p.handle_right_type = "AUTO"
        cu.materials.append(XBONE); link(bpy.data.objects.new(f"rib{side}{i}", cu)).location = Hx
spot = sphere("xray_spot", Hx + Vector((-0.45, -0.04, 1.55)), 0.11, mat("spot", (0.01, 0.01, 0.01), 0.9), scale=(1, 0.2, 1))
ring = bpy.data.curves.new("alarm_ring", "CURVE"); ring.dimensions = "3D"; ring.bevel_depth = 0.012
sp = ring.splines.new("NURBS"); sp.points.add(15); sp.use_cyclic_u = True
for i, p in enumerate(sp.points):
    a = i / 16 * math.tau; p.co = (0.22 * math.cos(a), 0, 0.22 * math.sin(a), 1)
ring.materials.append(RED); ro = link(bpy.data.objects.new("alarm_ring", ring)); ro.location = spot.location + Vector((0, -0.03, 0))
for i, t in enumerate((26.0, 26.5, 27.0, 27.5, 28.0)):
    key(ro, "scale", F(t), (1.0, 1, 1.0)); key(ro, "scale", F(t + 0.25), (1.25, 1, 1.25))
key(ro, "hide_render", F(24.9), True); key(ro, "hide_render", F(26.0), False)
light("H_front", "AREA", Hx + Vector((0, -2, 1.6)), 30, (0.8, 0.9, 1), size=2, rot=(math.radians(90), 0, 0))
camH = camera("cam12_xray", Hx + Vector((0, -3.4, 1.6)), Hx + Vector((0, 0, 1.6)), lens=40)
key(camH, "location", F(24.9), Hx + Vector((0, -3.6, 1.6))); key(camH, "location", F(28.6), Hx + Vector((-0.35, -1.6, 1.55)))
aimH = bpy.data.objects[camH["aim"]]
key(aimH, "location", F(24.9), Hx + Vector((0, 0, 1.6))); key(aimH, "location", F(28.6), spot.location.copy())

# ============================================================ SET I: doctor's scope (dark bronchus, ring light)
I = Vector((700, 0, 0))
br = path_curve("bronchus_path", [I + Vector(p) for p in [(0, 0, 5), (0.3, 0.2, 3.5), (-0.3, 0, 2), (0.2, -0.1, 0.8), (0, 0, 0)]])
tube_from(br, 0.55, mat("bronchus", (0.75, 0.4, 0.42), 0.25, coat=0.7), "bronchus", bumps=0.06, rings=0.12)
camI = camera("cam13_scope", I, lens=14)
follow(camI, br, F(28.6), F(30.3), 0.0, 0.74, cam=True)
li = light("I_ring", "SPOT", (0, 0, 0), 30, (0.85, 0.95, 1), size=0.1); li.parent = camI; li.data.spot_size = math.radians(100)
crust = sphere("crust_mass", I + Vector((0, 0, 0.1)), 0.35, mat("crust", (0.85, 0.82, 0.7), 0.8), seg=24)
crust.modifiers.new("lumps", "DISPLACE").texture = bpy.data.textures.new("lumps", "CLOUDS")

# ---------------------------------------------------------------- the edit (camera cuts)
EDIT = [(0.0, camA1), (3.05, camA2), (4.7, camB), (7.55, camC1), (9.75, camC2), (11.8, camC3), (12.95, camD),
        (15.6, camA3), (16.45, camE1), (17.85, camF), (20.55, camG1), (24.9, camH), (28.6, camI), (30.3, camG2), (33.3, camE2)]
for t, cam in EDIT:
    cut(t, cam)
S.camera = camA1
# smooth eased motion everywhere except LINEAR keys set on purpose
print("BUILT", len(bpy.data.objects), "objects,", len(EDIT), "shots,", S.frame_end, "frames")
