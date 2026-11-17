"""Realistic man beats for the seed video (uses the bite shot setup, no watermelon):
frames 1-68   : 15.60-17.85 s  swallow + relief, then the face turns serious ("here's the scary part"), light dims red
frames 69-155 : 33.30-36.20 s  laughing, then freezes on "don't laugh"
"""
import bpy, math, os
from mathutils import Vector
__file__ = os.path.join(os.getcwd(), "tools", "shot_bite.py")
exec(open(__file__).read())
S = bpy.context.scene
S.frame_start, S.frame_end = 1, 155
for n in [o for o in bpy.data.objects if o.name.startswith(("melon", "seed", "bite_cutter"))]:
    bpy.data.objects.remove(n)
rig.animation_data_clear()
for b in pb:
    b.rotation_mode = "XYZ"; b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
J = float(os.environ.get("JAW_SIGN", "1"))
def jw(f, d): jaw(f, d * J)
# --- beat 1: swallow + relief (1-25), serious (26-68)
jw(1, 3); jw(8, 0); jw(25, 1); jw(30, 0); jw(68, 0)
head(1, -2, 4, 0); head(8, 5, 4, 0); head(14, -3, 4, 0); head(25, -4, 2, 2); head(40, 2, 0, 0); head(68, 4, 0, 0)
for f, z in [(1, 0.0), (6, 0.006), (12, 0.0)]:
    pb["neck01"].location = (0, z, 0); pb["neck01"].keyframe_insert("location", frame=f)
# --- beat 2: laugh (69-117), freeze (118-155)
for k, f in enumerate(range(69, 118, 4)):
    jw(f, 9 if k % 2 == 0 else 3)
    head(f, -7 if k % 2 == 0 else -3, 3, 1.5 if k % 2 == 0 else -1)
jw(118, 9); head(118, -5, 3, 0)
jw(123, 1); head(123, 1, 0, 0); jw(155, 1); head(155, 1, 0, 0)
# light: warm -> dim red for the scary beat, back to normal for the laugh
key_l = bpy.data.objects["key"].data
for f, e, c in [(1, 45, (1, 0.92, 0.82)), (30, 45, (1, 0.92, 0.82)), (60, 14, (1, 0.35, 0.3)), (68, 14, (1, 0.35, 0.3)), (69, 45, (1, 0.92, 0.82))]:
    key_l.energy = e; key_l.color = c
    key_l.keyframe_insert("energy", frame=f); key_l.keyframe_insert("color", frame=f)
# camera: medium close, slow push on the scary beat, snap zoom on the freeze
cam.animation_data_clear()
def cpos(f, off): cam.location = mouth + Vector(off); cam.keyframe_insert("location", frame=f)
cpos(1, (-0.34, -0.72, 0.1)); cpos(29, (-0.33, -0.7, 0.1)); cpos(68, (-0.22, -0.48, 0.08))
cpos(69, (-0.36, -0.78, 0.12)); cpos(117, (-0.34, -0.74, 0.12)); cpos(124, (-0.2, -0.42, 0.08)); cpos(155, (-0.19, -0.4, 0.08))
focus.location = mouth + Vector((0, -0.02, 0.06))
cam.data.dof.aperture_fstop = 3.2
print("BEATS READY")
