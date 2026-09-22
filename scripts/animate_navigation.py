"""Build a separate, keyframed navigation demo from the open arena scene."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
assert s.name=='NavBot - Navigation Arena'
output=ROOT/'blender/navbot_navigation_animation.blend'
assert not output.exists(), 'Animation file already exists'
col=bpy.data.collections['Arena - Robot']
root=next(o for o in col.objects if not o.parent)
left=next(o for o in col.objects if o.get('urdf_link')=='wheel_left_link')
right=next(o for o in col.objects if o.get('urdf_link')=='wheel_right_link')
assert all(o.animation_data is None for o in (root,left,right)), 'Existing animation found'
restL=left.rotation_euler.to_quaternion();restR=right.rotation_euler.to_quaternion()
left.rotation_mode=right.rotation_mode='QUATERNION'
points=[(0,-.37),(-.15,-.19),(-.15,.12),(.06,.25),(.09,.49)]
# Planar conservative envelope from all visual bounding boxes, with extra margin.
bpy.context.view_layer.update()
bounds=[root.matrix_world.inverted() @ o.matrix_world @ Vector(v) for o in col.objects if o.type=='MESH' for v in o.bound_box]
radius=max(math.hypot(p.x,p.y) for p in bounds)+.005
rects=[]
for name in ['Rear boundary','Left boundary','Right boundary','Inner low wall','Obstacle block A','Obstacle block B']:
 ob=bpy.data.objects[name];vs=[ob.matrix_world @ Vector(p) for p in ob.bound_box]
 rects.append((name,min(p.x for p in vs),max(p.x for p in vs),min(p.y for p in vs),max(p.y for p in vs)))
circles=[('Obstacle cylinder A',-.29,.39,.09),('Obstacle cylinder B',.49,.40,.075)]
def clearance(x,y):
 results=[]
 for name,x0,x1,y0,y1 in rects:
  dx=max(x0-x,0,x-x1);dy=max(y0-y,0,y-y1)
  results.append((math.hypot(dx,dy)-radius,name))
 for name,cx,cy,r in circles:results.append((math.hypot(x-cx,y-cy)-r-radius,name))
 return min(results)
fps=30;poses=[];x,y=points[0];yaw=math.pi/2;sl=sr=0
def push():poses.append((x,y,yaw,sl,sr))
for _ in range(30):push()
def ease(t):return t*t*(3-2*t)
for dest in points[1:]:
 dx=dest[0]-x;dy=dest[1]-y;distance=math.hypot(dx,dy)
 desired=math.atan2(dy,dx);delta=(desired-yaw+math.pi)%math.tau-math.pi
 if abs(delta)>1e-5:
  count=max(18,math.ceil(abs(delta)/.9*fps))
  y0=yaw;l0=sl;r0=sr
  for k in range(1,count+1):
   a=delta*ease(k/count);yaw=y0+a;sl=l0-.08*a;sr=r0+.08*a;push()
 x0,y0=x,y;l0,r0=sl,sr
 count=math.ceil(distance/.14*fps)
 for k in range(1,count+1):
  t=ease(k/count);x=x0+dx*t;y=y0+dy*t;sl=l0+distance*t;sr=r0+distance*t;push()
for _ in range(45):push()
minimum=min((clearance(p[0],p[1])[0],i+1,clearance(p[0],p[1])[1]) for i,p in enumerate(poses))
assert minimum[0]>0,minimum
# Bake every frame, wheel rotation = differential-drive travel / wheel radius.
for frame,(x,y,yaw,sl,sr) in enumerate(poses,1):
 root.location=(x,y,.0002);root.rotation_euler=(0,0,yaw)
 root.keyframe_insert(data_path='location',frame=frame,group='Navigation path')
 root.keyframe_insert(data_path='rotation_euler',frame=frame,group='Heading')
 left.rotation_quaternion=restL @ Quaternion((0,0,1),sl/.033)
 right.rotation_quaternion=restR @ Quaternion((0,0,1),sr/.033)
 left.keyframe_insert(data_path='rotation_quaternion',frame=frame,group='Wheel roll')
 right.keyframe_insert(data_path='rotation_quaternion',frame=frame,group='Wheel roll')
# Match the floor guide to the animation path.
for ob in list(bpy.data.collections['Arena - Markings'].objects):
 if ob.name.startswith('Illustrative route'):ob.hide_render=True;ob.hide_set(True)
me=bpy.data.meshes.new('Animation route');verts=[];faces=[]
for a,b in zip(points[:-1],points[1:]):
 a=Vector((*a,.0015));b=Vector((*b,.0015));d=b-a;n=Vector((-d.y,d.x,0)).normalized()*.003
 count=max(1,int(d.length/.035))
 for i in range(count):
  p=a+d*i/count;q=a+d*(i+.55)/count;k=len(verts)
  verts.extend([p+n,p-n,q-n,q+n]);faces.append((k,k+1,k+2,k+3))
me.from_pydata(verts,[],faces);me.update()
guide=bpy.data.objects.new('Animation route - illustrative',me)
bpy.data.collections['Arena - Markings'].objects.link(guide)
me.materials.append(bpy.data.materials['Arena | teal'])
s.render.fps=fps;s.frame_start=1;s.frame_end=len(poses)
s.camera=bpy.data.objects['Camera - Full Arena']
s.render.resolution_x=1280;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264'
s.render.filepath='//../renders/navbot_navigation_animation.mp4'
for name,frame in [('START',1),('DRIVE',31),('GOAL',len(poses)-44),('END',len(poses))]:
 marker=s.timeline_markers.new(name,frame=frame)
s['animation_note']='Preset navigation demonstration, not live obstacle avoidance or a ROS planner recording.'
s['animation_clearance_m']=minimum[0]
s.frame_set(1)
for a in [area for screen in bpy.data.screens for area in screen.areas]:
 if a.type=='VIEW_3D':
  a.spaces.active.region_3d.view_perspective='CAMERA'
  a.spaces.active.overlay.show_overlays=False
report={'frames':len(poses),'fps':fps,'duration_seconds':len(poses)/fps,'waypoints_m':points,'conservative_robot_radius_m':radius,'minimum_clearance_m':minimum[0],'closest_frame':minimum[1],'closest_obstacle':minimum[2],'wheel_radius_m':.033,'wheel_track_m':.16,'type':'keyframed differential-drive demonstration; no live navigation planner'}
(ROOT/'animation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(output))
print(json.dumps(report,indent=2))



