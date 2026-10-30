"""Read-only, physical-path Berber inventory; never traverse reparse points."""
from pathlib import Path
import collections,gzip,hashlib,json,os,stat,time,faulthandler
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
EXTERNAL=Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014')
SCOPES=[ROOT,EXTERNAL]
OUTSIDE=[Path('E:/age of empires 4 mods/01_Custom_Civilizations/Berber_Future_Kingdom'),ROOT.parent/'output',Path('F:/aoe_4_temp/b031siege'),Path('F:/aoe_4_temp/berber_040_university_donors'),Path('F:/aoe_4_temp/berber_040_wonder_envelope')]
REPARSE=stat.FILE_ATTRIBUTE_REPARSE_POINT

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def save(p,value):
    Path(p).write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')

def linked(p):return bool(p.lstat().st_file_attributes & REPARSE)

def walk(base):
    if not base.exists():return
    if linked(base):return
    pending=[base]
    while pending:
        current=pending.pop()
        with os.scandir(current) as entries:
            for e in entries:
                if e.name=='.git':continue
                info=e.stat(follow_symlinks=False)
                if info.st_file_attributes & REPARSE:continue
                if e.is_dir(follow_symlinks=False):pending.append(Path(e.path))
                elif e.is_file(follow_symlinks=False):yield Path(e.path)

def main():
    faulthandler.dump_traceback_later(45,repeat=True)
    REPORT.mkdir(exist_ok=True)
    rows=[];groups=collections.defaultdict(lambda:[0,0]);archives=[]
    def entry(p):
        s=p.stat();return {'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'links':s.st_nlink,'sha256':sha(p)}
    for base in SCOPES:
        print('SCANNING',base,flush=True)
        paths=[p for p in walk(base) if not p.is_relative_to(REPORT)]
        print('FOUND',len(paths),flush=True)
        with ThreadPoolExecutor(max_workers=24) as pool:
          for r in pool.map(entry,paths):
            p=Path(r['path']);sbytes=r['bytes']
            rows.append(r);rel=p.relative_to(base);key=str(base.drive)+'/'+'/'.join(rel.parts[:2]);groups[key][0]+=sbytes;groups[key][1]+=1
            if p.suffix.lower() in ('.zip','.sga'):archives.append(r)
            if len(rows)%1000==0:print('HASHED',len(rows),str(p),flush=True)
    with gzip.open(REPORT/'inventory.json.gz','wt',encoding='utf8') as f:json.dump(rows,f)
    save(REPORT/'archive-inventory.json',archives)
    save(REPORT/'scope-before.json',{'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'by_drive':{d:sum(r['bytes'] for r in rows if Path(r['path']).drive==d) for d in ('E:','F:')},'largest':sorted([[v[0],v[1],k] for k,v in groups.items()],reverse=True)[:50],'git':'excluded, preserved'})
    outside=[]
    for base in OUTSIDE:
        files=[]
        for p in walk(base):
            s=p.stat();files.append({'path':str(p),'bytes':s.st_size,'sha256':sha(p)})
        outside.append({'root':str(base),'files':files,'bytes':sum(r['bytes'] for r in files),'action':'inspection only; no outside deletion authorized by this pass'})
    with gzip.open(REPORT/'outside-inventory.json.gz','wt',encoding='utf8') as f:json.dump(outside,f)
    print('INVENTORY_COMPLETE',len(rows),sum(r['bytes'] for r in rows),flush=True)

if __name__=='__main__':main()
