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
c.max_bounces = int(job.get("max_bounces", 4))          # fewer bounces: most of the look is direct light
c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transmission_bounces = 4; c.volume_bounces = 0
c.caustics_reflective = False; c.caustics_refractive = False   # caustics = noise for little gain
c.blur_glossy = 1.0                                           # filter glossy: kills glossy noise
c.sample_clamp_indirect = 10.0                                # no fireflies from bright bounces
for m in bpy.data.materials:                                  # cheaper skin/tissue scattering
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED" and hasattr(n, "subsurface_method"):
                n.subsurface_method = "BURLEY"
c.transparent_max_bounces = max(8, c.transparent_max_bounces)
s.render.use_persistent_data = True
s.render.threads_mode = "AUTO"
s.render.image_settings.file_format = "PNG"
s.render.image_settings.color_mode = "RGB"
s.render.use_file_extension = True
os.makedirs(outdir, exist_ok=True)
t0 = time.time()
ALL = list(job["frames"]) if "frames" in job else list(range(int(job["start"]), int(job["end"]) + 1))
mine = job["frames"][start::step] if "frames" in job else list(range(start, end + 1, step))

BORD = json.load(open(job["borders"])) if "borders" in job else None   # {frame: [x0, y0, x1, y1]} in 0..1, y up: patch renders
def render(f):
    s.frame_set(f)
    if BORD is not None:
        b = BORD.get(str(f), [0, 0, 0.01, 0.01])
        s.render.use_border = True; s.render.use_crop_to_border = False
        s.render.border_min_x, s.render.border_min_y, s.render.border_max_x, s.render.border_max_y = b
    s.render.filepath = os.path.join(outdir, f"{f:05d}.png")
    tf = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - tf
    print(f"CUBEY frame {f} {dt:.1f}s", flush=True)
    return dt

Q = os.environ.get("CUBEY_QUEUE")
done_n = 0
if not Q:  # old mode: fixed frames per runner
    for f in mine: render(f); done_n += 1
else:
    # Shared queue on a git branch: c/<frame>_<time> = claimed, d/<frame> = done.
    # Each runner takes its own frames first, then steals whatever is left (and
    # frames stuck on a runner that died), so nobody sits idle while others work.
    import subprocess, random
    REF, RREF = f"refs/heads/{Q}", f"refs/remotes/origin/{Q}"
    IDX = dict(os.environ, GIT_INDEX_FILE="/tmp/cubey_queue_idx")
    def git(*a, env=None, inp=""):
        return subprocess.run(["git", *a], capture_output=True, text=True, input=inp, env=env)
    EMPTY = git("hash-object", "-w", "--stdin").stdout.strip()
    def state():
        git("fetch", "-q", "--no-tags", "origin", f"+{REF}:{RREF}")
        tip = git("rev-parse", RREF).stdout.strip()
        claimed, done, first, count = {}, set(), {}, {}
        for p in git("ls-tree", "-r", "--name-only", tip).stdout.split():
            d, n = p.split("/", 1)
            if d == "d": done.add(int(n))
            elif d == "c":
                f, t = n.split("_"); f, t = int(f), int(t)
                claimed[f] = max(claimed.get(f, 0), t); first[f] = min(first.get(f, t), t); count[f] = count.get(f, 0) + 1
        state.first, state.count = first, count
        return tip, claimed, done
    def push(tip, paths):
        git("read-tree", tip, env=IDX)
        for p in paths: git("update-index", "--add", "--cacheinfo", f"100644,{EMPTY},{p}", env=IDX)
        tree = git("write-tree", env=IDX).stdout.strip()
        c = git("commit-tree", tree, "-p", tip, "-m", "q").stdout.strip()
        return git("push", "-q", "origin", f"{c}:{REF}").returncode == 0
    times, pending, mine_done = [], [], set()
    while True:
        f = None
        for attempt in range(40):
            tip, claimed, done = state()
            now = int(time.time())
            avg = sum(times) / len(times) if times else 60
            free = [x for x in mine if x not in claimed] or [x for x in ALL if x not in claimed]
            if free:
                f = free[0] if free[0] in mine else random.choice(free)
            else:
                # Nothing left to claim. Never sit idle while others still render: help with the
                # frames still in progress (oldest first, at most 3 runners per frame). Whoever
                # finishes first wins; dead runners' frames get picked up this way too.
                busy = [x for x in claimed if x not in done and x not in mine_done and state.count.get(x, 1) < 3]
                busy.sort(key=lambda x: (state.count.get(x, 1), state.first.get(x, now)))
                f = busy[0] if busy else None
            if f is None: break
            if push(tip, [f"c/{f:05d}_{now}"] + pending):
                pending = []; break
            f = None; time.sleep(random.uniform(0.5, 2.5))
        if f is None: break
        times.append(render(f)); done_n += 1; mine_done.add(f)
        pending.append(f"d/{f:05d}")
        for attempt in range(6):   # publish 'done' right away so nobody duplicates it
            tip, _, _ = state()
            if push(tip, pending): pending = []; break
            time.sleep(random.uniform(0.3, 1.5))
    for attempt in range(20):
        if not pending: break
        tip, _, _ = state()
        if push(tip, pending): pending = []
        else: time.sleep(random.uniform(0.5, 2.5))
print(f"CUBEY runner {start}: {done_n} frames in {time.time() - t0:.0f}s", flush=True)
