"""Runs inside Blender on the runner: apply the job's render settings, then render one chunk of frames.
Usage: blender -b scene.blend --python tools/cloud_render.py -- job.json START END OUTDIR"""
import bpy, json, os, sys, time
args = sys.argv[sys.argv.index("--") + 1:]
job = json.load(open(args[0])); start, end, outdir = int(args[1]), int(args[2]), args[3]
step = int(args[4]) if len(args) > 4 and args[4] else 1
s = bpy.context.scene
w, h = job.get("res", [720, 1280])  # default: render 720p, stitch upscales to 1080p
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = int(w), int(h), 100
s.render.fps = int(job.get("fps", 30))
s.render.engine = "CYCLES"
c = s.cycles
c.device = "CPU"
c.samples = int(job.get("samples", 40))  # fast default; OIDN denoise cleans the rest
c.use_adaptive_sampling = True
c.adaptive_threshold = float(job.get("noise_threshold", 0.05))
c.denoising_input_passes = "RGB_ALBEDO_NORMAL"; c.denoising_prefilter = "ACCURATE"
c.use_denoising = True
c.denoiser = "OPENIMAGEDENOISE"
c.max_bounces = int(job.get("max_bounces", 6))
c.transparent_max_bounces = max(8, c.transparent_max_bounces)
s.render.use_persistent_data = True
s.render.threads_mode = "AUTO"
s.render.image_settings.file_format = "PNG"
s.render.image_settings.color_mode = "RGB"
s.render.use_file_extension = True
os.makedirs(outdir, exist_ok=True)
t0 = time.time()
frames = job["frames"][start::step] if "frames" in job else list(range(start, end + 1, step))
for f in frames:
    s.frame_set(f)
    s.render.filepath = os.path.join(outdir, f"{f:05d}.png")
    tf = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"CUBEY frame {f} {time.time() - tf:.1f}s", flush=True)
n = len(frames)
print(f"CUBEY chunk {start}-{end}: {n} frames in {time.time() - t0:.0f}s ({(time.time() - t0) / n:.1f}s/frame)", flush=True)
