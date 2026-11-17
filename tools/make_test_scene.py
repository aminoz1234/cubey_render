"""Builds the 3 s cloud-render test: inside a throat, a water drop slides down the tube (Zack D. Films-style look)."""
import bpy, math, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.frame_start, s.frame_end, s.render.fps = 1, 90, 30
# throat: a tube built ring by ring (so bumps follow its length), along -Y
import bmesh
bm = bmesh.new(); R, NS, NR, L = 1.0, 72, 140, 14.0
rings = []
for i in range(NR):
    y = 2 - L * i / (NR - 1)
    rings.append([bm.verts.new((R * math.cos(2*math.pi*j/NS), y, R * math.sin(2*math.pi*j/NS))) for j in range(NS)])
for i in range(NR - 1):
    for j in range(NS):
        bm.faces.new((rings[i][j], rings[i][(j+1) % NS], rings[i+1][(j+1) % NS], rings[i+1][j]))
me = bpy.data.meshes.new('throat'); bm.to_mesh(me); tube = bpy.data.objects.new('throat', me); s.collection.objects.link(tube)
for p_ in me.polygons: p_.use_smooth = True
d = tube.modifiers.new('bumps', 'DISPLACE'); tx = bpy.data.textures.new('flesh', 'CLOUDS'); tx.noise_scale = 0.5
d.texture = tx; d.texture_coords = 'GLOBAL'; d.strength = -0.22; d.mid_level = 0.5
m = bpy.data.materials.new('flesh'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.55, 0.09, 0.08, 1); b.inputs['Roughness'].default_value = 0.22
b.inputs['Subsurface Weight'].default_value = 0.0; b.inputs['Subsurface Radius'].default_value = (0.4, 0.1, 0.05)
b.inputs['Coat Weight'].default_value = 0.35
tube.data.materials.append(m)
# water drop (glassy blue) sliding down
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.38, location=(0, 0, 0.35)); drop = bpy.context.object
bpy.ops.object.shade_smooth()
wm = bpy.data.materials.new('water'); wm.use_nodes = True; wb = wm.node_tree.nodes['Principled BSDF']
wb.inputs['Base Color'].default_value = (0.35, 0.75, 1.0, 1); wb.inputs['Transmission Weight'].default_value = 0.85
wb.inputs['Roughness'].default_value = 0.03; wb.inputs['IOR'].default_value = 1.33
drop.data.materials.append(wm)
for f, y, sc in [(1, 0.5, (1, 1, 1)), (45, -3.0, (0.9, 1.25, 0.9)), (90, -8.0, (1, 1, 1))]:
    drop.location.y = y; drop.scale = sc
    drop.keyframe_insert('location', frame=f); drop.keyframe_insert('scale', frame=f)
# camera follows a little behind, slight handheld drift
bpy.ops.object.camera_add(location=(0.15, 2.6, 0.25), rotation=(math.radians(92), 0, math.radians(180))); cam = bpy.context.object
cam.data.lens = 22; s.camera = cam
cam.keyframe_insert('location', frame=1); cam.location = (-0.1, -4.5, 0.15); cam.keyframe_insert('location', frame=90)
# lights: warm key travelling with the camera + cool rim deep in the tube
bpy.ops.object.light_add(type='POINT', location=(0.4, 1.8, 0.6)); key = bpy.context.object; key.data.energy = 120; key.data.color = (1, 0.85, 0.7)
key.parent = cam; key.matrix_parent_inverse = cam.matrix_world.inverted()
bpy.ops.object.light_add(type='POINT', location=(0, -10, 0)); rim = bpy.context.object; rim.data.energy = 400; rim.data.color = (0.5, 0.7, 1)
s.world = bpy.data.worlds.new('w'); s.world.color = (0.01, 0.0, 0.0)
s.view_settings.view_transform = 'AgX'; s.view_settings.look = 'AgX - Punchy'
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1], compress=True)
print("saved", sys.argv[-1])
