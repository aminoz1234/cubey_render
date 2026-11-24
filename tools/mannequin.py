"""Sculptural mannequins from the MPFB man (no hair, clothes or eyes): matte 'stone' or glowing.
exec() in a session that opened scenes/real/man.blend; call strip_man() once, then mannequin(name, pose, mat, loc, rot_z)."""
import bpy, math
from mathutils import Vector, Matrix


def strip_man():
    for o in list(bpy.data.objects):
        if o.name.startswith("Man.") and o.name not in ("Man.body", "Man.high-poly"):
            bpy.data.objects.remove(o, do_unlink=True)
    body = bpy.data.objects["Man.body"]
    for m in list(body.modifiers):
        if m.type == "MASK" and m.name.startswith("Delete"):
            body.modifiers.remove(m)
    body.data.materials.clear()
    eyes = bpy.data.objects["Man.high-poly"]; eyes.data.materials.clear()
    return bpy.data.objects["Man"], body


def stone_mat(name="mq_stone", col=(0.09, 0.11, 0.16)):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; nz.inputs["Detail"].default_value = 12
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 140; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    mx = N.new("ShaderNodeMath"); mx.operation = "MULTIPLY"; L.new(nz.outputs["Fac"], mx.inputs[0]); L.new(vo.outputs["Distance"], mx.inputs[1])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.004
    L.new(mx.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (col[0] * 0.6, col[1] * 0.6, col[2] * 0.6, 1); cr.color_ramp.elements[1].color = (*col, 1)
    L.new(nz.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.75
    return m


def glow_mat(name="mq_glow", col=(0.12, 0.42, 1.0), strength=3.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    # brighter at the silhouette (fresnel), soft inner glow
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    mr = N.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = strength * 0.45; mr.inputs["To Max"].default_value = strength * 1.4
    L.new(lw.outputs["Facing"], mr.inputs["Value"])
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Emission Color"].default_value = (*col, 1)
    L.new(mr.outputs["Result"], b.inputs["Emission Strength"])
    b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Roughness"].default_value = 0.4
    return m


def _aim(rig, pb, name, direction):
    p = pb[name]; M = p.matrix.copy(); cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    p.matrix = Matrix.Translation(M.translation) @ q.to_matrix().to_4x4() @ Matrix.Translation(-M.translation) @ M
    bpy.context.view_layer.update()


# poses: bone -> direction in armature space (+z up, -y forward, +x = his left)
POSES = {
    "stand": {"upperarm01.L": (0.12, 0.05, -1), "upperarm01.R": (-0.12, 0.05, -1), "lowerarm01.L": (0.05, -0.1, -1), "lowerarm01.R": (-0.05, -0.1, -1)},
    "rifle": {"upperarm01.R": (-0.1, -0.25, -0.95), "lowerarm01.R": (0.25, -0.95, 0.15), "upperarm01.L": (0.15, -0.55, -0.8), "lowerarm01.L": (-0.45, -0.88, 0.15)},
    "point_gun": {"upperarm01.R": (-0.05, -1, 0.05), "lowerarm01.R": (-0.02, -1, 0.05), "upperarm01.L": (0.15, 0.05, -1), "lowerarm01.L": (0.05, -0.2, -1)},
    "sit": {"upperarm01.L": (0.15, -0.1, -1), "upperarm01.R": (-0.15, -0.1, -1), "lowerarm01.L": (0.0, -0.9, -0.3), "lowerarm01.R": (0.0, -0.9, -0.3),
            "upperleg01.L": (0.05, -1, 0.0), "upperleg01.R": (-0.05, -1, 0.0), "lowerleg01.L": (0.0, -0.1, -1), "lowerleg01.R": (0.0, -0.1, -1)},
    "swing": {"upperarm01.R": (-0.2, -0.5, 0.85), "lowerarm01.R": (0.1, -0.8, 0.6), "upperarm01.L": (0.2, -0.3, -0.9), "lowerarm01.L": (0.05, -0.5, -0.8)},
}


def mannequin(name, pose, m, loc, rot_z=0.0, scale=1.0, helmet=False, rifle=False):
    rig0 = bpy.data.objects["Man"]; body0 = bpy.data.objects["Man.body"]
    rig = rig0.copy(); rig.data = rig0.data.copy(); rig.animation_data_clear(); bpy.context.scene.collection.objects.link(rig)
    rig.name = name; rig.location = loc; rig.rotation_euler = (0, 0, math.radians(rot_z)); rig.scale = (scale,) * 3
    body = body0.copy(); body.data = body0.data.copy(); bpy.context.scene.collection.objects.link(body); body.name = name + "_body"
    body.parent = rig; body.matrix_parent_inverse = Matrix.Identity(4)
    for md in body.modifiers:
        if md.type == "ARMATURE":
            md.object = rig
    body.data.materials.clear(); body.data.materials.append(m)
    e0 = bpy.data.objects["Man.high-poly"]; eyes = e0.copy(); eyes.data = e0.data.copy(); bpy.context.scene.collection.objects.link(eyes)
    eyes.name = name + "_eyes"; eyes.parent = rig; eyes.matrix_parent_inverse = Matrix.Identity(4)
    for md in eyes.modifiers:
        if md.type == "ARMATURE":
            md.object = rig
    eyes.data.materials.clear(); eyes.data.materials.append(m)
    bpy.context.view_layer.update()
    pb = rig.pose.bones
    for p in pb:
        p.rotation_mode = "QUATERNION"; p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0)
    bpy.context.view_layer.update()
    for bone, d in POSES[pose].items():
        if bone in pb:
            _aim(rig, pb, bone, d)
    if pose == "sit":
        rig.location = (loc[0], loc[1], loc[2] - 0.45 * scale)
    if rifle:
        rifle_hold(rig, m)
    if helmet:
        import bmesh
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.125)
        for v in bm.verts:
            if v.co.z < -0.01:
                v.co.z = -0.01 + (v.co.z + 0.01) * 0.25
        me = bpy.data.meshes.new(name + "_helmet"); bm.to_mesh(me); bm.free(); me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = True
        h = bpy.data.objects.new(name + "_helmet", me); bpy.context.scene.collection.objects.link(h)
        h.parent = rig; h.parent_type = "BONE"; h.parent_bone = "head"
        hb = rig.data.bones["head"]; h.matrix_world = rig.matrix_world @ pb["head"].matrix @ Matrix.Translation((0, 0.12, 0.0))
    return rig, body


def walk(rig, f0, f1, period=18, swing=0.42, bob=0.03, key_z=True):
    """Key a simple walk cycle (legs + body bob) on a posed mannequin between frames f0 and f1."""
    sc = bpy.context.scene; pb = rig.pose.bones; base_z = rig.location.z
    legs = ("upperleg01.L", "lowerleg01.L", "upperleg01.R", "lowerleg01.R")
    for f in range(f0, f1 + 1, 2):
        ph = (f - f0) / period * 2 * math.pi
        for side, sgn in (("L", 1), ("R", -1)):
            a = swing * math.sin(ph) * sgn
            up, lo = pb["upperleg01." + side], pb["lowerleg01." + side]
            for b in (up, lo):
                b.rotation_quaternion = (1, 0, 0, 0)
            bpy.context.view_layer.update()
            _aim(rig, pb, up.name, (0.0, -math.sin(a), -math.cos(a)))
            bpy.context.view_layer.update()
            knee = max(0.0, -math.cos(ph + (0 if sgn > 0 else math.pi))) * 0.7      # bend while the leg swings through
            _aim(rig, pb, lo.name, (0.0, -math.sin(a) + knee, -math.cos(a)))
            bpy.context.view_layer.update()
        for n in legs:
            pb[n].keyframe_insert("rotation_quaternion", frame=f)
        if key_z:
            rig.location.z = base_z + bob * abs(math.sin(ph)); rig.keyframe_insert("location", index=2, frame=f)
    for n in legs:   # stand still after the walk
        pb[n].rotation_quaternion = (1, 0, 0, 0); pb[n].keyframe_insert("rotation_quaternion", frame=f1 + 6)
    if key_z:
        rig.location.z = base_z; rig.keyframe_insert("location", index=2, frame=f1 + 6)


# ---------------------------------------------------------------- props held in the hands
def _parts_mesh(name, parts, m):
    """parts: [(kind, centre, half_or_(r, depth), axis)] in object space -> one mesh."""
    import bmesh
    bm = bmesh.new()
    for kind, c, dims in parts:
        if kind == "box":
            g = bmesh.ops.create_cube(bm, size=1.0)
            for v in g["verts"]:
                v.co = Vector((v.co.x * dims[0] * 2 + c[0], v.co.y * dims[1] * 2 + c[1], v.co.z * dims[2] * 2 + c[2]))
        else:   # cylinder along y
            g = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=dims[0], radius2=dims[0], depth=dims[1])
            for v in g["verts"]:
                v.co = Vector((v.co.x + c[0], v.co.z + c[1], v.co.y + c[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.modifiers.new("bev", "BEVEL").width = 0.004
    return o


def _empty(name, parent, loc):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.parent = parent; e.location = loc; e.empty_display_size = 0.03
    return e


def rifle_hold(rig, m):
    """A carbine at low ready, stock in the right shoulder, both hands locked on it with IK."""
    name = rig.name
    # rifle object space: butt at origin, muzzle toward -y
    parts = [("box", (0, -0.07, -0.01), (0.022, 0.07, 0.05)),          # stock
             ("box", (0, -0.3, 0.0), (0.024, 0.16, 0.04)),             # receiver
             ("box", (0, -0.3, -0.085), (0.016, 0.022, 0.06)),         # magazine
             ("box", (0, -0.21, -0.075), (0.014, 0.018, 0.05)),        # pistol grip
             ("box", (0, -0.56, 0.0), (0.026, 0.11, 0.032)),           # handguard
             ("cyl", (0, -0.78, 0.0), (0.009, 0.2)),                   # barrel
             ("box", (0, -0.3, 0.055), (0.012, 0.05, 0.016))]          # optic
    r = _parts_mesh(name + "_rifle", parts, m)
    d = Vector((0.08, -1.0, -0.42)).normalized()                       # low ready: muzzle forward and down
    rot = Vector((0, -1, 0)).rotation_difference(d).to_matrix().to_4x4()
    r.parent = rig; r.matrix_parent_inverse = Matrix.Identity(4)
    r.matrix_basis = Matrix.Translation(Vector((-0.11, -0.06, 1.33))) @ rot
    tgt_r = _empty(name + "_gripR", r, (0.0, -0.2, -0.07)); tgt_l = _empty(name + "_gripL", r, (0.0, -0.55, -0.035))
    pole_r = _empty(name + "_poleR", rig, (-0.55, 0.25, 0.95)); pole_l = _empty(name + "_poleL", rig, (0.45, -0.25, 0.85))
    for side, tgt, pole in (("R", tgt_r, pole_r), ("L", tgt_l, pole_l)):
        pb = rig.pose.bones["lowerarm02." + side]
        c = pb.constraints.new("IK"); c.target = tgt; c.chain_count = 4; c.pole_target = pole; c.pole_angle = math.radians(-90)
    return r


def pistol_in_hand(rig, m):
    pb = rig.pose.bones; bpy.context.view_layer.update()
    w = pb["wrist.R"]; fwd = (w.tail - pb["lowerarm02.R"].head).normalized()
    parts = [("box", (0, -0.06, 0.0), (0.016, 0.09, 0.026)), ("box", (0, -0.0, -0.055), (0.014, 0.022, 0.05))]
    g = _parts_mesh(rig.name + "_pistol", parts, m)
    g.parent = rig; g.matrix_parent_inverse = Matrix.Identity(4)
    g.matrix_basis = Matrix.Translation(w.tail + fwd * 0.03) @ Vector((0, -1, 0)).rotation_difference(fwd).to_matrix().to_4x4()
    return g


def knife_in_hand(rig, m):
    pb = rig.pose.bones; bpy.context.view_layer.update()
    w = pb["wrist.R"]; fwd = (w.tail - pb["lowerarm02.R"].head).normalized()
    parts = [("box", (0, -0.05, 0.0), (0.016, 0.06, 0.02)), ("box", (0, -0.25, 0.0), (0.007, 0.15, 0.032))]
    k = _parts_mesh(rig.name + "_knife", parts, m)
    k.parent = rig; k.matrix_parent_inverse = Matrix.Identity(4)
    k.matrix_basis = Matrix.Translation(w.tail) @ Vector((0, -1, 0)).rotation_difference(fwd).to_matrix().to_4x4()
    return k


# ---------------------------------------------------------------- moving along a route (upright, heading only)
def route_points(curve_obj, step=0.04):
    dg = bpy.context.evaluated_depsgraph_get(); ev = curve_obj.evaluated_get(dg); me = ev.to_mesh()
    pts = [curve_obj.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    return pts, L


def _at(pts, L, s):
    s = max(0.0, min(L[-1], s))
    for i in range(1, len(L)):
        if L[i] >= s:
            t = (s - L[i - 1]) / max(1e-9, L[i] - L[i - 1]); return pts[i - 1].lerp(pts[i], t)
    return pts[-1]


def move_along(rig, curve_obj, keys, bob=0.025, period=18):
    """keys: [(frame, fraction 0..1)] - keyed every 2 frames, eased between keys; body upright, turns toward travel."""
    pts, L = route_points(curve_obj); last = None
    fr = list(range(keys[0][0], keys[-1][0] + 1, 2))
    for f in fr:
        for (fa, sa), (fb, sb) in zip(keys, keys[1:]):
            if fa <= f <= fb:
                t = (f - fa) / max(1, fb - fa); t = t * t * (3 - 2 * t); frac = sa + (sb - sa) * t; moving = sb != sa; break
        s = frac * L[-1]; p = _at(pts, L, s)
        a = _at(pts, L, s - 0.2); b = _at(pts, L, s + 0.2); dvec = (b - a); dvec.z = 0
        ang = math.atan2(dvec.x, -dvec.y) if dvec.length > 1e-4 else (last if last is not None else 0.0)
        if last is not None:
            while ang - last > math.pi: ang -= 2 * math.pi
            while ang - last < -math.pi: ang += 2 * math.pi
        last = ang
        ph = (f - keys[0][0]) / period * 2 * math.pi
        rig.location = (p.x, p.y, p.z + (bob * abs(math.sin(ph)) if moving else 0.0)); rig.keyframe_insert("location", frame=f)
        rig.rotation_euler = (0, 0, ang); rig.keyframe_insert("rotation_euler", frame=f)
