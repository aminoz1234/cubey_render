"""Knoxville video: 3D map dive, documentary style. Real terrain (AWS Terrain Tiles, open data) shaded dark,
thin state borders, Tennessee outlined in glowing blue, a light cone dropping onto Knoxville, letter-spaced labels,
soft depth of field. Vectors: Natural Earth 10m. 1 unit = 10 km, origin = Knoxville.  Shot 1-240."""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
bpy.ops.wm.read_factory_settings(use_empty=True)
ROOT = os.getcwd(); S = bpy.context.scene
exec(open("tools/realism.py").read()); exec(open("tools/common_build.py").read())
cycles_quality(S, samples=32, res=(1280, 720)); S.view_settings.look = "AgX - Medium High Contrast"
S.frame_start, S.frame_end = 1, 240; S.render.fps = 30
LON0, LAT0 = -83.92, 35.96; KX = math.cos(math.radians(LAT0)) * 111.0 / 10.0; KY = 11.1
EXAG = 6.0 / 10000.0      # metres of elevation -> units, 3x exaggerated
D = json.load(open(os.path.join(ROOT, "assets/knox/tn_map.json")))
w = bpy.data.worlds.new("w"); S.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.006, 0.01, 1)
FONT = bpy.data.fonts.load(os.path.join(ROOT, "assets", "fonts", "BebasNeue-Regular.ttf"))
GRIDS = [np.load(os.path.join(ROOT, "assets/knox/dem_wide.npz"))]


def height(x, y):
    """Terrain height (units) at projected x, y: fine Knoxville grid where it covers, else the wide grid."""
    lon = x / KX + LON0; lat = y / KY + LAT0
    for g in GRIDS:
        lo, la, h = g["lons"], g["lats"], g["h"]
        if lo[0] <= lon <= lo[-1] and la[0] <= lat <= la[-1]:
            fi = (lon - lo[0]) / (lo[-1] - lo[0]) * (len(lo) - 1); fj = (lat - la[0]) / (la[-1] - la[0]) * (len(la) - 1)
            i, j = min(int(fi), len(lo) - 2), min(int(fj), len(la) - 2); u, v = fi - i, fj - j
            e = h[j, i] * (1 - u) * (1 - v) + h[j, i + 1] * u * (1 - v) + h[j + 1, i] * (1 - u) * v + h[j + 1, i + 1] * u * v
            return max(float(e), 0.0) * EXAG
    return 0.0


def terrain(name, g, m, dz=0.0):
    lo, la, h = g["lons"], g["lats"], np.maximum(g["h"], 0)
    nx, ny = len(lo), len(la)
    X, Y = np.meshgrid((lo - LON0) * KX, (la - LAT0) * KY)
    co = np.stack([X.ravel(), Y.ravel(), h.ravel() * EXAG + dz], 1).astype(np.float32)
    idx = np.arange(nx * ny).reshape(ny, nx)
    q = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(name); me.vertices.add(len(co)); me.vertices.foreach_set("co", co.ravel())
    me.loops.add(q.size); me.loops.foreach_set("vertex_index", q.ravel().astype(np.int32))
    me.polygons.add(len(q)); me.polygons.foreach_set("loop_start", np.arange(0, q.size, 4, dtype=np.int32)); me.polygons.foreach_set("loop_total", np.full(len(q), 4, np.int32))
    me.update(); me.validate()
    me.polygons.foreach_set("use_smooth", np.ones(len(q), bool))
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def terrain_mat():
    m = bpy.data.materials.new("terrain"); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    # height tint: lowlands near-black blue, ridges lighter grey-blue
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 1.0
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.035, 0.045, 0.06, 1); cr.color_ramp.elements[1].color = (0.3, 0.33, 0.38, 1)
    L.new(mr.outputs["Result"], cr.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 12
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.35
    L.new(cr.outputs["Color"], mx.inputs[6]); L.new(nz.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    return m


def emis(name, col, s):
    return mat(name, col, emit=s, rough=0.6)


def draped(name, lines, m, depth, lift=0.05, step=1):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = 1
    for pts in lines:
        pts = pts[::step]
        if len(pts) < 2:
            continue
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for p, (x, y) in zip(sp.points, pts):
            p.co = (x, y, height(x, y) + lift, 1)
    cu.materials.append(m)
    return link(bpy.data.objects.new(name, cu))


def label(t, x, y, size, m, spacing=1.6, lift=0.05):
    cu = bpy.data.curves.new("t_" + t, "FONT"); cu.body = t; cu.font = FONT; cu.size = size; cu.space_character = spacing
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.materials.append(m)
    o = link(bpy.data.objects.new("t_" + t, cu)); o.location = (x, y, height(x, y) + lift)
    return o


def pop(o, pairs):
    for f, s in pairs:
        o.scale = (s,) * 3; o.keyframe_insert("scale", frame=f)


M_TERR = terrain_mat()
terrain("terrain_wide", GRIDS[0], M_TERR)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.01)); bpy.context.active_object.data.materials.append(mat("sea", (0.01, 0.015, 0.025), rough=0.9))

M_BORDER = emis("m_border", (0.75, 0.8, 0.88), 1.2)
M_TN = emis("m_tn", (0.1, 0.45, 1.0), 10.0)
M_RIVER = emis("m_river", (0.25, 0.6, 1.0), 2.5)
M_TEXT = emis("m_text", (0.72, 0.76, 0.82), 1.6)
M_TEXT_HI = emis("m_text_hi", (0.85, 0.93, 1.0), 4.0)
tn = [s["pts"] for s in D["states"] if s["name"] == "Tennessee"]
others = [s["pts"] for s in D["states"] if s["name"] != "Tennessee"]
b_ot = draped("borders", [p + p[:1] for p in others], M_BORDER, 0.03)
b_tn = draped("tn_outline", [p + p[:1] for p in tn], M_TN, 0.07)
riv = draped("tn_river", [r["pts"] for r in D["rivers"] if r["name"] == "Tennessee"], M_RIVER, 0.03)
for ob, d0, d1 in ((b_ot, 0.03, 0.006), (b_tn, 0.07, 0.012), (riv, 0.03, 0.007)):
    for f, d in ((1, d0), (70, d0), (200, d1)):
        ob.data.bevel_depth = d; ob.data.keyframe_insert("bevel_depth", frame=f)
b_tn.data.bevel_factor_end = 0.0; b_tn.data.keyframe_insert("bevel_factor_end", frame=8)
b_tn.data.bevel_factor_end = 1.0; b_tn.data.keyframe_insert("bevel_factor_end", frame=70)

# letter-spaced region labels (fade out as we dive)
for t, x, y, s in (("KENTUCKY", -18, 14, 2.4), ("VIRGINIA", 22, 14, 2.4), ("NORTH CAROLINA", 26, -4, 2.2), ("GEORGIA", 2, -24, 2.4),
                   ("ALABAMA", -30, -24, 2.4), ("MISSISSIPPI", -60, -24, 2.2), ("ARKANSAS", -78, -6, 2.2)):
    pop(label(t, x, y, s, M_TEXT, lift=0.3), ((1, 1.0), (95, 1.0), (125, 0.0)))
pop(label("TENNESSEE", -26, -3.5, 3.0, M_TEXT_HI, lift=0.3), ((1, 0.0), (20, 1.0), (100, 1.0), (125, 0.0)))
for c in D["cities"]:
    if c["name"] in ("Nashville", "Memphis", "Chattanooga"):
        x, y = c["p"]
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.22, depth=0.04, location=(x, y, height(x, y) + 0.05))
        bpy.context.active_object.data.materials.append(M_TEXT_HI)
        pop(label(c["name"].upper(), x, y - 1.6, 1.4, M_TEXT, lift=0.3), ((1, 1.0), (100, 1.0), (125, 0.0)))

# Knoxville: light cone from above + glow spot + label
kx, ky = 0.0, 0.11; kz = height(kx, ky)
cone_m = bpy.data.materials.new("cone"); cone_m.use_nodes = True; nt = cone_m.node_tree; N, L = nt.nodes, nt.links
for n in list(N):
    if n.type != "OUTPUT_MATERIAL":
        N.remove(n)
tr = N.new("ShaderNodeBsdfTransparent"); em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.55, 0.78, 1.0, 1); em.inputs["Strength"].default_value = 2.0
mx = N.new("ShaderNodeMixShader")
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(lw.outputs["Facing"], mul.inputs[0])
inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L.new(sep.outputs["Z"], inv.inputs[1])
pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.5; L.new(inv.outputs[0], pw.inputs[0])
L.new(pw.outputs[0], mul.inputs[1])
fac = N.new("ShaderNodeMath"); fac.operation = "MULTIPLY"; fac.inputs[1].default_value = 0.18; L.new(mul.outputs[0], fac.inputs[0])
st = N.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = 1.4; L.new(fac.outputs[0], st.inputs[0])
L.new(st.outputs[0], em.inputs["Strength"]); ad = N.new("ShaderNodeAddShader")
L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs["Surface"])
cone_m.surface_render_method = "BLENDED" if hasattr(cone_m, "surface_render_method") else None
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.45, radius2=0.02, depth=14, location=(kx, ky, kz + 7.0), end_fill_type="NOTHING")
cone = bpy.context.active_object; cone.name = "light_cone"; cone.data.materials.append(cone_m); cone.visible_shadow = False
pop(cone, ((1, 0.0), (110, 0.0), (135, 1.0)))
spot = bpy.data.lights.new("knox_spot", "SPOT"); spot.energy = 0.0; spot.spot_size = math.radians(6); spot.spot_blend = 0.8; spot.color = (0.55, 0.78, 1.0); spot.shadow_soft_size = 0.2
so = link(bpy.data.objects.new("knox_spot", spot)); so.location = (kx, ky, kz + 9)
for f, e in ((1, 0), (110, 0), (135, 3500)):
    spot.energy = e; spot.keyframe_insert("energy", frame=f)
kl = label("KNOXVILLE", kx + 1.3, ky - 0.3, 0.3, M_TEXT_HI, spacing=1.8, lift=0.08)
pop(kl, ((1, 0.0), (130, 0.0), (140, 1.0)))

# light + camera dive with soft depth of field
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 1.6; sun.color = (0.75, 0.82, 1.0); sun.angle = math.radians(3)
so2 = link(bpy.data.objects.new("sun", sun)); so2.rotation_euler = (math.radians(68), 0, math.radians(-60))
cam, aim = camera("cam", Vector((-22, -60, 70)), Vector((-20, -2, 0)), lens=35)
cam.data.clip_end = 600; cam.data.dof.use_dof = True; cam.data.dof.focus_object = aim
for f, fs in ((1, 2.8), (100, 2.0), (240, 1.4)):
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
for f, cl, al in ((1, (-24, -62, 68), (-20, -2, 0)), (70, (-15, -46, 50), (-14, -1, 0)), (180, (kx + 1.8, ky - 11.0, kz + 9.0), (kx, ky, kz)),
                  (240, (kx + 2.6, ky - 9.0, kz + 7.2), (kx + 0.05, ky, kz))):
    cam.location = cl; cam.keyframe_insert("location", frame=f); aim.location = al; aim.keyframe_insert("location", frame=f)
for o in (cam, aim):
    for fc in fcurves(o):
        for k in fc.keyframe_points:
            k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"
S.camera = cam
os.makedirs("scenes/knox_map", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes/knox_map/map.blend"))
if "--still" in sys.argv:
    S.cycles.samples = 12
    for f in map(int, sys.argv[sys.argv.index("--still") + 1].split(",")):
        S.frame_set(f); S.render.filepath = f"/tmp/et/map_{f}.png"; bpy.ops.render.render(write_still=True)
