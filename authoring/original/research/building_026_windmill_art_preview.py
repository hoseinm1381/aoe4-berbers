"""Isolated material repair previews from existing native-source Blends."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/windmill';OUT=ROOT/'output/berber_update_0_2_6/authors/windmill';CAP=OUT/'previews';r=json.loads((ART/'recipe.json').read_text())
def meshhash():
 return hashlib.sha256(json.dumps({o.name:{'v':[tuple(v.co) for v in o.data.vertices],'p':[tuple(p.vertices) for p in o.data.polygons],'uv':{u.name:[tuple(x.uv) for x in u.data] for u in o.data.uv_layers},'matrix':[list(row) for row in o.matrix_world]} for o in bpy.context.scene.objects if o.type=='MESH'},sort_keys=True).encode()).hexdigest()
def setup():
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Repair Evidence World');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.15,.15,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.view_settings.view_transform='AgX'
 for name,loc,energy in [('Repair Key',(7,-10,14),2300),('Repair Fill',(-10,3,12),1900)]:
  light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.size=9;obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,4))-obj.location).to_track_quat('-Z','Y').to_euler()
 cam=bpy.data.cameras.new('Repair Evidence Camera');obj=bpy.data.objects.new('Repair Evidence Camera',cam);scene.collection.objects.link(obj);scene.camera=obj;cam.type='ORTHO';cam.ortho_scale=12
def capture(label,direction=(1,-1,.9),solid=False):
 s=bpy.context.scene;center=Vector((0,0,4.1));cam=s.camera;cam.location=center+Vector(direction).normalized()*30;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(CAP/f'age1_{label}.png');restore=[]
 if solid:
  clay=bpy.data.materials.get('Repair Evidence Clay') or bpy.data.materials.new('Repair Evidence Clay');clay.diffuse_color=(.48,.47,.44,1);clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.48,.47,.44,1)
  for o in bpy.context.scene.objects:
   if o.type=='MESH':restore.append((o,list(o.data.materials)));o.data.materials.clear();o.data.materials.append(clay)
 bpy.ops.render.render(write_still=True)
 for o,mats in restore:
  o.data.materials.clear()
  for mat in mats:o.data.materials.append(mat)
def team(colour=None):
 for mat in bpy.data.materials:
  if mat.use_nodes and (control:=mat.node_tree.nodes.get('GARRISON Material Controls')) and control.inputs.get('Team Colour'):
   if colour:control.inputs['Team Colour'].default_value=colour
   control.inputs['Team Colour Strength'].default_value=1 if colour else 0
def main():
 bpy.ops.wm.open_mainfile(filepath=str(ART/'UNTOUCHED_Common_Windmill_Age1.blend'));setup();team();capture('before')
 path=ART/'Berber_Windmill_Age1_0_2_6.blend';bpy.ops.wm.open_mainfile(filepath=str(path));before=meshhash();spec=next(m for m in r['materials'] if m['name']=='windmill')
 for obj in bpy.context.scene.objects:
  if obj.type!='MESH' or obj.get('garrison_material_slot')!='windmill':continue
  for mat in obj.data.materials:
   for edit in spec['textures']:
    if edit['slot'] not in ['albedoTex2','albedoTex3','albedoTex4']:continue
    node=mat.node_tree.nodes.get('Essence · '+edit['slot']);assert node;im=bpy.data.images.load(edit['image'],check_existing=False);im.colorspace_settings.name='sRGB';node.image=im
   for old,new in [('normalMap2','normalMap6'),('normalMap3','normalMap6'),('metalTex2','metalTex6'),('metalTex3','metalTex6')]:
    a=mat.node_tree.nodes.get('Essence · '+old);b=mat.node_tree.nodes.get('Essence · '+new);assert a and b,(old,new);a.image=b.image
   mat['berber_art_repair']='Earthen plaster housing and cap; native wall UV diamond band; stock plaster PBR on housing layers2/3.'
 assert meshhash()==before;setup();team();capture('after')
 for name,d in [('front',(0,-1,0)),('back',(0,1,0)),('left',(-1,0,0)),('right',(1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:capture('solid_'+name,d,True)
 team((.02,.15,.8,1));capture('team_blue');team((.8,.025,.025,1));capture('team_red');team();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path));assert meshhash()==before
 validation=json.loads((OUT/'source-validation.json').read_text());validation['ages'][0]['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();validation['art_repair']='strong plaster housing with native wall UV geometric band; no additional geometry changes';validation['art_repair_geometry_hash']=before;(OUT/'source-validation.json').write_text(json.dumps(validation,indent=2)+'\n');print('WINDMILL_REPAIR_PREVIEWS_READY',flush=True)
if __name__=='__main__':main()
