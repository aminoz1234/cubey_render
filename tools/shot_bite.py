"""Realistic proof shot: a man bites a watermelon slice, chews and swallows the seed.
Needs scenes/real/man.blend (MPFB2 human, CC0) and assets/hdri/comfy_cafe_2k.hdr. Blender 5.2+, Cycles."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else os.getcwd()
exec(open(os.path.join(ROOT, "tools", "realism.py")).read())
FPS = 30
S = bpy.context.scene
S.render.fps = FPS
S.frame_start, S.frame_end = 1, 96
cycles_quality(S, samples=96, res=(1080, 1920))
S.view_settings.look = "AgX - Base Contrast"

rig = bpy.data.objects["Man"]
body = bpy.data.objects["Man.body"]
pb = rig.pose.bones
def bone_world(name, tail=False):
    b = rig.data.bones[name]
    return rig.matrix_world @ (b.tail_local if tail else b.head_local)

# ---------------------------------------------------------------- eyes: iris texture + clear cornea
EYE_TEX = None
for base in ("/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/eyes/materials/brown_eye.png",):
    if os.path.exists(base):
        EYE_TEX = base
eyes = bpy.data.objects.get("Man.high-poly")
if eyes and EYE_TEX:
    img = bpy.data.images.load(EYE_TEX, check_existing=True); img.pack()
    m = bpy.data.materials.new("eye_iris"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    tx = m.node_tree.nodes.new("ShaderNodeTexImage"); tx.image = img
    m.node_tree.links.new(tx.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.1; p.inputs["Coat Weight"].default_value = 1.0; p.inputs["Coat Roughness"].default_value = 0.0
    c = bpy.data.materials.new("eye_cornea"); c.use_nodes = True; cn = c.node_tree.nodes; cl = c.node_tree.links
    cn.remove(cn["Principled BSDF"])
    tr_ = cn.new("ShaderNodeBsdfTransparent"); gl = cn.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.0
    fr = cn.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.376; mx_ = cn.new("ShaderNodeMixShader")
    cl.new(fr.outputs[0], mx_.inputs[0]); cl.new(tr_.outputs[0], mx_.inputs[1]); cl.new(gl.outputs[0], mx_.inputs[2])
    cl.new(mx_.outputs[0], cn["Material Output"].inputs["Surface"])
    me = eyes.data; me.materials.clear(); me.materials.append(m); me.materials.append(c)
    bm = bmesh.new(); bm.from_mesh(me); seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]; comp = []; seen.add(f.index)
        while stack:
            x = stack.pop(); comp.append(x)
            for e in x.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index); stack.append(g)
        vs = {v for q in comp for v in q.verts}
        for q in comp:
            q.material_index = 1 if len(vs) == 256 else 0
    bm.to_mesh(me); bm.free()

# ---------------------------------------------------------------- skin: add pores and a faint oily sheen on top of MPFB's SSS skin
for ms in body.material_slots:
    mt = ms.material
    if not mt or not mt.use_nodes:
        continue
    for n in mt.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            nt = mt.node_tree
            nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 4
            vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1400
            mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"
            nt.links.new(nz.outputs["Fac"], mx.inputs[0]); nt.links.new(vor.outputs["Distance"], mx.inputs[1])
            bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.0005
            nt.links.new(mx.outputs["Value"], bp.inputs["Height"])
            if not n.inputs["Normal"].is_linked:
                nt.links.new(bp.outputs["Normal"], n.inputs["Normal"])
            n.inputs["Coat Weight"].default_value = 0.0
            if not n.inputs["Roughness"].is_linked:
                n.inputs["Roughness"].default_value = 0.5

hair = bpy.data.objects.get("Man.short02")
if hair:
    for ms in hair.material_slots:
        for n in (ms.material.node_tree.nodes if ms.material and ms.material.use_nodes else []):
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Roughness"].default_value = 0.65
                for k in ("Coat Weight", "Specular IOR Level"):
                    if not n.inputs[k].is_linked: n.inputs[k].default_value = 0.1 if k == "Coat Weight" else 0.3

# ---------------------------------------------------------------- watermelon slice (tip toward the mouth)
R, TH, HALF = 0.12, 0.028, math.radians(24)
bm = bmesh.new()
tip_top, tip_bot = bm.verts.new((0, 0, TH / 2)), bm.verts.new((0, 0, -TH / 2))
arc_t, arc_b = [], []
for i in range(25):
    a = -HALF + 2 * HALF * i / 24
    arc_t.append(bm.verts.new((R * math.cos(a), R * math.sin(a), TH / 2)))
    arc_b.append(bm.verts.new((R * math.cos(a), R * math.sin(a), -TH / 2)))
bm.faces.new([tip_top] + arc_t); bm.faces.new([tip_bot] + arc_b[::-1])
for i in range(24):
    bm.faces.new((arc_t[i], arc_b[i], arc_b[i + 1], arc_t[i + 1]))
bm.faces.new((tip_top, tip_bot, arc_b[0], arc_t[0])); bm.faces.new((tip_top, arc_t[-1], arc_b[-1], tip_bot))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("melon"); bm.to_mesh(me); bm.free()
melon = bpy.data.objects.new("melon_slice", me); S.collection.objects.link(melon)
sub = melon.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 3; sub.subdivision_type = "SIMPLE"
bev = melon.modifiers.new("bevel", "BEVEL"); bev.width = 0.002; bev.segments = 3
dsp = melon.modifiers.new("cells", "DISPLACE"); dtx = bpy.data.textures.new("melon_cells", "VORONOI"); dtx.noise_scale = 0.006
dsp.texture = dtx; dsp.strength = 0.0012; dsp.texture_coords = "OBJECT"
for p in me.polygons:
    p.use_smooth = True
# shader: flesh -> pale rind -> green striped skin, by distance from the tip
m = bpy.data.materials.new("watermelon"); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
cmb = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs["X"], cmb.inputs["X"]); L.new(sep.outputs["Y"], cmb.inputs["Y"])
ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(cmb.outputs[0], ln.inputs[0])
div = N.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = R; L.new(ln.outputs["Value"], div.inputs[0])
ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "B_SPLINE"
cols = [(0.0, (0.5, 0.008, 0.02)), (0.66, (0.62, 0.015, 0.03)), (0.8, (0.85, 0.35, 0.3)), (0.86, (0.86, 0.9, 0.7)), (0.93, (0.55, 0.75, 0.35)), (0.97, (0.08, 0.28, 0.05))]
cr.elements[0].position, cr.elements[0].color = cols[0][0], (*cols[0][1], 1)
cr.elements[1].position, cr.elements[1].color = cols[-1][0], (*cols[-1][1], 1)
for pos, c in cols[1:-1]:
    e = cr.elements.new(pos); e.color = (*c, 1)
L.new(div.outputs[0], ramp.inputs[0])
# dark green stripes on the outer skin
wav = N.new("ShaderNodeTexWave"); wav.wave_type = "BANDS"; wav.bands_direction = "Z"; wav.inputs["Scale"].default_value = 3
wav.inputs["Distortion"].default_value = 8; wav.inputs["Detail"].default_value = 4
L.new(tc.outputs["Object"], wav.inputs["Vector"])
skinmask = N.new("ShaderNodeMapRange"); skinmask.inputs["From Min"].default_value = 0.94; skinmask.inputs["From Max"].default_value = 0.97
L.new(div.outputs[0], skinmask.inputs["Value"])
stripe = N.new("ShaderNodeMix"); stripe.data_type = "RGBA"; stripe.blend_type = "MULTIPLY"
L.new(skinmask.outputs["Result"], stripe.inputs["Factor"]); L.new(ramp.outputs["Color"], stripe.inputs["A"]); L.new(wav.outputs["Color"], stripe.inputs["B"])
L.new(stripe.outputs["Result"], b.inputs["Base Color"])
fleshmask = N.new("ShaderNodeMapRange"); fleshmask.inputs["From Min"].default_value = 0.82; fleshmask.inputs["From Max"].default_value = 0.72
L.new(div.outputs[0], fleshmask.inputs["Value"])
sssw = N.new("ShaderNodeMath"); sssw.operation = "MULTIPLY"; sssw.inputs[1].default_value = 0.35
L.new(fleshmask.outputs["Result"], sssw.inputs[0]); L.new(sssw.outputs[0], b.inputs["Subsurface Weight"])
b.inputs["Subsurface Radius"].default_value = (1.0, 0.05, 0.04); b.inputs["Subsurface Scale"].default_value = 0.01
b.inputs["Roughness"].default_value = 0.3
wet = N.new("ShaderNodeMath"); wet.operation = "MULTIPLY"; wet.inputs[1].default_value = 0.9
L.new(fleshmask.outputs["Result"], wet.inputs[0]); L.new(wet.outputs[0], b.inputs["Coat Weight"])
b.inputs["Coat Roughness"].default_value = 0.05
# juicy crystalline cells
vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 260; L.new(tc.outputs["Object"], vor.inputs["Vector"])
vb = N.new("ShaderNodeBump"); vb.inputs["Strength"].default_value = 0.35; vb.inputs["Distance"].default_value = 0.0008
L.new(vor.outputs["Distance"], vb.inputs["Height"]); L.new(vb.outputs["Normal"], b.inputs["Normal"])
me.materials.append(m)
# seeds in an arc, half-buried on both faces
seedmat = glossy_seed("seed_mat")
seeds = []
for face in (1, -1):
    for i in range(7):
        a = -HALF * 0.75 + 1.5 * HALF * i / 6; r = 0.085 + 0.012 * ((i % 2) * 2 - 1)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(r * math.cos(a), r * math.sin(a), face * TH / 2 * 0.85))
        sd = bpy.context.object; sd.name = f"seed{face}_{i}"; sd.scale = (0.0045, 0.0028, 0.0016)
        sd.rotation_euler = (0, 0, a); sd.data.materials.append(seedmat)
        for p in sd.data.polygons:
            p.use_smooth = True
        sd.parent = melon; seeds.append(sd)
# bite cutter (enabled at the moment of the bite)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(0.0, 0, 0))
cutter = bpy.context.object; cutter.name = "bite_cutter"; cutter.scale = (0.045, 0.03, 0.05); cutter.parent = melon
cutter.hide_render = True; cutter.display_type = "WIRE"
bo = melon.modifiers.new("bite", "BOOLEAN"); bo.object = cutter; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
melon.modifiers.move(len(melon.modifiers) - 1, 0)
for sd in seeds:  # seeds inside the bite disappear with it
    if (Vector(sd.location[:2]).length < 0.05):
        sd.hide_render = True

# ---------------------------------------------------------------- choreography
mouth = (bone_world("oris01") + bone_world("oris05")) / 2 if "oris05" in rig.data.bones else bone_world("oris01")
headpos = bone_world("head")
mouth = mouth + Vector((0, 0, -0.022))  # aim at the gap between the lips
face_dir = Vector((0.6, -0.8, 0)).normalized()  # comes in from his left, flesh side faces the camera

def place(f, dist, drop, tilt=0.0):
    """Slice tip `dist` m in front of the mouth, `drop` m below it, pointing at the mouth."""
    loc = mouth + face_dir * dist + Vector((0.0, 0, -drop))
    rot = Matrix.Rotation(math.radians(-53), 4, "Z") @ Matrix.Rotation(math.radians(90 + tilt), 4, "X")
    melon.matrix_world = Matrix.Translation(loc) @ rot
    melon.keyframe_insert("location", frame=f); melon.keyframe_insert("rotation_euler", frame=f)

place(1, 0.22, 0.16, -20)
place(16, 0.06, 0.01, -8)
place(24, -0.012, 0.0, -4)      # tip between the teeth
place(30, 0.0, 0.0, -4)
place(42, 0.2, 0.2, -25)        # pulled away and down, bite mark visible
place(96, 0.32, 0.35, -30)
bo.show_render = False; bo.show_viewport = False
bo.keyframe_insert("show_render", frame=1); bo.keyframe_insert("show_viewport", frame=1)
bo.show_render = True; bo.show_viewport = True
bo.keyframe_insert("show_render", frame=28); bo.keyframe_insert("show_viewport", frame=28)

def jaw(f, open_deg, side=0.0):
    pb["jaw"].rotation_mode = "XYZ"; pb["jaw"].rotation_euler = (math.radians(open_deg), 0, math.radians(side))
    pb["jaw"].keyframe_insert("rotation_euler", frame=f)

def head(f, pitch=0.0, yaw=0.0, roll=0.0):
    for bn, k in (("head", 0.6), ("neck02", 0.4)):
        pb[bn].rotation_mode = "XYZ"; pb[bn].rotation_euler = (math.radians(pitch * k), math.radians(roll * k), math.radians(yaw * k))
        pb[bn].keyframe_insert("rotation_euler", frame=f)

JAW_SIGN = float(os.environ.get("JAW_SIGN", "1"))
for f, d in [(1, 0), (10, 4), (20, 17), (25, 17), (29, 2), (36, 3), (44, 7), (50, 1), (56, 7), (62, 1), (68, 6), (74, 0), (96, 0)]:
    jaw(f, d * JAW_SIGN, side=(2.5 if f in (44, 68) else -2.5 if f == 56 else 0))
head(1, 0, 6, 0); head(20, 6, 3, -2); head(29, 9, 2, -2); head(44, -2, 5, 1); head(76, -3, 4, 0)
head(82, 6, 4, 0)   # swallow: chin dips
head(90, -4, 4, 0); head(96, -3, 5, 0)
# swallow: Adam's apple rises and falls (neck01 nudges up)
for f, z in [(76, 0.0), (82, 0.006), (88, 0.0)]:
    pb["neck01"].location = (0, z, 0); pb["neck01"].keyframe_insert("location", frame=f)
# blinks
for f0 in (12, 58):
    for bn in ("special05.L", "special05.R"):
        pass


# ---------------------------------------------------------------- real set pieces (Poly Haven, CC0) behind him, out of focus
def import_model(mid, loc, rot_z=0.0, scale=1.0):
    path = os.path.join(ROOT, "assets", "models", mid, mid + "_1k.gltf")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(mid + "_root", None); S.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot_z)); root.scale = (scale,) * 3
    bpy.context.view_layer.update()
    top = max((o.matrix_world @ Vector(c)).z for o in new if o.type == "MESH" for c in o.bound_box)
    return root, top

table, ttop = import_model("dining_table", Vector((0.35, 1.25, 0)), 90)
import_model("dining_chair_02", Vector((0.95, 0.75, 0)), 200)
import_model("potted_plant_02", Vector((-0.85, 1.0, 0)), 30, 1.3)
import_model("jug_01", Vector((0.15, 1.15, ttop)), 0)
import_model("carved_wooden_plate", Vector((0.55, 1.05, ttop)), 0)
for k, (dx, dy) in enumerate(((0.5, 1.0), (0.6, 1.1), (0.47, 1.12))):
    import_model("food_lime_01", Vector((dx, dy, ttop + 0.02)), k * 40)
for f in range(1, 1):
    pass

# ---------------------------------------------------------------- lights, world, camera
w = bpy.data.worlds.new("cafe"); S.world = w; w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(ROOT, "assets", "hdri", "comfy_cafe_4k.hdr")); env.image.pack()
mp = w.node_tree.nodes.new("ShaderNodeMapping"); tcw = w.node_tree.nodes.new("ShaderNodeTexCoord")
mp.inputs["Rotation"].default_value = (0, 0, math.radians(355))
w.node_tree.links.new(tcw.outputs["Generated"], mp.inputs["Vector"]); w.node_tree.links.new(mp.outputs[0], env.inputs["Vector"])
w.node_tree.links.new(env.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

def area(name, loc, target, energy, size, col):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size; d.color = col; d.shape = "DISK"
    ob = bpy.data.objects.new(name, d); S.collection.objects.link(ob); ob.location = loc
    tr = ob.constraints.new("TRACK_TO"); e = bpy.data.objects.new(name + "_t", None); S.collection.objects.link(e); e.location = target
    tr.target = e; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    return ob

area("key", headpos + Vector((-0.9, -1.0, 0.7)), headpos, 45, 1.0, (1.0, 0.92, 0.82))
area("rim", headpos + Vector((0.9, 0.9, 0.5)), headpos, 30, 1.6, (0.85, 0.92, 1.0))
area("fill", headpos + Vector((0.9, -1.2, -0.2)), headpos, 6, 1.5, (1.0, 0.9, 0.85))

cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam_bite", cd); S.collection.objects.link(cam)
cam.location = mouth + Vector((-0.24, -0.5, -0.02))
focus = bpy.data.objects.new("focus", None); S.collection.objects.link(focus); focus.location = mouth + Vector((0, -0.02, 0.01))
tr = cam.constraints.new("TRACK_TO"); tr.target = focus; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
macro_cam(cam, focus, fstop=2.8, lens=85)
cam.keyframe_insert("location", frame=1)
cam.location = mouth + Vector((-0.2, -0.44, -0.03)); cam.keyframe_insert("location", frame=96)
S.camera = cam
print("SHOT READY", tuple(round(x, 3) for x in mouth))
