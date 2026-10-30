"""Maintained Berber workspace: inventory, lossless inputs, exact releases, safe cleanup.

No historical Python imports. Installed Garrison tools and the compatible installed
SGA reader are toolchain dependencies, never payloads copied into the release.
"""
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,collections,gzip,hashlib,json,os,shutil,stat,subprocess,sys,warnings,zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
EXTERNAL=Path(os.environ.get('BERBER_STORAGE','F:/aoe_4_temp/Berber_future_kingdom_ai_20261014'))
OUT=EXTERNAL/'output/berber_update_1_0_5'
INPUTS=EXTERNAL/'rebuild_inputs/current'
BASE=EXTERNAL/'output/berber_update_1_0_4/Berber_future_kingdom.sga'
ROLLBACK=BASE.with_name('Berber-1.0.4.zip')
BASE_SHA='55629909581fd0035a141f212e38274d3e1f7f185fecffed635b821e2b7204a6'
ROLLBACK_SHA='8b932f0c9a54f23e140be2a9e03d59f87ccd24e92c13ac7f971e72a4ff78a5ad'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
ARCH=EXT/'bin/sga-archiver.exe'
READER=Path('E:/age of empires 4 mods/07_Subscribed_Mods/Subscribed_Mods/Current/subscribed_mods/.aoe4-sga-v10-runtime')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.suffix=='.gz':
        with gzip.open(path,'wt',encoding='utf8') as f:json.dump(data,f)
    else:path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def read(path):
    if str(path).endswith('.gz'):
        with gzip.open(path,'rt',encoding='utf8') as f:return json.load(f)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def run(*args):
    p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace',env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
    if p.returncode:raise RuntimeError(p.stdout[-3000:]+p.stderr[-3000:])
    return p.stdout
def linked(p):return bool(p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
def safe_target(path,roots=None):
    p=Path(os.path.abspath(path));roots=[Path(os.path.abspath(r)) for r in (roots or [ROOT,EXTERNAL])]
    if not any(p!=r and p.is_relative_to(r) for r in roots):raise ValueError('Outside owned scope: '+str(p))
    if any(s.lower()=='.git' for s in p.parts):raise ValueError('Git is protected from source cleanup')
    for q in (p,*p.parents):
        if q.exists() and linked(q):raise ValueError('Reparse path: '+str(q))
    return p
def member_name(value):
    value=value.replace('\\','/');p=PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or ':' in value or not p.parts:raise ValueError('Unsafe member '+value)
    return p.as_posix()
def verify_cleanup_candidate(row,roots=None,hash_bytes=True):
    p=safe_target(row['path'],roots)
    s=p.stat()
    if s.st_size!=row['bytes']:raise ValueError('Cleanup input changed: '+str(p))
    if hash_bytes:
        if sha(p)!=row['sha256']:raise ValueError('Cleanup input changed: '+str(p))
    elif 'mtime_ns' not in row or s.st_mtime_ns!=row['mtime_ns']:
        raise ValueError('Input changed since its verified SHA inventory: '+str(p))
    if p.stat().st_nlink!=1:raise ValueError('Shared file link; inspect before deletion: '+str(p))
    return p
def restore_one(z,member,dest,expected):
    dest=Path(dest)
    if dest.exists():raise FileExistsError(dest)
    raw=z.read(member)
    if digest(raw)!=expected:raise ValueError('Restore hash mismatch')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(raw)
    return len(raw)
def source_bundle(index):
    current=INPUTS/'source-blobs.zip'
    path=current if current.is_file() else Path(index['bundle'])
    if sha(path)!=index['bundle_sha256']:raise ValueError('Canonical source bundle changed')
    return path
def indexed_path(row):
    base=ROOT if row['scope']=='project' else EXTERNAL
    return base/member_name(row['relative'])
def restore_inputs(path=None,destination=None):
    index=read(HERE/'source-index.json.gz');archive=source_bundle(index)
    requested=Path(path).resolve() if path else None
    # Index paths are inventoried physical paths. Normalize lexically rather
    # than performing filesystem resolution for every archived missing file.
    rows=[r for r in index['files'] if requested is None or any(p==requested or p.is_relative_to(requested) for p in (Path(os.path.abspath(r['path'])),Path(os.path.abspath(indexed_path(r)))))]
    if path and not rows:raise FileNotFoundError(path)
    if destination:
        destination=Path(destination).absolute()
        if destination.exists():raise FileExistsError(destination)
        destination.mkdir(parents=True)
    count=0
    with zipfile.ZipFile(archive) as z:
        for row in rows:
            target=(destination/row['scope']/member_name(row['relative'])) if destination else indexed_path(row)
            safe_target(target,[destination] if destination else None)
            if target.is_file():
                if sha(target)!=row['sha256']:raise FileExistsError('Edited input protected: '+str(target))
                continue
            restore_one(z,row['member'],target,row['sha256']);count+=1
    return count
def walk(root):
    stack=[Path(root)]
    while stack:
        folder=stack.pop()
        with os.scandir(folder) as entries:
            for e in entries:
                p=Path(e.path)
                if e.stat(follow_symlinks=False).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:continue
                if e.is_dir(follow_symlinks=False):stack.append(p)
                elif e.is_file(follow_symlinks=False):yield p
def validate_inputs():
    index=read(HERE/'source-index.json.gz');archive=source_bundle(index)
    expected={r['member']:r['sha256'] for r in index['files']}
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        assert set(z.namelist())==set(expected)
        for n,(member,h) in enumerate(expected.items()):
            with z.open(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
            if n%3000==0:print('VALIDATED_BLOBS',n,len(expected),flush=True)
    missing=[]
    for row in read(HERE/'editable-masters.json.gz')['files']:
        master=Path(row['path'])
        assert master.is_file() or any(r['path']==row['path'] and r['sha256']==row['sha256'] for r in index['files']),str(master)
        missing.extend(d['resolved'] for d in row['dependencies'] if not Path(d['resolved']).is_file())
    assert not missing,missing
    assert sha(BASE)==BASE_SHA and sha(ROLLBACK)==ROLLBACK_SHA
    report={'status':'passed','bundle_sha256':index['bundle_sha256'],'all_unique_blobs_decoded_sha256_checked':len(expected),'all_indexed_master_dependencies_present':True,'baseline_and_rollback_hashes_verified':True}
    save(OUT/'input-validation.json',report);print('INPUTS_VALIDATED',len(expected),flush=True)
def totals():
    result={}
    for root in (ROOT,EXTERNAL):
        data=collections.Counter()
        stack=[Path(root)]
        while stack:
            folder=stack.pop()
            with os.scandir(folder) as entries:
                for e in entries:
                    s=e.stat(follow_symlinks=False)
                    if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:continue
                    p=Path(e.path)
                    if e.is_dir(follow_symlinks=False):stack.append(p);continue
                    rel=p.relative_to(root);data['total']+=s.st_size
                    data[rel.parts[0] if len(rel.parts)>1 else '(root)']+=s.st_size
        result[str(root)]=dict(data)
    return result
def git_snapshot(label):
    gitdir=Path(run('git','rev-parse','--git-common-dir').strip()).resolve()
    assert gitdir==ROOT/'.git'
    alternates=gitdir/'objects/info/alternates'
    assert not alternates.exists(),'Inspect alternate object stores before repack'
    metadata={}
    for p in walk(gitdir):
        rel=p.relative_to(gitdir)
        if rel.parts[0]=='objects' or p.name in ('index.lock','gc.log'):continue
        metadata[rel.as_posix()]=sha(p)
    objects=sorted(run('git','cat-file','--batch-all-objects','--batch-check=%(objectname)').splitlines())
    save(OUT/('git-'+label+'.json.gz'),{'metadata':metadata,'objects':objects,'worktrees':run('git','worktree','list','--porcelain'),'gitdir':str(gitdir),'stage':run('git','ls-files','--stage')})
    print('GIT_SNAPSHOT',label,len(objects),flush=True)
def inventory():
    assert sha(BASE)==BASE_SHA and sha(ROLLBACK)==ROLLBACK_SHA
    OUT.mkdir(parents=True,exist_ok=True)
    if not (OUT/'storage-before.json').exists():save(OUT/'storage-before.json',totals())
    rows=[];links=[]
    for root in (ROOT,EXTERNAL):
        stack=[root]
        while stack:
            folder=stack.pop()
            with os.scandir(folder) as entries:
                for e in entries:
                    p=Path(e.path);s=e.stat(follow_symlinks=False)
                    if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                        links.append({'path':str(p),'target':os.readlink(p)});continue
                    if e.is_dir(follow_symlinks=False):
                        if p!=ROOT/'.git' and p!=OUT:stack.append(p)
                        continue
                    rows.append({'path':str(p),'scope':'project' if root==ROOT else 'external','relative':p.relative_to(root).as_posix(),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'links':s.st_nlink})
    save(OUT/'inventory-metadata.json.gz',rows)
    journal=OUT/'inventory-hashes.jsonl';cached={}
    if journal.exists():
        for line in journal.read_text().splitlines():
            try:
                row=json.loads(line);cached[row['path']]=row
            except ValueError:pass
    done=[];pending=[]
    for r in rows:
        old=cached.get(r['path'])
        if old and (old['bytes'],old['mtime_ns'])==(r['bytes'],r['mtime_ns']):done.append(old)
        else:pending.append(r)
    def hashed(r):r['sha256']=sha(r['path']);return r
    print('HASH_INVENTORY',len(rows),'resume',len(done),flush=True)
    with journal.open('a',encoding='utf8') as f,ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(hashed,r) for r in pending]
        for future in as_completed(futures):
            r=future.result();done.append(r);f.write(json.dumps(r)+'\n')
            if len(done)%100==0:f.flush()
            if len(done)%5000==0:print('HASHED',len(done),len(rows),flush=True)
    rows=done
    save(OUT/'inventory.json.gz',rows);save(OUT/'junctions.json',links)
    if not (OUT/'git-before.json.gz').exists():git_snapshot('before')
    save(OUT/'tracked-before.json',{'status':run('git','status','--porcelain=v1'),'tracked':run('git','ls-files').splitlines()})
    print('INVENTORY',len(rows),sum(r['bytes'] for r in rows),flush=True)
def archive_hashes(archive):
    import platform
    platform.system=lambda:'Windows'
    sys.path[:0]=[str(READER/'site-packages'),str(READER/'SGA-V10/src')]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        from relic.sga.v10 import EssenceFSHandler
        from relic.sga.core.definitions import Version
    with Path(archive).open('rb') as f:
        h=f.read(12);f.seek(0);assert h[:8]==b'_ARCHIVE'
        EssenceFSHandler.version=Version(int.from_bytes(h[8:10],'little'),int.from_bytes(h[10:12],'little'))
        fs=EssenceFSHandler.read(f)
        return {n.lstrip('/').replace('\\','/'):digest(fs.readbytes(n)) for n in fs.walk.files()}
def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist();assert len(names)==len(set(names))
        manifests=[n for n in names if PurePosixPath(n).name.lower()=='garrison.json'];assert len(manifests)==1
        manifest=json.loads(z.read(manifests[0]));members={};all_hashes={}
        # Reading each stream to EOF verifies zipfile's CRC while calculating
        # SHA256, avoiding a second complete decompression of the game archive.
        for name in names:
            if name.endswith('/'):continue
            with z.open(name) as f:all_hashes[name]=hashlib.file_digest(f,'sha256').hexdigest()
        for m in manifest['members']:
            n=str(PurePosixPath(manifests[0]).parent/m['path'])
            h=all_hashes[n]
            assert h==m['sha256'];members[n]=h
        return {'zip_sha256':sha(path),'bytes':Path(path).stat().st_size,'version':manifest['details']['version'],'members':members,'crc':'passed'}
def package(destination=None):
    dest=Path(destination) if destination else OUT
    dest.mkdir(parents=True,exist_ok=True)
    assert sha(BASE)==BASE_SHA and sha(ROLLBACK)==ROLLBACK_SHA
    final=dest/'Berber-1.0.5.zip';assert not final.exists()
    with zipfile.ZipFile(ROLLBACK) as src:
        manifest=json.loads(src.read('garrison.json'))
        assert manifest['details']['version']=='1.0.4'
        manifest['details']['version']='1.0.5';manifest['details']['updated']='2026-10-19'
        manifest['details']['summary']='Consolidated development workspace; all Berber 1.0.4 gameplay, art, voices, music and native AI preserved.'
        manifest['details']['changelog']='Storage and rebuild workflow consolidation. Game archive unchanged from 1.0.4. Native acceptance remains pending.'
        note='Berber 1.0.5\nImport this ZIP in Garrison and select both Berber tuning pack and game mode.\nAll 8,529 game resources are identical to 1.0.4. Native acceptance remains pending.\nDevelopment inputs and rebuild instructions are retained separately in the author workspace.\n'
        with zipfile.ZipFile(final,'x',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as target:
            for name in src.namelist():
                if name=='garrison.json':target.writestr(name,json.dumps(manifest,indent=2)+'\n')
                elif name in ('START-HERE.txt','RELEASE_NOTES.md'):target.writestr(name,note)
                elif name.endswith('.sga'):
                    with BASE.open('rb') as f,target.open(name,'w',force_zip64=True) as o:shutil.copyfileobj(f,o,1024*1024)
                else:
                    with src.open(name) as f,target.open(name,'w',force_zip64=True) as o:shutil.copyfileobj(f,o,1024*1024)
    result=verify_zip(final);assert result['version']=='1.0.5' and set(result['members'].values())=={BASE_SHA}
    save(dest/'release-validation.json',dict(result,status='offline_verified_native_pending',sga_sha256=BASE_SHA,unchanged_resources=8529))
    print('PACKAGE_VERIFIED',result['bytes'],result['zip_sha256'],flush=True)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['inventory','package','verify','restore','restore-extra','export-inputs','storage','validate-inputs']);p.add_argument('--destination');p.add_argument('--path');a=p.parse_args()
    if a.command=='inventory':inventory()
    elif a.command=='package':package(a.destination)
    elif a.command=='verify':print(json.dumps(verify_zip((Path(a.destination) if a.destination else OUT)/'Berber-1.0.5.zip'),indent=2))
    elif a.command=='storage':print(json.dumps(totals(),indent=2))
    elif a.command=='validate-inputs':validate_inputs()
    elif a.command=='restore':print('Restored',restore_inputs(a.path))
    elif a.command=='export-inputs':print('Exported',restore_inputs(destination=a.destination))
    elif a.command=='restore-extra':
        record=read(HERE/'retired-package-inputs.json.gz');archive=INPUTS/'retired-package-inputs.zip'
        assert sha(archive)==record['sha256'];assert any(r['sha256']==a.path for r in record['files'])
        target=Path(a.destination).absolute();safe_target(target,[target.parent])
        with zipfile.ZipFile(archive) as z:restore_one(z,a.path,target,a.path)
if __name__=='__main__':main()
