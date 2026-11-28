"""POV hand art for holding a phone (right hand, seen from the holder's eyes).
Two layers in phone-local metres (x right, z up, phone centred): back = palm + fingers behind the phone
(only the parts outside the phone show), front = fingertips over the left edge + thumb over the right edge.
Usage: python3 povhand.py OUTDIR [phone_width]"""
import sys, json
from PIL import Image, ImageDraw
OUT = sys.argv[1]; PW = float(sys.argv[2]) if len(sys.argv) > 2 else 0.093
PX = 4000; X0, X1, Z0, Z1 = -0.09, 0.13, -0.21, 0.05
Wpx, Hpx = int((X1 - X0) * PX), int((Z1 - Z0) * PX)
SKIN, SKIN_D, INK, CREASE = (247, 228, 200), (232, 204, 170), (43, 27, 32), (178, 132, 100)
OL = 11
def P(x, z): return ((x - X0) * PX, (Z1 - z) * PX)
def capsule(d, a, b, w, fill):
    (x0, y0), (x1, y1) = P(*a), P(*b); r = w * PX / 2
    d.line((x0, y0, x1, y1), fill=fill, width=int(2 * r))
    for x, y in ((x0, y0), (x1, y1)): d.ellipse((x - r, y - r, x + r, y + r), fill=fill)
def blob(d, pts, fill, grow=0):
    d.polygon([P(*p) for p in pts], fill=fill, outline=fill, width=int(grow * 2) if grow else 0)
E_ = PW / 2
def shade(im):   # soft vertical shading, darker toward the wrist
    import numpy as np
    a = np.array(im).astype(float); h = a.shape[0]; g = np.linspace(0, 1, h)[:, None]
    m = (a[..., 3] > 0) & (np.abs(a[..., :3] - np.array(SKIN)).sum(-1) < 6)
    for i in range(3): a[..., i] = np.where(m, SKIN[i] * (1 - 0.6 * g) + SKIN_D[i] * 0.6 * g, a[..., i])
    return Image.fromarray(a.astype("uint8"))
# ---- back layer
back = Image.new("RGBA", (Wpx, Hpx), (0, 0, 0, 0)); d = ImageDraw.Draw(back)
palm = [(-0.035, -0.02), (0.03, -0.012), (E_ + 0.012, -0.05), (E_ + 0.03, -0.11), (E_ + 0.03, -0.165), (0.0, -0.186), (-0.032, -0.118)]
fingers = [((0.02, -0.010), (-E_ - 0.013, -0.004), 0.0195), ((0.02, -0.034), (-E_ - 0.014, -0.029), 0.0200),
           ((0.02, -0.058), (-E_ - 0.013, -0.055), 0.0195), ((0.02, -0.082), (-E_ - 0.009, -0.081), 0.0170)]
blob(d, palm, INK, OL / PX * 2 + 0.0)
for a, b, w in fingers: capsule(d, a, b, w + 2 * OL / PX, INK)
d.polygon([P(*p) for p in palm], fill=SKIN)
# fill palm shrunk by the outline: redraw ink edge
d.line([P(*p) for p in palm + [palm[0]]], fill=INK, width=OL * 2, joint="curve")
d.polygon([P(*p) for p in palm], fill=SKIN)
for a, b, w in reversed(fingers):           # top finger last so its outline sits over the one below
    capsule(d, a, b, w + 2 * OL / PX, INK); capsule(d, a, b, w, SKIN)
back = shade(back); back.save(f"{OUT}/pov_back.png")
# ---- front layer: fingertip pads wrapping onto the left edge, thumb along the right edge
front = Image.new("RGBA", (Wpx, Hpx), (0, 0, 0, 0)); d = ImageDraw.Draw(front)
for (a, b, w) in fingers:
    tip2 = (-E_ + 0.0026 - w / 2, b[1])
    capsule(d, b, tip2, w + 2 * OL / PX, INK); capsule(d, b, tip2, w, SKIN)
T = [((E_ + 0.026, -0.128), (E_ + 0.007, -0.074), 0.034), ((E_ + 0.007, -0.074), (E_ - 0.0045, -0.034), 0.025)]
for a, b, w in T: capsule(d, a, b, w + 2 * OL / PX, INK)
for a, b, w in T: capsule(d, a, b, w, SKIN)
nx, nz = E_ - 0.0035, -0.041; d.rounded_rectangle([*P(nx - 0.0072, nz + 0.0085), *P(nx + 0.0072, nz - 0.006)], 18, fill=(255, 241, 228), outline=CREASE, width=4)
d.line([P(E_ + 0.002, -0.078), P(E_ + 0.013, -0.082)], fill=CREASE, width=5)
front = shade(front); front.save(f"{OUT}/pov_front.png")
json.dump({"x0": X0, "x1": X1, "z0": Z0, "z1": Z1, "wrist": [E_ + 0.012, -0.178]}, open(f"{OUT}/pov_hand.json", "w"))
print("ok", Wpx, Hpx)
