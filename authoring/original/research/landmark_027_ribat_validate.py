"""Fresh numerical checks of final authored Ribat scene, not recipe-only assertions."""
import bpy,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/landmarks_0_2_7/ribat';bpy.ops.wm.open_mainfile(filepath=str(ART/'ribat_of_sanhaja.blend'))
obs=list(bpy.data.collections['Ribat_Editables'].objects)
def find(fragment):return next(o for o in obs if o.name=='Ribat_'+fragment)
def bounds(o):
 ps=[o.matrix_world@v.co for v in o.data.vertices];return {'min':[min(v[i] for v in ps) for i in range(3)],'max':[max(v[i] for v in ps) for i in range(3)]}
checks=[]
def seat(label,upper,lower,tol=.01,intent='surface contact'):
 gap=upper-lower;checks.append({'interface':label,'upper_part_bottom':upper,'lower_part_top':lower,'signed_gap':gap,'tolerance':tol,'intent':intent,'passed':abs(gap)<=tol})
floor=bounds(find('CourtyardPaving'));foot=bounds(find('EnclosureFoot_1_0_0'));seat('Footing bottom / court top',foot['min'][2],floor['max'][2],.003)
for tx,ty in [(-5,-5),(5,-5),(-5,5),(5,5)]:
 tag=f'Tower{tx}_{ty}';body=bounds(find(tag+'TaperedBody'));stone=bounds(find(tag+'Base_0_4_0'));seat(tag+' plaster / stone footing',body['min'][2],stone['max'][2],.05,'intentional plaster overlap of upper stone edge')
for side in [-1,1]:
 f=bounds(find('StableFloor'+str(side)));post=bounds(find(f'StablePost{side}_0_{side*3.65}'));beam=bounds(find(f'StableCrossBeam{side}_0'));raft=bounds(find(f'StableRafter{side}_0'))
 seat('Stable post / floor '+str(side),post['min'][2],f['max'][2],.001)
 seat('Stable crossbeam / post '+str(side),beam['min'][2],post['max'][2],.045,'intentional mortised timber seat')
 seat('Stable rafter / beam '+str(side),raft['min'][2],beam['max'][2],.001)
 canopy=bounds(find(f'WovenCanopy{side}_0'));seat('Woven canopy outer edge / rafter '+str(side),canopy['max'][2],raft['max'][2],.003,'edge rests on roof laths')
 checks.append({'interface':'canopy centre / lath '+str(side),'signed_gap':canopy['min'][2]-raft['max'][2],'intent':'thin woven surface tucked beneath roof laths at sag','passed':abs(canopy['min'][2]-raft['max'][2])<.035})
back=bounds(find('RearHallParapetBack'));side=bounds(find('RearHallParapetSide1'));seat('Rear parapet corner end / inside back face',back['min'][1],side['max'][1],.001)
roof=bounds(find('WatchRoof'));pole=bounds(find('FlagPole'));seat('Flag pole / watch roof',pole['min'][2],roof['max'][2],.001)
flag={'position':[0,-4.42,7.1377],'scale':.7,'cloth_top':7.1377+1.339*.7,'pole_top':pole['max'][2],'top_gap':7.1377+1.339*.7-pole['max'][2],'inner_edge_overlap_y':.039*.7-.03}
meshes=[]
for lod in range(3):
 for ob in bpy.data.collections[f'Ribat_LOD{lod}'].objects:
  mesh=ob.data;mesh.calc_loop_triangles();uv=mesh.uv_layers.active
  rows={'LOD':lod,'name':ob.name,'stage':ob.get('garrison_building_first_stage'),'triangles':len(mesh.loop_triangles),'UV_loops':len(uv.data),'finite_vertices':all(math.isfinite(a) for v in mesh.vertices for a in v.co),'finite_UVs':all(math.isfinite(a) for u in uv.data for a in u.uv),'UVs_in_unit_square':all(-1e-6<=a<=1+1e-6 for u in uv.data for a in u.uv),'valid_normals':all(p.normal.length>.99 for p in mesh.polygons),'materials':len({mesh.materials[p.material_index].name for p in mesh.polygons}),'material_slots':len(mesh.materials)};meshes.append(rows)
result={'contacts':checks,'flag_mount':flag,'meshes':meshes,'passed':all(c['passed'] for c in checks) and all(r['finite_vertices'] and r['finite_UVs'] and r['UVs_in_unit_square'] and r['valid_normals'] and r['materials']==1 for r in meshes),'proof':'numerically measured live saved .blend geometry; native render/owner colour runtime remains pending'}
(ART/'live-contact-validation.json').write_text(json.dumps(result,indent=2));print('RIBAT_LIVE_VALIDATION',result['passed']);bpy.ops.wm.quit_blender()

