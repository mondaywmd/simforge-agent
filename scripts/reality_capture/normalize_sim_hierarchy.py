"""Create v2 with a single normalization root; never save any source blend."""
import bpy, json, hashlib, shutil
import numpy as np
from pathlib import Path
from mathutils import Matrix
from pxr import Usd,UsdGeom,UsdUtils,Gf,Vt,Sdf
R=Path(__file__).resolve().parents[1];P=R/'sim/isaac_corridor_v2'
assert not P.exists(),'Use a new output directory, do not overwrite an existing revision'
protected=[R/'blender'/n for n in ['corridor_capture_matched.blend','home_reconstructed_photoref.blend','home_reconstructed_furnished.blend','corridor_architecture.blend']]
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
config=json.loads((R/'renders/sim_source_snapshot.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/config['snapshot']))
s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
def verts(o,evaluated=False):
 me=bpy.data.meshes.new_from_object(o.evaluated_get(deps)) if evaluated else o.data
 a=np.empty((len(me.vertices),3),np.float64);me.vertices.foreach_get('co',a.ravel())
 m=np.array(o.matrix_world);a=a@m[:3,:3].T+m[:3,3]
 if evaluated:bpy.data.meshes.remove(me)
 return a
def box(a):return {'min':a.min(0).tolist(),'max':a.max(0).tolist(),'size':(a.max(0)-a.min(0)).tolist()}
selected=[o for o in s.objects if o.visible_get() and not o.hide_render]
source_components={o.name:{'type':o.type,'bbox':box(verts(o,True))} if o.type in {'MESH','CURVE'} else {'type':o.type,'matrix':np.array(o.matrix_world).tolist()} for o in selected}
source_bounds=box(np.array([v['bbox'][k] for v in source_components.values() if 'bbox' in v for k in ['min','max']]))
source_counts={'total_objects':len(s.objects),'exported_components':len(selected),'excluded_hidden_objects':len(s.objects)-len(selected),'mesh_or_curve':sum(o.type in {'MESH','CURVE'} for o in selected),'lights':sum(o.type=='LIGHT' for o in selected),'cameras':sum(o.type=='CAMERA' for o in selected)}
floor=verts(bpy.data.objects['F01 Continuous architectural floor'],True)
floor_before=float(floor[:,2].max())
units={'system':s.unit_settings.system,'meters_per_unit':s.unit_settings.scale_length,'up_axis':'Z'}
images={n.image.name:n.image for o in selected if hasattr(o.data,'materials') for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
source_textures=[{'name':im.name,'packed':bool(im.packed_file),'available':bool(im.has_data or im.packed_file or Path(bpy.path.abspath(im.filepath)).is_file())} for im in images.values()]
# The old independent Sim version already has -0.08 baked into coordinates.
# Undo that baked translation, then apply exactly one root transform.
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/corridor_sim_ready.blend'))
s=bpy.context.scene;existing=list(s.objects)
before_world={o.name:verts(o) if o.type=='MESH' else np.array(o.matrix_world).copy() for o in existing}
for o in existing:
 if o.type=='MESH':o.data.transform(Matrix.Translation((0,0,.08)))
 elif o.type in {'CAMERA','LIGHT'}:o.location.z+=.08
bpy.context.view_layer.update()
before_normalize={o.name:verts(o) if o.type=='MESH' else np.array(o.matrix_world).copy() for o in existing}
root=bpy.data.objects.new('SIM_ROOT_GroundNormalization',None);s.collection.objects.link(root)
for o in existing:
 if o.parent is None:
  m=o.matrix_world.copy();o.parent=root;o.matrix_world=m
root.location=(0,0,-.08);root['normalization_translation_m']=[0.,0.,-.08]
root['note']='Single normalization transform for visuals, colliders, cameras and lights. Child geometry is in original source-world coordinates.'
bpy.context.view_layer.update()
errors=[];source_errors=[];component_rows=[]
for o in existing:
 after=verts(o) if o.type=='MESH' else np.array(o.matrix_world)
 expected=before_normalize[o.name].copy()
 if o.type=='MESH':expected[:,2]-=.08
 else:expected[2,3]-=.08
 error=float(np.max(np.abs(after-expected)));errors.append(error)
 # Compare all geometry/camera/light world positions with previous exported version.
 if o.type in {'MESH','CAMERA','LIGHT'}:assert np.max(np.abs(after-before_world[o.name]))<2e-6,o.name
 original=o.get('source_name')
 if original:
  src=source_components[original]
  row={'source_name':original,'export_name':o.name,'type':o.type,'common_translation_error_m':error}
  if o.type=='MESH':
   row['before_bbox']=src['bbox'];row['after_bbox']=box(after)
   expected_box=np.array([src['bbox']['min'],src['bbox']['max']])+[0,0,-.08]
   row['source_bbox_error_m']=float(np.max(np.abs(np.array([row['after_bbox']['min'],row['after_bbox']['max']])-expected_box)))
   source_errors.append(row['source_bbox_error_m'])
  else:
   row['before_matrix']=src['matrix'];row['after_matrix']=after.tolist()
   e=np.array(src['matrix']);e[2,3]-=.08;source_errors.append(float(np.max(np.abs(e-after))))
  component_rows.append(row)
assert max(errors)<2e-6 and max(source_errors)<2e-5,(max(errors),max(source_errors))
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/corridor_isaac_export_v2.blend'))
shutil.copytree(R/'sim/isaac_corridor',P)
# Restore source-space USD geometry, preserving names, materials and relationships.
def usd_points(prim,cache):
 a=np.array(UsdGeom.Mesh(prim).GetPointsAttr().Get(),dtype=np.float64)
 m=np.array(cache.GetLocalToWorldTransform(prim));return a@m[:3,:3]+m[3,:3]
old_stage=Usd.Stage.Open(str(R/'sim/isaac_corridor/corridor.usda'));cache=UsdGeom.XformCache()
old_meshes={str(p.GetPath()):usd_points(p,cache) for p in old_stage.Traverse() if p.IsA(UsdGeom.Mesh)}
for name in ['visual.usdc','collision.usda']:
 stage=Usd.Stage.Open(str(P/name))
 for prim in stage.Traverse():
  if prim.IsA(UsdGeom.Mesh):
   me=UsdGeom.Mesh(prim);a=np.array(me.GetPointsAttr().Get(),dtype=np.float32);a[:,2]+=.08
   me.GetPointsAttr().Set(Vt.Vec3fArray.FromNumpy(a));me.CreateExtentAttr([Gf.Vec3f(*a.min(0).tolist()),Gf.Vec3f(*a.max(0).tolist())])
  elif prim.IsA(UsdGeom.Camera) or prim.GetTypeName().endswith('Light'):
   if prim.GetTypeName()=='DomeLight':continue
   # Blender exports camera/light data below the object transform. Translate
   # that object transform in its unrotated group space, not sensor-local Z.
   x=UsdGeom.Xformable(prim.GetParent())
   ops=x.GetOrderedXformOps();op=x.AddTranslateOp(opSuffix='restoreSourceSpace');op.Set(Gf.Vec3d(0,0,.08));x.SetXformOpOrder([op]+ops)
 stage.GetRootLayer().Save()
stage=Usd.Stage.Open(str(P/'corridor.usda'));UsdGeom.Xformable(stage.GetDefaultPrim()).AddTranslateOp(opSuffix='groundNormalization').Set(Gf.Vec3d(0,0,-.08));stage.GetRootLayer().Save()
cache=UsdGeom.XformCache();usd_errors=[];vb=[];cb=[];floor_after=None
for prim in stage.Traverse():
 if not prim.IsA(UsdGeom.Mesh):continue
 a=usd_points(prim,cache);usd_errors.append(float(np.max(np.abs(a-old_meshes[str(prim.GetPath())]))))
 (cb if '/Collision/' in str(prim.GetPath()) else vb).extend([a.min(0),a.max(0)])
 if str(prim.GetPath())=='/Corridor/Collision/Floor':floor_after=float(a[:,2].max())
assert max(usd_errors)<2e-6
layers,assets,missing=UsdUtils.ComputeAllDependencies(str(P/'corridor.usda'));assert not missing
# Diagnostic NPZ is documented as world-space; its numbers remain unchanged.
checker=(P/'validate_asset.py').read_text()
checker=checker.replace('collisions={};visual_meshes=0;', 'xform_cache=UsdGeom.XformCache()\n collisions={};visual_meshes=0;')
checker=checker.replace("mesh=UsdGeom.Mesh(prim);v=np.asarray(mesh.GetPointsAttr().Get(),dtype=np.float64)","mesh=UsdGeom.Mesh(prim);v=np.asarray(mesh.GetPointsAttr().Get(),dtype=np.float64)\n  matrix=np.array(xform_cache.GetLocalToWorldTransform(prim));v=v@matrix[:3,:3]+matrix[3,:3]")
(P/'validate_asset.py').write_text(checker,encoding='utf8')
after_counts={'visual_meshes':len(component_rows)-source_counts['lights']-source_counts['cameras'],'lights':source_counts['lights'],'cameras':source_counts['cameras'],'collision_groups':48,'scene_objects_in_blend':len(s.objects),'normalization_roots':1}
report={'protected_files':{p.name:{'before_sha256':hashes[p.name],'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'unchanged':hashes[p.name]==hashlib.sha256(p.read_bytes()).hexdigest()} for p in protected},
 'scope':'Bboxes are evaluated visual mesh/curve geometry only, excluding lights/cameras and hidden scan. Collision bounds reported separately. Component table includes cameras and lights.',
 'normalization':{'method':'single common root transform','blender_root':root.name,'usd_root':'/Corridor','translation_m':[0,0,-.08],'max_component_translation_error_m':max(errors),'max_source_component_bbox_or_matrix_error':max(source_errors),'max_usd_world_vertex_difference_from_v1_m':max(usd_errors)},
 'before':{'visual_bbox_m':source_bounds,'floor_top_z_m':floor_before,'units':units,'counts':source_counts,'missing_textures':[t['name'] for t in source_textures if not t['available']],'textures':source_textures},
 'after':{'visual_bbox_m':box(np.array(vb)),'collision_bbox_m':box(np.array(cb)),'floor_top_z_m':floor_after,'units':{'system':'METRIC','meters_per_unit':UsdGeom.GetStageMetersPerUnit(stage),'up_axis':str(UsdGeom.GetStageUpAxis(stage))},'counts':after_counts,'texture_asset_count':len(assets),'missing_textures':list(missing)},
 'excluded':'87 hidden/reference objects were excluded in the original Sim export. 48 collider objects and grouping/root empties are additional, not lost visual components.',
 'runtime_validation':'Isaac Sim not installed; no runtime validation claimed.'}
assert all(x['unchanged'] for x in report['protected_files'].values())
(P/'conversion_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(P/'component_transforms.json').write_text(json.dumps(component_rows,ensure_ascii=False,indent=2),encoding='utf8')
m=json.loads((P/'manifest.json').read_text());m['normalization_root']='/Corridor';m['normalization_method']='single root transform, source-space layer geometry';m['collision_geometry_npz_space']='normalized world coordinates';m['validation_status']['usd_static']='pending v2 recheck';m['validation_status']['relocated_package']='pending v2 recheck';(P/'manifest.json').write_text(json.dumps(m,indent=2))
readme=(P/'README.md').read_text(encoding='utf8');readme+='\n## v2 统一根节点与转换审计\n\n地面归零由 `/Corridor` 的单一 `(0,0,-0.08)` 平移完成；视觉、碰撞、相机和灯光共同继承。`visual.usdc` / `collision.usda` 独立层保存源坐标，单独打开时地面是 0.08 m；请以 `corridor.usda` 或 `test_scene.usda` 为仿真入口。Blender 独立工作文件为 `corridor_isaac_export_v2.blend`，所有组件在 `SIM_ROOT_GroundNormalization` 下。\n\n`conversion_audit.json` 记录转换前后包围盒、地面高度、单位、up-axis、组件数量、纹理缺失及受保护源文件哈希。`component_transforms.json` 是逐组件核对表。诊断 NPZ 沿用归零后的世界坐标；静态验证脚本从 USD 实际组合世界变换计算碰撞。\n'
(P/'README.md').write_text(readme,encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
