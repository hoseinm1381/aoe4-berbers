"""Task-owned Blender snapshot matching the house's requested 0.8 visual ratio."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'art/building_remix_0_2_6/house';OUT.mkdir(parents=True,exist_ok=True)
rows=[]
def dimensions(objects):
 points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
 return [max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
for age in range(1,5):
 source=ROOT/f'art/house_remix_0_2_4/Berber_House_Age{age}_0_2_4.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];before=dimensions(objects)
 for o in objects:o.location*=.8;o.scale*=.8
 bpy.context.view_layer.update();after=dimensions(objects);assert all(abs(b*.8-a)<1e-5 for b,a in zip(before,after))
 target=OUT/f'Berber_House_Age{age}_0_2_6.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target))
 rows.append({'age':age,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'before_dimensions':before,'after_dimensions':after,'ratio':.8})
(OUT/'resize-validation.json').write_text(json.dumps({'status':'passed','ages':rows,'native_stamp_scale':1.104,'native_previous_scale':1.38,'gameplay_footprint':'unchanged'},indent=2))
print('HOUSE_EDITABLE_SOURCES_SCALED_80_PERCENT')
