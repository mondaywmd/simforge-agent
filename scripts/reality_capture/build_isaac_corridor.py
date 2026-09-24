"""Run with Blender --background --python; creates a separate portable USD package."""
import bpy, bmesh, json, re, hashlib, math, sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
from pxr import Usd, UsdGeom, UsdShade, UsdPhysics, Sdf, Gf, Vt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sim/isaac_corridor';OUT.mkdir(parents=True,exist_ok=True)
config=json.loads((ROOT/'renders/sim_source_snapshot.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/config['snapshot']))
s=bpy.context.scene
source_hash=hashlib.sha256((ROOT/'blender/corridor_capture_matched.blend').read_bytes()).hexdigest()
def slug(x):
 x=re.sub('[^A-Za-z0-9_]+','_',x).strip('_')
 return ('n_'+x if x[:1].isdigit() else x) or 'Group'
def enum(o,key,value):
 assert value in [x.identifier for x in o.bl_rna.properties[key].enum_items],(key,value)
 setattr(o,key,value)
visible=[o for o in s.objects if o.visible_get() and not o.hide_render]
mesh_sources=[o for o in visible if o.type in {'MESH','CURVE'}]
groups={o.name:slug(o.users_collection[0].name) for o in visible}
COL=OUT/'textures';COL.mkdir(exist_ok=True)
materials={m.name:m for o in mesh_sources for m in o.data.materials if m}
notes=[];baked=[]
# Bake base-color networks that cannot be represented by USD Preview Surface.
# Each selected object's generated coordinates and world transform remain intact.
try:s.render.engine='CYCLES'
except TypeError:raise
s.cycles.samples=1;s.cycles.device='CPU'
for m in list(materials.values()):
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p or not p.inputs['Base Color'].is_linked:continue
 source=p.inputs['Base Color'].links[0].from_socket
 if source.node.type=='TEX_IMAGE':continue
 targets=[o for o in mesh_sources if o.type=='MESH' and m in list(o.data.materials)]
 if not targets:continue
 assert all(len(o.data.materials)==1 for o in targets),m.name
 print('BAKE',m.name,len(targets),flush=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in targets:
  o.select_set(True)
  if o.data.uv_layers.active:o.data.uv_layers.active.name='SourceUV'
 for n in list(m.node_tree.nodes):
  if n.type=='TEX_IMAGE' and not n.inputs['Vector'].is_linked:
   uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='SourceUV';m.node_tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
 for o in targets:
  uv=o.data.uv_layers.new(name='SimBakeUV');o.data.uv_layers.active=uv;uv.active_render=True
 bpy.context.view_layer.objects.active=targets[0]
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(island_margin=.012)
 bpy.ops.object.mode_set(mode='OBJECT')
 im=bpy.data.images.new('Baked_'+slug(m.name),width=2048,height=2048,alpha=False)
 im.generated_color=(.15,.1,.06,1)
 nodes=m.node_tree.nodes;links=m.node_tree.links
 output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
 original=output.inputs['Surface'].links[0].from_socket
 em=nodes.new('ShaderNodeEmission');links.new(source,em.inputs['Color']);links.new(em.outputs[0],output.inputs['Surface'])
 target=nodes.new('ShaderNodeTexImage');target.image=im;nodes.active=target
 cached=COL/('Baked_'+slug(m.name)+'.png')
 if cached.exists():
  cached_image=bpy.data.images.load(str(cached));target.image=cached_image;im=cached_image
 else:bpy.ops.object.bake(type='EMIT',use_clear=False,margin=8)
 links.new(original,output.inputs['Surface']);nodes.remove(em)
 for link in list(p.inputs['Base Color'].links):links.remove(link)
 links.new(target.outputs['Color'],p.inputs['Base Color'])
 uv=nodes.new('ShaderNodeUVMap');uv.uv_map='SimBakeUV';links.new(uv.outputs['UV'],target.inputs['Vector'])
 im.filepath_raw=str(cached);im.file_format='PNG';im.save();im.pack()
 baked.append(m.name)
# Normalize material graphs to a portable, explicit Preview Surface subset.
for m in materials.values():
 ns=m.node_tree.nodes;ls=m.node_tree.links
 p=next((n for n in ns if n.type=='BSDF_PRINCIPLED'),None)
 if not p:continue
 out=next(n for n in ns if n.type=='OUTPUT_MATERIAL')
 if m.name.startswith('Captured corridor'):
  tex=next(n for n in ns if n.type=='TEX_IMAGE' and n.image)
  for link in list(p.inputs['Base Color'].links):ls.remove(link)
  p.inputs['Base Color'].default_value=(0,0,0,1)
  p.inputs['Emission Strength'].default_value=1
  ls.new(tex.outputs['Color'],p.inputs['Emission Color'])
  p.inputs['Specular IOR Level'].default_value=0
  notes.append({'material':m.name,'conversion':'Captured-light texture -> emissive Preview Surface; not relightable albedo.'})
 if p.inputs['Normal'].is_linked:
  for link in list(p.inputs['Normal'].links):ls.remove(link)
  notes.append({'material':m.name,'conversion':'Procedural micro-bump omitted; base color and roughness retained.'})
 ls.new(p.outputs['BSDF'],out.inputs['Surface'])
 # Remove disconnected graphs, making portability explicit and export predictable.
 keep={p,out}
 def upstream(n):
  for inp in n.inputs:
   for link in inp.links:
    if link.from_node not in keep:keep.add(link.from_node);upstream(link.from_node)
 upstream(p)
 for n in list(ns):
  if n not in keep:ns.remove(n)
 m.name=slug(m.name)
# Generate collision meshes BEFORE visual modifiers are applied.
skip_prefix=('Floor plank','Woven rug stripe','Rug fringe','Sofa cushion piping','Floor chair horizontal crease',
 'Photo referenced shelf','Corridor nonrepeating','Corridor captured ceiling','West wall original','East wall original',
 'Whiteboard','Clock hour tick','Coffee table papers','Dining magazines','Media console books','Books on shelf',
 'Shoe lace','Remote button','Bathroom horizontal tile grout','Bathroom vertical tile grout','Bathroom floor grout',
 'Bathmat color band','Curtain horizontal check','Curtain vertical check','Stool anti slip','Luminaire casing seam')
collision={};decisions=[]
deps=bpy.context.evaluated_depsgraph_get()
shift=Matrix.Translation((0,0,-.08))
for o in mesh_sources:
 if o.name.startswith(skip_prefix):decisions.append({'object':o.name,'collision':'visual detail omitted'});continue
 if o.type=='MESH' and all(m.type in {'BEVEL','WEIGHTED_NORMAL'} for m in o.modifiers):me=o.data.copy()
 else:me=bpy.data.meshes.new_from_object(o.evaluated_get(deps))
 me.transform(shift@o.matrix_world)
 bm=bmesh.new();bm.from_mesh(me)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 key='Floor' if o.name.startswith('F01') else groups[o.name]
 verts,faces=collision.setdefault(key,([],[]));offset=len(verts)
 verts.extend([list(v.co) for v in me.vertices]);faces.extend([tuple(offset+i for i in p.vertices) for p in me.polygons if p.area>1e-10])
 decisions.append({'object':o.name,'collision':key,'triangles':len(me.polygons)})
 bpy.data.meshes.remove(me)
# Exclude reference scan and intentionally hidden alternatives from the asset.
for o in list(s.objects):
 if o not in visible:bpy.data.objects.remove(o,do_unlink=True)
visual_col=bpy.data.collections.new('SIM_Visual');s.collection.children.link(visual_col)
parents={}
for o in visible:
 key=groups[o.name]
 if key not in parents:
  p=bpy.data.objects.new('Group_'+key,None);visual_col.objects.link(p);parents[key]=p
 original=o.name
 if o.type in {'MESH','CURVE'}:
  if o.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
   bpy.ops.object.convert(target='MESH')
  me=bpy.data.meshes.new_from_object(o.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
  me.transform(shift@o.matrix_world)
  o.modifiers.clear();o.data=me
  o.matrix_world=Matrix.Identity(4)
 else:o.matrix_world=shift@o.matrix_world
 mat=o.matrix_world.copy();o.parent=parents[key];o.matrix_world=mat
 o['source_name']=original;o['semantic_class']=key
 o.name=slug(original)
 visual_col.objects.link(o)
 for c in list(o.users_collection):
  if c!=visual_col:c.objects.unlink(o)
for c in list(bpy.data.collections):
 if c!=visual_col and not c.objects:bpy.data.collections.remove(c)
bpy.context.view_layer.update()
# Only used image files travel in the package.
for im in bpy.data.images:
 if im.packed_file:continue
 if im.source=='FILE' and im.has_data:im.pack()
s.render.filepath='//../sim/isaac_corridor/preview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/corridor_sim_ready.blend'))
print('EXPORT VISUAL',flush=True)
bpy.ops.wm.usd_export(filepath=str(OUT/'visual.usdc'),selected_objects_only=False,export_animation=False,
 export_materials=True,generate_preview_surface=True,generate_materialx_network=False,
 export_textures_mode='NEW',overwrite_textures=True,relative_paths=True,root_prim_path='/Visual',
 export_custom_properties=True,allow_unicode=False,convert_orientation=False,convert_scene_units='METERS',
 export_subdivision='TESSELLATE',export_curves=False,export_hair=False,export_armatures=False,
 export_cameras=True,export_lights=True,convert_world_material=True,triangulate_meshes=True)
# Physics layer uses static triangle meshes, never a single convex hull across doors.
stage=Usd.Stage.CreateNew(str(OUT/'collision.usda'))
UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z);UsdGeom.SetStageMetersPerUnit(stage,1)
root=UsdGeom.Xform.Define(stage,'/Collision');stage.SetDefaultPrim(root.GetPrim())
phys=UsdShade.Material.Define(stage,'/Collision/PhysicsMaterial')
api=UsdPhysics.MaterialAPI.Apply(phys.GetPrim());api.CreateStaticFrictionAttr(.7);api.CreateDynamicFrictionAttr(.6);api.CreateRestitutionAttr(0)
for key,(verts,faces) in collision.items():
 if not faces:continue
 mesh=UsdGeom.Mesh.Define(stage,'/Collision/'+key)
 points=np.asarray(verts,dtype=np.float32);tri=np.asarray(faces,dtype=np.int32)
 mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(points));mesh.CreateFaceVertexCountsAttr([3]*len(faces));mesh.CreateFaceVertexIndicesAttr(tri.flatten().tolist())
 mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none);mesh.CreateExtentAttr([Gf.Vec3f(*points.min(axis=0).tolist()),Gf.Vec3f(*points.max(axis=0).tolist())])
 mesh.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
 UsdPhysics.CollisionAPI.Apply(mesh.GetPrim()).CreateCollisionEnabledAttr(True)
 UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr(UsdPhysics.Tokens.none)
 UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(phys,UsdShade.Tokens.weakerThanDescendants,'physics')
stage.GetRootLayer().Save()
# Referenceable environment asset; no PhysicsScene or robot is embedded here.
stage=Usd.Stage.CreateNew(str(OUT/'corridor.usda'));UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z);UsdGeom.SetStageMetersPerUnit(stage,1)
UsdPhysics.SetStageKilogramsPerUnit(stage,1)
root=UsdGeom.Xform.Define(stage,'/Corridor');stage.SetDefaultPrim(root.GetPrim())
root.GetPrim().SetAssetInfoByKey('name','Corridor capture-matched navigation environment')
UsdGeom.Xform.Define(stage,'/Corridor/Visual').GetPrim().GetReferences().AddReference('./visual.usdc','/Visual')
UsdGeom.Xform.Define(stage,'/Corridor/Collision').GetPrim().GetReferences().AddReference('./collision.usda','/Collision')
stage.GetRootLayer().Save()
# Standalone stage for opening and physics testing.
stage=Usd.Stage.CreateNew(str(OUT/'test_scene.usda'));UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z);UsdGeom.SetStageMetersPerUnit(stage,1)
UsdPhysics.SetStageKilogramsPerUnit(stage,1)
root=UsdGeom.Xform.Define(stage,'/World');stage.SetDefaultPrim(root.GetPrim())
UsdGeom.Xform.Define(stage,'/World/Corridor').GetPrim().GetReferences().AddReference('./corridor.usda','/Corridor')
physics=UsdPhysics.Scene.Define(stage,'/World/PhysicsScene');physics.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));physics.CreateGravityMagnitudeAttr(9.81)
for name,pos in [('Start',(-.28,-2.45,.0)),('HallGoal',(-.28,1.8,.0))]:
 marker=UsdGeom.Xform.Define(stage,'/World/Navigation/'+name);marker.AddTranslateOp().Set(Gf.Vec3d(*pos))
 marker.GetPrim().CreateAttribute('sim:note',Sdf.ValueTypeNames.String).Set('Reference floor position; robot root height depends on its asset.')
stage.GetRootLayer().Save()
# Blender collision-preview collection remains separate and disabled in beauty views.
cc=bpy.data.collections.new('SIM_Collision - preview only');s.collection.children.link(cc)
for key,(verts,faces) in collision.items():
 if not faces:continue
 me=bpy.data.meshes.new('COL_'+key);me.from_pydata(verts,[],faces);me.update()
 o=bpy.data.objects.new('COL_'+key,me);cc.objects.link(o);enum(o,'display_type','WIRE');o.hide_render=True;o.hide_set(True)
 o['usd_collision']='static triangle mesh; see collision.usda'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/corridor_sim_ready.blend'))
manifest={'source_blend':'corridor_capture_matched.blend','source_sha256':source_hash,'input_snapshot_sha256':hashlib.sha256((ROOT/config['snapshot']).read_bytes()).hexdigest(),'units':'meter','up_axis':'Z',
 'original_to_asset_translation':[0,0,-.08],'visual_objects':len(mesh_sources),'collider_groups':len(collision),
 'collision_triangles':sum(len(f) for v,f in collision.values()),'baked_base_color_materials':baked,'material_changes':notes,
 'collision_policy':'Static un-beveled geometry grouped by semantic class; visual microdetails excluded. Door openings are preserved by triangle meshes, not convex room bounds.',
 'friction':{'static':.7,'dynamic':.6,'restitution':0,'status':'assumed, not measured'},
 'navigation_probe':{'radius_m':.13,'height_m':.22,'start_xy':[-.28,-2.45],'goal_xy':[-.28,1.8]},
 'validation_status':{'usd_static':'pending','isaac_runtime':'not_run - Isaac Sim unavailable','robot_navigation':'not_run','sensors':'not_run'},
 'limitations':['Scale inherited from scan fitting; not calibrated to physical measurements.','Static environment: no door joints or movable furniture physics.',
 'Captured textures contain original lighting; emission conversion is appearance-oriented, not fully relightable PBR.',
 'Procedural micro-bump is omitted. Base-color procedural networks are baked.',
 'Unscanned and inferred perimeter geometry is retained as modeled; only validated free space should be used for navigation.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
(OUT/'collision_sources.json').write_text(json.dumps(decisions,indent=2),encoding='utf8')
np.savez_compressed(OUT/'collision_geometry.npz',**{k+'_'+field:np.asarray(data) for k,(v,f) in collision.items() for field,data in [('vertices',v),('triangles',f)]})
assert hashlib.sha256((ROOT/'blender/corridor_capture_matched.blend').read_bytes()).hexdigest()==source_hash
print('BUILD COMPLETE',manifest['collision_triangles'],flush=True)
