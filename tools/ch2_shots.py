# shots for ch2_bl.py (exec'd inside it)
M_CARPET = noisy("Carpet", (0.12, 0.02, 0.02), (0.22, 0.05, 0.04), scale=8, rough=0.95, bump=0.4)
M_CREAM = noisy("Cream", (0.55, 0.48, 0.36), (0.66, 0.58, 0.45), scale=2, rough=0.8, bump=0.05)
M_BLANKET = noisy("Blanket", (0.32, 0.28, 0.22), (0.45, 0.40, 0.32), scale=3, rough=0.95, bump=0.5)
M_ALU = noisy("Alu", (0.6, 0.62, 0.64), (0.75, 0.77, 0.79), scale=10, rough=0.25, metal=1.0, bump=0.02)
M_SODALIQ = glassy("Cola", (0.12, 0.04, 0.02), 0.0, 1.34)
M_PET = glassy("PET", (0.93, 0.96, 0.95), 0.02, 1.45)
M_MIRROR = simple("Mirror", (0.8, 0.8, 0.8), rough=0.05, metal=1.0)
M_SHELFW = simple("ShelfWhite", (0.8, 0.8, 0.78), rough=0.5)

def curtain(name, x0, x1, y, z0, z1, mat, gap=None):
    bm = bmesh.new(); nx, nz = 70, 12; verts = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        row = []
        for k in range(nz + 1):
            z = z0 + (z1 - z0) * k / nz
            row.append(bm.verts.new((x, y + 2.5 * math.sin(x * 0.32) + 0.8 * math.sin(x * 1.1), z)))
        verts.append(row)
    for i in range(nx):
        for k in range(nz): bm.faces.new((verts[i][k], verts[i + 1][k], verts[i + 1][k + 1], verts[i][k + 1]))
    return mesh_obj(name, bm, [mat])
def cyl(name, r, h, mat, loc, rot=(0, 0, 0), seg=16):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    o = mesh_obj(name, bm, [mat]); o.location = loc; o.rotation_euler = rot; return o

# ================================================================ N1 Pullman sleeper car at night
n = "N1_train"; X = SX(n); WORLD[n] = 2
box("TrainFloor", (X, 0, -1), (760, 150, 1), M_CARPET, 0.2)
box("TrainCeil", (X, 0, 262), (760, 150, 2), M_CREAM, 0.2)
for s in (-1, 1): box(f"TrainWall{s}", (X, s * 152, 130), (760, 2, 132), M_MAHOG, 0.2)
for i, sx in enumerate(range(-600, 700, 190)):
    for s in (-1, 1):
        box(f"LB{i}{s}", (X + sx, s * 105, 42), (88, 45, 8), M_MAHOG, 1.0)
        box(f"LM{i}{s}", (X + sx, s * 105, 53), (86, 43, 4), M_BLANKET, 2.0)
        box(f"UB{i}{s}", (X + sx, s * 105, 168), (88, 45, 6), M_MAHOG, 1.0)
        box(f"Div{i}{s}", (X + sx - 92, s * 105, 130), (3, 45, 125), M_MAHOG, 0.8)
        open_ = (i == 3 and s == 1)
        if not open_:
            curtain(f"CurL{i}{s}", X + sx - 88, X + sx + 88, s * 60, 18, 150, M_VELVET)
            curtain(f"CurU{i}{s}", X + sx - 88, X + sx + 88, s * 60, 152, 246, M_VELVET)
        else:
            curtain(f"CurL{i}{s}", X + sx - 88, X + sx + 88, s * 60, 18, 150, M_VELVET)
            curtain(f"CurU{i}{s}", X + sx - 88, X + sx - 50, s * 60, 152, 246, M_VELVET)
            b = box("Rumple", (X + sx + 10, s * 100, 177), (70, 38, 4), M_BLANKET, 3.0); b.rotation_euler = (0.05, 0.03, 0.06)
            sub = b.modifiers.new("ss", 'SUBSURF'); sub.levels = 2
            d = b.modifiers.new("disp", 'DISPLACE'); tx = bpy.data.textures.new("rumpleT", 'CLOUDS'); tx.noise_scale = 18; d.texture = tx; d.strength = 6
            for k in range(5): cyl(f"Ladder{k}", 0.8, 70, M_BRASS, (X + sx + 60, s * 62, 40 + k * 25), (0, math.pi / 2, 0)) if False else None
            cyl("LadderA", 1.0, 150, M_BRASS, (X + sx + 50, s * 62, 95)); cyl("LadderB", 1.0, 150, M_BRASS, (X + sx + 75, s * 62, 95))
            for k in range(5): cyl(f"Rung{k}", 0.8, 25, M_BRASS, (X + sx + 62.5, s * 62, 40 + k * 28), (0, math.pi / 2, 0))
        cyl(f"Rail{i}{s}", 0.9, 180, M_BRASS, (X + sx, s * 60, 248), (0, math.pi / 2, 0), 10)
for i, sx in enumerate(range(-600, 700, 190)):
    lathe(f"Bowl{i}", [(0, 0), (9, 0), (7, -5), (0, -6)], M_GLOWW, 24, loc=(X + sx, 0, 259))
    L(f"TrL{i}", (X + sx, 0, 245), 1.08e+05, (1.0, 0.68, 0.38), 6, n)
box("EndWall", (X + 700, 0, 130), (3, 150, 132), M_MAHOG, 0.3)
box("EndWin", (X + 698, 0, 150), (1, 30, 40), M_CLEAR, 0.2)
# passing lights outside the end window
pl = bpy.data.lights.new("Pass", 'POINT'); pl.energy = 6e5; pl.color = (1.0, 0.8, 0.5); pl.shadow_soft_size = 30
PO = link(bpy.data.objects.new("Pass", pl)); LIGHTS.append((PO, span(n)))
t0, t1 = span(n)
for k in range(5):
    PO.location = (X + 760, -400, 160); PO.keyframe_insert('location', frame=F(t0 + k * 1.4))
    PO.location = (X + 760, 400, 160); PO.keyframe_insert('location', frame=F(t0 + k * 1.4 + 1.2))
fogbox("TrainFog", (X, 0, 130), (750, 140, 128), 0.0003, (0.9, 0.8, 0.7)); FOGS.append((bpy.data.objects["TrainFog"], n))
cam(n, [(0, (X - 660, -10, 150), (X + 600, 20, 140)), (1, (X - 470, 8, 146), (X + 600, 0, 150))], lens=26)

# ================================================================ N2 doctor's desk
n = "N2_desk"; X = SX(n); WORLD[n] = 1
box("Desk", (X, 0, 75), (90, 50, 3), M_MAHOG, 1.0)
box("DeskWall", (X, 160, 150), (300, 3, 150), M_MAHOG, 0.3)
HBD = radithor("DeskBottle", hero=True); HBD.location = (X + 8, -6, 78); HBD.rotation_euler.z = math.radians(30)
plane("RxPad", 13, 18, M_RX, (X - 20, -4, 78.15), (-math.pi / 2, 0, math.radians(-12)))
for i, (h, c) in enumerate([(4, 0), (3, 1), (5, 2), (3.5, 3)]):
    box(f"Book{i}", (X - 52, 18, 78 + sum([4, 3, 5, 3.5][:i]) + h / 2), (16, 11, h / 2), M_BOOK[c], 0.4).rotation_euler.z = random.uniform(-0.15, 0.15)
cyl("Pen", 0.6, 14, M_RUBBER, (X - 6, -14, 78.7), (0, math.pi / 2, math.radians(25)))
lathe("LampBase", [(0, 0), (9, 0), (9, 1.5), (2, 3), (0, 3)], M_BRASS, 32, loc=(X + 45, 22, 78))
cyl("LampStem", 1, 30, M_BRASS, (X + 45, 22, 93))
sh = lathe("Shade", [(0, -15), (5, -15), (7, -10), (7.5, 10), (5, 15), (0, 15)], M_LAMPG, 32, loc=(X + 45, 14, 110)); sh.rotation_euler = (0, math.pi / 2, 0); sh.scale = (1, 1.6, 1)
cyl("Bulb", 2, 18, M_GLOWW, (X + 45, 14, 104), (0, math.pi / 2, 0))
L("DeskLamp", (X + 45, 10, 100), 1.5e+05, (1.0, 0.75, 0.45), 4, n)
L("DeskFill", (X - 80, -120, 160), 1.2e+05, (0.6, 0.7, 1.0), 40, n)
DF = empty("DeskFocus", (X + 6, -9, 80))
cam(n, [(0, (X + 30, -60, 92), (X + 6, 0, 82)), (1, (X + 22, -44, 88), (X + 6, 0, 82))], lens=55, dof=DF, fstop=2.0)

# ================================================================ N3 Bailey's lab
n = "N3_lab"; X = SX(n); WORLD[n] = 1
box("LabFloor", (X, 0, -1), (400, 400, 1), M_FLOOR, 0.2)
box("Bench", (X, 0, 85), (140, 40, 3), M_MAHOG, 1.0)
box("BenchBody", (X, 5, 42), (135, 35, 40), M_PLANK, 1.0)
box("LabWall", (X, 70, 150), (300, 3, 150), M_PLASTER, 0.3)
for k, z in enumerate((140, 180, 220)):
    box(f"LShelf{k}", (X, 58, z), (140, 10, 1.5), M_PLANK, 0.3)
    for j in range(16):
        jx = X - 130 + j * 17
        if (j + k) % 3 == 0: lathe(f"Jar{k}{j}", [(0, 0), (5, 0), (5, 14), (3, 16), (3, 19), (0, 19)], M_CLEAR, 20, loc=(jx, 58, z + 1.5))
        else:
            b = radithor(f"SB{k}{j}"); b.location = (jx, 58, z + 1.5); b.scale = (1.4, 1.4, 1.4)
proto = collection_of(lambda: radithor("RBproto"), "RadProto")
for i in range(6):
    for j in range(9): inst(f"RB{i}{j}", proto, (X - 40 + j * 5.2, -18 + i * 5.2, 88))
for i in range(3):
    lathe(f"Flask{i}", [(0, 0), (8, 0), (8.5, 1), (3, 14), (2, 15), (2, 22), (0, 22)], M_CLEAR, 32, loc=(X + 40 + i * 22, -10 + (i % 2) * 8, 88))
    lathe(f"FlaskW{i}", [(0, 0.3), (7.6, 0.3), (5.5, 6), (0, 6)], M_WATER, 32, loc=(X + 40 + i * 22, -10 + (i % 2) * 8, 88))
box("Crate", (X - 95, -5, 99), (22, 16, 11), M_PLANK, 0.6)
plane("CrateL", 40, 15, M_CRATEL, (X - 95, -21.2, 99), (0, 0, 0))
area("LabWin", (X + 260, -120, 220), (0, math.radians(60), math.radians(55)), 8e5, (1.0, 0.85, 0.65), 120, n)
fogbox("LabFog", (X, 0, 150), (300, 200, 150), 0.0004, (1, 0.9, 0.8)); FOGS.append((bpy.data.objects["LabFog"], n))
LF = empty("LabFocus", (X - 15, -5, 92))
cam(n, [(0, (X - 120, -130, 125), (X - 25, 0, 95)), (1, (X - 10, -120, 118), (X + 10, 0, 95))], lens=38, dof=LF, fstop=3.2)

# ================================================================ N4 stable with crates of Radithor
n = "N4_stable"; X = SX(n); WORLD[n] = 1
fl = box("StableFloor", (X, 0, -1), (400, 400, 1), M_HAY, 0.2)
add_hair(fl, 12000, 5.0, 0, radius=0.08, normal=0.2, rand=1.0, seed=3)
box("StableBack", (X, 150, 150), (300, 4, 150), M_PLANK, 0.3)
for s in (-1, 1): box(f"Stall{s}", (X + s * 120, 60, 75), (4, 90, 75), M_PLANK, 0.5)
for k in range(3): box(f"Beam{k}", (X - 150 + k * 150, 60, 280), (8, 120, 8), M_PLANK, 1)
hb = bmesh.new(); blob(hb, (0, 0, 0), (70, 45, 35), 0, 30); hay = mesh_obj("HayPile", hb, [M_HAY], loc=(X - 60, 95, 0))
add_hair(hay, 9000, 9.0, 0, radius=0.1, normal=0.6, rand=1.0, seed=5)
for i, (dx, dz, rz) in enumerate([(20, 11, 0.05), (66, 11, -0.08), (42, 33, 0.12)]):
    box(f"SCrate{i}", (X + dx, 30, dz), (22, 16, 11), M_PLANK, 0.6).rotation_euler.z = rz
    pc = plane(f"SCrateL{i}", 40, 15, M_CRATEL, (X + dx, 13.6, dz), (0, 0, 0)); pc.parent = None
for i in range(5):
    b = radithor(f"StB{i}", hero=(i < 2)); b.location = (X + 30 + i * 6, 25 - (i % 2) * 5, 44); b.rotation_euler.z = random.uniform(-1, 1)
lathe("Bucket", [(0, 0), (12, 0), (14, 26), (14.5, 27), (0, 27)], M_STEEL, 32, loc=(X - 20, 10, 0))
area("SunBeam", (X + 180, -60, 300), (0, math.radians(50), math.radians(70)), 1.2e6, (1.0, 0.85, 0.6), 30, n)
L("StableFill", (X - 100, -200, 150), 9e+04, (0.6, 0.7, 1.0), 60, n)
fogbox("StableDust", (X, 0, 150), (300, 200, 150), 0.0006, (1, 0.9, 0.75)); FOGS.append((bpy.data.objects["StableDust"], n))
SF = empty("StableFocus", (X + 40, 20, 40))
cam(n, [(0, (X - 60, -170, 70), (X + 40, 30, 35)), (1, (X - 20, -130, 62), (X + 40, 30, 38))], lens=35, dof=SF, fstop=3.0)

# ================================================================ N5 mausoleum vault
n = "N5_mausoleum"; X = SX(n); WORLD[n] = 2
box("MFloor", (X, 0, -1), (300, 400, 1), M_STONE, 0.3)
for s in (-1, 1): box(f"MWall{s}", (X + s * 200, 0, 170), (4, 400, 170), M_STONE, 0.3)
box("MBack", (X, 300, 170), (200, 4, 170), M_STONE, 0.3)
box("MCeil", (X, 0, 340), (200, 400, 4), M_STONE, 0.3)
for s in (-1, 1):
    for r in range(3):
        for c in range(4):
            box(f"Crypt{s}{r}{c}", (X + s * 194, -60 + c * 90, 60 + r * 90), (3, 38, 36), M_STONE, 1.5)
for s in (-1, 1): lathe(f"Col{s}", [(0, 0), (22, 0), (20, 8), (16, 12), (15, 300), (20, 306), (22, 314), (0, 314)], M_STONE, 32, loc=(X + s * 120, 250, 0))
box("Slab", (X, 120, 35), (55, 120, 35), M_STONE, 2.0)
def coffin_shape(name, sc_, h, mat, bev, loc):
    pts = [(-0.55, 1.0), (-1.0, 0.42), (-0.62, -1.0), (0.62, -1.0), (1.0, 0.42), (0.55, 1.0)]
    bm = bmesh.new(); bot = [bm.verts.new((x * sc_[0], y * sc_[1], 0)) for x, y in pts]
    f = bm.faces.new(bot); r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]: v.co.z = h
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, [mat], smooth_all=False); o.location = loc
    b = o.modifiers.new("bev", 'BEVEL'); b.width = bev; b.segments = 3; b.limit_method = 'ANGLE'
    for p_ in o.data.polygons: p_.use_smooth = True
    return o
cof = coffin_shape("LeadCoffin", (34, 100), 40, M_LEAD, 1.5, (X, 120, 70))
coffin_shape("CofLid", (36, 102), 4, M_LEAD, 1.2, (X, 120, 110))
area("Doorway", (X, -420, 160), (math.radians(80), 0, 0), 7e5, (0.75, 0.85, 1.0), 120, n)
L("MCandleB", (X + 70, 60, 150), 3e5, (0.7, 0.8, 1.0), 30, n)
L("MCandle", (X - 60, 230, 120), 1.8e+04, (1.0, 0.6, 0.3), 3, n)
fogbox("MFog", (X, 0, 170), (196, 396, 168), 0.0004, (0.8, 0.85, 0.95)); FOGS.append((bpy.data.objects["MFog"], n))
cam(n, [(0, (X + 10, -330, 150), (X, 120, 95)), (1, (X + 6, -150, 135), (X, 120, 95))], lens=30, dof=cof, fstop=4.0)

# ================================================================ J1 drugstore shelf of Jamaica ginger
n = "J1_shelf"; X = SX(n); WORLD[n] = 1
box("ShelfBack", (X, 25, 140), (260, 3, 140), M_MAHOG, 0.3)
jp = collection_of(lambda: jake_bottle("JKproto"), "JakeProto")
for k, z in enumerate((40, 90, 140, 190)):
    box(f"JShelf{k}", (X, 5, z), (250, 20, 1.5), M_MAHOG, 0.4)
    for j in range(36):
        jx = X - 240 + j * 13.5 + random.uniform(-1, 1)
        if k == 2 and 14 <= j <= 20:
            b = jake_bottle(f"JH{j}", hero=True); b.location = (jx, -4, z + 1.5); b.rotation_euler.z = random.uniform(-0.2, 0.2)
        else: inst(f"JB{k}{j}", jp, (jx, 2 + random.uniform(-3, 3), z + 1.5), (0, 0, random.uniform(-0.3, 0.3)))
L("ShelfKey", (X + 60, -160, 200), 5.4e+05, (1.0, 0.75, 0.45), 30, n)
L("ShelfRim", (X - 200, -40, 260), 2.4e+05, (0.7, 0.8, 1.0), 20, n)
JF = empty("JakeFocus", (X - 30, -6, 150))
cam(n, [(0, (X - 110, -60, 152), (X - 60, 0, 148)), (1, (X + 10, -52, 150), (X + 50, 0, 148))], lens=40, dof=JF, fstop=2.2)

# ================================================================ J2 drums of TOCP
n = "J2_drums"; X = SX(n); WORLD[n] = 2
box("DFloor", (X, 0, -1), (600, 600, 1), M_CONC, 0.2)
box("DWall", (X, 450, 250), (600, 4, 250), M_CONC, 0.3)
for i in range(4):
    for j in range(3):
        if i in (1, 2) and j == 1: continue
        drum(f"Drum{i}{j}", M_TOCP, (X - 180 + i * 120, 80 + j * 110, 0), random.uniform(0, 6.28))
vat = lathe("Vat", [(0, 0), (90, 0), (95, 10), (95, 200), (90, 210), (0, 210)], M_STEEL, 48, loc=(X, 330, 0))
for k in range(3): cyl(f"Pipe{k}", 5, 300, M_STEEL, (X - 60 + k * 60, 330, 260))
lathe("HangShade", [(0, 0), (30, -14), (32, -16), (0, -4)], M_STEEL, 32, loc=(X, 120, 330))
L("DrumFront", (X - 40, -150, 120), 1.2e6, (1.0, 0.85, 0.65), 40, n)
L("HangL", (X, 120, 300), 1.32e+06, (1.0, 0.85, 0.6), 10, n)
L("DrumRim", (X + 300, 500, 200), 1.8e+06, (0.5, 0.8, 0.6), 60, n)
fogbox("DFog", (X, 200, 200), (580, 400, 200), 0.0004, (0.7, 0.8, 0.7)); FOGS.append((bpy.data.objects["DFog"], n))
DFc = empty("DrumFocus", (X - 60, 80, 45))
cam(n, [(0, (X - 20, -230, 90), (X - 40, 150, 60)), (1, (X - 30, -110, 70), (X - 50, 150, 55))], lens=28, dof=DFc, fstop=4.0)

# ================================================================ J3 1930 ward: empty beds, canes and crutches
n = "J3_ward"; X = SX(n); WORLD[n] = 1
box("WFloor", (X, 0, -1), (700, 400, 1), M_TILE, 0.2)
box("WWall", (X, 220, 200), (700, 4, 200), M_PLASTER, 0.3)
for k in range(5):
    plane(f"WWin{k}", 90, 180, M_GLOWC, (X - 500 + k * 250, 216, 200), (math.pi / 2, 0, 0) if False else (0, 0, 0))
    area(f"WWinL{k}", (X - 500 + k * 250, 190, 200), (math.radians(-90), 0, 0), 1.2e4, (0.9, 0.95, 1.0), 90, n)
for b in range(6):
    bx = X - 500 + b * 200
    box(f"Mat{b}", (bx, 110, 55), (45, 95, 9), M_SHEET, 3.0)
    box(f"Pil{b}", (bx, 190, 68), (35, 12, 7), M_SHEET, 4.0)
    for s in (-1, 1):
        for e in (0, 1):
            cyl(f"Leg{b}{s}{e}", 1.6, 100 if e else 70, M_IRON, (bx + s * 46, 15 + e * 190, 50 if e else 35))
        cyl(f"Head{b}{s}", 1.2, 92, M_IRON, (bx, 15 + (s > 0) * 190, 95 if s > 0 else 68), (0, math.pi / 2, 0))
cam(n, [(0, (X - 600, -160, 120), (X - 300, 120, 60)), (1, (X - 380, -170, 115), (X - 50, 120, 60))], lens=30)

# ================================================================ P1 barrels of denatured (poisoned) alcohol
n = "P1_barrels"; X = SX(n); WORLD[n] = 3
box("PFloor", (X, 0, -1), (400, 1400, 1), M_CONC, 0.2)
dp = collection_of(lambda: drum("DNproto", M_DENAT, (0, 0, 0)), "DenatProto")
for row in (-1, 1):
    for k in range(14):
        for lvl in range(2):
            inst(f"DN{row}{k}{lvl}", dp, (X + row * 110, -200 + k * 64, lvl * 90), (0, 0, random.uniform(-0.6, 0.6) + (math.pi if row < 0 else 0)))
for k in range(7):
    lathe(f"Tube{k}", [(0, 0), (4, 0), (4, 160), (0, 160)], M_GLOWC, 12, loc=(X, -200 + k * 150, 330)).rotation_euler = (math.pi / 2, 0, 0)
    L(f"TubeL{k}", (X, -200 + k * 150 + 80, 320), 3.6e+05, (0.85, 0.92, 1.0), 20, n)
fogbox("PFog", (X, 300, 200), (380, 1000, 200), 0.0012, (0.8, 0.85, 0.9)); FOGS.append((bpy.data.objects["PFog"], n))
cam(n, [(0, (X + 10, -380, 110), (X - 20, 600, 80)), (1, (X + 5, -240, 120), (X - 10, 600, 80))], lens=30)

# ================================================================ P2 speakeasy bar
n = "P2_speakeasy"; X = SX(n); WORLD[n] = 2
box("SFloor", (X, 0, -1), (500, 400, 1), M_FLOOR, 0.2)
box("BarTop", (X, 0, 108), (260, 30, 3), M_MAHOG, 1.0)
box("BarBody", (X, 6, 54), (255, 26, 52), M_MAHOG, 1.0)
cyl("FootRail", 2, 500, M_BRASS, (X, -32, 18), (0, math.pi / 2, 0))
box("BackBar", (X, 120, 150), (260, 10, 150), M_MAHOG, 0.5)
plane("Mirror", 480, 110, M_MIRROR, (X, 108, 190))
bp = bpy.data.collections.new("LiqProto")
def liq_bottle():
    r = empty("LQproto")
    lathe("LQg", [(0, 0), (3.6, 0), (3.6, 18), (1.2, 23), (1.1, 29), (0, 29)], M_CLEAR, 20, parent=r)
    lathe("LQl", [(0, 0.3), (3.3, 0.3), (3.3, 14), (0, 14)], M_BEER, 20, parent=r)
    return r
lqp = collection_of(liq_bottle, "LiqProto2")
for k, z in enumerate((122, 162)):
    box(f"BBShelf{k}", (X, 96, z), (250, 12, 1.5), M_MAHOG, 0.3)
    for j in range(40): inst(f"LQ{k}{j}", lqp, (X - 240 + j * 12, 96, z + 1.5), (0, 0, random.uniform(0, 6)))
for j in range(7):
    gx = X - 60 + j * 22
    lathe(f"Shot{j}", [(0, 0), (2.6, 0), (3.0, 7), (0, 7)], M_CLEAR, 20, loc=(gx, -8, 111))
    lathe(f"ShotL{j}", [(0, 0.6), (2.5, 0.6), (2.8, 5.5), (0, 5.5)], M_BEER, 20, loc=(gx, -8, 111))
b = liq_bottle(); b.location = (X + 90, -4, 111)
for k in range(4): L(f"BarL{k}", (X - 180 + k * 120, -20, 200), 1.5e+05, (1.0, 0.6, 0.3), 8, n)
fogbox("Smoke", (X, 0, 150), (480, 380, 150), 0.0009, (0.85, 0.8, 0.75)); FOGS.append((bpy.data.objects["Smoke"], n))
SPF = empty("BarFocus", (X + 10, -8, 115))
cam(n, [(0, (X - 160, -80, 128), (X - 20, 0, 112)), (1, (X - 40, -78, 124), (X + 90, 0, 112))], lens=40, dof=SPF, fstop=2.0)

# ================================================================ L1 2010 party table of tall cans
n = "L1_party"; X = SX(n); WORLD[n] = 2
box("PTable", (X, 0, 74), (90, 45, 2), M_WHITE, 0.6)
box("PFloor2", (X, 0, -1), (400, 400, 1), M_FLOOR, 0.2)
def can():
    r = empty("CNproto")
    lathe("CNb", [(0, 0), (2.6, 0), (3.3, 0.8), (3.3, 22.5), (2.8, 23.6), (2.7, 23.8), (0, 23.8)], M_ALU, 32, parent=r)
    wrap_label("CNl", 3.32, 0.9, 22.3, 0, 2 * math.pi, M_CAN, parent=r, seg=40)
    return r
cp = collection_of(can, "CanProto")
spots = [(-50, 10), (-35, -15), (-18, 12), (5, -8), (22, 16), (38, -12), (55, 6), (-62, -20), (70, -22), (12, 22)]
for i, (dx, dy) in enumerate(spots): inst(f"Can{i}", cp, (X + dx, dy, 76), (0, 0, random.uniform(0, 6)))
for i, (dx, dy) in enumerate([(-25, -28), (30, 28), (-75, 25), (60, -30)]):
    cu = lathe(f"Cup{i}", [(0, 0), (3, 0), (4.6, 11), (4.8, 11.3), (0, 11.3)], M_REDCUP, 24, loc=(X + dx, dy, 76))
fallen = inst("CanFallen", cp, (X - 5, -30, 79.3), (math.pi / 2, 0, 0.7))
for k in range(26):
    t = k / 25; bx = X - 220 + 440 * t; bz = 200 - 40 * math.sin(math.pi * t)
    lathe(f"Fairy{k}", [(0, 0), (1.5, 0), (1.5, 3), (0, 3)], simple(f"FL{k}", (1, 1, 1), emit=[(1.0, 0.7, 0.3), (1.0, 0.4, 0.6), (0.4, 0.7, 1.0)][k % 3], es=40), 8, loc=(bx, 220, bz))
L("PartyKey", (X + 120, -120, 160), 1.8e+05, (0.7, 0.5, 1.0), 20, n)
L("PartyRim", (X - 60, 150, 140), 2.4e+05, (1.0, 0.4, 0.6), 15, n)
PF2 = empty("PartyFocus", (X + 5, -8, 88))
cam(n, [(0, (X - 70, -110, 100), (X, 0, 86)), (1, (X + 40, -105, 96), (X, 0, 86))], lens=40, dof=PF2, fstop=2.0)

# ================================================================ L2 one can, macro with condensation
n = "L2_can"; X = SX(n); WORLD[n] = 2
box("CTable", (X, 0, 74), (90, 45, 2), noisy("RoughWood2", (0.05, 0.02, 0.01), (0.13, 0.06, 0.03), scale=0.25, rough=0.85, bump=0.05, stripes=(0.2, (0.04, 0.014, 0.007))), 0.6)
hc = can(); hc.location = (X, 0, 76); hc.rotation_euler.z = math.radians(-60)
dr = bpy.data.collections.new("DropProto")
db = bmesh.new(); bmesh.ops.create_uvsphere(db, u_segments=10, v_segments=6, radius=0.12)
dob = mesh_obj("DropP", db, [M_WATER]);
for cc in list(dob.users_collection): cc.objects.unlink(dob)
dr.objects.link(dob)
for k in range(900):
    a = random.uniform(-2.4, -0.4); z = random.uniform(1.5, 22)
    s = random.uniform(0.5, 1.6)
    inst(f"Dr{k}", dr, (X + 3.36 * math.cos(a), 3.36 * math.sin(a), 76 + z), (0, 0, 0), (s * 0.8, s * 0.8, s * 1.2))
L("CanKey", (X + 40, -50, 110), 7.2e+04, (1.0, 0.9, 0.85), 8, n)
L("CanRimA", (X - 30, 30, 100), 9.6e+04, (1.0, 0.35, 0.6), 4, n)
L("CanRimB", (X + 30, 35, 95), 7.2e+04, (0.3, 0.6, 1.0), 4, n)
CF = empty("CanFocus", (X + 1, -3.3, 88))
cam(n, [(0, (X + 40, -100, 102), (X, 0, 88)), (1, (X + 28, -80, 98), (X, 0, 88))], lens=50, dof=CF, fstop=2.0)

# ================================================================ soda bottle (generic, no brand)
def soda(name, lab, hero=False):
    r = empty(name)
    prof = [(0, 0), (3.2, 0), (3.6, 0.8), (3.6, 13), (3.4, 14), (3.6, 15), (3.6, 17), (2.4, 21), (1.4, 24), (1.3, 26), (0, 26)]
    g = lathe(name + "g", prof, M_PET, 32 if hero else 14, parent=r)
    lathe(name + "l", [(0, 0.3), (3.4, 0.3), (3.4, 18), (2.2, 21), (0, 21)], M_SODALIQ, 32 if hero else 12, parent=r)
    lathe(name + "c", [(0, 25.5), (1.5, 25.5), (1.5, 27.5), (0, 27.5)], M_SODA[lab], 16, parent=r)
    wrap_label(name + "w", 3.65, 8, 13, 0, 2 * math.pi, M_SODA[lab], parent=r, seg=32 if hero else 12)
    return r
sp = [collection_of(lambda c=c: soda(f"SDp{c}", c), f"SodaProto{c}") for c in range(4)]

# ================================================================ F1 fridge
n = "F1_fridge"; X = SX(n); WORLD[n] = 2
box("FrBack", (X, 64, 90), (40, 2, 90), M_FRIDGEIN, 0.5)
for s_ in (-1, 1): box(f"FrSide{s_}", (X + s_ * 39, 30, 90), (2, 35, 90), M_FRIDGEIN, 0.5)
box("FrTop", (X, 30, 179), (40, 35, 2), M_FRIDGEIN, 0.5)
box("FrBot", (X, 30, 2), (40, 35, 2), M_FRIDGEIN, 0.5)
box("FrOuter", (X, 30, 90), (44, 37, 92), simple("FridgeOut", (0.55, 0.56, 0.57), rough=0.3, metal=0.6), 1.5).hide_render = True
for k, z in enumerate((40, 80, 120)):
    box(f"FrSh{k}", (X, 30, z), (37, 32, 0.6), M_CLEAR, 0.2)
    for j in range(7): inst(f"FS{k}{j}", sp[(j + k) % 4], (X - 30 + j * 10, 12 + (j % 2) * 8, z + 0.6), (0, 0, random.uniform(0, 6)))
door = box("FrDoor", (X - 41, -5 - 36 * 0.42, 90), (2, 36, 88), M_FRIDGEIN, 1.5); door.rotation_euler.z = math.radians(-65); door.location = (X - 41 - 18, -5 - 30, 90)
area("FrLight", (X, 25, 172), (0, 0, 0), 6000, (0.9, 0.95, 1.0), 50, n)
L("FrSpill", (X, -60, 100), 7.2e+04, (0.8, 0.9, 1.0), 30, n)
box("FrKitchen", (X, 200, 150), (300, 3, 150), M_PLASTER, 0.3)
FF = empty("FridgeFocus", (X, 12, 85))
cam(n, [(0, (X + 30, -140, 115), (X, 30, 85)), (1, (X + 14, -90, 104), (X, 30, 85))], lens=32, dof=FF, fstop=3.0)

# ================================================================ F2 supermarket soda aisle
n = "F2_aisle"; X = SX(n); WORLD[n] = 3
box("AFloor", (X, 0, -1), (300, 1600, 1), M_TILE, 0.2)
for s in (-1, 1):
    for k in range(5):
        z = 15 + k * 38
        box(f"AShelf{s}{k}", (X + s * 110, 300, z), (30, 1300, 1), M_SHELFW, 0.3)
        for j in range(0, 170):
            yy = -900 + j * 15
            inst(f"AS{s}{k}{j}", sp[(j // 6 + k) % 4], (X + s * 110 + random.uniform(-3, 3), yy, z + 1), (0, 0, random.uniform(0, 6)), 1.15)
    box(f"ABack{s}", (X + s * 142, 300, 110), (2, 1300, 110), M_SHELFW, 0.3)
for k in range(9):
    lathe(f"ATube{k}", [(0, 0), (4, 0), (4, 140), (0, 140)], M_GLOWC, 12, loc=(X, -700 + k * 220, 290)).rotation_euler = (math.pi / 2, 0, 0)
    L(f"ATL{k}", (X, -630 + k * 220, 280), 3e+05, (0.95, 0.98, 1.0), 20, n)
fogbox("AFog", (X, 300, 150), (280, 1300, 150), 0.0008, (0.9, 0.92, 0.95)); FOGS.append((bpy.data.objects["AFog"], n))
cam(n, [(0, (X - 10, -1000, 120), (X, 600, 90)), (1, (X - 5, -760, 125), (X, 600, 90))], lens=30)

# ================================================================ F3 one soda and its sugar as cubes
n = "F3_cubes"; X = SX(n); WORLD[n] = 1
box("CubeTable", (X, 0, 74), (90, 50, 2), noisy("RoughWood", (0.05, 0.02, 0.01), (0.13, 0.06, 0.03), scale=0.25, rough=0.8, bump=0.05, stripes=(0.2, (0.04, 0.014, 0.007))), 0.8)
hs = soda("HeroSoda", 0, hero=True); hs.location = (X - 14, 4, 76)
cb = bmesh.new(); bmesh.ops.create_cube(cb, size=1.6)
cub = mesh_obj("CubeP", cb, [M_SUGAR], smooth_all=False); bv = cub.modifiers.new("b", 'BEVEL'); bv.width = 0.12; bv.segments = 2
cc_ = bpy.data.collections.new("CubeProto")
for c in list(cub.users_collection): c.objects.unlink(cub)
cc_.objects.link(cub)
k = 0
for lvl, (nx, ny) in enumerate([(4, 3), (3, 2), (2, 1), (1, 1)]):
    for i in range(nx):
        for j in range(ny):
            if k >= 16: break
            inst(f"Cube{k}", cc_, (X + 6 + (i - (nx - 1) / 2) * 1.7, 2 + (j - (ny - 1) / 2) * 1.7, 76.8 + lvl * 1.62), (0, 0, random.uniform(-0.08, 0.08))); k += 1
L("CubeKey", (X + 50, -60, 120), 1.32e+05, (1.0, 0.85, 0.7), 12, n)
L("CubeRim", (X - 40, 50, 100), 9e+04, (1.0, 0.7, 0.45), 6, n)
CBF = empty("CubeFocus", (X + 4, 0, 80))
cam(n, [(0, (X + 28, -70, 92), (X - 4, 0, 88)), (1, (X + 18, -56, 89), (X - 4, 0, 88))], lens=40, dof=CBF, fstop=3.0)
