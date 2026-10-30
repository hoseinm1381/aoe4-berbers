"""Auditable inventory for previous Berber release cleanup; no wildcard deletion."""
import os,json,stat,collections,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).absolute().parents[1]
EXTERNAL=Path(r'F:\aoe_4_temp\Berber_future_kingdom_ai_20261014')
REPORT=ROOT/'research/cleanup_20261016'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def walk(root):
 stack=[str(root)]
 while stack:
  folder=stack.pop()
  with os.scandir(folder) as entries:
   for e in entries:
    s=e.stat(follow_symlinks=False)
    if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
     yield e.path,s.st_size,'link';continue
    if e.is_dir(follow_symlinks=False):
     if e.name not in ('.git',):stack.append(e.path)
    else:yield e.path,s.st_size,'file'
def inventory():
 REPORT.mkdir(exist_ok=True)
 records=[];groups=collections.Counter();links=[]
 for root in (ROOT,EXTERNAL):
  print('SCAN',root,flush=True)
  for p,n,k in walk(root):
   if k=='link':links.append(p);continue
   rel=Path(p).relative_to(root);key=str(root/Path(*rel.parts[:min(3,len(rel.parts)-1)]))
   groups[key]+=n;records.append({'path':p,'bytes':n})
 print('FILES',len(records),'BYTES',sum(r['bytes'] for r in records),flush=True)
 (REPORT/'inventory.json').write_text(json.dumps({'files':records,'links_not_followed':links,'roots':[str(ROOT),str(EXTERNAL)]},indent=1))
 (REPORT/'directory-sizes.json').write_text(json.dumps(groups.most_common(),indent=1))
 for p,n in groups.most_common(35):print(round(n/2**30,3),p,flush=True)
def duplicate_plan():
 """Only byte-identical cache copies, with a retained source for every file."""
 records=json.loads((REPORT/'inventory.json').read_text())['files']
 cache_names={'readback','cook-readback','candidate-readback','garrison-cook-readback','base-readback','binding-readback','decoded-qa','assembly','staging','stage','native-package'}
 protected_ext={'.blend','.blend1','.blend2','.blend3','.py','.ps1','.cmd','.scar','.lua','.csv','.json','.xml','.md','.txt','.log','.png','.jpg','.jpeg','.zip','.wwu','.wproj','.wsettings','.wav','.rgd'}
 def candidate(p):
  p=Path(p);parts=p.parts
  # Restrict to released build outputs; authoring and shared caches remain protected.
  if EXTERNAL/'output' not in p.parents or not any(x.startswith('berber_update_') for x in parts):return False
  if p.suffix.lower() in protected_ext or '.blend' in p.name.lower():return False
  marked=any(x in cache_names or x.startswith('candidate-readback-') for x in parts)
  marked=marked or ('cook' in parts and 'dist' in parts)
  if p.suffix.lower()=='.sga':return marked and p.name in ('donor.sga','grafted.sga')
  return marked
 candidates=[r for r in records if candidate(r['path'])]
 sizes={r['bytes'] for r in candidates};index={};protected_zips=[];zip_checks=[]
 # Validate every retained release ZIP and keep hashes of all members before removal.
 for row in records:
  p=Path(row['path'])
  if p.suffix.lower()!='.zip' or EXTERNAL/'output' not in p.parents:continue
  if not any(x.startswith('berber_update_') for x in p.parts):continue
  if p.parent.name.startswith('berber_update_') or p.parent.name=='READY_TO_IMPORT':protected_zips.append(p)
 previous={r['path']:r for r in json.loads((REPORT/'protected-zips.json').read_text())} if (REPORT/'protected-zips.json').exists() else {}
 for p in protected_zips:
  print('VERIFY ZIP',p.name,flush=True)
  if str(p) in previous and sha(p)==previous[str(p)]['sha256']:
   check=previous[str(p)];zip_checks.append(check)
   with zipfile.ZipFile(p) as z:
    for item in z.infolist():
     digest=check['members'].get(item.filename)
     if digest and item.file_size in sizes:index.setdefault((item.file_size,digest),{'zip':str(p),'member':item.filename,'sha256':digest})
   continue
  members={}
  with zipfile.ZipFile(p) as z:
   if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate ZIP members')
   for item in z.infolist():
    if item.is_dir():continue
    with z.open(item) as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    members[item.filename]=digest
    if item.file_size in sizes:index.setdefault((item.file_size,digest),{'zip':str(p),'member':item.filename,'sha256':digest})
  zip_checks.append({'path':str(p),'sha256':sha(p),'members':members})
 (REPORT/'protected-zips.json').write_text(json.dumps(zip_checks,indent=1))
 # Retained release ZIPs already index compiled assets. Preserve one cache
 # representative for anything absent from them instead of hashing all masters.
 print('INDEXED RETAINED FILES',len(index),flush=True)
 selected=[];retained=[]
 for row in candidates:
  digest=sha(row['path']);key=(row['bytes'],digest)
  if key in index:
   selected.append(dict(row,sha256=digest,restore=index[key]))
  else:
   # Retain one exact representative if no released/authoring source exists.
   index[key]={'file':row['path'],'sha256':digest}
   retained.append(dict(row,reason='Only retained copy or no verified duplicate'))
 plan={'status':'inventoried_not_deleted','files':selected,'retained_unique_candidates':retained,'logical_bytes':sum(r['bytes'] for r in selected),'protected_zip_count':len(zip_checks),'scope':'Exact duplicate build/cache files only. All audio WAVs, Blender files, editable sources, release ZIPs and authoritative SGAs protected.'}
 (REPORT/'deletion-plan.json').write_text(json.dumps(plan,indent=1))
 print('REMOVABLE',len(selected),'BYTES',plan['logical_bytes'],flush=True)
 summary=collections.Counter()
 for row in selected:
  p=Path(row['path']);summary[str(Path(*p.parts[:6]))]+=row['bytes']
 print(summary,flush=True)
def apply_duplicates():
 plan=json.loads((REPORT/'deletion-plan.json').read_text());selected=plan['files']
 removed_paths={r['path'].lower() for r in selected}
 checked_parents=set();checked_sources={}
 def retained_hash(path):
  if path not in checked_sources:checked_sources[path]=sha(path)
  return checked_sources[path]
 # Preflight every target and retained dependency before the first deletion.
 for number,row in enumerate(selected):
  p=Path(row['path'])
  if Path(os.path.abspath(p))!=p or EXTERNAL/'output' not in p.parents:raise ValueError('Containment failure')
  for node in (p,*p.parents):
   if node==EXTERNAL:break
   if node in checked_parents:break
   if node.is_junction() or node.is_symlink():raise ValueError('Reparse point refused')
   if node!=p:checked_parents.add(node)
  if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('Target changed')
  source=row['restore']
  if 'file' in source:
   if source['file'].lower() in removed_paths or retained_hash(source['file'])!=row['sha256']:raise ValueError('Source missing or also selected')
  elif 'decoder' in source:
   if retained_hash(source['decoder'])!=source['decoder_sha256'] or retained_hash(source['wem'])!=source['wem_sha256']:raise ValueError('Decoder input differs')
  if number%2000==0:print('PREFLIGHT',number,'/',len(selected),flush=True)
 for z in json.loads((REPORT/'protected-zips.json').read_text()):
  if sha(z['path'])!=z['sha256']:raise ValueError('ZIP changed before cleanup')
 result={'status':'in_progress','removed':[],'logical_reclaimed_by_drive':{},'physical_reclaimed_lower_bound_by_drive':{}}
 try:
  for number,row in enumerate(selected):
   p=Path(row['path']);s=p.stat();p.unlink();result['removed'].append(row['path'])
   drive=p.drive
   result['logical_reclaimed_by_drive'][drive]=result['logical_reclaimed_by_drive'].get(drive,0)+row['bytes']
   if s.st_nlink==1:result['physical_reclaimed_lower_bound_by_drive'][drive]=result['physical_reclaimed_lower_bound_by_drive'].get(drive,0)+row['bytes']
   if number%2000==0:print('REMOVED',number,'/',len(selected),flush=True)
  for z in json.loads((REPORT/'protected-zips.json').read_text()):
   if sha(z['path'])!=z['sha256']:raise ValueError('ZIP changed after cleanup')
   with zipfile.ZipFile(z['path']) as archive:
    if archive.testzip():raise ValueError('ZIP CRC failed after cleanup')
  result['status']='passed'
 finally:
  (REPORT/'cleanup-result.json').write_text(json.dumps(result,indent=1))
 print(json.dumps({k:v for k,v in result.items() if k!='removed'}),flush=True)
if __name__=='__main__':
 import sys
 {'inventory':inventory,'plan':duplicate_plan,'apply':apply_duplicates}[sys.argv[1] if len(sys.argv)>1 else 'inventory']()
