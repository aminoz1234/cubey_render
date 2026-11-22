# Deadliest Drinks ch.1 (Radithor) - Blender shots. Cycles, 1 unit = 1 cm, 16:9.
# MODE: 'build' (save packed blend) | 'preview' (stills per shot: ONLY, AT, PCT)
import bpy, bmesh, math, random, os
from mathutils import Vector

ROOT = globals().get('ROOT_OVERRIDE', '/home/claude/cubey_render')
OUT = globals().get('OUT_OVERRIDE', '/home/claude/ch1/bl')
CR = '/home/claude/cubey_render'
LABEL = '/home/claude/ch1/tex/label.png'
MODE = globals().get('MODE', 'build')
FPS = 30
# shot lengths (s) incl. 0.5 s handle
SH = [("S1_cemetery", 9.1), ("S2_hero", 5.0), ("S3_label", 7.5), ("S4_byers", 6.8), ("S5_pile", 6.3), ("S6_warehouse", 6.3)]
T0 = {}; acc = 0.0
for n, d in SH: T0[n] = acc; acc += d
END_T = acc
random.seed(11)
def F(t): return int(round(t * FPS)) + 1
exec(open('/home/claude/rabbl/helpers.py').read())
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
put(sc.render, use_motion_blur=False)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(globals().get('SAMPLES', 32))
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 6
sc.cycles.glossy_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.volume_bounces = 0
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
GREEN = (0.3, 1.0, 0.55)
SP = 20000.0  # set spacing (200 m)

def span(n): return (T0[n], T0[n] + dict(SH)[n])

# ---------------------------------------------------------------- world: 0 night, 1 lounge, 2 warehouse dark
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
wn = world.node_tree; N = wn.nodes
for n in list(N):
    if n.type != 'OUTPUT_WORLD': N.remove(n)
wout = [n for n in N if n.type == 'OUTPUT_WORLD'][0]
tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, 2.6)
et = N.new('ShaderNodeTexEnvironment'); et.image = bpy.data.images.load(os.path.join(CR, 'assets', 'hdri', 'lythwood_lounge_2k.hdr'), check_existing=True)
tint = N.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs[0].default_value = 1.0; tint.inputs[7].default_value = (1.0, 0.78, 0.55, 1)
bgL = N.new('ShaderNodeBackground'); bgL.inputs['Strength'].default_value = 0.28
wn.links.new(tc.outputs['Generated'], mp.inputs['Vector']); wn.links.new(mp.outputs['Vector'], et.inputs['Vector'])
wn.links.new(et.outputs['Color'], tint.inputs[6]); wn.links.new(tint.outputs[2], bgL.inputs['Color'])
bgN = N.new('ShaderNodeBackground'); bgN.inputs['Color'].default_value = (0.012, 0.02, 0.045, 1)
bgD = N.new('ShaderNodeBackground'); bgD.inputs['Color'].default_value = (0.004, 0.004, 0.005, 1)
m1 = N.new('ShaderNodeMixShader'); m2 = N.new('ShaderNodeMixShader')
wn.links.new(bgN.outputs[0], m1.inputs[1]); wn.links.new(bgL.outputs[0], m1.inputs[2])
wn.links.new(m1.outputs[0], m2.inputs[1]); wn.links.new(bgD.outputs[0], m2.inputs[2]); wn.links.new(m2.outputs[0], wout.inputs['Surface'])
def wkey(t, a, b):
    kval(m1.inputs[0], t, float(a), 'CONSTANT'); kval(m2.inputs[0], t, float(b), 'CONSTANT')
wkey(0.0, 0, 0)
for n in ("S2_hero", "S3_label", "S4_byers", "S5_pile"): wkey(T0[n], 1, 0)
wkey(T0["S6_warehouse"], 1, 1)

# ---------------------------------------------------------------- materials
def glassy(name, col, rough=0.03):
    m = simple(name, col, rough=rough); p = m.node_tree.nodes["Principled BSDF"]
    setin(p, 'Transmission Weight', 1.0); setin(p, 'IOR', 1.5); return m
M_AMBER = glassy("Amber", (0.62, 0.24, 0.05), 0.04)
M_AMBER2 = simple("AmberCheap", (0.28, 0.09, 0.018), rough=0.06, coat=1.0)
M_WATER = glassy("Water", (0.95, 0.97, 1.0), 0.0)
M_CORK2 = noisy("CorkDim", (0.16, 0.11, 0.07), (0.26, 0.19, 0.12), scale=60, rough=0.9, bump=0.4)
M_CORK = noisy("Cork", (0.42, 0.30, 0.17), (0.62, 0.48, 0.30), scale=60, rough=0.85, bump=0.4)
def label_mat():
    m, nt, p = node_mat("Label")
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(LABEL)
    nt.links.new(tx.outputs['Color'], p.inputs['Base Color']); setin(p, 'Roughness', 0.8); return m
M_LABEL = label_mat()
M_WOOD = noisy("CoffinWood", (0.07, 0.035, 0.018), (0.17, 0.09, 0.045), scale=0.4, rough=0.4, coat=0.3, bump=0.08, stripes=(0.15, (0.05, 0.025, 0.012)))
M_LEAD = noisy("Lead", (0.26, 0.27, 0.28), (0.40, 0.41, 0.42), scale=2, rough=0.5, metal=1.0, bump=0.2)
M_STONE = noisy("Stone", (0.16, 0.16, 0.17), (0.32, 0.32, 0.33), scale=1.5, rough=0.85, bump=0.6)
M_GRASS = noisy("Grass", (0.025, 0.05, 0.025), (0.07, 0.10, 0.045), scale=0.6, rough=0.95, bump=0.8)
M_DIRT = noisy("Dirt", (0.04, 0.03, 0.02), (0.10, 0.07, 0.045), scale=1.5, rough=1.0, bump=0.8)
M_TABLE = noisy("Mahogany", (0.05, 0.016, 0.008), (0.14, 0.05, 0.022), scale=0.25, rough=0.6, coat=0.0, bump=0.05, stripes=(0.2, (0.04, 0.014, 0.007)))
M_FLOOR = noisy("Parquet", (0.07, 0.035, 0.018), (0.16, 0.09, 0.045), scale=0.3, rough=0.5, coat=0.1, bump=0.05, stripes=(0.05, (0.06, 0.03, 0.015)))
M_CONC = noisy("Concrete", (0.10, 0.10, 0.10), (0.20, 0.20, 0.19), scale=0.8, rough=0.8, bump=0.3)
M_STEEL = noisy("ShelfSteel", (0.10, 0.11, 0.12), (0.18, 0.19, 0.2), scale=3, rough=0.5, metal=0.8, bump=0.1)
M_CRATE = noisy("CrateWood", (0.20, 0.13, 0.07), (0.36, 0.25, 0.14), scale=0.5, rough=0.8, bump=0.2, stripes=(0.3, (0.16, 0.10, 0.05)))
M_LAMP = simple("LampGlow", (1, 0.8, 0.5), emit=(1.0, 0.75, 0.45), es=4.0)

def box(name, c, half, mat, bev=0.8):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    for v in bm.verts: v.co = Vector((v.co.x * half[0], v.co.y * half[1], v.co.z * half[2]))
    o = mesh_obj(name, bm, [mat], smooth_all=False); o.location = c
    if bev > 0:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = min(bev, min(half) * 0.45); b.segments = 3
    for p in o.data.polygons: p.use_smooth = True
    return o

def lathe(name, prof, mat, seg=40, parent=None):
    bm = bmesh.new(); rows = []
    for (r, z) in prof:
        rows.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), z)) for j in range(seg)])
    for i in range(len(rows) - 1):
        for j in range(seg):
            try: bm.faces.new((rows[i][j], rows[i][(j + 1) % seg], rows[i + 1][(j + 1) % seg], rows[i + 1][j]))
            except Exception: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, [mat], parent=parent)

# ---------------------------------------------------------------- the real Radithor bottle: small amber bottle, ~5.5 cm + cork
BOT_PROF = [(0, 0), (1.95, 0), (2.08, 0.18), (2.1, 3.45), (1.98, 3.9), (1.35, 4.35), (1.08, 4.55), (1.08, 5.15), (1.2, 5.28), (1.2, 5.5), (0.95, 5.5), (0, 5.5)]
def make_bottle(name, hero=False, label=True, seg=None):
    root = empty(name)
    g = lathe(name + "_g", BOT_PROF, M_AMBER if hero else M_AMBER2, seg or (48 if hero else 20), parent=root)
    if hero:
        s = g.modifiers.new("sol", 'SOLIDIFY'); s.thickness = 0.12
        wb = bmesh.new(); bmesh.ops.create_cone(wb, cap_ends=True, segments=40, radius1=1.9, radius2=1.9, depth=3.0)
        for v in wb.verts: v.co.z += 1.75
        mesh_obj(name + "_water", wb, [M_WATER], parent=root)
    cork = lathe(name + "_cork", [(0, 4.9), (0.98, 4.9), (1.02, 6.0), (1.06, 6.35), (0.9, 6.45), (0, 6.45)], M_CORK if hero else M_CORK2, 24 if hero else 12, parent=root)
    if label:
        lbm = bmesh.new(); sg = 32 if hero else 10; a0, a1 = -1.15, 1.15; rows = []
        for k in range(2):
            z = 0.55 + 2.8 * k
            rows.append([lbm.verts.new((2.125 * math.cos(a0 + (a1 - a0) * j / sg), 2.125 * math.sin(a0 + (a1 - a0) * j / sg), z)) for j in range(sg + 1)])
        uvl = lbm.loops.layers.uv.new()
        for j in range(sg):
            f = lbm.faces.new((rows[0][j], rows[0][j + 1], rows[1][j + 1], rows[1][j]))
            for lp in f.loops:
                v = lp.vert; jj = j + (1 if v in (rows[0][j + 1], rows[1][j + 1]) else 0); kk = 1 if v in rows[1] else 0
                lp[uvl].uv = (jj / sg, kk)
        lo = mesh_obj(name + "_label", lbm, [M_LABEL], parent=root); lo.rotation_euler.z = -math.pi / 2
    return root

# collection of a cheap bottle for instancing (pile + warehouse)
proto_coll = bpy.data.collections.new("BottleProto")
cheap = make_bottle("Cheap", hero=False)
for o in [cheap] + list(cheap.children):
    for c in o.users_collection: c.objects.unlink(o)
    proto_coll.objects.link(o)
def inst(name, coll, loc, rot=(0, 0, 0), s=1.0):
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = coll
    e.location = loc; e.rotation_euler = rot; e.scale = (s, s, s); link(e); return e

# light helper keyed visible only in a span
LIGHTS = []
def L(name, loc, energy, col, radius, n):
    o = plight(name, loc, energy, col, radius); LIGHTS.append((o, span(n))); return o

# ================================================================ S1 cemetery (x = 0)
CX = 0.0
gb = bmesh.new(); bmesh.ops.create_grid(gb, x_segments=120, y_segments=120, size=900)
for v in gb.verts: v.co.z = 4 * math.sin(v.co.x * 0.01) * math.sin(v.co.y * 0.013) + 2 * math.sin(v.co.x * 0.041 + v.co.y * 0.03)
GROUND = mesh_obj("Ground", gb, [M_GRASS])
add_hair(GROUND, 70000, 6.0, 0, radius=0.12, normal=1.0, rand=0.6, seed=4)
def coffin_shape(name, sc_, h, mat, bev):
    pts = [(-0.55, 1.0), (-1.0, 0.42), (-0.62, -1.0), (0.62, -1.0), (1.0, 0.42), (0.55, 1.0)]
    bm = bmesh.new(); bot = [bm.verts.new((x * sc_[0], y * sc_[1], 0)) for x, y in pts]
    f = bm.faces.new(bot); r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]: v.co.z = h
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, [mat], smooth_all=False)
    b = o.modifiers.new("bev", 'BEVEL'); b.width = bev; b.segments = 3; b.limit_method = 'ANGLE'
    for p_ in o.data.polygons: p_.use_smooth = True
    return o
cof = coffin_shape("Coffin", (34, 98), 44, M_WOOD, 1.5); cof.location = (CX, 0, 10)
lin = coffin_shape("LeadLining", (30, 93), 0.6, M_LEAD, 0.2); lin.location = (CX, 0, 53.2)
lid = coffin_shape("Lid", (36, 101), 4, M_WOOD, 1.2); lid.location = (CX + 60, 0, 2); lid.rotation_euler = (0, math.radians(-62), 0)
for z in (-60, 60): box(f"Plank{z}", (CX, z, 5), (55, 9, 5), M_WOOD, 0.6)
mb = bmesh.new(); blob(mb, (0, 0, 0), (110, 55, 34), 0, 40); mesh_obj("DirtMound", mb, [M_DIRT], loc=(CX - 150, 60, 0))
for i, (x, y, r) in enumerate([(-260, 240, 0.1), (60, 340, -0.15), (250, 270, 0.25), (-390, 130, 0.3), (340, 160, -0.2), (-130, 500, 0), (190, 480, 0.1), (-430, 400, 0.2), (440, 430, -0.1), (-20, 640, 0.05), (520, 620, 0.2), (-560, 620, -0.2)]):
    hh = random.uniform(35, 60); ww = random.uniform(24, 36)
    st = box(f"Stone{i}", (x, y, hh), (ww, 9, hh), M_STONE, 2.5); st.rotation_euler.z = r; st.rotation_euler.x = random.uniform(-0.07, 0.07)
    tb = bmesh.new(); bmesh.ops.create_cone(tb, cap_ends=True, segments=32, radius1=ww, radius2=ww, depth=18)
    top = mesh_obj(f"StoneTop{i}", tb, [M_STONE], loc=(x, y, 2 * hh)); top.rotation_euler = (math.pi / 2 + st.rotation_euler.x, 0, r)
# two lanterns on the ground (the dig crew)
for i, (x, y) in enumerate([(CX + 75, -70), (CX - 85, 120)]):
    lb = bmesh.new(); bmesh.ops.create_cone(lb, cap_ends=True, segments=16, radius1=6, radius2=5, depth=16)
    for v in lb.verts: v.co.z += 8
    mesh_obj(f"Lantern{i}", lb, [M_LAMP], loc=(x, y, 0))
    L(f"LanternL{i}", (x, y, 22), 1.2e5, (1.0, 0.62, 0.3), 6, "S1_cemetery")
moon = bpy.data.lights.new("Moon", 'SUN'); moon.energy = 1.6; moon.color = (0.6, 0.72, 1.0); moon.angle = math.radians(3)
MO = link(bpy.data.objects.new("Moon", moon)); MO.rotation_euler = (math.radians(55), 0, math.radians(-140))
L("CoffinGlow", (CX - 5, -10, 60), 1.6e5, GREEN, 12, "S1_cemetery")
L("GraveRim", (CX - 150, 900, 350), 6e7, (0.45, 0.6, 1.0), 120, "S1_cemetery")
L("CamFill", (CX + 400, -500, 250), 2.0e6, (0.5, 0.6, 1.0), 120, "S1_cemetery")
fb = bmesh.new(); bmesh.ops.create_cube(fb, size=2.0)
for v in fb.verts: v.co = Vector((v.co.x * 800, v.co.y * 800 + 200, v.co.z * 30 + 30))
FOG = mesh_obj("GroundFog", fb, [], smooth_all=False)
fm = bpy.data.materials.new("Fog"); fm.use_nodes = True; fn = fm.node_tree.nodes
for n in list(fn):
    if n.type != 'OUTPUT_MATERIAL': fn.remove(n)
vp = fn.new('ShaderNodeVolumePrincipled'); vp.inputs['Density'].default_value = 0.001; vp.inputs['Color'].default_value = (0.6, 0.7, 0.8, 1)
fm.node_tree.links.new(vp.outputs[0], [n for n in fn if n.type == 'OUTPUT_MATERIAL'][0].inputs['Volume']); FOG.data.materials.append(fm)
t0, t1 = span("S1_cemetery")
camera("C1", t0, [(t0, (CX + 360, -470, 150), (CX - 20, 60, 50)), (t1, (CX + 175, -235, 92), (CX - 10, 20, 48))], lens=38, dof=cof, fstop=5.0, head=0)

# ================================================================ S2 / S3 hero bottle on the table (x = SP)
HX = SP
box("HeroTable", (HX, 0, 70), (90, 60, 3), M_TABLE, 1.2)
HB = make_bottle("HeroBottle", hero=True); HB.location = (HX, 0, 73); HB.rotation_euler.z = math.radians(24)
for i, (dx, dy, rz) in enumerate([(-11, 9, 0.4), (9, 13, -0.3)]):
    b = make_bottle(f"BackBottle{i}", hero=True); b.location = (HX + dx, dy, 73); b.rotation_euler.z = rz
L("HeroKey", (HX + 45, -50, 110), 1800, (1.0, 0.82, 0.62), 10, "S2_hero")
L("HeroRim", (HX - 35, 45, 95), 2200, (1.0, 0.75, 0.5), 5, "S2_hero")
L("HeroKey3", (HX + 45, -50, 110), 1800, (1.0, 0.82, 0.62), 10, "S3_label")
L("HeroRim3", (HX - 35, 45, 95), 2200, (1.0, 0.75, 0.5), 5, "S3_label")
HF = empty("HeroFocus", (HX, -2.1, 75.5))
t0, t1 = span("S2_hero")
camera("C2", t0, [(t0, (HX + 20, -44, 81), (HX + 1, 0, 76.2)), (t1, (HX + 15, -33, 79), (HX + 0.5, 0, 76.0))], lens=60, dof=HF, fstop=2.4, head=0)
t0, t1 = span("S3_label")
camera("C3", t0, [(t0, (HX + 10, -26, 77.2), (HX, 0, 75.4)), (t1, (HX + 4, -15.5, 75.9), (HX, 0, 75.1))], lens=70, dof=HF, fstop=4.0, head=0)

# ================================================================ S4 Byers at the table (x = 2*SP)
MX = 2 * SP
with bpy.data.libraries.load(os.path.join(CR, 'scenes', 'real', 'man.blend'), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
MAN = None
for o in dst.objects:
    if o is None: continue
    link(o)
    if o.type == 'ARMATURE': MAN = o
MAN.scale = (100, 100, 100); MAN.location = (MX, 0, 0)
for mt in bpy.data.materials:
    if ('t-shirt' in mt.name or 'short' in mt.name) and mt.use_nodes:
        for nd in mt.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                for l in list(nd.inputs['Base Color'].links): mt.node_tree.links.remove(l)
                nd.inputs['Base Color'].default_value = (0.035, 0.03, 0.03, 1); setin(nd, 'Roughness', 0.85)
PB = MAN.pose.bones
for b in PB: b.rotation_mode = 'XYZ'
for n, r in {'upperarm01.R': (0, 0, 42), 'lowerarm01.R': (8, 0, 0), 'upperarm01.L': (0, 0, -42), 'lowerarm01.L': (8, 0, 0),
             'head': (26, -4, 0), 'neck01': (6, 0, 0), 'spine01': (4, 0, 0)}.items():
    if n in PB: PB[n].rotation_euler = tuple(math.radians(v) for v in r)
box("Floor4", (MX, 0, -1), (400, 400, 1), M_FLOOR, 0.2)
box("ByersTable", (MX, -62, 104), (45, 22, 2), M_TABLE, 1.0)
for i in range(16):
    b = make_bottle(f"TB{i}", hero=(i < 6));
    b.location = (MX - 30 + (i % 8) * 8.5 + random.uniform(-1.5, 1.5), -52 - (i // 8) * 10 + random.uniform(-1.5, 1.5), 106); b.rotation_euler.z = random.uniform(-0.6, 0.6)
L("FaceGlow4", (MX, -48, 134), 6e4, (0.55, 1.0, 0.75), 10, "S4_byers")
L("LampKey4", (MX + 140, -160, 230), 2.0e5, (1.0, 0.72, 0.45), 40, "S4_byers")
HD = empty("HeadF"); HD.parent = MAN; HD.parent_type = 'BONE'; HD.parent_bone = 'head'; HD.location = (0, 0.06, -0.08)
t0, t1 = span("S4_byers")
camera("C4", t0, [(t0, (MX + 36, -175, 134), (MX + 2, -10, 136)), (t1, (MX + 26, -140, 136), (MX + 2, -10, 140))], lens=34, dof=HD, fstop=2.2, head=0)

# ================================================================ S5 the pile of 1,400 (x = 3*SP)
PX = 3 * SP
box("Floor5", (PX, 0, -1), (400, 400, 1), M_FLOOR, 0.2)
box("Wall5", (PX, 120, 150), (400, 2, 150), noisy("Wallpaper", (0.10, 0.07, 0.05), (0.16, 0.11, 0.07), scale=0.2, rough=0.9, bump=0.05, stripes=(0.4, (0.08, 0.055, 0.04))), 0.5)
box("Wall5b", (PX - 160, 0, 150), (2, 400, 150), M_FLOOR, 0.5)
cnt = 0
while cnt < 1400:
    a = random.uniform(0, 2 * math.pi); r = random.random() ** 0.7 * 55
    x, y = PX + r * math.cos(a), r * math.sin(a) * 0.8
    h = max(0.0, 28 * (1 - r / 55) ** 1.2) * random.uniform(0.55, 1.0)
    inst(f"P{cnt}", proto_coll, (x, y, 2.1 + h), (math.radians(90) + random.uniform(-0.4, 0.4), 0, random.uniform(0, 6.28)))
    cnt += 1
L("PileKey", (PX + 90, -110, 120), 2.5e5, (1.0, 0.75, 0.5), 25, "S5_pile")
L("PileRim", (PX - 30, 70, 25), 1.5e5, (1.0, 0.6, 0.3), 12, "S5_pile")
PF = empty("PF", (PX + 8, -22, 10))
t0, t1 = span("S5_pile")
camera("C5", t0, [(t0, (PX + 52, -72, 20), (PX + 2, 0, 13)), (t1, (PX + 44, -60, 33), (PX, 0, 15))], lens=40, dof=PF, fstop=4.0, head=0)

# ================================================================ S6 warehouse of 400,000 (x = 4*SP)
WX = 4 * SP
box("Floor6", (WX, 0, -1), (900, 2500, 1), M_CONC, 0.2)
# one shelf unit = steel frame, 4 boards, crates of 24 bottles
unit = bpy.data.collections.new("ShelfUnit")
def to_unit(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    unit.objects.link(o); return o
for lvl in range(4):
    z = 12 + lvl * 45
    to_unit(box(f"Board{lvl}", (0, 0, z), (60, 22, 1.2), M_STEEL, 0.3))
    for ci in range(4):
        cx = -45 + ci * 30
        to_unit(box(f"Crate{lvl}_{ci}", (cx, 0, z + 5), (14, 20, 4), M_CRATE, 0.4))
        for bi in range(6):
            for bj in range(4):
                to_unit(inst(f"UB{lvl}_{ci}_{bi}_{bj}", proto_coll, (cx - 11.5 + bi * 4.6, -12 + bj * 8, z + 6.2)))
for px in (-60, 60):
    for py in (-22, 22): to_unit(box(f"Post{px}_{py}", (px, py, 95), (1.5, 1.5, 95), M_STEEL, 0.2))
for row in (-130, -60, 60, 130):
    for k in range(18):
        u = inst(f"Shelf{row}_{k}", unit, (WX + row, -60 + k * 125, 0), (0, 0, math.pi / 2))
for k in range(10):
    lp = bpy.data.lights.new(f"Hang{k}", 'POINT'); lp.energy = 2.4e5; lp.color = (1.0, 0.7, 0.42); lp.shadow_soft_size = 8
    lo = link(bpy.data.objects.new(f"Hang{k}", lp)); lo.location = (WX, -20 + k * 230, 260); LIGHTS.append((lo, span("S6_warehouse")))
    lb = bmesh.new(); bmesh.ops.create_cone(lb, cap_ends=True, segments=16, radius1=18, radius2=4, depth=10)
    mesh_obj(f"Shade{k}", lb, [M_STEEL], loc=(WX, -20 + k * 230, 268))
t0, t1 = span("S6_warehouse")
camera("C6", t0, [(t0, (WX + 8, 120, 120), (WX - 20, 600, 95)), (t1, (WX + 4, -110, 150), (WX - 10, 600, 100))], lens=28, dof=None, head=0)

# ---------------------------------------------------------------- light spans, world, cuts
for o, (a, b) in LIGHTS:
    d = o.data; e = d.energy
    for f, v in ((1, 0.0), (F(a), e), (F(b), 0.0)):
        d.energy = v; d.keyframe_insert('energy', frame=f)
    for fc in d.animation_data.action.layers[0].strips[0].channelbag(d.animation_data.action_slot).fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    if a == 0.0:
        d.energy = e; d.keyframe_insert('energy', frame=1)
moon.energy = 1.6; moon.keyframe_insert('energy', frame=1); moon.energy = 0.0; moon.keyframe_insert('energy', frame=F(T0["S2_hero"]))
for d in [moon]:
    for fc in d.animation_data.action.layers[0].strips[0].channelbag(d.animation_data.action_slot).fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
ad = wn.animation_data
for fc in ad.action.layers[0].strips[0].channelbag(ad.action_slot).fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for c_ in bpy.data.cameras: c_.clip_start = 1.0; c_.clip_end = 1e5
# fog only in the cemetery shot
FOG.hide_render = False; FOG.keyframe_insert('hide_render', frame=1); FOG.hide_render = True; FOG.keyframe_insert('hide_render', frame=F(T0["S2_hero"]))
sc.frame_end = F(END_T) - 1

# mist fog in compositor (cemetery + warehouse depth)
sc.view_layers[0].use_pass_mist = True
world.mist_settings.start = 200; world.mist_settings.depth = 1800; world.mist_settings.falloff = 'QUADRATIC'
try:
    ng = sc.compositing_node_group
    rl = [n for n in ng.nodes if n.type == 'R_LAYERS'][0]; gl = [n for n in ng.nodes if n.type == 'GLARE'][0]
    mx = ng.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mt = ng.nodes.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = 0.35
    ng.links.new(rl.outputs['Mist'], mt.inputs[0]); ng.links.new(mt.outputs[0], mx.inputs[0])
    ng.links.new(rl.outputs['Image'], mx.inputs[6]); mx.inputs[7].default_value = (0.05, 0.05, 0.06, 1)
    ng.links.new(mx.outputs[2], gl.inputs['Image']); print("MIST ON")
except Exception as e: print("mist skipped:", e)

print("SHOTS", {n: (F(T0[n]), F(T0[n] + d) - 1) for n, d in SH}, "END", sc.frame_end)
os.makedirs(OUT, exist_ok=True)
if MODE == 'build':
    sc.camera = CAMS[0][1]; sc.frame_set(1)
    bpy.ops.file.pack_all()
    os.makedirs(os.path.join(ROOT, "scenes", "ch1"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes", "ch1", "ch1.blend"), compress=True)
if MODE == 'preview':
    os.makedirs(os.path.join(OUT, "stills"), exist_ok=True)
    sc.render.resolution_percentage = int(globals().get('PCT', 50))
    only = globals().get('ONLY'); at = globals().get('AT', [0.5])
    for i, (n, d) in enumerate(SH):
        if only and n not in only: continue
        for u in at:
            f = F(T0[n] + d * u); sc.frame_set(f); sc.camera = CAMS[i][1]
            sc.render.filepath = os.path.join(OUT, "stills", f"{n}_{int(u*100):02d}.jpg"); bpy.ops.render.render(write_still=True); print("STILL", n, u, flush=True)
print("CH1 DONE", MODE)
