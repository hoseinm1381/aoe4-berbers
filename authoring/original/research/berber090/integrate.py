"""Fresh native 090 building media, preserving the accepted 081 archive identity.

Commands: audit, prepare, cook, assemble, compose. No game files are modified.
"""
import copy, hashlib, json, math, os, re, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
OUT=ROOT/'output/berber_update_0_9_0'
BASE=ROOT/'output/berber_update_0_8_1/Berber_future_kingdom.sga'
BASE_SHA='c58ef43ad4b0e664609161eb35178c97500837e9a844d7583fb014a50b7cc441'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe'
EDITOR=Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe'
PROJECT=OUT/'garrison-library/Mods/berber_buildings_090'
ART=ROOT/'art/building_remix_0_9_0'
sys.path[:0]=[str(EXT),str(ROOT/'research')]
from garrison_shared import rgd, relic_chunky as rc, building_project as bp
from berber_040_integrate import NativeTree, active_visuals
from landmark_027_export_codec import intact_damage_conditions,copy_native_markers,visibility_evidence
from berber_040_integrate_models import single_lod0_geometry
SCALE='default/entity_blueprint_ext/animator_scale'
ACTORS={
 'tlemcen':'attrib/ebps/races/malian/buildings/landmarks/great_mosque_of_tlemcen/building_landmark_age2_landmarkc_control_mal.rgd',
 'marrakech':'attrib/ebps/races/malian/buildings/landmarks/marrakech/building_landmark_age2_landmarkd_control_mal.rgd',
 'fez':'attrib/ebps/races/malian/buildings/landmarks/madrasa_fez/building_landmark_age3_landmarke_mal.rgd',
 'wonder':'attrib/ebps/races/malian/buildings/building_wonder_mal.rgd'}
KINDS={'fez':'fez','wonder':'koutoubia'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
 if p.returncode:raise RuntimeError(str(args)+'\n'+p.stdout[-3000:]+'\n'+p.stderr[-4000:])
 return p.stdout
def inventory(p):
 v=json.loads(run(ARCH,'list',p,'--verify'));assert v['archive']['verification']['verified'];return v
def extract(member):
 dest=OUT/'baseline-inputs'/member
 if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);run(ARCH,'extract-member',BASE,member,dest)
 return dest
def semantic(nodes):return [(n.key,n.hash,n.kind,semantic(n.value) if isinstance(n.value,list) else n.value) for n in nodes]
def patch_scale(raw,expected):
 original=rgd.read(raw);doc=copy.deepcopy(original);node=rgd.find(doc.nodes,SCALE)
 assert node.kind=='Float' and math.isfinite(node.value) and node.value==expected
 node.value=expected*1.40;raw=rgd.write(doc);after=rgd.read(raw)
 assert math.isclose(rgd.find(after.nodes,SCALE).value,expected*1.4,abs_tol=1e-5)
 restored=copy.deepcopy(after);rgd.find(restored.nodes,SCALE).value=expected
 assert semantic(restored.nodes)==semantic(original.nodes),'Non-scale gameplay changes'
 return raw,rgd.find(after.nodes,SCALE).value
def stem(kind):return f'art/scenario/garrison/berber_buildings_040/buildings/{KINDS[kind]}_lod0/model'
def audit():
 import package_unified_release
 package=package_unified_release.check();assert sha(BASE)==BASE_SHA
 inv=inventory(BASE);write(OUT/'baseline-inventory.json',inv)
 names={r['path'] for r in inv['members']}
 # Resolve exact actor names from the archive; fail rather than substitute donors.
 candidates=[n for n in names if n.startswith('attrib/ebps/') and 'wonder' in n and n.endswith('.rgd')]
 if ACTORS['wonder'] not in names:
  assert len(candidates)==1,candidates;ACTORS['wonder']=candidates[0]
 rows=[]
 for kind,member in ACTORS.items():
  doc=rgd.read(extract(member).read_bytes());flat=list(rgd.flatten(doc.nodes))
  rows.append({'kind':kind,'actor':member,'actor_sha256':sha(extract(member)),
   'scale':rgd.find(doc.nodes,SCALE).value,
   'footprint_and_collision_fields':[(p,n.value) for p,n in flat if n.kind!='Table' and any(s in p for s in ('footprint','simbox','collision','exit','rally')) and not isinstance(n.value,list)],
   'visual_binding_fields':[(p,n.value) for p,n in flat if n.kind=='CString' and (p.endswith('/$PBGNAME') or p.endswith('/stamp')) and ('tier_ext' in p or 'animator' in p or 'stamp' in p)]})
 for kind in KINDS:
  member=f'art/stamps/garrison/berber_buildings_040/{KINDS[kind]}.bin'
  visuals=active_visuals(NativeTree(extract(member)))
  assert any(v['model']==stem(kind) for v in visuals),(kind,visuals)
  for ext in ('.rgm','.rgo','.rrgeom','.rrmaterial'):assert stem(kind)+ext in names;extract(stem(kind)+ext)
  rows.append({'kind':kind,'stamp':member,'stamp_sha256':sha(extract(member)),'active_visuals':visuals,
   'principal':stem(kind),'native_lifecycle_graph_sha256':sha(extract(stem(kind)+'.rgo')),
   'policy':'Keep this stamp, tier identity, flag, markers and native graph; replace principal geometry/model/material only'})
 write(OUT/'baseline-audit.json',{'status':'passed','base':str(BASE),'base_sha256':BASE_SHA,'package':package,'targets':rows})
 print('090_AUDIT_PASSED',flush=True)
def prepare():
 assert read(OUT/'baseline-audit.json')['status']=='passed'
 if not (PROJECT/'mod-project.json').exists():run(CORE,'mod-project','create','--library',OUT/'garrison-library','--name','berber_buildings_090')
 run(CORE,'mod-project','settings','--project',PROJECT,'--live-reload','off','--mod-id','1d3145e8-f1b2-427f-8bb0-067851fcf0f1')
 sources={}
 from PIL import Image
 for kind in KINDS:
  source=ART/kind/'export_lod0';parts=read(source/'building.json')['parts']
  assert parts and len({p['name'] for p in parts})==len(parts)
  for p in source.rglob('*.png'):
   with Image.open(p) as im:assert all(n>0 and n&(n-1)==0 for n in im.size),p
  sources[kind]={'source':str(source),'files':{str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}}
  run(CORE,'mod-project','building','--project',PROJECT,'--source',source,'--name',kind+'_lod0','--profile','english-house','--integration','script')
 write(OUT/'prepared.json',{'status':'prepared','sources':sources})
 print('090_PREPARED',flush=True)
def check_sources(record):
 for item in record['sources'].values():
  source=Path(item['source']);assert {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}==item['files'],'Source changed after preparation'
def cook():
 prep=read(OUT/'prepared.json');check_sources(prep)
 run(CORE,'mod-project','cook','--project',PROJECT,'--editor',EDITOR,'--timeout','1200')
 record=read(PROJECT/'mod-project.json')['cooks'][-1]
 assert record['live_reload'] is False and sha(record['archive'])==record['sha256']
 check_sources(prep);back=OUT/('art-cook-readback-'+record['sha256'][:16])
 run(ARCH,'unpack',record['archive'],'--output',back)
 write(OUT/'art-cook.json',{'status':'passed','cook':record,'readback':str(back),'sources':prep['sources']})
 print('090_FRESH_COOK_PASSED',flush=True)
def assemble():
 cook=read(OUT/'art-cook.json');assert cook['status']=='passed';check_sources(cook)
 back=Path(cook['readback']);payload=[];reports=[]
 def save(member,raw):
  p=OUT/'integration/payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  payload.append({'member':member,'file':str(p),'sha256':sha(p),'bytes':len(raw)})
 for kind in KINDS:
  fresh=f'art/scenario/garrison/{PROJECT.name}/buildings/{kind}_lod0/model';final=stem(kind)
  parts=read(ART/kind/'export_lod0/building.json')['parts']
  raw=bp.construction_model((back/(fresh+'.rgm')).read_bytes(),extract(final+'.rgm').read_bytes(),parts,profile_id='english-barracks')
  raw,damage=intact_damage_conditions(raw);visibility=visibility_evidence(raw,parts)
  raw,markers=copy_native_markers(raw,extract(final+'.rgm').read_bytes())
  doc=rc.parse(raw);bana=[c for c in rc.walk(doc.roots) if c.tag==b'BANA'];assert len(bana)==1
  raw=rc.rebuild(doc,lambda c:rc.lp_string(final.replace('/','\\')) if c.offset==bana[0].offset else None)
  geom,evidence=single_lod0_geometry([(back/(fresh+'.rrgeom')).read_bytes()]*3)
  save(final+'.rgm',raw);save(final+'.rrgeom',geom)
  save(final+'.rrmaterial',(back/(fresh+'.rrmaterial')).read_bytes())
  for p in (back/Path(fresh).parent).glob('*.rrtex'):save(p.relative_to(back).as_posix(),p.read_bytes())
  reports.append({'kind':kind,'principal':final,'native_graph':'byte preserved in base archive','stamp_tier_flag':'byte preserved','markers':markers,'visibility':visibility,'damage':damage,'geometry':evidence})
 targets=read(OUT/'baseline-audit.json')['targets'];scales=[]
 for kind in ('tlemcen','marrakech'):
  target=next(r for r in targets if r['kind']==kind and 'actor' in r);member=target['actor']
  before=target['scale'];raw,after=patch_scale(extract(member).read_bytes(),before)
  save(member,raw);scales.append({'kind':kind,'member':member,'before':before,'after':after,'multiplier':1.40,'only_scale_semantics_changed':True})
 write(OUT/'integration/payloads.json',{'status':'passed','payloads':payload,'models':reports,'scales':scales,'source_cook_sha256':cook['cook']['sha256']})
 print('090_MEDIA_ASSEMBLED',len(payload),flush=True)
def compose():
 assert sha(BASE)==BASE_SHA
 report=read(OUT/'integration/payloads.json');check_sources(read(OUT/'art-cook.json'));rows=report['payloads']
 assert len({r['member'] for r in rows})==len(rows)
 for r in rows:assert sha(r['file'])==r['sha256']
 current=BASE
 for alias,prefix in [('data','art/'),('attrib','attrib/')]:
  selected=[r for r in rows if r['member'].startswith(prefix)];mapping=OUT/'integration'/(alias+'-members.txt')
  mapping.write_text('\n'.join(r['member']+'='+r['file'] for r in selected)+'\n',encoding='utf8')
  target=OUT/'integration'/(alias+'-candidate.sga');run(ARCH,'set-members',current,mapping,target,'--alias',alias);current=target
 final=OUT/'Berber_future_kingdom.sga';shutil.copy2(current,final)
 before=read(OUT/'baseline-inventory.json');after=inventory(final);old={r['path']:r for r in before['members']};new={r['path']:r for r in after['members']}
 allow={r['member']:r for r in rows};assert set(new)==set(old)|set(allow)
 unchanged=[];changed=[]
 for member in old:
  if member not in allow:
   assert all(old[member][k]==new[member][k] for k in ('size','crc','storage','encryption','toc')),member
   unchanged.append(member)
  else:changed.append(member)
 for i,row in enumerate(rows):
  p=OUT/'integration/readback'/str(i);p.parent.mkdir(parents=True,exist_ok=True);run(ARCH,'extract-member',final,row['member'],p);assert sha(p)==row['sha256']
 assert before['archive']['name']==after['archive']['name']
 write(OUT/'composition-report.json',{'status':'passed','base_sha256':BASE_SHA,'archive':str(final),'archive_sha256':sha(final),'project_guid':after['archive']['name'],'payloads':rows,'changed_existing':changed,'new_members':sorted(set(new)-set(old)),'unchanged_member_count':len(unchanged),'unrelated_members_crc_size_identical':True,'archive_verification':after['archive']['verification'],'game_runtime':'pending','native_graphs_stamps_tiers_voices_preserved':True})
 print('090_CANDIDATE_VERIFIED',sha(final),flush=True)
def strong_verify():
 """Full decoded SHA proof; these two readbacks are regenerable cleanup targets."""
 report=read(OUT/'composition-report.json');final=Path(report['archive'])
 assert report['status']=='passed' and sha(BASE)==BASE_SHA and sha(final)==report['archive_sha256']
 back=OUT/'integration/full-base-readback';after=OUT/'integration/full-final-readback'
 if not back.exists():run(ARCH,'extract',BASE,back)
 if not after.exists():run(ARCH,'extract',final,after)
 # Unpack also generates authoring XML/RDO sidecars; compare actual archive members only.
 oldnames={r['path'] for r in read(OUT/'baseline-inventory.json')['members']}
 newnames=oldnames|{r['member'] for r in report['payloads']}
 old={member:sha(back/member) for member in sorted(oldnames)}
 new={member:sha(after/member) for member in sorted(newnames)}
 allow={r['member']:r['sha256'] for r in report['payloads']}
 assert set(new)==set(old)|set(allow)
 changes=[]
 for member,digest in old.items():
  if member not in allow:assert new[member]==digest,member
  elif new[member]!=digest:changes.append(member)
 for member,digest in allow.items():assert new[member]==digest,member
 # All material texture references must resolve inside the candidate or official index.
 import sqlite3
 db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
 deps=[]
 for row in report['payloads']:
  if not row['member'].endswith('.rrmaterial'):continue
  raw=Path(row['file']).read_bytes()
  refs={v.decode().replace('\\','/') for v in re.findall(rb'art[\\/][A-Za-z0-9_\\/.-]+\.rrtex',raw)}
  assert refs,('No texture refs discovered',row['member'])
  for ref in sorted(refs):
   exists=ref in new
   if not exists:assert db.execute('select 1 from resolved_assets where lower(logical_path)=lower(?)',(ref,)).fetchone(),ref
   deps.append({'material':row['member'],'texture':ref,'source':'candidate' if exists else 'official-index'})
 write(OUT/'member-sha256-proof.json',{'status':'passed','baseline_sha256':BASE_SHA,'archive_sha256':report['archive_sha256'],'baseline_members':len(old),'final_members':len(new),'changed_existing':changes,'added_members':sorted(set(new)-set(old)),'unchanged_member_count':len(old)-len(changes),'all_unrelated_decoded_member_sha256_identical':True,'before':old,'after':new,'texture_dependencies':deps,'regenerable_readbacks':[str(back),str(after)]})
 print('090_STRONG_SHA_PROOF_PASSED',len(old)-len(changes),'unchanged',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
