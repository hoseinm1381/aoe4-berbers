"""Restore native visibility for the nine converted Berber building materials."""
import argparse
import json
from pathlib import Path

from garrison_shared import model_variants as mv, relic_chunky as rc


def materials(raw):
    for chunk in rc.parse(raw).roots:
        if chunk.tag == b'GMat':
            packed = rc.pack_document([rc.pack_chunk(chunk.kind, chunk.tag, chunk.payload,
                version=chunk.version, name=chunk.name)])
            yield chunk, packed, mv.material_slots(packed)


def edit_material(raw, native):
    replacements = {}
    for c, one, slots in materials(raw):
        textures = slots['textures']
        parameters = slots['parameters']
        assert parameters['options']['values'] == ['64','0','0','8']
        assert all((native / tex.replace('\\','/')).is_file() or tex == '__default'
                   or tex.startswith('art\\material_library\\') for tex in textures.values())
        # Native structure materials such as the shipped Tlemcen main material
        # enable the third lane. Retain layer 7 and its existing blue mask.
        after = mv.rewrite_material(one, {}, {'options': ['64','0','1','8']})
        parsed, = rc.parse(after).roots
        replacements[c.offset] = parsed.payload
        assert mv.material_slots(after)['textures'] == textures
    assert replacements
    return rc.rebuild(rc.parse(raw), lambda c: replacements.get(c.offset))


def run(stage, rows):
    native = stage/'baseline'
    older = stage/'older'
    fresh = stage/'fresh-tent'
    report = []
    for row in json.loads(rows.read_text(encoding='utf-8')):
        stem = row['model']
        member = stem+'.rrmaterial'
        old = native/member
        new = stage/'overlay'/member
        new.parent.mkdir(parents=True,exist_ok=True)
        new.write_bytes(edit_material(old.read_bytes(),native))
        record = {'member': member, 'material_slots': [c.decoded_name for c,_,_ in materials(new.read_bytes())],
                  'native_structure_options': [64,0,1,8], 'owner_layer': 'blue maskTex5 -> albedoTex7',
                  'original_lifecycle_preserved': (older/(stem+'.rgo')).read_bytes() == (native/(stem+'.rgo')).read_bytes()}
        if row['family']=='tribal tent':
            record['recooked_geometry_matches'] = (fresh/(stem+'.rrgeom')).read_bytes() == (native/(stem+'.rrgeom')).read_bytes()
            assert record['recooked_geometry_matches']
            # The fresh isolated cook has a template RGO, so the live model
            # retains its shipped construction/damage graph.
            a=rc.parse((fresh/(stem+'.rgm')).read_bytes())
            b=rc.parse((native/(stem+'.rgm')).read_bytes())
            chunk=lambda d: next(c.payload for c in rc.walk(d.roots) if c.tag==b'MSCL')
            assert chunk(a)==chunk(b)
        assert record['original_lifecycle_preserved']
        report.append(record)
    (stage/'visibility-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'{len(report)} structure material resources staged',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',type=Path)
    parser.add_argument('conversion_receipt',type=Path)
    args=parser.parse_args()
    run(args.stage,args.conversion_receipt)

