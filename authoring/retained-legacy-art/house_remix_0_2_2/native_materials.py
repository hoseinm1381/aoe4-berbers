"""Apply supported Garrison material edits to individual native material roots.

The ordinary variant API flattens repeated slot names. Isolating each GMat
avoids replacing a roof's wood or a team's layer with another material's plaster.
"""
from garrison_shared import relic_chunky as rc,model_variants as mv

def rewrite_scoped(raw,edits):
    doc=rc.parse(raw)
    names={c.decoded_name.removesuffix('_collection') for c in doc.roots if c.tag==b'GMat'}
    if set(edits)-names:raise ValueError('Unknown native material: '+str(set(edits)-names))
    changed={}
    for c in doc.roots:
        key=c.decoded_name.removesuffix('_collection')
        if c.tag!=b'GMat' or key not in edits:continue
        one=rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,version=c.version,name=c.name)])
        updated=mv.rewrite_material(one,edits[key].get('textures',{}),edits[key].get('parameters',{}))
        changed[c.offset]=rc.parse(updated).roots[0].payload
    result=rc.rebuild(doc,lambda c:changed.get(c.offset))
    assert len(rc.parse(result).roots)==len(doc.roots)
    return result
