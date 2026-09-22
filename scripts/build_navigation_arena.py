import bpy,bmesh,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
assert not bpy.data.scenes.get('NavBot - Navigation Arena'), 'Arena already exists'
s=bpy.data.scenes.new('NavBot - Navigation Arena')
env=bpy.data.collections.new('Arena - Architecture');s.collection.children.link(env)
details=bpy.data.collections.new('Arena - Markings');s.collection.children.link(details)
bots=bpy.data.collections.new('Arena - Robot');s.collection.children.link(bots)
rig=bpy.data.collections.new('Arena - Cameras and Lighting');s.collection.children.link(rig)
def mat(name,c,rough=.6,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
 n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 n.inputs[0].default_value=(*c,1);n.inputs[1].default_value=metal;n.inputs[2].default_value=rough
 return m
floor=mat('Arena | warm grey',(.48,.51,.52),.8)
edge=mat('Arena | graphite',(.055,.075,.085),.65)
wall=mat('Arena | chalk',(.72,.75,.73),.65)
grid=mat('Arena | grid',(.30,.35,.36),.85)
teal=mat('Arena | teal',(.025,.30,.32),.4)
orange=mat('Arena | amber',(.86,.33,.065),.45)
ink=mat('Arena | ink',(.065,.105,.12),.8)
back=mat('Arena | studio background',(.19,.24,.27),.9)
def make(name,bm,m,col=env):
 me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(m);return ob
def box(name,loc,size,m,bevel=.006,col=env):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:
  for i in range(3):v.co[i]*=size[i]
 ob=make(name,bm,m,col);ob.location=loc
 if bevel:
  mod=ob.modifiers.new('Rounded edges','BEVEL');mod.width=bevel;mod.segments=3
 return ob
def cyl(name,loc,r,h,m):
 bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=64,radius1=r,radius2=r,depth=h)
 ob=make(name,bm,m);ob.location=loc
 for f in ob.data.polygons:f.use_smooth=len(f.vertices)==4
 mod=ob.modifiers.new('Edge softness','BEVEL');mod.width=.003;mod.segments=3
 return ob
def line(name,pts,width,m,col=details):
 # Mesh ribbon for planar floor marks.
 vs=[];fs=[]
 for a,b in zip(pts[:-1],pts[1:]):
  a=Vector(a);b=Vector(b);d=(b-a).normalized();n=Vector((-d.y,d.x,0))*width/2
  k=len(vs);vs.extend([a+n,a-n,b-n,b+n]);fs.append((k,k+1,k+2,k+3))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(m);return ob
box('Floating test platform',(0,0,-.042),(1.7,1.35,.066),edge,.018)
box('Navigation floor',(0,0,-.004),(1.67,1.32,.008),floor,.004)
box('Studio ground',(0,0,-.089),(200,200,.04),back,0)
for i in range(-8,9):
 x=i*.1;line('Grid X %02d'%i,[(x,-.63,.0004),(x,.63,.0004)],.0008,grid)
for i in range(-6,7):
 y=i*.1;line('Grid Y %02d'%i,[(-.8,y,.0004),(.8,y,.0004)],.0008,grid)
box('Rear boundary',(0,.646,.065),(1.68,.035,.13),wall)
box('Left boundary',(-.819,0,.065),(.035,1.28,.13),wall)
box('Right boundary',(.819,.26,.065),(.035,.75,.13),wall)
box('Rear teal cap',(0,.646,.132),(1.67,.035,.006),teal,.002)
box('Inner low wall',(-.49,.26,.07),(.38,.035,.14),wall)
box('Obstacle block A',(.33,.04,.10),(.20,.20,.20),wall,.01)
box('Obstacle block A top',(.33,.04,.202),(.18,.18,.006),orange,.003)
box('Obstacle block B',(-.46,-.02,.065),(.14,.16,.13),wall,.008)
cyl('Obstacle cylinder A',(-.29,.39,.095),.09,.19,teal)
cyl('Obstacle cylinder A cap',(-.29,.39,.192),.087,.006,wall)
cyl('Obstacle cylinder B',(.49,.40,.075),.075,.15,orange)
# Start bay, goal ring and an illustrative route (not a recorded planner trajectory).
for x in [-.155,.155]:line('Start bay',[(x,-.52,.001),(x,-.22,.001)],.005,teal)
line('Start back',[(-.155,-.52,.001),(.155,-.52,.001)],.005,teal)
pts=[(0,-.20,.001),(0,-.02,.001),(-.04,.14,.001),(.06,.29,.001),(.09,.48,.001)]
for a,b in zip(pts[:-1],pts[1:]):
 a=Vector(a);b=Vector(b);length=(b-a).length;count=max(1,int(length/.035))
 for i in range(count):
  line('Illustrative route',[a+(b-a)*i/count,a+(b-a)*(i+.55)/count],.006,teal)
ring=[(.09+.061*math.cos(t*math.tau/80),.49+.061*math.sin(t*math.tau/80),.0015) for t in range(81)]
line('Goal marker',ring,.006,teal)
line('Goal plus X',[(.07,.49,.0015),(.11,.49,.0015)],.004,teal)
line('Goal plus Y',[(.09,.47,.0015),(.09,.51,.0015)],.004,teal)
def label(name,body,loc,size,m):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.00005
 ob=bpy.data.objects.new(name,cu);details.objects.link(ob);ob.location=loc;cu.materials.append(m)
label('Title','NAVBOT / NAVIGATION LAB',(-.76,-.615,.0015),.035,ink)
label('Goal label','GOAL',(.02,.575,.0015),.023,teal)
label('Zone label','01 / OBSTACLES',(.27,.20,.0015),.021,ink)
label('Scale label','0.10 m GRID',(.48,-.60,.0015),.019,ink)
# Copy hierarchy and meshes, keeping the original robot scene untouched.
copies={}
for old in bpy.data.collections['NavBot - URDF Robot'].objects:
 ob=old.copy()
 if old.data:ob.data=old.data.copy()
 bots.objects.link(ob);copies[old]=ob
for old,ob in copies.items():
 if old.parent in copies:
  ob.parent=copies[old.parent];ob.matrix_parent_inverse=old.matrix_parent_inverse.copy();ob.matrix_basis=old.matrix_basis.copy()
root=next(ob for old,ob in copies.items() if old.name=='base_footprint')
root.location=(0,-.37,.0002);root.rotation_euler.z=math.pi/2
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def camera(name,loc,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.005
 ob=bpy.data.objects.new(name,d);rig.objects.link(ob);ob.location=loc;aim(ob,target);return ob
overview=camera('Camera - Full Arena',(1.5,-2.1,2.15),(0,0,0),2.55)
hero=camera('Camera - Robot Detail',(.64,-1.13,.67),(0,-.18,.075),.88)
s.camera=overview
def light(name,loc,energy,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size
 ob=bpy.data.objects.new(name,d);rig.objects.link(ob);ob.location=loc;aim(ob,target)
light('Key softbox',(-1.1,-1.4,2.4),170,1.5,(0,0,0))
light('Cool fill',(1.3,.3,1.7),80,1.2,(0,0,.1))
light('Back rim',(-.4,1.6,1.9),120,1,(0,0,.1))
world=bpy.data.worlds.new('Arena studio world');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs[0].default_value=(.5,.6,.7,1);bg.inputs[1].default_value=.25;s.world=world
try:s.render.engine='CYCLES'
except TypeError:pass
if s.render.engine=='CYCLES':s.cycles.samples=96;s.cycles.use_denoising=True
s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath='//../renders/navbot_arena_overview.png'
s['route_note']='Floor route is illustrative, not recorded navigation data.'
bpy.context.window.scene=s
for a in bpy.context.screen.areas:
 if a.type=='VIEW_3D':
  a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/navbot_navigation_arena.blend'))
def render_preview():
 bpy.ops.render.render(write_still=True)
 return None
bpy.app.timers.register(render_preview,first_interval=1)
print('Arena saved; overview preview scheduled.')


