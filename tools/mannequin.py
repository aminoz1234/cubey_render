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
        import bmesh
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.05, v.co.y * 0.85, v.co.z * 0.09))
        me = bpy.data.meshes.new(name + "_rifle"); bm.to_mesh(me); bm.free(); me.materials.append(m)
        r = bpy.data.objects.new(name + "_rifle", me); bpy.context.scene.collection.objects.link(r)
        hand = rig.matrix_world @ pb["wrist.R"].head if "wrist.R" in pb else rig.matrix_world @ pb["lowerarm01.R"].tail
        r.parent = rig; r.matrix_parent_inverse = rig.matrix_world.inverted()
        r.matrix_world = Matrix.Translation(hand + rig.matrix_world.to_3x3() @ Vector((0.18, -0.15, 0.05))) @ rig.matrix_world.to_3x3().to_4x4()
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


def walk(rig, f0, f1, period=18, swing=0.42, bob=0.03):
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
        rig.location.z = base_z + bob * abs(math.sin(ph)); rig.keyframe_insert("location", index=2, frame=f)
    for n in legs:   # stand still after the walk
        pb[n].rotation_quaternion = (1, 0, 0, 0); pb[n].keyframe_insert("rotation_quaternion", frame=f1 + 6)
    rig.location.z = base_z; rig.keyframe_insert("location", index=2, frame=f1 + 6)
