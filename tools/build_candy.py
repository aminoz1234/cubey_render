"""Candy-in-bed video: "This is what happens when you eat candy in bed and fall asleep without brushing".
Starts from scenes/ear/ear.blend (bedroom, sleeping man, kidney tray), strips the ear-video parts and adds:
gummy bears, a phone showing the real Cubey app, a macro mouth set (10x, x=200), a tooth cutaway (x=230)
and baby teeth in the tray. Saves scenes/candy/candy.blend.  Blender 5.2+, Cycles."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

ROOT = os.environ.get("CUBEY_ROOT") or os.getcwd()
for f_ in ("realism.py", "common_build.py"):
    exec(open(os.path.join(ROOT, "tools", f_)).read())
random.seed(21)
FPS = 30
T_END = 33.65


def F(t):
    return int(round(t * FPS)) + 1


S = bpy.context.scene
S.frame_start, S.frame_end = 1, F(T_END)
S.timeline_markers.clear()
T = dict(bed=0.0, teeth=3.75, bact=5.8, acid=8.6, morning=10.2, demo=13.3, saliva=17.5, melt=21.7,
         cutaway=25.0, hospital=28.1, end=31.5)
FR = {k: F(v) for k, v in T.items()}
order = list(T)
RANGE = {k: (FR[k], (FR[order[i + 1]] - 1) if i + 1 < len(order) else F(T_END)) for i, k in enumerate(order)}

# ---------------------------------------------------------------- strip the ear video
DROP = ("bug", "baby", "blade", "bubble", "canal", "chip", "crumbs", "drum", "eardrum", "mother", "oil", "pulled",
        "smear", "tweezers", "wax", "C0", "C1", "clinic", "bug_fill", "bug_in", "drum_back")
for o in list(bpy.data.objects):
    if (o.name.startswith(DROP) and o.name != "chip_bag") or o.type == "CAMERA":
        bpy.data.objects.remove(o, do_unlink=True)
for idb in [o for o in bpy.data.objects] + [o.data for o in bpy.data.objects if o.type == "LIGHT"] + \
        [m.node_tree for m in bpy.data.materials if m.node_tree] + [S.world.node_tree]:
    if idb and idb.animation_data and not (hasattr(idb, "type") and idb.type == "ARMATURE"):
        idb.animation_data_clear()
for o in bpy.data.objects:
    o.hide_render = False
# fixed night lights / world (were keyed for the clinic shots)
L_ = bpy.data.objects
L_["moon"].data.energy = 9.0; L_["nightlight"].data.energy = 2.5; L_["facefill"].data.energy = 1.6
wn = S.world.node_tree.nodes
for n in wn:
    if n.type == "MIX" and n.data_type == "RGBA" and n.inputs["Factor"].is_linked is False and n.blend_type == "MIX":
        n.inputs["Factor"].default_value = 0.0
wn["Background"].inputs["Strength"].default_value = 0.12
pill = bpy.data.materials["pillowcase"].node_tree
for n in pill.nodes:
    if n.type == "MIX" and n.blend_type == "MULTIPLY":
        n.inputs["B"].default_value = (0.85, 0.86, 0.9, 1)

rig = bpy.data.objects["Man"]; pb = rig.pose.bones
rig.animation_data_clear()
for nm in ("orbicularis03.L", "orbicularis03.R", "orbicularis04.L", "orbicularis04.R"):
    pb[nm].rotation_mode = "XYZ"
for s_ in ("L", "R"):
    pb["orbicularis03." + s_].rotation_euler = (math.radians(-26), 0, 0)
    pb["orbicularis04." + s_].rotation_euler = (math.radians(9), 0, 0)
pb["jaw"].rotation_mode = "XYZ"; pb["jaw"].rotation_euler = (math.radians(9), 0, 0)      # mouth slightly open
bpy.context.view_layer.update()
MT = 0.5; PILLOW_TOP = MT + 0.12
HEAD = rig.matrix_world @ Vector((0, -0.05, 1.66))
MOUTH = rig.matrix_world @ Vector((0.0, -0.115, 1.565))

# ---------------------------------------------------------------- gummy bag + spilled gummy bears
bag = bpy.data.objects["chip_bag"]
m_bag = bpy.data.materials["bag_print"]; nt = m_bag.node_tree
for n in nt.nodes:
    if n.type == "VALTORGB":
        n.color_ramp.elements[0].color = (0.05, 0.25, 0.75, 1); n.color_ramp.elements[1].color = (0.98, 0.85, 0.1, 1)
bag.location = (-0.1, -0.36, MT + 0.035)


def gummy_mat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.18
    b.inputs["Transmission Weight"].default_value = 0.55; b.inputs["IOR"].default_value = 1.45
    b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Radius"].default_value = col
    b.inputs["Subsurface Scale"].default_value = 0.004; b.inputs["Coat Weight"].default_value = 0.4
    return m


GUM_COLS = [(0.85, 0.05, 0.04), (0.95, 0.45, 0.02), (0.95, 0.8, 0.05), (0.25, 0.75, 0.1), (0.9, 0.85, 0.75)]
GUM_MATS = [gummy_mat(f"gummy{k}", c) for k, c in enumerate(GUM_COLS)]


def gummy_bear_mesh(name):
    """Little bear: body, head, ears, 4 legs (metaball, converted to a mesh)."""
    mb = bpy.data.metaballs.new(name); mb.resolution = 0.06; mb.render_resolution = 0.04
    def el(co, r, sz=None):
        e = mb.elements.new(); e.co = co; e.radius = r
        if sz:
            e.type = "ELLIPSOID"; e.size_x, e.size_y, e.size_z = sz
    el((0, 0, 0), 0.5, (0.5, 0.42, 0.62)); el((0, 0, 0.7), 0.42)
    for s in (-1, 1):
        el((0.28 * s, 0, 1.05), 0.17); el((0.38 * s, -0.05, 0.2), 0.22); el((0.25 * s, -0.05, -0.55), 0.24)
    ob = bpy.data.objects.new(name + "_mb", mb); S.collection.objects.link(ob)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); me.name = name
    bpy.data.objects.remove(ob); bpy.data.metaballs.remove(mb)
    for p in me.polygons:
        p.use_smooth = True
    return me


BEAR = gummy_bear_mesh("gummy_bear")


def bear(loc, scale, rot, k):
    ob = link(bpy.data.objects.new(f"bear{k}", BEAR.copy())); ob.data.materials.append(GUM_MATS[k % len(GUM_MATS)])
    ob.location = loc; ob.scale = (scale,) * 3; ob.rotation_euler = rot
    return ob


for k in range(9):
    on_pillow = k < 4
    loc = Vector((-0.14 + random.uniform(-0.05, 0.05), -0.22 + random.uniform(-0.03, 0.03), PILLOW_TOP - 0.002)) if on_pillow else \
        Vector((-0.1 + random.uniform(-0.08, 0.1), -0.27 + random.uniform(-0.05, 0.04), MT + 0.004))
    bear(loc, 0.0095, (math.radians(90 + random.uniform(-10, 10)), 0, random.uniform(0, 6.28)), k)

# ---------------------------------------------------------------- the phone on the bed, showing the real Cubey app
UI = os.path.join(ROOT, "assets", "ui")
PW, PH = 0.0715, 0.1545
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co = Vector((v.co.x * PW, v.co.y * PH, v.co.z * 0.0078))
bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6], offset=0.009, segments=6, affect="EDGES")
me = bpy.data.meshes.new("phone"); bm.to_mesh(me); bm.free()
phone = link(bpy.data.objects.new("phone", me))
bv = phone.modifiers.new("bev", "BEVEL"); bv.width = 0.0015; bv.segments = 3
me.materials.append(mat("phone_body", (0.02, 0.02, 0.025), rough=0.25, metal=0.6, coat=0.6))
phone.location = (0.06, -0.33, MT + 0.008); phone.rotation_euler = (math.radians(4), math.radians(-3), math.radians(-12))
# screen: three real screenshots (scan -> result scrolled -> Today), swapped on keyed factors
scr = link(bpy.data.objects.new("phone_screen", bpy.data.meshes.new("phone_screen")))
bms = bmesh.new(); bmesh.ops.create_grid(bms, x_segments=1, y_segments=1, size=0.5)
for v in bms.verts:
    v.co = Vector((v.co.x * (PW - 0.006) * 2, v.co.y * (PH - 0.006) * 2, 0))
bms.to_mesh(scr.data); bms.free()
scr.data.uv_layers.new(name="UVMap")
for loop in scr.data.loops:
    co = scr.data.vertices[loop.vertex_index].co
    scr.data.uv_layers[0].data[loop.index].uv = (0.5 + co.x / ((PW - 0.006) * 2), 0.5 + co.y / ((PH - 0.006) * 2))
scr.parent = phone; scr.location = (0, 0, 0.0040)
sm = bpy.data.materials.new("phone_ui"); sm.use_nodes = True; snt = sm.node_tree; N, Lk = snt.nodes, snt.links
uvn = N.new("ShaderNodeUVMap")
def img_node(fn, scroll=False):
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(UI, fn)); t.image.pack()
    t.extension = "CLIP"
    if scroll:
        mp = N.new("ShaderNodeMapping"); mp.name = "scroll"
        mp.inputs["Scale"].default_value = (1, 2532 / 4500, 1)
        Lk.new(uvn.outputs["UV"], mp.inputs["Vector"]); Lk.new(mp.outputs[0], t.inputs["Vector"])
        return t, mp
    Lk.new(uvn.outputs["UV"], t.inputs["Vector"])
    return t, None
i_read, _ = img_node("reading.png"); i_res, mp_res = img_node("result_tall.png", True); i_today, _ = img_node("today.png")
mx1 = N.new("ShaderNodeMix"); mx1.data_type = "RGBA"; Lk.new(i_read.outputs["Color"], mx1.inputs["A"]); Lk.new(i_res.outputs["Color"], mx1.inputs["B"])
mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; Lk.new(mx1.outputs["Result"], mx2.inputs["A"]); Lk.new(i_today.outputs["Color"], mx2.inputs["B"])
em = N.new("ShaderNodeEmission"); Lk.new(mx2.outputs["Result"], em.inputs["Color"])
br = N.new("ShaderNodeValue"); br.outputs[0].default_value = 0.0; Lk.new(br.outputs[0], em.inputs["Strength"])
gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03; gl.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1)
add = N.new("ShaderNodeAddShader"); Lk.new(em.outputs[0], add.inputs[0]); Lk.new(gl.outputs[0], add.inputs[1])
Lk.new(add.outputs[0], N["Material Output"].inputs["Surface"]); N.remove(N["Principled BSDF"])
scr.data.materials.append(sm)
d0, d1 = RANGE["demo"]
f_res, f_today = F(14.7), F(16.2)
for f, a, b in ((1, 0, 0), (f_res, 0, 0), (f_res + 1, 1, 0), (f_today, 1, 0), (f_today + 1, 1, 1)):
    mx1.inputs["Factor"].default_value = a; mx1.inputs["Factor"].keyframe_insert("default_value", frame=f)
    mx2.inputs["Factor"].default_value = b; mx2.inputs["Factor"].keyframe_insert("default_value", frame=f)
mp_res.inputs["Location"].default_value = (0, 0.0, 0); mp_res.inputs["Location"].keyframe_insert("default_value", frame=f_res + 6)
mp_res.inputs["Location"].default_value = (0, 1 - 2532 / 4500, 0); mp_res.inputs["Location"].keyframe_insert("default_value", frame=f_today - 4)
for f, v in ((1, 0.0), (d0 - 1, 0.0), (d0 + 3, 1.6), (d1, 1.6), (d1 + 1, 0.0)):
    br.outputs[0].default_value = v; br.outputs[0].keyframe_insert("default_value", frame=f)
set_interp(snt, "CONSTANT")
for fc in fcurves(snt):
    if "Location" in fc.data_path or "inputs[1]" in fc.data_path:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
# the phone's glow lights his face a little
glow = point("phone_glow", phone.location + Vector((0, 0, 0.06)), 0.0, (0.9, 0.95, 1.0), r=0.05)
key_energy(glow, [(1, 0.0), (d0, 0.5), (d1 + 1, 0.0)])

# ================================================================ MACRO MOUTH SET (10x, x=200): molars in gum
XT = 200.0; CT = Vector((XT, 0, 0))
m_gum = tissue("gum", base=(0.72, 0.3, 0.3), crease=(0.45, 0.12, 0.14), sss=0.5, wet=0.6, bump=0.25, scale=30, veins=0.05)


def enamel_mat(name="enamel"):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 8
    Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeValToRGB"); base.color_ramp.elements[0].color = (0.78, 0.72, 0.6, 1); base.color_ramp.elements[1].color = (0.92, 0.9, 0.84, 1)
    Lk.new(nz.outputs["Fac"], base.inputs[0])
    # decay: chalky white spots, then brown pits around the gap (keyed "DECAY" 0..1)
    dec = N.new("ShaderNodeValue"); dec.name = dec.label = "DECAY"
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 9; Lk.new(tc.outputs["Object"], vo.inputs["Vector"])
    gx = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Object"], gx.inputs[0])
    edge = N.new("ShaderNodeMapRange"); edge.inputs["From Min"].default_value = 0.2; edge.inputs["From Max"].default_value = 0.95
    ax = N.new("ShaderNodeMath"); ax.operation = "ABSOLUTE"; Lk.new(gx.outputs["X"], ax.inputs[0]); Lk.new(ax.outputs[0], edge.inputs["Value"])
    spread = N.new("ShaderNodeMath"); spread.operation = "MULTIPLY"; Lk.new(edge.outputs["Result"], spread.inputs[0]); Lk.new(dec.outputs[0], spread.inputs[1])
    thr = N.new("ShaderNodeMath"); thr.operation = "SUBTRACT"; Lk.new(spread.outputs[0], thr.inputs[0]); Lk.new(vo.outputs["Distance"], thr.inputs[1])
    chalk = N.new("ShaderNodeMath"); chalk.operation = "MULTIPLY"; chalk.inputs[1].default_value = 6; chalk.use_clamp = True; Lk.new(thr.outputs[0], chalk.inputs[0])
    pit = N.new("ShaderNodeMath"); pit.operation = "SUBTRACT"; pit.inputs[1].default_value = 0.35; Lk.new(thr.outputs[0], pit.inputs[0])
    pit2 = N.new("ShaderNodeMath"); pit2.operation = "MULTIPLY"; pit2.inputs[1].default_value = 6; pit2.use_clamp = True; Lk.new(pit.outputs[0], pit2.inputs[0])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; Lk.new(chalk.outputs[0], c1.inputs["Factor"]); Lk.new(base.outputs["Color"], c1.inputs["A"])
    c1.inputs["B"].default_value = (0.97, 0.96, 0.93, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; Lk.new(pit2.outputs[0], c2.inputs["Factor"]); Lk.new(c1.outputs["Result"], c2.inputs["A"])
    c2.inputs["B"].default_value = (0.12, 0.06, 0.02, 1)
    Lk.new(c2.outputs["Result"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMath"); rr.operation = "MULTIPLY_ADD"; rr.inputs[1].default_value = 0.55; rr.inputs[2].default_value = 0.18
    Lk.new(chalk.outputs[0], rr.inputs[0]); Lk.new(rr.outputs[0], b.inputs["Roughness"])
    b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Scale"].default_value = 0.02
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.85, 0.6)
    b.inputs["Coat Weight"].default_value = 0.5; b.inputs["Coat Roughness"].default_value = 0.05
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.invert = True
    hb = N.new("ShaderNodeMath"); hb.operation = "ADD"; Lk.new(chalk.outputs[0], hb.inputs[0]); Lk.new(pit2.outputs[0], hb.inputs[1])
    Lk.new(hb.outputs[0], bp.inputs["Height"]); Lk.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m, dec


m_enamel, DECAY = enamel_mat()


def molar(name, loc, size=0.1, seed=0):
    rnd = random.Random(seed)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.0)
    cusps = [(0.42, 0.38), (-0.42, 0.38), (0.42, -0.38), (-0.42, -0.38)]
    for v in bm.verts:
        x, y, z = v.co
        # boxy-round crown: a superellipse in plan
        r = math.hypot(x, y)
        if r > 1e-6:
            k = 1.0 + 0.18 * (abs(math.cos(2 * math.atan2(y, x))))
            x, y = x * k, y * k
        if z > 0.25:                    # biting surface: flattened with four cusps and a central groove
            h = 0.25 + (z - 0.25) * 0.35
            for cx, cy in cusps:
                h += 0.16 * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / 0.09)
            h -= 0.07 * math.exp(-(x * x) / 0.01) * (z > 0.6) - 0.0
            z = h
        if z < -0.2:                    # narrow neck going into the gum
            s_ = 1 - 0.35 * min(1, (-z - 0.2) / 0.8); x, y = x * s_, y * s_
        v.co = Vector((x * 0.5 * (1 + rnd.uniform(-0.03, 0.03)), y * 0.46, z * 0.5))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); ob.location = loc; ob.scale = (size,) * 3
    tx2 = bpy.data.textures.new(name + "_n", "CLOUDS"); tx2.noise_scale = 0.3
    d2 = ob.modifiers.new("irreg", "DISPLACE"); d2.texture = tx2; d2.strength = 0.025; d2.texture_coords = "LOCAL"
    sb = ob.modifiers.new("sub", "SUBSURF"); sb.levels = sb.render_levels = 1
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m_enamel)
    return ob


teeth = [molar(f"molar{k}", CT + Vector((k * 0.105 - 0.105, 0, 0)), 0.1, k) for k in range(3)]
# the cavity pit grows in the side of the middle molar facing the gap (keyed displacement)
mid_t = teeth[1]
pit_tx = bpy.data.textures.new("pit", "BLEND"); pit_tx.progression = "SPHERICAL"
pit_e = link(bpy.data.objects.new("pit_center", None)); pit_e.location = CT + Vector((0.048, -0.01, 0.025)); pit_e.scale = (0.05, 0.05, 0.05)
pd = mid_t.modifiers.new("pit", "DISPLACE"); pd.texture = pit_tx; pd.texture_coords = "OBJECT"; pd.texture_coords_object = pit_e
pd.direction = "NORMAL"; pd.mid_level = 0.0; pd.strength = 0.0
for f, v in ((1, 0.0), (RANGE["melt"][0], 0.0), (RANGE["melt"][1], -0.028)):
    pd.strength = v; pd.keyframe_insert("strength", frame=f)
for f, v in ((1, 0.0), (RANGE["acid"][0], 0.0), (RANGE["morning"][1], 0.25), (RANGE["saliva"][1], 0.55), (RANGE["melt"][1], 1.0)):
    DECAY.outputs[0].default_value = v; DECAY.outputs[0].keyframe_insert("default_value", frame=f)
# gum around the base
gum = soft_box("gum", (XT, 0, -0.06), (0.24, 0.09, 0.04), m_gum, levels=3, cast=0.3, wrinkle=0.006, wscale=0.03)
# a gummy chunk wedged between the first two molars
gchunk = link(bpy.data.objects.new("gummy_chunk", bpy.data.meshes.new("gummy_chunk")))
bmc = bmesh.new(); bmesh.ops.create_icosphere(bmc, subdivisions=4, radius=1.0); bmc.to_mesh(gchunk.data); bmc.free()
for p in gchunk.data.polygons:
    p.use_smooth = True
gchunk.data.materials.append(GUM_MATS[0]); gchunk.location = CT + Vector((0.052, 0, 0.026)); gchunk.scale = (0.011, 0.024, 0.015)
gtx = bpy.data.textures.new("chunk_n", "CLOUDS"); gtx.noise_scale = 0.4
dch = gchunk.modifiers.new("lumps", "DISPLACE"); dch.texture = gtx; dch.strength = 0.25
# saliva film: a clear wet shell over the teeth that dries up overnight
m_saliva = bpy.data.materials.new("saliva"); m_saliva.use_nodes = True; sn_ = m_saliva.node_tree.nodes; sl_ = m_saliva.node_tree.links
sn_.remove(sn_["Principled BSDF"])
_tr = sn_.new("ShaderNodeBsdfTransparent"); _gl = sn_.new("ShaderNodeBsdfGlossy"); _gl.inputs["Roughness"].default_value = 0.02
_fr = sn_.new("ShaderNodeFresnel"); _fr.inputs["IOR"].default_value = 1.33; _mx = sn_.new("ShaderNodeMixShader")
sl_.new(_fr.outputs[0], _mx.inputs[0]); sl_.new(_tr.outputs[0], _mx.inputs[1]); sl_.new(_gl.outputs[0], _mx.inputs[2])
sl_.new(_mx.outputs[0], sn_["Material Output"].inputs["Surface"])
for k, t in enumerate(teeth):
    sh = t.copy(); sh.data = t.data.copy(); S.collection.objects.link(sh); sh.name = f"saliva{k}"
    sh.scale = tuple(v * 1.03 for v in t.scale); sh.data.materials.clear(); sh.data.materials.append(m_saliva)
    for m_ in list(sh.modifiers):
        if m_.type == "DISPLACE" and m_.name == "pit":
            sh.modifiers.remove(m_)
    show_only(sh, [(1, F(19.6))])
# bacteria swarming the gummy (capsules, purple), multiplying through the acid shots
m_bac = bpy.data.materials.new("bacteria"); m_bac.use_nodes = True; bb_ = m_bac.node_tree.nodes["Principled BSDF"]
bb_.inputs["Base Color"].default_value = (0.5, 0.55, 0.2, 1); bb_.inputs["Roughness"].default_value = 0.3
bb_.inputs["Subsurface Weight"].default_value = 0.5; bb_.inputs["Subsurface Scale"].default_value = 0.003
bb_.inputs["Coat Weight"].default_value = 0.6; bb_.inputs["Coat Roughness"].default_value = 0.1
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
for v in bm.verts:
    v.co.z = v.co.z + (1.8 if v.co.z > 0 else -1.8)
bac_me = bpy.data.meshes.new("bac"); bm.to_mesh(bac_me); bm.free(); bac_me.materials.append(m_bac)
for p in bac_me.polygons:
    p.use_smooth = True
rnd = random.Random(4)
dg = bpy.context.evaluated_depsgraph_get()
bact_objs = []
for k in range(600):
    b = link(bpy.data.objects.new(f"bac{k}", bac_me))
    r_ = rnd.uniform(0.00035, 0.0006); b.scale = (r_, r_, r_)
    tgt = CT + Vector((0.052 + rnd.gauss(0, 0.018), rnd.uniform(-0.035, 0.035), 0.09))
    hit, loc, nrm, *_ = S.ray_cast(dg, tgt, Vector((0, 0, -1)))
    p = loc + nrm * 0.0008 if hit else tgt
    b.location = p; b.rotation_euler = (math.radians(90 + rnd.uniform(-20, 20)), 0, rnd.uniform(0, 6.28))
    b.keyframe_insert("location", frame=1); b.keyframe_insert("rotation_euler", frame=1)
    for fc in fcurves(b):
        nmod = fc.modifiers.new("NOISE"); nmod.scale = rnd.uniform(5, 12); nmod.phase = rnd.uniform(0, 100)
        nmod.strength = 0.25 if "rotation" in fc.data_path else 0.002
    f_on = RANGE["bact"][0] + int(k * 0.08)          # they keep arriving
    show_only(b, [(min(f_on, RANGE["melt"][1]), RANGE["melt"][1])])
# acid: yellow-green droplets oozing out onto the enamel, with tiny bubbles
m_acid = liquid("acid", tint=(0.8, 1.0, 0.3), density=0.15, rough=0.02, glow=0.4)
for k in range(26):
    d = link(bpy.data.objects.new(f"acid{k}", bpy.data.meshes.new(f"acid{k}")))
    bmd = bmesh.new(); bmesh.ops.create_uvsphere(bmd, u_segments=20, v_segments=10, radius=1.0); bmd.to_mesh(d.data); bmd.free()
    for p in d.data.polygons:
        p.use_smooth = True
    d.data.materials.append(m_acid)
    tgt = CT + Vector((0.052 + rnd.gauss(0, 0.028), rnd.uniform(-0.045, 0.045), 0.09))
    hit, loc, nrm, *_ = S.ray_cast(dg, tgt, Vector((0, 0, -1)))
    d.location = loc if hit else tgt
    f0 = RANGE["acid"][0] + rnd.randint(0, 30); r_ = rnd.uniform(0.003, 0.007)
    d.scale = (0.0001,) * 3; d.keyframe_insert("scale", frame=f0)
    d.scale = (r_, r_, r_ * 0.45); d.keyframe_insert("scale", frame=f0 + 18)
    show_only(d, [(f0, RANGE["melt"][1])])
mlk = area("mouth_key", CT + Vector((0.25, -0.4, 0.45)), CT, 3.0, 0.4, (1.0, 0.92, 0.85))
mfl = area("mouth_fill", CT + Vector((-0.4, -0.25, 0.15)), CT, 1.2, 0.5, (0.85, 0.9, 1.0))
key_energy(mlk, [(1, 3.0), (RANGE["morning"][0], 1.0), (RANGE["demo"][0], 3.0), (RANGE["saliva"][0], 1.6)])
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.5); bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("mouth_bg"); bm.to_mesh(me); bm.free()
me.materials.append(tissue("mouth_wall", base=(0.28, 0.06, 0.06), crease=(0.12, 0.02, 0.03), sss=0.4, wet=0.3, bump=0.3, scale=12, veins=0.0))
link(bpy.data.objects.new("mouth_bg", me)).location = CT

# ================================================================ TOOTH CUTAWAY (x=230): enamel / dentin / pulp, the hole reaches the nerve
XC = 230.0; CC = Vector((XC, 0, 0))
OUTLINE = [(-0.95, 0.55), (-0.85, 0.85), (-0.55, 1.0), (-0.3, 0.88), (0.0, 0.8), (0.3, 0.88), (0.55, 1.0), (0.85, 0.85),
           (0.95, 0.55), (0.9, 0.2), (0.75, 0.0), (0.72, -0.4), (0.62, -1.0), (0.5, -1.55), (0.38, -1.62), (0.28, -1.2),
           (0.15, -0.55), (0.0, -0.4), (-0.15, -0.55), (-0.28, -1.2), (-0.38, -1.62), (-0.5, -1.55), (-0.62, -1.0),
           (-0.72, -0.4), (-0.75, 0.0), (-0.9, 0.2)]
def profile(scale_xy, z_top):
    return [Vector((x * scale_xy, 0, min(z * scale_xy, z_top))) for x, z in OUTLINE]
def slab(name, pts, depth, m, yoff):
    bm = bmesh.new(); front = [bm.verts.new(p + Vector((0, yoff, 0))) for p in pts]; back = [bm.verts.new(p + Vector((0, yoff + depth, 0))) for p in pts]
    bm.faces.new(front[::-1]); bm.faces.new(back)
    for i in range(len(pts)):
        j = (i + 1) % len(pts); bm.faces.new((front[i], front[j], back[j], back[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    ob = link(bpy.data.objects.new(name, me)); ob.location = CC
    s = ob.modifiers.new("sub", "SUBSURF"); s.levels = s.render_levels = 2
    bvl = ob.modifiers.new("bev", "BEVEL"); bvl.width = 0.003; bvl.segments = 3
    with bpy.context.temp_override(object=ob):
        bpy.ops.object.modifier_move_to_index(modifier="bev", index=0)
    return ob
m_dentin = mat("dentin", (0.85, 0.7, 0.42), rough=0.45, sss=0.3)
m_pulp = mat("pulp", (0.7, 0.08, 0.08), rough=0.4, sss=0.5, emit=0.0)
slab("cut_enamel", profile(0.2, 1.0), 0.05, m_enamel, 0.0)
slab("cut_dentin", [Vector((p.x * 0.86, 0, p.z * 0.9 - 0.012)) for p in profile(0.2, 1.0)], 0.05, m_dentin, -0.002)
pulp_pts = [Vector((p.x * 0.42, 0, p.z * 0.62 - 0.02)) for p in profile(0.2, 1.0)]
pulp = slab("cut_pulp", pulp_pts, 0.05, m_pulp, -0.004)
pb_ = m_pulp.node_tree.nodes["Principled BSDF"]; pb_.inputs["Emission Color"].default_value = (1.0, 0.1, 0.05, 1)
NERVE_T = F(27.6)
for f, v in ((1, 0.0), (NERVE_T - 1, 0.0), (NERVE_T + 3, 6.0), (NERVE_T + 12, 2.5), (RANGE["cutaway"][1], 4.0)):
    pb_.inputs["Emission Strength"].default_value = v; pb_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
# the hole: a dark eroded channel from the crown down toward the pulp
hole = link(bpy.data.objects.new("cavity", bpy.data.meshes.new("cavity")))
bmh = bmesh.new(); bmesh.ops.create_icosphere(bmh, subdivisions=3, radius=1.0); bmh.to_mesh(hole.data); bmh.free()
for p in hole.data.polygons:
    p.use_smooth = True
hole.data.materials.append(mat("cavity", (0.06, 0.03, 0.012), rough=0.8))
htx = bpy.data.textures.new("cav_n", "CLOUDS"); htx.noise_scale = 0.3
dh = hole.modifiers.new("ragged", "DISPLACE"); dh.texture = htx; dh.strength = 0.35
top = CC + Vector((0.025, -0.006, 0.175))
for f, depth in ((RANGE["cutaway"][0], 0.025), (F(26.3), 0.06), (NERVE_T, 0.105), (RANGE["cutaway"][1], 0.11)):
    hole.location = top - Vector((0, 0, depth / 2)); hole.keyframe_insert("location", frame=f)
    hole.scale = (0.02, 0.012, depth / 2); hole.keyframe_insert("scale", frame=f)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=2.0); bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("cut_bg"); bm.to_mesh(me); bm.free(); me.materials.append(mat("cut_bg", (0.015, 0.012, 0.02), rough=0.9))
link(bpy.data.objects.new("cut_bg", me)).location = CC
area("cut_key", CC + Vector((0.3, -0.7, 0.4)), CC, 6, 0.6, (1.0, 0.95, 0.9))
area("cut_rim", CC + Vector((-0.4, 0.5, 0.3)), CC, 4, 0.6, (0.6, 0.75, 1.0))

# ================================================================ HOSPITAL: little pulled teeth in the kidney tray (x=80, 10x)
XTR = 80.0
for k in range(8):
    t = molar(f"baby_tooth{k}", Vector((XTR + random.uniform(-0.25, 0.2), random.uniform(-0.12, 0.14), 0.045)), 0.11, 50 + k)
    t.rotation_euler = (random.uniform(0, 3.14), random.uniform(0, 3.14), random.uniform(0, 6.28))
    root = link(bpy.data.objects.new(f"baby_root{k}", bpy.data.meshes.new(f"baby_root{k}")))
    bmr = bmesh.new(); bmesh.ops.create_cone(bmr, cap_ends=True, segments=10, radius1=0.014, radius2=0.004, depth=0.05); bmr.to_mesh(root.data); bmr.free()
    root.data.materials.append(m_dentin); root.parent = t; root.location = (0, 0, -0.45); root.scale = (6, 6, 6)
m_blood = mat("blood_gauze", (0.55, 0.03, 0.03), rough=0.5, sss=0.4)
gauze, _ = img_mat("gauze", os.path.join(ROOT, "assets", "tex", "cotton_jersey"), tint=(0.95, 0.95, 0.95), scale=3, bump=0.9)
gz = soft_box("gauze_pad", (XTR - 0.35, 0.12, 0.02), (0.14, 0.11, 0.012), gauze, levels=2, cast=0.2, wrinkle=0.01, wscale=0.05)
spot = link(bpy.data.objects.new("blood_spot", bpy.data.meshes.new("blood_spot")))
bms = bmesh.new(); bmesh.ops.create_circle(bms, cap_ends=True, segments=32, radius=1.0); bms.to_mesh(spot.data); bms.free()
spot.data.materials.append(m_blood); spot.location = (XTR - 0.34, 0.11, 0.0335); spot.scale = (0.05, 0.035, 1)

# ================================================================ CAMERAS + CUTS
c_bed, a_bed = camera("C01_bed", HEAD + Vector((0.45, -0.85, 0.65)), (HEAD + MOUTH) / 2 + Vector((0, -0.05, -0.02)), lens=32, fstop=3.5)
key(c_bed, "location", RANGE["bed"][0], c_bed.location.copy()); key(c_bed, "location", RANGE["bed"][1], MOUTH + Vector((0.12, -0.3, 0.25)))
key(a_bed, "location", RANGE["bed"][0], a_bed.location.copy()); key(a_bed, "location", RANGE["bed"][1], MOUTH)
c_t, a_t = camera("C02_teeth", CT + Vector((0.12, -0.3, 0.22)), CT + Vector((0.04, 0, 0.04)), lens=45, fstop=5.6, clip=0.005)
key(c_t, "location", RANGE["teeth"][0], c_t.location.copy()); key(c_t, "location", RANGE["teeth"][1], CT + Vector((0.1, -0.24, 0.17)))
c_b, a_b = camera("C03_bact", CT + Vector((0.09, -0.11, 0.13)), CT + Vector((0.052, 0, 0.05)), lens=60, fstop=4.0, clip=0.003)
key(c_b, "location", RANGE["bact"][0], c_b.location.copy()); key(c_b, "location", RANGE["bact"][1], CT + Vector((0.075, -0.08, 0.1)))
c_a, a_a = camera("C04_acid", CT + Vector((0.0, -0.12, 0.1)), CT + Vector((0.045, 0, 0.04)), lens=60, fstop=4.0, clip=0.003)
c_m, a_m = camera("C05_morning", CT + Vector((-0.1, -0.35, 0.12)), CT + Vector((0.04, 0, 0.03)), lens=50, fstop=5.6, clip=0.005)
key(c_m, "location", RANGE["morning"][0], c_m.location.copy()); key(c_m, "location", RANGE["morning"][1], CT + Vector((-0.03, -0.17, 0.08)))
c_d, a_d = camera("C06_demo", phone.location + Vector((0.08, -0.12, 0.2)), phone.location, lens=40, fstop=2.8)
key(c_d, "location", RANGE["demo"][0], c_d.location.copy()); key(c_d, "location", RANGE["demo"][1], phone.location + Vector((0.035, -0.06, 0.2)))
c_s, a_s = camera("C07_saliva", CT + Vector((0.2, -0.28, 0.1)), CT + Vector((0.02, 0, 0.02)), lens=45, fstop=5.6, clip=0.005)
key(c_s, "location", RANGE["saliva"][0], c_s.location.copy()); key(c_s, "location", RANGE["saliva"][1], CT + Vector((0.14, -0.22, 0.08)))
c_me, a_me = camera("C08_melt", CT + Vector((0.11, -0.12, 0.08)), CT + Vector((0.05, -0.01, 0.025)), lens=60, fstop=4.0, clip=0.003)
key(c_me, "location", RANGE["melt"][0], c_me.location.copy()); key(c_me, "location", RANGE["melt"][1], CT + Vector((0.09, -0.09, 0.06)))
c_c, a_c = camera("C09_cutaway", CC + Vector((0.0, -0.95, -0.03)), CC + Vector((0, 0, -0.04)), lens=50, fstop=11, clip=0.01)
key(c_c, "location", RANGE["cutaway"][0], c_c.location.copy()); key(c_c, "location", RANGE["cutaway"][1], CC + Vector((0.0, -0.8, -0.02)))
c_h, a_h = camera("C10_hospital", Vector((XTR - 0.2, -0.5, 0.42)), Vector((XTR - 0.08, 0.0, 0.03)), lens=45, fstop=2.8)
key(c_h, "location", RANGE["hospital"][0], c_h.location.copy()); key(c_h, "location", RANGE["hospital"][1], Vector((XTR - 0.17, -0.4, 0.34)))
c_e, a_e = camera("C11_end", bag.location + Vector((0.15, -0.25, 0.2)), bag.location + Vector((0, 0.05, 0.02)), lens=40, fstop=3.5)
key(c_e, "location", RANGE["end"][0], c_e.location.copy()); key(c_e, "location", RANGE["end"][1], HEAD + Vector((0.45, -0.85, 0.65)))
key(a_e, "location", RANGE["end"][0], a_e.location.copy()); key(a_e, "location", RANGE["end"][1], (HEAD + MOUTH) / 2 + Vector((0, -0.05, -0.02)))
for nm, cam in (("bed", c_bed), ("teeth", c_t), ("bact", c_b), ("acid", c_a), ("morning", c_m), ("demo", c_d), ("saliva", c_s),
                ("melt", c_me), ("cutaway", c_c), ("hospital", c_h), ("end", c_e)):
    cut(T[nm], cam)
S.camera = c_bed
for cam in CAMS.values():
    set_interp(cam, "BEZIER")
out = os.path.join(ROOT, "scenes", "candy", "candy.blend")
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("CANDY READY", out, S.frame_end, RANGE)
