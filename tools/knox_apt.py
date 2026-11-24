"""Knoxville unit, detailed mono-blue reconstruction from the released bodycam (approximate layout).
exec() after common_build.py and mannequin.py. apt_set() builds it at the origin and returns key points.
Unit: metres, y = north. Floor of the unit at z=0; the curved stair rises from z=-2.8 on the west side."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

H = 2.25          # cut height of the walls
DOOR_H = 2.03


def mono_mat(name, v, rough=0.6, emit=0.0, bump=0.0, planks=False, base=(0.05, 0.07, 0.115)):
    m = bpy.data.materials.get(name)
    if m:
        return m
    col = tuple(c * v for c in base)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    tc = N.new("ShaderNodeTexCoord")
    if planks:   # laminate planks: brick texture gives board seams and per-board tone
        br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = 1.2; br.inputs["Row Height"].default_value = 0.18; br.inputs["Mortar Size"].default_value = 0.006
        br.inputs["Color1"].default_value = (*[c * 1.15 for c in col], 1); br.inputs["Color2"].default_value = (*[c * 0.85 for c in col], 1)
        br.inputs["Mortar"].default_value = (*[c * 0.4 for c in col], 1)
        L.new(tc.outputs["Object"], br.inputs["Vector"]); L.new(br.outputs["Color"], b.inputs["Base Color"])
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Roughness"].default_value = 0.35
    elif bump:
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40; nz.inputs["Detail"].default_value = 10
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


M = {}


def import_model(mid, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "assets", "models", mid, mid + "_1k.gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    root = link(bpy.data.objects.new(mid + "_root", None))
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot_z)); root.scale = (scale,) * 3
    return root, None


def mats():
    M["floor"] = mono_mat("apt_floor", 1.25, planks=True)
    M["base"] = mono_mat("apt_ground", 0.45, rough=0.9)
    M["wall"] = mono_mat("apt_wall", 1.9, rough=0.8)
    M["edge"] = mono_mat("apt_edge", 1.0, emit=1.0, base=(0.32, 0.55, 1.0))
    M["furn"] = mono_mat("apt_furn", 1.4, rough=0.7, bump=0.2)
    M["dark"] = mono_mat("apt_dark", 0.6, rough=0.4)
    M["fabric"] = mono_mat("apt_fabric", 1.7, rough=0.95, bump=0.5)
    M["cloth"] = mono_mat("apt_bluecloth", 1.0, rough=0.95, bump=0.4, base=(0.04, 0.08, 0.22))
    M["glass"] = mono_mat("apt_glass", 1.0, emit=0.25, base=(0.25, 0.4, 0.7))
    M["rail"] = mono_mat("apt_rail", 0.5, rough=0.3)
    M["light"] = mono_mat("apt_lamp", 1.0, emit=4.0, base=(0.5, 0.7, 1.0))


def _obj(name, me, m):
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def cuboid(name, center, half, m, rot_z=0.0, bevel=0.0):
    o = box(name, center, half, m, bevel=bevel); o.rotation_euler = (0, 0, rot_z)
    return o


def wall_run(name, a, b, openings=(), h=H, t=0.1, cap=True):
    """Straight wall from a to b (2D). openings: (s0, s1, z0, z1) measured along the wall from a."""
    a = Vector((a[0], a[1], 0)); b = Vector((b[0], b[1], 0)); d = b - a; ln = d.length; u = d / ln; ang = math.atan2(d.y, d.x)
    cuts = sorted({0.0, ln, *[s for o in openings for s in o[:2]]})
    k = 0
    for s0, s1 in zip(cuts, cuts[1:]):
        mid_s = (s0 + s1) / 2
        hole = [o for o in openings if o[0] <= mid_s <= o[1]]
        spans = [(0, h)] if not hole else [(0, hole[0][2]), (hole[0][3], h)]
        for z0, z1 in spans:
            if z1 - z0 < 0.01:
                continue
            c = a + u * mid_s
            cuboid(f"{name}_{k}", (c.x, c.y, (z0 + z1) / 2), ((s1 - s0) / 2 + (t / 2 if s0 == 0 or s1 == ln else 0), t / 2, (z1 - z0) / 2), M["wall"], rot_z=ang)
            k += 1
        if cap and (not hole or hole[0][3] < h):
            c = a + u * mid_s
            cuboid(f"{name}_cap{k}", (c.x, c.y, h + 0.006), ((s1 - s0) / 2 + 0.05, t / 2 + 0.004, 0.006), M["edge"], rot_z=ang)
    return ang


def window(name, a, b, s0, s1, z0, z1, blinds=True):
    """Glass + blind slats inside a wall opening."""
    a = Vector((a[0], a[1], 0)); b = Vector((b[0], b[1], 0)); u = (b - a).normalized(); ang = math.atan2(u.y, u.x)
    c = a + u * ((s0 + s1) / 2)
    cuboid(name + "_glass", (c.x, c.y, (z0 + z1) / 2), ((s1 - s0) / 2, 0.01, (z1 - z0) / 2), M["glass"], rot_z=ang)
    if blinds:
        n = int((z1 - z0) / 0.06)
        for i in range(n):
            cuboid(f"{name}_slat{i}", (c.x, c.y, z0 + 0.03 + i * 0.06), ((s1 - s0) / 2 - 0.02, 0.025, 0.004), M["furn"], rot_z=ang)


def door(name, hinge, width, open_deg, wall_ang, swing=1):
    """Door slab hinged at `hinge` (2D), closed along wall_ang, opened by open_deg."""
    piv = link(bpy.data.objects.new(name, None)); piv.location = (hinge[0], hinge[1], 0)
    piv.rotation_euler = (0, 0, wall_ang + math.radians(open_deg) * swing)
    s = cuboid(name + "_slab", (width / 2, 0, DOOR_H / 2), (width / 2 - 0.01, 0.02, DOOR_H / 2 - 0.005), M["furn"])
    s.parent = piv
    for i, (z0, z1) in enumerate(((0.15, 0.9), (1.1, 1.9))):   # raised panels
        p = cuboid(f"{name}_p{i}", (width / 2, 0, (z0 + z1) / 2), (width / 2 - 0.1, 0.028, (z1 - z0) / 2), M["wall"]); p.parent = piv
    k = cuboid(name + "_knob", (width - 0.07, 0, 0.95), (0.025, 0.06, 0.025), M["rail"]); k.parent = piv
    return piv


def blob(name, loc, size, m, seed=0, flat=0.35):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = _obj(name, me, m); o.location = loc; o.scale = (size[0], size[1], size[2] * flat)
    tx = bpy.data.textures.new(name + "_t", "CLOUDS"); tx.noise_scale = 0.45; tx.noise_basis = "ORIGINAL_PERLIN"
    md = o.modifiers.new("d", "DISPLACE"); md.texture = tx; md.strength = 0.55; md.texture_coords = "LOCAL"
    o.rotation_euler = (0, 0, random.Random(seed).uniform(0, 6.28))
    return o


def rumpled(name, center, half, z, m, strength=0.06, seed=0):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40, size=1.0)
    o = bpy.context.active_object; o.name = name; o.location = (center[0], center[1], z); o.scale = (half[0] * 2, half[1] * 2, 1)
    o.data.materials.append(m)
    tx = bpy.data.textures.new(name + "_t", "CLOUDS"); tx.noise_scale = 0.18
    md = o.modifiers.new("d", "DISPLACE"); md.texture = tx; md.strength = strength
    o.modifiers.new("s", "SUBSURF").levels = 1
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def spiral_stair(c, r_in, r_out, a0, a1, z0, z1, n):
    """Curved stair around centre c from angle a0 to a1 (deg), with inner handrail and balusters."""
    rise = (z1 - z0) / n; pts = []
    for i in range(n):
        t0 = math.radians(a0 + (a1 - a0) * i / n); t1 = math.radians(a0 + (a1 - a0) * (i + 1) / n)
        zt = z0 + rise * (i + 1)
        bm = bmesh.new(); vs = []
        for r, t in ((r_in, t0), (r_out, t0), (r_out, t1), (r_in, t1)):
            for z in (zt - 0.18, zt):
                vs.append(bm.verts.new((c[0] + r * math.cos(t), c[1] + r * math.sin(t), z)))
        bmesh.ops.convex_hull(bm, input=vs)
        me = bpy.data.meshes.new(f"stair{i}"); bm.to_mesh(me); bm.free(); _obj(f"apt_step{i}", me, M["furn"])
        tm = (t0 + t1) / 2; pts.append((c[0] + (r_in + r_out) / 2 * math.cos(tm), c[1] + (r_in + r_out) / 2 * math.sin(tm), zt))
        for j in range(2):   # balusters
            t = t0 + (t1 - t0) * (0.25 + 0.5 * j); rr = r_in + 0.05
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.011, depth=0.92, location=(c[0] + rr * math.cos(t), c[1] + rr * math.sin(t), zt + 0.46))
            bpy.context.active_object.data.materials.append(M["rail"]); bpy.context.active_object.name = f"apt_bal{i}_{j}"
    # handrail
    cu = bpy.data.curves.new("apt_handrail", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.028; cu.bevel_resolution = 3
    sp = cu.splines.new("NURBS"); m_ = 4 * n; sp.points.add(m_); sp.order_u = 3; sp.use_endpoint_u = True
    for k, p in enumerate(sp.points):
        f = k / m_; t = math.radians(a0 + (a1 - a0) * f); rr = r_in + 0.05
        p.co = (c[0] + rr * math.cos(t), c[1] + rr * math.sin(t), z0 + (z1 - z0) * f + 0.92, 1)
    cu.materials.append(M["rail"]); link(bpy.data.objects.new("apt_handrail", cu))
    return pts


def ceiling_fan(name, loc):
    hub = cuboid(name + "_hub", loc, (0.09, 0.09, 0.05), M["dark"], bevel=0.03)
    for k in range(5):
        a = k / 5 * 2 * math.pi
        cuboid(f"{name}_b{k}", (loc[0] + 0.38 * math.cos(a), loc[1] + 0.38 * math.sin(a), loc[2]), (0.3, 0.06, 0.008), M["dark"], rot_z=a)


def apt_set():
    mats(); rr = random.Random(7); P = {}
    # ground slab, floors
    cuboid("apt_ground", (5.0, 1.5, -2.86), (10, 6, 0.05), M["base"])
    cuboid("apt_floor_liv", (2.75, 1.9, -0.03), (2.75, 2.0, 0.03), M["floor"])
    cuboid("apt_floor_hall", (7.55, 2.0, -0.03), (2.05, 0.6, 0.03), M["floor"])
    cuboid("apt_floor_closet", (7.55, 0.65, -0.03), (2.05, 0.75, 0.03), M["floor"])
    cuboid("apt_floor_bed", (11.1, 1.95, -0.03), (1.5, 1.65, 0.03), M["floor"])
    cuboid("apt_floor_well", (-1.45, 1.5, -2.83), (1.45, 1.6, 0.03), M["floor"])
    # ---- stairwell (west): curved stair wrapping the well, tall window ----
    P["stair_pts"] = spiral_stair((-1.45, 1.5), 0.55, 1.35, 215, 0, -2.8, 0.0, 15)
    for nm, a, b, op in (("sw_w", (-2.9, -0.1), (-2.9, 3.1), [(0.9, 2.3, -2.1, -0.2)]),
                         ("sw_s", (-2.9, -0.1), (0.0, -0.1), []), ("sw_n", (-2.9, 3.1), (0.0, 3.1), [])):
        # stairwell walls run from the lower floor up to the cut height
        a3 = Vector((a[0], a[1], 0)); b3 = Vector((b[0], b[1], 0)); d = b3 - a3; ln = d.length; ang = math.atan2(d.y, d.x)
        cuts = sorted({0.0, ln, *[s for o in op for s in o[:2]]}); k = 0
        for s0, s1 in zip(cuts, cuts[1:]):
            ms = (s0 + s1) / 2; hole = [o for o in op if o[0] <= ms <= o[1]]
            spans = [(-2.8, 0.3)] if not hole else [(-2.8, hole[0][2]), (hole[0][3], 0.3)]
            for z0, z1 in spans:
                cc = a3 + d / ln * ms
                cuboid(f"apt_{nm}{k}", (cc.x, cc.y, (z0 + z1) / 2), ((s1 - s0) / 2 + 0.05, 0.05, (z1 - z0) / 2), M["wall"], rot_z=ang); k += 1
            cc = a3 + d / ln * ms
            cuboid(f"apt_{nm}cap{k}", (cc.x, cc.y, 0.306), ((s1 - s0) / 2 + 0.05, 0.054, 0.006), M["edge"], rot_z=ang)
        if op:
            window("apt_stairwin", a, b, op[0][0], op[0][1], op[0][2], op[0][3], blinds=False)
    # ---- unit walls ----
    # west wall of the unit: open to the top of the stairs between y=1.0 and 2.2
    wall_run("apt_w_w", (0, -0.1), (0, 3.9), [(1.1, 2.3, 0, DOOR_H)])
    wall_run("apt_w_s", (0, -0.1), (9.6, -0.1), [(2.4, 3.6, 0.9, 2.0)])
    wall_run("apt_w_n", (0, 3.9), (5.5, 3.9), [(2.3, 3.9, 0.95, 2.0)])
    window("apt_livwin", (0, 3.9), (5.5, 3.9), 2.3, 3.9, 0.95, 2.0)
    window("apt_livwin2", (0, -0.1), (9.6, -0.1), 2.4, 3.6, 0.9, 2.0)
    # living room east wall with the opening into the hallway (y 1.4-2.6)
    wall_run("apt_w_le", (5.5, -0.1), (5.5, 3.9), [(1.5, 2.7, 0, DOOR_H)])
    # hallway: north side has a side room (door ajar on the left), south side a closet wall with a picture
    wall_run("apt_h_n", (5.5, 2.6), (9.6, 2.6), [(1.0, 1.85, 0, DOOR_H)])
    wall_run("apt_h_s", (5.5, 1.4), (9.6, 1.4), [])
    wall_run("apt_side_n", (5.5, 4.4), (9.6, 4.4), [(1.2, 2.2, 0.95, 1.9)])
    window("apt_sidewin", (5.5, 4.4), (9.6, 4.4), 1.2, 2.2, 0.95, 1.9)
    wall_run("apt_side_w", (5.5, 3.9), (5.5, 4.4), [])
    cuboid("apt_floor_side", (7.55, 3.5, -0.03), (2.05, 0.9, 0.03), M["floor"])
    # bedroom at the end of the hallway (door in its west wall, y 1.55-2.45)
    wall_run("apt_b_w", (9.6, 0.3), (9.6, 4.4), [(1.25, 2.15, 0, DOOR_H)])
    wall_run("apt_b_s", (9.6, 0.3), (12.6, 0.3), [(0.9, 2.0, 0.85, 1.95)])
    window("apt_bedwin", (9.6, 0.3), (12.6, 0.3), 0.9, 2.0, 0.85, 1.95)
    wall_run("apt_b_e", (12.6, 0.3), (12.6, 4.4), [])
    wall_run("apt_b_n", (9.6, 3.6), (12.6, 3.6), [])
    wall_run("apt_e_close", (9.6, -0.1), (9.6, 0.3), [])
    # ---- doors ----
    door("apt_door_side", (6.5, 2.6), 0.82, 70, 0.0, swing=1)
    P["bed_door_piv"] = door("apt_door_bed", (9.6, 1.55), 0.88, 100, math.pi / 2, swing=-1)
    for i in range(4):   # clothes hanging on the back of the bedroom door
        c = blob(f"apt_doorclothes{i}", (0, 0, 0), (0.18, 0.06, 1.2), M["fabric"], seed=i, flat=0.45)
        c.parent = P["bed_door_piv"]; c.location = (0.25 + i * 0.13, 0.08, 1.45); c.scale = (0.12, 0.05, 0.28)
    # ---- living room ----
    sofa, _ = import_model("sofa_02", Vector((2.9, 3.35, 0)), rot_z=180, scale=1.05)
    sofa.name = "apt_sofa"
    for o in sofa.children_recursive:
        if o.type == "MESH":
            o.data.materials.clear(); o.data.materials.append(M["fabric"])
    cuboid("apt_box", (3.3, 2.0, 0.09), (0.18, 0.13, 0.09), M["furn"])
    cuboid("apt_tvstand", (3.0, 0.15, 0.25), (0.8, 0.2, 0.25), M["furn"], bevel=0.02)
    cuboid("apt_tv", (3.0, 0.12, 0.85), (0.6, 0.03, 0.35), M["dark"])
    ceiling_fan("apt_fan", (2.9, 1.9, 2.1))
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.09, depth=1.05, location=(0.45, 0.25, 0.52))
    bpy.context.active_object.data.materials.append(M["dark"]); bpy.context.active_object.name = "apt_vacuum"

    # ---- hallway ----
    cuboid("apt_picture", (8.0, 1.46, 1.45), (0.35, 0.015, 0.25), M["glass"])
    cuboid("apt_picframe", (8.0, 1.455, 1.45), (0.39, 0.012, 0.29), M["dark"])
    # side room: a bed frame + clutter (not entered)
    cuboid("apt_side_bed", (8.4, 3.6, 0.25), (0.95, 0.7, 0.25), M["fabric"], bevel=0.05)
    # ---- bedroom ----
    cuboid("apt_bluecloth", (12.53, 1.95, 1.15), (0.02, 1.6, 1.1), M["cloth"])
    cuboid("apt_mattress", (11.75, 1.25, 0.11), (0.7, 0.95, 0.11), M["fabric"], bevel=0.05)
    rumpled("apt_sheet", (11.7, 1.3), (0.72, 0.95), 0.23, M["wall"], strength=0.09)
    rumpled("apt_redblanket", (11.55, 1.8), (0.45, 0.4), 0.27, mono_mat("apt_blanket", 2.6, rough=0.9), strength=0.08)
    cuboid("apt_tv_floor", (10.2, 0.6, 0.38), (0.45, 0.04, 0.3), M["dark"], rot_z=math.radians(-25))
    cuboid("apt_trunk", (10.25, 3.15, 0.22), (0.45, 0.28, 0.22), M["dark"], bevel=0.03)
    cuboid("apt_shelf", (12.25, 3.3, 0.55), (0.3, 0.22, 0.55), M["furn"], bevel=0.02)
    for i in range(16):   # clothes piles and bags across the floor
        x = rr.uniform(9.9, 12.3); y = rr.uniform(0.5, 3.4)
        if 11.0 < x < 12.5 and 0.3 < y < 2.2:
            continue
        blob(f"apt_clutter{i}", (x, y, 0.06), (rr.uniform(0.15, 0.35), rr.uniform(0.12, 0.3), 0.25), M["fabric"] if i % 3 else M["furn"], seed=i)
    P["mel"] = Vector((10.95, 2.55, 0)); P["girl"] = Vector((11.8, 1.35, 0.23)); P["bed_door"] = Vector((9.6, 2.0, 0))
    P["route"] = [p for p in P["stair_pts"]] + [(0.35, 1.7, 0), (1.6, 1.8, 0), (3.3, 1.5, 0), (4.8, 1.9, 0), (6.0, 2.0, 0), (7.6, 2.0, 0), (9.2, 2.0, 0)]
    return P
