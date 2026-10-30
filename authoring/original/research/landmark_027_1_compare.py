from pathlib import Path
import sys,os,collections,re,json,subprocess
R=Path.cwd();sys.path[:0]=[str(R/'research')];from landmark_027_export_codec import rc,EXT
from landmark_027_export_decode import decode_archive
O=R/'output/berber_update_0_2_7_1/diagnostics'
for kind in ['ribat','funduq']:
 p=O/kind/'model.rgo';d=rc.load(p);print(kind,collections.Counter((c.tag.decode(),c.version) for c in rc.walk(d.roots)))
 strings=[m.decode() for m in re.findall(rb'[A-Za-z0-9_\\/.:]{6,}',p.read_bytes())]
 (O/kind/'rgo-strings.json').write_text(json.dumps(strings,indent=2))
 print(kind,[s for s in strings if any(x in s.lower() for x in ['anim','mesh','model','skeleton','material','art\\','hka','bone'])][:100])
models=[f'art/scenario/garrison/{key}/buildings/{kind}_lod0/model.rgm' for kind,key in [('ribat','br027_ribat'),('funduq','bf027_funduq')]]
result=decode_archive(R/'output/berber_update_0_2_7/package/Berber_future_kingdom.sga',models,O/'decode-index.sqlite3',O/'decoded')
(O/'decoder-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
