"""Admit only decoded QA with exact retained WEM and historical decode proof."""
import json,subprocess
from pathlib import Path
from cleanup_previous_versions import REPORT,EXTERNAL,sha
def prepare():
 root=EXTERNAL/'output/berber_update_0_6_0';proof=json.loads((root/'decoded-media-validation.json').read_text())
 if proof['status']!='passed':raise ValueError('No passed full decode proof')
 decoder=root/'tools/vgmstream-r2117/vgmstream-cli.exe'
 if sha(decoder)!=proof['decoder_sha256']:raise ValueError('Decoder changed')
 selected=[];retained=[]
 for row in proof['rows']:
  wem=Path(row['wem']).resolve();decoded=root/'decoded-qa'/wem.with_suffix('.wav').name
  if not decoded.exists():continue
  expected=row['decode']['decoded_sha256']
  if sha(decoded)!=expected or sha(wem)!=row['sha256']:
   retained.append(str(decoded));continue
  selected.append({'path':str(decoded),'bytes':decoded.stat().st_size,'sha256':expected,'restore':{'decoder':str(decoder),'decoder_sha256':proof['decoder_sha256'],'wem':str(wem),'wem_sha256':row['sha256']}})
 # Independently exercise the preserved regeneration route before admission.
 if selected:
  sample=selected[0];target=REPORT/'decode-regeneration-probe.wav'
  subprocess.run([str(decoder),'-i','-o',str(target),sample['restore']['wem']],capture_output=True,check=True,timeout=60)
  if sha(target)!=sample['sha256']:raise ValueError('Decode not byte-reproducible')
  target.unlink()
 result={'files':selected,'retained_unmatched':retained,'bytes':sum(r['bytes'] for r in selected),'decode_proof_sha256':sha(root/'decoded-media-validation.json'),'regeneration_probe':'byte-identical'}
 (REPORT/'decoded-qa-plan.json').write_text(json.dumps(result,indent=1));print('QA_ADMITTED',len(selected),result['bytes'],'RETAINED',len(retained),flush=True)
if __name__=='__main__':prepare()
