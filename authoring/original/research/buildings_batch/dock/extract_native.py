import json,xml.etree.ElementTree as ET,sqlite3,subprocess
from pathlib import Path
O=Path(__file__).parent
d=json.loads(next((O/'stock').rglob('decoded-static.json')).read_text())
(O/'decoded_native_binding.json').write_text(json.dumps({k:d[k] for k in ['entity_binding','building_boundary_binding','skeleton','completeness','blockers','structure_collection_contract_status']},indent=2))
print(json.dumps({k:d[k] for k in ['entity_binding','building_boundary_binding','completeness','blockers']},indent=2)[:3500])
exe='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for logical in ['attrib/attachments/attachmentlists/building_unit_naval.rgd','attrib/attachments/attachmentlists/tier2_unit_naval_control_mal.rgd']:
 dest=O/(Path(logical).stem+'.rgd');r=subprocess.run([exe,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',logical,str(dest)],capture_output=True,text=True);print(logical,r.returncode,r.stderr[:250])
 if r.returncode==0:subprocess.run([exe,'decode-rgd',str(dest),str(dest.with_suffix('.xml'))],check=True,capture_output=True)
