"""Integrated alAttarin scholarly court details on actual native donor anchors."""
import bpy,json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research'))
from berber_040_university_geometry import Builder,review,export
ART=ROOT/'art/building_remix_0_4_0/university';OUT=ROOT/'art/building_remix_0_4_0/university_details'
bpy.ops.wm.open_mainfile(filepath=str(ART/'Berber_University_Age4_040.blend'));bpy.context.preferences.filepaths.save_version=0
# Native root preserved. Replace only this recipe's prior collection on rerun.
for col in list(bpy.data.collections):
 if col.name.startswith('university_details_lod0'):
  for ob in list(col.objects):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.collections.remove(col)
# Only bounded new detail collection is exported.
b=Builder('university_details_lod0',OUT)
b.box('court_paving_seated_z0',(1.1,-2.7,.025),(6.15,5.9,.05),1,0)
# Restrained tile perimeter, leaving a1.3m clear approach to native portal.
for name,ctr,size in [('west',(-1.88,-2.7,.059),(.13,5.9,.018)),('east',(4.08,-2.7,.059),(.13,5.9,.018)),('south',(1.1,-5.58,.059),(6.1,.13,.018))]:b.box('court_zellij_'+name,ctr,size,3,60)
# Basin has outer side, thick rim, inner side, inset floor: real recessed cavity.
b.rings('octagonal_recessed_fountain',(0,-2.9),[(.94,.05),(.94,.37),(.73,.37),(.73,.16),(.01,.16)],8,0,60,True)
b.rings('inset_water_tile_bed',(0,-2.9),[(.705,.17),(.705,.185)],8,3,80,True)
b.rings('central_fountain_nozzle',(0,-2.9),[(.11,.185),(.11,.39),(.07,.43)],8,0,80,True)
# Doorway source front face y=.45, center x1.995; narrow surrounds seat -.02m.
cx=1.995;fy=.43
for sign in (-1,1):b.box('cedar_portal_jamb_'+str(sign),(cx+sign*1.44,fy,1.68),(.14,.12,3.28),2,60)
b.box('cedar_portal_lintel',(cx,fy,3.42),(3.02,.14,.22),2,60)
# Horseshoe/pointed band, open center, one continuous closed ring mesh.
vs=[];n=20
for depth in (fy-.09,fy+.05):
 for radius in (1.40,1.28):
  for i in range(n+1):
   theta=math.pi*i/n;vs.append((cx+radius*math.cos(theta),depth,2.02+radius*math.sin(theta)))
fs=[];stride=n+1
for i in range(n):
 fs.extend([(i,i+1,stride+i+1,stride+i),(2*stride+i,3*stride+i,3*stride+i+1,2*stride+i+1),(i,2*stride+i,2*stride+i+1,i+1),(stride+i,stride+i+1,3*stride+i+1,3*stride+i)])
fs.extend([(0,stride,3*stride,2*stride),(n,2*stride+n,3*stride+n,stride+n)])
b.mesh('continuous_cedar_arch_surround',vs,fs,2,60)
for sign in (-1,1):b.box('zellij_portal_dado_'+str(sign),(cx+sign*1.62,fy+.015,.72),(.18,.12,1.35),3,60)
# Dedicated native owner flag pole; cloth supplied by integration, not baked.
pole=(4.30,-1.9);b.rings('University_native_owner_flag_pole',pole,[(.065,.05),(.065,5.9)],8,2,80,True)
flag={'location':[pole[0],pole[1]+.03,4.55],'rotation':[0,0,0],'scale':[1,1,1]};(ART/'flag-transform.json').write_text(json.dumps(flag,indent=2))
contacts={'fountain_bottom_paving_top_gap_m':0,'basin_inner_floor_z':.16,'basin_rim_z':.37,'basin_recess_depth_m':.21,'water_bed_floor_overlap_m':-.01,'portal_source_front_face_y':.45,'surround_back_face_y':.49,'intentional_portal_overlap_m':-.04,'court_clear_entrance_approach':'x[.75,3.25],y[-1.2,.4] clear; fountain footprint endsy-1.96','pole_bottom_paving_top_gap_m':0,'flag_top_z':5.8889,'pole_top_z':5.9}
# Image-node normal replacement preview only; integration cooks native packed maps.
for mat in bpy.data.materials:
 if (' '+chr(183)+' extra '+chr(183)+' ') in mat.name and mat.node_tree:
  for nd in mat.node_tree.nodes:
   if nd.type=='TEX_IMAGE' and ('normalMap2' in nd.name or 'normalMap3' in nd.name):nd.image=bpy.data.images.load(str(ART/'normal_tiles.png'),check_existing=True)
manifest=export(b,OUT)
visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
bounds=review(ART,'university_revised',visible)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Berber_University_Age4_040.blend'))
report={'schema':'berber.university-court/v040','status':'source-exported','new_geometry':True,'building_export':manifest,'collection':'university_details_lod0','source_bounds':[[min(v[i] for o in b.parts for v in [o.matrix_world@p.co for p in o.data.vertices]) for i in range(3)],[max(v[i] for o in b.parts for v in [o.matrix_world@p.co for p in o.data.vertices]) for i in range(3)]],'parts':b.report(),'contacts':contacts,'flag_transform':flag,'native_runtime':'unverified'}
(OUT/'source-validation.json').write_text(json.dumps(report,indent=2,default=str));print('UNIVERSITY_COURT_READY',len(b.parts),flush=True)
