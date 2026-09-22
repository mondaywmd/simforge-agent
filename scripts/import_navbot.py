"""Import the bundled NavBot URDF visuals in Blender. Run via Blender > Scripting."""
import bpy, bmesh, json
import xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Matrix, Euler, Vector
ROOT = Path(__file__).resolve().parents[1]
URDF = ROOT / "urdf/turtlebot3_burger_dense.urdf"
robot = ET.parse(URDF).getroot()
def nums(value, default):
    return tuple(float(v) for v in (value or default).split())
def origin(element):
    e=element.find("origin")
    if e is None: return Matrix.Identity(4)
    return Matrix.Translation(nums(e.get("xyz"),"0 0 0")) @ Euler(nums(e.get("rpy"),"0 0 0")).to_matrix().to_4x4()
def resolve(uri):
    if uri.startswith("package://"):
        return ROOT / "assets" / uri[len("package://"):]
    return URDF.parent / uri
for m in robot.findall(".//visual/geometry/mesh"):
    assert resolve(m.get("filename")).is_file(),m.get("filename")
assert not bpy.data.collections.get("NavBot - URDF Robot"), "Robot already imported"
collection=bpy.data.collections.new("NavBot - URDF Robot")
bpy.context.scene.collection.children.link(collection)
materials={}
for e in robot.findall("material"):
    color=e.find("color")
    if color is None: continue
    rgba=nums(color.get("rgba"),"0.5 0.5 0.5 1")
    m=bpy.data.materials.new("NavBot - "+e.get("name"));m.use_nodes=True;m.diffuse_color=rgba
    bs=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    bs.inputs[0].default_value=rgba;bs.inputs[2].default_value=.55
    materials[e.get("name")]=m
links={}
for e in robot.findall("link"):
    ob=bpy.data.objects.new(e.get("name"),None);collection.objects.link(ob)
    ob.empty_display_size=.012;ob["urdf_link"]=e.get("name");links[e.get("name")]=ob
    inertial=e.find("inertial")
    if inertial is not None: ob["mass_kg"]=float(inertial.find("mass").get("value"))
for j in robot.findall("joint"):
    child=links[j.find("child").get("link")]
    child.parent=links[j.find("parent").get("link")]
    child.matrix_parent_inverse=Matrix.Identity(4);child.matrix_basis=origin(j)
    child["urdf_joint"]=j.get("name");child["joint_type"]=j.get("type")
    axis=j.find("axis")
    if axis is not None: child["joint_axis_local"]=nums(axis.get("xyz"),"1 0 0")
visuals=[]
for e in robot.findall("link"):
    for index,v in enumerate(e.findall("visual")):
        geo=v.find("geometry");mesh=geo.find("mesh");box=geo.find("box")
        if mesh is not None:
            before=set(bpy.data.objects)
            bpy.ops.wm.stl_import(filepath=str(resolve(mesh.get("filename"))),forward_axis="Y",up_axis="Z",use_scene_unit=False)
            added=set(bpy.data.objects)-before
            assert len(added)==1
            ob=added.pop()
            scale=nums(mesh.get("scale"),"1 1 1")
            ob.data.transform(Matrix.Diagonal((*scale,1)))
        elif box is not None:
            me=bpy.data.meshes.new(e.get("name")+" geometry");bm=bmesh.new()
            bmesh.ops.create_cube(bm,size=1);bm.to_mesh(me);bm.free()
            me.transform(Matrix.Diagonal((*nums(box.get("size"),"1 1 1"),1)))
            ob=bpy.data.objects.new(e.get("name")+" visual",me)
        else: raise ValueError("Unsupported visual geometry")
        for old in list(ob.users_collection): old.objects.unlink(ob)
        collection.objects.link(ob)
        ob.name=e.get("name")+"__visual"
        ob.parent=links[e.get("name")];ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=origin(v)
        material=v.find("material")
        if material is not None: ob.data.materials.append(materials[material.get("name")])
        ob["urdf_visual_index"]=index
        if mesh is not None: ob["source_mesh"]=mesh.get("filename")
        visuals.append(ob)
scene=bpy.context.scene
scene.unit_settings.system="METRIC";scene.unit_settings.scale_length=1
scene.render.filepath="//../renders/navbot.png"
bpy.context.view_layer.update()
bounds=[ob.matrix_world @ Vector(v) for ob in visuals for v in ob.bound_box]
lower=Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
upper=Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
center=(lower+upper)/2
for ob in bpy.context.selected_objects: ob.select_set(False)
for ob in visuals: ob.select_set(True)
bpy.context.view_layer.objects.active=visuals[0]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=="VIEW_3D":
            sp=area.spaces.active;sp.shading.color_type="MATERIAL"
            sp.region_3d.view_perspective="PERSP"
            sp.region_3d.view_location=center;sp.region_3d.view_distance=.65
            sp.region_3d.view_rotation=Vector((1.2,-1.5,.85)).to_track_quat("Z","Y")
report={"robot":robot.get("name"),"links":len(links),"joints":len(robot.findall("joint")),"visuals":len(visuals),"bounds_min_m":list(lower),"bounds_max_m":list(upper),"dimensions_m":list(upper-lower),"note":"Visual geometry and joint hierarchy imported; Gazebo sensor/controller plugins are retained in URDF, not executed in Blender."}
(ROOT/"import_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"blender/navbot.blend"))
print(json.dumps(report,indent=2))

