"""Knoxville video: 3D 'sky view' explainer of the apartment (approximate layout from the released bodycam).
Dollhouse cutaway: walls cut at 1.2 m, seen from above; officers (dark blue), Melendez (red), the girl (white,
no detail), movement paths and floating labels. exec() after common_build.py; plan_set(X0) builds it at x=X0."""
import bpy, bmesh, math, os
from mathutils import Vector

FONT = bpy.data.fonts.load(os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf"))
WALL_H = 2.0


def flat(name, col, emit=0.0, rough=0.6):
    return mat(name, col, rough=rough, emit=emit)


M_FLOOR = flat("plan_floor", (0.32, 0.22, 0.14), rough=0.5)
M_CARPET = flat("plan_carpet", (0.35, 0.33, 0.32), rough=0.9)
M_WALL = flat("plan_wall", (0.72, 0.72, 0.7), rough=0.7)
M_CUT = flat("plan_cut", (0.08, 0.08, 0.09), rough=0.6)          # dark cap on cut walls
M_COP = flat("plan_cop", (0.08, 0.16, 0.42), rough=0.4)
M_SUS = flat("plan_sus", (0.75, 0.06, 0.05), rough=0.4)
M_GIRL = flat("plan_girl", (0.92, 0.92, 0.92), rough=0.5)
M_PATH = flat("plan_path", (1.0, 0.82, 0.2), emit=3.0)
M_RED = flat("plan_redglow", (1.0, 0.1, 0.05), emit=6.0)
M_LABEL = flat("plan_label", (1, 1, 1), emit=1.5)
M_FURN = flat("plan_furn", (0.6, 0.6, 0.62), rough=0.7)
M_MATT = flat("plan_mattress", (0.85, 0.85, 0.9), rough=0.8)


def wall(name, a, b, X0, h=WALL_H, t=0.1):
    a = Vector((a[0] + X0, a[1], 0)); b = Vector((b[0] + X0, b[1], 0))
    mid = (a + b) / 2; d = b - a; ln = d.length
    w = box(name, (mid.x, mid.y, h / 2), (ln / 2 + t / 2, t / 2, h / 2), M_WALL)
    w.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    cap = box(name + "_cap", (mid.x, mid.y, h + 0.005), (ln / 2 + t / 2, t / 2 + 0.002, 0.005), M_CUT)
    cap.rotation_euler = w.rotation_euler
    return w


def figure(name, m, loc, scale=1.0):
    """Simple mannequin pawn: capsule body + head (no faces, no detail)."""
    root = link(bpy.data.objects.new(name, None)); root.location = loc
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
    for v in bm.verts:
        v.co.z = v.co.z * 1.0 + (0.55 if v.co.z > 0 else -0.55)
    me = bpy.data.meshes.new(name + "_b"); bm.to_mesh(me); bm.free(); me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    b = link(bpy.data.objects.new(name + "_body", me)); b.parent = root; b.scale = (0.2 * scale, 0.15 * scale, 0.42 * scale); b.location = (0, 0, 0.66 * scale)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.12 * scale)
    me = bpy.data.meshes.new(name + "_h"); bm.to_mesh(me); bm.free(); me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    h = link(bpy.data.objects.new(name + "_head", me)); h.parent = root; h.location = (0, 0, 1.48 * scale)
    return root


def label(name, text, loc, size=0.28, m=None):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = text; cu.font = FONT; cu.size = size
    cu.extrude = 0.01; cu.align_x = "CENTER"; cu.align_y = "BOTTOM"
    ob = link(bpy.data.objects.new(name, cu)); ob.location = loc; cu.materials.append(m or M_LABEL)
    return ob


def path_line(name, pts, X0, z=0.03):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.035; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts):
        p.co = (x + X0, y, z, 1)
    cu.materials.append(M_PATH); cu.bevel_factor_end = 0.0
    return link(bpy.data.objects.new(name, cu))


def plan_set(X0):
    """Approximate unit: stair landing + entry/living room + hallway + small bedroom (metres, y up = north)."""
    out = {}
    box("plan_base", (X0 + 3.0, 2.5, -0.06), (6.5, 5.0, 0.06), flat("plan_ground", (0.03, 0.03, 0.035), rough=0.9))
    box("plan_floor_liv", (X0 + 2.5, 2.0, 0.0), (2.5, 2.0, 0.01), M_FLOOR)
    box("plan_floor_hall", (X0 + 5.6, 2.0, 0.0), (0.6, 2.0, 0.01), M_FLOOR)
    box("plan_floor_bed", (X0 + 7.6, 3.0, 0.0), (1.4, 1.5, 0.01), M_CARPET)
    # outer walls + rooms
    for nm, a, b in (("w_s", (0, 0), (0.15, 0)), ("w_s2", (1.05, 0), (6.2, 0)), ("w_w", (0, 0), (0, 4)), ("w_n", (0, 4), (9, 4)), ("w_e", (9, 4), (9, 1.5)),
                     ("w_bs", (6.2, 1.5), (9, 1.5)), ("w_he", (6.2, 0), (6.2, 0.6)), ("w_liv_e", (5.0, 0.0), (5.0, 2.6)),
                     ("w_hall_w2", (5.0, 3.5), (5.0, 4.0)), ("w_bw", (6.2, 1.5), (6.2, 2.2)), ("w_bw2", (6.2, 3.1), (6.2, 4.0))):
        wall("plan_" + nm, a, b, X0)
    # stairwell outside the front door (south-west), with the white railing
    for k in range(6):
        box(f"plan_step{k}", (X0 + 0.6 + 0.0, -0.6 - k * 0.28, -0.18 * (k + 1)), (0.5, 0.14, 0.09), M_FLOOR)
    box("plan_rail", (X0 + 1.15, -1.3, 0.35), (0.02, 0.9, 0.02), M_WALL)
    # furniture blocks
    box("plan_sofa", (X0 + 2.5, 3.5, 0.25), (1.0, 0.35, 0.25), M_FURN, bevel=0.05)
    box("plan_mattress", (X0 + 8.1, 3.2, 0.12), (0.7, 1.0, 0.12), M_MATT, bevel=0.04)
    box("plan_dresser", (X0 + 6.8, 3.7, 0.4), (0.5, 0.22, 0.4), M_FURN, bevel=0.02)
    # bedroom clutter (clothes piles, boxes) and a TV in the living room
    import random as _r
    rr = _r.Random(4)
    for k in range(10):
        box(f"plan_clutter{k}", (X0 + rr.uniform(6.5, 8.7), rr.uniform(1.7, 2.4), 0.06), (rr.uniform(0.1, 0.25), rr.uniform(0.1, 0.2), 0.06),
            flat(f"plan_cl{k}", (rr.uniform(0.1, 0.5), rr.uniform(0.1, 0.4), rr.uniform(0.2, 0.5)), rough=0.9), bevel=0.03)
    box("plan_tv", (X0 + 2.5, 0.25, 0.35), (0.6, 0.05, 0.3), flat("plan_tvm", (0.02, 0.02, 0.02), rough=0.2))
    box("plan_table", (X0 + 2.5, 2.2, 0.2), (0.5, 0.3, 0.02), M_FURN)
    out["door"] = Vector((X0 + 0.6, 0.0, 0))
    out["bed_door"] = Vector((X0 + 6.2, 2.65, 0))
    out["mattress"] = Vector((X0 + 8.1, 3.2, 0.24))
    return out
