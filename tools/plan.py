"""Split a job's frames across runners, one entry per runner. Prints matrix=<json> for GITHUB_OUTPUT.
Frames are interleaved (runner k renders start+k, start+k+n, ...) so heavy and light shots spread evenly
and every runner finishes at about the same time."""
import json, sys
job = json.load(open(sys.argv[1]))
if "frames" in job:  # explicit frame list (rescue renders)
    n = min(int(job.get("chunks", 20)), len(job["frames"]))
    print("matrix=" + json.dumps([{"start": k, "end": -1, "step": n} for k in range(n)])); sys.exit(0)
start, end = int(job["start"]), int(job["end"])
n = max(1, min(int(job.get("chunks", 20)), end - start + 1))
print("matrix=" + json.dumps([{"start": start + k, "end": end, "step": n} for k in range(n)]))
