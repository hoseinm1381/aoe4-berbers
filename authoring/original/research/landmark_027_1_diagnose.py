from pathlib import Path
import os,sys,subprocess,struct,json,re
R=Path.cwd();O=R/'output/berber_update_0_2_7_1/diagnostics';O.mkdir(parents=True,exist_ok=True)
X=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path[:0]=[str(X),str(R/'research')]
from landmark_027_export_codec import rc
A=X/'bin/sga-archiver.exe';BASE=R/'output/berber_update_0_2_7/package/Berber_future_kingdom.sga'
for kind,key in [('ribat','br027_ribat'),('funduq','bf027_funduq')]:
 base=f'art/scenario/garrison/{key}/buildings/{kind}_lod0/model'
 for suffix in ['.rgm','.rgo','.rrgeom','.rrmaterial']:
  p=O/kind/('model'+suffix);p.parent.mkdir(parents=True,exist_ok=True)
  subprocess.run([str(A),'extract-member',str(BASE),base+suffix,str(p)],check=True,capture_output=True)
  doc=rc.load(p);chunks=[(c.tag.decode(),c.version,len(c.payload),c.payload[:70].hex()) for c in rc.walk(doc.roots)]
  (p.with_suffix(suffix+'.chunks.json')).write_text(json.dumps(chunks,indent=2))
  if suffix=='.rrgeom':
   for c in rc.walk(doc.roots):
    if c.tag in [b'NBVE',b'NBIN',b'NBME',b'NBLO',b'BANA']:
     print(kind,c.tag,len(c.payload),c.payload[:90].hex() if c.tag==b'BANA' else int.from_bytes(c.payload,'little'))
  if suffix=='.rgo':print(kind,'RGOstrings',re.findall(rb'[A-Za-z0-9_\\/.:]{6,}',p.read_bytes())[:50])
