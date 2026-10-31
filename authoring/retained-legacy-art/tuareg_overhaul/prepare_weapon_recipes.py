import json,os,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'output/tuareg_art_guard_trial';ART=ROOT/'art/tuareg_overhaul'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';PROJECT=ART/'garrison_library/Mods/tuareg_weapon_lists'
def run(label,args):
    with (WORK/(label+'.log')).open('w',encoding='utf-8') as f:
        p=subprocess.run([str(CORE),*[str(a) for a in args]],stdout=f,stderr=subprocess.STDOUT,timeout=600)
    assert p.returncode==0,label
if not PROJECT.exists():run('weapon-project-create',['mod-project','create','--library',ART/'garrison_library','--name','tuareg_weapon_lists'])
record=PROJECT/'mod-project.json';doc=json.loads(record.read_text())
assert not doc.get('cooks')
# Project identity is adopted by the documented settings operation, before deriving.
run('weapon-project-identity',['mod-project','settings','--project',PROJECT,'--mod-id','1d3145e8-f1b2-427f-8bb0-067851fcf0f1'])
sources={}
for age in range(1,5):
    tree=ET.parse(ROOT/f'assets/attrib/instances/ebps/races/malian/units/unit_spearman_tuareg_{age}_ber.xml')
    for node in tree.findall('.//instance_reference[@name="animator_attachments"]'):
        parent=node.get('value').replace('\\','/')
        if '/weapons/' in parent and 'torch' not in parent:sources[parent]=None
for index,parent in enumerate(sorted(sources),1):
    name=f'tuareg_spear_visual_{index}';sources[parent]=name
    if not any(row['name']==name for row in json.loads(record.read_text()).get('derived_blueprints',[])):
        run(name+'-derive',['mod-project','derive','--project',PROJECT,'--source',parent,'--name',name])
    run(name+'-model',['mod-project','derive-change','--project',PROJECT,'--name',name,'--field','attachment_lists/parent_animator','--value','art\\scenario\\tuareg\\tuareg_leaf_spear\\tuareg_leaf_spear'])
(WORK/'weapon-parent-map.json').write_text(json.dumps(sources,indent=2))
run('weapon-cook',['mod-project','cook','--project',PROJECT,'--editor',r'E:\Games\steamapps\common\Age of Empires IV\EssenceEditor.exe','--timeout','600'])
print('WEAPON_LISTS_READY',len(sources),flush=True)
