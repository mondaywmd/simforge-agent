"""Refine the furnished room using the 15 supplied HEIC photographs.
Runs on the furnished blend, saves a separate photo-reference revision.
"""
import bpy,bmesh,math,random,json,hashlib,ast
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];TEX=ROOT/'assets/reconstruction'
s=bpy.context.scene
detail=bpy.data.collections['10_INTERIOR - doors trim and fixtures']
furniture=bpy.data.collections['11_FURNITURE - authored from scan and photo']
decor=bpy.data.collections['12_PERSONAL_ITEMS - art books and household items']
lighting=bpy.data.collections['13_LIGHTING - visible fixtures and light sources']
active_col=furniture
# Reuse geometry constructors without rebuilding the existing scene.
tree=ast.parse((ROOT/'scripts/furnish_reconstruction.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'<constructors>','exec'))
white=bpy.data.materials['Warm ivory paint'];wall=bpy.data.materials['Warm white plaster']
cream=bpy.data.materials['Cream linen'];black=bpy.data.materials['Dark rubber and fabric']
metal=bpy.data.materials['Brushed steel'];gray=bpy.data.materials['Sofa gray woven cloth']
pink=bpy.data.materials['Dusty rose cushions'];blue=bpy.data.materials['Blue gray textile']
oak=bpy.data.materials['Light oak cabinetry'];tablewood=bpy.data.materials['Honey oak tables']
green=bpy.data.materials['Deep green bags'];paper=bpy.data.materials['Paper off white']
glow=bpy.data.materials['Warm LED diffuser'];red=bpy.data.materials['Burgundy fabric']
source_hash=fingerprint(bpy.data.objects['mesh'].data)
def remove_prefix(prefixes):
    for o in list(s.objects):
        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
def fulluv(o,mirror=False):
    coords=[(0,0),(1,0),(1,1),(0,1)]
    for v,co in zip(o.data.uv_layers.active.data,coords):v.uv=((1-co[0]) if mirror else co[0],co[1])
count=0
for side in ['west','east']:
    for i in range(12):
        p=TEX/'photo_details'/f'{side}_{i:02d}.png'
        o=bpy.data.objects.get(f'{side.title()} wall original artwork {i:02d}')
        if not p.exists() or o is None:continue
        m=texturemat(f'Photo reference {side} artwork {i:02d}',p,.83)
        o.data.materials.clear();o.data.materials.append(m);fulluv(o,side=='east')
        o['photo_reference']='IMG_5732' if side=='west' else 'IMG_5731/5730';count+=1
remove_prefix(['East wall original artwork 07','West wall original artwork 10'])
# Lower blue whiteboard note is much smaller than the previous scan crop.
bluecard=bpy.data.objects.get('West wall original artwork 11')
if bluecard:
    coords=[(-.809,.22,.57),(-.809,.33,.57),(-.809,.33,.72),(-.809,.22,.72)]
    for v,co in zip(bluecard.data.vertices,coords):v.co=co
    bluecard.location=(0,0,0)
box('Wall whiteboard lower panel',(-.813,.42,.54),(.006,.92,.76),white,.001,detail)
if bluecard:bluecard.location.x+=.008
for y,m in [(.245,blue),(.29,pink)]:rod('Whiteboard round magnet',(-.799,y,.76),(-.793,y,.76),.013,m,decor)
box('Wall marker holder',(-.79,.68,.24),(.04,.12,.13),white,.015,decor)
for i,m in enumerate([black,red,blue]):rod('Whiteboard marker',(-.764,.644+i*.028,.28),(-.764,.644+i*.028,.42),.006,m,decor)
# Animal prints are now the user's actual bear and deer pictures.
animalobs=sorted([o for o in decor.objects if o.name.startswith('Dining animal print') and 'frame' not in o.name],key=lambda o:o.name)
for o,animal in zip(animalobs,['bear','deer']):
    o.data.materials.clear();o.data.materials.append(texturemat('Photo '+animal,TEX/'photo_details'/('animal_'+animal+'.png')));fulluv(o,True)
# Photo confirms four compact ceiling cylinders, one dark and three illuminated.
remove_prefix(['Hall ceiling cylinder fixture','Hall LED lens','Hall warm LED'])
for i,y in enumerate([-.45,-.78,-1.11,-1.44]):
    rod('Photo matched hall cylinder',(-.28,y,2.48),(-.28,y,2.674),.039,white,lighting)
    for z in [2.60,2.64]:
        pts=[(-.28+.040*math.cos(t),y+.040*math.sin(t),z) for t in np.linspace(0,math.tau,48,endpoint=False)]
        path('Luminaire casing seam',pts,.0008,gray,True,lighting)
    rod('Photo matched hall lens',(-.28,y,2.477),(-.28,y,2.485),.033,black if i==0 else glow,lighting)
    if i:light('Hall lamp warm light',(-.28,y,2.45),(-.28,y,.08),28,(1,.82,.62),.09)
# White door's circular wall ventilator and visible support arms.
rod('Ventilation dark recessed ring',(.254,.75,2.43),(.22,.75,2.43),.128,black,detail)
rod('Ventilation white floating cover',(.185,.75,2.43),(.17,.75,2.43),.114,white,detail)
for z in [2.37,2.49]:rod('Vent cover stand off',(.22,.66,z),(.18,.84,z),.005,gray,detail)
# Add the hanging gymnastics straps and rings from the new photographs.
for y in [1.105,1.14]:
    path('Gym suspension strap',[(.09,y,1.99),(.11,y,1.56),(.10,y,1.45)],.008,gray,False,decor)
    pts=[(.10+.055*math.cos(t),y,1.48+.065*math.sin(t)) for t in np.linspace(0,math.tau,48,endpoint=False)]
    path('Gym toy ring',pts,.009,blue,True,decor)
# More faithful soft floor chair, with piping and crease between seat and back.
remove_prefix(['Floor chair seat','Floor chair back','Pink slippers'])
cushion('Photo matched floor chair seat',(-.42,4.04,.145),(.64,.68,.105),cream,power=8)
cushion('Photo matched floor chair back',(-.42,4.35,.485),(.64,.085,.65),cream,(-.095,0,0),power=8)
for z in [.34,.36]:path('Floor chair horizontal crease',[(-.70,4.289,z),(-.42,4.288,z-.008),(-.14,4.289,z)],.0018,cream)
for o in [bpy.data.objects.get('Tablet on floor chair'),bpy.data.objects.get('Tablet glass')]:
    if o:o.location.z-=.044
for x in [-.92,-.76]:
    rod('Pink dumbbell grip',(x,3.99,.16),(x,4.15,.16),.022,pink)
    for y in [3.96,4.18]:rod('Pink dumbbell hex weight',(x,y-.025,.16),(x,y+.025,.16),.069,pink,vertices=6)
cushion('Gray kettlebell body',(-.97,4.29,.21),(.22,.19,.22),gray,power=2)
pts=[(-.97+.095*math.cos(t),4.29,.28+.10*math.sin(t)) for t in np.linspace(0,math.pi,32)]
path('Kettlebell handle',pts,.018,gray)
# Replace capsule-like bags with structured totes and real photo-patterned panels.
remove_prefix(['Hanging shoulder bag','Bag strap','Hanging hat'])
bagmat=texturemat('Actual green tote pattern',TEX/'photo_details/bag_green.png',.90)
for i,(x,z,m) in enumerate([(.05,.66,black),(.29,.84,cream),(.17,1.01,green),(.04,1.20,red)]):
    o=box('Structured hanging tote',(x,4.10,z),(.35,.095,.31),m,.035)
    for xx in [-.09,.09]:
        path('Tote shoulder loop',[(x+xx,4.05,z+.14),(x+xx*.95,4.045,z+.37),(x-xx*.95,4.045,z+.37),(x-xx,4.05,z+.14)],.0055,m)
    if i==2:patch('Green tote photographed front',(x-.17,4.047,z-.145),(.34,0,0),(0,0,.29),bagmat)
# Bucket hat brims and cloth crowns modeled separately.
def hat(name,x,y,z,m):
    rings=[(.13,.0),(.17,.018),(.12,.044),(.105,.16),(.03,.18)]
    verts=[];faces=[];N=48
    for r,h in rings:
        for j in range(N):
            t=math.tau*j/N;verts.append((x+r*math.cos(t),y-r*.28*math.sin(t)-h*.35,z+r*math.sin(t)+h))
    for k in range(len(rings)-1):
        for j in range(N):faces.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);furniture.objects.link(o);me.materials.append(m)
    sol=o.modifiers.new('Hat fabric thickness','SOLIDIFY');sol.thickness=.002
    for p in me.polygons:p.use_smooth=True
hat('Dark bucket hat',.16,4.095,1.80,black);hat('Cream bucket hat',.04,4.075,1.52,cream);hat('Gray cap',.32,4.09,1.63,gray)
# Photo-matched shoe details: contrasting sole, opening and laces.
for i,o in enumerate([o for o in furniture.objects if o.name.startswith('Shoes by cabinet')]):
    x,y,z=o.location
    box('Shoe contrast sole',(x,y,.097),(.115,.245,.017),white,.007)
    cushion('Shoe dark collar',(x,y+.06,.182),(.066,.09,.013),black,power=3)
    if i%3:
        for j in range(3):rod('Shoe lace',(x-.033,y-.015+j*.025,.181),(x+.033,y-.025+j*.025,.181),.0018,white,decor,8)
# Dining chair upholstery and bent plywood backs replace generic rounded pads.
remove_prefix(['Chair curved back pad'])
for cx,cy,angle in [(1.20,1.80,0),(1.87,3.06,math.pi)]:
    cushion('Dining chair gray seat pad',(cx,cy,.543),(.40,.38,.060),gray,rot=(0,0,angle),power=7)
    verts=[];faces=[]
    for j in range(2):
        for i in range(25):
            x=-.205+i*.410/24;y=-.20+.35-math.sqrt(.35**2-x*x)
            verts.append((cx+math.cos(angle)*x-math.sin(angle)*y,cy+math.sin(angle)*x+math.cos(angle)*y,.79+j*.24))
    for i in range(24):faces.append((i,i+1,26+i,25+i))
    me=bpy.data.meshes.new('Bent plywood chair back');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Bent plywood chair back',me);furniture.objects.link(o);me.materials.append(oak)
    sol=o.modifiers.new('Plywood thickness','SOLIDIFY');sol.thickness=.014
    b=o.modifiers.new('Rounded plywood edge','BEVEL');b.width=.009;b.segments=3
# Bathroom revealed by IMG_5728 and IMG_5730.
bath=collection('14_BATHROOM - photograph referenced');active_col=bath
tile=mat('Bathroom warm gray ceramic',(.34,.32,.27),.63);noise_bump(tile,75,.17,.0015)
ceramic=mat('Glazed ivory sanitary ware',(.83,.81,.73),.20)
grout=mat('Bathroom grout',(.18,.17,.14),.95)
box('Bathroom tiled floor',(1.135,-1.64,.085),(1.70,1.54,.014),tile,.002)
for x in [.30,.90,1.50]:box('Bathroom floor grout',(x,-1.64,.095),(.002,1.52,.001),grout,0)
for y in [-2.40,-1.80,-1.20]:box('Bathroom floor grout',(1.13,y,.095),(1.67,.002,.001),grout,0)
box('Bathroom tiled rear wall',(1.984,-1.64,1.25),(.012,1.54,2.32),tile,0)
for z in np.arange(.10,2.42,.30):box('Bathroom horizontal tile grout',(1.975,-1.64,z),(.002,1.54,.002),grout,0)
for y in [-2.40,-1.80,-1.20]:box('Bathroom vertical tile grout',(1.974,y,1.25),(.002,.002,2.32),grout,0)
# Fold door leaves inward along the jamb, leaving the basin visible.
for o in list(detail.objects):
    if o.name.startswith(('Utility folding door frame','Utility inset glass')):
        d=o.location-Vector((.65,-1.20,1.16));o.location=Vector((.70,-.94,1.16))+Vector((-d.y,d.x,d.z));o.rotation_euler.z+=math.pi/2
box('Bathroom vanity cabinet',(1.69,-2.05,.46),(.49,.62,.60),white,.015)
for z in [.31,.59]:
    box('Vanity drawer',(1.431,-2.05,z),(.021,.60,.265),white,.006)
    rod('Vanity drawer pull',(1.41,-2.15,z+.11),(1.41,-1.95,z+.11),.009,metal)
def bowl(name,center,rx,ry,profiles,m):
    N=64;verts=[];faces=[]
    for r,z in profiles:
        for j in range(N):
            t=math.tau*j/N;verts.append((center[0]+rx*r*math.cos(t),center[1]+ry*r*math.sin(t),z))
    for k in range(len(profiles)-1):
        for j in range(N):faces.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    faces.append(tuple(range(N-1,-1,-1)));faces.append(tuple((len(profiles)-1)*N+j for j in range(N)))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);active_col.objects.link(o);me.materials.append(m)
    for p in me.polygons:p.use_smooth=True
    return o
bowl('Vanity oval wash basin',(1.67,-2.05),.27,.33,[(.30,.69),(.85,.76),(1,.82),(.97,.855),(.83,.85),(.67,.77),(.12,.73)],ceramic)
rod('Basin drain',(1.67,-2.05,.732),(1.67,-2.05,.736),.021,metal)
rod('Mixer tap stem',(1.87,-2.05,.82),(1.87,-2.05,1.01),.015,metal)
rod('Mixer tap spout',(1.87,-2.05,1.01),(1.74,-2.05,1.01),.012,metal)
mirror=mat('Bathroom mirror silver',(.86,.88,.90),.02,1)
box('Bathroom mirror cabinet',(1.91,-2.03,1.40),(.13,.67,.73),metal,.008)
box('Bathroom mirrored face',(1.838,-2.03,1.40),(.008,.64,.70),mirror,.002)
for i,m in enumerate([pink,blue,green,cream,white]):
    y=-2.28+i*.095;rod('Toiletry bottle',(1.90,y,.85),(1.90,y,1.00+.015*(i%2)),.022,m)
    rod('Bottle cap',(1.90,y,1.00+.015*(i%2)),(1.90,y,1.02+.015*(i%2)),.010,white)
box('Bathroom step stool',(1.24,-2.00,.21),(.27,.33,.26),white,.03)
for i in range(5):
    for j in range(6):rod('Stool anti slip dot',(1.14+i*.045,-2.135+j*.045,.341),(1.14+i*.045,-2.135+j*.045,.344),.006,gray,vertices=12)
bowl('Toilet ceramic bowl',(1.48,-1.28),.30,.21,[(.43,.09),(.47,.25),(.84,.40),(1,.45),(1,.49),(.83,.495),(.68,.39),(.15,.31)],ceramic)
box('Toilet cistern',(1.78,-1.28,.67),(.19,.39,.39),ceramic,.05)
cushion('Toilet raised lid',(1.755,-1.28,.74),(.034,.35,.43),ceramic,rot=(0,-.12,0),power=5)
rod('Toilet flush button',(1.78,-1.28,.87),(1.78,-1.28,.88),.026,metal)
# Shower curtain with regular check pattern represented by thin yarn lines.
curtainmat=mat('Shower curtain gray',(.18,.21,.21),.93);noise_bump(curtainmat)
verts=[];faces=[];NU=40;NV=12
for j in range(NV+1):
    for i in range(NU+1):
        x=.96+i*.98/NU;verts.append((x,-.965+.028*math.sin(i*math.tau/5),.16+j*2.0/NV))
for j in range(NV):
    for i in range(NU):a=j*(NU+1)+i;faces.append((a,a+1,a+NU+2,a+NU+1))
me=bpy.data.meshes.new('Shower curtain folds');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Shower curtain',me);bath.objects.link(ob);me.materials.append(curtainmat)
for i in range(NU+1):
    if i%3==0:
        x=.96+i*.98/NU;y=-.965+.028*math.sin(i*math.tau/5)
        path('Curtain vertical check',[(x,y-.001,.16),(x,y-.001,2.16)],.001,cream)
for z in np.arange(.2,2.16,.09):path('Curtain horizontal check',[(.96+i*.98/NU,-.966+.028*math.sin(i*math.tau/5),z) for i in range(NU+1)],.001,cream)
rod('Shower curtain rail',(.96,-.96,2.19),(1.95,-.96,2.19),.012,metal)
light('Bathroom warm ceiling',(1.15,-1.6,2.36),(1.6,-1.7,.6),35,(1,.83,.60),.65)
# Small wave-color bathmat visible in the doorway.
matcolors=[mat('Bathmat cream',(.70,.65,.49),.98),mat('Bathmat sage',(.30,.43,.39),.98),mat('Bathmat pale green',(.48,.55,.45),.98)]
for i,m in enumerate(matcolors):
    noise_bump(m,220,.40,.002)
    box('Bathmat color band',(.01,-1.28+i*.095,.092),(.44,.095,.018),m,.005)
# Bedroom glimpses in IMG_5729: real window, bunk bed, children's table and ceiling fan.
room=collection('15_BEDROOM - photograph referenced');active_col=room
remove_prefix(['Northwest room desk','Northwest desk leg','Northwest desk books'])
box('Bedroom study tabletop',(-3.90,-.25,.80),(.57,1.10,.05),white,.012)
for x in [-4.10,-3.69]:
    for y in [-.70,.20]:box('Bedroom desk leg',(x,y,.44),(.045,.045,.69),white,.004)
for z in [.43,1.70]:
    box('Bunk bed platform',(-2.39,.68,z),(1.94,.86,.065),white,.008)
    cushion('Bunk mattress',(-2.39,.68,z+.095),(1.89,.81,.14),cream,power=7)
for x in [-3.39,-1.39]:
    for y in [.20,1.16]:box('Bunk bed post',(x,y,1.04),(.065,.065,1.90),white,.007)
for z in [1.95,2.11]:rod('Bunk safety guard',(-3.39,.20,z),(-1.39,.20,z),.015,white)
for z in np.arange(.36,1.8,.27):rod('Bunk ladder rung',(-1.47,.15,z),(-1.47,-.18,z),.014,white)
for y in [.15,-.18]:rod('Bunk ladder stile',(-1.47,y,.10),(-1.47,y,1.95),.018,white)
for x in [-2.9,-2.55,-2.20]:
    pts=[(x,.68+.44*math.cos(t),1.88+.63*math.sin(t)) for t in np.linspace(0,math.pi,32)]
    path('Pink bunk play canopy arch',pts,.021,pink)
box('Child activity table',(-2.92,-.50,.57),(.72,.51,.045),white,.03)
for x in [-3.20,-2.64]:
    for y in [-.68,-.32]:rod('Child table leg',(x,y,.08),(x,y,.55),.031,white)
cushion('Child chair seat',(-2.35,-.50,.35),(.28,.28,.055),white,power=8)
box('Child chair back',(-2.17,-.5,.54),(.04,.29,.35),white,.016)
# Replace just the newly authored opaque west wall fragment with a window assembly.
old=bpy.data.objects.get('W05b West rooms outside north fragment')
if old:bpy.data.objects.remove(old,do_unlink=True)
for name,loc,size in [('Bedroom window sill wall',(-4.40,.12,.465),(.12,2.23,.77)),('Bedroom window head wall',(-4.40,.12,2.565),(.12,2.23,.23)),('Bedroom window south pier',(-4.40,-.865,1.65),(.12,.17,1.60)),('Bedroom window north pier',(-4.40,1.045,1.65),(.12,.47,1.60))]:box(name,loc,size,wall,.003)
windowglass=mat('Bedroom pale daylight glazing',(.61,.73,.79),.16)
for y in [-.78,.02,.81]:box('Bedroom window vertical frame',(-4.32,y,1.65),(.05,.04,1.60),white,.003)
for z in [.85,1.85,2.45]:box('Bedroom window horizontal frame',(-4.32,.015,z),(.05,1.63,.04),white,.003)
for y in [-.38,.42]:
    for z,h in [(1.35,.96),(2.15,.55)]:box('Bedroom window glass',(-4.355,y,z),(.008,.75,h),windowglass,.001)
for y in [-.85,.9]:
    for i in range(6):rod('Blue bedroom curtain fold',(-4.22+.022*math.sin(i),y+i*.022,.85),(-4.22+.022*math.sin(i),y+i*.022,2.50),.026,blue)
light('Bedroom window daylight',(-4.20,.0,1.75),(-1.7,-.5,1),95,(.80,.9,1),1.4)
rod('Bedroom ceiling fan stem',(-2.9,.0,2.38),(-2.9,.0,2.68),.043,white)
rod('Bedroom fan light',(-2.9,.0,2.34),(-2.9,.0,2.40),.12,glow)
for i in range(3):
    t=i*math.tau/3;o=box('Bedroom ceiling fan blade',(-2.9+.29*math.cos(t),.29*math.sin(t),2.45),(.55,.12,.015),white,.024);o.rotation_euler.z=t
# Tone the wood toward the neutral brown seen in daylight reference photos.
floorm=bpy.data.materials['Actual scanned oak floor sample'];nodes=floorm.node_tree.nodes;links=floorm.node_tree.links
p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');tex=next(n for n in nodes if n.type=='TEX_IMAGE')
hue=nodes.new('ShaderNodeHueSaturation');hue.inputs['Saturation'].default_value=.68;hue.inputs['Value'].default_value=.76
links.new(tex.outputs['Color'],hue.inputs['Color']);links.new(hue.outputs['Color'],p.inputs['Base Color'])
# Save compact, reusable reference photos inside the deliverable without personal identification processing.
for path in sorted((ROOT/'ref/photos/preview').glob('*.jpg')):
    im=bpy.data.images.load(str(path),check_existing=True);im.use_fake_user=True;im.pack()
s['Photo reference revision']='IMG_5713 and IMG_5726 through IMG_5739 reviewed. 21 rectified photo artwork assets, four hall lights, circular vent, bathroom, bedroom window and bunk bed added.'
s['Uncertainty']='Corridor details supported by photographs; sofa shape/hidden furniture surfaces still approximate from scan. Bathroom and bedroom dimensions beyond scan are estimates. Original scan remains unchanged and hidden.'
assert fingerprint(bpy.data.objects['mesh'].data)==source_hash
ref=bpy.data.collections['90_REFERENCE_SCAN - original, hidden'];assert ref.hide_render and ref.hide_viewport
s.camera=bpy.data.objects['Interior - toward lounge'];s.render.filepath=str(ROOT/'renders/home_photoref_hall.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/home_reconstructed_photoref.blend'))
report={'photo_count':15,'individual_wall_art_replaced':count,'objects':len(s.objects),'scan_geometry_uv_hash':source_hash,'reference_hidden':True,
        'photos':'ref/photos','details_source_map':'assets/reconstruction/photo_details/sources.json',
        'limitations':['Bathroom and bedroom unseen dimensions remain estimates','Sofa and other partially scanned furniture require dedicated photographs for closer shape matching']}
(ROOT/'renders/photo_reference_revision.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PHOTO REFERENCE REVISION SAVED',json.dumps(report),flush=True)
