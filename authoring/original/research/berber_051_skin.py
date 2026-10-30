"""Small 0.5.1 skin palette patch on the verified packaged 0.5.0 archive.

Only skinTintLUT references, one native palette clone, and five skin-only baked
albedos are admitted. All unit/attachment/gameplay/geometry bytes stay identical.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import shutil
import subprocess
import sys
import struct
from io import BytesIO
import numpy as np
from PIL import Image
from berber_050_common import ROOT, OUT as OLD, ARCH, CORE, EDITOR, GUID, EXT, sha, read, write, run
from berber_050_build import MANIFESTS
from berber_050_model_payloads import records, absolute, atlas_jobs
from berber_050_materials import rc, texture_pairs, pack_pairs, canonical
from garrison_shared import rrtex_decoder

OUT = ROOT / 'output/berber_update_0_5_1'
ART = ROOT / 'art/unit_skin_0_5_1'
BASE = OLD / 'package/Berber_future_kingdom.sga'
BASE_SHA = '0bf6d113bf4c710d89d10affc95978b629ed13f6399cd343dcf2ca316e23184f'
LUT_SOURCE = 'art/civilizations/english/humans/tints/eng_skin_tinting_lut.rrtex'
LUT_MEMBER = 'art/scenario/garrison/berber_skin_051/fair_skin_lut.rrtex'
PNG_MANIFESTS = [ART / 'tuareg/tuareg-skin-manifest.json', ART / 'mounted/zenata-skin-manifest.json']


def extract(member, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha(destination) != baseline_hashes().get(member):
            raise ValueError('Existing baseline extraction differs from protected member')
        return destination
    run(ARCH, 'extract-member', BASE, member, destination)
    return destination


def replace_skin_lut(data, target=LUT_MEMBER):
    before = rc.parse(data)
    chunks = list(rc.walk(before.roots))
    changes = {}
    count = 0
    for chunk in chunks:
        if chunk.kind != b'DATA' or chunk.tag != b'PbTe':
            continue
        pairs = texture_pairs(chunk.payload)
        updated = []
        for slot, value in pairs:
            if slot == 'skinTintLUT':
                if '/humans/tints/' not in canonical(value) or not canonical(value).endswith('_skin_tinting_lut.rrtex'):
                    raise ValueError('Unqualified non-human skin palette')
                value = target.replace('/', '\\')
                count += 1
            updated.append((slot, value))
        if updated != pairs:
            changes[chunk.offset] = pack_pairs(updated)
    if not count:
        raise ValueError('Model has no native skin-tint slot')
    result = rc.rebuild(before, lambda c: changes.get(c.offset))
    after = list(rc.walk(rc.parse(result).roots))
    if len(after) != len(chunks):
        raise ValueError('Material chunk topology changed')
    restore = {}
    for a, b in zip(chunks, after):
        if (a.kind, a.tag, a.name, a.version) != (b.kind, b.tag, b.name, b.version):
            raise ValueError('Material chunk identity changed')
        if a.offset in changes:
            expected = [(slot, target.replace('/', '\\') if slot == 'skinTintLUT' else value)
                        for slot, value in texture_pairs(a.payload)]
            if texture_pairs(b.payload) != expected:
                raise ValueError('Material changed outside skinTintLUT')
            restore[b.offset] = a.payload
        elif not a.children and a.payload != b.payload:
            raise ValueError('Non-skin material bytes changed')
    if rc.rebuild(rc.parse(result), lambda c: restore.get(c.offset)) != data:
        raise ValueError('Skin slot rewrite failed exact native roundtrip')
    return result, {'skin_slots': count, 'only_skinTintLUT_changed': True,
                    'exact_native_roundtrip': True, 'owner_pattern_hair_albedo_and_shader_params_unchanged': True}


def rename_texture(data, stem):
    parsed = rc.parse(data)
    textures = [c for c in rc.walk(parsed.roots) if c.kind == b'FOLD' and c.tag == b'TXTR']
    if len(textures) != 1:
        raise ValueError('Only one-image native RRTexture containers are qualified')
    name = stem.replace('\\', '/').removesuffix('.rrtex').encode() + b'\0'
    result = rc.rebuild(parsed, lambda c: rc.Rename(name) if c.kind == b'FOLD' and c.tag == b'TXTR' else None)
    inverse = rc.rebuild(rc.parse(result), lambda c: rc.Rename(textures[0].name) if c.kind == b'FOLD' and c.tag == b'TXTR' else None)
    if inverse != data:
        raise ValueError('Native RRTexture identity rewrite is not reversible')
    return result


def verify_png(row):
    for key, digest in [('source_png','source_png_sha256'), ('authored_png','sha256'),
                        ('mask_png','mask_sha256'), ('source_owner_pattern','source_owner_pattern_sha256')]:
        if sha(absolute(row[key])) != row[digest]:
            raise ValueError(f'Changed authored skin input: {key}')
    source = np.asarray(Image.open(absolute(row['source_png'])).convert('RGBA'))
    target = np.asarray(Image.open(absolute(row['authored_png'])).convert('RGBA'))
    mask = np.asarray(Image.open(absolute(row['mask_png'])).convert('L')) > 0
    pattern = Image.open(absolute(row['source_owner_pattern'])).convert('RGB')
    if pattern.size != (source.shape[1], source.shape[0]):
        pattern = pattern.resize((source.shape[1], source.shape[0]), Image.Resampling.NEAREST)
    owner = np.asarray(pattern)[:,:,0] > 127
    if source.shape != target.shape or mask.shape != source.shape[:2]:
        raise ValueError('Skin atlas dimensions changed')
    changed = np.any(source != target, axis=2)
    if not changed.any() or (changed & ~mask).any() or (changed & owner).any() or np.any(source[:,:,3] != target[:,:,3]):
        raise ValueError('Skin edit is absent or changes cloth/owner pixels/alpha outside its qualified mask')
    if int(changed.sum()) != row['changed_pixels']:
        raise ValueError('Skin pixel receipt differs from current PNGs')
    return {'changed_pixels': int(changed.sum()), 'outside_skin_changes':0, 'owner_changes':0, 'alpha_changes':0}


def png_rows():
    rows = [r for path in PNG_MANIFESTS for r in read(path)['textures']]
    if {(r['family'],r['age']) for r in rows} != {('tuareg',1),('tuareg',2),('tuareg',3),('tuareg',4),('zenata',4)} or len(rows) != 5:
        raise ValueError('Exactly four accepted Tuareg and one baked Zenata IV skin atlas are required')
    for row in rows:
        if row['family']=='tuareg':
            expected=f"art/scenario/garrison/tuareg_refined_art/units/tuareg_age{row['age']}/body/albedo.rrtex"
        else:
            zenata=next(r for p in MANIFESTS for r in records(read(p)) if r['private_variant_name']=='zenata_age04')
            jobs=[j for j in atlas_jobs(zenata) if j['image'].resolve()==absolute(row['source_png']).resolve()
                  and '/humans/' in j['source_texture']]
            if len(jobs)!=1:raise ValueError('Zenata skin atlas is not its exact original human atlas')
            expected=jobs[0]['private_texture']
        if row['target_texture']!=expected:raise ValueError('Skin atlas targets a nonhuman or unrelated resource')
        verify_png(row)
    return rows


def baseline_hashes():
    if sha(BASE) != BASE_SHA:
        raise ValueError('Protected 0.5.0 package changed')
    evidence = read(OLD / 'package/EVIDENCE.json')['composition']
    if evidence['archive_sha256'] != BASE_SHA or not evidence['unaffected_members_sha256_identical']:
        raise ValueError('Original package composition proof missing')
    index_path = OLD / 'baseline-member-sha256.json'
    if sha(index_path) != evidence['source_hashes'][str(index_path.resolve())]:
        raise ValueError('Original baseline member index changed')
    result = read(index_path)
    result.update({r['member']:r['sha256'] for r in evidence['payloads']})
    if len(result) != 1524:
        raise ValueError('0.5.0 member closure differs')
    return result


def materials():
    payloads=[]; coverage=[]
    for path in MANIFESTS:
        for row in records(read(path)):
            name=row['private_variant_name']
            member=f'art/scenario/garrison/berber_units_050/{name}/{name}.rrmaterial'
            source=extract(member,OUT/'baseline-inputs/materials'/Path(member).name.replace('.rrmaterial',f'-{name}.rrmaterial'))
            if name == 'zenata_age04':
                if any(slot=='skinTintLUT' for c in rc.walk(rc.parse(source.read_bytes()).roots) if c.tag==b'PbTe' for slot,_ in texture_pairs(c.payload)):
                    raise ValueError('Zenata IV no-LUT assumption no longer holds')
                continue
            data,proof=replace_skin_lut(source.read_bytes())
            target=OUT/'payloads'/member; target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            payloads.append({'member':member,'file':str(target),'sha256':sha(target),'kind':'skin_palette_reference','proof':proof})
            coverage.append({'family':row['family'],'age':row['age'],'variant':name,'route':'skinTintLUT only','proof':proof})
    if len(payloads)!=48:
        raise ValueError('Expected exactly 48 native human skin palette materials')
    native=OUT/'baseline-inputs/eng_skin_tinting_lut.rrtex'
    if not native.exists():
        raise ValueError('Verified native fair palette source missing')
    target=OUT/'payloads'/LUT_MEMBER;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(rename_texture(native.read_bytes(),LUT_MEMBER))
    old=rrtex_decoder.decode_rrtex(native,validate_stream=True)
    new=rrtex_decoder.decode_rrtex(target,validate_stream=True)
    if old['mips']!=new['mips'] or old['projection']['sha256']!=new['projection']['sha256'] or (new['width'],new['height'])!=(20,3):
        raise ValueError('Native fair palette pixels/format changed')
    payloads.append({'member':LUT_MEMBER,'file':str(target),'sha256':sha(target),'kind':'private_native_fair_palette',
                     'proof':{'official_source':LUT_SOURCE,'official_source_sha256':sha(native),'all_native_palette_pixels_identical':True}})
    write(OUT/'material-payloads.json',{'status':'passed','payloads':payloads,'coverage':coverage})
    return payloads


def cook(rows):
    # Model variants are native texture carriers only. No carrier model is
    # admitted to the candidate. Native Garrison does not package orphan PNGs.
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    library=Path('F:/aoe_4_temp')/('berber051_cook_'+stamp)
    if library.exists():raise ValueError('Fresh cook directory already exists')
    run(CORE,'mod-project','create','--library',library,'--name','berber_skin_051')
    project=library/'Mods/berber_skin_051'
    run(CORE,'mod-project','settings','--project',project,'--live-reload','off','--mod-id',GUID)
    carrier_inputs=[]
    for row in rows:
        name=f"{row['family']}_age{row['age']}"
        source=absolute(row['authored_png'])
        original=extract(row['target_texture'],OUT/'baseline-inputs/old-textures'/f'{name}.rrtex')
        projection=original.with_suffix('.dds')
        info=rrtex_decoder.decode_rrtex(original,output_dds=projection,validate_stream=True)
        if info['projection']['format']=='BC1_UNORM_SRGB':
            if Image.open(projection).convert('RGBA').getchannel('A').getextrema()!=(255,255):
                raise ValueError('BC1 original has transparency; RGB carrier unsupported')
            source=library/'carrier-inputs'/f'{name}.png';source.parent.mkdir(exist_ok=True)
            Image.open(absolute(row['authored_png'])).convert('RGB').save(source)
        carrier_inputs.append(source)
        run(CORE,'mod-project','variant','--project',project,'--source',
            'art/civilizations/abbasids/humans/abb_ranged_bow_age02/abb_ranged_bow_age02','--name',name)
        run(CORE,'mod-project','variant-set','--project',project,'--name',name,'--slot','albedoTexture','--image',source)
    owner={'guid':GUID,'workspace':str(ROOT.resolve()),'project':str(project),'scope':'0.5.1 native texture-only cook carriers'}
    write(library/'.berber-051-owner.json',owner)
    if (OUT/'cook-project.json').exists():
        shutil.copy2(OUT/'cook-project.json',OUT/f'cook-project-previous-{stamp}.json')
    write(OUT/'cook-project.json',{'owned_root':str(library),'project':str(project),'owner_sha256':sha(library/'.berber-051-owner.json')})
    sources={str(p.resolve()):sha(p) for p in [Path(__file__),ROOT/'research/berber_051_release.py',
        ROOT/'research/berber_051_cleanup.py',ROOT/'Design/asset_overhaul/BERBER_051_REBUILD.md',*PNG_MANIFESTS,
        *[absolute(r[k]) for r in rows for k in ('authored_png','mask_png','source_png','source_owner_pattern')],
        OUT/'material-payloads.json',OUT/'baseline-inputs/eng_skin_tinting_lut.rrtex',*carrier_inputs,CORE,EDITOR,ARCH]}
    write(OUT/'frozen-inputs.json',sources)
    log=OUT/'texture-cook.log'
    with log.open('w',encoding='utf8') as stream:
        result=subprocess.run([str(CORE),'mod-project','cook','--project',str(project),'--editor',str(EDITOR),'--timeout','600'],stdout=stream,stderr=subprocess.STDOUT,timeout=660)
    if result.returncode:raise RuntimeError(f'Native texture cook failed; see {log}')
    if any(sha(p)!=digest for p,digest in sources.items()):raise ValueError('Frozen inputs changed during cook')
    record=read(project/'mod-project.json')['cooks'][-1]
    if record['live_reload'] is not False or sha(record['archive'])!=record['sha256']:raise ValueError('Native texture cook identity/Live Reload mismatch')
    write(OUT/'texture-cook.json',{'status':'passed','cook':record,'source_hashes':sources,'native_appearance':'pending'})
    return record


def textures(rows,record):
    if record['live_reload'] is not False or sha(record['archive'])!=record['sha256']:raise ValueError('Stale cook')
    if not json.loads(run(ARCH,'list',record['archive'],'--verify'))['archive']['verification']['verified']:
        raise ValueError('Native texture cook archive integrity failed')
    payloads=[]
    for row in rows:
        verify_png(row)
        name=f"{row['family']}_age{row['age']}"
        member=f'art/scenario/garrison/berber_skin_051/{name}/albedotexture.rrtex'
        source=OUT/'cook-readback'/record['build_id']/member
        run(ARCH,'extract-member',record['archive'],member,source)
        target=OUT/'payloads'/row['target_texture'];target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(rename_texture(source.read_bytes(),row['target_texture']))
        a=rrtex_decoder.decode_rrtex(source,validate_stream=True); b=rrtex_decoder.decode_rrtex(target,output_dds=target.with_suffix('.dds'),validate_stream=True)
        if a['mips']!=b['mips'] or a['projection']['sha256']!=b['projection']['sha256']:
            raise ValueError('Native identity rewrite changed image data')
        dims=Image.open(absolute(row['authored_png'])).size
        original=extract(row['target_texture'],OUT/'baseline-inputs/old-textures'/f"{name}.rrtex")
        original_info=rrtex_decoder.decode_rrtex(original,validate_stream=True)
        conversion=None
        if b['projection']['format']!=original_info['projection']['format']:
            if (original_info['projection']['format'],b['projection']['format'])!=('BC1_UNORM_SRGB','BC3_UNORM_SRGB'):
                raise ValueError('Unsupported native texture format conversion')
            # The installed native exporter always emits BC3. Prove its added
            # alpha remains fully opaque at every mip, matching the old BC1.
            blob=target.with_suffix('.dds').read_bytes();offset=148
            if blob[84:88]!=b'DX10' or struct.unpack_from('<I',blob,128)[0]!=78:
                raise ValueError('Unexpected native BC3 DDS projection')
            for mip in b['mips']:
                header=bytearray(blob[:148]);struct.pack_into('<I',header,128,77)
                struct.pack_into('<I',header,12,mip['height']);struct.pack_into('<I',header,16,mip['width']);struct.pack_into('<I',header,28,1)
                im=Image.open(BytesIO(header+blob[offset:offset+mip['size']])).convert('RGBA');offset+=mip['size']
                if im.getchannel('A').getextrema()!=(255,255):raise ValueError('Native export introduced transparency')
            conversion='native BC1 to BC3; identical fully opaque alpha verified at every mip'
        if ((b['width'],b['height'])!=dims or b['mip_count']!=max(dims).bit_length()):
            raise ValueError('Native skin texture dimensions/mips differ')
        payloads.append({'member':row['target_texture'],'file':str(target),'sha256':sha(target),'kind':'baked_exposed_skin_only',
            'proof':{'source':row,'native_stream_validated':True,'all_cooked_mips_preserved':True,'only_texture_identity_renamed':True,'native_format_conversion':conversion}})
    write(OUT/'texture-payloads.json',{'status':'passed','payloads':payloads})
    return payloads


def compose(payloads):
    expected=baseline_hashes()
    if len({p['member'] for p in payloads})!=54 or len(payloads)!=54:raise ValueError('Only 48 skin materials, five albedos and one palette are admitted')
    for row in payloads:
        if sha(row['file'])!=row['sha256']:raise ValueError('Payload changed')
    mapping=OUT/'texture-members.txt'
    mapping.write_text(''.join(f"{r['member']}={r['file']}\n" for r in payloads),encoding='utf8')
    candidate=OUT/'candidate.sga';run(ARCH,'set-members',BASE,mapping,candidate,'--alias','data')
    inventory=json.loads(run(ARCH,'list',candidate,'--verify'))
    if not inventory['archive']['verification']['verified'] or inventory['archive']['name'].replace('-','').lower()!=GUID.replace('-',''):
        raise ValueError('Candidate archive CRC/identity failed')
    rb=OUT/'candidate-readback';run(ARCH,'unpack',candidate,'--output',rb)
    actual={r['path']:sha(rb/r['path']) for r in inventory['members']}
    admitted={r['member']:r['sha256'] for r in payloads}
    if set(actual)!=set(expected)|{LUT_MEMBER}:raise ValueError('Member addition/removal outside one fair palette')
    changes={n for n in expected if actual[n]!=expected[n]}
    if changes != set(admitted)-{LUT_MEMBER} or any(actual[n]!=digest for n,digest in admitted.items()):
        raise ValueError('Final archive differs outside exact skin-only payloads')
    forbidden=('.rgm','.rgo','.rrgeom','.rgd','.scar','.wem','.spd','.rhka','.rootmotion')
    if any(n.endswith(forbidden) for n in changes):raise ValueError('Geometry/gameplay/animation change attempted')
    result={'status':'passed','version':'0.5.1','baseline_sha256':BASE_SHA,'archive':str(candidate),'archive_sha256':sha(candidate),
        'baseline_members':len(expected),'candidate_members':len(actual),'changed_members':sorted(changes),'new_members':[LUT_MEMBER],
        'unchanged_members':len(expected)-len(changes),'all_geometry_rigs_animations_attributes_audio_buildings_byte_identical':True,
        'payloads':payloads,'native_appearance_and_player_colour':'pending fresh-match testing'}
    write(OUT/'composition-report.json',result)
    return result


def build(do_cook):
    baseline_hashes(); rows=png_rows(); material=materials()
    record=cook(rows) if do_cook else read(OUT/'texture-cook.json')['cook']
    if any(sha(p)!=digest for p,digest in read(OUT/'texture-cook.json')['source_hashes'].items()):
        raise ValueError('Texture cook inputs are stale')
    result=compose(material+textures(rows,record))
    print('051_SKIN_ONLY_CANDIDATE_VALIDATED',result['archive_sha256'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cook',action='store_true')
    args=parser.parse_args();build(args.cook)
