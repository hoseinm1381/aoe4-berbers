"""Finish an assembled family only after fresh native stamp cook/readback."""
import os,sys,json,sqlite3,re,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from landmark_027_export_codec import rc,sha,visibility_evidence
def finish_assembled(outputRoot,stamp_readback,native_run_json,cook_records):
 outputRoot=Path(outputRoot);p=outputRoot/'media-manifest.json';report=json.loads(p.read_text())
 native=json.loads(Path(native_run_json).read_text());assert native['status']=='succeeded' and native['exit_code']==0
 for cook in cook_records:
  assert cook['live_reload'] is False
  archive=Path(cook['archive']);assert archive.exists() and sha(archive.read_bytes())==cook['sha256']
 assert len(cook_records)>0
 payloads=report['payloads'];by_member={r['member']:r for r in payloads}
 assert len(by_member)==len(payloads)
 for r in payloads:assert sha(Path(r['file']).read_bytes())==r['sha256']
 principal=next(r for r in payloads if '/buildings/' in r['member'] and r['member'].endswith('.rgm'))
 visibility_evidence(Path(principal['file']).read_bytes(),report['source_part_rows'])
 geom=by_member[principal['member'].removesuffix('.rgm')+'.rrgeom'];doc=rc.load(geom['file'])
 assert report['geometry_mode']=='native-compatible-single' and report['native_lod_count']==1
 assert [int.from_bytes(c.payload,'little') for c in rc.walk(doc.roots) if c.tag==b'NBLO']==[1]*report['lod_evidence']['source_levels'][0]['native_mesh_count']
 assert sha(Path(geom['file']).read_bytes())==report['lod_evidence']['runtime_geometry_sha256']
 collection=next(c.payload for c in rc.walk(rc.load(principal['file']).roots) if c.tag==b'DATA')
 assert sha(collection)==report['collection_data_sha256'] and report['collection_data_byte_identical_to_fresh_lod0'] is True
 stamp=Path(stamp_readback)/(report['primary_stamp']+'.bin');decoded=stamp.with_suffix('.rdo');assert stamp.exists() and decoded.exists()
 tree=ET.parse(decoded);references=[n.get('Value').replace('\\','/') for n in tree.iter('DataProperty') if n.get('Name')=='m_blueprint']
 expected=[principal['member'].removesuffix('.rgm'),next(r['member'].removesuffix('.rgm') for r in payloads if '/owner_flag/' in r['member'] and r['member'].endswith('.rgm'))]
 assert sorted(references)==sorted(expected),(references,expected)
 output=outputRoot/'payload'/(report['primary_stamp']+'.bin');output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(stamp.read_bytes())
 stamp_row={'member':report['primary_stamp']+'.bin','file':str(output.resolve()),'sha256':sha(output.read_bytes())}
 payloads=[r for r in payloads if r['member']!=stamp_row['member']]+[stamp_row]
 # Validate all material texture references either in this private payload or official catalogue.
 official=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True);dependencies=[]
 for r in payloads:
  if not r['member'].endswith('.rrmaterial'):continue
  raw=Path(r['file']).read_bytes()
  paths=set(m.decode().replace('\\','/') for m in re.findall(rb'art[\\/][A-Za-z0-9_./\\-]+\.rrtex',raw))
  assert paths,'Native material texture dependency list must be inspected, not assumed empty'
  for dep in sorted(paths):
   if dep in by_member:kind='private payload'
   else:
    found=official.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(dep,)).fetchone()
    assert found and Path(found[0]).exists(),dep;kind='official game resource'
   dependencies.append({'resource':dep,'resolution':kind})
 official.close()
 report.update(status='passed',fresh_cooks_verified=True,construction_visibility_verified=True,dependencies_resolved=True,dynamic_owner_colour_preserved=True,native_graph_preserved=True,fresh_native_stamp_cook=native,source_cook_records=cook_records,stamp_compiled_sha256=sha(stamp.read_bytes()),stamp_model_references=references,dependencies=dependencies,payloads=payloads)
 p.write_text(json.dumps(report,indent=2));return report
