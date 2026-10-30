"""Berber091: explicit donor UV restoration, isolated composition and evidence."""
from pathlib import Path
import os, sys, json, subprocess, hashlib, struct, math, sqlite3, tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/berber_update_0_9_1'
BASE = ROOT / 'output/berber_update_0_9_0/Berber_future_kingdom.sga'
BASE_SHA = '6c8a3a80fbc92139d7066c9730566f74a54a9781808fafc31634e4c5cfb69b88'
EXT = Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
ARCH = EXT / 'bin/sga-archiver.exe'
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
def run(*args):
    p = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding='utf8', errors='replace')
    if p.returncode: raise RuntimeError(p.stderr[-3000:] + p.stdout[-3000:])
    return p.stdout
def extract(archive, destination, members):
    # One scan for an entire archive; batching exact members repeatedly reparses
    # the whole SGA and is needlessly slow for full readbacks.
    if len(members)>1000 and not Path(destination).exists():
        assert all('/' in m for m in members)
        run(ARCH,'extract',archive,destination,'--filter','/')
        assert all((Path(destination)/m).exists() for m in members)
        return
    members = [m for m in members if not (Path(destination)/m).exists()]
    for start in range(0, len(members), 50):
        args = [ARCH, 'extract', archive, destination]
        for name in members[start:start+50]: args += ['--member', name]
        run(*args)

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

def targets():
    frozen=Path(__file__).parent/'donors.json'
    if frozen.exists():
        rows=read(frozen)['models']
        for row in rows:
            row['donor']=str(ROOT/row.pop('donor_relative'))
            assert sha(row['donor'])==row['donor_sha256']
        return rows
    old = ROOT / 'output/Berber-0.7.4-handoff.1-2026-10-17/evidence/uv-after-validation.json'
    flagged = [x for x in read(old) if x['remaining_nonfinite_uv_vertices']]
    assert len(flagged) == 22
    units = []
    for p in (ROOT/'art/unit_remix_0_5_0').rglob('*manifest.json'):
        d = read(p)
        if isinstance(d, dict):
            for key in ('variants', 'trader'):
                for row in d.get(key, []): units.append((row, p))
    result = []
    for row in flagged:
        name = row['member']; stem = name.removesuffix('.rrgeom')
        if '/bt026/' in name or '/bb026/' in name:
            family = 'towncenter' if '/bt026/' in name else 'barracks'
            recipe = ROOT/f'art/building_remix_0_2_6/{family}/recipe.json'
            m = next(x for x in read(recipe)['models'] if x['name'] == Path(stem).name)
            manifest = read(m['decode']); donor = Path(manifest['geometry']['source']['path'])
            expected = manifest['geometry']['source']['sha256']; logical = m['source'].removesuffix('.rgm') + '.rrgeom'
        else:
            matches = [(v,p) for v,p in units if v.get('private_stem',v.get('private_resource_stem')) == stem]
            assert len(matches) == 1, (name, len(matches))
            m, recipe = matches[0]
            logical = m['official_donor_rgm'].removesuffix('.rgm') + '.rrgeom'
            donor = ROOT / Path(m['decoded_manifest']).parent / 'source' / logical
            expected = m['native_source_rrgeom_sha256']
        assert donor.exists() and sha(donor) == expected, str(donor)
        result.append({**row, 'donor':str(donor), 'donor_sha256':expected,
                       'donor_logical':logical, 'recipe':str(recipe.relative_to(ROOT)), 'recipe_sha256':sha(recipe)})
    return result

def freeze():
    rows=[]
    for row in read(OUT/'input-audit.json')['models']:
        item={k:v for k,v in row.items() if k not in ('groups','donor_group_count','current_group_count','observed_invalid_uv_vertices','donor')}
        item['donor_relative']=str(Path(row['donor']).relative_to(ROOT)).replace('\\','/')
        rows.append(item)
    write(Path(__file__).parent/'donors.json',{'schema':'berber091-explicit-donors/v1','baseline_sha256':BASE_SHA,'models':rows})

def audit():
    assert sha(BASE) == BASE_SHA
    rows = targets(); extract(BASE, OUT/'work/baseline', [r['member'] for r in rows])
    for r in rows:
        print('AUDIT',r['member'],flush=True)
        source = OUT/'work/baseline'/r['member']; _, current = groups(source.read_bytes()); _, donor = groups(Path(r['donor']).read_bytes())
        if 'baseline_sha256' in r: assert sha(source)==r['baseline_sha256']
        r['baseline_sha256'] = sha(source)
        r['groups'] = []
        for i, a in enumerate(current):
            b = donor[i] if i < len(donor) else None
            r['groups'].append({'group':i,'stream':a['stream'],'vertices':a['count'], 'invalid_uv_vertices':len(a['bad']),
              'donor_invalid_uv_vertices':len(b['bad']) if b else None,
              'same_vertex_count': bool(b and a['count']==b['count']),
              'same_index_buffer': bool(b and a['index'].payload==b['index'].payload),
              'same_geometry_header': bool(b and next(x.payload for x in a['geometry'].children if x.tag==b'GOHD')==next(x.payload for x in b['geometry'].children if x.tag==b'GOHD'))})
        r['observed_invalid_uv_vertices'] = sum(len(x['bad']) for x in current)
        r['donor_group_count'] = len(donor); r['current_group_count'] = len(current)
        assert r['observed_invalid_uv_vertices'] == r['remaining_nonfinite_uv_vertices'], r['member']
    write(OUT/'input-audit.json', {'baseline':str(BASE),'baseline_sha256':BASE_SHA,'models':rows})
    print(json.dumps([{'member':r['member'], 'bad':r['observed_invalid_uv_vertices'], 'donor_bad':sum(g['donor_invalid_uv_vertices'] or 0 for g in r['groups']),
       'groups':(r['current_group_count'],r['donor_group_count']), 'all_topology_same':all(g['same_index_buffer'] and g['same_vertex_count'] and g['same_geometry_header'] for g in r['groups'])} for r in rows],indent=2))

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

def repair():
    audit=read(OUT/'input-audit.json'); assert sha(BASE)==BASE_SHA
    reports=[]
    for row in audit['models']:
        source=OUT/'work/baseline'/row['member']; assert sha(source)==row['baseline_sha256']
        assert sha(row['donor'])==row['donor_sha256']
        result,proof=restore_uv(source.read_bytes(),Path(row['donor']).read_bytes())
        target=OUT/'work/repaired'/row['member']; target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
        reports.append({'member':row['member'],'before_sha256':row['baseline_sha256'],'after_sha256':sha(target),
                        'donor_sha256':row['donor_sha256'],**proof})
    write(OUT/'uv-repair-proof.json',{'status':'passed','scope':'22 explicit final090 RRGeom members; UV0 only',
       'nonfinite_uv_vertices_before':sum(r['invalid_before'] for r in reports),'nonfinite_uv_vertices_after':0,'models':reports})
    print('REPAIRED',len(reports),'files;',sum(r['invalid_before'] for r in reports),'nonfinite UV vertices removed')

def official():
    rows=read(OUT/'input-audit.json')['models']
    db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
    archives={}; donors={}
    for row in rows:
        logical=row['donor_logical']
        source=db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(logical,)).fetchone()
        assert source,logical
        archive=Path(source[0]); donors[logical]=(archive,row['donor_sha256'])
        archives.setdefault(archive,[]).append(logical)
    for archive,members in archives.items(): extract(archive,OUT/'work/official',sorted(set(members)))
    result=[]
    for member,(archive,digest) in donors.items():
        path=OUT/'work/official'/member; assert sha(path)==digest,member
        result.append({'member':member,'sha256':digest,'official_archive':str(archive)})
    write(OUT/'official-donor-proof.json',{'status':'passed','unique_donors':result,
        'official_archives':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in archives},
        'all_current_official_donors_match_retained_sources':True})
    print('OFFICIAL_DONORS_VERIFIED',len(result))

def compose():
    assert sha(BASE)==BASE_SHA
    proof=read(OUT/'uv-repair-proof.json'); assert proof['status']=='passed'
    assert read(OUT/'official-donor-proof.json')['status']=='passed'
    final=OUT/'Berber_future_kingdom.sga'
    pairs=[]
    for row in proof['models']:
        payload=OUT/'work/repaired'/row['member']; assert sha(payload)==row['after_sha256']
        pairs.append(row['member']+'='+str(payload.resolve()))
    listing=OUT/'work/payload-members.txt'; listing.write_text('\n'.join(pairs)+'\n',encoding='utf8')
    if not final.exists(): run(ARCH,'set-members',BASE,listing,final)
    before=json.loads(run(ARCH,'list',BASE,'--verify')); after=json.loads(run(ARCH,'list',final,'--verify'))
    assert before['archive']['verification']['verified'] and after['archive']['verification']['verified']
    assert before['archive']['name']==after['archive']['name']
    write(OUT/'archive-inventory.json',after)
    old={r['path']:r for r in before['members']}; new={r['path']:r for r in after['members']}
    assert old.keys()==new.keys()
    allow={r['member']:r for r in proof['models']}
    for n in old:
        assert old[n]['toc']==new[n]['toc'],n
        if n not in allow:
            assert all(old[n][k]==new[n][k] for k in ('size','crc','storage','encryption')),n
    # Every decoded member is hashed; compression/CRC alone is insufficient.
    extract(BASE,OUT/'work/full-base',sorted(old))
    extract(final,OUT/'work/full-final',sorted(new))
    def hash_members(folder,names):
        def one(n):return n,sha(folder/n)
        with ThreadPoolExecutor(max_workers=8) as pool:return dict(pool.map(one,sorted(names)))
    oldsha=hash_members(OUT/'work/full-base',old)
    print('BASE_MEMBER_SHA256_DONE',len(oldsha),flush=True)
    newsha=hash_members(OUT/'work/full-final',new)
    print('FINAL_MEMBER_SHA256_DONE',len(newsha),flush=True)
    changed=[n for n in oldsha if oldsha[n]!=newsha[n]]
    assert set(changed)==set(allow)
    for n,row in allow.items():
        assert newsha[n]==row['after_sha256']
        _,mesh=groups((OUT/'work/full-final'/n).read_bytes())
        assert not any(g['bad'] for g in mesh)
    write(OUT/'member-sha256-proof.json',{'status':'passed','baseline_sha256':BASE_SHA,'archive_sha256':sha(final),
       'changed_existing':changed,'new_members':[],'removed_members':[],'baseline_members':len(old),'final_members':len(new),
       'unchanged_member_count':len(old)-len(changed),'all_unrelated_decoded_member_sha256_identical':True,
       'all_gameplay_attrib_scar_audio_models_materials_stamps_except22uv_members_identical':True,
       'before':oldsha,'after':newsha,'native_archive_verification':after['archive']['verification']})
    print('COMPOSITION_VERIFIED',len(changed),'changed;',len(old)-len(changed),'unchanged; SHA',sha(final))

def verify_models():
    rows=read(OUT/'input-audit.json')['models'];proof=read(OUT/'member-sha256-proof.json')
    final=OUT/'Berber_future_kingdom.sga'; assert sha(final)==proof['archive_sha256'] and sha(BASE)==BASE_SHA
    with tempfile.TemporaryDirectory(prefix='091-postflight-',dir=OUT.resolve()) as tmp:
        tmp=Path(tmp);assert tmp.resolve().parent==OUT.resolve()
        extract(BASE,tmp/'before',[r['member'] for r in rows])
        extract(final,tmp/'after',[r['member'] for r in rows])
        checked=[]
        for row in rows:
            name=row['member'];assert sha(tmp/'before'/name)==row['baseline_sha256']
            assert sha(row['donor'])==row['donor_sha256']
            expected,verification=restore_uv((tmp/'before'/name).read_bytes(),Path(row['donor']).read_bytes())
            actual=(tmp/'after'/name).read_bytes();assert actual==expected,name
            assert hashlib.sha256(actual).hexdigest()==proof['after'][name]
            checked.append({'member':name,'invalid_after':0,'exact_uv_only_reproduction':True})
    write(OUT/'model-postflight.json',{'status':'passed','archive_sha256':sha(final),'models':checked,
      'all22_fresh_archive_readback_and_exact_uv_only_reproduction':True})
    print('091_MODEL_POSTFLIGHT_PASSED',len(checked))

if __name__ == '__main__':
    if sys.argv[1:] == ['audit']: audit()
    elif sys.argv[1:] == ['repair']: repair()
    elif sys.argv[1:] == ['official']: official()
    elif sys.argv[1:] == ['compose']: compose()
    elif sys.argv[1:] == ['freeze']: freeze()
    elif sys.argv[1:] == ['verify-models']: verify_models()
