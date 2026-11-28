"""Reusable phone prop: an iPhone-style handset (rounded titanium frame, black glass, rounded screen,
Dynamic Island, side buttons, camera bump). The screen is a flat green emitter with full-rect UVs so the
real app screens can be keyed on top later, clipped to the rounded corners and the island for free.

Built in the XZ plane: width along X, height along Z, screen facing -Y (same convention as the other props).
phone_body["screen_wh"] = (w, h) of the screen rectangle; screen corners for compositing come from screen_rect_world().
"""
import bpy, bmesh, math
from mathutils import Vector

def _rrect(w, h, r, seg=10):
    pts = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg); pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts

def _mat(name, col, rough=0.4, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    if coat: b.inputs["Coat Weight"].default_value = coat
    return m

def _slab(name, w, h, r, d, mat, bevel=0.0, seg=10):
    """rounded-rectangle slab, centred, thickness d along Y"""
    bm = bmesh.new(); vs = [bm.verts.new((x, -d / 2, z)) for x, z in _rrect(w, h, r, seg)]
    f = bm.faces.new(vs); ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.y += d
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(mat)
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL"); bv.width = bevel; bv.segments = 4; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(50)
    for p in me.polygons: p.use_smooth = True
    return o

def _flat(name, pts, y, mat, uv_wh=None):
    me = bpy.data.meshes.new(name); me.from_pydata([(x, y, z) for x, z in pts], [], [list(range(len(pts)))]); me.update()
    if uv_wh:
        w, h = uv_wh; uv = me.uv_layers.new()
        for li, l in enumerate(me.loops):
            x, _, z = me.vertices[l.vertex_index].co; uv.data[li].uv = (x / w + 0.5, z / h + 0.5)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(mat); return o

def build(name, width=0.093, screen_col=(0.0, 1.0, 0.0), screen_emit=1.0, frame_col=(0.11, 0.11, 0.115)):
    """width ~0.093 = iPhone 15 Pro scaled 1.3x to match the 1.3x characters."""
    k = width / 0.0716
    W, H, D = width, 0.1476 * k, 0.0082 * k
    bez = 0.0019 * k; sw = W - 2 * bez; sh = sw * 2532 / 1170
    H = sh + 2 * bez                               # keep the bezel even all round for a 1170x2532 screen
    R = 0.0105 * k
    body = _slab(name, W, H, R, D, _mat("phone_frame", frame_col, 0.32, 1.0), bevel=0.0012 * k)
    glass = _flat(name + "_glass", _rrect(W - 0.0004 * k, H - 0.0004 * k, R - 0.0002 * k), -D / 2 - 0.00008, _mat("phone_glass_black", (0.004, 0.004, 0.005), 0.08, coat=1.0))
    glass.parent = body
    scr = _flat(name + "_screen", _rrect(sw, sh, R - bez * 0.9), -D / 2 - 0.00016, _mat(name + "_screen_m", screen_col, 0.3, emit=screen_emit), uv_wh=(sw, sh))
    scr.parent = body; scr.visible_shadow = False
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        if hasattr(scr, attr): setattr(scr, attr, False)
    iw, ih = 0.0126 * k, 0.0037 * k
    isl = _flat(name + "_island", _rrect(iw, ih, ih / 2 - 1e-6, 8), -D / 2 - 0.00024, _mat("phone_island", (0.0, 0.0, 0.0), 0.2))
    isl.location.z = sh / 2 - 0.0011 * k - ih / 2; isl.parent = body
    back = _flat(name + "_back", list(reversed(_rrect(W - 0.0006 * k, H - 0.0006 * k, R))), D / 2 + 0.00008, _mat("phone_back", (0.07, 0.07, 0.075), 0.45))
    back.parent = body
    bump = _slab(name + "_bump", 0.035 * k, 0.037 * k, 0.007 * k, 0.0016 * k, _mat("phone_back_glass", (0.09, 0.09, 0.095), 0.25), bevel=0.0004 * k)
    bump.location = (-(W / 2 - 0.0035 * k - 0.0175 * k), D / 2 + 0.0008 * k, H / 2 - 0.0035 * k - 0.0185 * k); bump.parent = body
    for i, (dx, dz) in enumerate(((-0.0095, 0.0098), (0.0095, 0.0098), (-0.0095, -0.0092))):
        ln = _slab(f"{name}_lens{i}", 0.0125 * k, 0.0125 * k, 0.00624 * k, 0.0013 * k, _mat("phone_lens", (0.02, 0.02, 0.025), 0.05, coat=1.0))
        ln.location = (bump.location.x + dx * k * 0.85, D / 2 + 0.0019 * k, bump.location.z + dz * k * 0.85); ln.parent = body
    for side, z, L in ((-1, 0.033, 0.006), (-1, 0.021, 0.0095), (-1, 0.008, 0.0095), (1, 0.014, 0.017)):
        bt = _slab(f"{name}_btn", 0.0012 * k, L * k, 0.0005 * k, 0.0026 * k, _mat("phone_frame", frame_col))
        bt.location = (side * (W / 2 + 0.0004 * k), 0, z * k * (H / (0.1476 * k)) * 1.0); bt.parent = body
    body["screen_wh"] = (sw, sh); body["screen_y"] = -D / 2 - 0.00016; body["depth"] = D; body["height"] = H
    return body, scr

def screen_rect_world(body):
    sw, sh = body["screen_wh"]; y = body["screen_y"]; mw = body.matrix_world
    return [mw @ Vector(p) for p in ((-sw / 2, y, -sh / 2), (sw / 2, y, -sh / 2), (sw / 2, y, sh / 2), (-sw / 2, y, sh / 2))]   # BL BR TR TL
