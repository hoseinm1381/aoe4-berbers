"""Check final 0.1.3 texture dependency closure and packaged LOD inventory."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3

from owner_color import INDEX,ROOT,blocks,decode,logical,rc,slots


def verify(root):
    doc=ROOT/'docs/update_013'
    policies=json.loads((ROOT/'source/update-013-policy.json').read_bytes())
    changed=policies['allowed_changed']
    db=sqlite3.connect('file:'+INDEX.as_posix()+'?mode=ro',uri=True)
    checked=set()
    for path in (m for m in changed if m.endswith('.rrmaterial')):
        for _,block in blocks((root/path).read_bytes()):
            for raw in slots(block)['textures'].values():
                member=logical(raw)
                if member in checked or member=='__default':
                    continue
                if not (root/member).is_file():
                    result=db.execute('select 1 from resolved_assets where logical_path=?',(member,)).fetchone()
                    if not result:
                        raise ValueError(f'Unresolved texture {member} referenced by {path}')
                checked.add(member)
    added=set(policies['allowed_added'])
    if not added<=checked:
        raise ValueError('New texture is unreferenced: '+str(added-checked))
    for member in sorted(added):
        decode((root/member).read_bytes())
    stats=Counter()
    for path in (root/'art/scenario').rglob('*.rrgeom'):
        if any(x in path.parts for x in ('berber_units_050','tuareg_refined_art','tuareg')):
            continue
        for mesh in (c for c in rc.walk(rc.parse(path.read_bytes()).roots) if c.tag==b'MESH'):
            levels=sum(c.tag==b'LOD ' for c in mesh.children)
            if levels!=1:
                raise ValueError(f'Custom building mesh has {levels} LODs: {path}')
            stats['building_mesh_groups']+=1
    for row in json.loads((doc/'units.json').read_bytes()):
        path=root/Path(row['model']).with_suffix('.rrgeom')
        geo=rc.parse(path.read_bytes())
        levels=[sum(c.tag==b'LOD ' for c in mesh.children)
                for mesh in rc.walk(geo.roots) if mesh.tag==b'MESH']
        if not levels or any(level!=3 for level in levels):
            raise ValueError(f'Unit is missing LODs: {path}, {levels}')
        triangles=[0,0,0]
        for mesh in (c for c in rc.walk(geo.roots) if c.tag==b'MESH'):
            for i,lod in enumerate(c for c in mesh.children if c.tag==b'LOD '):
                for geom in (c for c in lod.children if c.tag==b'GEOM'):
                    _,index=[c for c in geom.children if c.tag==b'GEOB']
                    triangles[i]+=int.from_bytes(index.payload[:4],'little')//3
        if triangles[0]>triangles[1]>triangles[2]:
            stats['unit_resources_with_reduced_triangle_counts']+=1
        else:
            stats['unit_resources_with_preserved_non_decimated_lods']+=1
        stats['unit_resources']+=1
    return {**stats,'resolved_texture_slots':len(checked),'new_textures_decoded':len(added)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.root),indent=2))
