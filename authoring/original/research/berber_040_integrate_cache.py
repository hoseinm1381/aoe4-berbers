"""Read regenerable040 projections directly from a verified compact bundle."""
import hashlib,json,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/building_remix_0_4_0'

def read_cached_json(path):
 path=Path(path)
 if path.exists():return json.loads(path.read_text(encoding='utf-8-sig'))
 from source_bundle import read_json
 try:return read_json(path)
 except FileNotFoundError:pass
 bundle=path.parent/'rebuild-cache.zip';manifest=json.loads((path.parent/'rebuild-cache.json').read_text())
 assert hashlib.sha256(bundle.read_bytes()).hexdigest()==manifest['bundle_sha256']
 with ZipFile(bundle) as z:raw=z.read(path.name)
 assert hashlib.sha256(raw).hexdigest()==manifest['members'][path.name]['sha256']
 return json.loads(raw)

def bundle_decoded(path,delete=False):
 path=Path(path);allowed=Path('F:/aoe_4_temp/berber_040_university_donors').resolve()
 assert path.resolve().is_relative_to(allowed) and path.name=='decoded-static.json'
 assert not path.parent.is_junction() and not path.parent.is_symlink() and not path.is_symlink()
 raw=path.read_bytes();target=path.parent/'rebuild-cache.zip'
 if (path.parent/'rebuild-cache.json').exists():
  previous=json.loads((path.parent/'rebuild-cache.json').read_text())
  assert hashlib.sha256(raw).hexdigest()==previous['members'][path.name]['sha256'],'Decoded donor cache changed since preserved provenance'
 with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=9) as z:z.writestr(path.name,raw)
 record={'bundle_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'members':{path.name:{'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}},'compressed_bytes':target.stat().st_size,'uncompressed_bytes':len(raw)}
 (path.parent/'rebuild-cache.json').write_text(json.dumps(record,indent=2)+'\n')
 (path.parent/'CACHE_REBUILD.md').write_text('040 University donor projection cache\n\nDecoded JSON is retained losslessly in rebuild-cache.zip, verified by rebuild-cache.json SHA256. Native geometry/material and source textures remain alongside it. All040 University readers use read_cached_json and can read this bundle without expanding it. To restore the raw JSON: py -3.13 research/berber_040_integrate_cache.py restore-decoded "'+str(path)+'"\n\nOfficial regeneration: py -3.13 research/berber_040_university_donors.py (active Abbasid donor; retained logical path and input hashes are in decoded JSON and University recipe).\n',encoding='utf8')
 with ZipFile(target) as z:assert z.testzip() is None and z.read(path.name)==raw
 if delete:
  path.unlink();assert read_cached_json(path)==json.loads(raw)
 return record

def restore_decoded(path):
 path=Path(path);assert path.resolve().is_relative_to(Path('F:/aoe_4_temp/berber_040_university_donors').resolve()) and path.name=='decoded-static.json'
 read_cached_json(path)
 manifest=json.loads((path.parent/'rebuild-cache.json').read_text())
 with ZipFile(path.parent/'rebuild-cache.zip') as z:raw=z.read(path.name)
 assert hashlib.sha256(raw).hexdigest()==manifest['members'][path.name]['sha256']
 if path.exists():assert path.read_bytes()==raw
 else:path.write_bytes(raw)

def bundle(family,delete=False):
 source=ART/family;resolved=source.resolve();assert resolved.is_relative_to(ART.resolve()) and resolved!=ART.resolve()
 assert not source.is_junction() and not source.is_symlink()
 files=sorted(source.glob('*-projection.json'))+sorted(source.glob('*-remix-projection.json'))+sorted(source.glob('*_projection.json'))
 files=sorted(set(files));assert files,family
 target=source/'rebuild-cache.zip';manifest={}
 with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=9) as z:
  for path in files:
   assert not path.is_junction() and not path.is_symlink()
   raw=path.read_bytes();manifest[path.name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};z.writestr(path.name,raw)
 with ZipFile(target) as z:
  assert z.testzip() is None
  for name,row in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==row['sha256']
 record={'bundle_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'members':manifest,'uncompressed_bytes':sum(r['bytes'] for r in manifest.values()),'compressed_bytes':target.stat().st_size}
 (source/'rebuild-cache.json').write_text(json.dumps(record,indent=2)+'\n')
 (source/'CACHE_REBUILD.md').write_text('040 projection cache bundle\n\nNative geometry, packed Blender and recipes remain outside this ZIP. read_cached_json(path) in research/berber_040_integrate_cache.py reads and verifies missing projection JSON directly from this bundle. To restore the original paths for another reader, run from project root:\n\n    py -3.13 research/berber_040_integrate_cache.py restore '+family+'\n\nEvery restored member is SHA256 checked against rebuild-cache.json. The source native recipe can also regenerate these projections from its retained donor/recipe inputs.\n',encoding='utf8')
 if delete:
  for path in files:
   assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest[path.name]['sha256'];path.unlink()
  for name in manifest:read_cached_json(source/name)
 print(json.dumps({'family':family,'deleted_originals':delete,**record},indent=2))
 return record

def restore(family):
 source=ART/family;assert source.resolve().is_relative_to(ART.resolve())
 manifest=json.loads((source/'rebuild-cache.json').read_text());bundle=source/'rebuild-cache.zip'
 assert hashlib.sha256(bundle.read_bytes()).hexdigest()==manifest['bundle_sha256']
 with ZipFile(bundle) as z:
  for name,row in manifest['members'].items():
   assert Path(name).name==name
   raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==row['sha256']
   target=source/name
   if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256']
   else:target.write_bytes(raw)
 print('040_CACHE_RESTORED',family)

if __name__=='__main__':
 if sys.argv[1]=='restore-decoded':restore_decoded(sys.argv[2])
 elif sys.argv[1]=='restore':restore(sys.argv[2])
 elif sys.argv[1]=='bundle':bundle(sys.argv[2],delete='--delete' in sys.argv)
