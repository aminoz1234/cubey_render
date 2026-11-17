One JSON file per render. Pushing a new or changed file here starts a render.

{
  "blend": "scenes/<name>/<name>.blend",   scene file (textures packed inside)
  "start": 1, "end": 900,                  frame range
  "fps": 30,
  "res": [720, 1280],                      render size
  "output": [1080, 1920],                  final MP4 size (upscaled)
  "samples": 32,                           Cycles samples (denoised)
  "chunks": 20,                            parallel machines (max 20 on the free plan)
  "audio": "audio/<name>.m4a"              optional soundtrack
}
