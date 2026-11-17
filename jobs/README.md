One JSON file per render. Pushing a new or changed file here starts a render.

{
  "blend": "scenes/<name>/<name>.blend",   scene file (textures packed inside)
  "start": 1, "end": 900,                  frame range
  "fps": 30,
  "res": [720, 1280],                      render size (default 720p: ~2.25x faster)
  "output": [1080, 1920],                  final MP4 size (upscaled)
  "samples": 40,                           Cycles samples (default 40 + denoise: ~1.5x faster)
  "chunks": 20,                            parallel machines (max 20 on the free plan)
  "audio": "audio/<name>.m4a"              optional soundtrack
}

Defaults (Nov 17): render at 720x1280 with 40 samples and denoising, then upscale to 1080x1920 when stitching.
About 1 hour for a 30 s realistic Short on 20 free runners.
