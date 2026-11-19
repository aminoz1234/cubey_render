"""Procedural cat foreleg + paw with fur, pink toe beans and retractable claws. exec() then paw(name, ...).
Paw points along -Y (toes forward), pads face -Z. Real size (paw ~4 cm wide). Root at the wrist.
root["claw"] 0..1 extends the claws (keyable)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix


def _pm(name, col, rough=0.5, sss=0.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.002
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.3)
    b.inputs["Coat Weight"].default_value = coat
    tc = m.node_tree.nodes.new("ShaderNodeTexCoord"); nz = m.node_tree.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 900; m.node_tree.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = m.node_tree.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    m.node_tree.links.new(nz.outputs["Fac"], bp.inputs["Height"]); m.node_tree.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _fur(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    N.remove(N["Principled BSDF"])
    hb = N.new("ShaderNodeBsdfHairPrincipled"); hb.parametrization = "COLOR"
    hb.inputs["Roughness"].default_value = 0.32; hb.inputs["Radial Roughness"].default_value = 0.45; hb.inputs["Coat"].default_value = 0.15
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.bands_direction = "Y"; wv.inputs["Scale"].default_value = 22
    wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    st = N.new("ShaderNodeValToRGB"); st.color_ramp.elements[0].position = 0.3; st.color_ramp.elements[0].color = (0.03, 0.022, 0.016, 1)
    st.color_ramp.elements[1].position = 0.62; st.color_ramp.elements[1].color = (0.3, 0.17, 0.08, 1)
    L.new(wv.outputs["Fac"], st.inputs[0])
    # white socks toward the toes
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.4; mr.inputs["From Max"].default_value = -0.75
    L.new(sp.outputs["Y"], mr.inputs["Value"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(mr.outputs["Result"], mx.inputs["Factor"])
    L.new(st.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (0.78, 0.72, 0.64, 1)
    hi = N.new("ShaderNodeHairInfo"); pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3
    L.new(hi.outputs["Intercept"], pw.inputs[0]); mf = N.new("ShaderNodeMath"); mf.operation = "MULTIPLY"; mf.inputs[1].default_value = 0.25
    L.new(pw.outputs[0], mf.inputs[0])
    tip = N.new("ShaderNodeMix"); tip.data_type = "RGBA"; tip.blend_type = "SCREEN"; L.new(mf.outputs[0], tip.inputs["Factor"])
    L.new(mx.outputs["Result"], tip.inputs["A"]); tip.inputs["B"].default_value = (0.75, 0.6, 0.42, 1)
    L.new(tip.outputs["Result"], hb.inputs["Color"]); L.new(hb.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def _claw_mat(name="claw"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.75, 0.55, 0.5, 1)    # pink quick at the base
    rp.color_ramp.elements[1].color = (0.9, 0.88, 0.82, 1); rp.color_ramp.elements[1].position = 0.45
    L.new(sp.outputs["X"], rp.inputs[0]); L.new(rp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.25; b.inputs["Transmission Weight"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.002
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.1
    return m


def _blob(name, center, radii, m, parent, seg=24):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent; ob.location = center; ob.scale = radii
    return ob


def claw_mesh(name, length=0.012, base_r=0.0016, curl=0.9, m=None):
    """Curved, laterally flattened cone (cat claw). Tip at the end of the arc."""
    bm = bmesh.new(); rings = []; n_r, n_a = 14, 10
    for i in range(n_r + 1):
        t = i / n_r; ang = curl * t
        c = Vector((0, -math.sin(ang) * length / curl, -(1 - math.cos(ang)) * length / curl))
        tan = Vector((0, -math.cos(ang), -math.sin(ang))); nor = Vector((0, -math.sin(ang), math.cos(ang)))
        r = base_r * (1 - t) ** 0.8 + 0.00004
        ring = [bm.verts.new(c + Vector((math.cos(2 * math.pi * k / n_a) * r * 0.55, 0, 0)) + nor * math.sin(2 * math.pi * k / n_a) * r) for k in range(n_a)]
        rings.append(ring)
    for i in range(n_r):
        for k in range(n_a):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % n_a], rings[i + 1][(k + 1) % n_a], rings[i + 1][k]))
    bm.faces.new(rings[0][::-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m or _claw_mat())
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def paw(name="paw", hairs=12000, children=12):
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    root["claw"] = 0.0
    m_skin = _pm("paw_skin", (0.1, 0.07, 0.05), 0.7)
    m_pad = _pm("paw_pad", (0.3, 0.14, 0.14), 0.55, sss=0.15, coat=0.1)
    # foreleg + paw body as one smooth mesh: a capsule tapering into a rounded mitten
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=1.0)
    for v in bm.verts:
        y = v.co.y                                        # -1 toes .. +1 elbow
        x, z = v.co.x, v.co.z
        if y > -0.3:                                      # leg: long and thinner
            yy = -0.3 + (y + 0.3) * 6.0
            w = 0.62 - 0.08 * (y + 0.3)
            v.co = Vector((x * w, yy, z * w * 0.95))
        else:
            v.co = Vector((x * 1.1, y, z * 0.62 - 0.12))
    me = bpy.data.meshes.new(name + "_leg"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m_skin); me.materials.append(_fur(name + "_fur"))
    leg = bpy.data.objects.new(name + "_leg", me); bpy.context.scene.collection.objects.link(leg)
    leg.parent = root; leg.scale = (0.02, 0.02, 0.02); leg.location = (0, 0, 0)
    mod = leg.modifiers.new("fur", "PARTICLE_SYSTEM"); st = mod.particle_system.settings
    st.type = "HAIR"; st.count = hairs; st.hair_length = 0.008; st.material = 2
    st.emit_from = "FACE"; st.use_emit_random = True
    st.child_type = "INTERPOLATED"; st.child_percent = 4; st.rendered_child_count = children
    st.clump_factor = 0.3; st.roughness_1 = 0.0008; st.roughness_endpoint = 0.001
    st.root_radius = 0.6; st.tip_radius = 0.0; st.radius_scale = 0.0006; st.render_step = 4; st.use_hair_bspline = True
    sub = leg.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 1
    with bpy.context.temp_override(object=leg):
        bpy.ops.object.modifier_move_to_index(modifier="sub", index=0)
    # pads (underside, -Z): four toe beans + the big pad
    toes = [(-0.0135, -0.016), (-0.0048, -0.02), (0.0048, -0.02), (0.0135, -0.016)]
    for k, (x, y) in enumerate(toes):
        _blob(f"{name}_bean{k}", (x, y, -0.0118), (0.0036, 0.0042, 0.0022), m_pad, root)
    _blob(name + "_pad", (0, -0.005, -0.012), (0.0095, 0.0065, 0.0025), m_pad, root)
    # claws: hidden inside the toes, slide out along -Y when root["claw"] goes to 1
    for k, (x, y) in enumerate(toes):
        c = claw_mesh(f"{name}_claw{k}", length=0.011, base_r=0.0015)
        c.parent = root; c.location = (x, y + 0.004, -0.007)
        c.rotation_euler = (math.radians(-8), 0, math.radians(8 * (x / 0.0135)))
        fc = c.driver_add("location", 1); d = fc.driver; d.type = "SCRIPTED"
        v = d.variables.new(); v.name = "claw"; v.targets[0].id = root; v.targets[0].data_path = '["claw"]'
        d.expression = f"{y + 0.004:.4f} - claw*0.007"
        fc = c.driver_add("location", 2); d = fc.driver; d.type = "SCRIPTED"
        v = d.variables.new(); v.name = "claw"; v.targets[0].id = root; v.targets[0].data_path = '["claw"]'
        d.expression = "-0.007 + claw*0.0015"
    return root
