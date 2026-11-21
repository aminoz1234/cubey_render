# Cubey - "What happens if you get rabies?"  (Blender 5.2, EEVEE, botfly look)
# Units: 1 Blender unit = 1 cm. Shot times follow Jamal's voiceover (37.4 s).
# MODE: 'build' | 'preview' (ONLY=[...], AT=[...], PCT=..)
import bpy, bmesh, math, random, os, sys
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '/home/claude/rabbl'
MODE = globals().get('MODE', 'build')
PCT = int(globals().get('PCT', 100))
ROOT = globals().get('ROOT_OVERRIDE', '/home/claude/rabbl/out')
OUT = os.path.join(ROOT, "renders", "rabies")
CR = '/home/claude/cubey_render'
FPS = 30
END_T = 37.40
random.seed(11)
def F(t): return int(round(t * FPS)) + 1

T = dict(S01=0.0, S02=3.30, S03=5.20, S04=8.45, S05=10.07, S05b=12.12, S06=14.58, S07=16.55, S08=20.08,
         S09=23.19, S10=25.23, S11=29.58, S11b=31.50, S12=33.87)

exec(open(os.path.join('/home/claude/rabbl', 'helpers.py')).read())
put(sc.render, use_motion_blur=False)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(globals().get('SAMPLES', 16))
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 4; sc.cycles.transparent_max_bounces = 16
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass

# ---------------------------------------------------------------- world: 0 bedroom night, 1 hospital, 2 micro (dark red), 3 bedroom warm
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
wn = world.node_tree; N = wn.nodes
for n in list(N):
    if n.type != 'OUTPUT_WORLD': N.remove(n)
wout = [n for n in N if n.type == 'OUTPUT_WORLD'][0]
def env(img, rot_z, strength, tint=(1, 1, 1)):
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, rot_z)
    et = N.new('ShaderNodeTexEnvironment')
    et.image = bpy.data.images.load(os.path.join(CR, 'assets', 'hdri', img), check_existing=True)
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    mx.inputs[7].default_value = (*tint, 1)
    bg = N.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = strength
    wn.links.new(tc.outputs['Generated'], mp.inputs['Vector']); wn.links.new(mp.outputs['Vector'], et.inputs['Vector'])
    wn.links.new(et.outputs['Color'], mx.inputs[6]); wn.links.new(mx.outputs[2], bg.inputs['Color']); return bg
bg_night = env("hotel_room_2k.hdr", 0.0, 0.55, (0.55, 0.65, 1.0))
bg_hosp = env("hospital_room_2k.hdr", 0.0, 0.9)
bg_micro = N.new('ShaderNodeBackground'); bg_micro.inputs['Color'].default_value = (0.20, 0.02, 0.03, 1); bg_micro.inputs['Strength'].default_value = 0.6
bg_warm = env("hotel_room_2k.hdr", 1.2, 0.8, (1.0, 0.85, 0.7))
mxa = N.new('ShaderNodeMixShader'); mxb = N.new('ShaderNodeMixShader'); mxc = N.new('ShaderNodeMixShader')
wn.links.new(bg_night.outputs[0], mxa.inputs[1]); wn.links.new(bg_hosp.outputs[0], mxa.inputs[2])
wn.links.new(mxa.outputs[0], mxb.inputs[1]); wn.links.new(bg_micro.outputs[0], mxb.inputs[2])
wn.links.new(mxb.outputs[0], mxc.inputs[1]); wn.links.new(bg_warm.outputs[0], mxc.inputs[2])
wn.links.new(mxc.outputs[0], wout.inputs['Surface'])
def world_set(t, k):
    kval(mxa.inputs[0], t, 1.0 if k == 1 else 0.0, 'CONSTANT'); kval(mxb.inputs[0], t, 1.0 if k == 2 else 0.0, 'CONSTANT')
    kval(mxc.inputs[0], t, 1.0 if k == 3 else 0.0, 'CONSTANT')

sun_d = bpy.data.lights.new("Moon", 'SUN'); sun_d.energy = 1.4; sun_d.color = (0.62, 0.72, 1.0); sun_d.angle = math.radians(4)
SUN = link(bpy.data.objects.new("Moon", sun_d)); SUN.rotation_euler = (math.radians(50), math.radians(-15), math.radians(-30))
def sun_key(t, e, col):
    set_interp('CONSTANT'); sun_d.energy = e; sun_d.keyframe_insert('energy', frame=F(t)); sun_d.color = col; sun_d.keyframe_insert('color', frame=F(t))

_simple0 = simple
def simple(name, base, rough=0.4, emit=None, es=0.0, sss=0.0, coat=0.0, metal=0.0, alpha=1.0):
    m = _simple0(name, base, rough, emit, es, sss, coat, metal, alpha)
    if emit or alpha < 1: return m
    nt = m.node_tree; Nn = nt.nodes; p = Nn["Principled BSDF"]
    tc = Nn.new('ShaderNodeTexCoord'); nz = Nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = Nn.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = max(0.0, rough - 0.12); mr.inputs['To Max'].default_value = min(1.0, rough + 0.12)
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], p.inputs['Roughness'])
    hv = Nn.new('ShaderNodeHueSaturation'); hv.inputs['Color'].default_value = (*base, 1)
    vm = Nn.new('ShaderNodeMapRange'); vm.inputs['To Min'].default_value = 0.93; vm.inputs['To Max'].default_value = 1.07
    nt.links.new(nz.outputs['Fac'], vm.inputs['Value']); nt.links.new(vm.outputs['Result'], hv.inputs['Value'])
    nt.links.new(hv.outputs['Color'], p.inputs['Base Color'])
    return m

# ================================================================ materials
M_BATFUR = noisy("BatFur", (0.16, 0.10, 0.06), (0.36, 0.24, 0.14), scale=8, rough=0.6, bump=0.2)
M_BATHAIR = simple("BatHair", (0.34, 0.22, 0.13), rough=0.55)
M_BATSKIN = noisy("BatSkin", (0.08, 0.05, 0.05), (0.20, 0.12, 0.11), scale=5, rough=0.35, coat=0.3, sss=0.3, bump=0.15)
def membrane():
    m, nt, p = node_mat("BatWing"); Nn = nt.nodes; L = nt.links
    tc = Nn.new('ShaderNodeTexCoord'); vo = Nn.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 3.5
    L.new(tc.outputs['Object'], vo.inputs['Vector'])
    r = Nn.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (0.04, 0.015, 0.015, 1); r.color_ramp.elements[1].color = (0.11, 0.05, 0.045, 1)
    r.color_ramp.elements[1].position = 0.04
    L.new(vo.outputs['Distance'], r.inputs['Fac']); L.new(r.outputs['Color'], p.inputs['Base Color'])
    setin(p, 'Roughness', 0.4); setin(p, 'Subsurface Weight', 0.6); setin(p, 'Subsurface Radius', (1, 0.3, 0.2)); setin(p, 'Subsurface Scale', 0.3)
    setin(p, 'Coat Weight', 0.2); put(m, use_backface_culling=False)
    return m
M_BATWING = membrane()
M_TOOTH = simple("Tooth", (0.95, 0.93, 0.88), rough=0.2, coat=0.6)
M_GLINT = simple("BatEye", (0.01, 0.01, 0.012), rough=0.02, coat=1.0, emit=(1.0, 0.15, 0.1), es=0.6)
M_BLOOD = simple("Blood", (0.28, 0.0, 0.01), rough=0.05, coat=1.0, sss=0.3)
M_NERVE = noisy("Nerve", (0.85, 0.72, 0.45), (0.98, 0.90, 0.68), scale=3, rough=0.25, coat=1.0, sss=0.7, bump=0.2)
M_NERVEGLOW = simple("NerveGlow", (1.0, 0.85, 0.5), rough=0.3, emit=(1.0, 0.75, 0.35), es=0.0)
M_VIRUS = noisy("Virus", (0.55, 0.06, 0.08), (0.90, 0.25, 0.20), scale=14, rough=0.3, coat=0.8, sss=0.3, bump=0.5)
M_SPIKE = simple("VirusSpike", (0.95, 0.55, 0.35), rough=0.35, emit=(1.0, 0.3, 0.15), es=0.6)
M_BRAIN = noisy("Brain", (0.80, 0.45, 0.45), (0.95, 0.68, 0.66), scale=2, rough=0.25, coat=1.0, sss=0.7, bump=0.5)
M_ANTI = simple("Antibody", (0.35, 0.95, 0.55), rough=0.3, emit=(0.3, 1.0, 0.5), es=1.2)
M_THROAT = noisy("Throat", (0.55, 0.08, 0.09), (0.88, 0.30, 0.28), scale=3, rough=0.2, coat=1.0, sss=0.6, bump=0.4)
M_THROATCUT = noisy("ThroatCut", (0.95, 0.55, 0.50), (1.0, 0.72, 0.66), scale=6, rough=0.4, sss=0.5, bump=0.2)
def glassy(name, col, rough=0.01, ior=1.45):
    m = simple(name, col, rough=rough); p = m.node_tree.nodes["Principled BSDF"]
    setin(p, 'Transmission Weight', 1.0); setin(p, 'IOR', ior); return m
M_WATER = glassy("Water", (0.80, 0.92, 1.0), 0.0, 1.33)
M_GLASS = glassy("Glass", (0.95, 0.98, 1.0), 0.01, 1.5)
M_WOODN = noisy("Nightstand", (0.20, 0.11, 0.06), (0.36, 0.21, 0.11), scale=0.15, rough=0.35, coat=0.3, bump=0.05)
M_SWEAT = glassy("Sweat", (0.95, 0.97, 1.0), 0.0, 1.33)
M_METAL = simple("Steel", (0.8, 0.8, 0.82), rough=0.15, metal=1.0)
M_PLASTIC = simple("Plastic", (0.92, 0.94, 0.95), rough=0.25, alpha=0.6)
M_VACC = simple("Vaccine", (0.6, 1.0, 0.7), rough=0.05, emit=(0.3, 1.0, 0.5), es=0.8, alpha=0.8)
M_SCREEN = simple("Screen", (0.01, 0.02, 0.02), rough=0.1)
M_ECG_G = simple("EcgGreen", (0.2, 1.0, 0.4), emit=(0.2, 1.0, 0.4), es=6)
M_ECG_R = simple("EcgRed", (1.0, 0.1, 0.1), emit=(1.0, 0.1, 0.1), es=6)
M_HOSPBED = simple("HospSheet", (0.78, 0.85, 0.90), rough=0.7)
M_SPARK = simple("Spark", (1.0, 0.8, 0.3), emit=(1.0, 0.75, 0.3), es=8)
M_LAMP = simple("LampShade", (1.0, 0.85, 0.6), rough=0.6, emit=(1.0, 0.7, 0.4), es=3)

# ================================================================ SET A: the forearm on a bed (x -30..30)
R_ARM = 4.5
def zs(x, y):
    y = max(-R_ARM + 1e-4, min(R_ARM - 1e-4, y)); return math.sqrt(R_ARM * R_ARM - y * y) - R_ARM
BITE = (1.2, 0.6)
M_ARMSKIN = skin_mat("ArmSkin", red=((BITE[0], BITE[1], 0.0), 0.0001))
def make_arm():
    bm = bmesh.new(); nx, na = 200, 140; rows = []
    for i in range(nx + 1):
        x = -22 + 44 * i / nx; row = []
        for j in range(na):
            a = 2 * math.pi * j / na
            row.append(bm.verts.new((x, R_ARM * math.sin(a), R_ARM * math.cos(a) - R_ARM)))
        rows.append(row)
    for i in range(nx):
        for j in range(na):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][(j + 1) % na], rows[i][(j + 1) % na]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj("Arm", bm, [M_ARMSKIN, M_ARMHAIR])
    add_hair(o, 5000, 0.65, 1, radius=0.0022, normal=0.3, align=(1.0, 0.0, 0.0), rand=0.5, seed=3)
    return o
ARM = make_arm()
def make_sheet(name, x0=0.0, mat=None):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=100, y_segments=100, size=40)
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        v.co.z = -2 * R_ARM + 0.6 * math.sin(x * 0.35 + y * 0.12) + 0.4 * math.sin(y * 0.5 - x * 0.1) - 0.25
    o = mesh_obj(name, bm, [mat or M_SHEET]); o.location.x = x0; return o
make_sheet("Sheet")

# the redness around the bite: animate the ramp radius of the arm skin's red patch
red_node = [n for n in M_ARMSKIN.node_tree.nodes if n.type == 'MAP_RANGE'][0]
def red_r(t, r): kval(red_node.inputs['From Max'], t, r)
red_r(0.0, 0.0001); red_r(T['S07'], 0.0001); red_r(T['S07'] + 1.2, 1.1); red_r(T['S08'], 1.3)

# puncture marks (two fang holes) + a blood bead
def disc(name, r, loc, mat):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=12, y_segments=12, size=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.length > r * 1.001], context='VERTS')
    for v in bm.verts: v.co.z = zs(loc[0] + v.co.x, loc[1] + v.co.y) - zs(loc[0], loc[1])
    o = mesh_obj(name, bm, [mat]); o.location = loc; return o
M_HOLE = simple("Hole", (0.08, 0.0, 0.005), rough=0.15, coat=1.0)
HOLES = []
for k, dy in enumerate((-0.18, 0.18)):
    hx, hy = BITE[0], BITE[1] + dy
    HOLES.append(disc(f"Fang{k}", 0.045, (hx, hy, zs(hx, hy) + 0.003), M_HOLE))
bb = bmesh.new(); blob(bb, (0, 0, 0), (0.09, 0.09, 0.06), 0, 20)
BEAD = mesh_obj("BloodBead", bb, [M_BLOOD], loc=(BITE[0], BITE[1] + 0.18, zs(BITE[0], BITE[1] + 0.18) + 0.03))
for o in HOLES: vis(o, (6.6, T['S05']), (T['S07'], T['S08']), (T['S11'], T['S11b']))
kf(BEAD, 6.6, scl=0.0); kf(BEAD, 7.4, scl=1.0)
vis(BEAD, (6.6, T['S05']), (T['S07'], T['S08']))

# ---------------------------------------------------------------- the bat (front = +X, origin at belly)
def make_bat(name, s=1.0):
    root = empty(name)
    bm = bmesh.new()
    blob(bm, (0, 0, 0.0), (1.6, 1.05, 1.0), 0)                       # body
    blob(bm, (1.75, 0, 0.35), (0.85, 0.8, 0.75), 0)                  # head
    blob(bm, (2.45, 0, 0.18), (0.42, 0.33, 0.30), 2)                 # snout
    blob(bm, (2.82, 0, 0.22), (0.12, 0.16, 0.10), 2, 14)             # nose
    for sy in (1, -1):
        blob(bm, (2.15, sy * 0.42, 0.62), (0.16, 0.14, 0.16), 3, 18)  # eyes
        # ears: tall thin cones
        stick(bm, (1.55, sy * 0.45, 0.85), (1.35, sy * 0.85, 2.05), 0.42, 0.06, 2, 14)
    o = mesh_obj(name + "_body", bm, [M_BATFUR, M_BATHAIR, M_BATSKIN, M_GLINT], parent=root)
    add_hair(o, 9000, 0.13, 1, radius=0.004, normal=0.5, rand=0.5, seed=7)
    # jaw with fangs (separate so it can open)
    jb = bmesh.new()
    blob(jb, (0.35, 0, -0.08), (0.38, 0.28, 0.14), 0, 16)
    for sy in (1, -1):
        stick(jb, (0.62, sy * 0.13, 0.05), (0.64, sy * 0.12, 0.42), 0.055, 0.008, 1, 8)   # lower fangs up
    jaw = mesh_obj(name + "_jaw", jb, [M_BATSKIN, M_TOOTH], parent=root, loc=(2.25, 0, -0.05))
    ub = bmesh.new()
    for sy in (1, -1):
        stick(ub, (0, sy * 0.15, 0), (0.03, sy * 0.13, -0.42), 0.065, 0.008, 0, 8)         # upper fangs down
    mesh_obj(name + "_fangs", ub, [M_TOOTH], parent=root, loc=(2.72, 0, 0.0))
    # wings: arm bone + 3 finger bones with a membrane fan, hinged at the shoulder
    wings = []
    for sy in (1, -1):
        w = empty(f"{name}_wing{sy}", (0.6, sy * 0.8, 0.35), parent=root)
        wb = bmesh.new()
        sh = Vector((0, 0, 0)); el = Vector((1.2, sy * 3.0, 0.3)); wr = Vector((0.4, sy * 5.6, 0.2))
        tips = [Vector((2.6, sy * 9.2, -0.2)), Vector((0.2, sy * 10.4, -0.6)), Vector((-2.2, sy * 8.6, -0.8)), Vector((-3.4, sy * 4.4, -0.6))]
        chain(wb, [sh, el, wr], [0.22, 0.16, 0.10], 1, 8)
        for tp in tips[:3]: chain(wb, [wr, (wr + tp) / 2 + Vector((0, 0, 0.15)), tp], [0.08, 0.05, 0.02], 1, 6)
        # membrane: wrist -> finger tips fan, plus the arm-to-body panel
        V = lambda p: wb.verts.new(p)
        vs, ve, vw = V(sh), V(el), V(wr); vt = [V(p) for p in tips]; vb = V(Vector((-2.4, sy * 0.6, -0.1)))
        def tri(a, b, c):
            try: wb.faces.new((a, b, c)).material_index = 0
            except Exception: pass
        tri(vs, ve, vw)
        for i in range(len(vt) - 1): tri(vw, vt[i], vt[i + 1])
        tri(vw, vt[-1], vb); tri(vw, vb, vs); tri(vw, vt[0], ve)
        sub = mesh_obj(f"{name}_wingmesh{sy}", wb, [M_BATWING, M_BATSKIN], parent=w)
        md = sub.modifiers.new("sub", 'SUBSURF'); md.levels = md.render_levels = 1
        wings.append((sy, w))
    # feet / claws
    fb = bmesh.new()
    for sy in (1, -1):
        for k in range(3):
            stick(fb, (-1.4, sy * (0.35 + k * 0.08), -0.5), (-1.85, sy * (0.40 + k * 0.1), -0.95), 0.05, 0.01, 0, 6)
    mesh_obj(name + "_feet", fb, [M_BATSKIN], parent=root)
    root.scale = (s, s, s)
    return root, wings, jaw

def flap(wings, t0, t1, speed=9.0, amp=1.0, every=1):
    for f, t in steps(t0, t1, every):
        a = math.sin(t * speed * 2 * math.pi / 2)
        for sy, w in wings:
            kf(w, t, rot=(sy * (0.25 + 0.75 * a * amp), 0.15 * a, sy * 0.1), interp='LINEAR', frame=f)
def fold_bat(wings, t, kind='fold'):
    for sy, w in wings:
        if kind == 'fold': kf(w, t, rot=(sy * -0.35, 0.0, sy * 1.45), scl=(0.6, 0.32, 1.0), interp='BEZIER')
        else: kf(w, t, rot=(sy * 0.2, 0.0, 0.0), scl=1.0, interp='BEZIER')

BAT_S = 1.25
BAT = make_bat("Bat", BAT_S)
bat_root, bat_wings, bat_jaw = BAT
BAT_Z = 1.05 * BAT_S + 0.25
bx, by = BITE[0] - 3.3 * BAT_S, BITE[1]
bk = [(5.20, (bx - 26, by - 14, 16.0, 0.6, 0.25)), (6.05, (bx - 0.6, by - 0.4, zs(bx, by) + BAT_Z + 1.2, 0.1, 0.0)),
      (6.30, (bx, by, zs(bx, by) + BAT_Z, 0.0, 0.0)), (6.40, (bx + 0.25, by, zs(bx, by) + BAT_Z - 0.15, 0.0, 0.28)),
      (8.30, (bx + 0.25, by, zs(bx, by) + BAT_Z - 0.15, 0.0, 0.28)), (8.45, (bx, by, zs(bx, by) + BAT_Z + 0.2, 0.0, -0.1)),
      (10.0, (bx + 22, by + 18, 18.0, 0.9, -0.3))]
for f, t in steps(5.20, 10.0, 1):
    x, y, z, yaw, pitch = sample(bk, t)
    air = t < 6.25 or t > 8.4
    if air: z += 0.35 * math.sin(t * 28)
    else: z += 0.04 * math.sin(t * 3.0)
    kf(bat_root, t, loc=(x, y, z), rot=(0.0, pitch, yaw), interp='LINEAR', frame=f)
flap(bat_wings, 5.20, 6.25, speed=8.0); fold_bat(bat_wings, 6.42, 'fold'); fold_bat(bat_wings, 8.32, 'fold')
fold_bat(bat_wings, 8.38, 'open'); flap(bat_wings, 8.40, 10.0, speed=8.0)
# bite: jaw opens, then clamps on "bit him"
for t, a in ((6.35, 0.0), (6.48, -0.55), (6.62, 0.12), (8.2, 0.12), (8.35, 0.0)):
    kf(bat_jaw, t, rot=(0, a, 0), interp='BEZIER')
vis_tree(bat_root, (T['S03'], T['S05']))

# ---------------------------------------------------------------- tingling: sparks around the bite
SPARKS = []
for i in range(26):
    sb = bmesh.new(); blob(sb, (0, 0, 0), (0.035, 0.035, 0.035), 0, 8)
    o = mesh_obj(f"Spark{i}", sb, [M_SPARK]); SPARKS.append(o)
    a0 = random.uniform(0, 2 * math.pi); r0 = random.uniform(0.2, 1.3); ph = random.uniform(0, 3)
    for f, t in steps(T['S07'], T['S08'], 2):
        a = a0 + t * 1.8; rr = r0 * (0.8 + 0.2 * math.sin(t * 7 + ph))
        x, y = BITE[0] + rr * math.cos(a), BITE[1] + rr * math.sin(a)
        on = 0.5 + 0.5 * math.sin(t * 13 + ph * 3)
        kf(o, t, loc=(x, y, zs(x, y) + 0.08 + 0.12 * on), scl=0.4 + 1.2 * on ** 3, interp='LINEAR', frame=f)
    vis(o, (T['S07'] + 0.9, T['S08']))

# ---------------------------------------------------------------- syringe into the arm
def make_syringe(name):
    root = empty(name)
    bm = bmesh.new()
    stick(bm, (0, 0, 0), (0, 0, 7.0), 0.55, 0.55, 0, 24)                # barrel
    sb2 = bmesh.new(); stick(sb2, (0, 0, 0.3), (0, 0, 6.2), 0.48, 0.48, 0, 24)
    nb = bmesh.new(); stick(nb, (0, 0, -0.1), (0, 0, -3.2), 0.045, 0.02, 0, 10); stick(nb, (0, 0, 0.0), (0, 0, -0.6), 0.2, 0.06, 0, 16)
    pb = bmesh.new(); stick(pb, (0, 0, 6.3), (0, 0, 10.5), 0.12, 0.12, 0, 8); stick(pb, (0, 0, 10.5), (0, 0, 10.8), 0.9, 0.9, 0, 24)
    mesh_obj(name + "_barrel", bm, [M_PLASTIC], parent=root)
    liq = mesh_obj(name + "_liquid", sb2, [M_VACC], parent=root)
    mesh_obj(name + "_needle", nb, [M_METAL], parent=root)
    plg = mesh_obj(name + "_plunger", pb, [M_PLASTIC], parent=root)
    return root, liq, plg
SYR = make_syringe("Syringe")
syr_root, syr_liq, syr_plg = SYR
sx, sy_ = BITE[0] - 2.2, BITE[1] - 1.2
ang = (0.0, math.radians(32), 0.0)
d = Vector((math.sin(ang[1]), 0, math.cos(ang[1])))
skin_pt = Vector((sx, sy_, zs(sx, sy_)))
for f, t in steps(T['S11'], T['S11b'], 2):
    u = smooth((t - T['S11'] - 0.3) / 0.6); push = smooth((t - T['S11'] - 1.1) / 0.8)
    p = skin_pt + d * (3.0 + 4.0 * (1 - u) - 0.9 * u)
    kf(syr_root, t, loc=tuple(p), rot=ang, interp='LINEAR', frame=f)
    kf(syr_plg, t, loc=(0, 0, -4.6 * push), interp='LINEAR', frame=f)
    kf(syr_liq, t, scl=(1, 1, max(0.05, 1 - 0.95 * push)), interp='LINEAR', frame=f)
vis_tree(syr_root, (T['S11'], T['S11b']))

# ================================================================ SET N: the nerve (x = 120) - micro, dark red
NX = 120.0
NERVE_PTS = [Vector((NX - 30, -2, -6)), Vector((NX - 15, 0, -3)), Vector((NX, 0, 0)), Vector((NX + 14, 1, 3)), Vector((NX + 26, 0, 7))]
def tube_obj(name, pts, r, mat, segs=24):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]; bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.materials.append(mat)
    return link(bpy.data.objects.new(name, cu))
NERVE = tube_obj("NerveFiber", NERVE_PTS, 1.6, M_NERVE)
for k in range(5):  # smaller fibers alongside
    off = Vector((random.uniform(-2, 2), random.uniform(6, 10), random.uniform(-6, 6)))
    tube_obj(f"Fiber{k}", [p + off + Vector((0, 0, random.uniform(-1, 1))) for p in NERVE_PTS], random.uniform(0.4, 0.9), M_NERVE)
# myelin rings
def along(u):
    # piecewise-linear point/tangent along NERVE_PTS (good enough for placement)
    L = [0.0]
    for i in range(len(NERVE_PTS) - 1): L.append(L[-1] + (NERVE_PTS[i + 1] - NERVE_PTS[i]).length)
    s = u * L[-1]
    for i in range(len(NERVE_PTS) - 1):
        if s <= L[i + 1] or i == len(NERVE_PTS) - 2:
            v = (s - L[i]) / (L[i + 1] - L[i]); a, b = NERVE_PTS[i], NERVE_PTS[i + 1]
            return a.lerp(b, v), (b - a).normalized()
for k in range(14):
    p, tg = along(0.04 + k * 0.07)
    rb = bmesh.new(); bmesh.ops.create_circle(rb, cap_ends=False, segments=32, radius=1.75)
    me = bpy.data.meshes.new(f"Myelin{k}"); rb.to_mesh(me); rb.free()
    o = link(bpy.data.objects.new(f"Myelin{k}", me)); o.location = p
    o.rotation_euler = tg.to_track_quat('Z', 'Y').to_euler()
    sk = o.modifiers.new("skin", 'SCREW')  # turn the circle into a short ring band
    sk.screw_offset = 0.5; sk.steps = 1; sk.render_steps = 1; sk.angle = 0; sk.axis = 'Z'
    so = o.modifiers.new("sol", 'SOLIDIFY'); so.thickness = 0.15
    me.materials.append(M_NERVE)
# the brain at the end of the nerve
brb = bmesh.new(); blob(brb, (0, 0, 0), (9, 7, 6), 0, 64)
BRAIN = mesh_obj("Brain", brb, [M_BRAIN], loc=(NX + 33, 0, 12))
tx = bpy.data.textures.new("gyri", 'VORONOI'); tx.noise_scale = 1.6; tx.distance_metric = 'DISTANCE'
dm = BRAIN.modifiers.new("gyri", 'DISPLACE'); dm.texture = tx; dm.strength = -1.2
sbm = BRAIN.modifiers.new("sub", 'SUBSURF'); sbm.levels = sbm.render_levels = 2
BRAIN.modifiers.move(1, 0)
# rabies virions: bullet shapes with spikes
def make_virion(name, s=1.0):
    root = empty(name)
    bm = bmesh.new()
    prof = []
    for i in range(21):
        x = -1 + 2 * i / 20
        r = 0.32 if x < 0.45 else 0.32 * math.sqrt(max(0.0, 1 - ((x - 0.45) / 0.55) ** 2))
        prof.append((x, max(0.01, r)))
    ring = 20; rows = []
    for x, r in prof:
        rows.append([bm.verts.new((x, r * math.cos(2 * math.pi * j / ring), r * math.sin(2 * math.pi * j / ring))) for j in range(ring)])
    for i in range(len(rows) - 1):
        for j in range(ring):
            bm.faces.new((rows[i][j], rows[i][(j + 1) % ring], rows[i + 1][(j + 1) % ring], rows[i + 1][j]))
    bm.faces.new(list(reversed(rows[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for i in range(1, 20, 2):
        x, r = prof[i]
        for j in range(0, ring, 2):
            a = 2 * math.pi * (j + 0.5 * (i % 4 == 1)) / ring
            p0 = Vector((x, r * math.cos(a), r * math.sin(a))); n = Vector((0, math.cos(a), math.sin(a)))
            stick(bm, p0, p0 + n * 0.12, 0.025, 0.04, 1, 5)
    o = mesh_obj(name + "_body", bm, [M_VIRUS, M_SPIKE], parent=root)
    root.scale = (s, s, s)
    return root, o
VIRS = []
for i in range(16):
    v = make_virion(f"Vir{i}", random.uniform(0.9, 1.25))
    u0 = random.uniform(-0.35, 0.25); ang0 = random.uniform(0, 2 * math.pi); spd = random.uniform(0.11, 0.16)
    for f, t in steps(T['S05'], T['S06'], 2):
        u = u0 + (t - T['S05']) * spd
        if u > 1.0:  # into the brain
            p = BRAIN.location + Vector((-7 + 4 * math.cos(ang0), 4 * math.sin(ang0), -3)) * min(1.0, 0.6 + (u - 1.0))
            tg = Vector((1, 0, 0.3)).normalized()
        else:
            p, tg = along(max(0.0, min(1.0, u)))
            side = Vector((0, math.cos(ang0 + t * 0.4), math.sin(ang0 + t * 0.4)))
            p = p + side * 1.95
        q = tg.to_track_quat('X', 'Z').to_euler()
        kf(v[0], t, loc=tuple(p), rot=(q.x + 0.1 * math.sin(t * 5 + i), q.y, q.z), interp='LINEAR', frame=f)
    VIRS.append(v)
    vis_tree(v[0], (T['S05'], T['S06']))
# glow travelling along the nerve (signal) on the nerve material
kval(M_NERVE.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'], T['S05'], 0.0)
M_NERVE.node_tree.nodes["Principled BSDF"].inputs['Emission Color'].default_value = (1.0, 0.45, 0.2, 1)
kval(M_NERVE.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'], T['S05b'] + 1.0, 0.25)

# ---- antibodies (vaccine) dissolving virions (S11b): reuse a cluster in front of the camera at x=120,y=40
AX = 120.0; AY = 40.0
ANTIS = []
for i in range(7):
    v = make_virion(f"VirB{i}", 1.1)
    base = Vector((AX + random.uniform(-3, 3), AY + random.uniform(-1.5, 1.5), random.uniform(-2.5, 2.5)))
    rot = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
    t_hit = T['S11b'] + 0.5 + i * 0.18
    for f, t in steps(T['S11b'], END_T if False else T['S12'], 2):
        sh = 1.0 if t < t_hit + 0.6 else max(0.0, 1 - (t - t_hit - 0.6) / 0.8)
        kf(v[0], t, loc=tuple(base + Vector((0.2 * math.sin(t * 2 + i), 0, 0.2 * math.cos(t * 1.7 + i)))), rot=rot, scl=1.1 * sh, interp='LINEAR', frame=f)
    vis_tree(v[0], (T['S11b'], T['S12']))
    # Y-shaped antibodies flying in and sticking
    for k in range(4):
        ab = bmesh.new()
        stick(ab, (0, 0, 0), (0, 0, 0.5), 0.05, 0.05, 0, 6)
        stick(ab, (0, 0, 0.5), (0.25, 0, 0.85), 0.05, 0.05, 0, 6); stick(ab, (0, 0, 0.5), (-0.25, 0, 0.85), 0.05, 0.05, 0, 6)
        o = mesh_obj(f"Ab{i}_{k}", ab, [M_ANTI])
        dirn = Vector((random.uniform(-1, 1), random.uniform(-1, 0.2), random.uniform(-1, 1))).normalized()
        tk = t_hit + k * 0.08
        for f, t in steps(T['S11b'], T['S12'], 2):
            u = smooth((t - (tk - 0.5)) / 0.5)
            p = base + dirn * (0.45 + 5.0 * (1 - u))
            sh = 1.0 if t < t_hit + 0.6 else max(0.0, 1 - (t - t_hit - 0.6) / 0.8)
            kf(o, t, loc=tuple(p), rot=(-dirn).to_track_quat('Z', 'Y').to_euler(), scl=max(0.001, sh), interp='LINEAR', frame=f)
        vis(o, (T['S11b'], T['S12']))

# ================================================================ SET T: the throat (x = 180) - cutaway
TX = 180.0
def throat():
    bm = bmesh.new(); seg = 40; rows = []
    for i in range(41):
        z = -12 + 24 * i / 40
        rr = 2.2 + 0.25 * math.sin(z * 0.8)
        rows.append([bm.verts.new((TX + rr * math.cos(math.pi * j / seg), rr * math.sin(math.pi * j / seg), z)) for j in range(seg + 1)])
    for i in range(40):
        for j in range(seg):
            bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj("ThroatTube", bm, [M_THROAT])
    o.data.materials.append(M_THROATCUT)
    so = o.modifiers.new("sol", 'SOLIDIFY'); so.thickness = 1.2; so.material_offset_rim = 1; so.use_rim = True
    return o
THR = throat()
# squeezing muscle band: a lattice-free way = a displaced ring mesh scaling in and out
SQ = []
def half_ring(name, R, r, z):
    bm = bmesh.new(); nu, nv = 40, 16; rows = []
    for i in range(nu + 1):
        a = math.pi * i / nu          # back half only (y >= 0)
        rows.append([bm.verts.new((R * math.cos(a) + r * math.cos(2 * math.pi * j / nv) * math.cos(a),
                                   R * math.sin(a) + r * math.cos(2 * math.pi * j / nv) * math.sin(a),
                                   r * math.sin(2 * math.pi * j / nv))) for j in range(nv)])
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((rows[i][j], rows[i][(j + 1) % nv], rows[i + 1][(j + 1) % nv], rows[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, [M_THROAT], loc=(TX, 0, z))
for k in range(3):
    o = half_ring(f"Squeeze{k}", 2.6, 0.55, 2.5 - k * 2.2); SQ.append(o)
    for f, t in steps(T['S08'], T['S09'], 2):
        sq = 0.5 + 0.5 * math.sin((t - T['S08']) * 9 - k * 0.9)
        s_ = 1.0 - 0.35 * sq * smooth((t - T['S08'] - 0.3) / 0.5)
        kf(o, t, scl=(s_, s_, 1.0 + 0.3 * sq), interp='LINEAR', frame=f)
# a gulp of water that gets stopped and pushed back up
wb_ = bmesh.new(); blob(wb_, (0, 0, 0), (1.0, 1.0, 1.3), 0, 28)
GULP = mesh_obj("Gulp", wb_, [simple('GulpWater', (0.45, 0.7, 0.95), rough=0.05, coat=1.0, emit=(0.3, 0.55, 0.9), es=0.4)])
for f, t in steps(T['S08'], T['S09'], 2):
    u = (t - T['S08'])
    z = 9 - 3.2 * smooth(u / 1.1) + 3.8 * smooth((u - 1.5) / 0.8)
    s_ = 1.0 + 0.15 * math.sin(u * 14) * (1 if 1.0 < u < 1.7 else 0)
    kf(GULP, t, loc=(TX, 0, z), scl=(s_, s_, 1 / s_), interp='LINEAR', frame=f)
vis(GULP, (T['S08'], T['S09']))

# ================================================================ SET M: the man (x = 400), bedroom; man scaled x100 (meters -> cm)
MX = 400.0
with bpy.data.libraries.load(os.path.join(CR, 'scenes', 'real', 'man.blend'), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
MAN = None
for o in dst.objects:
    if o is None: continue
    link(o)
    if o.type == 'ARMATURE': MAN = o
MAN.scale = (100, 100, 100)
PB = MAN.pose.bones
for b in PB: b.rotation_mode = 'XYZ'
def pose(t, d, interp='BEZIER'):
    """d: {bone: (x, y, z) degrees}"""
    for n, r in d.items():
        b = PB[n]; b.rotation_euler = tuple(math.radians(v) for v in r)
        set_interp(interp); b.keyframe_insert('rotation_euler', frame=F(t))
def man_at(t, loc, rot_deg, interp='CONSTANT'):
    set_interp(interp); MAN.location = loc; MAN.keyframe_insert('location', frame=F(t))
    MAN.rotation_euler = tuple(math.radians(v) for v in rot_deg); MAN.keyframe_insert('rotation_euler', frame=F(t))
NEUTRAL = {n: (0, 0, 0) for n in ('jaw', 'spine01', 'spine02', 'spine03', 'neck01', 'head', 'upperarm01.L', 'upperarm01.R',
                                   'lowerarm01.L', 'lowerarm01.R', 'upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R')}
# nightstand + glass + lamp (in front of him, toward -Y)
def box(name, c, half, mat, soft=0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    for v in bm.verts: v.co = Vector((v.co.x * half[0], v.co.y * half[1], v.co.z * half[2]))
    o = mesh_obj(name, bm, [mat], smooth_all=False); o.location = c
    bv = o.modifiers.new("bev", 'BEVEL'); bv.width = min(0.6, min(half) * 0.4) if not soft else min(half) * 0.45; bv.segments = 3 if not soft else 6
    for p_ in o.data.polygons: p_.use_smooth = True
    if soft:   # fabric: rounded, with soft folds
        rm = o.modifiers.new("rem", 'SUBSURF'); rm.levels = rm.render_levels = 2
        tx = bpy.data.textures.new(name + "_folds", 'CLOUDS'); tx.noise_scale = soft; tx.noise_depth = 2
        dsp = o.modifiers.new("folds", 'DISPLACE'); dsp.texture = tx; dsp.strength = soft * 0.12; dsp.texture_coords = 'GLOBAL'
    return o
STAND = box("Dresser", (MX + 14, -44, 55), (30, 18, 55), M_WOODN)
GX, GY, GZ = MX + 6, -36.0, 110.0
def glass_obj(name):
    root = empty(name, (GX, GY, GZ))
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=3.2, radius2=3.7, depth=12)
    for v in bm.verts: v.co.z += 6
    g = mesh_obj(name + "_glass", bm, [M_GLASS], parent=root)
    bb_ = bmesh.new(); bmesh.ops.create_cone(bb_, cap_ends=True, segments=48, radius1=3.2, radius2=3.2, depth=0.8)
    for v in bb_.verts: v.co.z += 0.4
    mesh_obj(name + "_base", bb_, [M_GLASS], parent=root)
    wb2 = bmesh.new(); bmesh.ops.create_cone(wb2, cap_ends=True, segments=48, radius1=3.0, radius2=3.4, depth=8.6)
    for v in wb2.verts: v.co.z += 5.1
    wat = mesh_obj(name + "_water", wb2, [M_WATER], parent=root)
    # ripples on top
    tx = bpy.data.textures.new("ripple", 'WOOD'); tx.wood_type = 'RINGNOISE'; tx.noise_basis_2 = 'SIN'; tx.turbulence = 2
    return root, wat
GL = glass_obj("WaterGlass")
gl_root, gl_water = GL
bk_ = bmesh.new(); bmesh.ops.create_grid(bk_, x_segments=1, y_segments=1, size=14)
GBACK = mesh_obj('GlassBackdrop', bk_, [simple('Backdrop', (1.0, 0.8, 0.55), emit=(1.0, 0.75, 0.5), es=2.5)]); GBACK.location = (GX - 2, GY + 30, GZ + 10); GBACK.rotation_euler = (math.radians(90), 0, 0)
VISSED.add(GBACK.name); vis(GBACK, (T['S02'], T['S03']))
area_l = plight('GlassBack', (GX - 6, GY + 18, GZ + 12), 3e3, (0.7, 0.85, 1.0), 4)
lb = bmesh.new(); stick(lb, (0, 0, 0), (0, 0, 14), 6, 4, 0, 32)
LAMP = mesh_obj("Lamp", lb, [M_LAMP], loc=(MX + 40, -50, 110))
lamp_l = plight("LampLight", (MX + 40, -50, 118), 2.0e4, (1.0, 0.72, 0.45), 6)
# bed behind him
BED = box("Bed", (MX - 20, 45, 25), (90, 110, 25), M_SHEET, soft=18)
PILLOW = box("Pillow", (MX - 20, 140, 52), (35, 13, 5), M_SHEET, soft=18)
BLANKET = box("Blanket", (MX - 20, 22, 66), (58, 72, 9), M_SHEET, soft=18)

# --- S01: he stands at the dresser and recoils from the glass of water
man_at(0.0, (MX, -10, 0), (0, 0, 0))
REC = {'jaw': (14, 0, 0), 'spine01': (-6, 0, 0), 'spine02': (-4, 0, 0), 'neck01': (4, 14, 0), 'head': (6, 30, 0),
       'upperarm01.L': (48, 0, -38), 'upperarm01.R': (48, 0, 38), 'lowerarm01.L': (45, 0, 0), 'lowerarm01.R': (45, 0, 0)}
pose(0.0, dict(NEUTRAL, **{'spine01': (-2, 0, 0), 'head': (2, 12, 0), 'neck01': (0, 6, 0), 'upperarm01.L': (25, 0, -40), 'upperarm01.R': (25, 0, 40),
                           'lowerarm01.L': (20, 0, 0), 'lowerarm01.R': (20, 0, 0)}))
pose(0.45, dict(NEUTRAL, **REC))
for t in (0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2):   # trembling
    j = 2.0 * math.sin(t * 37)
    pose(t, {'head': (6 + j, 30 + j, 0), 'neck01': (4, 14 + j * 0.5, 0)})
# S09: he sees the glass again and swats it away
pose(T['S09'] - 0.01, dict(NEUTRAL, **{'upperarm01.L': (0, 0, -42), 'upperarm01.R': (0, 0, 42)}))
pose(T['S09'] + 0.35, dict(NEUTRAL, **dict(REC, **{'upperarm01.R': (60, 0, 20), 'lowerarm01.R': (20, 0, 0)})))
pose(T['S09'] + 0.6, {'upperarm01.R': (55, 0, 70), 'lowerarm01.R': (10, 0, 0)})
# glass: stands; in S09 it tips over and falls off
kf(gl_root, T['S09'] + 0.45, loc=(GX, GY, GZ), rot=(0, 0, 0))
kf(gl_root, T['S09'] + 0.75, loc=(GX + 6, GY - 2, GZ + 1.5), rot=(0, math.radians(75), 0))
kf(gl_root, T['S09'] + 1.15, loc=(GX + 14, GY - 4, GZ - 30), rot=(0, math.radians(160), 0.4))
# water splash drops
DROPS = []
for i in range(40):
    db = bmesh.new(); r = random.uniform(0.25, 0.7); blob(db, (0, 0, 0), (r, r, r * 1.2), 0, 12)
    o = mesh_obj(f"Drop{i}", db, [M_WATER]); DROPS.append(o)
    v0 = Vector((random.uniform(4, 18), random.uniform(-6, 6), random.uniform(3, 14)))
    t0 = T['S09'] + 0.62 + random.uniform(0, 0.15)
    for f, t in steps(T['S09'], T['S10'], 1):
        u = max(0.0, t - t0)
        p = Vector((GX + 2, GY, GZ + 11)) + v0 * u + Vector((0, 0, -490 * u * u))
        kf(o, t, loc=tuple(p), scl=(1.0 if u > 0 else 0.0), interp='LINEAR', frame=f)
    vis(o, (t0, T['S10']))
# ripples: S02 push-in, the water surface trembles (keyed z-scale wobble)
for f, t in steps(T['S01'], T['S03'], 2):
    kf(gl_water, t, scl=(1, 1, 1 + 0.01 * math.sin(t * 40)), interp='LINEAR', frame=f)

# --- S06 fever, S12 asleep: lying in the bed
def lie(t):
    man_at(t, (MX - 20, -30, 62), (-90, 0, 0))
    pose(t, dict(NEUTRAL, **{'head': (6, 0, 0), 'upperarm01.L': (-28, 0, -10), 'upperarm01.R': (-28, 0, 10)}), interp='CONSTANT')
lie(T['S06'])
for t in [T['S06'] + i * 0.35 for i in range(6)]:   # restless head turns
    pose(t, {'head': (6, 10 * math.sin(t * 3), 0)})
man_at(T['S07'], (MX, -10, 0), (0, 0, 0)); pose(T['S07'], dict(NEUTRAL, **{'upperarm01.L': (0, 0, -42), 'upperarm01.R': (0, 0, 42)}), interp='CONSTANT')
man_at(T['S09'], (MX, -10, 0), (0, 0, 0))
lie(T['S12'])
# sweat drops on his forehead (S06)
SWEAT = []
for i in range(9):
    sb3 = bmesh.new(); r = random.uniform(0.18, 0.32); blob(sb3, (0, 0, 0), (r, r, r * 0.7), 0, 12)
    o = mesh_obj(f"Sweat{i}", sb3, [M_SWEAT]); SWEAT.append(o); VISSED.add(o.name)
    o.parent = MAN; o.parent_type = 'BONE'; o.parent_bone = 'head'
    o.location = (random.uniform(-0.05, 0.05) / 1.0, random.uniform(0.09, 0.13), random.uniform(-0.11, -0.095))
    o.scale = (0.01, 0.01, 0.01)
    vis(o, (T['S06'], T['S07']))

# ================================================================ SET H: hospital (x = 600)
HX = 600.0
HBED = box("HospBed", (HX, 0, 40), (50, 110, 10), M_HOSPBED, soft=18)
HFR = box("HospFrame", (HX, 0, 20), (52, 112, 18), M_METAL)
MON = box("Monitor", (HX + 62, 55, 118), (2, 22, 16), M_SCREEN)
POLE = box("MonPole", (HX + 62, 55, 52), (1.2, 1.2, 52), M_METAL)
def ecg(name, mat, flat_from=None):
    pts = []
    for i in range(160):
        u = i / 159; ph = (u * 3.3) % 1.0
        y = 0.0
        if flat_from is None:
            y = 7 if 0.45 < ph < 0.5 else (-3 if 0.5 < ph < 0.55 else (1.5 if 0.2 < ph < 0.3 else 0))
        pts.append(Vector((0, -18 + 36 * u, y)))
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.25
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    cu.materials.append(mat)
    o = link(bpy.data.objects.new(name, cu)); o.parent = MON; o.location = (2.3, 0, 0); return o
ECG1 = ecg("EcgBeat", M_ECG_G); ECG2 = ecg("EcgFlat", M_ECG_R, flat_from=0)
VISSED.update({ECG1.name, ECG2.name})
vis(ECG1, (T['S10'], 27.4)); vis(ECG2, (27.4, T['S11']))
# the beating line scrolls (keyed offset)
for f, t in steps(T['S10'], 27.4, 2):
    kf(ECG1, t, loc=(2.3, ((t * 6) % 6.0) - 3.0, 0), interp='LINEAR', frame=f)
mon_l = plight("MonLight", (HX + 64, 56, 120), 600, (0.3, 1.0, 0.5), 3)
set_interp('CONSTANT'); mon_l.data.energy = 600; mon_l.data.keyframe_insert('energy', frame=F(T['S10']))
mon_l.data.color = (0.3, 1.0, 0.5); mon_l.data.keyframe_insert('color', frame=F(T['S10']))
mon_l.data.color = (1.0, 0.1, 0.1); mon_l.data.keyframe_insert('color', frame=F(27.4))
man_at(T['S10'], (HX, -85, 62), (-90, 0, 0))
HBLANKET = box("HospBlanket", (HX, -18, 66), (48, 72, 9), M_HOSPBED, soft=18)
HPIL = box("HospPillow", (HX, 95, 52), (32, 12, 5), M_HOSPBED, soft=18)
pose(T['S10'], dict(NEUTRAL, **{'head': (6, 18, 0), 'upperarm01.L': (-28, 0, -10), 'upperarm01.R': (-28, 0, 10)}), interp='CONSTANT')
man_at(T['S11'], (MX, -10, 0), (0, 0, 0))

# ================================================================ CAMERAS
HEADF = empty("HeadFocus"); HEADF.parent = MAN; HEADF.parent_type = 'BONE'; HEADF.parent_bone = 'head'; HEADF.location = (0, 0.06, -0.08)
VISSED.add(HEADF.name)
BATF = empty("BatFocus", parent=bat_root, loc=(2.2, 0, 0.4)); VISSED.add(BATF.name)
BITEF = empty("BiteFocus", (BITE[0], BITE[1], zs(*BITE)))
GLF = empty("GlassFocus", parent=gl_root, loc=(0, 0, 9)); VISSED.add(GLF.name)
# S01 hook: low by the glass, his face recoiling behind it
camera("S01", T['S01'], [(0.0, (MX + 26, -112, 138), (MX + 3, -12, 146)), (3.30, (MX + 20, -98, 136), (MX + 3, -12, 148))],
       lens=40, dof=HEADF, fstop=2.2, head=0, shake=[(0.0, 0.7, 1.2)])
camera("S02", T['S02'], [(3.30, (GX + 3, GY - 34, GZ + 9), (GX, GY, GZ + 6)), (5.20, (GX + 1, GY - 17, GZ + 7.5), (GX, GY, GZ + 6))],
       lens=50, dof=GLF, fstop=2.0, head=0)
camera("S03", T['S03'], [(5.20, (BITE[0] - 4, BITE[1] - 26, 12), (BITE[0] - 6, BITE[1], 3)), (8.45, (BITE[0] + 2, BITE[1] - 17, 7), (BITE[0] - 2, BITE[1], 1.5))],
       lens=40, dof=BATF, fstop=1.8)
camera("S04", T['S04'], [(8.45, (BITE[0] + 2.2, BITE[1] - 2.4, 1.6), (BITE[0], BITE[1], zs(*BITE))), (10.07, (BITE[0] + 1.3, BITE[1] - 1.5, 1.0), (BITE[0], BITE[1], zs(*BITE)))],
       lens=50, dof=BITEF, fstop=1.4)
V0F = empty("VirFocus", parent=VIRS[3][0], loc=(0, 0, 0)); VISSED.add(V0F.name)
camera("S05", T['S05'], [(10.07, (NX - 24, -11, -1), (NX - 16, 0, -3)), (12.12, (NX - 8, -10, 3), (NX, 0, 0.5))],
       lens=35, dof=V0F, fstop=2.8, head=0)
camera("S05b", T['S05b'], [(12.12, (NX + 8, -13, 6), (NX + 22, 0, 6)), (14.58, (NX + 16, -16, 12), (NX + 31, 0, 11))],
       lens=35, dof=empty("BrainFocus", (NX + 26, 0, 8)), fstop=3.5, head=0)
camera("S06", T['S06'], [(14.58, (MX - 20 + 30, 100, 102), (MX - 20, 136, 70)), (16.55, (MX - 20 + 22, 108, 94), (MX - 20, 136, 70))],
       lens=50, dof=HEADF, fstop=1.8, head=0)
camera("S07", T['S07'], [(16.55, (BITE[0] + 3.6, BITE[1] - 4.0, 2.6), (BITE[0], BITE[1], zs(*BITE))), (20.08, (BITE[0] + 2.2, BITE[1] - 2.6, 1.7), (BITE[0], BITE[1], zs(*BITE)))],
       lens=45, dof=BITEF, fstop=1.6)
camera("S08", T['S08'], [(20.08, (TX + 2, -26, 4), (TX, 0, 1)), (23.19, (TX + 1, -19, 2), (TX, 0, 1.5))],
       lens=40, dof=empty("ThroatFocus", (TX, 0, 1)), fstop=4.0, head=0)
camera("S09", T['S09'], [(23.19, (GX + 38, GY - 72, GZ + 30), (GX - 4, GY + 4, GZ + 14)), (25.23, (GX + 44, GY - 80, GZ + 18), (GX + 6, GY, GZ + 2))],
       lens=40, dof=GLF, fstop=2.4, head=0, shake=[(23.6, 24.2, 1.5)])
camera("S10", T['S10'], [(25.23, (HX + 120, -110, 150), (HX + 30, 40, 85)), (29.58, (HX + 100, -85, 140), (HX + 45, 55, 100))],
       lens=35, dof=empty("MonFocus", (HX + 70, 60, 115)), fstop=2.8, head=0)
camera("S11", T['S11'], [(29.58, (BITE[0] - 9, BITE[1] - 10, 5), (BITE[0] - 2.4, BITE[1] - 1.2, 1.4)), (31.5, (BITE[0] - 7, BITE[1] - 8, 3.6), (BITE[0] - 2.2, BITE[1] - 1.2, 0.8))],
       lens=40, dof=empty("SyrFocus", (sx, sy_, zs(sx, sy_) + 1)), fstop=2.0)
camera("S11b", T['S11b'], [(31.5, (AX + 1, AY - 11, 1), (AX, AY, 0)), (33.87, (AX + 0.5, AY - 8, 0.5), (AX, AY, 0))],
       lens=40, dof=empty("AbFocus", (AX, AY, 0)), fstop=3.0, head=0)
# S12: the bat hangs from the headboard above him, eyes catching the light
BAT2 = make_bat("BatHang", 2.6)
b2_root, b2_wings, b2_jaw = BAT2
b2p = (MX - 20 + 22, 150, 118)
for f, t in steps(T['S12'], END_T, 2):
    kf(b2_root, t, loc=(b2p[0], b2p[1], b2p[2] + 0.3 * math.sin(t * 1.3)), rot=(0.12 * math.sin(t * 0.9), math.pi / 2, -math.pi / 2), interp='LINEAR', frame=f)
fold_bat(b2_wings, T['S12'], 'fold')
HB = box("Headboard", (MX - 20, 158, 75), (92, 4, 48), M_WOODN)
vis_tree(b2_root, (T['S12'], None))
B2F = empty("Bat2Focus", parent=b2_root, loc=(2.2, 0, 0.4)); VISSED.add(B2F.name)
camera("S12", T['S12'], [(33.87, (MX - 20 + 62, 92, 112), (MX - 20 + 22, 146, 104)), (END_T, (MX - 20 + 50, 104, 112), (MX - 20 + 22, 146, 106))],
       lens=45, dof=B2F, fstop=2.0, head=0)

# world + moonlight per shot
world_set(0.0, 3); world_set(T['S03'], 0); world_set(T['S05'], 2); world_set(T['S06'], 0); world_set(T['S07'], 0)
world_set(T['S08'], 2); world_set(T['S09'], 3); world_set(T['S10'], 1); world_set(T['S11'], 0); world_set(T['S11b'], 2); world_set(T['S12'], 0)
ad = wn.animation_data
for fc in ad.action.layers[0].strips[0].channelbag(ad.action_slot).fcurves:
    for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
sun_key(0.0, 0.6, (1.0, 0.85, 0.7)); sun_key(T['S03'], 1.6, (0.62, 0.72, 1.0)); sun_key(T['S05'], 0.0, (1, 1, 1))
sun_key(T['S06'], 1.2, (0.62, 0.72, 1.0)); sun_key(T['S07'], 1.6, (0.62, 0.72, 1.0)); sun_key(T['S08'], 0.0, (1, 1, 1))
sun_key(T['S09'], 0.6, (1.0, 0.85, 0.7)); sun_key(T['S10'], 1.5, (1.0, 1.0, 1.0)); sun_key(T['S11'], 1.8, (0.8, 0.9, 1.0))
sun_key(T['S11b'], 0.0, (1, 1, 1)); sun_key(T['S12'], 0.9, (0.55, 0.65, 1.0))
# micro sets get their own soft lights
for nm, loc, e, col in (("MicroKey", (NX - 10, -20, 25), 6e4, (1.0, 0.8, 0.7)), ("MicroRim", (NX + 30, 25, 10), 3e4, (1.0, 0.3, 0.2)),
                        ("ThroatKey", (TX - 10, -30, 20), 5e4, (1.0, 0.9, 0.85)), ("AbKey", (AX - 8, AY - 20, 12), 4e4, (0.8, 1.0, 0.9))):
    plight(nm, loc, e, col, 5)

# ================================================================ set visibility by x
SETS = [(-40, 40, [(T['S03'], T['S05']), (T['S07'], T['S08']), (T['S11'], T['S11b'])]),
        (80, 170, [(T['S05'], T['S06']), (T['S11b'], T['S12'])]),
        (170, 250, [(T['S08'], T['S09'])]),
        (300, 520, [(None, T['S03']), (T['S06'], T['S07']), (T['S09'], T['S10']), (T['S12'], None)]),
        (520, 700, [(T['S10'], T['S11'])])]
cam_objs = {c[1] for c in CAMS} | {c[2] for c in CAMS}
bpy.context.view_layer.update()
for o in list(sc.objects):
    if o in cam_objs or o.type in ('CAMERA', 'EMPTY'): continue
    if o.name in VISSED or (o.parent and o.parent.name in VISSED): continue
    if o.type == 'ARMATURE': continue
    if o.parent == MAN: continue
    try: x = sum((o.matrix_world @ Vector(c)).x for c in o.bound_box) / 8
    except Exception: x = o.matrix_world.translation.x
    if o.type == 'LIGHT': x = o.matrix_world.translation.x
    for x0, x1, spans in SETS:
        if x0 <= x < x1: vis(o, *spans); break
# the man is visible in the bedroom shots and the hospital
for o in [MAN] + list(MAN.children):
    if o.type == 'MESH' and o.name not in VISSED:
        vis(o, (None, T['S03']), (T['S06'], T['S07']), (T['S09'], T['S11']), (T['S12'], None))
CAMS.sort(key=lambda c: c[0])
for i, (t0, cam, hl) in enumerate(CAMS):
    hl.hide_render = True; hl.keyframe_insert('hide_render', frame=1)
    hl.hide_render = False; hl.keyframe_insert('hide_render', frame=F(t0))
    if i + 1 < len(CAMS): hl.hide_render = True; hl.keyframe_insert('hide_render', frame=F(CAMS[i + 1][0]))
set_interp('BEZIER')
def fc_of(idb):
    ad_ = idb.animation_data
    if not ad_ or not ad_.action: return []
    return list(ad_.action.layers[0].strips[0].channelbag(ad_.action_slot).fcurves)
for fc in fc_of(MAN):
    if fc.data_path in ('location', 'rotation_euler'):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

CUTF = {F(v) for v in T.values()} | {F(T['S09']) - 1}
for fc in fc_of(MAN):
    kp = list(fc.keyframe_points)
    for i in range(len(kp) - 1):
        if int(round(kp[i + 1].co.x)) in CUTF or int(round(kp[i + 1].co.x)) - 1 in CUTF:
            kp[i].interpolation = 'CONSTANT'

sc.view_layers[0].use_pass_mist = True
world.mist_settings.start = 60; world.mist_settings.depth = 420; world.mist_settings.falloff = 'QUADRATIC'
try:
    ng = sc.compositing_node_group
    rl = [n for n in ng.nodes if n.type == 'R_LAYERS'][0]; gl = [n for n in ng.nodes if n.type == 'GLARE'][0]
    mx = ng.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    A, B, Fc, O = mx.inputs[6], mx.inputs[7], mx.inputs[0], mx.outputs[2]
    mt = ng.nodes.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = 0.16
    ng.links.new(rl.outputs['Mist'], mt.inputs[0]); ng.links.new(mt.outputs[0], Fc)
    ng.links.new(rl.outputs['Image'], A); B.default_value = (0.30, 0.27, 0.29, 1)
    ng.links.new(O, gl.inputs['Image'])
    print("MIST FOG ON")
except Exception as e: print("mist comp skipped:", e)

# ================================================================ save / preview
os.makedirs(os.path.join(ROOT, "scenes"), exist_ok=True); os.makedirs(OUT, exist_ok=True)
sc.camera = CAMS[0][1]; sc.frame_set(1)
if MODE == 'build' or globals().get('SAVE'):
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes", "rabies.blend"), compress=True)

def still(cam, frame, name):
    sc.frame_set(frame); sc.camera = cam
    sc.render.filepath = os.path.join(OUT, "stills", name)
    bpy.ops.render.render(write_still=True); print("STILL", name, frame, flush=True)

if MODE == 'preview':
    os.makedirs(os.path.join(OUT, "stills"), exist_ok=True)
    sc.render.resolution_percentage = PCT
    marks = sorted(sc.timeline_markers, key=lambda m: m.frame)
    only = globals().get('ONLY'); at = globals().get('AT', [0.5])
    for i, m in enumerate(marks):
        if only and m.name not in only: continue
        nxt = marks[i + 1].frame if i + 1 < len(marks) else sc.frame_end
        for u in at:
            f = int(m.frame + (nxt - 1 - m.frame) * float(u)); still(m.camera, f, f"{m.name}_{f:04d}.jpg")
    sc.render.resolution_percentage = 100
print("RABIES DONE", MODE)
