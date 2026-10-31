"""Repair inspected wall/tower taper gaps in saved source; no new assemblies."""
import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/keep';O=R/'output/buildings_batch/keep'
try:
 for age in [3,4]:
    bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Keep_Age{age}.blend'))
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
      for ob in bpy.context.scene.objects:
        ax=1 if ob.name.startswith('curtain_wall') else 0 if ob.name in ['front_gate_wall','rear_wall'] else None
        if ax is not None:
          for v in ob.data.vertices:
            if abs(v.co[ax])>1.5:v.co[ax]=1.8 if v.co[ax]>0 else -1.8
          ob.data.update()
      H=4.35 if age==3 else 4.60;removed=[]
      for ob in list(bpy.context.scene.objects):
        if ob.name.startswith('tower_merlon') and abs(abs(ob.location.x)-2.65)<.01 and abs(abs(ob.location.y)-1.87)<.01:
          removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
        elif ob.name.startswith('tower_parapet'):
          ax=0 if abs(abs(ob.location.x)-1.87)<.01 else 1 if abs(abs(ob.location.y)-1.87)<.01 else None
          if ax is not None:
            bpy.ops.mesh.primitive_cube_add(size=1,location=ob.location);c=bpy.context.object;c.dimensions=(.30,.92,.6) if ax==0 else (.92,.30,.6);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.context.view_layer.objects.active=ob;m=ob.modifiers.new('walk_access','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
      mp=A/f'age{age}_construction.json';d=json.loads(mp.read_text());d['parts']=[p for p in d['parts'] if p['object'] not in removed];mp.write_text(json.dumps(d,indent=2))
      bpy.ops.object.select_all(action='DESELECT');objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
      for o in objects:o.hide_viewport=False;o.select_set(True)
      bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_Keep_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=True,path_mode='COPY',embed_textures=True)
      bpy.ops.wm.save_as_mainfile(filepath=str(A/f'Berber_Keep_Age{age}.blend'))
      scene=bpy.context.scene;cam=scene.camera
      for key,loc in [('preview',(12,-16,13)),('front',(0,-15,2.3)),('back',(0,15,2.3)),('left',(-15,0,2.3)),('right',(15,0,2.3)),('top',(0,0,16)),('bottom',(0,0,-15))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,2.2 if key=='preview' else 2.3))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=scene.render.resolution_y=768 if key=='preview' else 400;scene.render.filepath=str(O/f'age{age}_{key}.png');bpy.ops.render.render(write_still=True)
 (O/'JOIN_REPAIR_COMPLETE.json').write_text(json.dumps({'wall_lengths':3.6,'reason':'inspected taper seam at wall/tower interface','ages':[3,4]}))
except Exception:(O/'JOIN_REPAIR_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
