"""040 explicit per-object composition contract; source-only stamp inspection."""
import json,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research'))
from economy_025_native_stamp import NativeTree
from berber_031_marrakech_overlap import world_box
specs=json.loads((ROOT/'output/berber_update_0_3_1/binding-specs.json').read_text())['specs']
for family in ('keep','marrakech','siege'):
 art=ROOT/'art/building_remix_0_4_0'/family
 recipe=json.loads((art/'recipe.json').read_text());result=[]
 for row in recipe['models']:
  spec=next(s for s in specs if s['family']==family and s['age']==row['age'])
  member=next(v.replace('\\','/')+'.bin' for k,v in spec['stock_stamp_fields'] if 'const_dest' not in v)
  tree=NativeTree(ROOT/'output/shared_stock_cache/buildings_031/stamps'/member)
  visuals=[];retained=[];removed=[]
  marker={'keep':'keep_control','marrakech':'mal_landmark_b_age03','siege':'siege_workshop_control'}[family]
  for obj in tree.objects.values():
   if obj['type']!='VisualStampBlueprint':continue
   model=tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/')
   tf=struct.unpack('<10f',bytes.fromhex(tree.field(obj,obj['fields']['m_transform'])['raw']))
   principal=marker in model
   flag='/flag' in model or 'flag_' in model
   r={'id':str(obj['id']),'model':model,'transform':tf,'action':'replace_principal' if principal else 'retain_flag' if flag else 'remove_conflicting_visual'}
   if principal:r['root_frame_bounds_m']=world_box(row['bounds_m'],tf)
   visuals.append(r)
   if principal or flag:retained.append(r)
   else:removed.append(r)
  principal=[v for v in retained if v['action']=='replace_principal'];assert len(principal)==1,(family,len(principal))
  result.append({'name':row['name'],'actor':spec['actor'],'stock_tier':spec['source_tier'],'stock_stamp':member,'principal':principal[0],'retained_visual_allowlist':retained,'removed_visuals':removed,'functional_policy':'Keep every nonvisual object, marker, transform, stage and healthy/damage/construction lifecycle unchanged; preserve player flag.','no_new_shells':True,'stamp_contacts':'one retained connected native core; zero supplementary attached architecture; inter-building shell overlaps eliminated by excluding every other architectural visual','contact_audit':row['source_checks']})
 (art/'composition-contract.json').write_text(json.dumps(result,indent=2)+'\n')
 print('COMPOSITION',family,[(r['name'],len(r['retained_visual_allowlist']),len(r['removed_visuals'])) for r in result])
