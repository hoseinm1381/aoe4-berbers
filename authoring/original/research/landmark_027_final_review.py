"""Independent final candidate comparison, run by fresh package reviewer."""
import json,hashlib,sys,os,subprocess,copy,re,zlib,sqlite3
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'output/berber_update_0_2_7'; I=O/'integration'; W=I/'independent-final-review'
E=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path[:0]=[str(E),str(R/'research')]
from garrison_shared import rgd,relic_chunky as rc
from landmark_027_export_codec import visibility_evidence
A=E/'bin/sga-archiver.exe'
def j(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(*args):return subprocess.run([str(A),*map(str,args)],check=True,capture_output=True,text=True).stdout
def sem(nodes):return [(n.key,n.hash,n.kind,sem(n.value) if isinstance(n.value,list) else n.value) for n in nodes]
W.mkdir(parents=True,exist_ok=True)
B=R/'output/berber_update_0_2_6/package/Berber_future_kingdom.sga'; C=I/'candidate/Berber_future_kingdom.sga'
lists={}
for k,p in [('baseline',B),('candidate',C)]:
 lists[k]=jstr=json.loads(run('list',p,'--verify'));assert jstr['archive']['verification']['verified']
 run('unpack',p,'--output',W/k)
 for row in jstr['members']:
  raw=(W/k/row['path']).read_bytes();assert len(raw)==row['size']
assert lists['candidate']['archive']['name']=='1d3145e8f1b2427f8bb0067851fcf0f1'
old={x['path']:x for x in lists['baseline']['members']};new={x['path']:x for x in lists['candidate']['members']}
assert set(old)<=set(new)
changed=[m for m in old if h(W/'baseline'/m)!=h(W/'candidate'/m)]
expected={'ribat':'attrib/ebps/races/malian/buildings/landmarks/ribat_of_sanhaja/building_landmark_age1_landmarka_mal.rgd','funduq':'attrib/ebps/races/malian/buildings/landmarks/funduq/building_landmark_age1_landmarkb_mal.rgd'}
assert set(changed)==set(expected.values())
assert len(old)==697 and len(new)==723
for m in old:assert old[m]['toc']==new[m]['toc']
added=set(new)-set(old);allowed=j(I/'allowlist.json');assert added==set(allowed['all'])-set(old)
checks={};db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
official_data={x['path'] for x in json.loads(run('list','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Data.sga'))['members']}
for kind,actor in expected.items():
 key={'ribat':'br027_ribat','funduq':'bf027_funduq'}[kind]
 assert all(m.startswith(('attrib/attachments/attachment_lists/garrison/'+key+'/', 'art/scenario/garrison/'+key+'/', 'art/stamps/garrison/'+key+'/')) for m in added if key in m)
 b=rgd.read((W/'baseline'/actor).read_bytes());c=rgd.read((W/'candidate'/actor).read_bytes())
 differences=[]
 def compare(ns,ms,path=''):
  assert len(ns)==len(ms)
  for a,d in zip(ns,ms):
   assert (a.key,a.hash,a.kind)==(d.key,d.hash,d.kind)
   p=path+'/'+str(a.key)
   if isinstance(a.value,list):compare(a.value,d.value,p)
   elif a.value!=d.value:differences.append((p,a.value,d.value));d.value=a.value
 compare(b.nodes,c.nodes);assert len(differences)==1 and '/attachments/' in differences[0][0] and differences[0][0].endswith('/$PBGNAME')
 assert differences[0][2]=='1d3145e8f1b2427f8bb0067851fcf0f1:'+kind+'_tier' and sem(b.nodes)==sem(c.nodes)
 tier='attrib/attachments/attachment_lists/garrison/'+key+'/'+kind+'_tier.rgd';t=rgd.read((W/'candidate'/tier).read_bytes())
 stamprefs=[n.value.replace('\\','/') for p,n in rgd.flatten(t.nodes) if n.key=='stamp'];assert 'art/stamps/garrison/'+key+'/'+kind in stamprefs
 for ref in stamprefs:
  if ref.startswith('art/stamps/garrison/'):assert ref+'.bin' in new
  else:assert ref+'.bin' in official_data or ref in official_data,ref
 media=j(I/kind/'media-manifest.json');assert media['status']=='passed' and media['native_lod_count']==1 and media['lod_count_three'] is False
 for payload in media['payloads']:assert h(W/'candidate'/payload['member'])==payload['sha256']
 geom='art/scenario/garrison/'+key+'/buildings/'+kind+'_lod0/model.rrgeom'
 assert h(W/'candidate'/geom)==media['lod_evidence']['source_levels'][0]['source_sha256']
 model=geom.removesuffix('.rrgeom')+'.rgm';visibility_evidence((W/'candidate'/model).read_bytes(),media['source_part_rows'])
 collection=next(x.payload for x in rc.walk(rc.load(W/'candidate'/model).roots) if x.tag==b'DATA');assert hashlib.sha256(collection).hexdigest()==media['collection_data_sha256']
 for m in added:
  if key not in m:continue
  assert new[m]['toc']==('attrib' if m.startswith('attrib/') else 'data')
  if m.endswith('.rrmaterial'):
   paths=set(x.decode().replace('\\','/') for x in re.findall(rb'art[\\/][A-Za-z0-9_./\\-]+\.rrtex',(W/'candidate'/m).read_bytes()));assert paths
   for p in paths:assert p in new or db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(p,)).fetchone()
 assert media['fresh_native_stamp_cook']['status']=='succeeded' and media['fresh_native_stamp_cook']['exit_code']==0
 assert all(x['live_reload'] is False and h(x['archive'])==x['sha256'] for x in media['source_cook_records'])
 source=j(O/'reviews'/(kind+'-source.json'));assert source['status']=='approved'
 checks[kind]={'actor_changes':differences,'all_nonvisual_actor_values_and_types_identical':True,'private_tier_and_retained_auxiliary_stamp_dependencies_resolved':True,'candidate_payload_sha256_match':True,'fresh_native_geometry_LOD0_exact':True,'native_collection_membership_hash_match':True,'construction_healthy_damage_ruins_selectors_evaluated':True,'material_texture_dependencies_resolved':True,'fresh_native_cooks_success_and_live_reload_off':True,'independent_source_review_approved':True}
db.close()
result={'status':'candidate_checks_passed','scope':'Independent native archive SHA1-block verification, actual extraction sizes/SHA256 and decoded native binding/media comparison. Native game acceptance not tested.','archive_sha256':h(C),'baseline_sha256':h(B),'member_count':len(new),'unchanged_baseline_members':len(old)-len(changed),'changed_existing_members':changed,'new_member_count':len(added),'checks':checks,'known_limits':['Native full-detail LOD0 only; repaired authored and separately cooked lower LODs retained but runtime lower LOD switching unsupported.','Native in-game team colours, construction, damage, gameplay and appearance acceptance pending user test.','Original reconstructions, not historical replicas; native auxiliary wreck visuals retained.'],'findings':[]}
(O/'reviews/final-package.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'sha256':result['archive_sha256'],'unchanged':result['unchanged_baseline_members'],'added':result['new_member_count']}))
