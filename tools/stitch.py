"""Join rendered frames into the final MP4 (upscaled to the job's output size, optional audio).
Prints a short markdown summary for the run page."""
import glob, json, os, subprocess, sys
job = json.load(open(sys.argv[1])); frames, out = sys.argv[2], sys.argv[3]
files = sorted(glob.glob(os.path.join(frames, "*.png")))
want = int(job["end"]) - int(job["start"]) + 1
if len(files) != want:
    sys.exit(f"Expected {want} frames, got {len(files)}")
ow, oh = job.get("output", [1080, 1920])
cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(job.get("fps", 30)), "-start_number", str(job["start"]),
       "-i", os.path.join(frames, "%05d.png")]
if job.get("audio"):
    cmd += ["-i", job["audio"], "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "256k", "-shortest"]
cmd += ["-vf", f"scale={ow}:{oh}:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
mb = os.path.getsize(out) / 1e6
print(f"### {out}\n{want} frames, {ow}x{oh}, {mb:.1f} MB. Download it from the Releases page or the artifacts below.")
