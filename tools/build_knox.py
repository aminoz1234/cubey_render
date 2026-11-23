"""Knoxville case video: 3D reconstruction shots (landscape 16:9) for the parts the bodycam doesn't show.
Six 4-second shots on one timeline, one set each (spaced along x), cut with markers:
  1 phone alert  2 empty bedroom  3 detectives' desk + warrants  4 the building outside  5 knocking (inside)  6 hallway.
Run: blender -b --factory-startup --python tools/build_knox.py  (CUBEY_ROOT = repo root). Saves scenes/knox/knox.blend."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

ROOT = os.environ.get("CUBEY_ROOT") or os.getcwd()
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
for f_ in ("realism.py", "common_build.py"):
    exec(open(os.path.join(ROOT, "tools", f_)).read())
random.seed(3)
FPS = 30; SHOT = 120
S.render.fps = FPS
cycles_quality(S, samples=32, res=(1280, 720))
S.view_settings.look = "AgX - Medium High Contrast"
SH = ["phone", "bedroom", "desk", "outside", "knock", "hallway"]
RANGE = {k: (1 + i * SHOT, (i + 1) * SHOT) for i, k in enumerate(SH)}
S.frame_start, S.frame_end = 1, len(SH) * SHOT
A = lambda *p: os.path.join(ROOT, "assets", *p)


def import_model(mid, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=A("models", mid, mid + "_1k.gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    root = link(bpy.data.objects.new(mid + "_root", None))
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot_z)); root.scale = (scale,) * 3
    bpy.context.view_layer.update()
    top = max((o.matrix_world @ Vector(c)).z for o in new if o.type == "MESH" for c in o.bound_box)
    return root, top


def tex_mat(name, folder, scale=2.0, tint=(1, 1, 1), bump=0.5, rough_mul=1.0):
    m, _ = img_mat(name, A("tex", folder), tint=tint, scale=scale, bump=bump, rough_mul=rough_mul)
    m.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.0
    return m


def box(name, center, half, m, bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 2 * half[0], v.co.y * 2 * half[1], v.co.z * 2 * half[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    ob = link(bpy.data.objects.new(name, me)); ob.location = center
    if bevel:
        b = ob.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 2
    return ob


def plane(name, center, size, m, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], 0))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        me.uv_layers[0].data[loop.index].uv = (0.5 + co.x / size[0], 0.5 + co.y / size[1])
    me.materials.append(m)
    ob = link(bpy.data.objects.new(name, me)); ob.location = center; ob.rotation_euler = rot
    return ob


def image_mat(name, path, emit=0.0, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.image.pack()
    L.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    if emit:
        L.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m


def shot_world(strength_keys):
    pass


# world: overcast sky; strength keyed per shot (night shots dark)
W = bpy.data.worlds.new("world"); S.world = W; W.use_nodes = True; wn = W.node_tree.nodes; wl = W.node_tree.links
env = wn.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(A("hdri", "kloofendal_overcast_puresky_2k.hdr")); env.image.pack()
wl.new(env.outputs["Color"], wn["Background"].inputs["Color"])
bgs = wn["Background"].inputs["Strength"]
for k, v in (("phone", 0.0), ("bedroom", 0.25), ("desk", 0.0), ("outside", 1.0), ("knock", 0.0), ("hallway", 0.05)):
    bgs.default_value = v; bgs.keyframe_insert("default_value", frame=RANGE[k][0])
set_interp(W.node_tree, "CONSTANT")


def lit(lt, shot, e):
    keys = [(RANGE[shot][0], e), (RANGE[shot][1] + 1, 0.0)]
    if RANGE[shot][0] > 1:
        keys = [(1, 0.0), (RANGE[shot][0] - 1, 0.0)] + keys
    key_energy(lt, keys)
    return lt


m_wall = tex_mat("plaster", "painted_plaster_wall", scale=1.0, tint=(0.82, 0.8, 0.76), bump=0.3)
m_wall_dark = tex_mat("plaster_dark", "painted_plaster_wall", scale=1.0, tint=(0.45, 0.47, 0.5), bump=0.3)
m_carpet = tex_mat("carpet", "cotton_jersey", scale=3.0, tint=(0.33, 0.28, 0.23), bump=1.0)
m_wood = mat("door_wood", (0.6, 0.58, 0.54), rough=0.45, coat=0.15)

# ================================================================ 1. PHONE ALERT (x=0): night, phone buzzing on a nightstand
X = 0.0
ns, ns_top = import_model("painted_wooden_nightstand", Vector((X, 0, 0)), 0)
clock, _ = import_model("alarm_clock_01", Vector((X - 0.12, 0.22, ns_top)), 25, 0.8)
PW, PH = 0.0715, 0.1545
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co = Vector((v.co.x * PW, v.co.y * PH, v.co.z * 0.0078))
bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6], offset=0.009, segments=6, affect="EDGES")
me = bpy.data.meshes.new("phone"); bm.to_mesh(me); bm.free(); me.materials.append(mat("phone_body", (0.02, 0.02, 0.025), rough=0.25, metal=0.6, coat=0.6))
phone = link(bpy.data.objects.new("phone", me)); phone.location = (X + 0.06, -0.02, ns_top + 0.004); phone.rotation_euler = (0, 0, math.radians(-18))
scr = plane("phone_screen", (0, 0, 0.0041), (PW - 0.006, PH - 0.006), image_mat("alert_ui", A("knox", "alert_screen.png"), emit=1.2, rough=0.05))
scr.parent = phone
rnd = random.Random(1)
for f in range(RANGE["phone"][0], RANGE["phone"][1] + 1):
    buzz = (f - RANGE["phone"][0]) % 30 < 12
    phone.location = (X + 0.06 + (rnd.uniform(-0.0015, 0.0015) if buzz else 0), -0.02 + (rnd.uniform(-0.0015, 0.0015) if buzz else 0), ns_top + 0.004)
    phone.keyframe_insert("location", frame=f)
lit(point("phone_glow", Vector((X + 0.06, -0.02, ns_top + 0.08)), 0.6, (0.9, 0.95, 1.0), r=0.04), "phone", 0.6)
lit(area("moon1", Vector((X + 1.2, 0.8, 1.6)), Vector((X, 0, ns_top)), 6, 1.0, (0.45, 0.6, 1.0)), "phone", 6)
box("phone_wall", (X, 0.45, 1.0), (2.0, 0.03, 1.2), m_wall_dark)
box("phone_floor", (X, 0, -0.01), (2.0, 2.0, 0.01), m_carpet)
c1, a1 = camera("K1_phone", Vector((X + 0.35, -0.55, ns_top + 0.35)), Vector((X + 0.06, -0.02, ns_top)), lens=50, fstop=2.0)
key(c1, "location", RANGE["phone"][0], c1.location.copy()); key(c1, "location", RANGE["phone"][1], Vector((X + 0.22, -0.36, ns_top + 0.25)))

# ================================================================ 2. EMPTY BEDROOM (x=20): her room, bed unmade, daylight
X = 20.0
box("bed_base", (X, 0.35, 0.18), (0.8, 1.0, 0.18), mat("bed_base", (0.3, 0.22, 0.16), rough=0.5), bevel=0.02)
box("headboard", (X, 1.38, 0.6), (0.82, 0.04, 0.6), mat("headboard", (0.3, 0.22, 0.16), rough=0.5), bevel=0.02)
box("mattress", (X, 0.35, 0.42), (0.76, 0.97, 0.08), mat("mattress", (0.85, 0.85, 0.82), rough=0.8), bevel=0.04)
m_duv, _ = img_mat("bed_duvet", A("tex", "cotton_jersey"), tint=(0.55, 0.42, 0.55), scale=5, bump=0.7)
duv = box("bed_duvet", (X + 0.05, 0.15, 0.53), (0.82, 0.8, 0.035), m_duv, bevel=0.03)
duv.rotation_euler = (0, 0, math.radians(-6))
_s = duv.modifiers.new("sub", "SUBSURF"); _s.levels = _s.render_levels = 3; _s.subdivision_type = "SIMPLE"
_t = bpy.data.textures.new("duv_w", "CLOUDS"); _t.noise_scale = 0.15; _t.noise_depth = 3
_d = duv.modifiers.new("folds", "DISPLACE"); _d.texture = _t; _d.strength = 0.08; _d.texture_coords = "GLOBAL"
_s2 = duv.modifiers.new("sub2", "SUBSURF"); _s2.levels = _s2.render_levels = 1
pil, _ = img_mat("bed_pillow", A("tex", "cotton_jersey"), tint=(0.9, 0.88, 0.9), scale=6, bump=0.6)
_p = box("bed_pillow", (X - 0.3, 1.15, 0.58), (0.3, 0.17, 0.06), pil, bevel=0.05)
_ps = _p.modifiers.new("sub", "SUBSURF"); _ps.levels = _ps.render_levels = 2
box("br_wall_back", (X, 1.45, 1.3), (2.6, 0.03, 1.4), m_wall)
box("br_wall_side", (X + 1.6, 0, 1.3), (0.03, 2.6, 1.4), m_wall)
box("br_floor", (X, 0, -0.01), (2.6, 2.6, 0.01), m_carpet)
# window in the side wall: bright daylight + sheer curtain
win = plane("br_window", (X + 1.57, 0.2, 1.4), (1.1, 1.2), mat("daylight", (1, 1, 1), emit=3.0), rot=(math.radians(90), 0, math.radians(-90)))
cur_m = bpy.data.materials.new("curtain"); cur_m.use_nodes = True; cb = cur_m.node_tree.nodes["Principled BSDF"]
cb.inputs["Base Color"].default_value = (0.95, 0.95, 0.92, 1); cb.inputs["Transmission Weight"].default_value = 0.6; cb.inputs["Roughness"].default_value = 0.8
cur = plane("br_curtain", (X + 1.5, 0.2, 1.4), (1.3, 1.5), cur_m, rot=(math.radians(90), 0, math.radians(-90)))
cs_ = cur.modifiers.new("sub", "SUBSURF"); cs_.levels = cs_.render_levels = 4; cs_.subdivision_type = "SIMPLE"
wv = cur.modifiers.new("folds", "WAVE"); wv.use_y = False; wv.height = 0.03; wv.width = 0.18; wv.speed = 0.004; wv.narrowness = 1.2
lit(area("br_sun", Vector((X + 2.4, 0.2, 1.6)), Vector((X, 0.4, 0.5)), 120, 1.2, (1.0, 0.95, 0.88)), "bedroom", 120)
# fairy lights along the back wall
for k in range(18):
    s = link(bpy.data.objects.new(f"fairy{k}", bpy.data.meshes.new(f"fairy{k}")))
    bmf = bmesh.new(); bmesh.ops.create_uvsphere(bmf, u_segments=8, v_segments=6, radius=0.012); bmf.to_mesh(s.data); bmf.free()
    s.data.materials.append(mat("fairy", (1.0, 0.7, 0.35), emit=6.0))
    s.location = (X - 1.2 + k * 0.14, 1.41, 1.85 - 0.08 * math.sin(k / 17 * math.pi))
c2, a2 = camera("K2_bedroom", Vector((X - 1.6, -1.6, 1.5)), Vector((X + 0.1, 0.5, 0.6)), lens=28, fstop=4.0)
key(c2, "location", RANGE["bedroom"][0], c2.location.copy()); key(c2, "location", RANGE["bedroom"][1], Vector((X - 1.2, -1.3, 1.4)))

# ================================================================ 3. DETECTIVES' DESK (x=40): night, lamp, the three warrants
X = 40.0
desk, desk_top = import_model("metal_office_desk", Vector((X, 0, 0)), 0)
lamp, _ = import_model("desk_lamp_arm_01", Vector((X - 0.45, 0.2, desk_top)), 140)
binder, _ = import_model("binder_notebook", Vector((X + 0.45, 0.15, desk_top)), 20)
clip, _ = import_model("clipboard", Vector((X + 0.25, -0.1, desk_top)), -15)
for i in range(3):
    w = plane(f"warrant{i+1}", (X - 0.15 + i * 0.07, -0.05 + i * 0.03, desk_top + 0.002 + i * 0.0015), (0.216, 0.28),
              image_mat(f"warrant_m{i+1}", A("knox", f"warrant{i+1}.png"), rough=0.7), rot=(0, 0, math.radians(-8 + i * 7)))
lit(point("desk_lamp", Vector((X - 0.28, 0.05, desk_top + 0.42)), 18, (1.0, 0.78, 0.5), r=0.06), "desk", 18)
lit(area("desk_fill", Vector((X + 1.2, -1.0, 1.6)), Vector((X, 0, desk_top)), 4, 1.0, (0.5, 0.62, 0.9)), "desk", 4)
box("office_floor", (X, 0, -0.01), (3, 3, 0.01), mat("office_floor", (0.15, 0.15, 0.16), rough=0.5))
box("office_wall", (X, 1.2, 1.4), (3, 0.03, 1.5), m_wall_dark)
c3, a3 = camera("K3_desk", Vector((X - 0.05, -0.55, desk_top + 0.55)), Vector((X - 0.05, 0.0, desk_top)), lens=40, fstop=2.8)
key(c3, "location", RANGE["desk"][0], c3.location.copy()); key(c3, "location", RANGE["desk"][1], Vector((X - 0.08, -0.38, desk_top + 0.42)))

# ================================================================ 4. THE BUILDING OUTSIDE (x=80): two-storey brick + siding block, parking lot, overcast
X = 80.0
m_brick = tex_mat("brick", "brick_wall_10", scale=0.35, tint=(0.8, 0.75, 0.72), bump=0.8)
m_asph = tex_mat("asphalt", "asphalt_02", scale=0.15, tint=(0.75, 0.75, 0.78), bump=0.6)
m_conc = tex_mat("concrete", "concrete_floor_02", scale=0.4, bump=0.4)
# siding: horizontal boards
m_sid = bpy.data.materials.new("siding"); m_sid.use_nodes = True; snt = m_sid.node_tree; sb_ = snt.nodes["Principled BSDF"]
tc = snt.nodes.new("ShaderNodeTexCoord"); wvn = snt.nodes.new("ShaderNodeTexWave"); wvn.bands_direction = "Z"; wvn.wave_profile = "SAW"
wvn.inputs["Scale"].default_value = 0.9; snt.links.new(tc.outputs["Object"], wvn.inputs["Vector"])
bpn = snt.nodes.new("ShaderNodeBump"); bpn.inputs["Strength"].default_value = 0.5; snt.links.new(wvn.outputs["Fac"], bpn.inputs["Height"]); snt.links.new(bpn.outputs["Normal"], sb_.inputs["Normal"])
sb_.inputs["Base Color"].default_value = (0.36, 0.42, 0.48, 1); sb_.inputs["Roughness"].default_value = 0.6
BL, BD = 26.0, 9.0
box("bld_lower", (X, 0, 1.5), (BL / 2, BD / 2, 1.5), m_brick)
box("bld_upper", (X, 0, 4.5), (BL / 2, BD / 2, 1.5), m_sid)
box("bld_band", (X, 0, 3.0), (BL / 2 + 0.05, BD / 2 + 0.05, 0.08), mat("trim", (0.85, 0.85, 0.82), rough=0.5))
# pitched roof
bm = bmesh.new()
v = [bm.verts.new(p) for p in ((-BL / 2 - 0.4, -BD / 2 - 0.5, 6.0), (BL / 2 + 0.4, -BD / 2 - 0.5, 6.0), (BL / 2 + 0.4, 0, 8.0), (-BL / 2 - 0.4, 0, 8.0),
                                 (-BL / 2 - 0.4, BD / 2 + 0.5, 6.0), (BL / 2 + 0.4, BD / 2 + 0.5, 6.0))]
bm.faces.new((v[0], v[1], v[2], v[3])); bm.faces.new((v[3], v[2], v[5], v[4])); bm.faces.new((v[0], v[3], v[4])); bm.faces.new((v[1], v[5], v[2]))
me = bpy.data.meshes.new("roof"); bm.to_mesh(me); bm.free(); me.materials.append(mat("shingles", (0.12, 0.11, 0.11), rough=0.85))
roof = link(bpy.data.objects.new("roof", me)); roof.location = (X, 0, 0)
sol = roof.modifiers.new("t", "SOLIDIFY"); sol.thickness = 0.15
# windows + entry doors along the front (-y side)
m_glass = mat("window_glass", (0.05, 0.06, 0.07), rough=0.05, metal=0.3, coat=1.0)
m_frame = mat("window_frame", (0.9, 0.9, 0.88), rough=0.4)
for k in range(8):
    x = X - BL / 2 + 1.6 + k * 3.15
    for z in (1.6, 4.6):
        if k in (3, 4) and z < 3:
            continue
        box(f"winf{k}_{z}", (x, -BD / 2 - 0.02, z), (0.62, 0.04, 0.68), m_frame)
        box(f"win{k}_{z}", (x, -BD / 2 - 0.05, z), (0.55, 0.03, 0.6), m_glass)
        for sd in (-1, 1):
            box(f"shut{k}_{z}_{sd}", (x + sd * 0.82, -BD / 2 - 0.04, z), (0.16, 0.03, 0.68), mat("shutter", (0.08, 0.1, 0.12), rough=0.5))
# central stairwell entrance: open doorway, a glimpse of the white-railed stairs inside
box("entry_frame", (X, -BD / 2 - 0.03, 1.25), (1.0, 0.05, 1.3), m_frame)
box("entry_dark", (X, -BD / 2 - 0.06, 1.15), (0.85, 0.03, 1.15), mat("entry_dark", (0.03, 0.03, 0.035), rough=0.9))
box("canopy", (X, -BD / 2 - 0.7, 2.7), (1.4, 0.75, 0.06), mat("canopy", (0.2, 0.2, 0.22), rough=0.6))
box("lot", (X, -14, -0.02), (30, 12, 0.02), m_asph)
box("sidewalk", (X, -BD / 2 - 1.2, 0.05), (BL / 2 + 1, 1.2, 0.07), m_conc)
m_shrub = tissue("shrub", base=(0.12, 0.22, 0.06), crease=(0.03, 0.06, 0.02), sss=0.2, wet=0.0, bump=0.8, scale=6, veins=0.0)
for k in range(14):
    x = X - BL / 2 + 1 + k * 1.85
    if abs(x - X) < 1.3:
        continue
    sh = link(bpy.data.objects.new(f"shrub{k}", bpy.data.meshes.new(f"shrub{k}")))
    bmh = bmesh.new(); bmesh.ops.create_icosphere(bmh, subdivisions=3, radius=1.0); bmh.to_mesh(sh.data); bmh.free()
    sh.data.materials.append(m_shrub)
    sh.location = (x, -BD / 2 - 0.55, 0.35); r = random.uniform(0.45, 0.65); sh.scale = (r, r * 0.8, r * 0.75)
    _tx = bpy.data.textures.new(f"shr{k}", "CLOUDS"); _tx.noise_scale = 0.25
    _dm = sh.modifiers.new("lumps", "DISPLACE"); _dm.texture = _tx; _dm.strength = 0.3
for k in range(9):          # parking lines
    box(f"pline{k}", (X - 12 + k * 3, -9.5, 0.002), (0.06, 2.4, 0.004), mat("paint", (0.9, 0.9, 0.85), rough=0.6))
lit(area("out_sun", Vector((X + 15, -20, 25)), Vector((X, 0, 0)), 1500, 15, (1.0, 0.97, 0.92)), "outside", 1500)
c4, a4 = camera("K4_outside", Vector((X - 12, -20, 1.4)), Vector((X - 1, 0, 3.4)), lens=30, fstop=8)
key(c4, "location", RANGE["outside"][0], c4.location.copy()); key(c4, "location", RANGE["outside"][1], Vector((X - 9, -16.5, 1.4)))

# ================================================================ 5. KNOCKING, FROM INSIDE (x=120): dark entry, door jolts, boots' shadows under the door
X = 120.0
box("ent_wall_l", (X - 1.08, 0.0, 1.3), (0.62, 0.06, 1.4), m_wall_dark)
box("ent_wall_r", (X + 1.08, 0.0, 1.3), (0.62, 0.06, 1.4), m_wall_dark)
box("ent_header", (X, 0.0, 2.4), (0.47, 0.06, 0.3), m_wall_dark)
box("ent_trim", (X, -0.065, 2.12), (0.5, 0.01, 0.04), mat("trim_w", (0.8, 0.8, 0.78), rough=0.4))
box("ent_side", (X - 1.1, -1.4, 1.3), (0.03, 1.4, 1.4), m_wall_dark)
box("ent_floor", (X, -1.4, -0.01), (2, 1.6, 0.01), m_carpet)
hinge = link(bpy.data.objects.new("door_hinge", None)); hinge.location = (X - 0.45, 0.0, 0)
door = box("door", (0.45, 0, 1.055), (0.45, 0.022, 1.03), m_wood, bevel=0.004); door.parent = hinge
for k, z in enumerate((0.45, 1.05, 1.55)):         # panel insets
    p = box(f"panel{k}", (0.45, -0.024, z + 0.12), (0.34, 0.004, 0.22 if k < 2 else 0.12), mat("panel", (0.55, 0.53, 0.5), rough=0.5), bevel=0.003)
    p.parent = hinge
knob = link(bpy.data.objects.new("knob", bpy.data.meshes.new("knob")))
bmk = bmesh.new(); bmesh.ops.create_uvsphere(bmk, u_segments=16, v_segments=8, radius=0.03); bmk.to_mesh(knob.data); bmk.free()
knob.data.materials.append(mat("brass", (0.75, 0.6, 0.35), rough=0.25, metal=1.0)); knob.parent = hinge; knob.location = (0.82, -0.05, 1.0)
# light leaking under the door, with boots moving through it
gap = plane("door_gap_light", (X, 0.12, 0.004), (0.9, 0.18), mat("hall_light", (1, 0.97, 0.9), emit=25.0))
for k in range(3):
    b = box(f"boot{k}", (X - 0.25 + k * 0.28, 0.2, 0.06), (0.06, 0.13, 0.06), mat("boot", (0.01, 0.01, 0.01), rough=0.7))
    for f, dx in ((RANGE["knock"][0], 0.0), (RANGE["knock"][0] + 40, 0.05 * (k - 1)), (RANGE["knock"][1], 0.02)):
        b.location.x = X - 0.25 + k * 0.28 + dx; b.keyframe_insert("location", frame=f)
spill = lit(area("gap_spill", Vector((X, 0.15, 0.05)), Vector((X, -1.0, 0.0)), 25, 0.9, (1.0, 0.95, 0.85), "RECTANGLE"), "knock", 25)
lit(area("ent_amb", Vector((X + 1.0, -2.5, 2.2)), Vector((X, 0, 1.0)), 6, 1.5, (0.5, 0.6, 0.85)), "knock", 6)
lit(point("peephole", Vector((X, -0.2, 1.55)), 0.05, (1, 0.95, 0.85), r=0.01), "knock", 0.05)
# the knocks: door jolts in its frame
f0 = RANGE["knock"][0] + 12
for i in range(9):
    f = f0 + i * 11 + (6 if i % 3 == 2 else 0)
    if f > RANGE["knock"][1] - 3:
        break
    hinge.rotation_euler = (0, 0, 0); hinge.keyframe_insert("rotation_euler", frame=f - 1)
    hinge.rotation_euler = (0, 0, math.radians(-0.35)); hinge.keyframe_insert("rotation_euler", frame=f)
    hinge.rotation_euler = (0, 0, 0); hinge.keyframe_insert("rotation_euler", frame=f + 3)
c5, a5 = camera("K5_knock", Vector((X + 0.5, -2.2, 0.55)), Vector((X - 0.05, 0.0, 0.85)), lens=35, fstop=2.8)
key(c5, "location", RANGE["knock"][0], c5.location.copy()); key(c5, "location", RANGE["knock"][1], Vector((X + 0.35, -1.7, 0.6)))

# ================================================================ 6. HALLWAY (x=150): dim, narrow, the bedroom door ajar at the end
X = 150.0
HL = 6.0
box("hw_left", (X - 0.55, HL / 2, 1.25), (0.03, HL / 2, 1.25), m_wall)
box("hw_right", (X + 0.55, HL / 2, 1.25), (0.03, HL / 2, 1.25), m_wall)
box("hw_ceil", (X, HL / 2, 2.5), (0.6, HL / 2, 0.02), m_wall)
box("hw_floor", (X, HL / 2, -0.01), (0.6, HL / 2, 0.01), m_carpet)
box("hw_end", (X, HL + 0.02, 1.25), (0.6, 0.03, 1.25), m_wall)
for k, (side, y) in enumerate(((-1, 1.6), (1, 2.8), (-1, 4.0))):
    box(f"hw_door{k}", (X + side * 0.53, y, 1.0), (0.02, 0.43, 1.0), m_wood, bevel=0.004)
# bedroom door at the end, ajar, warm light spilling out
eh = link(bpy.data.objects.new("end_hinge", None)); eh.location = (X - 0.42, HL - 0.03, 0)
ed = box("end_door", (0.42, 0, 1.0), (0.42, 0.02, 1.0), m_wood, bevel=0.004); ed.parent = eh
eh.rotation_euler = (0, 0, math.radians(22))
lit(point("bedroom_light", Vector((X + 0.3, HL + 1.0, 1.4)), 150, (1.0, 0.8, 0.6), r=0.2), "hallway", 150)
box("br2_back", (X, HL + 2.6, 1.25), (1.5, 0.03, 1.3), m_wall)
box("br2_floor", (X, HL + 1.4, -0.01), (1.5, 1.3, 0.01), m_carpet)
lit(point("hw_dim", Vector((X, 1.0, 2.3)), 45, (0.7, 0.78, 0.95), r=0.3), "hallway", 45)
c6, a6 = camera("K6_hallway", Vector((X + 0.05, -0.3, 1.55)), Vector((X, HL, 1.15)), lens=24, fstop=4.0)
key(c6, "location", RANGE["hallway"][0], c6.location.copy()); key(c6, "location", RANGE["hallway"][1], Vector((X + 0.03, 3.2, 1.5)))

# ---------------------------------------------------------------- cuts
for k, cam in zip(SH, (c1, c2, c3, c4, c5, c6)):
    mk = S.timeline_markers.new(cam.name, frame=RANGE[k][0]); mk.camera = cam
    set_interp(cam, "LINEAR")
S.camera = c1
out = os.path.join(ROOT, "scenes", "knox", "knox.blend")
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("KNOX READY", out, S.frame_end, RANGE)
