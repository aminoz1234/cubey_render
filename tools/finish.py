"""Camera finish: makes CG frames read as 'filmed' for a few milliseconds per frame, no re-render.
Applied after the cloud render (locally), so it can be tweaked without rendering again.

  python3 finish.py IN_DIR OUT_DIR [--mist MIST_DIR] [--haze 0.35] [--grade warm|cool|neutral]

Steps (in order, like a real camera):
  1. depth haze from the mist pass (fake volumetric fog: the effect that cost hours as a real volume)
  2. halation + bloom: bright areas bleed a soft warm glow
  3. lens: slight barrel distortion + chromatic aberration growing toward the edges
  4. vignette
  5. grade: filmic S-curve, split toning (cool shadows, warm highlights)
  6. sharpen (helps the 720p -> 1080p upscale)
  7. animated film grain (luma-weighted, different every frame)
"""
import argparse, glob, os
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--mist"); ap.add_argument("--haze", type=float, default=0.3)
ap.add_argument("--haze_color", default="1.0,0.85,0.8")
ap.add_argument("--grade", default="warm"); ap.add_argument("--size", default="1080x1920")
ap.add_argument("--bloom", type=float, default=0.22); ap.add_argument("--grain", type=float, default=0.014)
ap.add_argument("--ca", type=float, default=0.0025); ap.add_argument("--distort", type=float, default=0.035)
ap.add_argument("--vignette", type=float, default=0.3)
a = ap.parse_args()
W, H = map(int, a.size.split("x"))
os.makedirs(a.out, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
cx, cy = (W - 1) / 2, (H - 1) / 2
nx, ny = (xx - cx) / cx, (yy - cy) / cy
r2 = nx * nx * (W / H) ** 2 + ny * ny          # aspect-correct radius^2
r2n = r2 / r2.max()

def remap_for(k):                                 # barrel distortion with strength k
    f = 1 + k * r2n
    return (cx + (xx - cx) / f).astype(np.float32), (cy + (yy - cy) / f).astype(np.float32)

MAPS = {c: remap_for(a.distort + d) for c, d in (("r", a.ca), ("g", 0.0), ("b", -a.ca))}
VIG = (1 - a.vignette * np.clip(r2n, 0, 1) ** 1.3)[..., None]
HAZE = np.array([float(x) for x in a.haze_color.split(",")], np.float32)[::-1]  # BGR
GRADES = {
    "warm": dict(sh=(1.03, 1.0, 0.94), hi=(0.95, 1.0, 1.05)),     # BGR: cool shadows, warm highlights
    "cool": dict(sh=(1.06, 1.0, 0.95), hi=(1.0, 1.0, 1.0)),
    "neutral": dict(sh=(1, 1, 1), hi=(1, 1, 1)),
}[a.grade]

def scurve(x, k=0.35):  # filmic S-curve: deeper shadows, brighter highlights, soft roll-off
    s = x * x * (3 - 2 * x)           # smoothstep
    return np.clip(x * (1 - k) + s * k, 0, 1)

rng = np.random.default_rng(1)
files = sorted(glob.glob(os.path.join(a.inp, "*.png")))
for i, fp in enumerate(files):
    img = cv2.imread(fp, cv2.IMREAD_COLOR).astype(np.float32) / 255.0
    img = np.clip(cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4), 0, 1)
    lin = img ** 2.2                                                  # work in linear light
    if a.mist:  # 1. depth haze
        mp = os.path.join(a.mist, os.path.basename(fp))
        if os.path.exists(mp):
            m = cv2.resize(cv2.imread(mp, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0, (W, H))
            m = np.clip(m, 0, 1)[..., None] ** 1.4 * a.haze
            lin = lin * (1 - m) + (HAZE ** 2.2) * 0.35 * m
    # 2. halation + bloom from highlights
    lum = lin.max(axis=2, keepdims=True)
    hi = lin * np.clip((lum - 0.55) / 0.45, 0, 1)
    bloom = cv2.GaussianBlur(hi, (0, 0), W * 0.02) * 0.6 + cv2.GaussianBlur(hi, (0, 0), W * 0.06) * 0.4
    hal = cv2.GaussianBlur(hi, (0, 0), W * 0.008) * np.array([0.25, 0.45, 1.0], np.float32)  # red-orange edge glow
    lin = lin + bloom * a.bloom + hal * a.bloom * 0.5
    # 3. lens distortion + chromatic aberration (per channel)
    b, g, r = cv2.split(lin)
    b = cv2.remap(b, *MAPS["b"], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    g = cv2.remap(g, *MAPS["g"], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    r = cv2.remap(r, *MAPS["r"], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    lin = cv2.merge([b, g, r])
    # 4. vignette
    lin = lin * VIG
    # 5. grade (back to display space)
    out = np.clip(lin, 0, 1) ** (1 / 2.2)
    out = scurve(out)
    grey = out.mean(axis=2, keepdims=True)
    out = np.clip(grey + (out - grey) * 1.15, 0, 1)                    # +15% saturation
    l = out.mean(axis=2, keepdims=True)
    out = out * (np.array(GRADES["sh"], np.float32) * (1 - l) + np.array(GRADES["hi"], np.float32) * l)
    # 6. sharpen (unsharp mask)
    blur = cv2.GaussianBlur(out, (0, 0), 1.2)
    out = cv2.addWeighted(out, 1.35, blur, -0.35, 0)
    # 7. animated grain, strongest in the mids
    gr = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
    gr = cv2.resize(gr, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    mid = 1 - (2 * out.mean(axis=2, keepdims=True) - 1) ** 2
    out = out + gr * a.grain * (0.4 + 0.6 * mid)
    cv2.imwrite(os.path.join(a.out, os.path.basename(fp)), np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8))
    if i % 100 == 0:
        print("finished", i, "/", len(files), flush=True)
print("done", len(files))
