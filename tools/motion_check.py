"""Motion QA for cut-out rigs. Run on a built .blend before any render: catches what still frames can't show.
Usage: python3 motion_check.py scene.blend   (exit code 1 = do not render)
Checks every frame:
  - hand-atlas cell offsets are whole cells (a fractional offset = the hand drawing slides through the sheet)
  - Child Of influences are 0 or 1 (in between = a held prop drifting between hand and table)
  - no hand turns more than 60 deg between frames, and no wrist is bent past 75 deg from its forearm
"""
import bpy, sys, math
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1]); S = bpy.context.scene
cells = [m for m in bpy.data.materials if m.node_tree and "cell" in m.node_tree.nodes]
rigs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
held = [(o, c) for o in bpy.data.objects for c in o.constraints if c.type == "CHILD_OF"]
errs = []; prev = {}
def rest(arm, b):
    v = arm.data.bones[b].matrix_local.to_3x3().col[1]; return math.degrees(math.atan2(v.z, v.x))
def ang(arm, b): v = arm.pose.bones[b].matrix.to_3x3().col[1]; return math.degrees(math.atan2(v.z, v.x))
for f in range(S.frame_start, S.frame_end + 1):
    S.frame_set(f)
    for m in cells:
        n = 6; v = m.node_tree.nodes["cell"].inputs["Location"].default_value[0] * n
        if abs(v - round(v)) > 1e-3: errs.append(f"f{f} {m.name}: hand cell {v:.2f} (sliding drawing)")
    for o, c in held:
        if 1e-3 < c.influence < 0.999: errs.append(f"f{f} {o.name}.{c.name}: influence {c.influence:.2f} (prop drifting)")
    for arm in rigs:
        for sd in "LR":
            b = f"hand.{sd}"
            if b not in arm.pose.bones: continue
            v3 = arm.pose.bones[b].matrix.to_3x3().col[1].normalized(); k = (arm.name, b)
            if k in prev:
                turn = math.degrees(v3.angle(prev[k], 0.0))
                if turn > 60: errs.append(f"f{f} {arm.name} {b}: turned {turn:.0f} deg in one frame")
            prev[k] = v3.copy()
            fo = arm.pose.bones[f"fore.{sd}"].matrix.to_3x3().col[1]
            if math.hypot(fo.x, fo.z) > 0.7 and math.hypot(v3.x, v3.z) > 0.7:
                a = ang(arm, b); r0 = rest(arm, b) - rest(arm, f"fore.{sd}")
                rel = abs((a - ang(arm, f"fore.{sd}") - r0 + 180) % 360 - 180)
                if rel > 75: errs.append(f"f{f} {arm.name} {b}: wrist bent {rel:.0f} deg")
print(f"MOTION CHECK: {len(errs)} problems")
for e in errs[:40]: print("  ", e)
sys.exit(1 if errs else 0)
