"""Read installed native schemas and attachments; keep compact route evidence."""
import json,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7/qualification'
CORE=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe'
def fields(file):
 p=subprocess.run([str(CORE),'mod-project','attrib-fields','--file',file,'--table','default'],capture_output=True,text=True,check=True)
 return json.loads(p.stdout.split('GARRISON_MOD_PROJECT=',1)[1])['fields']
names={
 'ribat_tier':'attachments/attachment_lists/civilizations/malian/buildings/mal_landmark_b_02',
 'funduq_tier':'attachments/attachment_lists/civilizations/abbasid/buildings/tech_unit_ranged_abb/tier3_tech_unit_ranged_control_abb',
 'ribat_schema':'statemodel_schema/buildings/unit_cavalry',
 'funduq_schema':'statemodel_schema/buildings/civilizations/chinese_ha_01/jiangnan_tower_chi_ha_01',
 'house_schema':'statemodel_schema/buildings/house'}
report={}
for key,name in names.items():
 rows=fields(name)
 if key.endswith('schema'):
  rows=[r for r in rows if r['value'] is not None and ('property_id' in r['field'] or 'construction' in str(r['value']) or 'life_cycle' in str(r['value']))]
 report[key]={'native_file':name,'fields':rows}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'installed-contract.json').write_text(json.dumps(report,indent=2))
print(json.dumps({key:[r['value'] for r in val['fields'] if 'construction' in str(r['value']) or 'life_cycle' in str(r['value'])] for key,val in report.items()},indent=2))
