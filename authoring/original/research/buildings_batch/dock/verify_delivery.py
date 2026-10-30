from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3];O=R/'output/buildings_batch/dock';A=R/'art/buildings/dock';d=json.loads((O/'delivery.json').read_text())
assert d['required_ages']==[1,2,3,4]
for f in d['files']:
 p=R/f['path'];assert p.stat().st_size==f['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
for age in d['required_ages']:
 v=json.loads((O/f'age{age}_validation.json').read_text());assert all(c['pass'] for c in v['contacts']);assert not v['footprint_envelope']['central_lane_obstacles']
 assert all(x['finite_vertices'] and x['positive_transforms'] and x['positive_volume']>0 and x['non_manifold_edges']==x['degenerate_faces']==x['uv_zero_area_faces']==0 for x in v['objects'])
 assert len(v['objects'])==len(json.loads((A/f'age{age}_construction.json').read_text())['parts'])
 for name in ['preview','front','back','left','right','top','bottom','sixside']:assert (O/f'age{age}_{name}.png').is_file()
audit=json.loads((O/'saved_source_fbx_audit.json').read_text());assert [x['age'] for x in audit]==[1,2,3,4];assert all(x['saved_meshes']==x['fbx_meshes'] and x['packed_images']==5 and x['stage_manifest_matches'] and x['uvs_preserved'] for x in audit)
assert not list(O.glob('*ERROR*'))
print('DOCK_DELIVERY_VERIFIED',[(x['age'],x['saved_meshes'],x['triangles']) for x in audit])
