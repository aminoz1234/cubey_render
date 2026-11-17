# cubey_render

Free cloud rendering for Cubey Shorts on GitHub Actions.
A job file in `jobs/` splits the frames across up to 20 free runners (Blender 5.2 LTS, Cycles on CPU),
then one more job joins them into an MP4 and publishes it under Releases.

- Add the scene: `scenes/<name>/<name>.blend` with textures packed (File > External Data > Pack Resources). Keep it under 100 MB.
- Add `jobs/<name>.json` (see `jobs/README.md`) and push. Or start it from Actions > render > Run workflow.
- Download the MP4 from Releases.
