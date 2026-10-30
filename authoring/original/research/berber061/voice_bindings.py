"""0.6.1 canonical native villager/trader speech bindings; no gameplay edits."""
import copy,sys,json,os
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research/berber060'))
from common import EXT,OUT as OUT060,ARCH,GAME,read,write,sha,run
sys.path.insert(0,str(EXT))
from garrison_shared import rgd
from bindings import encode,verify_undo
BASE=OUT060/'candidate.sga'
BASE_SHA='6e4a4f3fcb00627df40f5a50fbf128c949cc281f54b4cf1a424f6bdfc9370f51'
OUT=ROOT/'output/berber_update_0_6_1/voice-bindings'
FAMILIES={'villager':{'name':'unit_villager_1_mal','speaker':'b27xxxxxxxxx','old':'b01xxxxxxxxx','pbgid':2359463},
 'trader':{'name':'unit_trade_cart_mal','speaker':'b28xxxxxxxxx','old':'b04xxxxxxxxx','pbgid':2201796}}

def source_member(family,kind):
 item=FAMILIES[family];folder='ebps/races/malian/units' if kind=='ebps' else 'sbps/races/malian/berbers'
 return 'attrib/'+folder+'/'+item['name']+'.rgd'

def source_bytes(family,kind):
 member=source_member(family,kind);report=read(OUT060/'bindings/payload-manifest.json')
 row=next(r for r in report['payloads'] if r['member']==member)
 path=Path(row['file'])
 if sha(path)!=row['sha256']:raise ValueError('0.6.0 source payload changed')
 if read(OUT060/'composition-report.json')['archive_sha256']!=BASE_SHA:raise ValueError('Unexpected authoritative 0.6.0 composition')
 return path.read_bytes()

def patch(data,family,kind):
 item=FAMILIES[family];original=rgd.read(data);doc=copy.deepcopy(original);nodes=dict(rgd.flatten(doc.nodes));changes=[]
 path='default/speech_ext/speaker_code' if kind=='ebps' else 'default/squad_speech_ext/squad_speaker_code'
 node=nodes[path]
 if node.kind!='CString' or node.value!=item['old']:raise ValueError('Unexpected original private speaker')
 if kind=='sbps':
  if nodes['default/pbgid'].value!=item['pbgid']:raise ValueError('Squad identity changed')
  if nodes['default/squad_loadout_ext/squad_female_chance'].value!=0:raise ValueError('Unexpected existing gender contract')
  if nodes['default/squad_loadout_ext/unit_list/loadout_data/type/$PBGNAME'].value!=item['name']:raise ValueError('Unexpected native loadout')
 changes.append({'field':path,'kind':node.kind,'before':node.value,'after':item['speaker']});node.value=item['speaker']
 if kind=='sbps':
  age=[(p,n) for p,n in nodes.items() if p.startswith('default/squad_speech_ext/age_mapping/')]
  if len(age)!=4 or any(n.kind!='Int' for p,n in age):raise ValueError('Unexpected native age map')
  for p,n in age:
   if n.value!=1:changes.append({'field':p,'kind':'Int','before':n.value,'after':1});n.value=1
 payload=encode(doc);verify_undo(original,rgd.read(payload),changes)
 return payload,changes

def official_identity_proof():
 # Existing pinned reader reads only two official members into memory, writes none.
 skill=Path('C:/Users/RS/.codex/skills/extract-aoe4-sga-sources/scripts');sys.path.insert(0,str(skill))
 import extract_aoe4_sga_sources as ex
 handler,version=ex.load_handler(Path('C:/Users/RS/.codex/cache/aoe4-sga-extractor-session-20260717/_skill_sga_live_runtime'))
 archive=GAME/'cardinal/archives/Attrib.sga';ex.prepare_handler(handler,version,archive);proof=[]
 with archive.open('rb') as stream:
  filesystem=handler.read(stream)
  for family,item in FAMILIES.items():
   member='attrib/sbps/races/malian/'+item['name']+'.rgd';data=filesystem.readbytes('/'+member);nodes=dict(rgd.flatten(rgd.read(data).nodes))
   if nodes['default/pbgid'].value!=item['pbgid']:raise ValueError('Official/candidate squad PBGID differs')
   if nodes['default/squad_loadout_ext/unit_list/loadout_data/type/$PBGNAME'].value!=item['name']:raise ValueError('Official/custom loadout owner differs')
   proof.append({'family':family,'member':member,'pbgid':item['pbgid'],'official_speaker':nodes['default/squad_speech_ext/squad_speaker_code'].value,
    'official_source_sha256':__import__('hashlib').sha256(data).hexdigest(),'canonical_payload_policy':'Use immutable 0.6.0 custom same-PBGID full native bytes, not stock gameplay; speech edits only'})
 return {'archive':str(archive),'members':proof}

def build():
 if sha(BASE)!=BASE_SHA:raise ValueError('0.6.0 archive changed')
 official=official_identity_proof();payloads=[]
 for family,item in FAMILIES.items():
  for kind in ('ebps','sbps'):
   source=source_bytes(family,kind);member=source_member(family,kind)
   # Confirm retained payload is the current packaged source without extraction.
   row=next(r for r in read(OUT060/'bindings/payload-manifest.json')['payloads'] if r['member']==member)
   current=OUT060/'integration'/('candidate-readback-'+BASE_SHA[:12])/member
   if not current.is_file() or current.read_bytes()!=source:raise ValueError('Packaged source readback differs')
   payload,changes=patch(source,family,kind)
   members=[member]
   if kind=='sbps':members.append('attrib/sbps/races/malian/'+item['name']+'.rgd')
   for target_member in members:
    target=OUT/'payloads'/target_member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    payloads.append({'family':family,'member':target_member,'file':str(target),'sha256':sha(target),'source':str(current),
     'source_member':member,'source_sha256':sha(current),'changes':changes,'semantic_undo':'passed',
     'new_canonical_alias':target_member!=member,'race':'malian','speaker':item['speaker'],
     'pbgid':item['pbgid'] if kind=='sbps' else dict(rgd.flatten(rgd.read(payload).nodes))['default/pbgid'].value})
 report={'schema':'berber061-native-voice-bindings/v1','status':'passed','base':str(BASE),'base_sha256':BASE_SHA,
  'official_identity':official,'payloads':payloads,'owner_count':len(payloads),
  'routing_diagnosis':'0.6.0 SBPS overrides were only under races/malian/berbers; production/start refs and official owners use canonical races/malian paths. Add same-PBGID custom native bytes at canonical paths while retaining old aliases.',
  'all_non_speech_semantics':'Preserved exactly against 0.6.0 custom source; canonical aliases are identical copies of the patched custom owner, not stock replacements',
  'speech_age_mapping':[1,1,1,1],'native_playback':'pending','scope':'Two unit families only; no API, SCAR, art, gameplay, production, gender or identity edits'}
 write(OUT/'payload-manifest.json',report);print('061_VOICE_BINDINGS',len(payloads));return report
if __name__=='__main__':build()
