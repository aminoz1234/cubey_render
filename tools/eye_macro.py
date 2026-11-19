"""Macro human eye set (10x scale) for the cat-scratch video. exec() after common_build.py; call eye_set(X0).
Eyeball radius 0.12 (real 12 mm). Looks along -Y. Returns dict of objects and the cornea node handles:
  N_L (cut length 0..1), N_W (cut width), N_U (ulcer radius), N_NERVE (nerve glow), N_RED (sclera redness)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

R = 0.12


def _val(nt, name, v):
    n = nt.nodes.new("ShaderNodeValue"); n.name = name; n.label = name; n.outputs[0].default_value = v
    return n


def eyeball_mat(nt_name="eyeball"):
    m = bpy.data.materials.new(nt_name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    # radial distance from the visual axis (object y is the axis, front = -y)
    cxz = N.new("ShaderNodeCombineXYZ"); L.new(sp.outputs["X"], cxz.inputs["X"]); L.new(sp.outputs["Z"], cxz.inputs["Y"])
    rr = N.new("ShaderNodeVectorMath"); rr.operation = "LENGTH"; L.new(cxz.outputs[0], rr.inputs[0])
    front = N.new("ShaderNodeMath"); front.operation = "LESS_THAN"; front.inputs[1].default_value = 0.0; L.new(sp.outputs["Y"], front.inputs[0])
    # iris fibres: noise in (angle, radius) space
    at = N.new("ShaderNodeMath"); at.operation = "ARCTAN2"; L.new(sp.outputs["X"], at.inputs[0]); L.new(sp.outputs["Z"], at.inputs[1])
    pol = N.new("ShaderNodeCombineXYZ"); am = N.new("ShaderNodeMath"); am.operation = "MULTIPLY"; am.inputs[1].default_value = 14
    L.new(at.outputs[0], am.inputs[0]); L.new(am.outputs[0], pol.inputs["X"])
    rm = N.new("ShaderNodeMath"); rm.operation = "MULTIPLY"; rm.inputs[1].default_value = 1.2; L.new(rr.outputs["Value"], rm.inputs[0]); L.new(rm.outputs[0], pol.inputs["Y"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 8
    L.new(pol.outputs[0], nz.inputs["Vector"])
    nz.noise_dimensions = "2D"
    ic = N.new("ShaderNodeValToRGB"); e = ic.color_ramp.elements
    e[0].position = 0.3; e[0].color = (0.09, 0.045, 0.015, 1); e[1].position = 0.72; e[1].color = (0.62, 0.38, 0.13, 1)
    L.new(nz.outputs["Fac"], ic.inputs[0])
    # radial zones: pupil < 0.16, collarette ring, iris < 0.42, dark limbus to 0.45, sclera
    zone = N.new("ShaderNodeValToRGB"); zr = zone.color_ramp; zr.interpolation = "LINEAR"
    zr.elements[0].position = 0.11; zr.elements[0].color = (0, 0, 0, 1)        # pupil
    for pos, c in ((0.125, (1, 1, 1, 1)), (0.40, (0.85, 0.85, 0.85, 1)), (0.43, (0.15, 0.15, 0.15, 1))):
        el = zr.elements.new(pos); el.color = c
    zr.elements[-1].position = 0.47; zr.elements[-1].color = (0.0, 0.0, 0.0, 1)   # beyond: mask 0 -> sclera
    L.new(rr.outputs["Value"], zone.inputs[0])
    irisc = N.new("ShaderNodeMix"); irisc.data_type = "RGBA"; irisc.blend_type = "MULTIPLY"; irisc.inputs["Factor"].default_value = 1
    L.new(ic.outputs["Color"], irisc.inputs["A"]); L.new(zone.outputs["Color"], irisc.inputs["B"])
    # sclera with veins, redness keyable
    vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = 4
    nzv = N.new("ShaderNodeTexNoise"); nzv.inputs["Scale"].default_value = 3
    L.new(tc.outputs["Object"], nzv.inputs["Vector"])
    warp = N.new("ShaderNodeMix"); warp.data_type = "VECTOR"; warp.inputs["Factor"].default_value = 0.6
    L.new(tc.outputs["Object"], warp.inputs["A"]); L.new(nzv.outputs["Color"], warp.inputs["B"]); L.new(warp.outputs["Result"], vor.inputs["Vector"])
    vein = N.new("ShaderNodeMapRange"); vein.inputs["From Min"].default_value = 0.012; vein.inputs["From Max"].default_value = 0.0
    L.new(vor.outputs["Distance"], vein.inputs["Value"])
    red = _val(nt, "RED", 0.0)
    vstr = N.new("ShaderNodeMath"); vstr.operation = "MULTIPLY_ADD"; vstr.inputs[1].default_value = 0.75; vstr.inputs[2].default_value = 0.25
    L.new(red.outputs[0], vstr.inputs[0])
    vfac = N.new("ShaderNodeMath"); vfac.operation = "MULTIPLY"; L.new(vstr.outputs[0], vfac.inputs[0]); L.new(vein.outputs["Result"], vfac.inputs[1])
    # limbal ring is far from vessels; vessels fade toward the cornea
    lim = N.new("ShaderNodeMapRange"); lim.inputs["From Min"].default_value = 0.5; lim.inputs["From Max"].default_value = 0.85
    L.new(rr.outputs["Value"], lim.inputs["Value"])
    lim2 = N.new("ShaderNodeMath"); lim2.operation = "MULTIPLY"; L.new(lim.outputs["Result"], lim2.inputs[0]); L.new(vfac.outputs[0], lim2.inputs[1])
    flush = N.new("ShaderNodeMath"); flush.operation = "MULTIPLY"; flush.inputs[1].default_value = 0.35; L.new(red.outputs[0], flush.inputs[0])
    sc0 = N.new("ShaderNodeMix"); sc0.data_type = "RGBA"; L.new(flush.outputs[0], sc0.inputs["Factor"])
    sc0.inputs["A"].default_value = (0.82, 0.78, 0.72, 1); sc0.inputs["B"].default_value = (0.75, 0.32, 0.28, 1)
    scl = N.new("ShaderNodeMix"); scl.data_type = "RGBA"; L.new(lim2.outputs[0], scl.inputs["Factor"])
    L.new(sc0.outputs["Result"], scl.inputs["A"]); scl.inputs["B"].default_value = (0.55, 0.05, 0.04, 1)
    # iris region mask (front hemisphere, r < 0.47)
    im = N.new("ShaderNodeMath"); im.operation = "LESS_THAN"; im.inputs[1].default_value = 0.47; L.new(rr.outputs["Value"], im.inputs[0])
    imf = N.new("ShaderNodeMath"); imf.operation = "MULTIPLY"; L.new(im.outputs[0], imf.inputs[0]); L.new(front.outputs[0], imf.inputs[1])
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"; L.new(imf.outputs[0], col.inputs["Factor"])
    L.new(scl.outputs["Result"], col.inputs["A"]); L.new(irisc.outputs["Result"], col.inputs["B"])
    L.new(col.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.25; b.inputs["Subsurface Scale"].default_value = 0.01
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.25)
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def cornea_mat():
    """Clear cornea with a keyable scratch (segment a->b grown by L, width W), ulcer (radius U) and nerve glow."""
    m = bpy.data.materials.new("cornea"); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    # thin clear shell: transparent + mirror-sharp gloss by Fresnel (no refraction darkening)
    b.inputs["Roughness"].default_value = 0.0; b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    trn = N.new("ShaderNodeBsdfTransparent"); gls = N.new("ShaderNodeBsdfGlossy"); gls.inputs["Roughness"].default_value = 0.02
    frn = N.new("ShaderNodeFresnel"); frn.inputs["IOR"].default_value = 1.45
    clear = N.new("ShaderNodeMixShader"); L.new(frn.outputs[0], clear.inputs[0]); L.new(trn.outputs[0], clear.inputs[1]); L.new(gls.outputs[0], clear.inputs[2])
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    p2 = N.new("ShaderNodeCombineXYZ"); L.new(sp.outputs["X"], p2.inputs["X"]); L.new(sp.outputs["Z"], p2.inputs["Y"])
    A = Vector((-0.42, 0.3, 0)); D = Vector((0.8, -0.55, 0))
    va = N.new("ShaderNodeVectorMath"); va.operation = "SUBTRACT"; L.new(p2.outputs[0], va.inputs[0]); va.inputs[1].default_value = A
    dt = N.new("ShaderNodeVectorMath"); dt.operation = "DOT_PRODUCT"; L.new(va.outputs[0], dt.inputs[0]); dt.inputs[1].default_value = D
    dv = N.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = D.length_squared; L.new(dt.outputs["Value"], dv.inputs[0])
    nL = _val(nt, "L", 0.0); nW = _val(nt, "W", 0.035); nU = _val(nt, "U", 0.0); nN = _val(nt, "NERVE", 0.0)
    cl = N.new("ShaderNodeClamp"); L.new(dv.outputs[0], cl.inputs["Value"]); cl.inputs["Min"].default_value = 0.0; L.new(nL.outputs[0], cl.inputs["Max"])
    sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs[0].default_value = D; L.new(cl.outputs[0], sc.inputs["Scale"])
    q = N.new("ShaderNodeVectorMath"); q.operation = "SUBTRACT"; L.new(va.outputs[0], q.inputs[0]); L.new(sc.outputs[0], q.inputs[1])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(q.outputs[0], ln.inputs[0])
    # wobbly edge
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    wob = N.new("ShaderNodeMath"); wob.operation = "MULTIPLY_ADD"; wob.inputs[1].default_value = 0.015; wob.inputs[2].default_value = -0.0075
    L.new(nz.outputs["Fac"], wob.inputs[0])
    dd = N.new("ShaderNodeMath"); dd.operation = "ADD"; L.new(ln.outputs["Value"], dd.inputs[0]); L.new(wob.outputs[0], dd.inputs[1])
    cut = N.new("ShaderNodeMath"); cut.operation = "LESS_THAN"; L.new(dd.outputs[0], cut.inputs[0]); L.new(nW.outputs[0], cut.inputs[1])
    # only where L > 0
    on = N.new("ShaderNodeMath"); on.operation = "GREATER_THAN"; on.inputs[1].default_value = 0.001; L.new(nL.outputs[0], on.inputs[0])
    cutm = N.new("ShaderNodeMath"); cutm.operation = "MULTIPLY"; L.new(cut.outputs[0], cutm.inputs[0]); L.new(on.outputs[0], cutm.inputs[1])
    # ulcer: noisy disc around the middle of the scratch
    cU = N.new("ShaderNodeVectorMath"); cU.operation = "DISTANCE"; L.new(p2.outputs[0], cU.inputs[0]); cU.inputs[1].default_value = A + D * 0.5
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 9; nz2.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    ud = N.new("ShaderNodeMath"); ud.operation = "MULTIPLY_ADD"; ud.inputs[1].default_value = 0.25; L.new(nz2.outputs["Fac"], ud.inputs[0]); L.new(cU.outputs["Value"], ud.inputs[2])
    um = N.new("ShaderNodeMath"); um.operation = "SUBTRACT"; L.new(nU.outputs[0], um.inputs[0]); L.new(ud.outputs[0], um.inputs[1])
    um2 = N.new("ShaderNodeMath"); um2.operation = "MULTIPLY"; um2.inputs[1].default_value = 12; um2.use_clamp = True; L.new(um.outputs[0], um2.inputs[0])
    um3 = N.new("ShaderNodeMath"); um3.operation = "ADD"; um3.inputs[1].default_value = 0.125; L.new(um2.outputs[0], um3.inputs[0])   # offset fixes 0 at U=0
    ulc = N.new("ShaderNodeMath"); ulc.operation = "MULTIPLY"; ulc.use_clamp = True; L.new(um2.outputs[0], ulc.inputs[0]); ulc.inputs[1].default_value = 1.0
    opaque = N.new("ShaderNodeMath"); opaque.operation = "MAXIMUM"; L.new(cutm.outputs[0], opaque.inputs[0]); L.new(ulc.outputs[0], opaque.inputs[1])
    # damaged tissue: cloudy white-grey, rough, slightly yellow in the ulcer
    w = N.new("ShaderNodeBsdfPrincipled"); w.inputs["Base Color"].default_value = (0.85, 0.82, 0.72, 1); w.inputs["Roughness"].default_value = 0.6
    w.inputs["Subsurface Weight"].default_value = 0.6; w.inputs["Subsurface Scale"].default_value = 0.01
    mix = N.new("ShaderNodeMixShader"); L.new(opaque.outputs[0], mix.inputs[0]); L.new(clear.outputs[0], mix.inputs[1]); L.new(w.outputs[0], mix.inputs[2])
    # nerves: thin voronoi edges glowing blue-white
    vr = N.new("ShaderNodeTexVoronoi"); vr.feature = "DISTANCE_TO_EDGE"; vr.inputs["Scale"].default_value = 6
    nzw = N.new("ShaderNodeMix"); nzw.data_type = "VECTOR"; nzw.inputs["Factor"].default_value = 0.4
    L.new(tc.outputs["Object"], nzw.inputs["A"]); L.new(nz2.outputs["Color"], nzw.inputs["B"]); L.new(nzw.outputs["Result"], vr.inputs["Vector"])
    nv = N.new("ShaderNodeMapRange"); nv.inputs["From Min"].default_value = 0.012; nv.inputs["From Max"].default_value = 0.0
    L.new(vr.outputs["Distance"], nv.inputs["Value"])
    ne = N.new("ShaderNodeMath"); ne.operation = "MULTIPLY"; L.new(nv.outputs["Result"], ne.inputs[0]); L.new(nN.outputs[0], ne.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.55, 0.8, 1.0, 1); L.new(ne.outputs[0], em.inputs["Strength"])
    add = N.new("ShaderNodeAddShader"); L.new(mix.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1])
    L.new(add.outputs[0], N["Material Output"].inputs["Surface"])
    # groove bump along the scratch
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.invert = True
    hgt = N.new("ShaderNodeMath"); hgt.operation = "MAXIMUM"; L.new(cutm.outputs[0], hgt.inputs[0]); L.new(ulc.outputs[0], hgt.inputs[1])
    L.new(hgt.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], gls.inputs["Normal"]); L.new(bp.outputs["Normal"], w.inputs["Normal"])
    return m, nL, nW, nU, nN


def eye_set(X0, skin_mat):
    out = {}
    c0 = Vector((X0, 0, 0))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=1.0)
    me = bpy.data.meshes.new("eyeball"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    em = eyeball_mat(); me.materials.append(em)
    ball = link(bpy.data.objects.new("eyeball", me)); ball.location = c0; ball.scale = (R,) * 3
    out["ball"] = ball; out["N_RED"] = em.node_tree.nodes["RED"]
    # cornea dome: front cap pushed forward
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=96, radius=1.0)
    kill = [v for v in bm.verts if v.co.y > -0.86]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    for v in bm.verts:
        r2 = v.co.x ** 2 + v.co.z ** 2
        v.co.y -= 0.17 * max(0.0, 1 - r2 / 0.26)
        v.co *= 1.012
    me = bpy.data.meshes.new("cornea"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    cm, nL, nW, nU, nN = cornea_mat(); me.materials.append(cm)
    cor = link(bpy.data.objects.new("cornea", me)); cor.location = c0; cor.scale = (R,) * 3
    cor.modifiers.new("sub", "SUBSURF").levels = 1
    out.update(cornea=cor, N_L=nL, N_W=nW, N_U=nU, N_NERVE=nN)
    # eyelids: skin sheet with an almond opening, wrapped around the ball
    bm = bmesh.new(); NA, NR = 128, 26
    def margin(th):
        x = 0.135 * math.cos(th); sn = math.sin(th)
        h = (0.07 * (1 - (x / 0.135) ** 2) ** 0.8 + 0.006) if sn >= 0 else -(0.05 * (1 - (x / 0.135) ** 2) ** 0.9 + 0.004)
        return x, h + 0.004 * x / 0.135
    rings = []
    for k in range(NR + 1):
        t = (k / NR) ** 1.6
        ring = []
        for a_ in range(NA):
            th = 2 * math.pi * a_ / NA; mx_, mz_ = margin(th)
            ox, oz = 0.5 * math.cos(th), 0.5 * math.sin(th)
            ring.append(bm.verts.new((mx_ + (ox - mx_) * t, 0, mz_ + (oz - mz_) * t)))
        rings.append(ring)
    for k in range(NR):
        for a_ in range(NA):
            bm.faces.new((rings[k][a_], rings[k][(a_ + 1) % NA], rings[k + 1][(a_ + 1) % NA], rings[k + 1][a_]))
    for v in bm.verts:
        x, z = v.co.x, v.co.z; r = math.hypot(x, z)
        rr_ = R + 0.012
        y = -math.sqrt(max(0.0, rr_ ** 2 - r ** 2)) if r < rr_ else 0.0
        y = y * (1 - min(1, max(0, (r - 0.1) / 0.3))) - 0.02 * min(1, r / 0.3)   # flatten out to the face
        v.co = Vector((x, y - 0.012, z))
    me = bpy.data.meshes.new("lids"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(skin_mat)
    lids = link(bpy.data.objects.new("lids", me)); lids.location = c0
    so = lids.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.02; so.offset = 1.0
    lids.modifiers.new("sub", "SUBSURF").levels = 1
    out["lids"] = lids
    # lashes on the upper and lower lid margins
    bl = bmesh.new(); rnd = random.Random(7)
    for k in range(90):
        up = k < 60
        x = rnd.uniform(-0.12, 0.12)
        h = (0.07 * (1 - (x / 0.135) ** 2) ** 0.8 + 0.008) if up else -(0.05 * (1 - (x / 0.135) ** 2) ** 0.9 + 0.006)
        r = math.hypot(x, h); y = -math.sqrt(max(0, (R + 0.016) ** 2 - r ** 2)) - 0.012
        base = Vector((x, y, h))
        d = Vector((x * 0.8, -1.0, 0.7 if up else -0.6)).normalized()
        ln = rnd.uniform(0.045, 0.07) * (1 if up else 0.45)
        segs = 5; prev = None
        for s in range(segs):
            t = s / (segs - 1)
            curl = Vector((0, 0, (0.55 if up else -0.35) * t * t * ln))
            p0 = base + d * ln * t + curl
            if prev is not None:
                mid = (prev + p0) / 2; dirv = (p0 - prev); L_ = dirv.length
                rad = 0.0008 * (1 - t) + 0.00012
                bmesh.ops.create_cone(bl, cap_ends=False, segments=5, radius1=rad * 1.15, radius2=rad, depth=L_,
                                      matrix=Matrix.Translation(mid) @ dirv.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4())
            prev = p0
    me = bpy.data.meshes.new("lashes"); bl.to_mesh(me); bl.free()
    lm = bpy.data.materials.new("lash"); lm.use_nodes = True; lb = lm.node_tree.nodes["Principled BSDF"]
    lb.inputs["Base Color"].default_value = (0.015, 0.01, 0.008, 1); lb.inputs["Roughness"].default_value = 0.35
    me.materials.append(lm)
    lashes = link(bpy.data.objects.new("lashes", me)); lashes.location = c0
    out["lashes"] = lashes
    # tear film meniscus along the lower lid (wet line)
    return out
