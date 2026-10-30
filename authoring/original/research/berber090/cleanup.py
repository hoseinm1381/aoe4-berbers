"""Inventory then remove only verified regenerable090 build copies after ZIP checks."""
import json,sys,os,shutil,hashlib
from pathlib import Path
from release import ROOT,OUT,verify,sha
PHYSICAL=OUT.resolve()
ART=(ROOT/'art/building_remix_0_9_0').resolve()
RECIPES=Path(__file__).resolve().parent


def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')


def safe(path,allowed):
    path=Path(path).resolve()
    assert path!=allowed and path.is_relative_to(allowed),(path,allowed)
    for p in (path,*path.parents):
        if p.exists():assert not (p.lstat().st_file_attributes&0x400),str(p)
        if p==allowed:break
    if path.is_dir():
        for base,dirs,files in os.walk(path,followlinks=False):
            for name in dirs+files:
                p=Path(base)/name
                assert p.resolve().is_relative_to(allowed),str(p)
                assert not (p.lstat().st_file_attributes&0x400),str(p)
                assert p.suffix.lower() not in {'.blend','.blend1','.blend2'},str(p)
    return path


def files(path):return list(path.rglob('*')) if path.is_dir() else [path]


def snapshot_cook():
    project=PHYSICAL/'garrison-library/Mods/berber_buildings_090'
    if (project/'mod-project.json').exists():
        write('retained-garrison-project.json',json.loads((project/'mod-project.json').read_text(encoding='utf8')))
    runs=[]
    for p in project.rglob('run.json'):
        log=p.parent/'logs/burn.log'
        runs.append({'record':json.loads(p.read_text(encoding='utf8')),
                     'burn_log_tail':log.read_text(encoding='utf8',errors='replace').splitlines()[-80:] if log.exists() else []})
    write('retained-native-cook-evidence.json',{'runs':runs})


def inventory():
    delivery=verify()
    assert json.loads((OUT/'member-sha256-proof.json').read_text(encoding='utf8'))['status']=='passed'
    snapshot_cook()
    selected=[(PHYSICAL/'baseline-inputs','Re-extract from hash-protected081 base'),
              (PHYSICAL/'garrison-library','Generated090 project/cook; recreate audit/prepare/cook from retained export inputs'),
              (PHYSICAL/'integration/payload','Recreate assemble from retained source exports and fresh cook'),
              (PHYSICAL/'integration/readback','Re-extract14payloads from retained090 SGA'),
              (PHYSICAL/'integration/full-base-readback','Exact081members preserved in081 SGA; full SHA proof retained'),
              (PHYSICAL/'integration/full-final-readback','Exact090members preserved in090 SGA; full SHA proof retained'),
              (PHYSICAL/'integration/data-candidate.sga','Intermediate composition; recreate compose'),
              (PHYSICAL/'integration/attrib-candidate.sga','Duplicate final composition; authoritative090SGA retained')]
    selected += [(p,'Regenerate fresh090 art cook and unpack') for p in PHYSICAL.glob('art-cook-readback-*')]
    for name in ('export_unmerged_preview','export_stage_preview','export_pre_seating_fix'):
        selected.append((ART/'fez'/name,'Superseded disposable export; retained full editableFez recipe/source plus final export_lod0'))
    selected.append((RECIPES/'__pycache__','Python bytecode regenerated from retained090 recipe scripts'))
    rows=[]
    for p,reason in selected:
        if not p.exists():continue
        allowed=ART if p.is_relative_to(ART) else RECIPES if p.is_relative_to(RECIPES) else PHYSICAL
        checked=safe(p,allowed)
        entries=[f for f in files(checked) if f.is_file()]
        rows.append({'path':str(checked),'allowed_root':str(allowed),'bytes':sum(f.stat().st_size for f in entries),
                     'file_count':len(entries),'ownership':'Berber090 isolated build','regeneration_evidence':reason})
    protected={str(OUT/'Berber_future_kingdom.sga'):delivery['sga_sha256'],delivery['zip']:delivery['zip_sha256']}
    for p in ART.rglob('*'):
        if p.is_file() and (p.suffix.lower().startswith('.blend') or 'export_lod0' in p.parts):
            protected[str(p)]=sha(p)
    plan={'status':'inventoried','targets':rows,'protected_hashes':protected,
          'bytes_before':sum(r['bytes'] for r in rows),'dependency_route':'research/berber090/REBUILD.md',
          'all_unique_voice_recordings_retained_in_unchanged081_and090_members':True}
    write('cleanup-plan.json',plan)
    return plan


def apply():
    plan=inventory()
    # Preflight every target and protection before the first removal.
    for p,digest in plan['protected_hashes'].items():assert sha(p)==digest,p
    for row in plan['targets']:
        path=safe(row['path'],Path(row['allowed_root']))
        assert sum(f.stat().st_size for f in files(path) if f.is_file())==row['bytes'],str(path)
    reclaimed={'E:':0,'F:':0}
    for row in plan['targets']:
        path=safe(row['path'],Path(row['allowed_root']))
        if path.is_dir():shutil.rmtree(path)
        else:path.unlink()
        reclaimed[path.drive.upper()]+=row['bytes']
    for p,digest in plan['protected_hashes'].items():assert sha(p)==digest,p
    verify()
    result={'status':'passed','bytes_before':plan['bytes_before'],'bytes_after':0,
            'bytes_reclaimed_by_drive':reclaimed,'removed':plan['targets'],
            'protected_sources_and_deliveries_rehashed':len(plan['protected_hashes']),
            'working081_postflight':'passed','090_zip_postflight':'passed',
            'source_blends_voice_files_and_required_exports_removed':0,
            'rebuild_inputs':'081+090finalSGAs/ZIPs;090Blender sources+atlases+finalexports;recipes/tooling/reports retained'}
    write('cleanup-report.json',result)
    print(json.dumps({k:result[k] for k in ('status','bytes_before','bytes_after','bytes_reclaimed_by_drive')}))


if __name__=='__main__':
    if '--apply' in sys.argv:apply()
    else:print(json.dumps(inventory(),indent=2))
