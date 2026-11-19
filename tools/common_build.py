"""Shared scene-building helpers (exec after defining S, ROOT, F, RANGE as needed)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler
from bpy_extras import anim_utils
# ---------------------------------------------------------------- helpers
def link(ob):
    S.collection.objects.link(ob); return ob


def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if getattr(act, "is_action_layered", False) or not hasattr(act, "fcurves"):
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    return list(act.fcurves)


def set_interp(idb, interp="LINEAR", path=None):
    for fc in fcurves(idb):
        if path is None or fc.data_path.startswith(path):
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def key(ob, path, f, val):
    setattr(ob, path, val); ob.keyframe_insert(path, frame=f)


def keyp(ob, prop, f, val):
    ob[prop] = val; ob.keyframe_insert(f'["{prop}"]', frame=f)


def mat(name, col, rough=0.5, metal=0.0, coat=0.0, sss=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m


def img_mat(name, folder, tint=(1, 1, 1), scale=4.0, rough_mul=1.0, bump=0.4):
    """Poly Haven texture set (Diffuse / Rough / nor_gl) on object coords; images packed into the .blend."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    def tex(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(folder, fn), check_existing=True)
        t.image.pack()
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        t.projection = "BOX"; t.projection_blend = 0.3
        L.new(mp.outputs[0], t.inputs["Vector"]); return t
    d = tex("Diffuse.jpg"); mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0; L.new(d.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (*tint, 1)
    L.new(mx.outputs["Result"], b.inputs["Base Color"])
    r = tex("Rough.jpg", True); rm = N.new("ShaderNodeMath"); rm.operation = "MULTIPLY"; rm.inputs[1].default_value = rough_mul
    L.new(r.outputs["Color"], rm.inputs[0]); L.new(rm.outputs[0], b.inputs["Roughness"])
    n = tex("nor_gl.jpg", True); nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump
    L.new(n.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = 0.4; b.inputs["Sheen Tint"].default_value = (1, 1, 1, 1)
    return m, mx


def area(name, loc, target, energy, size, col=(1, 1, 1), shape="DISK"):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size; d.color = col; d.shape = shape
    ob = link(bpy.data.objects.new(name, d)); ob.location = loc
    e = link(bpy.data.objects.new(name + "_t", None)); e.location = target
    tr = ob.constraints.new("TRACK_TO"); tr.target = e; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    return ob


def point(name, loc, energy, col=(1, 1, 1), r=0.01, parent=None):
    d = bpy.data.lights.new(name, "POINT"); d.energy = energy; d.color = col; d.shadow_soft_size = r
    ob = link(bpy.data.objects.new(name, d)); ob.location = loc
    if parent:
        ob.parent = parent
    return ob


CAMS = {}


def camera(name, loc, target, lens=35, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = clip; d.sensor_width = 36
    ob = link(bpy.data.objects.new(name, d)); ob.location = loc
    aim = link(bpy.data.objects.new(name + "_aim", None)); aim.location = target
    tr = ob.constraints.new("TRACK_TO"); tr.target = aim; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = focus or aim
    CAMS[name] = ob
    return ob, aim


def cut(t, cam):
    mk = S.timeline_markers.new(cam.name, frame=F(t)); mk.camera = cam


def shake(cam, f0, f1, amp, seed=3):
    rnd = random.Random(seed); base = cam.location.copy()
    for f in range(f0, f1 + 1):
        a = amp * max(0.0, 1 - (f - f0) / max(1, f1 - f0))
        cam.location = base + Vector((rnd.uniform(-a, a), rnd.uniform(-a, a), rnd.uniform(-a, a))); cam.keyframe_insert("location", frame=f)
    cam.location = base; cam.keyframe_insert("location", frame=f1 + 1)


def show_only(ob, frames_on):
    """hide_render keyed: visible only inside the given (f0, f1) frame ranges."""
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1)
    for f0, f1 in frames_on:
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0)
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1 + 1)


def hide_tree(root, frames_on):
    for o in [root] + list(root.children_recursive):
        show_only(o, frames_on)


def key_energy(lt, pairs):
    for f, e in pairs:
        lt.data.energy = e; lt.data.keyframe_insert("energy", frame=f)
    set_interp(lt.data, "CONSTANT")



def soft_box(name, center, half, m, levels=3, cast=0.35, wrinkle=0.006, wscale=0.08):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); ob.location = center; ob.scale = half
    sb = ob.modifiers.new("sub", "SUBSURF"); sb.levels = sb.render_levels = levels
    cs = ob.modifiers.new("cast", "CAST"); cs.factor = cast; cs.use_z = True
    if wrinkle:
        tx = bpy.data.textures.new(name + "_w", "CLOUDS"); tx.noise_scale = wscale; tx.noise_depth = 3
        d = ob.modifiers.new("wrinkle", "DISPLACE"); d.texture = tx; d.strength = wrinkle; d.texture_coords = "GLOBAL"
        sb2 = ob.modifiers.new("sub2", "SUBSURF"); sb2.levels = sb2.render_levels = 1
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    return ob


