"""Realism kit for the Cubey body-interior shots (Blender 5.2+, Cycles).
Wet living tissue, liquids, glossy seeds, haze. Import with exec(open(...).read())."""
import bpy, math
from mathutils import Vector


def _nodes(m):
    m.use_nodes = True
    nt = m.node_tree
    return nt, nt.nodes, nt.links


def tissue(name, base=(0.55, 0.08, 0.07), crease=(0.18, 0.02, 0.02), sss=0.35, wet=1.0, bump=0.35, scale=6.0):
    """Wet living tissue: subsurface flesh, darker creases (pointiness), mucus coat, fine bumpy detail, veins."""
    m = bpy.data.materials.new(name); nt, N, L = _nodes(m)
    b = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry")
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.47; ramp.color_ramp.elements[0].color = (*crease, 1)
    ramp.color_ramp.elements[1].position = 0.56; ramp.color_ramp.elements[1].color = (*base, 1)
    L.new(geo.outputs["Pointiness"], ramp.inputs[0])
    # veins: thin dark-red voronoi edges mixed into the color
    tc = N.new("ShaderNodeTexCoord")
    vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = scale * 0.6
    L.new(tc.outputs["Object"], vor.inputs["Vector"])
    vr = N.new("ShaderNodeValToRGB")
    vr.color_ramp.elements[0].position = 0.0; vr.color_ramp.elements[0].color = (0.25, 0.01, 0.02, 1)
    vr.color_ramp.elements[1].position = 0.035; vr.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(vor.outputs["Distance"], vr.inputs[0])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 0.55
    L.new(ramp.outputs["Color"], mix.inputs["A"]); L.new(vr.outputs["Color"], mix.inputs["B"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.25, 0.12)
    b.inputs["Subsurface Scale"].default_value = 0.08
    b.inputs["Roughness"].default_value = 0.45
    b.inputs["Coat Weight"].default_value = wet
    b.inputs["Coat Roughness"].default_value = 0.04
    b.inputs["Coat IOR"].default_value = 1.38
    b.inputs["Specular IOR Level"].default_value = 0.6
    # fine surface detail (pores / mucus irregularity)
    n1 = N.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = scale * 9; n1.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], n1.inputs["Vector"])
    bm = N.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = bump; bm.inputs["Distance"].default_value = 0.02
    L.new(n1.outputs["Fac"], bm.inputs["Height"])
    L.new(bm.outputs["Normal"], b.inputs["Normal"])
    # the coat gets its own lumpier normal so highlights break up like real mucus
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = scale * 2.5; n2.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], n2.inputs["Vector"])
    bm2 = N.new("ShaderNodeBump"); bm2.inputs["Strength"].default_value = 0.25
    L.new(n2.outputs["Fac"], bm2.inputs["Height"]); L.new(bm2.outputs["Normal"], b.inputs["Coat Normal"])
    return m


def liquid(name, tint=(0.55, 0.85, 0.12), density=0.8, rough=0.02, glow=0.0):
    """Transparent liquid with colored absorption (use on a closed mesh / solidified surface)."""
    m = bpy.data.materials.new(name); nt, N, L = _nodes(m)
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.34
    vol = N.new("ShaderNodeVolumeAbsorption"); vol.inputs["Color"].default_value = (*tint, 1); vol.inputs["Density"].default_value = density
    out = N["Material Output"]
    if glow:
        em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*tint, 1); em.inputs["Strength"].default_value = glow
        add = N.new("ShaderNodeAddShader"); L.new(vol.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1])
        L.new(add.outputs[0], out.inputs["Volume"])
    else:
        L.new(vol.outputs[0], out.inputs["Volume"])
    return m


def glossy_seed(name, col=(0.035, 0.025, 0.018), rim=(0.35, 0.25, 0.14)):
    """Watermelon seed: dark lacquered shell with a lighter rim and fine ridges."""
    m = bpy.data.materials.new(name); nt, N, L = _nodes(m)
    b = N["Principled BSDF"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*col, 1); mix.inputs["B"].default_value = (*rim, 1)
    L.new(lw.outputs["Fresnel"], mix.inputs["Factor"]); L.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.18
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.08
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 25; wv.inputs["Distortion"].default_value = 3
    bm = N.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.08
    L.new(wv.outputs["Fac"], bm.inputs["Height"]); L.new(bm.outputs["Normal"], b.inputs["Normal"])
    return m


def bubble_mat(name):
    m = bpy.data.materials.new(name); nt, N, L = _nodes(m)
    b = N["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.0
    b.inputs["IOR"].default_value = 1.0 / 1.33 + 0.05
    b.inputs["Thin Film Thickness"].default_value = 450
    return m


def haze(name, loc, size, density=0.04, col=(1.0, 0.8, 0.75)):
    """Box of light volumetric scatter for depth and light shafts."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); ob = bpy.context.object; ob.name = name; ob.scale = size
    m = bpy.data.materials.new(name + "_vol"); nt, N, L = _nodes(m)
    N.remove(N["Principled BSDF"])
    sc = N.new("ShaderNodeVolumeScatter"); sc.inputs["Density"].default_value = density; sc.inputs["Color"].default_value = (*col, 1)
    sc.inputs["Anisotropy"].default_value = 0.4
    L.new(sc.outputs[0], N["Material Output"].inputs["Volume"])
    ob.data.materials.append(m); ob.visible_shadow = False
    return ob


def cycles_quality(scene, samples=96, res=(1080, 1920), dof=True):
    scene.render.engine = "CYCLES"
    c = scene.cycles
    c.samples = samples; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.02
    c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 8; c.transmission_bounces = 8; c.transparent_max_bounces = 16; c.volume_bounces = 1
    c.caustics_reflective = False; c.caustics_refractive = False; c.blur_glossy = 1.0
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0
    scene.render.film_transparent = False


def macro_cam(cam, focus_obj, fstop=2.0, lens=50):
    cam.data.lens = lens
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = focus_obj; cam.data.dof.aperture_fstop = fstop
    cam.data.sensor_width = 36
