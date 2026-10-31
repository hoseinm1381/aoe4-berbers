"""Isolated native cheer-trigger qualification, preserving the working .2 source.

This reuses Shrek's existing cheer_toggle ability hook with Tuareg's own stock
cheer clips. It does not copy the Shrek model/library or claim a custom 15-second
upper-body pose. Native behavior/restoration requires the user's solo test.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shrek_animation_test'
CANDIDATE=WORK/'candidate'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
ARCHIVER=EXT/'bin/sga-archiver.exe'
ABILITY='assets/attrib/instances/abilities/ber_spearman_ranged_damage_reduction.xml'
MEMBER='attrib/abilities/ber_spearman_ranged_damage_reduction.rgd'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
VERSION='0.1.3-tuareg-q-trigger.1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inspect(p):return json.loads(subprocess.check_output([str(ARCHIVER),'list',str(p),'--verify'],text=True))
def check_original():
    baseline=json.loads((WORK/'source-baseline.json').read_text())
    for name,digest in baseline.items():assert sha(ROOT/name)==digest,name
    return len(baseline)
def prepare():
    assert not CANDIDATE.exists(),'Preserve the existing candidate and choose a fresh directory.'
    sources=[ROOT/'Berber_future_kingdom.aoe4mod']+[p for p in (ROOT/'assets').rglob('*') if p.is_file()]
    (WORK/'source-baseline.json').write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in sources},indent=2))
    CANDIDATE.mkdir();shutil.copy2(ROOT/'Berber_future_kingdom.aoe4mod',CANDIDATE/'Berber_future_kingdom.aoe4mod')
    shutil.copytree(ROOT/'assets',CANDIDATE/'assets')
    before=ET.parse(CANDIDATE/ABILITY).getroot();after=copy.deepcopy(before)
    nodes=after.findall('.//group[@name="ability_active_state_tree_group"]/state_tree_node[@name="ability_activate_entity_tree"]')
    assert len(nodes)==2 and all(n.get('value')=='' for n in nodes)
    for node in nodes:node.set('value','cheer_toggle')
    ET.ElementTree(after).write(CANDIDATE/ABILITY,encoding='utf-8',xml_declaration=True)
    neutral=copy.deepcopy(after)
    for node in neutral.findall('.//group[@name="ability_active_state_tree_group"]/state_tree_node[@name="ability_activate_entity_tree"]'):
        node.set('value','')
    assert ET.tostring(neutral)==ET.tostring(before),'Changes beyond the two native visual-trigger fields'
    for p in sources:
        rel=p.relative_to(ROOT)
        if rel.as_posix()!=ABILITY:assert sha(CANDIDATE/rel)==sha(p),rel
    report={'schema':'tuareg-native-cheer-probe-source/v1','guid':GUID,'ability_pbgid':1073741839,
            'changed_source':ABILITY,'changed_fields':2,'hook':'cheer_toggle','original_sources_preserved':check_original(),
            'native_library':'unchanged base_spearshield; no Shrek resources copied',
            'scope':'activation/restoration probe; custom 15-second shield pose not implemented'}
    (WORK/'candidate-source.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
def build():
    check_original()
    editor=Path(r'E:\Games\steamapps\common\Age of Empires IV\EssenceEditor.exe')
    run=WORK/'candidate-build';assert not run.exists()
    for folder in ('logs','output','intermediate'):(run/folder).mkdir(parents=True,exist_ok=True)
    args=[str(editor),'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report','--no_source_control',
          '--log_path',str(run/'logs'),'--build_mod',str(CANDIDATE/'Berber_future_kingdom.aoe4mod'),
          '--no_burn_window','--burn_verbose_log_level','--burn_cache_type','Local','--burn_max_threads','1',
          '--burn_log_path',str(run/'logs/burn.log'),'--build_path',str(run/'output'),'--intermediate_path',str(run/'intermediate')]
    report={'schema':'tuareg-native-cheer-probe-build/v1','status':'running','command':args}
    (WORK/'candidate-build.json').write_text(json.dumps(report,indent=2))
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    with (run/'logs/stdout.log').open('w') as stdout,(run/'logs/stderr.log').open('w') as stderr:
        result=subprocess.run(args,cwd=editor.parent,stdout=stdout,stderr=stderr,startupinfo=startup,timeout=300)
    archives=list((run/'output').rglob('*.sga'))
    report.update(status='succeeded' if result.returncode==0 else 'failed',exit_code=result.returncode,
                  archives=[{'path':str(p),'sha256':sha(p)} for p in archives],original_sources_preserved=check_original())
    (WORK/'candidate-build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
    assert result.returncode==0 and len(archives)==1
def package():
    check_original()
    build=json.loads((WORK/'candidate-build.json').read_text());assert build['status']=='succeeded' and build['exit_code']==0
    donor=Path(build['archives'][0]['path']);assert sha(donor)==build['archives'][0]['sha256']
    working=json.loads((ROOT/'output/tuareg_shield_test/delivery-verification.json').read_text())
    base=Path(working['archive']);assert sha(base)==working['archive_sha256']
    package_dir=WORK/'package';package_dir.mkdir(exist_ok=True)
    archive=package_dir/'Berber_future_kingdom.sga';assert not archive.exists()
    graft=subprocess.run([str(ARCHIVER),'graft',str(base),str(donor),str(archive),MEMBER],check=True,capture_output=True,text=True)
    (WORK/'graft-result.json').write_text(graft.stdout)
    before=inspect(base);after=inspect(archive)
    assert after['archive']['verification']['verified'] is True
    assert after['archive']['name'].replace('-','').lower()==GUID
    old={x['path']:x for x in before['members']};new={x['path']:x for x in after['members']}
    assert set(old)==set(new) and len(new)==263
    changes=[p for p in old if (old[p]['crc'],old[p]['size'],old[p]['toc'])!=(new[p]['crc'],new[p]['size'],new[p]['toc'])]
    assert changes==[MEMBER],changes
    for label,path in [('before',base),('after',archive)]:
        directory=WORK/f'{label}-readback';assert not directory.exists()
        subprocess.run([str(ARCHIVER),'unpack',str(path),'--output',str(directory)],check=True,capture_output=True,text=True)
    old_xml=ET.parse(WORK/'before-readback'/MEMBER.replace('.rgd','.xml')).getroot()
    new_xml=ET.parse(WORK/'after-readback'/MEMBER.replace('.rgd','.xml')).getroot()
    hooks=[n for n in new_xml.iter('RGDNode') if n.get('Key')=='ability_activate_entity_tree']
    old_hooks=[n for n in old_xml.iter('RGDNode') if n.get('Key')=='ability_activate_entity_tree']
    assert len(hooks)==len(old_hooks)>0
    assert all(n.get('Value')=='' for n in old_hooks)
    assert all(n.get('Value')=='cheer_toggle' for n in hooks)
    for old_node,new_node in zip(old_hooks,hooks):new_node.attrib.clear();new_node.attrib.update(old_node.attrib)
    assert ET.tostring(old_xml)==ET.tostring(new_xml),'Other cooked ability fields changed'
    report={'schema':'tuareg-native-cheer-probe-package/v1','version':VERSION,'guid':GUID,
            'archive_sha256':sha(archive),'members':len(new),'changed_members':changes,
            'unchanged_members':len(new)-1,'compiled_visual_trigger_fields':len(hooks),
            'original_sources_preserved':check_original(),'runtime':'pending user solo qualification',
            'custom_15_second_shield_pose':'not implemented; this is the stock gesture trigger probe'}
    (WORK/'archive-inventory.json').write_text(json.dumps(after,indent=2))
    (package_dir/'PROBE-EVIDENCE.json').write_text(json.dumps(report,indent=2))
    shutil.copy2(WORK/'TEST-PROBE.txt',package_dir/'TEST-PROBE.txt')
    sys.path.insert(0,str(EXT));from garrison_shared import mod_bundle
    details={'id':'berber_future_kingdom','name':'The Berber Dynasties','version':VERSION,
             'summary':'Q native gesture trigger probe; custom shield hold pending',
             'author':'hossein81 and marcokistan','updated':'2026-10-11','min_garrison':'0.1.3',
             'content_types':['game-mode','tuning-pack'],
             'description':'Isolated solo qualification of Shrek native cheer_toggle hook on the existing Tuareg Q ability. Current body/shield models, ability effects, speakers, production and upgrade data are retained. Uses stock spearman cheer clips. Custom 15-second shield pose and native movement/combat/restoration acceptance remain pending.',
             'changelog':'Add only ability_activate_entity_tree=cheer_toggle to the existing ability variants in an isolated candidate. No Shrek model or animation library dependency.'}
    mod_bundle.write_manifest(package_dir,bundle_key='berber_future_kingdom',members=[{'mod_key':'berber_future_kingdom','role':'tuning','path':archive.name,'sha256':sha(archive)}],details=details)
    zip_path=WORK/f'berber_future_kingdom-{VERSION}.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package_dir.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        assert hashlib.sha256(z.read(archive.name)).hexdigest()==report['archive_sha256']
    report.update(zip=str(zip_path),zip_sha256=sha(zip_path))
    (WORK/'delivery.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','build','package'])
    args=parser.parse_args();globals()[args.stage]()
