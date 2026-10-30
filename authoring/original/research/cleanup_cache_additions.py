"""Additional exact duplicates: cached image copies and pilot intermediates."""
import collections,json,zipfile
from pathlib import Path
from cleanup_previous_versions import REPORT,EXTERNAL,sha
def prepare():
 inventory=json.loads((REPORT/'inventory.json').read_text())['files'];checks=json.loads((REPORT/'protected-zips.json').read_text());plan=json.loads((REPORT/'deletion-plan.json').read_text())
 existing={r['path'] for r in plan['files']};rows=[]
 for row in inventory:
  p=Path(row['path']);parts=p.parts
  if EXTERNAL/'output' not in p.parents or not any(x.startswith('berber_update_') for x in parts):continue
  cached=any(x.endswith('readback') or x.startswith('candidate-readback-') for x in parts) or ('cook' in parts and 'dist' in parts)
  image=p.suffix.lower() in ('.png','.jpg','.jpeg') and cached
  intermediate=p.suffix.lower()=='.sga' and (p.name.startswith('attrib-pilot') or p.name=='attrib-candidate.sga')
  if (image or intermediate) and row['path'] not in existing:rows.append(row)
 sizes={r['bytes'] for r in rows};index={}
 for check in checks:
  with zipfile.ZipFile(check['path']) as z:
   for info in z.infolist():
    if info.file_size in sizes and info.filename in check['members']:
     digest=check['members'][info.filename];index[(info.file_size,digest)]={'zip':check['path'],'member':info.filename,'sha256':digest}
 selected=[]
 for row in rows:
  digest=sha(row['path']);key=(row['bytes'],digest)
  if key in index:selected.append(dict(row,sha256=digest,restore=index[key]))
  else:index[key]={'file':row['path'],'sha256':digest}
 plan['files'].extend(selected);plan['logical_bytes']=sum(r['bytes'] for r in plan['files'])
 plan['additional_scope']='Exact duplicate cached images and pilot attrib intermediates. Original images, models and Blender backups untouched.'
 (REPORT/'deletion-plan.json').write_text(json.dumps(plan,indent=1))
 print('ADDITIONAL_DUPLICATES',len(selected),sum(r['bytes'] for r in selected),'TOTAL',plan['logical_bytes'],flush=True)
if __name__=='__main__':prepare()
