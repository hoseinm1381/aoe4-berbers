"""Read back compiled final040 attributes, restore only named visual edits."""
import copy
from berber_040_integrate import OUT,read,write,sha
from garrison_shared import rgd
from build_berber_update_0_2_5 import semantics

def main():
 composition=read(OUT/'integration/composition-report.json');assert composition['status']=='passed'
 back=OUT/'integration/candidate-readback';baseline=OUT/'integration/baseline-readback';results=[]
 for target in read(OUT/'new-targets.json')['targets']:
  kind=target['kind'];binding=read(OUT/f'integration/model-manifests/{kind}-binding.json');assert binding['status']=='passed'
  actor=rgd.read((back/target['actor']).read_bytes());old=rgd.read((baseline/target['actor']).read_bytes());restored=copy.deepcopy(actor)
  for change in binding['actor_visual_changes']:
   assert rgd.find(actor.nodes,change['path']).value==change['new']
   assert rgd.find(old.nodes,change['path']).value==change['old']
   rgd.find(restored.nodes,change['path']).value=change['old']
  assert semantics(restored.nodes)==semantics(old.nodes),(kind,'Nonvisual actor fields changed')
  tier=rgd.read((back/binding['private_tier']).read_bytes());original=rgd.read((OUT/'official-inputs'/target['tier_member']).read_bytes());restored=copy.deepcopy(tier)
  stamp=next(row['member'] for row in binding['payloads'] if row['member'].endswith('.bin')).removesuffix('.bin').replace('/','\\')
  for path in binding['stamp_fields_changed']:
   assert rgd.find(tier.nodes,path).value==stamp
   rgd.find(restored.nodes,path).value=rgd.find(original.nodes,path).value
  pbgids=0
  for path,node in rgd.flatten(restored.nodes):
   if node.key=='pbgid':
    assert node.value==binding['allocated_pbgid'];node.value=rgd.find(original.nodes,path).value;pbgids+=1
  assert pbgids and semantics(restored.nodes)==semantics(original.nodes),(kind,'Nonvisual tier fields changed')
  results.append({'kind':kind,'actor_sha256':sha(back/target['actor']),'tier_sha256':sha(back/binding['private_tier']),'actor_nonvisual_semantics':'exact baseline after named visual refs restored','tier_nonvisual_semantics':'exact consuming native tier after allocated identity and named stamp restored','footprint_scale_gameplay_fields':'preserved'})
 write(OUT/'final-attribute-readback.json',{'status':'passed','archive_sha256':composition['archive_sha256'],'buildings':results,'native_runtime':'unverified'})
 print('040_FINAL_ATTRIBUTE_SEMANTICS_PASSED',len(results))

if __name__=='__main__':main()
