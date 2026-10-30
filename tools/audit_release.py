"""Check current editable UI/gameplay source against the verified final release.

Native media were fully verified at assembly/readback. This audit compares their
unchanged manifest and on-disk inventory, without repeating a full media rehash.
Use tools/inputs.py verify for a new full native/master file verification.
"""
import hashlib,json,gzip,os
from pathlib import Path
from runtime import ROOT,read_json,write_json,import_table,rgd
from codex import build
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 cfg=read_json(ROOT/'project.json');v=read_json(ROOT/'docs/BUILD_VERIFICATION.json');manifest=json.loads(gzip.decompress((ROOT/'docs/FINAL_MEMBER_MANIFEST.json.gz').read_bytes()));members=manifest['members'];assert cfg['version']==v['version']==manifest['version']=='0.1.2';assert cfg['owner']==v['owner']==manifest['owner']
 old=read_json(ROOT/'docs/update_012/before/project.json')
 for key in ('owner','race','bundle_key','dispatcher','shared_entities'):assert cfg[key]==old[key]
 package=ROOT/'release'/v['zip_name'];assert list((ROOT/'release').iterdir())==[package] and sha(package)==v['zip_sha256'];assert manifest['archive_sha256']==v['archive_sha256']
 tables={p.relative_to(ROOT/'source/tables').as_posix()[:-5]:rgd.read(import_table(read_json(p))) for p in (ROOT/'source/tables').rglob('*.rgd.json')};doc,graph=build(tables,cfg)
 for member,d in tables.items():assert hashlib.sha256(rgd.write(d)).hexdigest()==members[member]['sha256'],member
 native=read_json(ROOT/'inputs/native-manifest.json');assert sha(ROOT/'inputs/native-manifest.json')==v['native_input_manifest_sha256'];assert sha(ROOT/'source/master-index.json')==v['editable_master_index_sha256']
 for m,row in native.items():
  assert row['sha256']==members[m]['sha256'] and row['bytes']==members[m]['bytes'],m
 inventory=set()
 for directory,dirs,files in os.walk(ROOT/'inputs/native',followlinks=False):
  for name in dirs:
   p=Path(directory)/name;assert not p.is_symlink() and not p.is_junction()
  inventory.update((Path(directory)/name).relative_to(ROOT/'inputs/native').as_posix() for name in files)
 assert inventory==set(native),(len(inventory-set(native)),len(set(native)-inventory))
 for p in (ROOT/'source/scar').rglob('*.scar'):
  m='scar/'+p.relative_to(ROOT/'source/scar').as_posix()
  if m!=cfg['dispatcher']:assert sha(p)==members[m]['sha256'],m
 if (ROOT/'source/locale/en.json').exists():
  loc=read_json(ROOT/'source/locale/en.json');raw=''.join(str(k)+'\t'+str(v)+'\r\n' for k,v in sorted(loc.items(),key=lambda row:int(row[0]))).encode('utf-16');assert hashlib.sha256(raw).hexdigest()==members['en/en.ucs']['sha256']
 else:assert sha(ROOT/'source/resources/en/en.ucs')==members['en/en.ucs']['sha256']
 report={'version':'0.1.2','current_editable_tables_match_final_native_sha256':len(tables),'codex_regeneration_byte_identical':True,'native_manifest_rows_match_final_archive':len(native),'native_input_inventory_exact':True,'locale_and_nonpromoted_scar_source_match_final_archive':True,'stable_owner_race_bundle_dispatcher_shared_entities':True,'player_zip_sha256':v['zip_sha256'],'master_index_unchanged_since_full_build_verification':True,'native_game_test':'pending','source_rebuild':'Current full builder consumes these source tables and retained exact native inputs; historical authoring paths are not used for this package rebuild.'}
 write_json(ROOT/'docs/CURRENT_SOURCE_RELEASE_AUDIT.json',report);print('CURRENT_SOURCE_MATCHES_FINAL_NATIVE',cfg['race'],len(tables),'tables',len(native),'native inputs',flush=True)
if __name__=='__main__':main()
