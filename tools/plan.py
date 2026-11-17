"""Split a job's frame range into chunks, one per runner. Prints matrix=<json> for GITHUB_OUTPUT."""
import json, sys
job = json.load(open(sys.argv[1]))
start, end = int(job["start"]), int(job["end"])
n = max(1, min(int(job.get("chunks", 20)), end - start + 1))
total = end - start + 1
chunks, s = [], start
for i in range(n):
    size = total // n + (1 if i < total % n else 0)
    chunks.append({"start": s, "end": s + size - 1})
    s += size
print("matrix=" + json.dumps(chunks))
