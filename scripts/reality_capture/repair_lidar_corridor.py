"""Independent scan-cleanup branch. Starts only from corridor_scaniverse.blend.
Keeps original scan furniture and UVs outside selected corridor architecture.
"""
import bpy,bmesh,json,hashlib,math,shutil
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
protected=[ROOT/'blender'/n for n in ['corridor_scaniverse.blend','corridor_capture_matched.blend','home_reconstructed_photoref.blend']]
filehash=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.name:filehash(p) for p in protected}
bpy.ops.wm.open_mainfile(filepath=str(protected[0]));s=bpy.context.scene;s.name='LiDAR corridor - repaired scan branch'
source=next(o for o in s.objects if o.type=='MESH');source.name='Original scan - untouched reference'
ref=bpy.data.collections.new('90_ORIGINAL_SCAN - untouched hidden backup');s.collection.children.link(ref)
for c in list(source.users_collection):c.objects.unlink(source)
ref.objects.link(source);ref.hide_viewport=True;ref.hide_render=True
working=source.copy();working.data=source.data.copy();working.name='LiDAR scan - locally repaired';s.collection.objects.link(working)
working.hide_render=False;working.hide_set(False);working.hide_select=False
working.parent=None;working.matrix_world=source.matrix_world.copy()
me=working.data
bm=bmesh.new();bm.from_mesh(me)
initial={'vertices':len(bm.verts),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges)}
# Join coincident geometric seams; corner UVs remain per-loop and are preserved.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00015)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001)
bm.normal_update()
west=lambda y:-.82554+.012874*y
east=lambda y:.26367+.005341*y
gaps={'west':[(-4.12,-3.53),(-2.65,-1.53),(-1.27,-.36)],'east':[(-3.98,-3.20),(-1.73,-.84)]}
def region(p,n=None):
 x,y,z=p
 if -4.12<y<1.25:
  if -.88<x<.32 and 2.57<z<2.87 and (n is None or abs(n.z)>.65):return 'ceiling'
  if west(y)+.025<x<east(y)-.025 and -.015<z<.18 and (n is None or abs(n.z)>.70):return 'floor'
  for side,fn in [('west',west),('east',east)]:
   if abs(x-fn(y))<.105 and .18<z<2.72:
    if z<2.42 and any(a-.18<y<b+.18 for a,b in gaps[side]):continue
    # Keep raised switches, door hardware, vent and pull-up bar as captured geometry.
    if side=='east' and .30<y<1.15 and z>2.15:continue
    if .97<y<1.25 and 1.80<z<2.14:continue
    return side
 return None
classes={f:region(f.calc_center_median(),f.normal) for f in bm.faces}
votes={}
for f,key in classes.items():
 if key:
  for v in f.verts:votes.setdefault(v,{}).setdefault(key,0);votes[v][key]+=f.calc_area()
movement=[];counts={k:0 for k in ['west','east','floor','ceiling']}
for v,tally in votes.items():
 key=max(tally,key=tally.get);old=v.co.copy();x,y,z=v.co
 if region(v.co)!=key:continue
 if any(classes.get(f)!=key for f in v.link_faces):continue # Freeze trim/door/furniture transition vertices.
 # Exact flattening is restricted to the selected architectural scan vertices.
 if key=='west':v.co.x=west(y)
 elif key=='east':v.co.x=east(y)
 elif key=='floor':v.co.z=.08
 elif key=='ceiling':v.co.z=2.68
 movement.append((v.co-old).length);counts[key]+=1
bm.normal_update()
# Small true boundary loops: fill only known solid architecture, never doorway openings.
seen=set();filled=[];unfilled=[]
for edge in list(bm.edges):
 if not edge.is_boundary or edge in seen:continue
 stack=[edge];component=[];verts=set()
 while stack:
  e=stack.pop()
  if e in seen:continue
  seen.add(e);component.append(e);verts.update(e.verts)
  for v in e.verts:
   stack.extend(q for q in v.link_edges if q.is_boundary and q not in seen)
 if len(component)<3:continue
 center=sum((v.co for v in verts),Vector())/len(verts);key=region(center)
 closed=all(sum(e in component for e in v.link_edges)==2 for v in verts)
 diameter=max((v.co-center).length for v in verts)*2
 if closed and key and diameter<(.75 if key=='ceiling' else .50) and len(component)<180:
  result=bmesh.ops.holes_fill(bm,edges=component,sides=0)
  for f in result.get('faces',[]):classes[f]=key
  if result.get('faces'):filled.append({'region':key,'diameter_m':diameter,'faces':len(result.get('faces',[]))})
 else:unfilled.append({'edges':len(component),'diameter_m':diameter,'center':list(center)})
# Locally bridge the visibly missing transom above the bathroom door, behind its original frame.
# This is an explicit scan-gap patch, not a newly reconstructed room or replacement furniture.
patchverts=[bm.verts.new(p) for p in [(.32,-1.78,2.24),(.32,-1.78,2.68),(.32,-.80,2.68),(.32,-.80,2.24)]]
transom=bm.faces.new(patchverts);classes[transom]='east'
# New planar UV charts affect only repaired architectural faces, not the source furniture UVs.
assets=ROOT/'assets/lidar_repair';assets.mkdir(exist_ok=True)
charts=json.loads((ROOT/'assets/corridor_capture/charts.json').read_text())
specs={x['name']:x for x in charts}
def enum(obj,prop,value):
 assert value in [i.identifier for i in obj.bl_rna.properties[prop].enum_items];setattr(obj,prop,value)
indices={}
for key in counts:
 dst=assets/(key+'.png');assert dst.exists(), 'Run prepare_lidar_repair_textures.py first'
 m=bpy.data.materials.new('Scan repair - '+key);nodes=m.node_tree.nodes;links=m.node_tree.links
 p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.8
 tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(dst));tex.image.pack();enum(tex,'extension','EXTEND');links.new(tex.outputs['Color'],p.inputs['Base Color'])
 # Keep captured appearance usable in material preview and render without doubling its lighting.
 emission=nodes.new('ShaderNodeEmission');links.new(tex.outputs['Color'],emission.inputs['Color'])
 output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');links.new(emission.outputs[0],output.inputs['Surface'])
 indices[key]=len(me.materials);me.materials.append(m)
uv=bm.loops.layers.uv.active
retextured={k:0 for k in counts}
for f in bm.faces:
 key=classes.get(f)
 if f!=transom and key in ['west','east'] and any(region(v.co)!=key for v in f.verts):key=None
 if key:
  sp=specs[key];o=Vector(sp['origin']);u=Vector(sp['u']);v=Vector(sp['v'])
  f.material_index=indices[key]
  for loop in f.loops:
   p=loop.vert.co-o;loop[uv].uv=(p.dot(u)/u.length_squared,p.dot(v)/v.length_squared)
  retextured[key]+=1
bm.normal_update();bm.to_mesh(me);bm.free();me.update()
# Use original texture appearance for untouched scan, with no additional synthetic light rig.
originalmat=me.materials[0].copy();originalmat.name='Original captured appearance - scan branch';me.materials[0]=originalmat
ns=originalmat.node_tree.nodes;ls=originalmat.node_tree.links;tex=next(n for n in ns if n.type=='TEX_IMAGE');out=next(n for n in ns if n.type=='OUTPUT_MATERIAL');em=ns.new('ShaderNodeEmission');ls.new(tex.outputs['Color'],em.inputs['Color']);ls.new(em.outputs[0],out.inputs['Surface'])
cam=bpy.data.objects.new('Comparison camera',bpy.data.cameras.new('Comparison camera'));s.collection.objects.link(cam);s.camera=cam;cam.data.lens=20;cam.data.clip_start=.02
cam.location=(-.28,-2.45,1.65);cam.rotation_euler=(Vector((-.25,4.2,1.45))-cam.location).to_track_quat('-Z','Y').to_euler()
try:s.render.engine='BLENDER_WORKBENCH'
except TypeError as e:raise RuntimeError(str(e))
enum(s.display.shading,'light','FLAT');enum(s.display.shading,'color_type','TEXTURE');s.display.shading.show_shadows=False;s.display.shading.show_cavity=False
s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;enum(sp.shading,'type','SOLID');enum(sp.shading,'light','FLAT');enum(sp.shading,'color_type','TEXTURE');sp.shading.show_shadows=False;sp.use_local_camera=True;sp.camera=cam;enum(sp.region_3d,'view_perspective','CAMERA');sp.region_3d.view_camera_zoom=0;sp.region_3d.view_camera_offset=(0,0);sp.overlay.show_overlays=False
s['Method']='Original LiDAR mesh locally flattened, micro-seams welded, small architectural holes filled, repaired metric UV charts. Scan furniture retained. Independent alternative branch.'
report={'protected_files_before':before,'initial':initial,'repaired_vertices_by_region':counts,'max_displacement_m':max(movement),'median_displacement_m':float(np.median(movement)),'filled_hole_loops':filled,'explicit_transom_gap_patches':1,'retextured_faces':retextured,'final_vertices':len(me.vertices),'final_faces':len(me.polygons),'unfilled_boundary_components':len(unfilled),'largest_unfilled':sorted(unfilled,key=lambda x:x['diameter_m'],reverse=True)[:12]}
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/corridor_lidar_repaired.blend'))
s.render.filepath=str(ROOT/'renders/lidar_repaired_hall.png');bpy.ops.render.render(write_still=True)
cam.location=(-.28,-1.62,1.60);cam.rotation_euler=(Vector((-.25,3.8,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/'renders/lidar_repaired_close.png');bpy.ops.render.render(write_still=True)
report['protected_files_after']={p.name:filehash(p) for p in protected};assert report['protected_files_before']==report['protected_files_after']
(ROOT/'renders/lidar_repair_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
