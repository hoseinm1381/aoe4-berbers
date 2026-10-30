"""Native UV0 preservation, migrated from the verified 0.9.1 algorithm."""
import sys,struct,math
from workspace import EXT
sys.path.insert(0,str(EXT))
from garrison_shared import relic_chunky as rc

def groups(raw):
    doc = rc.parse(raw); result = []
    for c in rc.walk(doc.roots):
        if c.tag != b'GEOM': continue
        header = next(x for x in c.children if x.tag == b'GOHD')
        at = 0; names = []
        for _ in range(4):
            value, at = rc.read_lp_string(header.payload, at); names.append(value)
        stream = names[3]
        buffers = [x for x in c.children if x.tag == b'GEOB']
        assert len(buffers) == 2
        vertex, index = buffers
        count, _, stride, _ = struct.unpack_from('<4I', vertex.payload)
        assert len(vertex.payload) == 16 + count * stride
        assert (stream, stride) in {('UnitDataStream', 28), ('StructureCollectionPositionDataStream', 24), ('ObjectDataStream', 28)}
        bad = [i for i in range(count) if not all(math.isfinite(v) for v in struct.unpack_from('<2e', vertex.payload, 16+i*stride+12))]
        result.append(dict(chunk=vertex, geometry=c, stream=stream, count=count, stride=stride, bad=bad, index=index))
    return doc, result

def restore_uv(raw, donor_raw):
    """Replace declared UV0 half2 only, after exact topology/order qualification."""
    doc, current = groups(raw); donor_doc, donor = groups(donor_raw)
    assert len(current) == len(donor), 'Donor group count mismatch'
    replacements = {}; report = []; allowed = set()
    source_chunks = list(rc.walk(doc.roots)); donor_chunks = list(rc.walk(donor_doc.roots))
    assert len(source_chunks) == len(donor_chunks), 'Donor chunk count mismatch'
    vertex_offsets = {g['chunk'].offset for g in current}
    for a,b in zip(source_chunks,donor_chunks):
        assert (a.kind,a.tag,a.name,a.version)==(b.kind,b.tag,b.name,b.version), 'Donor chunk identity mismatch'
        if not a.children and a.offset not in vertex_offsets:
            assert a.payload==b.payload, 'Nonvertex donor structure/topology mismatch'
    for gi,(a,b) in enumerate(zip(current,donor)):
        assert (a['stream'],a['count'],a['stride']) == (b['stream'],b['count'],b['stride']), 'Donor stream mismatch'
        assert a['index'].payload==b['index'].payload, 'Donor topology mismatch'
        assert not b['bad'], 'Donor has non-finite UVs'
        buf=bytearray(a['chunk'].payload); src=b['chunk'].payload; changed=0
        assert buf[:16]==src[:16], 'Donor vertex header mismatch'
        for i in range(a['count']):
            at=16+i*a['stride']
            # Stable native skin/selector/secondary-UV/tangent lanes also pin
            # donor vertex correspondence; authored position/normal edits stay.
            assert buf[at+16:at+a['stride']]==src[at+16:at+a['stride']], 'Donor vertex-order/skin mismatch'
            if buf[at+12:at+16]!=src[at+12:at+16]:
                changed+=1;buf[at+12:at+16]=src[at+12:at+16]
            allowed.update(range(a['chunk'].offset+20+at+12,a['chunk'].offset+20+at+16))
        replacements[a['chunk'].offset]=bytes(buf)
        report.append({'group':gi,'stream':a['stream'],'vertices':a['count'],'invalid_before':len(a['bad']),
                       'changed_uv_vertices':changed,'donor_uv0_restored_exactly':True})
    result=rc.rebuild(doc,lambda c:replacements.get(c.offset))
    assert len(result)==len(raw), 'Geometry size changed'
    differences=[i for i,(a,b) in enumerate(zip(raw,result)) if a!=b]
    assert differences and all(i in allowed for i in differences), 'Changed byte outside UV0'
    _,after=groups(result)
    assert sum(len(g['bad']) for g in after)==0
    for a,b in zip(after,donor):
        for i in range(a['count']):
            at=16+i*a['stride']; assert a['chunk'].payload[at+12:at+16]==b['chunk'].payload[at+12:at+16]
    return result, {'groups':report,'invalid_before':sum(len(g['bad']) for g in current),
                    'invalid_after':0,'changed_bytes':len(differences),'only_uv0_bytes_changed':True,
                    'positions_normals_real_tangents_skin_indices_all_other_bytes_identical':True}
