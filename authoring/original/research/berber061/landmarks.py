"""0.6.1 Castle-landmark visual scaling over the immutable 0.6.0 archive."""
import copy,json,math,sys
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research/berber060'))
from common import EXT,ARCH,sha,read,write,run
sys.path.insert(0,str(EXT))
from garrison_shared import rgd
BASE=ROOT/'output/berber_update_0_6_0/candidate.sga'
BASE_SHA='6e4a4f3fcb00627df40f5a50fbf128c949cc281f54b4cf1a424f6bdfc9370f51'
OUT=ROOT/'output/berber_update_0_6_1/landmarks'
FIELD='default/entity_blueprint_ext/animator_scale'
TARGETS={
 'tlemcen':('attrib/ebps/races/malian/buildings/landmarks/great_mosque_of_tlemcen/building_landmark_age2_landmarkc_control_mal.rgd',150.0),
 'marrakech':('attrib/ebps/races/malian/buildings/landmarks/marrakech/building_landmark_age2_landmarkd_control_mal.rgd',100.0)}
def semantic(nodes):
 return [(n.key,n.hash,n.kind,semantic(n.value) if isinstance(n.value,list) else n.value) for n in nodes]
def patch(data,expected_scale):
 original=rgd.read(data);doc=copy.deepcopy(original);nodes=dict(rgd.flatten(doc.nodes))
 node=nodes[FIELD]
 if node.kind!='Float' or not math.isfinite(node.value) or node.value!=expected_scale:raise ValueError('Unexpected native animator scale')
 # Native availability requires Feudal present, Castle absent: these advance to Castle.
 requirements=[(p,n.value) for p,n in nodes.items() if p.startswith('default/requirement_ext/') and p.endswith('upgrade_name/$PBGNAME')]
 if {v for p,v in requirements}!={'castle_age','feudal_age'}:raise ValueError('Not the qualified Castle landmark requirements')
 for path,age in requirements:
  prefix=path.rsplit('/upgrade_name/',1)[0]
  if nodes[prefix+'/is_present'].value!=(age=='feudal_age'):raise ValueError('Unexpected landmark age requirement polarity')
 node.value=expected_scale*1.25
 encoded=rgd.write(doc);candidate=rgd.read(encoded)
 if semantic(candidate.nodes)!=semantic(doc.nodes):raise ValueError('Typed roundtrip changed semantics')
 restored=copy.deepcopy(candidate);dict(rgd.flatten(restored.nodes))[FIELD].value=expected_scale
 if semantic(restored.nodes)!=semantic(original.nodes):raise ValueError('Non-scale semantic change')
 return encoded,[{'field':FIELD,'kind':'Float','before':expected_scale,'after':node.value}]
def build(base=BASE,destination=OUT):
 base=Path(base);destination=Path(destination)
 if sha(base)!=BASE_SHA:raise ValueError('Wrong immutable 0.6.0 base')
 inventory=json.loads(run(ARCH,'list',base,'--verify'))
 if not inventory['archive']['verification']['verified']:raise ValueError('Base archive verification failed')
 names={r['path'] for r in inventory['members']};payloads=[]
 for family,(member,scale) in TARGETS.items():
  if member not in names:raise ValueError('Qualified Castle landmark absent')
  source=destination/'sources'/member;source.parent.mkdir(parents=True,exist_ok=True)
  if source.exists():raise FileExistsError('Retain prior source extraction; use a fresh destination')
  run(ARCH,'extract-member',base,member,source)
  data,changes=patch(source.read_bytes(),scale)
  target=destination/'payloads'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  payloads.append({'family':family,'member':member,'file':str(target),'sha256':sha(target),'source':str(source),'source_sha256':sha(source),'changes':changes,'semantic_roundtrip':'passed','semantic_undo':'passed'})
 report={'schema':'berber061-landmark-scale/v1','status':'passed','base':str(base),'base_sha256':BASE_SHA,'payloads':payloads,'linear_visual_multiplier':1.25,'policy':'Only existing animator_scale Float; all footprint, combat, economy, requirements, attachments and identity semantics preserved','scope':'Typed compiled RGD proof; native visual scale/contact/entrance validation pending'}
 write(destination/'payload-manifest.json',report);return report
if __name__=='__main__':print(json.dumps(build(),indent=2))
