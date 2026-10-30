"""Inventory-only deletion plan; PowerShell performs checked workspace mutations."""
import os,json,hashlib,zipfile,collections,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';AUDIT=OUT/'_cleanup';AUDIT.mkdir(exist_ok=True)
ACTIVE={'berber_update_0_2_0','berber_update_0_2_1','berber_update_0_2_2','berber_update_0_2_3','berber_update_0_2_4','buildings_batch','tribal_tent','discoveries','releases','_cleanup'}
PROTECTED=('berber_update_0_2_2/stock/','berber_update_0_2_2/payload/','berber_update_0_2_4/')
TEXT={'.json','.jsonl','.log','.txt','.md','.csv','.lua','.scar','.py','.xml','.rdo','.material','.rgotemplate','.toml','.html'}
BINARY={'.sga','.wav','.wem','.spd','.rrtex','.rrgeom','.rgm','.rgo','.bin','.dll','.exe','.pyd','.fbx','.dds'}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def is_reparse(p):return bool(getattr(p.lstat(),'st_file_attributes',0)&0x400)
def paths(base):
    for d,dirs,files in os.walk(base):
        dirs[:]=[n for n in dirs if not is_reparse(Path(d)/n)]
        for n in files:
            p=Path(d)/n
            if not is_reparse(p):yield p
files=[p for p in paths(OUT) if not p.is_relative_to(AUDIT) and not p.is_relative_to(OUT/'berber_update_0_2_4')]
snapshot=AUDIT/'HISTORICAL_METADATA.zip'
if '--resume' not in sys.argv:
    with zipfile.ZipFile(snapshot,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:
            if p.suffix.lower() in TEXT:z.write(p,p.relative_to(OUT).as_posix())
else:
    with zipfile.ZipFile(snapshot) as z:assert len(z.namelist())>1000
print('Metadata snapshot retained',flush=True)
delete_dirs=[]
for d,dirs,_ in os.walk(OUT):
    here=Path(d);rel=here.relative_to(OUT).as_posix()+'/'
    if here==AUDIT or any(rel.startswith(p) for p in PROTECTED):dirs[:]=[];continue
    for name in list(dirs):
        p=here/name;low=name.lower();part=p.relative_to(OUT).as_posix()+'/'
        if is_reparse(p) or any(part.startswith(q) or q.startswith(part) for q in PROTECTED):continue
        disposable=(low in {'intermediate','cache','__pycache__','package-candidates','donor-final-readbacks','stamp-readbacks'} or 'readback' in low or (low=='cook' and here.name.lower()=='dist'))
        if disposable:delete_dirs.append(p);dirs.remove(name)
delete_files=[];reasons={}
pruned_prefixes=tuple(str(p)+os.sep for p in delete_dirs)
for p in files:
    if str(p).startswith(pruned_prefixes):continue
    rel=p.relative_to(OUT).as_posix()
    if any(rel.startswith(q) for q in PROTECTED):continue
    if p.name.lower() in {'with-house-media.sga','with-art.sga'}:
        delete_files.append(p);reasons[str(p)]='temporary archive assembly; complete release retained'
# Compare generated binary copies with authoritative sources first, then keep
# one remaining copy per content hash. Required release packages/payloads stay.
initial_deleted=set(delete_files)
remaining=[p for p in files if p not in initial_deleted and not str(p).startswith(pruned_prefixes)]
sizes=collections.defaultdict(list)
for p in remaining:
    if p.suffix.lower() in BINARY:sizes[p.stat().st_size].append(p)
authoritative=collections.defaultdict(list)
for folder in ['art','assets','new_music','new_voices']:
    for p in paths(ROOT/folder):
        if p.suffix.lower() in BINARY and p.stat().st_size in sizes:authoritative[p.stat().st_size].append(p)
def protected(p):
    rel=p.relative_to(OUT).as_posix();return any(rel.startswith(q) for q in PROTECTED) or '/package/' in rel or '/rollback/' in rel or p.parent==OUT or p.suffix.lower()=='.zip'
duplicates=[]
print('Hashing candidate duplicate binaries',len(remaining),'files outside pruned directories',flush=True)
for size,group in sizes.items():
    if len(group)+len(authoritative[size])<2:continue
    owners={}
    for p in authoritative[size]:owners.setdefault(sha(p),p)
    for p in sorted(group,key=lambda p:(not protected(p),len(str(p)))):
        digest=sha(p)
        if digest in owners and not protected(p):
            delete_files.append(p);reasons[str(p)]='byte-identical generated binary copy';duplicates.append({'removed':str(p),'retained':str(owners[digest]),'sha256':digest,'bytes':size})
        else:owners.setdefault(digest,p)
moves=[]
for p in OUT.iterdir():
    if p.is_dir() and p.name not in ACTIVE:moves.append({'from':str(p),'to':str(OUT/'discoveries'/p.name)})
    elif p.is_file():
        if p.suffix.lower() in {'.md','.txt','.json','.log'}:moves.append({'from':str(p),'to':str(OUT/'discoveries'/'notes'/p.name)})
        elif p.suffix.lower() in {'.zip','.sga'}:moves.append({'from':str(p),'to':str(OUT/'releases'/'historical'/p.name)})
deleted_set=set(delete_files)
removed=[p for p in files if p in deleted_set or str(p).startswith(pruned_prefixes)]
manifest={'schema':'berber.output-cleanup/v1','root':str(OUT),'metadata_snapshot':str(snapshot),'before_files':len(files),'before_bytes':sum(p.stat().st_size for p in files),'delete_directories':[str(p) for p in delete_dirs],'delete_files':[str(p) for p in delete_files],'reasons':reasons,'moves':moves,'duplicate_proof':duplicates,'planned_delete_files':len(removed),'planned_delete_bytes':sum(p.stat().st_size for p in removed),'preserved_active_paths':sorted(ACTIVE),'protected_fixture_paths':PROTECTED}
(AUDIT/'plan.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:manifest[k] for k in ['before_files','before_bytes','planned_delete_files','planned_delete_bytes']}));print('directories to prune',len(delete_dirs),'verified duplicate binaries',len(duplicates),'entries to relocate',len(moves))
