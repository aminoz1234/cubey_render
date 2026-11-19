"""Realistic-ish tabby cat for Blender 5.2+ Cycles: Poly Haven concrete_cat_statue (CC0) as the body,
particle-hair fur with tabby stripes, glossy eyes with slit pupils, whiskers. exec() this file, then cat(ROOT, ...).
Returns the root empty (cat sits on its origin, faces -Y, ~0.40 m tall)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix


def _fur_mat(name="cat_fur", base=(0.36, 0.2, 0.09), dark=(0.035, 0.025, 0.018), belly=(0.75, 0.68, 0.58)):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    N.remove(N["Principled BSDF"])
    hb = N.new("ShaderNodeBsdfHairPrincipled"); hb.parametrization = "COLOR"
    hb.inputs["Roughness"].default_value = 0.35; hb.inputs["Radial Roughness"].default_value = 0.5
    hb.inputs["Coat"].default_value = 0.2
    tc = N.new("ShaderNodeTexCoord")
    # tabby: distorted stripes running around the body (along z) + darker back, pale belly/chin
    wv = N.new("ShaderNodeTexWave"); wv.bands_direction = "Z"; wv.inputs["Scale"].default_value = 38
    wv.inputs["Distortion"].default_value = 14; wv.inputs["Detail"].default_value = 3; wv.inputs["Detail Scale"].default_value = 2
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    st = N.new("ShaderNodeValToRGB"); st.color_ramp.elements[0].position = 0.35; st.color_ramp.elements[0].color = (*dark, 1)
    st.color_ramp.elements[1].position = 0.6; st.color_ramp.elements[1].color = (*base, 1)
    L.new(wv.outputs["Fac"], st.inputs[0])
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    bm_ = N.new("ShaderNodeMapRange"); bm_.inputs["From Min"].default_value = -0.065; bm_.inputs["From Max"].default_value = -0.09
    L.new(sp.outputs["Y"], bm_.inputs["Value"])                       # front of chest / chin pale
    zr = N.new("ShaderNodeMapRange"); zr.inputs["From Min"].default_value = 0.215; zr.inputs["From Max"].default_value = 0.19
    L.new(sp.outputs["Z"], zr.inputs["Value"])
    mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; L.new(bm_.outputs["Result"], mm.inputs[0]); L.new(zr.outputs["Result"], mm.inputs[1])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(mm.outputs[0], mx.inputs["Factor"])
    L.new(st.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (*belly, 1)
    # strand tips lighter (agouti)
    hi = N.new("ShaderNodeHairInfo")
    tip = N.new("ShaderNodeMix"); tip.data_type = "RGBA"; tip.blend_type = "SCREEN"
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3.0
    L.new(hi.outputs["Intercept"], pw.inputs[0]); mf = N.new("ShaderNodeMath"); mf.operation = "MULTIPLY"; mf.inputs[1].default_value = 0.2
    L.new(pw.outputs[0], mf.inputs[0]); L.new(mf.outputs[0], tip.inputs["Factor"])
    L.new(mx.outputs["Result"], tip.inputs["A"]); tip.inputs["B"].default_value = (0.8, 0.65, 0.45, 1)
    L.new(tip.outputs["Result"], hb.inputs["Color"])
    L.new(hb.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def _skin_mat(name="cat_skin"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.12, 0.08, 0.05, 1); b.inputs["Roughness"].default_value = 0.7
    return m


def _eye_mat(name="cat_eye", iris=(0.55, 0.45, 0.05)):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    # slit pupil: |x| small, along z; iris radial fibres
    ax = N.new("ShaderNodeMath"); ax.operation = "ABSOLUTE"; L.new(sp.outputs["X"], ax.inputs[0])
    sl = N.new("ShaderNodeMath"); sl.operation = "LESS_THAN"; sl.inputs[1].default_value = 0.13; L.new(ax.outputs[0], sl.inputs[0])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 3; wv.inputs["Distortion"].default_value = 12
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    ir = N.new("ShaderNodeValToRGB"); ir.color_ramp.elements[0].color = (iris[0] * 0.4, iris[1] * 0.4, iris[2] * 0.4, 1)
    ir.color_ramp.elements[1].color = (*iris, 1); L.new(wv.outputs["Fac"], ir.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(sl.outputs[0], mx.inputs["Factor"])
    L.new(ir.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (0.005, 0.004, 0.003, 1)
    L.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.0; b.inputs["Coat IOR"].default_value = 1.38
    b.inputs["Subsurface Weight"].default_value = 0.2; b.inputs["Subsurface Scale"].default_value = 0.002
    return m


EYES = [Vector((-0.0155, -0.0835, 0.2225)), Vector((0.0255, -0.0855, 0.2225))]


def cat(ROOT, scale=1.4, hairs=14000, children=12, fur_len=0.0065, name="cat"):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "assets", "models", "concrete_cat_statue", "concrete_cat_statue_1k.gltf"))
    body = [o for o in bpy.data.objects if o not in before and o.type == "MESH"][0]
    for o in bpy.data.objects:
        if o not in before and o is not body:
            bpy.data.objects.remove(o)
    body.name = name + "_body"; body.parent = None
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    body.parent = root; root.scale = (scale,) * 3
    me = body.data
    me.materials.clear(); me.materials.append(_skin_mat()); me.materials.append(_fur_mat())
    for p in me.polygons:
        p.use_smooth = True
    # fur
    mod = body.modifiers.new("fur", "PARTICLE_SYSTEM"); ps = mod.particle_system; st = ps.settings
    st.type = "HAIR"; st.count = hairs; st.hair_length = fur_len; st.material = 2
    st.emit_from = "FACE"; st.use_emit_random = True
    st.effector_weights.gravity = 0.0
    st.child_type = "INTERPOLATED"; st.child_percent = 4; st.rendered_child_count = children
    st.child_length = 0.85; st.child_length_threshold = 0.3
    st.clump_factor = 0.3; st.roughness_1 = 0.001; st.roughness_endpoint = 0.0012; st.kink = "NO"
    st.hair_step = 5; st.display_step = 3; st.render_step = 4
    st.root_radius = 0.6; st.tip_radius = 0.0; st.radius_scale = 0.0006
    st.use_hair_bspline = True
    # eyes
    for k, c in enumerate(EYES):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
        em = bpy.data.meshes.new(f"{name}_eye{k}"); bm.to_mesh(em); bm.free(); em.materials.append(_eye_mat())
        for p in em.polygons:
            p.use_smooth = True
        e = bpy.data.objects.new(f"{name}_eye{k}", em); bpy.context.scene.collection.objects.link(e)
        e.parent = root; e.location = c; e.scale = (0.0092, 0.0092, 0.0092)
        e.rotation_euler = (math.radians(90), 0, math.radians(8 if k else -8))   # object z -> looking forward (-y)
    # whiskers
    wm = bpy.data.materials.new(name + "_whisker"); wm.use_nodes = True; wb = wm.node_tree.nodes["Principled BSDF"]
    wb.inputs["Base Color"].default_value = (0.9, 0.88, 0.85, 1); wb.inputs["Roughness"].default_value = 0.3
    rnd = random.Random(3)
    for s in (-1, 1):
        for k in range(8):
            cu = bpy.data.curves.new(f"{name}_wh{s}{k}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.00035
            sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
            b0 = Vector((0.005 + s * 0.012, -0.1, 0.196 + 0.003 * (k % 4) - 0.004))
            d = Vector((s * 1.0, -0.25 + rnd.uniform(-0.1, 0.1), (k % 4 - 1.5) * 0.12)).normalized()
            ln = rnd.uniform(0.05, 0.075)
            for i, bp in enumerate(sp.bezier_points):
                t = i / 2
                bp.co = b0 + d * ln * t + Vector((0, 0, -0.008 * t * t))
                bp.radius = 1.0 - 0.9 * t; bp.handle_left_type = bp.handle_right_type = "AUTO"
            cu.materials.append(wm)
            w = bpy.data.objects.new(cu.name, cu); bpy.context.scene.collection.objects.link(w); w.parent = root
    return root
