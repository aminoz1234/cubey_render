# ---------------------------------------------------------------- reset
sc = bpy.context.scene
for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
             bpy.data.textures, bpy.data.worlds, bpy.data.actions, bpy.data.node_groups, bpy.data.curves,
             bpy.data.particles):
    for d in list(coll):
        try: coll.remove(d)
        except Exception: pass
sc.timeline_markers.clear()
sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = F(END_T)
RES_W = int(globals().get('RES_W', 720))
sc.render.resolution_x, sc.render.resolution_y = RES_W, RES_W * 16 // 9
sc.render.resolution_percentage = 100

def put(obj, **kw):
    for k, v in kw.items():
        try: setattr(obj, k, v)
        except Exception: pass

for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try: sc.render.engine = eng; break
    except Exception: pass
ee = sc.eevee
put(ee, taa_render_samples=16, taa_samples=8, use_gtao=True, use_shadows=True, shadow_ray_count=2,
    shadow_step_count=6, use_raytracing=False)
put(sc.render, use_motion_blur=True, motion_blur_shutter=0.5)
put(sc.render, hair_type='STRIP', hair_subdiv=1)
try:
    sc.view_settings.view_transform = 'AgX'
    for lk in ('AgX - Punchy', 'Punchy'):
        try: sc.view_settings.look = lk; break
        except Exception: pass
except Exception: pass
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92

def glow_comp():
    try:
        ng = bpy.data.node_groups.new("BotGlow", "CompositorNodeTree")
        ng.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new('CompositorNodeRLayers'); gl = ng.nodes.new('CompositorNodeGlare')
        out = ng.nodes.new('NodeGroupOutput')
        for k, v in (('Type', 'Bloom'), ('Threshold', 1.6), ('Smoothness', 0.5), ('Strength', 0.25),
                     ('Saturation', 1.0), ('Size', 0.55)):
            try: gl.inputs[k].default_value = v
            except Exception as e: print("glare", k, e)
        ng.links.new(rl.outputs['Image'], gl.inputs['Image']); ng.links.new(gl.outputs['Image'], out.inputs[0])
        sc.compositing_node_group = ng; sc.render.use_compositing = True
    except Exception as e: print("glow skipped:", e)
glow_comp()

# ---------------------------------------------------------------- animation helpers
def set_interp(kind):
    try: bpy.context.preferences.edit.keyframe_new_interpolation_type = kind
    except Exception: pass

def kf(o, t, loc=None, rot=None, scl=None, interp='BEZIER', frame=None):
    set_interp(interp); f = frame if frame is not None else F(t)
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
    if scl is not None:
        o.scale = (scl, scl, scl) if isinstance(scl, (int, float)) else scl
        o.keyframe_insert('scale', frame=f)

VISSED = set()
def vis(o, *spans):
    VISSED.add(o.name); set_interp('CONSTANT')
    def key(f, hidden):
        o.hide_render = hidden; o.keyframe_insert('hide_render', frame=f)
    first = spans[0][0]
    key(1, bool(first and first > 0))
    for a, b in spans:
        if a and a > 0: key(F(a), False)
        if b is not None and b < END_T: key(F(b), True)

def vis_tree(root, *spans):
    VISSED.add(root.name)
    for c in root.children_recursive:
        if c.type in ('MESH', 'CURVE'): vis(c, *spans)
        else: VISSED.add(c.name)

def kval(sock, t, val, interp='LINEAR'):
    set_interp(interp); sock.default_value = val; sock.keyframe_insert('default_value', frame=F(t))

def look(src, dst):
    d = Vector(dst) - Vector(src); return d.to_track_quat('-Z', 'Y').to_euler()
def lerp(a, b, u): return tuple(a[i] + (b[i] - a[i]) * u for i in range(len(a)))
def smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def sample(keys, t):
    """keys: [(t, tuple)], smoothstep between keys"""
    if t <= keys[0][0]: return keys[0][1]
    for i in range(len(keys) - 1):
        if keys[i][0] <= t <= keys[i + 1][0]:
            u = smooth((t - keys[i][0]) / max(1e-6, keys[i + 1][0] - keys[i][0]))
            return lerp(keys[i][1], keys[i + 1][1], u)
    return keys[-1][1]

def steps(t0, t1, every=2):
    f = F(t0)
    while f <= F(t1):
        yield f, (f - 1) / FPS
        f += every

# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]; return m, nt, p
def setin(p, key, val):
    if key in p.inputs: p.inputs[key].default_value = val

def simple(name, base, rough=0.4, emit=None, es=0.0, sss=0.0, coat=0.0, metal=0.0, alpha=1.0):
    m, nt, p = node_mat(name)
    setin(p, 'Base Color', (*base, 1)); setin(p, 'Roughness', rough); setin(p, 'Metallic', metal)
    setin(p, 'Subsurface Weight', sss); setin(p, 'Subsurface Radius', (1, 0.4, 0.3)); setin(p, 'Subsurface Scale', 0.05)
    setin(p, 'Coat Weight', coat)
    if emit: setin(p, 'Emission Color', (*emit, 1)); setin(p, 'Emission Strength', es)
    if alpha < 1:
        setin(p, 'Alpha', alpha); put(m, surface_render_method='BLENDED', use_backface_culling=False)
    return m

def noisy(name, c1, c2, scale=8.0, rough=0.4, coat=0.0, sss=0.0, bump=0.1, metal=0.0, stripes=None, coords='Object'):
    """two-colour noise; stripes=(scale, c3) adds bands along X (abdomen rings, leg bands)"""
    m, nt, p = node_mat(name); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs[coords], nz.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1); ramp.color_ramp.elements[1].color = (*c2, 1)
    L.new(nz.outputs['Fac'], ramp.inputs['Fac']); col = ramp.outputs['Color']
    if stripes:
        wv = N.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
        wv.inputs['Scale'].default_value = stripes[0]; wv.inputs['Distortion'].default_value = 1.5
        L.new(tc.outputs[coords], wv.inputs['Vector'])
        sr = N.new('ShaderNodeValToRGB'); sr.color_ramp.interpolation = 'CONSTANT'
        sr.color_ramp.elements[1].position = 0.55
        sr.color_ramp.elements[0].color = (0, 0, 0, 1); sr.color_ramp.elements[1].color = (1, 1, 1, 1)
        L.new(wv.outputs['Fac'], sr.inputs['Fac'])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        L.new(sr.outputs['Color'], mx.inputs[0]); L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (*stripes[1], 1)
        col = mx.outputs[2]
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    L.new(nz.outputs['Fac'], bp.inputs['Height'])
    L.new(col, p.inputs['Base Color']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    setin(p, 'Roughness', rough); setin(p, 'Coat Weight', coat); setin(p, 'Metallic', metal)
    setin(p, 'Subsurface Weight', sss); setin(p, 'Subsurface Radius', (1.0, 0.35, 0.2)); setin(p, 'Subsurface Scale', 0.1)
    return m

def skin_mat(name="Skin", red=None):
    """human skin seen at bug scale: tone noise, pores, fine creases, a soft sheen.
    red=(centre, radius): an inflamed patch around an object-space point"""
    m, nt, p = node_mat(name); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 5
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.78, 0.48, 0.36, 1); ramp.color_ramp.elements[1].color = (0.93, 0.66, 0.53, 1)
    L.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    # pores: dark dots
    vor = N.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 9.0
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    pr = N.new('ShaderNodeValToRGB')
    pr.color_ramp.elements[0].position = 0.0; pr.color_ramp.elements[0].color = (0, 0, 0, 1)
    pr.color_ramp.elements[1].position = 0.12; pr.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(vor.outputs['Distance'], pr.inputs['Fac'])
    # creases: thin cell edges, stretched along the arm
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.6, 1.4, 1.4)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    ve = N.new('ShaderNodeTexVoronoi'); ve.feature = 'DISTANCE_TO_EDGE'; ve.inputs['Scale'].default_value = 7.0
    L.new(mp.outputs['Vector'], ve.inputs['Vector'])
    cr = N.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.05; cr.color_ramp.elements[0].color = (0.55, 0.55, 0.55, 1); cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(ve.outputs['Distance'], cr.inputs['Fac'])
    hm = N.new('ShaderNodeMath'); hm.operation = 'MULTIPLY'
    L.new(pr.outputs['Color'], hm.inputs[0]); L.new(cr.outputs['Color'], hm.inputs[1])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.02
    L.new(hm.outputs[0], bp.inputs['Height'])
    nf = N.new('ShaderNodeTexNoise'); nf.inputs['Scale'].default_value = 30; nf.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], nf.inputs['Vector'])
    b2 = N.new('ShaderNodeBump'); b2.inputs['Strength'].default_value = 0.12
    L.new(nf.outputs['Fac'], b2.inputs['Height']); L.new(bp.outputs['Normal'], b2.inputs['Normal'])
    dk = N.new('ShaderNodeMix'); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs[0].default_value = 0.35
    L.new(ramp.outputs['Color'], dk.inputs[6]); L.new(hm.outputs[0], dk.inputs[7])
    col = dk.outputs[2]
    if red:
        c, r = red
        vd = N.new('ShaderNodeVectorMath'); vd.operation = 'DISTANCE'; vd.inputs[1].default_value = c
        L.new(tc.outputs['Object'], vd.inputs[0])
        rr = N.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = 0.0; rr.inputs['From Max'].default_value = r
        L.new(vd.outputs['Value'], rr.inputs['Value'])
        rc = N.new('ShaderNodeValToRGB')
        rc.color_ramp.elements[0].color = (0.55, 0.06, 0.08, 1); rc.color_ramp.elements[1].color = (1, 1, 1, 0)
        rc.color_ramp.elements[1].position = 1.0
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        L.new(rr.outputs['Result'], inv.inputs[1])
        pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 0.7
        L.new(inv.outputs[0], pw.inputs[0])
        L.new(pw.outputs[0], mx.inputs[0]); L.new(col, mx.inputs[6]); L.new(rc.outputs['Color'], mx.inputs[7])
        col = mx.outputs[2]
    L.new(col, p.inputs['Base Color']); L.new(b2.outputs['Normal'], p.inputs['Normal'])
    setin(p, 'Roughness', 0.48); setin(p, 'Coat Weight', 0.18); setin(p, 'Coat Roughness', 0.25)
    setin(p, 'Subsurface Weight', 0.35); setin(p, 'Subsurface Radius', (1.0, 0.35, 0.2)); setin(p, 'Subsurface Scale', 0.25)
    return m

M_SKIN = skin_mat()
M_ARMHAIR = simple("ArmHair", (0.10, 0.06, 0.035), rough=0.35, coat=0.3)
M_SHEET = noisy("Sheet", (0.80, 0.84, 0.92), (0.95, 0.96, 1.0), scale=0.3, rough=0.75, bump=0.04)
M_SPBODY = noisy("SpiderBody", (0.07, 0.04, 0.02), (0.30, 0.18, 0.09), scale=6, rough=0.32, coat=0.5, bump=0.25)
M_SPABD = noisy("SpiderAbd", (0.10, 0.06, 0.03), (0.42, 0.27, 0.13), scale=5, rough=0.3, coat=0.6, bump=0.2,
                stripes=(3.2, (0.05, 0.03, 0.015)))
M_SPLEG = noisy("SpiderLeg", (0.10, 0.06, 0.03), (0.32, 0.20, 0.10), scale=9, rough=0.32, coat=0.5, bump=0.2,
                stripes=(1.6, (0.04, 0.025, 0.015)))
M_SPHAIR = simple("SpiderHair", (0.16, 0.10, 0.05), rough=0.4)
M_EYE = simple("BlackEye", (0.005, 0.005, 0.006), rough=0.04, coat=1.0)
M_FANG = simple("Fang", (0.02, 0.012, 0.01), rough=0.15, coat=1.0)
M_FLYEYE = noisy("FlyEye", (0.35, 0.08, 0.02), (0.75, 0.25, 0.05), scale=40, rough=0.12, coat=1.0, bump=0.4)
M_FLYTHX = noisy("FlyThorax", (0.30, 0.20, 0.08), (0.55, 0.42, 0.18), scale=7, rough=0.5, bump=0.2)
M_FLYABD = simple("FlyAbdomen", (0.06, 0.14, 0.55), rough=0.18, metal=0.85, coat=0.9)
M_FLYHAIR = simple("FlyHair", (0.62, 0.48, 0.20), rough=0.45)
M_FLYLEG = noisy("FlyLeg", (0.05, 0.04, 0.03), (0.45, 0.35, 0.12), scale=5, rough=0.4, stripes=(4, (0.6, 0.45, 0.15)))
M_MOSBODY = noisy("MosBody", (0.03, 0.03, 0.035), (0.12, 0.11, 0.12), scale=12, rough=0.35, coat=0.4,
                  stripes=(18, (0.92, 0.92, 0.88)))
M_MOSLEG = noisy("MosLeg", (0.02, 0.02, 0.02), (0.08, 0.08, 0.08), scale=10, rough=0.4, stripes=(9, (0.9, 0.9, 0.88)))
M_EGG = noisy("Egg", (0.95, 0.90, 0.72), (1.0, 0.97, 0.86), scale=60, rough=0.3, coat=0.7, sss=0.5, bump=0.1)
M_LARVA = noisy("Larva", (0.86, 0.78, 0.60), (0.98, 0.93, 0.80), scale=4, rough=0.25, coat=0.9, sss=0.7, bump=0.15,
                stripes=(5.5, (0.80, 0.74, 0.58)))
M_SPINE = simple("Spine", (0.04, 0.02, 0.01), rough=0.3, coat=0.5)
M_SPIRACLE = simple("Spiracle", (0.18, 0.08, 0.02), rough=0.3, coat=0.8)
M_SILK = simple("Silk", (0.95, 0.96, 1.0), rough=0.15, emit=(0.9, 0.95, 1.0), es=0.4, coat=1.0)
M_SAC = simple("Sac", (0.96, 0.95, 0.92), rough=0.6, sss=0.6)
M_WOOD = noisy("Frame", (0.85, 0.83, 0.78), (0.97, 0.96, 0.93), scale=2, rough=0.4, bump=0.05)
M_HOLE = simple("Hole", (0.06, 0.005, 0.005), rough=0.15, coat=1.0)
M_WOUND = noisy("Wound", (0.50, 0.05, 0.06), (0.85, 0.22, 0.20), scale=6, rough=0.2, coat=1.0, sss=0.6, bump=0.3)
M_DERMIS = noisy("Dermis", (0.80, 0.36, 0.34), (0.96, 0.60, 0.54), scale=3, rough=0.3, coat=0.9, sss=0.6, bump=0.3)
M_EPI = noisy("Epidermis", (0.80, 0.55, 0.42), (0.95, 0.72, 0.60), scale=6, rough=0.4, sss=0.4, bump=0.1)
M_FAT = noisy("Fat", (0.98, 0.75, 0.25), (1.0, 0.90, 0.45), scale=3, rough=0.2, coat=1.0, sss=0.8, bump=0.2)
M_CAVITY = noisy("Cavity", (0.40, 0.03, 0.04), (0.75, 0.12, 0.12), scale=4, rough=0.15, coat=1.0, sss=0.5, bump=0.25)
M_FLOOR = simple("Studio", (0.82, 0.86, 0.92), rough=0.6)

def wing_mat(name, col=(0.55, 0.50, 0.45), a=0.35):
    m, nt, p = node_mat(name)
    setin(p, 'Base Color', (*col, 1)); setin(p, 'Roughness', 0.08); setin(p, 'Alpha', a)
    setin(p, 'Coat Weight', 1.0)
    put(m, surface_render_method='BLENDED', use_backface_culling=False)
    return m
M_FLYWING = wing_mat("FlyWing", (0.45, 0.38, 0.30), 0.38)
M_MOSWING = wing_mat("MosWing", (0.75, 0.78, 0.80), 0.30)

def heat_mat():
    m, nt, p = node_mat("Heat"); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); gr = N.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    L.new(tc.outputs['Object'], gr.inputs['Vector'])
    setin(p, 'Base Color', (1, 0.4, 0.1, 1)); setin(p, 'Emission Color', (1.0, 0.35, 0.05, 1))
    L.new(gr.outputs['Fac'], p.inputs['Alpha'])
    put(m, surface_render_method='BLENDED', use_backface_culling=False)
    return m, p
M_HEAT, P_HEAT = heat_mat()

# ---------------------------------------------------------------- geometry helpers
def link(o): bpy.context.collection.objects.link(o); return o
def empty(name, loc=(0, 0, 0), parent=None):
    o = link(bpy.data.objects.new(name, None)); o.location = loc
    if parent: o.parent = parent
    return o

def blob(bm, c, r, mat_i=0, seg_n=32):
    m4 = bmesh.ops.create_uvsphere(bm, u_segments=seg_n, v_segments=seg_n // 2 + 2, radius=1.0)
    for v in m4['verts']: v.co = Vector((v.co.x * r[0], v.co.y * r[1], v.co.z * r[2])) + Vector(c)
    for f in {f for v in m4['verts'] for f in v.link_faces}: f.material_index = mat_i
    return m4['verts']

def stick(bm, a, b, r1, r2=None, mat_i=0, segs=10):
    a, b = Vector(a), Vector(b); d = b - a
    m4 = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2 if r2 is not None else r1 * 0.85,
                               depth=d.length)
    q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    for v in m4['verts']: v.co = (q @ v.co) + (a + b) / 2
    for f in {f for v in m4['verts'] for f in v.link_faces}: f.material_index = mat_i

def chain(bm, pts, radii, mat_i=0, segs=10):
    for i in range(len(pts) - 1):
        stick(bm, pts[i], pts[i + 1], radii[i], radii[i + 1], mat_i, segs)
        if i < len(pts) - 2: blob(bm, pts[i + 1], (radii[i + 1] * 1.15,) * 3, mat_i, 12)

def mesh_obj(name, bm, mats, parent=None, loc=(0, 0, 0), smooth_all=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth_all:
        for p in me.polygons: p.use_smooth = True
    for m in mats: me.materials.append(m)
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    if parent: o.parent = parent
    return o

def add_hair(o, count, length, mat_slot, radius=0.003, normal=1.0, align=None, rand=0.4, seed=1):
    md = o.modifiers.new("hair", 'PARTICLE_SYSTEM'); ps = o.particle_systems[-1]; ps.seed = seed
    pt = ps.settings; pt.type = 'HAIR'; pt.count = count; pt.hair_length = length
    pt.emit_from = 'FACE'; pt.use_emit_random = True; pt.use_even_distribution = True
    # with advanced hair the strand length IS the emit velocity, so scale every factor by the length
    pt.use_advanced_hair = True; pt.normal_factor = normal * length; pt.factor_random = length * rand
    if align: pt.object_align_factor = tuple(a * length for a in align)
    pt.material_slot = o.material_slots[mat_slot].name if o.material_slots else ''
    put(pt, root_radius=1.0, tip_radius=0.1, radius_scale=radius, shape=-0.2, render_step=3, display_step=2,
        child_type='NONE')
    return pt

def plight(name, loc, energy, col, radius=0.2, parent=None):
    d = bpy.data.lights.new(name, 'POINT'); d.energy = energy; d.color = col; d.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, d)); o.location = loc
    if parent: o.parent = parent
    return o

CAMS = []
def camera(name, t_start, keys, lens=50, head=40.0, dof=None, shake=None, fstop=1.4):
    """keys: [(t, loc, target)] (smoothstep between keys, keyed every 2 frames); shake: [(t0, t1, amount)]"""
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = 0.005; d.clip_end = 400
    if dof is not None:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(dof, (int, float)): d.dof.focus_distance = dof
        else: d.dof.focus_object = dof
    o = link(bpy.data.objects.new(name, d))
    rnd = random.Random(sum(map(ord, name)))
    t_end = keys[-1][0]
    for f, t in steps(keys[0][0], t_end, 2):
        loc = sample([(k[0], k[1]) for k in keys], t); tgt = sample([(k[0], k[2]) for k in keys], t)
        amp = 0.0
        for a, b, s in (shake or []):
            if a <= t <= b: amp = max(amp, s * math.sin(math.pi * (t - a) / (b - a)) ** 0.5)
        tgt = tuple(c + rnd.uniform(-1, 1) * amp for c in tgt)
        # a slow hand-held drift on every shot (nothing is ever locked off)
        tgt = (tgt[0] + 0.012 * math.sin(t * 2.3) * lens / 50, tgt[1] + 0.01 * math.cos(t * 1.7), tgt[2] + 0.012 * math.sin(t * 1.9 + 1))
        kf(o, t, loc=loc, rot=look(loc, tgt), interp='LINEAR', frame=f)
    hl = plight(name + "_head", (0.0, 0.25, 0.0), head, (1.0, 0.92, 0.82), 0.3, parent=o)
    m = sc.timeline_markers.new(name, frame=F(t_start)); m.camera = o
    CAMS.append((t_start, o, hl)); return o

