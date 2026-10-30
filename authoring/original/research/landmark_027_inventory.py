import os,sys,subprocess,json,sqlite3,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'output/berber_update_0_2_7/inventory';O.mkdir(parents=True,exist_ok=True)
X=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path[:0]=[str(X),str(R/'research')]
from garrison_shared import rgd
from economy_025_native_stamp import NativeTree
A=X/'bin/sga-archiver.exe';C=X/'bin/core/garrison-core.exe';I=Path('C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3');B=R/'output/berber_update_0_2_6/package/Berber_future_kingdom.sga';D=sqlite3.connect('file:'+str(I)+'?mode=ro',uri=True)
def run(args):
 if str(args[1])=='decode-rgd' and Path(args[-1]).exists():return ''
 if 'decode-static' in list(map(str,args)):
  logical=str(args[list(args).index('--logical-path')+1]);target=Path(args[list(args).index('--output-root')+1])
  for prior in target.glob('*/decoded-static.json'):
   if json.loads(prior.read_text())['request']['logical_path']==logical:return 'Reused current decoded cache; delete cache folder to regenerate.'
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8');assert p.returncode==0,p.stderr;return p.stdout
official=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
offmembers={m['path'] for m in json.loads(run([A,'list',official]))['members']}
assert hashlib.sha256(B.read_bytes()).hexdigest()=='cf9c73bdc0a64c655525f943f7e7b4ddfd1338124216ec7bf75eb331614f8123'
members={m['path'] for m in json.loads(run([A,'list',B]))['members']}
def fetch(m):
 p=O/'extracted'/m;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  arc=B if m in members else official if m in offmembers else (D.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(m,)).fetchone() or [str(official.with_name('Data.sga'))])[0]
  run([A,'extract-member',arc,m,p])
 return p
report=[]
for name,leaf in [('ribat','ribat_of_sanhaja/building_landmark_age1_landmarka_mal'),('funduq','funduq/building_landmark_age1_landmarkb_mal')]:
 m='attrib/ebps/races/malian/buildings/landmarks/'+leaf+'.rgd';p=fetch(m);doc=rgd.read(p.read_bytes());rows=[(k,n.value) for k,n in rgd.flatten(doc.nodes) if isinstance(n.value,(str,float,int))];run([A,'decode-rgd',p,p.with_suffix('.xml')]);r={'building':name,'actor':m,'actor_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actor_fields':rows,'tiers':[]}
 for k,v in rows:
  if k.endswith('/$PBGMAP') and v=='attachments\\attachment_lists':
   leafname=rgd.find(doc.nodes,k.removesuffix('$PBGMAP')+'$PBGNAME').value
   if not leafname:continue
   candidates=[m for m in members|offmembers if m.startswith('attrib/attachments/attachment_lists/') and m.endswith('/'+leafname+'.rgd')];assert len(candidates)==1,(leafname,candidates)
   tm=candidates[0];tp=fetch(tm);td=rgd.read(tp.read_bytes());tr=[(k,n.value) for k,n in rgd.flatten(td.nodes) if isinstance(n.value,(str,float,int))];tier={'member':tm,'fields':tr,'stamps':[]};run([A,'decode-rgd',tp,tp.with_suffix('.xml')])
   for kk,vv in tr:
    if isinstance(vv,str) and vv.startswith('art\\stamps\\'):
     sm=vv.replace('\\','/')+'.bin';sp=fetch(sm);tree=NativeTree(sp);tier['stamps'].append({'member':sm,'sha256':hashlib.sha256(sp.read_bytes()).hexdigest(),'objects':[tree.describe(o) for o in tree.objects.values()]})
   r['tiers'].append(tier)
 report.append(r)
(O/'manifest.json').write_text(json.dumps(report,indent=2));print([(r['building'],[(t['member'],[s['member'] for s in t['stamps']]) for t in r['tiers']]) for r in report])

principals=[]
for r in report:
 for tier in r['tiers']:
  for stamp in tier['stamps']:
   for obj in stamp['objects']:
    if obj['type']!='VisualStampBlueprint':continue
    model=obj['fields']['m_blueprint']['text'].replace(chr(92),'/')
    if '/landmark_2b/' in model or '/arsenal/abb_arsenal_control_age03/' in model:
     if model in principals:continue
     principals.append(model)
     for suffix in ['.rgo','.rgm','.rrgeom']:fetch(model+suffix)
     result=run([C,'convert','decode-static','--logical-path',model+'.rgm','--config',I.with_name('game-assets.local.json'),'--index',I,'--output-root',O/'decoded'])
     (O/(r['building']+'-decode.log')).write_text(result)

for model in ['art/civilizations/common/props/moving_flag/moving_flag','art/civilizations/common/flags/flag_rectangle/flag_rectangle','art/civilizations/common/banners/banner_stables/banner_stables']:
 for suffix in ['.rgo','.rgm','.rrgeom']:fetch(model+suffix)
 run([C,'convert','decode-static','--logical-path',model+'.rgm','--config',I.with_name('game-assets.local.json'),'--index',I,'--output-root',O/'decoded'])

from garrison_shared import relic_chunky as rc
import struct
compact={'baseline_sha256':hashlib.sha256(B.read_bytes()).hexdigest(),'regeneration':'Run research/landmark_027_inventory.py with Blender Python; selective official archive extraction and installed Garrison decoder only. No gameplay or cook mutation. All inventory/extracted and inventory/decoded caches may be removed after dependent consumers finish.','buildings':[],'models':[],'integration_allowlist_existing':[r['actor'] for r in report],'pitfalls':['Footprint fields 6x6 and8x8 are native gameplay grid measurements, not an assumption of physical meters.','Funduq animator125% affects its new stamps and flags; use source dimensions80% of intended visible result.','Ribat principal stamp zoffset2.62378 belongs to original donor. New ground-authored geometry must use new zero-contact stamp rather than blindly copying donor offset.','Ribat outskirts native tier could leave stock debris, tents and props; explicitly review and omit obsolete structures through private clone.','Fundug native tier has healthy, rubble and external scaffolding refs repeated across template variants. All intended categories must be rebound.','Raw decoded triangle totals include construction and damage fragments plus LODs; do not claim completed LOD0 without selector evaluation.']}
for r in report:
 a={'name':r['building'],'actor':r['actor'],'actor_sha256':r['actor_sha256'],'footprint':dict((k,v) for k,v in r['actor_fields'] if 'site_ext/footprint_scale/' in k),'animator_scale':next(v for k,v in r['actor_fields'] if k.endswith('/animator_scale')),'tiers':[]}
 for t in r['tiers']:
  a['tiers'].append({'member':t['member'],'fields':t['fields'],'stamps':[{'member':ss['member'],'sha256':ss['sha256'],'components':[{'model':o['fields']['m_blueprint']['text'],'transform_native_quaternion_position_scale':list(struct.unpack('<10f',bytes.fromhex(o['fields']['m_transform']['raw']))),'selectable':o['fields']['m_isSelectable'],'pathfinding':o['fields']['m_addToPathfinding']} for o in ss['objects'] if o['type']=='VisualStampBlueprint']} for ss in t['stamps']]})
 compact['buildings'].append(a)
for p in (O/'decoded').glob('*/decoded-static.json'):
 d=json.loads(p.read_text());points=[v for g in d['geometry']['groups'] for v in g['positions']];model=d['request']['logical_path'];rgo=O/'extracted'/Path(model).with_suffix('.rgo');chunks=list(rc.walk(rc.load(rgo).roots))
 compact['models'].append({'path':model,'source_rgm_sha256':d['resources']['model']['sha256'],'bounds_all_decoded_states':[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)],'triangles_all_states_lods':sum(g['triangle_count'] for g in d['geometry']['groups']),'completed_LOD0_triangle_budget':'not isolated; source all-state totals are conservative bounds only','behaviour_names':[c.name.decode('utf8').rstrip(chr(0)) for c in chunks if c.tag==b'BVBP'],'action_names':[c.name.decode('utf8').rstrip(chr(0)) for c in chunks if c.tag==b'ACTN'],'native_graph_sha256':hashlib.sha256(rgo.read_bytes()).hexdigest(),'native_team_materials':[{'name':m['name'],'shader':m['class'],'team_textures':[t for t in m['textures'] if 'team_color' in (t.get('texture_name') or '')],'wave_parameters':[x for x in m['parameters'] if any(k in x['name'] for k in ['wavePrimary','windPrimary'])]} for m in d['material']['materials']]})
(O/'compact-manifest.json').write_text(json.dumps(compact,indent=2));print('Compact summary saved',len(compact['models']),'models')
