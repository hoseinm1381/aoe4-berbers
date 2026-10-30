"""Small reusable native donor cache, keyed by logical identity and content SHA.
No decoded-static JSON is a rebuild dependency. Official archive fingerprint
invalidates entries after game updates. --refresh exercises actual extraction.
"""
import hashlib,json,os,sqlite3,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'output/shared_stock_cache/native_landmark_donors'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stock(member,refresh=False):
 CACHE.mkdir(parents=True,exist_ok=True);index=CACHE/'index.json'
 records=json.loads(index.read_text()) if index.exists() else {}
 with sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True) as db:
  row=db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(member,)).fetchone()
 assert row,member
 archive=Path(row[0]);info=archive.stat();fingerprint={'path':str(archive),'size':info.st_size,'mtime_ns':info.st_mtime_ns}
 prior=records.get(member)
 if prior and not refresh:
  p=CACHE/prior['file']
  if prior['archive']==fingerprint and p.exists() and digest(p)==prior['sha256']:return p
 with tempfile.TemporaryDirectory(dir=CACHE) as td:
  extracted=Path(td)/Path(member).name
  subprocess.run([str(EXT/'bin/sga-archiver.exe'),'extract-member',str(archive),member,str(extracted)],check=True,capture_output=True)
  h=digest(extracted);relative=Path(h)/Path(member).name;p=CACHE/relative;p.parent.mkdir(exist_ok=True)
  p.write_bytes(extracted.read_bytes())
 records[member]={'file':relative.as_posix(),'sha256':h,'archive':fingerprint,'logical_identity':member}
 index.write_text(json.dumps(records,indent=2),encoding='utf8');return p
if __name__=='__main__':
 from landmark_027_export_assemble import DONORS,FLAG
 for base in DONORS.values():
  for suffix in ['.rgm','.rgo']:print(base+suffix,digest(stock(base+suffix,True)))
 for suffix in ['.rgm','.rgo','.rrgeom','.rrmaterial']:print(FLAG+suffix,digest(stock(FLAG+suffix,True)))
