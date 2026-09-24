"""Independent, low-poly architectural reconstruction. Scan is reference only.
Run in a background Blender process. All output meshes are authored from dimensions.
"""
import bpy, bmesh, math, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/corridor_scaniverse.blend'))
s=bpy.context.scene
s.name='Reconstructed Architecture'
ref=bpy.data.collections.new('90_REFERENCE_SCAN - original, hidden')
s.collection.children.link(ref)
scan_objects=list(s.objects)
for o in scan_objects:
    for col in list(o.users_collection): col.objects.unlink(o)
    ref.objects.link(o)
    o.hide_render=True
    o.hide_select=True
for col in list(s.collection.children):
    if col != ref and len(col.all_objects)==0: bpy.data.collections.remove(col)
ref.hide_viewport=True
ref.hide_render=True
scan=next(o for o in scan_objects if o.type=='MESH')
def fingerprint(mesh):
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    loops=np.empty(len(mesh.loops),np.int32);mesh.loops.foreach_get('vertex_index',loops)
    h=hashlib.sha256(co.tobytes()+loops.tobytes())
    for layer in mesh.uv_layers:
        uv=np.empty(len(layer.data)*2,np.float32);layer.data.foreach_get('uv',uv);h.update(uv.tobytes())
    return h.hexdigest()
original_hash=fingerprint(scan.data)
def collection(name):
    c=bpy.data.collections.new(name);s.collection.children.link(c);return c
walls=collection('01_ARCHITECTURE - measured walls and openings')
floors=collection('02_FLOORS - reconstructed footprint')
ceilings=collection('03_CEILINGS - toggle visibility for interior')
inferred=collection('04_INFERRED - incomplete scan boundaries')
views=collection('80_CAMERAS')
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=.8
    return m
wallmat=material('Architecture - warm plaster',(.72,.75,.77))
floormat=material('Architecture - floor',(.30,.38,.43))
infermat=material('Inferred boundary - review',(.63,.43,.20))
ceilmat=material('Architecture - ceiling',(.85,.86,.86))
objects=[]
def make(name,verts,faces,col,mat,confidence='scan measured'):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    ob=bpy.data.objects.new(name,mesh);col.objects.link(ob);mesh.materials.append(mat)
    ob['evidence']=confidence;ob['construction']='New authored planar quad surfaces; no scan geometry reused'
    objects.append(ob);return ob
def grid_solid(name,U,V,inside,convert,col,mat,confidence='scan measured'):
    """Extruded 2D grid union: welded quad shell, no internal faces or booleans."""
    cells={(i,j) for i in range(len(U)-1) for j in range(len(V)-1)
           if inside((U[i]+U[i+1])/2,(V[j]+V[j+1])/2)}
    verts=[];faces=[];index={}
    def vertex(i,j,k):
        key=(i,j,k)
        if key not in index:index[key]=len(verts);verts.append(convert(U[i],V[j],k))
        return index[key]
    def face(keys):faces.append([vertex(*key) for key in keys])
    for i,j in sorted(cells):
        for k in [0,1]:face([(i,j,k),(i+1,j,k),(i+1,j+1,k),(i,j+1,k)])
        if (i-1,j) not in cells:face([(i,j,0),(i,j+1,0),(i,j+1,1),(i,j,1)])
        if (i+1,j) not in cells:face([(i+1,j,0),(i+1,j+1,0),(i+1,j+1,1),(i+1,j,1)])
        if (i,j-1) not in cells:face([(i,j,0),(i+1,j,0),(i+1,j,1),(i,j,1)])
        if (i,j+1) not in cells:face([(i,j+1,0),(i+1,j+1,0),(i+1,j+1,1),(i,j+1,1)])
    return make(name,verts,faces,col,mat,confidence)
F=.08;TOP=2.68
def wall(name,p0,p1,thickness=.12,openings=(),bottom=F,top=TOP,col=walls,confidence='scan measured'):
    p0=Vector((*p0,0));p1=Vector((*p1,0));d=p1-p0;length=d.length;d.normalize()
    normal=Vector((-d.y,d.x,0))
    # p0/p1 denote the measured face; thickness extends toward the supplied side.
    U=sorted(set([0,length]+[t for op in openings for t in op[:2]]))
    V=sorted(set([bottom,top]+[z for op in openings for z in op[2:]]))
    def inside(u,z):return not any(a<u<b and c<z<e for a,b,c,e in openings)
    return grid_solid(name,U,V,inside,lambda u,z,k:tuple(p0+d*u+normal*(k*thickness)+Vector((0,0,z))),col,infermat if col==inferred else wallmat,confidence)
# Corridor face coordinates from weighted fits to near-vertical scan triangles.
west=lambda y:-.82554+.012874*y
east=lambda y:.26367+.005341*y
Y0=-4.15;Y1=1.28
west_open=[(-2.65,-1.53,F,2.23),(-1.27,-.36,F,2.23),(-4.12,-3.53,F,2.23)]
east_open=[(-3.98,-3.20,F,2.21),(-1.73,-.84,F,2.24)]
def corridor_wall(name,fn,openings,thick):
    fac=math.sqrt(1+((fn(Y1)-fn(Y0))/(Y1-Y0))**2)
    ops=[((a-Y0)*fac,(b-Y0)*fac,z0,z1) for a,b,z0,z1 in openings]
    return wall(name,(fn(Y0),Y0),(fn(Y1),Y1),thick,ops)
corridor_wall('W01 Corridor west - three openings',west,west_open,.12)
corridor_wall('W02 Corridor east - two openings',east,east_open,-.12)
# Lounge transverse wall and beam at corridor end. Opening is full corridor width.
wall('W03 West room to lounge',(-4.35,1.28),(west(1.28),1.28),.12)
wall('W04 East lounge return',(east(1.28),1.28),(2.97,1.337),.12)
wall('B01 Corridor to lounge header',(west(1.28),1.28),(east(1.28),1.28),.18,bottom=2.31)
# Well-observed perimeter planes; slight plan rotations retained from fits.
wall('W05a West rooms outside south fragment',(-4.3335,-4.15),(-4.3406,-2.60),.14)
wall('W05b West rooms outside north fragment',(-4.3481,-.95),(-4.3583,1.28),.14)
wall('I04 West perimeter occlusion',(-4.3406,-2.60),(-4.3481,-.95),.14,col=inferred,
     confidence='inferred plane across scan gap; no window assumed without supporting evidence')
wall('W06 Southwest room back',(-4.3335,-4.1655),(-1.42,-4.1095),-.14)
wall('W07 Lounge back west',(-4.35,4.680),(0.25,4.548),.14)
wall('W08 Lounge back east',(.25,4.239),(2.82,4.271),.14)
wall('W09 Lounge back step',(.25,4.239),(.25,4.548),.14)
wall('W10 Lounge east short return',(2.82,3.50),(2.82,4.271),-.14)
wall('W11 Utility east wall',(1.99,-2.42),(1.99,-.87),-.12,top=2.40)
wall('W12 Utility north return',(.38,-.86),(1.99,-.86),.12,top=2.40)
wall('W13 Entrance east fragment',(.24,-4.97),(.242,-4.15),-.12,top=2.53)
wall('W14 Entrance terminal fragment',(-1.38,-6.46),(.27,-6.46),-.12,top=2.43)
# These closures are explicitly separate from measured architecture.
wall('I01 West room dividing partition',(-4.35,-1.43),(-.95,-1.43),.12,col=inferred,
     confidence='inferred continuation between observed doorway pier and west boundary; heavily occluded')
wall('I02 Lounge west boundary',(-4.35,1.40),(-4.35,4.68),.14,col=inferred,
     confidence='unscanned perimeter continuation; provisional, verify before use')
wall('I03 Utility south boundary',(.38,-2.42),(1.99,-2.42),-.12,top=2.40,col=inferred,
     confidence='inferred from partial utility floor scan')
# Footprint is a union of simple survey rectangles. Unscanned east rooms remain absent.
regions=[(-4.35,2.82,1.28,4.24),(-4.35,.25,4.24,4.61),
         (-4.35,.27,-4.15,1.28),(.27,1.99,-2.42,-.86),(-1.38,.27,-6.46,-4.15)]
xs=sorted(set(v for r in regions for v in r[:2]));ys=sorted(set(v for r in regions for v in r[2:]))
contains=lambda x,y:any(a<x<b and c<y<d for a,b,c,d in regions)
grid_solid('F01 Continuous architectural floor',xs,ys,contains,lambda x,y,k:(x,y,F-.12+k*.12),floors,floormat,
           'scan floor level; footprint regularized across occluded regions; scan truncations are not room boundaries')
grid_solid('C01 Reconstructed ceiling',xs,ys,contains,lambda x,y,k:(x,y,TOP+k*.12),ceilings,ceilmat,
           'scan ceiling plane regularized to 2.68m; footprint follows reconstructed floor')
ceilings.hide_viewport=True;ceilings.hide_render=True
photo=bpy.data.images.load(str(ROOT/'assets/corridor/IMG_5713_reference.jpg'),check_existing=True);photo.pack()
s['Reference photo']=photo.name
s['Scope']='Clean architectural shell. Original scan isolated in 90_REFERENCE_SCAN, hidden from viewport/render. Ceiling separately hidden for overview.'
s['Uncertainty']='Wall thicknesses 0.12-0.14m are assumptions. Amber I* walls are provisional. Unscanned eastern rooms not invented. Floor boundary partly inferred. No survey calibration.'
def camera(name,pos,target,ortho=None):
    o=bpy.data.objects.new(name,bpy.data.cameras.new(name));views.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    if ortho:
        assert 'ORTHO' in [i.identifier for i in o.data.bl_rna.properties['type'].enum_items]
        o.data.type='ORTHO';o.data.ortho_scale=ortho
    o.data.clip_start=.03;return o
overview=camera('Overview - architecture',(11,-15,13),(-.7,-.7,.6),15)
plan=camera('Plan - architecture',(-.6,-.85,18),(-.6,-.85,0),16)
plan.data.clip_start=15.80
interior=camera('Interior - toward lounge',(-.29,-2.5,1.65),(-.25,3.5,1.5));interior.data.lens=22
s.camera=overview
s.render.engine='BLENDER_WORKBENCH'
sh=s.display.shading
for prop,val in [('light','STUDIO'),('color_type','MATERIAL'),('background_type','WORLD')]:
    assert val in [i.identifier for i in sh.bl_rna.properties[prop].enum_items];setattr(sh,prop,val)
if s.world is None:s.world=bpy.data.worlds.new('Architecture background')
s.world.color=(.12,.12,.12)
sh.show_shadows=True;sh.show_cavity=True
s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active
            vals=[i.identifier for i in sp.shading.bl_rna.properties['type'].enum_items]
            if 'SOLID' in vals:sp.shading.type='SOLID'
            sp.shading.color_type='MATERIAL'
            sp.region_3d.view_rotation=overview.rotation_euler.to_quaternion()
            sp.region_3d.view_location=Vector((-.7,-.7,.6));sp.region_3d.view_distance=16
            sp.overlay.show_overlays=False
for o in s.objects:o.select_set(False)
# Check each authored component is a closed quad manifold, and scan is byte-identical.
qa=[]
for o in objects:
    bm=bmesh.new();bm.from_mesh(o.data)
    qa.append({'name':o.name,'vertices':len(bm.verts),'faces':len(bm.faces),
               'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
               'nonquad_faces':sum(len(f.verts)!=4 for f in bm.faces),
               'degenerate_faces':sum(f.calc_area()<1e-10 for f in bm.faces)})
    bm.free()
assert all(x['nonmanifold_edges']==x['nonquad_faces']==x['degenerate_faces']==0 for x in qa)
assert fingerprint(scan.data)==original_hash
report={'scan_hash_original_and_reference':original_hash,'scan_vertices':len(scan.data.vertices),
        'new_meshes':len(objects),'new_vertices':sum(x['vertices'] for x in qa),
        'new_quad_faces':sum(x['faces'] for x in qa),'floor_z_m':F,'ceiling_z_m':TOP,
        'corridor_width_at_y0_m':east(0)-west(0),'checks':qa,
        'note':'Manifold validation is per modular component; separate wall junctions are not a single fused mesh.'}
(ROOT/'renders/architecture_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s.render.filepath=str(ROOT/'renders/corridor_architecture_overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/corridor_architecture.blend'))
bpy.ops.render.render(write_still=True)
s.camera=plan;sh.show_shadows=False;s.render.filepath=str(ROOT/'renders/corridor_architecture_plan.png');bpy.ops.render.render(write_still=True)
sh.show_shadows=True
ceilings.hide_render=False;s.camera=interior;s.render.filepath=str(ROOT/'renders/corridor_architecture_interior.png');bpy.ops.render.render(write_still=True)
print(json.dumps(report))
