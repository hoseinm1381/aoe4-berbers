"""Bounded E: author-cache cleanup, only after verified 0.6.0 delivery ZIPs.

Default inventories only. --apply removes only Wwise .cache, this project's
RS.validationcache, and Python bytecode backed by retained source. Originals,
Conversion Settings, SoundBanks and every editable project/script stay exact.
"""
import argparse,os,re,subprocess
from pathlib import Path
from common import ROOT,OUT,ART,read,write,sha
from cleanup import physical_root,verify_delivery,safe,tree,remove_checked


def author_inventory(project,research):
    # Check the logical roots before resolve can hide a junction/reparse owner.
    project=safe(Path(project).absolute().parent,project)
    research=safe(Path(research).absolute().parent,research)
    if not (project/'BerberVoices.wproj').is_file():raise ValueError('Editable Wwise project missing')
    candidates=[];protected=[]
    for owner,target,route in [(project,project/'.cache','Wwise rebuilds its conversion cache from retained project, Conversion Settings, Originals and external WAVs'),
        (project,project/'BerberVoices.RS.validationcache','Wwise reconstructs project validation cache when opening/validating retained .wproj'),
        (research,research/'__pycache__','Python313 recompiles each retained matching .py source')]:
        if not target.exists():continue
        rows=tree(owner,target)
        if target.name=='__pycache__':
            for row in rows:
                name=Path(row['path']).name;match=re.fullmatch(r'([A-Za-z0-9_]+)\.cpython-\d+(?:\.opt-\d+)?\.pyc',name)
                if not match or not (research/(match[1]+'.py')).is_file():raise ValueError('Bytecode lacks retained regeneration source: '+name)
        if rows:candidates.append({'owner':str(owner),'target':str(target),'regenerate':route,'files':rows,'bytes':sum(r['bytes'] for r in rows)})
    selected={str(Path(c['owner'])/r['path']) for c in candidates for r in c['files']}
    allrows=[]
    for owner in (project,research):
        for path in sorted(owner.iterdir()):
            for row in tree(owner,path):
                absolute=str(owner/row['path']);allrows.append(row)
                if absolute not in selected:protected.append({'path':absolute,'sha256':row['sha256'],'bytes':row['bytes']})
    return {'scope':'Only Wwise project and research/berber060 author trees on E:',
        'candidates':candidates,'protected':protected,'bytes_before':sum(r['bytes'] for r in allrows),
        'planned_reclaim_bytes':sum(c['bytes'] for c in candidates),'owners':[str(project),str(research)]}


def idle():
    if (OUT/'generation.lock').exists() or (OUT/'normalization.lock').exists():raise ValueError('Synthesis/normalization active')
    check=subprocess.run(['powershell.exe','-NoProfile','-Command',"@(Get-Process -Name Wwise,WwiseConsole -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True)
    if check.returncode or check.stdout.strip()!='0':raise ValueError('Wwise authoring/conversion active or idle state unavailable')


def build_plan():
    root=physical_root();verify_delivery(root);idle()
    project=safe(ROOT.resolve(),ART/'wwise/BerberVoices')
    research=safe(ROOT.resolve(),ROOT/'research/berber060')
    if project.drive.lower()!='e:' or research.drive.lower()!='e:' or ROOT.resolve() not in project.parents or ROOT.resolve() not in research.parents:
        raise ValueError('Author caches no longer in the expected E: project')
    plan=author_inventory(project,research);plan.update(mode='inventory_only',release_root=str(root),
        release_validation_sha256=sha(root/'release-validation.json'),native_playback='pending')
    write(root/'author-cache-inventory.json',plan)
    return plan


def apply():
    plan=build_plan();root=Path(plan['release_root']);write(root/'author-cache-before.json',plan)
    try:
        # All protected source/project files and selected cache hashes preflight.
        for item in plan['protected']:
            if sha(item['path'])!=item['sha256']:raise ValueError('Retained author input changed')
        for candidate in plan['candidates']:
            owner=Path(candidate['owner']);target=safe(owner,candidate['target']);idle()
            remove_checked(owner,candidate['files'])
            if target.is_dir():
                directories=[]
                for parent,dirs,files in os.walk(target,followlinks=False):
                    safe(owner,parent)
                    for name in dirs:safe(owner,Path(parent)/name)
                    directories.append(Path(parent))
                for directory in sorted(directories,key=lambda p:len(p.parts),reverse=True):directory.rmdir()
        verify_delivery(root)
        for item in plan['protected']:
            if sha(item['path'])!=item['sha256']:raise ValueError('Retained author input changed after cleanup')
        after=0
        for owner_string in plan['owners']:
            owner=Path(owner_string)
            for path in sorted(owner.iterdir()):after+=sum(r['bytes'] for r in tree(owner,path))
        reclaimed=sum(c['bytes'] for c in plan['candidates'])
        if plan['bytes_before']-after!=reclaimed:raise ValueError('Author tree changed during cleanup accounting')
        plan.update(mode='applied',status='passed',bytes_after=after,reclaimed_bytes=reclaimed,zip_post_cleanup='All delivery ZIP members and current SGA reverified')
    except Exception as error:
        plan.update(mode='applied',status='incomplete',error=str(error));write(root/'author-cache-cleanup-report.json',plan);raise
    write(root/'author-cache-cleanup-report.json',plan)
    return plan

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    report=apply() if args.apply else build_plan()
    print({k:v for k,v in report.items() if k not in ('candidates','protected')})
