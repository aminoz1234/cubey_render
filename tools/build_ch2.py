# Deadliest Drinks: all new Blender shots (no people). Cycles, 1 unit = 1 cm, 16:9.
# MODE: 'build' (save packed blend) | 'preview' (stills: ONLY, AT, PCT)
import bpy, bmesh, math, random, os
from mathutils import Vector

ROOT = globals().get('ROOT_OVERRIDE', '/home/claude/cubey_render')
OUT = globals().get('OUT_OVERRIDE', '/home/claude/ch2/bl')
CR = '/home/claude/cubey_render'
TEX = '/home/claude/ch2/tex/'
LABEL = '/home/claude/ch1/tex/label.png'
MODE = globals().get('MODE', 'build')
FPS = 30
SH = [("N1_train", 6.5), ("N2_desk", 5.5), ("N3_lab", 6.5), ("N4_stable", 5.5), ("N5_mausoleum", 6.5),
      ("J1_shelf", 6.0), ("J2_drums", 6.5), ("J3_ward", 5.5),
      ("P1_barrels", 6.5), ("P2_speakeasy", 6.5),
      ("L1_party", 6.5), ("L2_can", 5.5),
      ("F1_fridge", 6.5), ("F2_aisle", 6.5), ("F3_cubes", 5.5)]
T0 = {}; acc = 0.0
for n, d in SH: T0[n] = acc; acc += d
END_T = acc
random.seed(23)
def F(t): return int(round(t * FPS)) + 1
exec(open('/home/claude/rabbl/helpers.py').read())
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
put(sc.render, use_motion_blur=False)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(globals().get('SAMPLES', 24))
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 6
sc.cycles.glossy_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.volume_bounces = 0
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
SP = 20000.0
def span(n): return (T0[n], T0[n] + dict(SH)[n])
def SX(n): return SP * [s[0] for s in SH].index(n)

# ---------------------------------------------------------------- world: 0 night-blue, 1 warm lounge, 2 near-black, 3 cool grey
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
wn = world.node_tree; N = wn.nodes
for n in list(N):
    if n.type != 'OUTPUT_WORLD': N.remove(n)
wout = [n for n in N if n.type == 'OUTPUT_WORLD'][0]
tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, 2.6)
et = N.new('ShaderNodeTexEnvironment'); et.image = bpy.data.images.load(os.path.join(CR, 'assets', 'hdri', 'lythwood_lounge_2k.hdr'), check_existing=True)
tint = N.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs[0].default_value = 1.0; tint.inputs[7].default_value = (1.0, 0.78, 0.55, 1)
bgL = N.new('ShaderNodeBackground'); bgL.inputs['Strength'].default_value = 0.22
wn.links.new(tc.outputs['Generated'], mp.inputs['Vector']); wn.links.new(mp.outputs['Vector'], et.inputs['Vector'])
wn.links.new(et.outputs['Color'], tint.inputs[6]); wn.links.new(tint.outputs[2], bgL.inputs['Color'])
bgs = []
for col in [(0.012, 0.02, 0.045), None, (0.004, 0.004, 0.005), (0.05, 0.055, 0.06)]:
    if col is None: bgs.append(bgL); continue
    b = N.new('ShaderNodeBackground'); b.inputs['Color'].default_value = (*col, 1); bgs.append(b)
# chain of mix shaders selected by key value 0..3
mixes = []
prev = bgs[0].outputs[0]
for i in range(1, 4):
    m = N.new('ShaderNodeMixShader'); wn.links.new(prev, m.inputs[1]); wn.links.new(bgs[i].outputs[0], m.inputs[2]); mixes.append(m); prev = m.outputs[0]
wn.links.new(prev, wout.inputs['Surface'])
def wset(t, k):
    for i, m in enumerate(mixes):
        # mix i selects bgs[i+1] if k >= i+1 else previous chain; to select exactly k, set mixes up to k-1 = 1 and mix k.. =0? use chain semantics
        v = 1.0 if (i + 1) == k else (0.0 if (i + 1) > k else 0.0)
        kval(m.inputs[0], t, v, 'CONSTANT')
    # chain: result = mixes[2](mixes[1](mixes[0](bg0,bg1),bg2),bg3): selecting k means mixes[k-1]=1 and all later = 0
    if k >= 1:
        kval(mixes[k - 1].inputs[0], t, 1.0, 'CONSTANT')

# ---------------------------------------------------------------- materials
def glassy(name, col, rough=0.03, ior=1.5):
    m = simple(name, col, rough=rough); p = m.node_tree.nodes["Principled BSDF"]
    setin(p, 'Transmission Weight', 1.0); setin(p, 'IOR', ior); return m
def imgmat(name, path, rough=0.7, metal=0.0, emit=0.0):
    m, nt, p = node_mat(name)
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tx.outputs['Color'], p.inputs['Base Color']); setin(p, 'Roughness', rough); setin(p, 'Metallic', metal)
    if emit: nt.links.new(tx.outputs['Color'], p.inputs['Emission Color']); setin(p, 'Emission Strength', emit)
    return m
M_AMBER = glassy("Amber", (0.62, 0.24, 0.05), 0.04)
M_AMBER2 = simple("AmberCheap", (0.28, 0.09, 0.018), rough=0.06, coat=1.0)
M_CLEAR = glassy("ClearGlass", (0.95, 0.97, 0.96), 0.01)
M_WATER = glassy("Water", (0.95, 0.97, 1.0), 0.0, 1.33)
M_BROWNLIQ = glassy("Tonic", (0.55, 0.28, 0.08), 0.0, 1.36)
M_CORK = noisy("Cork", (0.42, 0.30, 0.17), (0.62, 0.48, 0.30), scale=60, rough=0.85, bump=0.4)
M_CORK2 = noisy("CorkDim", (0.16, 0.11, 0.07), (0.26, 0.19, 0.12), scale=60, rough=0.9, bump=0.4)
M_LABEL = imgmat("Label", LABEL, 0.8)
M_JAKE = imgmat("JakeLabel", TEX + "jake.png", 0.8)
M_TOCP = imgmat("TOCP", TEX + "tocp.png", 0.55, 0.5)
M_DENAT = imgmat("Denat", TEX + "denat.png", 0.5, 0.4)
M_CRATEL = imgmat("CrateLbl", TEX + "crate.png", 0.85)
M_RX = imgmat("Rx", TEX + "rx.png", 0.9)
M_CAN = imgmat("CanArt", TEX + "can.png", 0.25, 0.6)
M_SODA = [imgmat(f"Soda{c}", TEX + f"soda_{c}.png", 0.6) for c in ("red", "orange", "green", "blue")]
M_MAHOG = noisy("Mahogany", (0.05, 0.016, 0.008), (0.14, 0.05, 0.022), scale=0.25, rough=0.5, coat=0.15, bump=0.05, stripes=(0.2, (0.04, 0.014, 0.007)))
M_FLOOR = noisy("Parquet", (0.07, 0.035, 0.018), (0.16, 0.09, 0.045), scale=0.3, rough=0.5, coat=0.1, bump=0.05, stripes=(0.05, (0.06, 0.03, 0.015)))
M_VELVET = noisy("Velvet", (0.02, 0.06, 0.035), (0.05, 0.12, 0.07), scale=2, rough=0.9, bump=0.2)
M_BRASS = noisy("Brass", (0.55, 0.38, 0.12), (0.75, 0.55, 0.2), scale=4, rough=0.3, metal=1.0, bump=0.05)
M_STEEL = noisy("Steel", (0.10, 0.11, 0.12), (0.2, 0.21, 0.22), scale=3, rough=0.45, metal=0.9, bump=0.1)
M_STONE = noisy("Stone", (0.20, 0.19, 0.18), (0.36, 0.34, 0.32), scale=1.5, rough=0.85, bump=0.6)
M_LEAD = noisy("Lead", (0.26, 0.27, 0.28), (0.40, 0.41, 0.42), scale=2, rough=0.5, metal=1.0, bump=0.2)
M_PLANK = noisy("Planks", (0.16, 0.10, 0.05), (0.30, 0.20, 0.11), scale=0.4, rough=0.85, bump=0.3, stripes=(0.25, (0.12, 0.07, 0.035)))
M_HAY = noisy("Hay", (0.45, 0.35, 0.12), (0.7, 0.58, 0.25), scale=6, rough=0.95, bump=0.8)
M_PLASTER = noisy("Plaster", (0.55, 0.52, 0.46), (0.68, 0.65, 0.58), scale=1.2, rough=0.9, bump=0.15)
M_SHEET = noisy("Sheet", (0.72, 0.71, 0.68), (0.82, 0.81, 0.78), scale=3, rough=0.9, bump=0.1)
M_IRON = noisy("IronBed", (0.12, 0.13, 0.13), (0.2, 0.21, 0.2), scale=3, rough=0.5, metal=0.7, bump=0.05)
M_CONC = noisy("Concrete", (0.12, 0.12, 0.12), (0.22, 0.22, 0.21), scale=0.8, rough=0.8, bump=0.3)
M_TILE = noisy("Tile", (0.55, 0.56, 0.54), (0.7, 0.71, 0.69), scale=0.15, rough=0.25, bump=0.05, stripes=(0.4, (0.4, 0.41, 0.4)))
M_REDCUP = simple("RedCup", (0.55, 0.02, 0.02), rough=0.35, coat=0.5)
M_WHITE = simple("WhitePlastic", (0.85, 0.86, 0.87), rough=0.3)
M_FRIDGEIN = simple("FridgeIn", (0.9, 0.92, 0.93), rough=0.35)
M_SUGAR = noisy("Sugar", (0.86, 0.86, 0.84), (0.97, 0.97, 0.96), scale=40, rough=0.7, bump=0.9)
M_LAMPG = simple("BankerGreen", (0.02, 0.25, 0.08), rough=0.15, coat=1.0)
M_GLOWW = simple("BulbWarm", (1, 0.8, 0.5), emit=(1.0, 0.72, 0.42), es=12.0)
M_GLOWC = simple("TubeCool", (1, 1, 1), emit=(0.85, 0.92, 1.0), es=10.0)
M_PAPER = noisy("Paper", (0.75, 0.72, 0.64), (0.85, 0.82, 0.74), scale=2, rough=0.9, bump=0.05)
M_BOOK = [noisy(f"Book{i}", c, tuple(min(1, x * 1.6) for x in c), scale=3, rough=0.7, bump=0.1) for i, c in enumerate([(0.25, 0.04, 0.03), (0.05, 0.12, 0.06), (0.06, 0.06, 0.15), (0.25, 0.17, 0.06)])]
M_RUBBER = simple("Rubber", (0.03, 0.03, 0.03), rough=0.6)
M_BEER = glassy("Liquor", (0.75, 0.45, 0.15), 0.0, 1.36)

def box(name, c, half, mat, bev=0.8, rot=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    for v in bm.verts: v.co = Vector((v.co.x * half[0], v.co.y * half[1], v.co.z * half[2]))
    o = mesh_obj(name, bm, [mat], smooth_all=False); o.location = c
    if rot: o.rotation_euler = rot
    if bev > 0:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = min(bev, min(half) * 0.45); b.segments = 3
    for p in o.data.polygons: p.use_smooth = True
    return o
def lathe(name, prof, mat, seg=40, parent=None, loc=None):
    bm = bmesh.new(); rows = []
    for (r, z) in prof:
        rows.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), z)) for j in range(seg)])
    for i in range(len(rows) - 1):
        for j in range(seg):
            try: bm.faces.new((rows[i][j], rows[i][(j + 1) % seg], rows[i + 1][(j + 1) % seg], rows[i + 1][j]))
            except Exception: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, [mat], parent=parent)
    if loc: o.location = loc
    return o
def wrap_label(name, r, z0, z1, a0, a1, mat, parent=None, seg=24, flip=False):
    lbm = bmesh.new(); rows = []
    for k in range(2):
        z = z0 + (z1 - z0) * k
        rows.append([lbm.verts.new((r * math.cos(a0 + (a1 - a0) * j / seg), r * math.sin(a0 + (a1 - a0) * j / seg), z)) for j in range(seg + 1)])
    uvl = lbm.loops.layers.uv.new()
    for j in range(seg):
        f = lbm.faces.new((rows[0][j], rows[0][j + 1], rows[1][j + 1], rows[1][j]))
        for lp in f.loops:
            v = lp.vert; jj = j + (1 if v in (rows[0][j + 1], rows[1][j + 1]) else 0); kk = 1 if v in rows[1] else 0
            lp[uvl].uv = ((1 - jj / seg) if flip else jj / seg, kk)
    return mesh_obj(name, lbm, [mat], parent=parent)
def plane(name, w, h, mat, loc, rot=(0, 0, 0), parent=None):
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)]]
    f = bm.faces.new(vs); uvl = bm.loops.layers.uv.new()
    for lp, uv in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): lp[uvl].uv = uv
    o = mesh_obj(name, bm, [mat], parent=parent, smooth_all=False); o.location = loc; o.rotation_euler = rot; return o
BOT_PROF = [(0, 0), (1.95, 0), (2.08, 0.18), (2.1, 3.45), (1.98, 3.9), (1.35, 4.35), (1.08, 4.55), (1.08, 5.15), (1.2, 5.28), (1.2, 5.5), (0.95, 5.5), (0, 5.5)]
def radithor(name, hero=False):
    root = empty(name)
    g = lathe(name + "_g", BOT_PROF, M_AMBER if hero else M_AMBER2, 40 if hero else 20, parent=root)
    if hero: s = g.modifiers.new("sol", 'SOLIDIFY'); s.thickness = 0.12
    lathe(name + "_cork", [(0, 4.9), (0.98, 4.9), (1.02, 6.0), (1.06, 6.35), (0.9, 6.45), (0, 6.45)], M_CORK if hero else M_CORK2, 16, parent=root)
    lo = wrap_label(name + "_l", 2.125, 0.55, 3.35, -1.15, 1.15, M_LABEL, parent=root, seg=24 if hero else 10); lo.rotation_euler.z = -math.pi / 2
    return root
def jake_bottle(name, hero=False):
    # tall flat-shouldered medicine bottle ~ 13 cm
    root = empty(name)
    prof = [(0, 0), (2.3, 0), (2.45, 0.3), (2.45, 9.2), (2.2, 10.0), (1.0, 10.7), (0.85, 11.0), (0.85, 12.2), (0.95, 12.4), (0, 12.4)]
    g = lathe(name + "_g", prof, M_CLEAR if hero else M_AMBER2, 36 if hero else 16, parent=root)
    if hero:
        s = g.modifiers.new("sol", 'SOLIDIFY'); s.thickness = 0.12
        lathe(name + "_liq", [(0, 0.3), (2.25, 0.3), (2.25, 8.5), (0, 8.5)], M_BROWNLIQ, 36, parent=root)
    lathe(name + "_cap", [(0, 11.6), (1.05, 11.6), (1.05, 12.9), (0, 12.9)], M_CORK2, 16, parent=root)
    lo = wrap_label(name + "_l", 2.47, 1.6, 8.6, -1.05, 1.05, M_JAKE, parent=root, seg=20 if hero else 8); lo.rotation_euler.z = -math.pi / 2
    return root
def drum(name, mat_lbl, loc, rz=0):
    root = empty(name, loc); root.rotation_euler.z = rz
    lathe(name + "_b", [(0, 0), (28, 0), (29, 2), (29, 30), (30, 31), (29, 32), (29, 56), (30, 57), (29, 58), (29, 86), (28, 88), (0, 88)], M_STEEL, 40, parent=root)
    wrap_label(name + "_l", 29.15, 36, 54, 0, 2 * math.pi, mat_lbl, parent=root, seg=48)
    return root
def barrel(name, loc, rot=(0, 0, 0)):
    root = empty(name, loc); root.rotation_euler = rot
    prof = [(0, 0), (24, 0)] + [(24 + 6 * math.sin(math.pi * z / 90), z) for z in range(2, 90, 4)] + [(24, 90), (0, 90)]
    lathe(name + "_s", prof, M_PLANK, 32, parent=root)
    for z in (8, 26, 64, 82):
        r = 24 + 6 * math.sin(math.pi * z / 90) + 0.4
        lathe(name + f"_h{z}", [(r, z - 1.5), (r + 0.3, z - 1.5), (r + 0.3, z + 1.5), (r, z + 1.5)], M_IRON, 32, parent=root)
    return root
LIGHTS = []
def L(name, loc, energy, col, radius, n):
    o = plight(name, loc, energy, col, radius); LIGHTS.append((o, span(n))); return o
def area(name, loc, rot, energy, col, size, n):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.color = col; d.size = size
    o = link(bpy.data.objects.new(name, d)); o.location = loc; o.rotation_euler = rot; LIGHTS.append((o, span(n))); return o
def collection_of(builder, name):
    c = bpy.data.collections.new(name); r = builder()
    for o in [r] + list(r.children_recursive):
        for cc in list(o.users_collection): cc.objects.unlink(o)
        c.objects.link(o)
    return c
def inst(name, coll, loc, rot=(0, 0, 0), s=1.0):
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = coll
    e.location = loc; e.rotation_euler = rot; e.scale = (s, s, s) if isinstance(s, (int, float)) else s; link(e); return e
def fogbox(name, c, half, dens, col=(0.8, 0.8, 0.8)):
    fb = bmesh.new(); bmesh.ops.create_cube(fb, size=2.0)
    for v in fb.verts: v.co = Vector((v.co.x * half[0], v.co.y * half[1], v.co.z * half[2]))
    o = mesh_obj(name, fb, [], smooth_all=False); o.location = c
    fm = bpy.data.materials.new(name + "M"); fm.use_nodes = True; fn = fm.node_tree.nodes
    for n in list(fn):
        if n.type != 'OUTPUT_MATERIAL': fn.remove(n)
    vp = fn.new('ShaderNodeVolumePrincipled'); vp.inputs['Density'].default_value = dens; vp.inputs['Color'].default_value = (*col, 1)
    fm.node_tree.links.new(vp.outputs[0], [n for n in fn if n.type == 'OUTPUT_MATERIAL'][0].inputs['Volume']); o.data.materials.append(fm)
    return o
FOGS = []
def cam(n, keys, lens=35, dof=None, fstop=2.8):
    t0, t1 = span(n)
    k = [(t0 + (t1 - t0) * u, loc, tgt) for (u, loc, tgt) in keys]
    camera("C_" + n, t0, k, lens=lens, dof=dof, fstop=fstop, head=0)
WORLD = {}

exec(open('/home/claude/rabbl/ch2_shots.py').read())

# ---------------------------------------------------------------- light spans, world, fog, finish
for o, (a, b) in LIGHTS:
    d = o.data; e = d.energy
    for f, v in ((1, 0.0), (F(a), e), (F(b), 0.0)):
        d.energy = v; d.keyframe_insert('energy', frame=f)
    if a == 0.0: d.energy = e; d.keyframe_insert('energy', frame=1)
    for fc in d.animation_data.action.layers[0].strips[0].channelbag(d.animation_data.action_slot).fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for n, _ in SH: wset(T0[n], WORLD.get(n, 1))
ad = wn.animation_data
for fc in ad.action.layers[0].strips[0].channelbag(ad.action_slot).fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for o, n in FOGS:
    a, b = span(n)
    o.hide_render = True; o.keyframe_insert('hide_render', frame=1)
    o.hide_render = False; o.keyframe_insert('hide_render', frame=F(a))
    o.hide_render = True; o.keyframe_insert('hide_render', frame=F(b))
for c_ in bpy.data.cameras: c_.clip_start = 0.5; c_.clip_end = 1e5
sc.frame_end = F(END_T) - 1
print("SHOTS", {n: (F(T0[n]), F(T0[n] + d) - 1) for n, d in SH}, "END", sc.frame_end)
os.makedirs(OUT, exist_ok=True)
if MODE == 'build':
    sc.camera = CAMS[0][1]; sc.frame_set(1)
    bpy.ops.file.pack_all()
    os.makedirs(os.path.join(ROOT, "scenes", "ch2"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes", "ch2", "ch2.blend"), compress=True)
if MODE == 'preview':
    os.makedirs(os.path.join(OUT, "stills"), exist_ok=True)
    sc.render.resolution_percentage = int(globals().get('PCT', 40))
    only = globals().get('ONLY'); at = globals().get('AT', [0.5])
    names = [s[0] for s in SH]
    for n, d in SH:
        if only and n not in only: continue
        cobj = bpy.data.objects.get("C_" + n)
        if cobj is None: continue
        for u in at:
            f = F(T0[n] + d * u); sc.frame_set(f); sc.camera = cobj
            sc.render.filepath = os.path.join(OUT, "stills", f"{n}_{int(u*100):02d}.jpg"); bpy.ops.render.render(write_still=True); print("STILL", n, u, flush=True)
print("CH2 DONE", MODE)
