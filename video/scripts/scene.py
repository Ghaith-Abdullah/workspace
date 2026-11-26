"""Night desk scene: frosted window, wooden table, laptop, phone, mug.
Usage: python scene.py --seg A|B --frames 0,50,100 | --range a b  --out DIR [--samples N] [--pct 100]
"""
import bpy, bmesh, math, os, sys, json, argparse
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, 'tex'); FONTS = os.path.join(ROOT, 'fonts')
ap = argparse.ArgumentParser()
ap.add_argument('--seg', default='A'); ap.add_argument('--frames', default='')
ap.add_argument('--range', nargs=2, type=int); ap.add_argument('--out', default='out')
ap.add_argument('--samples', type=int, default=128); ap.add_argument('--pct', type=int, default=100)
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
FPS = 30

# ---------------------------------------------------------------- helpers
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_io(x): x = clamp(x); return 4 * x**3 if x < .5 else 1 - (-2 * x + 2)**3 / 2
def ease_in(x): x = clamp(x); return x**3
def ease_out(x): x = clamp(x); return 1 - (1 - x)**3
def lerpv(a, b, t): return Vector(a).lerp(Vector(b), t)

def rrect_verts(w, d, r, seg=10):
    pts = []
    cs = [(w/2-r, d/2-r, 0), (-w/2+r, d/2-r, 90), (-w/2+r, -d/2+r, 180), (w/2-r, -d/2+r, 270)]
    for cx, cy, a0 in cs:
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def rrect_prism(name, w, d, h, r, mat, bevel=0.0008, seg=10, z0=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    pts = rrect_verts(w, d, r, seg)
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z0 + h)) for x, y in pts]
    bm.faces.new(list(reversed(bot))); bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        bm.faces.new([bot[i], bot[(i+1) % n], top[(i+1) % n], top[i]])
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    if bevel > 0:
        m = ob.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = 3
        m.limit_method = 'ANGLE'; m.angle_limit = math.radians(50); m.harden_normals = True
    for p in me.polygons: p.use_smooth = True
    return ob

def box(name, size, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object; ob.name = name; ob.scale = size
    bpy.ops.object.transform_apply(scale=True); ob.data.materials.append(mat)
    if bevel:
        m = ob.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = 3
    return ob

def principled(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, coat=0.0, coat_rough=0.05, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = coat_rough
    b.inputs['Specular IOR Level'].default_value = spec
    return m

def img(path, colorspace='sRGB'):
    im = bpy.data.images.load(path, check_existing=True); im.colorspace_settings.name = colorspace; return im

# ---------------------------------------------------------------- reset & render settings
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = args.samples; sc.cycles.adaptive_threshold = 0.02
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 4
sc.cycles.transmission_bounces = 4; sc.cycles.sample_clamp_indirect = 4.0
sc.render.resolution_x = 1440; sc.render.resolution_y = 1080; sc.render.resolution_percentage = args.pct
sc.render.fps = FPS; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
sc.view_settings.view_transform = 'AgX'
for lk in ('AgX - Medium High Contrast', 'Medium High Contrast'):
    try: sc.view_settings.look = lk; break
    except Exception: pass
sc.view_settings.exposure = 0.0

world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.005, 0.009, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0

# ---------------------------------------------------------------- materials
alu = principled('alu', (0.135, 0.14, 0.148), rough=0.34, metal=1.0)
alu_tp = principled('trackpad', (0.125, 0.13, 0.136), rough=0.42, metal=0.55)
keys = principled('keys', (0.010, 0.010, 0.011), rough=0.52, spec=0.4)
well = principled('well', (0.004, 0.004, 0.004), rough=0.7)
bezel = principled('bezel', (0.002, 0.002, 0.002), rough=0.03, spec=0.5)
hinge = principled('hinge', (0.02, 0.02, 0.022), rough=0.45, metal=0.7)
wall = principled('wall', (0.20, 0.19, 0.18), rough=0.9)
frame = principled('frame', (0.03, 0.03, 0.032), rough=0.4, metal=0.6)
mug = principled('mug', (0.045, 0.045, 0.05), rough=0.32, coat=0.6, coat_rough=0.12)
coffee = principled('coffee', (0.02, 0.009, 0.004), rough=0.06, spec=0.6)
ph_glass = principled('phone_glass', (0.001, 0.001, 0.0012), rough=0.02, spec=0.6, coat=1.0, coat_rough=0.02)
ph_frame = principled('phone_frame', (0.42, 0.42, 0.44), rough=0.22, metal=1.0)

# wood
wood = bpy.data.materials.new('wood'); wood.use_nodes = True
nt = wood.node_tree; b = nt.nodes['Principled BSDF']
tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.7, 1.7, 1.7)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
def wtex(fn, cs):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(os.path.join(TEX, fn), cs); t.projection = 'BOX'; t.projection_blend = 0.2
    nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); return t
c = wtex('Wood049_2K-JPG_Color.jpg', 'sRGB'); r = wtex('Wood049_2K-JPG_Roughness.jpg', 'Non-Color'); n = wtex('Wood049_2K-JPG_NormalGL.jpg', 'Non-Color')
hsv = nt.nodes.new('ShaderNodeHueSaturation'); hsv.inputs['Value'].default_value = 0.62; hsv.inputs['Saturation'].default_value = 1.05
nt.links.new(c.outputs['Color'], hsv.inputs['Color']); nt.links.new(hsv.outputs['Color'], b.inputs['Base Color'])
rm = nt.nodes.new('ShaderNodeMapRange'); rm.inputs['To Min'].default_value = 0.28; rm.inputs['To Max'].default_value = 0.62
nt.links.new(r.outputs['Color'], rm.inputs['Value']); nt.links.new(rm.outputs['Result'], b.inputs['Roughness'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.3
nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
b.inputs['Coat Weight'].default_value = 0.18; b.inputs['Coat Roughness'].default_value = 0.22

# frosted window glass: city behind, blurred by the glass, plus a frosted reflective skin
glass = bpy.data.materials.new('frosted'); glass.use_nodes = True
gt = glass.node_tree; gb = gt.nodes['Principled BSDF']
ci = gt.nodes.new('ShaderNodeTexImage'); ci.image = img(os.path.join(TEX, 'city.jpg')); ci.extension = 'EXTEND'
noise = gt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 900; noise.inputs['Detail'].default_value = 4
bump = gt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.06
gt.links.new(noise.outputs['Fac'], bump.inputs['Height']); gt.links.new(bump.outputs['Normal'], gb.inputs['Normal'])
gb.inputs['Base Color'].default_value = (0.02, 0.022, 0.026, 1); gb.inputs['Roughness'].default_value = 0.32
gt.links.new(ci.outputs['Color'], gb.inputs['Emission Color']); gb.inputs['Emission Strength'].default_value = 1.05

# screen
scr = bpy.data.materials.new('screen'); scr.use_nodes = True
st = scr.node_tree; sb = st.nodes['Principled BSDF']
SCR_IMG = st.nodes.new('ShaderNodeTexImage'); SCR_IMG.image = img(os.path.join(TEX, 'dash.jpg')); SCR_IMG.extension = 'EXTEND'
st.links.new(SCR_IMG.outputs['Color'], sb.inputs['Emission Color'])
sb.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1); sb.inputs['Roughness'].default_value = 0.035
SCR_EMIT = sb.inputs['Emission Strength']; SCR_EMIT.default_value = 0.0

# grille dots
from math import floor
gimg = bpy.data.images.new('grille', 256, 256)
pix = []
for y in range(256):
    for x in range(256):
        dx = (x % 16) - 7.5; dy = (y % 16) - 7.5; v = 0.0 if dx*dx+dy*dy < 9 else 1.0
        pix += [v, v, v, 1]
gimg.pixels = pix; gimg.colorspace_settings.name = 'Non-Color'
gr = principled('grille', (0.135, 0.14, 0.148), rough=0.38, metal=1.0)
grt = gr.node_tree; grb = grt.nodes['Principled BSDF']
gtx = grt.nodes.new('ShaderNodeTexImage'); gtx.image = gimg; gtc = grt.nodes.new('ShaderNodeTexCoord')
gmp = grt.nodes.new('ShaderNodeMapping'); gmp.inputs['Scale'].default_value = (62, 62, 1)
grt.links.new(gtc.outputs['Object'], gmp.inputs['Vector']); grt.links.new(gmp.outputs['Vector'], gtx.inputs['Vector'])
mix = grt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
mix.inputs['A'].default_value = (0.002, 0.002, 0.002, 1); mix.inputs['B'].default_value = (0.135, 0.14, 0.148, 1)
grt.links.new(gtx.outputs['Color'], mix.inputs['Factor']); grt.links.new(mix.outputs['Result'], grb.inputs['Base Color'])

# ---------------------------------------------------------------- table, wall, window
TABLE_TOP = 0.0
box('table', (1.9, 1.0, 0.035), (0, -0.08, -0.0175), wood, bevel=0.003)
WY = 0.47  # wall plane (desk pushed against the window wall)
wx0, wx1, wz0, wz1 = -0.95, 0.95, 0.035, 1.55
box('wall_l', (1.6, 0.12, 3.0), (wx0 - 0.8, WY + 0.06, 0.7), wall)
box('wall_r', (1.6, 0.12, 3.0), (wx1 + 0.8, WY + 0.06, 0.7), wall)
box('wall_b', (wx1 - wx0, 0.12, 1.0), (0, WY + 0.06, wz0 - 0.5), wall)
box('wall_t', (wx1 - wx0, 0.12, 1.0), (0, WY + 0.06, wz1 + 0.5), wall)

GY = WY + 0.09
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, GY, (wz0 + wz1) / 2), rotation=(math.radians(90), 0, 0))
g = bpy.context.object; g.name = 'glass'; g.scale = (wx1 - wx0, wz1 - wz0, 1); g.data.materials.append(glass)
fw = 0.045
for nm_, sz, lc in [('fr_b', (wx1-wx0, 0.05, fw), (0, GY-0.02, wz0+fw/2)), ('fr_t', (wx1-wx0, 0.05, fw), (0, GY-0.02, wz1-fw/2)),
                    ('fr_l', (fw, 0.05, wz1-wz0), (wx0+fw/2, GY-0.02, (wz0+wz1)/2)), ('fr_r', (fw, 0.05, wz1-wz0), (wx1-fw/2, GY-0.02, (wz0+wz1)/2)),
                    ('fr_m', (0.05, 0.06, wz1-wz0), (-0.42, GY-0.025, (wz0+wz1)/2))]:
    box(nm_, sz, lc, frame, bevel=0.004)

# ---------------------------------------------------------------- laptop (14", space grey, no logos)
LW, LD, BH = 0.3126, 0.2212, 0.0108
base = rrect_prism('base', LW, LD, BH, 0.011, alu, bevel=0.0012)
tp = rrect_prism('trackpad', 0.150, 0.096, 0.0002, 0.006, alu_tp, bevel=0, z0=BH - 0.00005)
tp.location = (0, -LD/2 + 0.0105 + 0.048, 0)
kw = rrect_prism('kb_well', 0.282, 0.112, 0.0002, 0.004, well, bevel=0, z0=BH - 0.0001)
kw.location = (0, LD/2 - 0.0135 - 0.056, 0)
for sx in (-1, 1):
    gobj = rrect_prism('grille', 0.0135, 0.104, 0.00012, 0.001, gr, bevel=0, z0=BH - 0.00004)
    gobj.location = (sx * 0.150, LD/2 - 0.014 - 0.052, 0)
# keys
U = 0.0191; KG = 0.0026
rows = [  # (height in units, [widths])
    (0.55, [1.5] + [1.0]*12 + [1.0]),
    (1.0, [1.0]*13 + [1.5]),
    (1.0, [1.5] + [1.0]*13),
    (1.0, [1.8] + [1.0]*11 + [1.7]),
    (1.0, [2.35] + [1.0]*10 + [2.15]),
    (1.0, [1.0, 1.0, 1.0, 1.25, 5.0, 1.25, 1.0, 1.0, 1.5]),
]
ytop = LD/2 - 0.0155
yy = ytop
kb_parts = []
for hu, ws in rows:
    tot = sum(ws) * U; x = -tot / 2; h = hu * U
    for wu in ws:
        if len(ws) == 9 and wu == 1.5:  # arrow cluster
            aw = 0.5 * U
            for i, (ox, oy, hh) in enumerate([(0, 0, h/2), (aw, 0, h/2), (aw, h/2, h/2), (2*aw, 0, h/2)]):
                k = rrect_prism('key', aw*1.0 - KG*0.8, hh - KG*0.8, 0.0007, 0.0012, keys, bevel=0.0003, seg=4, z0=BH)
                k.location = (x + ox + aw/2, yy - h + oy + hh/2, 0); kb_parts.append(k)
        else:
            k = rrect_prism('key', wu*U - KG, h - KG, 0.0007, 0.0015, keys, bevel=0.0003, seg=4, z0=BH)
            k.location = (x + wu*U/2, yy - h/2, 0); kb_parts.append(k)
        x += wu * U
    yy -= h
# join keys into one mesh for speed
bpy.ops.object.select_all(action='DESELECT')
for k in kb_parts: k.select_set(True)
bpy.context.view_layer.objects.active = kb_parts[0]
for k in kb_parts:
    for m in list(k.modifiers):
        bpy.context.view_layer.objects.active = k; bpy.ops.object.modifier_apply(modifier=m.name)
bpy.context.view_layer.objects.active = kb_parts[0]
for k in kb_parts: k.select_set(True)
bpy.ops.object.join(); kb = bpy.context.object; kb.name = 'keyboard'

# lid: built flat (local y up the lid, local z = screen side), then rotated about the hinge
LH, LT = 0.2155, 0.0046
OPEN = math.radians(68)  # lid leans back 22 deg from vertical
lid = bpy.data.objects.new('lid', None); bpy.context.collection.objects.link(lid)
lid.location = (0, LD/2 - 0.004, BH + 0.0016); lid.rotation_euler = (OPEN, 0, 0)
shell = rrect_prism('lid_shell', LW, LH, LT, 0.011, alu, bevel=0.0012); shell.location = (0, LH/2, 0); shell.parent = lid
bz = rrect_prism('bezel', LW - 0.0016, LH - 0.0016, 0.0002, 0.0102, bezel, bevel=0, z0=LT); bz.location = (0, LH/2, 0); bz.parent = lid
SW, SH = 0.3016, 0.1958
SCY = LH - 0.0042 - SH/2  # active area centre (top bezel ~4mm)
bpy.ops.mesh.primitive_plane_add(size=1)
screen = bpy.context.object; screen.name = 'screen'; screen.scale = (SW, SH, 1)
bpy.ops.object.transform_apply(scale=True)
screen.data.materials.append(scr); screen.parent = lid; screen.location = (0, SCY, LT + 0.00025)
# rounded top corners of the display are hidden in the bezel; hinge
bpy.ops.mesh.primitive_cylinder_add(radius=0.0042, depth=LW - 0.05, rotation=(0, math.radians(90), 0), location=(0, LD/2 - 0.003, BH + 0.0005))
bpy.context.object.data.materials.append(hinge)

# world-space screen frame (for cameras / text)
bpy.context.view_layer.update()
M = screen.matrix_world
S_CEN = M @ Vector((0, 0, 0)); S_N = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
S_UP = (M.to_3x3() @ Vector((0, 1, 0))).normalized(); S_RIGHT = (M.to_3x3() @ Vector((1, 0, 0))).normalized()
def screen_pt(px, py):  # screen pixels (1512 x 982, origin top-left) -> world
    return S_CEN + S_RIGHT * ((px / 1512 - 0.5) * SW) + S_UP * ((0.5 - py / 982) * SH)

# ---------------------------------------------------------------- phone & mug
phone = bpy.data.objects.new('phone', None); bpy.context.collection.objects.link(phone)
phone.location = (0.248, -0.035, 0); phone.rotation_euler = (0, 0, math.radians(-9))
p1 = rrect_prism('phone_body', 0.0715, 0.1476, 0.0074, 0.0105, ph_frame, bevel=0.0015); p1.parent = phone
p2 = rrect_prism('phone_glass', 0.0703, 0.1464, 0.0004, 0.0099, ph_glass, bevel=0.0002, z0=0.0072); p2.parent = phone
bpy.ops.mesh.primitive_cylinder_add(radius=0.041, depth=0.094, vertices=96, location=(-0.275, 0.17, 0.047))
mg = bpy.context.object; mg.name = 'mug'; mg.data.materials.append(mug)
bpy.ops.object.mode_set(mode='EDIT'); bm = bmesh.from_edit_mesh(mg.data)
top = [f for f in bm.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
bmesh.update_edit_mesh(mg.data); bpy.ops.object.mode_set(mode='OBJECT')
s = mg.modifiers.new('sol', 'SOLIDIFY'); s.thickness = 0.0045; s.offset = -1
bv = mg.modifiers.new('bev', 'BEVEL'); bv.width = 0.0016; bv.segments = 3; bv.limit_method = 'ANGLE'
mg.modifiers.new('sub', 'SUBSURF').levels = 1
for p in mg.data.polygons: p.use_smooth = True
bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.0062, location=(-0.275 - 0.041, 0.17, 0.05), rotation=(math.radians(90), 0, 0))
hd = bpy.context.object; hd.scale = (0.85, 1.15, 1); hd.data.materials.append(mug)
for p in hd.data.polygons: p.use_smooth = True
bpy.ops.mesh.primitive_cylinder_add(radius=0.0362, depth=0.001, vertices=96, location=(-0.275, 0.17, 0.079))
bpy.context.object.data.materials.append(coffee)

# ---------------------------------------------------------------- lights
bpy.ops.object.light_add(type='AREA', location=(-1.05, -0.55, 0.95))
lamp = bpy.context.object; lamp.data.energy = 26; lamp.data.size = 0.5; lamp.data.color = (1.0, 0.66, 0.38)
lamp.rotation_euler = (Vector((0.0, 0.05, 0.0)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.light_add(type='AREA', location=(0.0, -2.2, 1.6))
fill = bpy.context.object; fill.data.energy = 6; fill.data.size = 2.0; fill.data.color = (0.55, 0.65, 1.0)
fill.rotation_euler = (Vector((0, 0.1, 0.1)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------- camera
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 50; cam_d.sensor_width = 36; cam_d.sensor_fit = 'HORIZONTAL'
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('tgt', None); bpy.context.collection.objects.link(tgt)
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.2
FILL_D = (SW / 2) / math.tan(math.atan(18 / 50))  # distance where screen width fills the frame
CAM_FILL = S_CEN + S_N * (FILL_D / 1.16)  # matches the 2D recording's first/last framing (zoom 1.16)

# ---------------------------------------------------------------- floating text (segment B)
def text_obj(name, body, font, size, color, strength):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.font = bpy.data.fonts.load(os.path.join(FONTS, font))
    cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    m = bpy.data.materials.new(name + '_m'); m.use_nodes = True; t = m.node_tree
    for n_ in list(t.nodes): t.nodes.remove(n_)
    out = t.nodes.new('ShaderNodeOutputMaterial'); em = t.nodes.new('ShaderNodeEmission'); tr = t.nodes.new('ShaderNodeBsdfTransparent')
    mx = t.nodes.new('ShaderNodeMixShader'); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(em.outputs[0], mx.inputs[2]); t.links.new(mx.outputs[0], out.inputs[0])
    mx.inputs['Fac'].default_value = 0.0
    ob.data.materials.append(m)
    return ob, mx.inputs['Fac']

TXT = {}
if args.seg == 'B':
    TXT['ans'] = text_obj('answer', 'Stop guessing. Ask an expert.', 'Inter-Medium.otf', 0.0215, (0.93, 0.93, 0.93), 2.2)
    TXT['name'] = text_obj('name', 'Ghaith Abdullah', 'Inter-SemiBold.otf', 0.030, (0.94, 0.92, 0.88), 2.0)
    TXT['role'] = text_obj('role', 'DIGITAL MARKETING EXPERT', 'Inter-Medium.otf', 0.0092, (0.80, 0.62, 0.30), 2.2)
    TXT['url'] = text_obj('url', 'web.ghayth-abdallah.com', 'Inter-Regular.otf', 0.0082, (0.62, 0.62, 0.64), 1.6)
    TXT['role'][0].data.space_character = 1.25

# ---------------------------------------------------------------- shot design
WIDE_A0 = (Vector((0.26, -0.75, 0.385)), Vector((0.055, 0.14, 0.12)))
WIDE_A1 = (Vector((0.15, -0.69, 0.37)), Vector((0.03, 0.15, 0.125)))
POV_A = (Vector((0.035, -0.53, 0.33)), screen_pt(756, 520))
POV_A2 = (Vector((0.03, -0.49, 0.315)), screen_pt(756, 500))
END_B = (Vector((0.11, -0.86, 0.405)), Vector((0.005, 0.16, 0.145)))
END_B2 = (Vector((0.095, -0.80, 0.39)), Vector((0.005, 0.16, 0.15)))

def shot(f):
    """returns cam_pos, target, focus_point, screen_emit, screen_tex"""
    t = f / FPS
    if args.seg == 'A':
        wake = 0.0 if t < 3.5 else min(1.0, ease_out((t - 3.5) / 0.35) * 1.0)
        if t < 3.5:
            x = ease_io(t / 3.5) * 0.85 + (t / 3.5) * 0.15
            p, g_ = lerpv(WIDE_A0[0], WIDE_A1[0], x), lerpv(WIDE_A0[1], WIDE_A1[1], x)
        elif t < 4.45:
            x = ease_io((t - 3.5) / 0.95)
            p, g_ = lerpv(WIDE_A1[0], POV_A[0], x), lerpv(WIDE_A1[1], POV_A[1], x)
        elif t < 5.8:
            x = (t - 4.45) / 1.35
            p, g_ = lerpv(POV_A[0], POV_A2[0], x), lerpv(POV_A[1], POV_A2[1], x)
        else:
            x = ease_in((t - 5.8) / (197 / FPS - 5.8))
            p, g_ = lerpv(POV_A2[0], CAM_FILL, x), lerpv(POV_A2[1], S_CEN, x)
        return p, g_, S_CEN, wake * 1.55, 'dash.jpg'
    else:
        tex = 'think_%03d.jpg' % (f % 60)
        if t < 2.3:
            x = ease_out(t / 2.3) ** 0.9
            p, g_ = lerpv(CAM_FILL, END_B[0], x), lerpv(S_CEN, END_B[1], x)
        else:
            x = (t - 2.3) / (345 / FPS - 2.3)
            p, g_ = lerpv(END_B[0], END_B2[0], x), lerpv(END_B[1], END_B2[1], x)
        return p, g_, S_CEN, 1.55, tex

def text_state(f, cam_p, cam_g):
    """position floating text in front of the camera; returns focus point"""
    t = f / FPS
    fwd = (cam_g - cam_p).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd).normalized()
    def at(dist, dx, dz): return cam_p + fwd * dist + right * dx + up * dz
    rot = fwd.to_track_quat('-Z', 'Y').to_euler()
    ans, afac = TXT['ans']; nm_, nfac = TXT['name']; rl, rfac = TXT['role']; ur, ufac = TXT['url']
    # think label on screen -> lift off
    tr = json.load(open(os.path.join(TEX, 'think_rect.json')))['think_rect_px']
    s0 = screen_pt(tr[0] + 230, tr[1] + tr[3] / 2)  # answer would print where 'Thinking' sits
    k = ease_io((t - 2.15) / 2.0)
    pos = s0.lerp(at(0.52, 0, 0.05), k)
    scale = 0.16 + 0.84 * ease_io((t - 2.15) / 1.6)
    # exit up and away
    e = ease_io((t - 6.35) / 0.9)
    pos = pos + up * 0.09 * e - fwd * 0.0 * e
    ans.location = pos; ans.rotation_euler = rot; ans.scale = (scale,) * 3
    afac.default_value = clamp((t - 2.05) / 0.25) * (1 - clamp((t - 6.45) / 0.6))
    # name card rises into focus
    k2 = ease_out((t - 6.75) / 1.1)
    for ob_, dz, fac_, delay in ((nm_, 0.016, nfac, 0.0), (rl, -0.012, rfac, 0.18), (ur, -0.037, ufac, 0.4)):
        kk = ease_out((t - 6.75 - delay) / 1.0)
        ob_.location = at(0.52, 0, 0.056 + dz - 0.03 * (1 - kk)); ob_.rotation_euler = rot
        fac_.default_value = clamp((t - 6.75 - delay) / 0.45)
    if t < 2.15: return None
    if t < 6.6: return ans.location
    return nm_.location

# ---------------------------------------------------------------- keyframes (camera) for motion blur
nB = 345; nA = 198
N = nA if args.seg == 'A' else nB
for f in range(0, N + 1):
    p, g_, *_ = shot(f)
    cam.location = p; tgt.location = g_
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f)
for ob_ in (cam, tgt):
    for fc in ob_.animation_data.action.fcurves if hasattr(ob_.animation_data.action, 'fcurves') else []:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------- render loop
frames = list(range(args.range[0], args.range[1] + 1)) if args.range else [int(x) for x in args.frames.split(',') if x]
os.makedirs(args.out, exist_ok=True)
import time
for f in frames:
    sc.frame_set(f)
    p, g_, focus, emit, texn = shot(f)
    SCR_EMIT.default_value = emit
    SCR_IMG.image = img(os.path.join(TEX, texn))
    fp = focus
    if args.seg == 'B':
        tf = text_state(f, p, g_)
        if tf is not None: fp = tf
    cam_d.dof.focus_distance = max(0.05, (fp - p).dot((g_ - p).normalized()))
    sc.render.filepath = os.path.join(args.out, '%s_%04d.png' % (args.seg, f))
    t0 = time.time(); bpy.ops.render.render(write_still=True)
    print('FRAME', args.seg, f, round(time.time() - t0, 1), flush=True)
