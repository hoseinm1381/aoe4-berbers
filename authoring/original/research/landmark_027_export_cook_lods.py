"""Serialized fresh native cook of three independently modeled geometry levels."""
import os,json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7/qualification'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe';PROJECT=OUT/'l/Mods/lf027'
def run(label,args):
 p=OUT/(label+'.log')
 with p.open('w',encoding='utf8') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=900)
 assert r.returncode==0,(label,r.returncode)
 print(label,'passed',flush=True)
if not (PROJECT/'mod-project.json').exists():run('lod-create',[CORE,'mod-project','create','--library',OUT/'l','--name','lf027'])
run('lod-settings',[CORE,'mod-project','settings','--project',PROJECT,'--live-reload','off','--mod-id','1d3145e8-f1b2-427f-8bb0-067851fcf0f1'])
for lod in range(3):run('lod-add-'+str(lod),[CORE,'mod-project','building','--project',PROJECT,'--source',OUT/f'lod{lod}-source','--name',f'fixture_lod{lod}','--profile','english-house','--integration','script'])
for key,source in [('ribat','attachments/attachment_lists/civilizations/malian/buildings/mal_landmark_b_02'),('funduq','attachments/attachment_lists/civilizations/abbasid/buildings/tech_unit_ranged_abb/tier3_tech_unit_ranged_control_abb')]:
 run('derive-'+key,[CORE,'mod-project','derive','--project',PROJECT,'--source',source,'--name','qual_'+key])
 run('tier-stamp-'+key,[CORE,'mod-project','derive-change','--project',PROJECT,'--name','qual_'+key,'--field','attachment_lists/attachment_lists/attachment_list/attachment_list/stamp_attachment/stamp','--value',r'art\stamps\garrison\lf027\fixture_lod0'])
run('independent-lod-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor','C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--timeout','600'])
record=json.loads((PROJECT/'mod-project.json').read_text());cook=record['cooks'][-1]
assert not cook['live_reload'];assert hashlib.sha256(Path(cook['archive']).read_bytes()).hexdigest()==cook['sha256']
run('independent-lod-readback',[ARCH,'unpack',cook['archive'],'--output',OUT/'independent-lod-readback'])
(OUT/'independent-lod-cook.json').write_text(json.dumps(cook,indent=2))
