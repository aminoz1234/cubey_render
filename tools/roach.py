"""Procedural realistic cockroach for Blender 5.2+ (Cycles). exec() this file, then call roach(name, scale, ...).
Body is modelled at unit length (1.0 along +Y, head at +Y, belly at z=0) and scaled.
Legs and antennae are driven by simple driver expressions (no Python needed at render time):
  root["spd"]  gait speed (radians per frame), root["amp"] leg swing 0..1, root["ant"] antenna wiggle 0..1."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler


def _mat(name, base, rough=0.3, coat=0.7, sss=0.0, trans=0.0, spec=0.5):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 0.35
    mix.inputs["A"].default_value = (*base, 1); L.new(nz.outputs["Color"], mix.inputs["B"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.16
    b.inputs["Specular IOR Level"].default_value = spec
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.15); b.inputs["Subsurface Scale"].default_value = 0.004
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    bm_ = N.new("ShaderNodeBump"); bm_.inputs["Strength"].default_value = 0.15
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 220; L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    L.new(nz2.outputs["Fac"], bm_.inputs["Height"]); L.new(bm_.outputs["Normal"], b.inputs["Normal"])
    return m


def _band_mat(name, light, dark, axis="Y", bands=9.0, rough=0.28, coat=0.75, sss=0.1):
    """Segmented abdomen / pronotum: pale and dark bands along an axis, glossy chitin."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.bands_direction = axis; wv.inputs["Scale"].default_value = bands
    wv.inputs["Distortion"].default_value = 0.4; wv.wave_profile = "SAW"
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    rp = N.new("ShaderNodeValToRGB"); cr = rp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (*dark, 1)
    cr.elements[1].position = 0.85; cr.elements[1].color = (*light, 1)
    L.new(wv.outputs["Fac"], rp.inputs[0]); L.new(rp.outputs["Color"], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; L.new(wv.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.14
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.2); b.inputs["Subsurface Scale"].default_value = 0.004
    return m


def _pronotum_mat(name, pale, dark):
    """German-cockroach shield: pale translucent rim with two dark stripes."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(sp.outputs["X"], ab.inputs[0])
    # object-space x of the shield runs -1..1 (unit sphere scaled by the object)
    rp = N.new("ShaderNodeValToRGB"); cr = rp.color_ramp; cr.interpolation = "EASE"
    cr.elements[0].position = 0.08; cr.elements[0].color = (*pale, 1)
    e = cr.elements.new(0.14); e.color = (*dark, 1)
    e = cr.elements.new(0.4); e.color = (*dark, 1)
    cr.elements[1].position = 0.5; cr.elements[1].color = (*pale, 1)
    L.new(ab.outputs[0], rp.inputs[0]); L.new(rp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.7; b.inputs["Coat Roughness"].default_value = 0.12
    b.inputs["Subsurface Weight"].default_value = 0.08; b.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.004
    return m


def _wing_mat(name, col):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.bands_direction = "X"; wv.inputs["Scale"].default_value = 14
    wv.inputs["Distortion"].default_value = 2.0; wv.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    vr = N.new("ShaderNodeValToRGB"); vr.color_ramp.elements[0].color = (col[0] * 0.45, col[1] * 0.45, col[2] * 0.45, 1)
    vr.color_ramp.elements[0].position = 0.0; vr.color_ramp.elements[1].position = 0.18; vr.color_ramp.elements[1].color = (*col, 1)
    L.new(wv.outputs["Fac"], vr.inputs[0]); L.new(vr.outputs["Color"], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; L.new(wv.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.12
    b.inputs["Transmission Weight"].default_value = 0.0
    b.inputs["Subsurface Weight"].default_value = 0.08; b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.15)
    b.inputs["Subsurface Scale"].default_value = 0.004
    return m


def _ellipsoid(name, center, radii, m, parent, rot=(0, 0, 0), seg=24, flat_bottom=0.0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    for v in bm.verts:
        if flat_bottom and v.co.z < -flat_bottom:
            v.co.z = -flat_bottom + (v.co.z + flat_bottom) * 0.25
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.scale = radii; ob.location = center; ob.rotation_euler = rot; ob.parent = parent
    me.materials.append(m)
    return ob


def _tube(name, pts, radii, m, parent, res=6):
    """Tapered curve tube (legs, antennae, cerci) converted to nothing: stays a curve object (cheap, animatable)."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = 1.0; cu.bevel_resolution = 2; cu.resolution_u = res; cu.use_fill_caps = True
    sp = cu.splines.new("POLY" if len(pts) < 3 else "BEZIER")
    if sp.type == "BEZIER":
        sp.bezier_points.add(len(pts) - 1)
        for bp, co, r in zip(sp.bezier_points, pts, radii):
            bp.co = co; bp.radius = r; bp.handle_left_type = bp.handle_right_type = "AUTO"
    else:
        sp.points.add(len(pts) - 1)
        for bp, co, r in zip(sp.points, pts, radii):
            bp.co = (*co, 1); bp.radius = r
    ob = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent; cu.materials.append(m)
    return ob


def _driver(ob, path, idx, expr, root, props=("spd", "amp", "ant", "ph0")):
    fc = ob.driver_add(path, idx); d = fc.driver; d.type = "SCRIPTED"
    for p in props:
        if p in expr:
            v = d.variables.new(); v.name = p; v.type = "SINGLE_PROP"
            v.targets[0].id = root; v.targets[0].data_path = f'["{p}"]'
    d.expression = expr
    return fc


def roach(name, scale=0.02, nymph=False, seed=1, palette=None):
    """Returns the root empty. Body length = scale (metres)."""
    rnd = random.Random(seed)
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    root.empty_display_size = 0.5
    root["spd"] = 0.9; root["amp"] = 1.0; root["ant"] = 1.0; root["ph0"] = rnd.uniform(0, 6.28)
    body = bpy.data.objects.new(name + "_body", None); bpy.context.scene.collection.objects.link(body)
    body.parent = root; body.scale = (scale,) * 3
    tag = "nym" if nymph else "adult"
    if nymph:
        pale, dark = (0.3, 0.2, 0.11), (0.03, 0.02, 0.012)
        m_abd = _band_mat("rc_abd_" + tag, (0.2, 0.12, 0.06), (0.025, 0.015, 0.008), bands=7.5, sss=0.25)
        m_leg = _mat("rc_leg_" + tag, (0.32, 0.22, 0.13), rough=0.35, coat=0.5, sss=0.35)
    else:
        pale, dark = (0.24, 0.12, 0.04), (0.012, 0.006, 0.003)
        m_abd = _band_mat("rc_abd_" + tag, (0.12, 0.05, 0.018), (0.02, 0.01, 0.005), bands=7.5)
        m_leg = _mat("rc_leg_" + tag, (0.2, 0.09, 0.03), rough=0.32, coat=0.5, sss=0.3)
    m_pro = _pronotum_mat("rc_pro_" + tag, pale, dark)
    m_head = _mat("rc_head_" + tag, (0.1, 0.045, 0.015) if not nymph else (0.15, 0.09, 0.05), rough=0.25, coat=0.8, sss=0.2)
    m_eye = _mat("rc_eye", (0.01, 0.008, 0.006), rough=0.1, coat=1.0)
    # body parts (unit space: length ~1 from y=-0.5 to 0.5)
    _ellipsoid(name + "_abd", (0, -0.12, 0.13), (0.2, 0.36, 0.075), m_abd, body, flat_bottom=0.5)
    _ellipsoid(name + "_thx", (0, 0.13, 0.12), (0.15, 0.13, 0.06), m_abd, body)
    _ellipsoid(name + "_pro", (0, 0.24, 0.155), (0.19, 0.13, 0.035), m_pro, body, rot=(math.radians(-8), 0, 0))
    hd = _ellipsoid(name + "_head", (0, 0.34, 0.075), (0.085, 0.07, 0.065), m_head, body, rot=(math.radians(50), 0, 0))
    for s in (-1, 1):
        _ellipsoid(name + f"_eye{s}", (0.058 * s, 0.355, 0.095), (0.022, 0.035, 0.03), m_eye, body, rot=(0, 0, math.radians(20 * s)))
        # palps
        _tube(name + f"_palp{s}", [(0.03 * s, 0.4, 0.06), (0.05 * s, 0.44, 0.03), (0.055 * s, 0.46, 0.0)], [0.012, 0.009, 0.006], m_leg, body)
        # cerci
        _tube(name + f"_cerc{s}", [(0.05 * s, -0.46, 0.12), (0.1 * s, -0.56, 0.11), (0.13 * s, -0.6, 0.1)], [0.018, 0.012, 0.004], m_leg, body)
    if not nymph:
        m_wing = _wing_mat("rc_wing", (0.14, 0.055, 0.016))
        for s in (-1, 1):
            _ellipsoid(name + f"_wing{s}", (0.055 * s, -0.14, 0.18), (0.13, 0.4, 0.03), m_wing, body,
                       rot=(math.radians(-3), math.radians(-6 * s), math.radians(-3 * s)))
    # legs: (hip y, knee offset, foot offset) for the right side; mirrored for the left
    legs = [(0.2, (0.17, 0.1, 0.07), (0.27, 0.28, -0.11), 0.0),
            (0.11, (0.25, 0.02, 0.08), (0.42, -0.04, -0.11), math.pi),
            (0.02, (0.22, -0.16, 0.09), (0.38, -0.5, -0.11), 0.0)]
    for i, (hy, knee, foot, ph) in enumerate(legs):
        for s in (-1, 1):
            piv = bpy.data.objects.new(name + f"_hip{i}{s}", None); bpy.context.scene.collection.objects.link(piv)
            piv.parent = body; piv.location = (0.07 * s, hy, 0.1); piv.empty_display_size = 0.05
            k = Vector((knee[0] * s, knee[1], knee[2])); f = Vector((foot[0] * s, foot[1], foot[2]))
            tar = f + (f - k).normalized() * 0.12 + Vector((0, 0, -0.01))
            mid = k * 0.5 + Vector((0, 0, 0.01))
            _tube(name + f"_leg{i}{s}", [(0, 0, 0), tuple(mid), tuple(k), tuple((k + f) / 2), tuple(f), tuple(tar)],
                  [0.02, 0.019, 0.013, 0.01, 0.007, 0.004], m_leg, piv)
            # spines along the tibia
            bm = bmesh.new()
            for j in range(5):
                t = 0.15 + 0.17 * j
                p = k + (f - k) * t
                out = Vector((s * 0.5, 0.0, -0.4)).normalized()
                bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.004, radius2=0.0, depth=0.045,
                                      matrix=Matrix.Translation(p + out * 0.025) @ out.to_track_quat("Z", "Y").to_matrix().to_4x4())
            me = bpy.data.meshes.new(name + f"_sp{i}{s}"); bm.to_mesh(me); bm.free(); me.materials.append(m_leg)
            so = bpy.data.objects.new(name + f"_sp{i}{s}", me); bpy.context.scene.collection.objects.link(so); so.parent = piv
            # tripod gait: legs 0 and 2 of one side move with leg 1 of the other side
            P = ph + (0 if s > 0 else math.pi)
            _driver(piv, "rotation_euler", 2, f"amp*0.42*sin(frame*spd+ph0+{P:.3f})", root)
            _driver(piv, "rotation_euler", 1, f"amp*{0.3 * s:.2f}*(cos(frame*spd+ph0+{P:.3f})+abs(cos(frame*spd+ph0+{P:.3f})))", root)
    # antennae: long whips from the head, wiggling
    for s in (-1, 1):
        piv = bpy.data.objects.new(name + f"_antp{s}", None); bpy.context.scene.collection.objects.link(piv)
        piv.parent = body; piv.location = (0.04 * s, 0.39, 0.1)
        pts = [(0, 0, 0), (0.08 * s, 0.25, 0.08), (0.22 * s, 0.55, 0.1), (0.38 * s, 0.85, 0.06), (0.55 * s, 1.1, -0.02)]
        _tube(name + f"_ant{s}", pts, [0.014, 0.01, 0.008, 0.006, 0.003], m_leg if nymph else m_head, piv, res=10)
        _driver(piv, "rotation_euler", 2, f"ant*0.35*sin(frame*0.17+ph0+{1.3 * s:.2f})", root)
        _driver(piv, "rotation_euler", 0, f"ant*0.25*sin(frame*0.23+ph0*2+{0.7 * s:.2f})", root)
    return root
