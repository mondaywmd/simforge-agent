"""Organize the live capture-matched scene without changing object data."""
import bpy, re, json, datetime, hashlib, os
from pathlib import Path
R=Path(os.environ.get('SIMFORGE_PROJECT_ROOT', Path(bpy.data.filepath).parent.parent))
s=bpy.context.scene
assert Path(bpy.data.filepath).name=='corridor_capture_matched.blend'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=R/'blender/backups'/('capture_before_organization_'+stamp+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(backup),copy=True)
objects=list(s.objects)
old_collections=list(bpy.data.collections)
def snapshot(o):
 return {'matrix':[list(row) for row in o.matrix_world], 'data':o.data.as_pointer() if o.data else None,
 'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],
 'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,
 'hide_set':o.hide_get(),'visible':o.visible_get()}
before={o.name:snapshot(o) for o in objects}
source={o.name:[c.name for c in o.users_collection] for o in objects}
ref=bpy.data.collections.get('90_REFERENCE_SCAN - original, hidden')
roots={}
def coll(path):
 parent=s.collection
 for part in path.split('/'):
  key=(parent.name,part)
  if key not in roots:
   c=bpy.data.collections.new(part);parent.children.link(c);roots[key]=c
  parent=roots[key]
 return parent
A='01 建筑 Architecture';D='02 门 Doors';F='03 家具 Furniture';P='04 装饰与日用品 Decor';B='05 浴室 Bathroom';E='06 卧室 Bedroom';L='07 灯具与照明 Lighting';C='08 相机 Cameras'
rules=[]
def rule(path,*prefixes):rules.append((path,tuple(x.lower() for x in prefixes)))
rule(A+'/墙体 Walls','W0','W1')
rule(A+'/补全隔墙 Inferred partitions','I0')
rule(A+'/地面 Floor','F01','Corridor nonrepeating','Floor plank')
rule(A+'/天花与梁 Ceiling and beams','C01','B01','Corridor captured ceiling','Living ceiling cove','Living perimeter lowered')
rule(A+'/踢脚线 Skirting','Corridor skirting','Living skirting')
rule(D+'/门框 Door frames','Door casing')
rule(D+'/装饰平开门 Decorated door','Closed white','Decorated door','Side door handle','Side door lever')
rule(D+'/玻璃折叠门 Folding door','Utility folding','Utility inset')
rule(F+'/沙发 Sofa','Sofa back','Sofa cushion','Sofa rounded','Sofa seat','Sofa short','Sofa timber','Loose sofa','Blue throw')
rule(F+'/边桌 Side table','Sofa side table','Side table')
rule(F+'/茶几 Coffee table','Coffee table','Oak coffee')
rule(F+'/储物架 Storage shelf/架体与照片 Shelf and photo panels','Storage shelf','Photo referenced shelf')
rule(F+'/储物架 Storage shelf/架上物品 Shelf contents','Folded shelf','Books on shelf','Blue storage box','Shelf orange','Pumpkin stem')
rule(F+'/鞋柜 Shoe cabinet','Tall oak','Shoe cabinet','Cabinet vertical')
rule(F+'/电视柜 Media cabinet','Media cabinet','Media cubby','Media open','Media console','Console photo','Console picture')
rule(F+'/电视 Television','Television','TV mounting','TV remote','Remote button')
rule(F+'/地毯 Rug','Living woven','Woven rug','Rug fringe')
rule(F+'/落地椅 Floor chair','Photo matched floor chair','Floor chair','Tablet','Leaning picture')
rule(F+'/餐桌 Dining table','Dining table','Dining magazines')
rule(F+'/餐椅与长凳 Dining seating','Dining chair','Dining bench','Dining wall bench','Bent plywood','Chair back upright')
rule(F+'/书桌与电脑 Work desk','Living work desk','Desk leg','Desktop monitor','Monitor','Keyboard')
rule(F+'/办公椅 Office chair','Desk chair','Office chair')
rule(F+'/衣帽架 Coat stand','Coat stand','Structured hanging','Tote shoulder','Cream bucket','Dark bucket','Gray cap','Green tote')
rule(F+'/空调 Air conditioner','Split air','AC outlet')
rule(F+'/窗帘 Living curtains','Curtain vertical fold')
rule(P+'/墙面画作 Wall art/西墙 West wall','West wall original')
rule(P+'/墙面画作 Wall art/东墙 East wall','East wall original')
rule(P+'/墙面画作 Wall art/餐厅 Dining','Dining animal')
rule(P+'/挂钟 Wall clock','Wall clock','Clock')
rule(P+'/白板 Whiteboard','Wall whiteboard','Wall marker','Whiteboard')
rule(P+'/通风口 Vent','Vent cover','Ventilation')
rule(P+'/健身器材 Exercise/门上单杠 Pull-up bar','Pull up','Orange grip','Gym suspension','Gym toy')
rule(P+'/健身器材 Exercise/哑铃 Kettlebell and dumbbells','Gray kettlebell','Kettlebell','Pink dumbbell')
rule(P+'/鞋子 Shoes','Shoes by','Shoe contrast','Shoe dark','Shoe lace')
rule(P+'/扫地机器人 Robot vacuum','Robot vacuum')
rule(P+'/垃圾桶 Waste basket','Waste basket')
rule(B+'/墙地砖 Tiles','Bathroom tiled','Bathroom floor grout','Bathroom horizontal','Bathroom vertical')
rule(B+'/洗手台 Vanity','Bathroom vanity','Vanity','Basin','Mixer tap')
rule(B+'/镜柜 Mirror cabinet','Bathroom mirror')
rule(B+'/马桶 Toilet','Toilet')
rule(B+'/浴帘 Shower curtain','Shower curtain','Curtain horizontal check','Curtain vertical check')
rule(B+'/脚凳 Step stool','Bathroom step','Stool anti')
rule(B+'/地垫 Bathmat','Bathmat')
rule(B+'/洗浴用品 Toiletries','Toiletry','Bottle cap')
rule(E+'/床与床品 Bed','Southwest bed','Bedroom blanket','Bedroom pillow')
rule(E+'/上下铺 Bunk bed','Bunk','Pink bunk')
rule(E+'/学习桌 Study desk','Bedroom desk','Bedroom study')
rule(E+'/儿童桌椅 Child table and chair','Child')
rule(E+'/窗与窗帘 Windows and curtains','Bedroom window','Blue bedroom curtain')
rule(L+'/卧室吊扇灯 Bedroom fan light','Bedroom ceiling fan','Bedroom fan light')
rule(L+'/走廊灯具 Hall fixtures','Photo matched hall','Luminaire casing')
rule(L+'/客厅灯具 Living fixtures','Living recessed')
unmatched=[];assigned={}
for o in objects:
 if ref and o.name in ref.objects:continue
 if o.type=='CAMERA':path=C
 elif o.type=='LIGHT':path=L+'/光源 Light sources'
 else:
  path=next((path for path,prefixes in rules if o.name.lower().startswith(prefixes)),None)
  if path is None:unmatched.append(o.name);continue
 assigned[o.name]=path
assert not unmatched,unmatched
for o in objects:
 if o.name not in assigned:continue
 target=coll(assigned[o.name]);target.objects.link(o)
 for c in list(o.users_collection):
  if c!=target:c.objects.unlink(o)
 o.hide_set(before[o.name]['hide_set'])
if ref:ref.name='90 参考扫描 Reference scan - hidden'
for c in old_collections:
 if c!=ref and not c.objects and not c.children:
  bpy.data.collections.remove(c)
bpy.context.view_layer.update()
after={o.name:snapshot(o) for o in objects}
differences={n:{k:(before[n][k],after[n][k]) for k in before[n] if before[n][k]!=after[n][k]} for n in before if before[n]!=after[n]}
assert not differences,differences
assert len(s.objects)==len(objects)
# Collapse all details, then expand only the scene and category level.
for area in bpy.context.screen.areas:
 if area.type=='OUTLINER':
  with bpy.context.temp_override(area=area,region=next(r for r in area.regions if r.type=='WINDOW')):
   for _ in range(8):bpy.ops.outliner.show_one_level(open=False)
   bpy.ops.outliner.show_one_level(open=True)
report={'backup':str(backup),'object_count':len(objects),'unchanged_object_state':not differences,'collections':{c.name:len(c.objects) for c in bpy.data.collections},'assignment':assigned}
(R/'renders/outliner_organization_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/corridor_capture_matched.blend'))
print(json.dumps({'objects':len(objects),'collections':len(bpy.data.collections),'unchanged':not differences,'backup':str(backup)},ensure_ascii=False))
