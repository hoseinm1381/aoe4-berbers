"""Original Koutoubia blockout; no old blend or donor geometry."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research'))
from berber_040_university_geometry import Builder,review
ART=ROOT/'art/building_remix_0_4_0/wonder';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
b=Builder('Koutoubia_original_lod0',ART)
b.box('site_plinth',(0,0,.06),(14.2,14,.12),0,0)
b.box('sanctuary_hypostyle_mass',(1,2.8,1.41),(10.8,7,2.58),1,40)
b.box('court_paving',(.2,-3.45,.14),(11.6,5.5,.04),1,0)
b.box('minaret_square_shaft',(-5.6,4.6,5.81),(2.4,2.4,11.38),0,40)
b.box('minaret_crown',(-5.6,4.6,11.7),(2.55,2.55,.4),0,60)
b.box('minaret_lantern',(-5.6,4.6,12.7),(1.35,1.35,1.6),0,80)
b.hip('lantern_green_cap',-5.6,4.6,1.55,1.55,13.5,.42,4,80)
for i in range(5):
 x=-3.32+i*2.16;y=2.8;w=2.30;d=7.18;z=2.82;h=.45;a=w/2;bb=d/2;rr=bb-a
 vs=[(x-a,y-bb,z),(x+a,y-bb,z),(x+a,y+bb,z),(x-a,y+bb,z),(x,y-rr,z+h),(x,y+rr,z+h),(x-a,y-bb,z-.12),(x+a,y-bb,z-.12),(x+a,y+bb,z-.12),(x-a,y+bb,z-.12)]
 b.mesh('hypostyle_green_roof_bay_'+str(i),vs,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(6,7,1,0),(7,8,2,1),(8,9,3,2),(9,6,0,3),(9,8,7,6)],4,80)
bounds=review(ART,'koutoubia_blockout',b.parts)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Koutoubia_blockout.blend'))
(ART/'blockout.json').write_text(json.dumps({'bounds':bounds,'parts':b.report(),'source':'new original geometry','native_runtime':'unverified'},indent=2));print('KOUTOUBIA_BLOCKOUT_DONE')
