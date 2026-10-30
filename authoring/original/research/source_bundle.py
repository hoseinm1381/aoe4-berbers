"""Lossless historical source reads and explicitly scoped restore.

python -B research/source_bundle.py --root PHYSICAL_DIRECTORY
python -B research/source_bundle.py --run research/legacy_recipe.py [arguments]
The legacy launcher restores bundled non-backup inputs before running old recipes.
It never overwrites an existing file, including a user's edited copy.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,os,runpy,stat,sys,zipfile

ROOT=Path(__file__).resolve().parents[1]
EXTERNAL=Path(os.environ.get('BERBER_STORAGE','F:/aoe_4_temp/Berber_future_kingdom_ai_20261014'))
ROOTS=[ROOT,EXTERNAL]
INDEX=ROOT/'research/development_cleanup_100/source-index.json'

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load():
 canonical=ROOT/'tools/berber105/source-index.json.gz'
 if canonical.exists():
  with gzip.open(canonical,'rt',encoding='utf8') as f:record=json.load(f)
  record['bundle']=str(EXTERNAL/'rebuild_inputs/current/source-blobs.zip')
  return record
 return json.loads(INDEX.read_text(encoding='utf8')) if INDEX.exists() else {'files':[]}

def safe_target(p):
 p=Path(p).absolute()
 if not any(p.is_relative_to(r.absolute()) and p!=r for r in ROOTS):raise ValueError(f'Outside allowed roots: {p}')
 for parent in (p,*p.parents):
  if parent.exists() and parent.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ValueError(f'Reparse destination: {parent}')
 return p

def payload(z,row):
 raw=z.read(row['member'])
 if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Corrupt bundled source: '+row['path'])
 return raw

def read_bytes(path):
 p=Path(path)
 if p.exists():return p.read_bytes()
 record=load();resolved=p.resolve()
 row=next((r for r in record['files'] if Path(r['path'])==resolved),None)
 if row is None:raise FileNotFoundError(p)
 with zipfile.ZipFile(record['bundle']) as z:return payload(z,row)

def read_json(path):return json.loads(read_bytes(path).decode('utf-8-sig'))

def size(path):
 p=Path(path)
 if p.exists():return p.stat().st_size
 row=next((r for r in load()['files'] if Path(r['path'])==p.resolve()),None)
 if row is None:raise FileNotFoundError(p)
 return row['bytes']

def export(destination):
 """Export a portable, verified project/external source tree without old drive paths."""
 destination=Path(destination).absolute();record=load()
 if destination.exists():raise FileExistsError('Export destination must be new')
 for p in (destination,*destination.parents):
  if p.exists() and p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ValueError('Linked export parent')
 if sha(record['bundle'])!=record['bundle_sha256']:raise ValueError('Source bundle SHA256 differs')
 targets=[]
 for row in record['files']:
  rel=Path(row['relative']);scope=row['scope']
  if rel.is_absolute() or '..' in rel.parts or ':' in str(rel) or scope not in ('project','external'):raise ValueError('Invalid portable source path')
  targets.append((destination/scope/rel,row))
 with zipfile.ZipFile(record['bundle']) as z:
  for target,row in targets:
   raw=payload(z,row);target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as f:f.write(raw)
 return len(targets)

def cached_paths(base,pattern,recursive=False):
 """Return live and archived original paths, including missing cached manifests."""
 import fnmatch
 base=Path(base).resolve();paths=set(base.rglob(pattern) if recursive else base.glob(pattern))
 for row in load()['files']:
  p=Path(row['path'])
  if p.is_relative_to(base):
   rel=p.relative_to(base).as_posix()
   if (recursive and fnmatch.fnmatch(p.name,pattern)) or (not recursive and len(p.relative_to(base).parts)==len(pattern.split('/')) and fnmatch.fnmatchcase(rel,pattern)):paths.add(p)
 return sorted(paths)

def restore(root,kind=None):
 root=Path(root).absolute();record=load();rows=[r for r in record['files'] if (Path(r['path'])==root or Path(r['path']).is_relative_to(root)) and (kind is None or r['kind']==kind)]
 if not rows:return 0
 # Check all target paths before opening or restoring anything.
 targets=[(safe_target(r['path']),r) for r in rows]
 if sha(record['bundle'])!=record['bundle_sha256']:raise ValueError('Source bundle SHA256 differs')
 count=0
 with zipfile.ZipFile(record['bundle']) as z:
  for target,row in targets:
   if target.exists():continue
   raw=payload(z,row);target.parent.mkdir(parents=True,exist_ok=True)
   temp=target.with_name(target.name+'.source-restore.tmp')
   if temp.exists():raise FileExistsError(temp)
   try:
    with temp.open('xb') as f:f.write(raw)
    if target.exists():raise FileExistsError(target)
    # Windows rename fails if destination exists, preserving concurrent user edits.
    os.rename(temp,target);count+=1
   finally:
    if temp.exists():temp.unlink()
 return count

def main():
 if '--run' in sys.argv:
  at=sys.argv.index('--run');args=sys.argv[at+1:]
  if not args:raise ValueError('--run requires a Python recipe')
  for root in ROOTS:
   for kind in ('decoded','projection','duplicate_cache','archived_input'):restore(root,kind)
  script=Path(args[0]).resolve()
  if not script.is_relative_to(ROOT):raise ValueError('Recipe must belong to Berber project')
  sys.path.insert(0,str(script.parent));sys.path.insert(0,str(ROOT/'research'));sys.argv=args
  runpy.run_path(str(script),run_name='__main__');return
 parser=argparse.ArgumentParser(description=__doc__);choice=parser.add_mutually_exclusive_group(required=True);choice.add_argument('--root');choice.add_argument('--export');parser.add_argument('--kind');args=parser.parse_args()
 if args.export:print('Exported',export(args.export),'bundled inputs')
 else:print('Restored',restore(args.root,args.kind),'bundled inputs')

if __name__=='__main__':main()
