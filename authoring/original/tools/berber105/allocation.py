"""Measure file allocation separately from file bytes (exFAT has 256KiB clusters)."""
from pathlib import Path
import collections,ctypes,json,os,stat
import workspace as w

def measure(root,cluster,skip_work=True):
    totals=collections.Counter();folders=collections.defaultdict(lambda:collections.Counter());stack=[root]
    while stack:
        folder=stack.pop()
        with os.scandir(folder) as entries:
            for e in entries:
                s=e.stat(follow_symlinks=False)
                if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:continue
                p=Path(e.path)
                if e.is_dir(follow_symlinks=False):
                    if skip_work and p==w.OUT/'work':continue
                    stack.append(p);continue
                allocated=((s.st_size+cluster-1)//cluster)*cluster
                totals['files']+=1;totals['bytes']+=s.st_size;totals['allocated_cluster_bytes']+=allocated
                rel=p.relative_to(root)
                for depth in range(1,min(3,len(rel.parts))):
                    key='/'.join(rel.parts[:depth]);folders[key]['bytes']+=s.st_size;folders[key]['allocated']+=allocated;folders[key]['files']+=1
    return {'root':str(root),'cluster_bytes':cluster,'totals':dict(totals),'largest_folders':sorted([dict(path=k,**v) for k,v in folders.items()],key=lambda r:-r['allocated'])[:30]}
def main():
    rows=w.read(w.OUT/'inventory.json.gz')
    f_before=sum(((r['bytes']+262143)//262144)*262144 for r in rows if r['scope']=='external')
    report={'method':'Allocation rounded by verified volume cluster size; excludes directory metadata, compression/resident NTFS differences, and disposable release/work. Exact exFAT regular-file cluster allocation; NTFS cluster estimate.','volumes':{'E:':{'filesystem':'NTFS','cluster_bytes':4096},'F:':{'filesystem':'exFAT','cluster_bytes':262144}},'initial_inventoried_F_allocated_file_bytes':f_before,'current':[measure(w.ROOT,4096),measure(w.EXTERNAL,262144)]}
    w.save(w.OUT/'allocation-report.json',report)
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
