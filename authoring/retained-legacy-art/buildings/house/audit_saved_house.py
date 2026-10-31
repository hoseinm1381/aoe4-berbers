"""Measure saved source interfaces; verify packed maps and atlas mask."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'art/buildings/house';OUT=ROOT/'output/buildings_batch/house'
report=[]
try:
    for age in range(1,5):
        bpy.ops.wm.open_mainfile(filepath=str(ART/f'Berber_House_Age{age}.blend'))
        with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
            for mapname in ('albedo','pattern'):
                im=bpy.data.images.get('House_'+mapname)
                if im is None:im=bpy.data.images.load(str(ART/(mapname+'.png')));im.name='House_'+mapname
                im.use_fake_user=True;im.pack()
            def bounds(name):
                ob=bpy.data.objects[name];points=[ob.matrix_world@Vector(v) for v in ob.bound_box]
                return [min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]
            bpy.context.view_layer.update();contacts=[]
            for child,parent,axis,cs,ps,expected in [('west_roof_deck','west_room',2,0,1,0),('east_roof_deck','east_room',2,0,1,0),('west_room','courtyard_earthen_floor',2,0,1,-.01),('east_room','courtyard_earthen_floor',2,0,1,-.01),('entrance_step','stone_foundation',1,1,0,0)]:
                gap=bounds(child)[cs][axis]-bounds(parent)[ps][axis]
                contacts.append({'child':child,'parent':parent,'axis':axis,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})
            masks={m.name:m.get('ber_owner_mask') for m in bpy.data.materials if m.users};packed={im.name:bool(im.packed_file) for im in bpy.data.images if im.name.startswith('House_')}
            data={'age':age,'contacts':contacts,'material_owner_annotations':masks,'packed_maps':packed,'native_player_colour':'pending'}
            parts=[{'object':o.name,'first_stage':o.get('garrison_building_first_stage'),'material':o.get('ber_material_role'),'owner_mask':o.data.materials[0].get('ber_owner_mask')} for o in bpy.data.objects if o.type=='MESH']
            manifest={'schema':'berber-building-source-stage/v1','age':age,'parts':parts,'stages':[0,20,40,60,80,100],'assignment':'first visible construction percentage; cumulative','game_binding_status':'not exported through Garrison building recipe'}
            (ART/f'age{age}_construction.json').write_text(json.dumps(manifest,indent=2))
            assert all(c['pass'] for c in contacts);assert all(packed.values());assert 1 in masks.values() and 0 in masks.values()
            assert {'House_albedo','House_pattern'}<=set(packed)
            bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_House_Age{age}.blend'))
            report.append(data)
    (OUT/'saved_source_audit.json').write_text(json.dumps(report,indent=2));print('SAVED_SOURCE_AUDIT_PASS',flush=True)
finally:bpy.ops.wm.quit_blender()
