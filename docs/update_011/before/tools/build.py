"""Portable source -> supported Garrison assembly -> verified player ZIP.

Requires Python 3.13 and the installed 0.1.8 authoring SDK/core. No original
Berber project, experiment output or Blender scene participates in this build.
"""
import argparse
import hashlib
import shutil
import subprocess
import zipfile
from pathlib import Path
from runtime import ROOT, EXT, read_json, write_json, import_table, stock_game, mod_bundle, rgd


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def run(args, log):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    Path(log).write_text(result.stdout+'\n'+result.stderr, encoding='utf-8')
    assert result.returncode == 0, f'Command failed; inspect {log}'


def build(output):
    config = read_json(ROOT/'project.json')
    assert not output.exists(), f'Use an empty build destination: {output}'
    output.mkdir(parents=True)
    native_root = ROOT/config['native_inputs']
    native_manifest = read_json(ROOT/'inputs/native-manifest.json')
    for member, row in native_manifest.items():
        path = native_root/member
        assert path.is_file() and path.stat().st_size == row['bytes'], path
        assert digest(path) == row['sha256'], path
    recipe = {k:config[k] for k in ('schema','owner','race','dispatcher','shared_entities')}
    recipe.update(attributes=[], members=[])
    baseline = read_json(ROOT/'source/baseline-members.json')
    expected = {}
    inputs = output/'prepared'
    def add(member, raw, toc):
        path = inputs/member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        row = {'member': member, 'file':str(path.resolve()), 'sha256':hashlib.sha256(raw).hexdigest()}
        if toc == 'attrib':
            recipe['attributes'].append(row)
        else:
            row['toc']=toc
            recipe['members'].append(row)
        expected[member]={'toc':toc,'sha256':row['sha256'],'bytes':len(raw)}
    for member in sorted(native_manifest):
        assert not Path(member).is_absolute() and '..' not in Path(member).parts
        add(member,(native_root/member).read_bytes(),baseline[member]['toc'])
    for path in sorted((ROOT/'source/tables').rglob('*.rgd.json')):
        add(path.relative_to(ROOT/'source/tables').as_posix()[:-5],import_table(read_json(path)),'attrib')
    for path in sorted((ROOT/'source/resources').rglob('*')):
        if path.is_file():
            member=path.relative_to(ROOT/'source/resources').as_posix()
            add(member,path.read_bytes(),baseline.get(member,{}).get('toc','data'))
    for path in sorted((ROOT/'source/scar').rglob('*.scar')):
        add('scar/'+path.relative_to(ROOT/'source/scar').as_posix(),path.read_bytes(),'data')
    assert expected['mod.bin']['toc']=='info' and expected['mod.rrtex']['toc']=='info'
    write_json(output/'build-recipe.json',recipe)
    core=EXT/'bin/core/garrison-core.exe'
    run([core,'civilization','validate',output/'build-recipe.json'],output/'validate.log')
    run([core,'civilization','build',output/'build-recipe.json','--output',output/'assembly'],output/'assembly.log')
    report=read_json(output/'assembly/report.json')
    archive=Path(report['archive'])
    game=stock_game.current()
    listing=game.archiver.run(['list',str(archive),'--verify'])
    assert listing['archive']['name']==config['owner'].replace('-','')
    assert listing['archive']['verification']['verified']
    readback=output/'readback'
    game.archiver.run(['extract',str(archive),str(readback),'--filter',''])
    actual={m['path']:m for m in listing['members']}
    assert set(actual)==set(report['members'])
    for member,row in report['members'].items():
        assert actual[member]['toc']==row['toc']
        assert digest(readback/member)==row['sha256'],member
    for member,row in expected.items():
        if member==config['dispatcher']:
            assert (readback/member).read_bytes().endswith((inputs/member).read_bytes())
        else:
            assert report['members'][member]['sha256']==row['sha256'],member
    decl=read_json(readback/'garrison/civilizations.json')
    for entry in [decl['attribute_root']]+decl['races']+decl['scripts']:
        assert digest(readback/entry['member'])==entry['sha256']
    root=rgd.read((readback/'attrib/berbers.rgd').read_bytes())
    assert [n.value for _,n in rgd.flatten(root.nodes) if n.key=='override_instances']==[False]
    baseline=read_json(ROOT/'source/baseline-members.json')
    changed=[m for m in sorted(set(baseline)&set(report['members'])) if baseline[m]!=report['members'][m]]
    removed=sorted(set(baseline)-set(report['members']))
    added=sorted(set(report['members'])-set(baseline))
    policy=read_json(ROOT/'source/release-changes.json')
    assert set(changed)==set(policy['changed']),changed
    assert removed==sorted(policy['removed']),removed
    assert added==sorted(policy['added']),added
    # Final native-table preservation: all numeric/Boolean gameplay leaves
    # retain the owner-tested baseline. SHA checks cover unedited records.
    preserved_art_audio=[m for m in baseline if m.startswith(('art/','audio/'))]
    for m in preserved_art_audio:
        assert report['members'][m]==baseline[m],m
    receipt={'version':config['version'],'archive_sha256':digest(archive),
             'archive_bytes':archive.stat().st_size,'verified_members':len(actual),
             'all_members_read_back':True,'native_crc_sha1_verified':True,
             'preserved_art_audio_members':len(preserved_art_audio),
             'changed_members':changed,'removed_members':removed,'added_members':added,
             'clean_source_rebuild':True,'native_flag_retest':'pending',
             'native_game_acceptance':'Owner accepted trial.3; this flag-only release needs visual retest.'}
    write_json(output/'verification.json',receipt)
    notes=(ROOT/'START-HERE.md').read_text(encoding='utf-8')
    for name in ('hossein81','marcokistan','Karyu','lammet','ForsakenCryz'):
        assert name in notes,name
    details={'id':'berbers','name':'Berbers','version':config['version'],
             'summary':'The Berber Dynasties: tribal alliances, desert warriors and trade.',
             'description':'Independent Berber civilization. Select Berbers with Standard and Tuning Pack=None.',
             'author':'hosein81 and marcokistan','updated':'2026-10-30','min_garrison':'0.1.9',
             'content_types':['civilization'],'cover':'cover.png',
             'changelog':'Owner-tested trial.3 gameplay preserved. Civilization flags now use the original Villager banner. Editable source, art and audio are available together in the GitHub repository.'}
    delivery=output/'delivery';delivery.mkdir()
    package=delivery/('Berbers-Garrison-'+config['version']+'.zip')
    mod_bundle.write_package(delivery/'package',package,bundle_key=config['bundle_key'],details=details,
                             archives=[('berbers','civilization',archive)],start_here=notes,
                             cover=ROOT/'source/presentation/berbers.png')
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        manifests=[n for n in z.namelist() if Path(n).name=='garrison.json']
        assert len(manifests)==1
        bundle=__import__('json').loads(z.read(manifests[0]))
        assert len(bundle['members'])==1
        member=bundle['members'][0]
        assert member['role']=='civilization' and member['sha256']==receipt['archive_sha256']
        prefix=manifests[0][:-len('garrison.json')]
        with z.open(prefix+member['path']) as f:
            assert hashlib.file_digest(f,'sha256').hexdigest()==receipt['archive_sha256']
    receipt.update(zip_name=package.name,zip_bytes=package.stat().st_size,zip_sha256=digest(package),zip_crc_verified=True)
    write_json(output/'verification.json',receipt)
    print(__import__('json').dumps(receipt,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'output/current');args=p.parse_args()
    build(args.output.resolve())
