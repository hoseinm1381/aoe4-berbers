"""Create canonical source bundle and dependency map before any retirement."""
from pathlib import Path
import ast,collections,hashlib,json,os,shutil,sys,zipfile
import workspace as w

def copy_checked(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert w.sha(src)==w.sha(dst);return
    shutil.copy2(src,dst);assert w.sha(src)==w.sha(dst)

def migrate_tools():
    source=w.ROOT/'research/berber104';dest=w.HERE/'native_ai'
    for directory in ('source','compiled-ai','official'):
        for p in w.walk(source/directory):copy_checked(p,dest/directory/p.relative_to(source/directory))
    for name in ('cook-reference-inputs.zip','cook-inputs.json','cook-media-inputs.zip','cook-media-inputs.json','_default.burnproj','mapping.json','editor-identities.json'):
        copy_checked(source/name,dest/name)
    for p in w.walk(source/'scar'):copy_checked(p,dest/'scar'/p.relative_to(source/'scar'))
    tests=(source/'test_native.py').read_text().replace('HERE.parents[1]','HERE.parents[2]')
    (dest/'test_native.py').write_text(tests)
    # AST extraction preserves the reviewed algorithms without their historical
    # release imports, paths or command entrypoints.
    text=(w.ROOT/'research/berber091/repair.py').read_text();tree=ast.parse(text)
    selected=[ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('groups','restore_uv')]
    header='"""Native UV0 preservation, migrated from the verified 0.9.1 algorithm."""\nimport sys,struct,math\nfrom workspace import EXT\nsys.path.insert(0,str(EXT))\nfrom garrison_shared import relic_chunky as rc\n\n'
    (w.HERE/'uv.py').write_text(header+'\n\n'.join(selected)+'\n')
    text=(w.ROOT/'research/berber100/audio_prepare.py').read_text()
    # Audio recipe already has no local module imports; retain its complete
    # exact preparation contract and explicit root/output parameters.
    text=text.replace("(root / 'research/berber100/berber_music_catalog.scar')","(out / 'berber_music_catalog.scar')")
    text=text.replace("out = root / 'output/berber_update_1_0_0'","out = root / 'output/berber_update_1_0_5/work/music-preparation'")
    (w.HERE/'audio_prepare.py').write_text(text)
    copy_checked(w.ROOT/'research/berber091/donors.json',w.HERE/'uv-donors.json')
    if (w.OUT/'inventory.json.gz').exists():
        recipes=[{'path':r['path'],'sha256':r['sha256']} for r in w.read(w.OUT/'inventory.json.gz') if Path(r['path']).suffix.lower() in ('.py','.json') and r['bytes']<2_000_000]
        w.save(w.HERE/'recipes.json.gz',recipes)

def prepare():
    rows=w.read(w.OUT/'inventory.json.gz');tracked=set(w.read(w.OUT/'tracked-before.json')['tracked'])
    byhash=collections.defaultdict(list)
    for r in rows:byhash[r['sha256']].append(r)
    audit=w.read(w.OUT/'blender-dependencies.json');assert audit['complete'] and not any('error' in r for r in audit['files'])
    referenced={str(Path(i['resolved']).resolve()).lower() for r in audit['files'] for i in r.get('images',[])+r.get('libraries',[])}
    # Repair seven pre-existing moved-cache paths without rewriting any scene.
    fixes=[]
    for r in audit['files']:
        for i in r.get('images',[])+r.get('libraries',[]):
            target=Path(i['resolved']).resolve()
            if target.exists():continue
            rel=target.relative_to(w.EXTERNAL/'output')
            moved=w.EXTERNAL/'output/discoveries'/rel
            assert moved.is_file(),str(target)
            copy_checked(moved,w.safe_target(target));fixes.append({'path':str(target),'source':str(moved),'sha256':w.sha(target)})
    w.save(w.OUT/'repaired-source-paths.json',fixes)
    # One latest release + one rollback. Only recognizable historical delivery
    # pairs are retired; donor/cook/source archives remain inputs until proven.
    retire=[]
    for r in rows:
        p=Path(r['path']);rel=r['relative'].lower()
        if p.is_relative_to(w.EXTERNAL/'output') and p.parent.name.startswith(('berber_update_','berber_dark_age_music_test_')) and p.parent!=w.BASE.parent:
            if p.name.lower().startswith('berber-') and p.suffix.lower()=='.zip':retire.append(dict(r,reason='superseded playable delivery'))
            elif p.name=='Berber_future_kingdom.sga':retire.append(dict(r,reason='superseded release archive; current resources frozen in 1.0.4'))
    retired={r['path'] for r in retire}
    selected=[]
    for r in rows:
        p=Path(r['path']);parts={s.lower() for s in p.parts}
        if r['path'] in retired or p.is_relative_to(w.ROOT/'.git') or p.is_relative_to(w.INPUTS):continue
        if r['scope']=='project' and r['relative'] in tracked:continue
        if str(p).lower() in referenced:continue
        if p.suffix.lower() in ('.py','.scar','.xml','.lua','.blend','.png','.jpg','.jpeg','.flac','.mp3'):continue
        kind=None
        if p.suffix.lower() in ('.blend1','.blend2') and any(Path(other['path']).suffix.lower()=='.blend' for other in byhash[r['sha256']]):kind='byte-identical Blender backup'
        elif p.suffix.lower()=='.json' and r['bytes']>1_000_000 and ('projection' in p.name.lower() or 'decoded' in p.name.lower()):kind='lossless decoded/projection input'
        elif r['bytes']>=4096 and len(byhash[r['sha256']])>1 and p.is_relative_to(w.EXTERNAL/'output') and p.parent!=w.BASE.parent:
            # Redundant outputs become content-addressed, recoverable inputs.
            kind='lossless deduplicated rebuild input'
        elif p.suffix.lower().startswith('.blend'):
            # Kept loose until source ownership is proven.
            continue
        if kind:
            category='decoded' if 'decoded' in p.name.lower() else 'projection' if 'projection' in p.name.lower() else 'backup' if p.suffix.lower().startswith('.blend') else 'duplicate_cache'
            selected.append(dict(r,reason=kind,kind=category))
    # Already bundled historical input bytes are migrated to the same current
    # store. The retired Test1 SGA is intentionally excluded under latest-only.
    old=w.read(w.ROOT/'research/development_cleanup_100/source-index.json')
    oldrows=[r for r in old['files'] if r['kind']!='retired_test']
    bundle=w.INPUTS/'source-blobs.zip';assert not bundle.exists();bundle.parent.mkdir(parents=True,exist_ok=True)
    unique={};entries=[]
    with zipfile.ZipFile(old['bundle']) as original,zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        for r in oldrows:
            h=r['sha256']
            if h not in unique:
                raw=original.read(r['member']);assert w.digest(raw)==h;z.writestr(h,raw);unique[h]=len(raw)
            entries.append(dict(r,member=h,reason='migrated lossless source input'))
        for i,r in enumerate(selected):
            p=Path(r['path']);h=r['sha256'];assert w.sha(p)==h
            if h not in unique:z.write(p,h);unique[h]=r['bytes']
            entries.append(dict(r,member=h))
            if i%500==0:print('CANONICAL_INPUT',i,len(selected),flush=True)
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        for h,n in unique.items():
            raw=z.read(h);assert len(raw)==n and w.digest(raw)==h
    # Store portable scope/relative paths as well as original paths for exact
    # recipe restoration. Current authoring does not import historical recipes.
    index={'schema':'berber-current-inputs/v1','bundle':str(bundle),'bundle_sha256':w.sha(bundle),'files':entries}
    w.save(w.HERE/'source-index.json.gz',index)
    w.save(w.OUT/'input-bundle-verification.json',{'status':'passed','unique_blobs':len(unique),'original_bytes':sum(unique.values()),'bundle_bytes':bundle.stat().st_size,'bundle_sha256':index['bundle_sha256'],'all_blobs_decoded_and_sha256_checked':True})
    # Old bundle now has a verified current replacement, including all entries
    # except the deliberately retired test archive.
    oldbundle=Path(old['bundle']);oldrow=next(r for r in rows if r['path']==str(oldbundle))
    retire.append(dict(oldrow,reason='replaced by verified current content store; obsolete test archive omitted'))
    # Keep only one physical copy of a selected hash when a loose current input
    # exists; all selected paths remain restorably indexed in the bundle.
    w.save(w.OUT/'cleanup-candidates.json.gz',{'retire':retire,'bundled':selected,'source_bundle_sha256':index['bundle_sha256']})
    migrate_tools()
    print('PREPARED',len(selected),'bundled paths;',sum(r['bytes'] for r in retire),'obsolete delivery/bundle bytes',flush=True)
if __name__=='__main__':prepare()
