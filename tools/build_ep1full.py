"""Episode 1 'The Soda Swap': full 41 s shot. python3 build_ep1full.py OUT.blend PUPDIR
PUPDIR holds <who>/head/####.webp (per-frame faces) and headmeta.json; rig art comes from kit/ep1/rig."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "build_ep1full_base.py")).read())
from mathutils import Matrix, Euler
FPS = 30
F = lambda t: int(round(t * FPS)) + 1                     # seconds -> frame

def key(o, path, val, f):
    setattr(o, path, val); o.keyframe_insert(path, frame=f)

# ------------------------------------------------------------ breakfast table props
def mmat(name, col, rough=0.45, emit=0.0, trans=0.0, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if alpha is not None: b.inputs["Alpha"].default_value = alpha
    return m
def obj_from(op, name, **kw):
    op(**kw); o = bpy.context.active_object; o.name = name; return o
def bevel(o, w, seg=3):
    b = o.modifiers.new("bev", "BEVEL"); b.width = w; b.segments = seg; b.limit_method = "ANGLE"; return o
def smooth(o): bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_smooth(); return o

WHITE = mmat("cube_m", (0.97, 0.96, 0.93), 0.55)
def sugar_cube(name, loc):
    o = obj_from(bpy.ops.mesh.primitive_cube_add, name, size=0.07, location=loc); o.data.materials.append(WHITE); bevel(o, 0.008, 2); o["kit"] = "cubes"; return o
def soda_can(name):
    o = obj_from(bpy.ops.mesh.primitive_cylinder_add, name, radius=0.062, depth=0.2, vertices=48, location=(0, 0, 0)); smooth(o)
    o.data.materials.append(mmat("can_red", (0.78, 0.04, 0.05), 0.25)); bevel(o, 0.006)
    band = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_band", radius=0.0625, depth=0.05, vertices=48, location=(0, 0, 0.02)); smooth(band)
    band.data.materials.append(mmat("can_band", (0.96, 0.95, 0.92), 0.3)); band.parent = o
    top = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_top", radius=0.055, depth=0.012, vertices=40, location=(0, 0, 0.1)); top.data.materials.append(mmat("can_top", (0.75, 0.76, 0.78), 0.2)); top.parent = o
    return o
def juice_glass(name):
    g = obj_from(bpy.ops.mesh.primitive_cylinder_add, name, radius=0.07, depth=0.21, vertices=48, location=(0, 0, 0)); smooth(g)
    g.data.materials.append(mmat("glass_m", (0.02, 0.02, 0.025), 0.05, alpha=0.1)); sol = g.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.006
    import bmesh; bm = bmesh.new(); bm.from_mesh(g.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if len(f.verts) > 4], context="FACES"); bm.to_mesh(g.data); bm.free()
    g.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.6
    j = obj_from(bpy.ops.mesh.primitive_cylinder_add, name + "_juice", radius=0.064, depth=0.17, vertices=48, location=(0, 0, -0.016)); smooth(j)
    j.data.materials.append(mmat("juice_m", (0.9, 0.27, 0.0), 0.2)); j.parent = g
    return g
def smoothie():
    b = obj_from(bpy.ops.mesh.primitive_cylinder_add, "smoothie", radius=0.058, depth=0.24, vertices=40, location=(0, 0, 0)); smooth(b); bevel(b, 0.02)
    b.data.materials.append(mmat("smoothie_m", (0.42, 0.72, 0.22), 0.35))
    c = obj_from(bpy.ops.mesh.primitive_cylinder_add, "smoothie_cap", radius=0.035, depth=0.05, vertices=32, location=(0, 0, 0.14)); c.data.materials.append(mmat("cap_m", (0.95, 0.95, 0.93), 0.4)); c.parent = b
    l = obj_from(bpy.ops.mesh.primitive_cylinder_add, "smoothie_label", radius=0.0585, depth=0.09, vertices=40, location=(0, 0, -0.01)); smooth(l); l.data.materials.append(mmat("label_m", (0.98, 0.93, 0.72), 0.5)); l.parent = b
    return b
def granola():
    b = obj_from(bpy.ops.mesh.primitive_cube_add, "granola", size=1, location=(0, 0, 0)); b.scale = (0.17, 0.06, 0.035); bevel(b, 0.008)
    b.data.materials.append(mmat("granola_m", (0.86, 0.5, 0.18), 0.5)); return b
def yogurt():
    y = obj_from(bpy.ops.mesh.primitive_cone_add, "yogurt", radius1=0.05, radius2=0.062, depth=0.1, vertices=40, location=(0, 0, 0)); smooth(y)
    y.data.materials.append(mmat("yog_m", (0.97, 0.97, 0.98), 0.4))
    lid = obj_from(bpy.ops.mesh.primitive_cylinder_add, "yogurt_lid", radius=0.064, depth=0.008, vertices=40, location=(0, 0, 0.054)); lid.data.materials.append(mmat("lid_m", (0.93, 0.36, 0.55), 0.3)); lid.parent = y
    return y
def orange():
    o = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, "orange", radius=0.075, segments=32, ring_count=16, location=(0, 0, 0)); smooth(o)
    o.data.materials.append(mmat("orange_m", (1.0, 0.45, 0.03), 0.6)); o.scale.z = 0.94
    lf = obj_from(bpy.ops.mesh.primitive_cone_add, "orange_leaf", radius1=0.018, depth=0.04, vertices=8, location=(0.012, 0, 0.075)); lf.data.materials.append(mmat("leaf_m", (0.2, 0.55, 0.15), 0.6)); lf.parent = o
    return o
def phone(name, screen_col=(0.0, 1.0, 0.0)):
    b = obj_from(bpy.ops.mesh.primitive_cube_add, name, size=1, location=(0, 0, 0)); b.scale = (0.09, 0.012, 0.185); bpy.context.view_layer.objects.active = b; [x.select_set(x == b) for x in bpy.context.view_layer.objects]; bpy.ops.object.transform_apply(scale=True); bevel(b, 0.012, 4)
    b.data.materials.append(mmat(name + "_body", (0.05, 0.05, 0.06), 0.25))
    me = bpy.data.meshes.new(name + "_screen"); hw, hh = 0.041, 0.087
    me.from_pydata([(-hw, 0, -hh), (hw, 0, -hh), (hw, 0, hh), (-hw, 0, hh)], [], [(0, 1, 2, 3)]); me.update()
    uv = me.uv_layers.new(); [setattr(uv.data[i], "uv", c) for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
    sc = bpy.data.objects.new(name + "_screen", me); S.collection.objects.link(sc); sc.parent = b; sc.location = (0, -0.0085, 0)
    sm = mmat(name + "_screen_m", screen_col, 0.2, emit=1.0); sc.data.materials.append(sm)
    return b, sc

def place(o, x, y, rotz=0.0):
    mn, mx = bb(o); o.location.x += x - (mn.x + mx.x) / 2; o.location.y += y - (mn.y + mx.y) / 2; o.location.z += TOP + 0.004 - mn.z; o.rotation_euler.z = R(rotz)
    bpy.context.view_layer.update(); return o

CAN_T, GLASS_T = (-1.35, -1.86), (-1.0, -1.86)
TOW10, TOW8 = (-1.18, -1.86), (-0.82, -1.86)
ITEMS = {"smoothie": (-0.42, -1.72), "granola": (-0.06, -1.76), "yogurt": (0.28, -1.72)}
can = soda_can("soda_can"); place(can, *CAN_T)
glass = juice_glass("juice_glass"); place(glass, *GLASS_T)
sm_ = smoothie(); place(sm_, *ITEMS["smoothie"]); gr_ = granola(); place(gr_, *ITEMS["granola"], 12); yo_ = yogurt(); place(yo_, *ITEMS["yogurt"])
org = orange(); org.location = (0.5, 0.3, TOP + 0.08)
ph_g, scr_g = phone("phone_grandpa"); ph_m, scr_m = phone("phone_mom", (0.55, 0.75, 1.0))

# warm pendant lamp over the table
cord = obj_from(bpy.ops.mesh.primitive_cylinder_add, "lamp_cord", radius=0.008, depth=2.2, location=(-0.4, -0.9, 6.9)); cord.data.materials.append(mmat("cord_m", (0.05, 0.05, 0.05)))
shade_ = obj_from(bpy.ops.mesh.primitive_cone_add, "lamp_shade", radius1=0.42, radius2=0.12, depth=0.34, vertices=48, location=(-0.4, -0.9, 5.65)); smooth(shade_)
shade_.data.materials.append(mmat("shade_m", (0.95, 0.72, 0.25), 0.4)); sol = shade_.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.015
bulb = obj_from(bpy.ops.mesh.primitive_uv_sphere_add, "lamp_bulb", radius=0.07, location=(-0.4, -0.9, 5.5)); bulb.data.materials.append(mmat("bulb_m", (1.0, 0.85, 0.6), emit=8))
pl = bpy.data.objects.new("lamp_light", bpy.data.lights.new("lamp_light", "POINT")); S.collection.objects.link(pl); pl.location = (-0.4, -0.9, 5.4)
pl.data.energy = 350; pl.data.color = (1.0, 0.78, 0.5); pl.data.shadow_soft_size = 0.15

# ------------------------------------------------------------ characters
PUPA = os.path.abspath(sys.argv[-1]); HM = json.load(open(f"{PUPA}/headmeta.json")); ARTD = os.path.join(HERE, "ep1", "rig")
POS = {"son": (-2.6, -1.7), "mom": (-1.7, -2.2), "grandpa": (1.85, -1.1)}
RIG = {w: rig2.build(w, (*POS[w], 0), ARTD, f"{PUPA}/{w}/head", HM[w], cam, frames=NFR) for w in ("son", "mom", "grandpa")}
son, mom, gpa = RIG["son"], RIG["mom"], RIG["grandpa"]

# contact shadows
for who, r in RIG.items():
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.3, fill_type="NGON", location=(r["arm"].location.x, r["arm"].location.y, 0.004)); sh = bpy.context.active_object; sh.name = f"{who}_contact"
    sh.scale = (1.3, 0.55, 1); cl = sh.constraints.new("COPY_LOCATION"); cl.target = r["arm"]; cl.use_z = False
    sm = bpy.data.materials.new(f"{who}_contact_m"); sm.use_nodes = True; nt = sm.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial"); mx = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs[0].default_value = (0.02, 0.015, 0.02, 1); grd = nt.nodes.new("ShaderNodeTexGradient"); grd.gradient_type = "SPHERICAL"; tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3.3, 3.3, 3.3)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], grd.inputs[0]); nt.links.new(grd.outputs[1], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(df.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs[0])
    sh.data.materials.append(sm); sh.visible_shadow = False

# ------------------------------------------------------------ holding props: one Child Of per holder, influence switched by keys
def grip_world(r, sd, axis_deg):
    """World matrix a held prop has in the rest pose: at the grip point, axis turned in the card plane, squashed in depth."""
    arm = r["arm"]; g = r["grip"][sd]
    local = Matrix.Translation(g) @ Euler((0, R(axis_deg), 0)).to_matrix().to_4x4() @ Matrix.Diagonal((1, 0.45, 1, 1))
    return arm.matrix_world @ local
def holders(obj, spans):
    """spans: [(rig, side, axis_deg, t_on, t_off)]; outside every span the prop rests at its own (table) transform."""
    bpy.context.view_layer.update(); T = obj.matrix_world.copy()
    for i, (r, sd, axis, t0, t1) in enumerate(spans):
        arm = r["arm"]; c = obj.constraints.new("CHILD_OF"); c.name = f"hold{i}"; c.target = arm; c.subtarget = f"hand.{sd}"
        bone_rest = arm.matrix_world @ arm.data.bones[f"hand.{sd}"].matrix_local
        c.inverse_matrix = bone_rest.inverted() @ grip_world(r, sd, axis) @ T.inverted(); c.set_inverse_pending = False
        for f, v in ((1, 0.0), (F(t0) - 1, 0.0), (F(t0), 1.0), (F(t1), 1.0), (F(t1) + 1, 0.0)):
            if f < 1: continue
            c.influence = v; c.keyframe_insert("influence", frame=f)
    ad = obj.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
def pop(o, t_in=None, t_out=None, dur=0.18):
    """scale in/out with a little overshoot"""
    s1 = o.scale.copy()
    if t_in is not None:
        key(o, "scale", s1 * 0.0, max(1, F(t_in) - 1)); key(o, "scale", s1 * 0.0, F(t_in)); key(o, "scale", s1 * 1.15, F(t_in + dur * 0.6)); key(o, "scale", s1, F(t_in + dur))
    if t_out is not None:
        key(o, "scale", s1, F(t_out)); key(o, "scale", s1 * 0.0, F(t_out + dur))

bpy.context.view_layer.update()
exec(open(os.path.join(HERE, "ep1_keys.py")).read())

# ------------------------------------------------------------ phone screen corners per frame (for compositing the real Cubey screens locally)
from bpy_extras.object_utils import world_to_camera_view
corners = {}
for f in range(1, NFR + 1):
    S.frame_set(f)
    for scr in SCREENS:
        par = scr.parent
        if par.hide_render or scr.hide_render or scr.matrix_world.to_scale().length < 1e-3: continue
        mw = scr.matrix_world; pts = []
        for v in scr.data.vertices:
            p = world_to_camera_view(S, cam, mw @ v.co); pts.append((round(p.x * 1080, 2), round((1 - p.y) * 1920, 2), round(p.z, 3)))
        n = (mw.to_3x3() @ Vector((0, -1, 0))).normalized(); facing = n.dot((cam.matrix_world.translation - mw.translation).normalized())
        if facing > 0.1 and all(z > 0 for *_, z in pts): corners[f] = [pts[0][:2], pts[1][:2], pts[2][:2], pts[3][:2]]; break
json.dump(corners, open(OUT.replace(".blend", "_phone_corners.json"), "w"))
print("phone frames", len(corners))

S.frame_set(1)
for im in bpy.data.images:
    if im.source == "FILE" and not im.packed_file: im.pack()
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("saved", OUT)
