# Shot 1 keys (30 fps). Character units: x right, z up, feet at 0. Angles in degrees, counter-clockwise.
import math
A = rig2.Anim(son)
A.key("hand.L", 1, -0.13, 0.5).key("hand.L", 60, -0.16, 0.54).key("hand.L", 150, -0.15, 0.53)
A.key("hand.R", 1, 0.2, 0.55).key("hand.R", 14, 0.17, 1.0).key("hand.R", 47, 0.17, 1.0).key("hand.R", 56, 0.25, 0.75).key("hand.R", 150, 0.24, 0.74)
# can axis = fingers + 90: upright while hanging, tipped toward the mouth while sipping
A.key("fingers.R", 1, 0).key("fingers.R", 14, 62).key("fingers.R", 30, 70).key("fingers.R", 47, 62).key("fingers.R", 56, 4).key("fingers.R", 150, 6)
A.key("fingers.L", 1, -95)
A.key("head", 1, 0).key("head", 14, -8).key("head", 30, -6).key("head", 47, -9).key("head", 56, 6).key("head", 100, 4).key("head", 150, 7)
A.key("spine", 1, 0).key("spine", 14, -3).key("spine", 56, 2).key("spine", 150, 0)
A.key("hips", 1, 0).key("hips", 47, 0).key("hips", 52, 0.05).key("hips", 58, 0).key("hips", 150, 0)
for sd, s in (("L", -1), ("R", 1)): A.key(f"foot.{sd}", 1, s * son["S"]["hipW"], son["z"]["ank"])
A.bake(1, 150)
rig2.set_hand(son, "R", "grip", 1); rig2.set_hand(son, "L", "open", 1); rig2.set_hand(son, "L", "fist", 68)

M = rig2.Anim(mom); m = mom["arm"]; X0, X1, WALK = -3.9, -5.75, 40
ease = lambda u: 1 - (1 - u) ** 2
rootx = lambda f: X0 + (X1 - X0) * ease(min(1, (f - 1) / (WALK - 1)))
hw = mom["S"]["hipW"]; ank = mom["z"]["ank"]; sc = 1.3
swing = {"R": [(1, 11), (21, 31)], "L": [(11, 21), (31, 41)]}
for sd, s in (("L", -1), ("R", 1)):
    plants = [s * hw]
    for a, b in swing[sd]: plants.append(s * hw + (rootx(min(b + 5, WALK + 1)) - X0) / sc)
    for f in range(1, WALK + 2):
        g = plants[0]; lift = 0.0
        for k, (a, b) in enumerate(swing[sd]):
            if f >= b: g = plants[k + 1]
            elif a <= f < b: u = (f - a) / (b - a); g = plants[k] + (plants[k + 1] - plants[k]) * (u * u * (3 - 2 * u)); lift = 0.07 * math.sin(math.pi * u)
        M.key(f"foot.{sd}", f, g - (rootx(f) - X0) / sc, ank + lift)
for f in range(1, WALK + 2):
    key(m, "location", Vector((rootx(f), m.location.y, 0)), f)
    ph = (f - 1) / 10 * math.pi; M.key("hips", f, abs(math.sin(ph)) * 0.025)
    M.key("hand.L", f, -0.18 - 0.06 * math.sin(ph), 0.53); M.key("hand.R", f, 0.18 + 0.06 * math.sin(ph), 0.53)
M.key("spine", 1, -2).key("spine", 40, -2).key("spine", 45, 5)
for sd in "LR": M.key(f"fingers.{sd}", 1, -90).key(f"fingers.{sd}", 41, -90); rig2.set_hand(mom, sd, "open", 1); rig2.set_hand(mom, sd, "wave", 42)
# shock: hands fly up beside the face, palms out, fingers up
M.key("hand.L", 45, -0.24, 1.22).key("hand.R", 45, 0.24, 1.22).key("hand.L", 56, -0.25, 1.24).key("hand.R", 56, 0.25, 1.24)
M.key("fingers.L", 45, 105).key("fingers.R", 45, 75).key("fingers.L", 56, 100).key("fingers.R", 56, 80)
M.key("hips", 41, 0).key("hips", 44, 0.06).key("hips", 48, 0)
# rant: left arm points at the son, right fist shakes up high
M.key("hand.L", 62, -0.52, 1.06).key("hand.R", 62, 0.42, 1.48)
M.key("fingers.L", 62, 182).key("fingers.R", 62, 75).key("spine", 62, -6).key("head", 1, 0).key("head", 56, 0)
for i, f in enumerate(range(66, 151, 5)):
    w = 1 if i % 2 else -1
    M.key("hand.R", f, 0.42 + 0.02 * w, 1.48 + 0.05 * w).key("hand.L", f, -0.52 - 0.015 * w, 1.06 + 0.02 * w)
    M.key("head", f, 5 * w).key("spine", f, -6 + 2 * w).key("hips", f, 0.02 if w > 0 else 0)
M.bake(1, 150)
rig2.set_hand(mom, "L", "point", 59); rig2.set_hand(mom, "R", "fist", 59)
