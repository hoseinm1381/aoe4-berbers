"""Package only a completely admitted 0.5.0 candidate; native tests stay pending."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from berber_050_common import BASE, BASE_SHA, GUID, OUT, ROOT, read, sha, write
from berber_050_admission import admit_coverage

REQUIRED = {'Berber_future_kingdom.sga', 'garrison.json', 'EVIDENCE.json',
            'INSTALL_AND_TEST.txt', 'COVERAGE.json', 'MODEL_REVIEW.html', 'REBUILD_050.md'}

def verify_zip(path, expected_sga_sha):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC validation failed')
        names = archive.namelist()
        if len(names) != len(set(names)) or not REQUIRED <= set(names):
            raise ValueError('Duplicate or missing release ZIP members')
        if any(Path(n).is_absolute() or '..' in Path(n).parts or '\\' in n for n in names):
            raise ValueError('Unsafe ZIP member name')
        digest = hashlib.sha256(archive.read('Berber_future_kingdom.sga')).hexdigest()
        if digest != expected_sga_sha:
            raise ValueError('Packaged SGA hash does not match validated archive')
        manifest = json.loads(archive.read('garrison.json'))
        if manifest['details']['version'] != '0.5.0' or manifest['members'][0]['sha256'] != digest:
            raise ValueError('Release version or manifest hash mismatch')
        admit_coverage(json.loads(archive.read('COVERAGE.json')))
        return {'zip_readable': True, 'members': names, 'sga_sha256': digest,
                'manifest_version': '0.5.0', 'native_acceptance': 'pending'}

def package(coverage_path, review_path, rebuild_path, review_images):
    if sha(BASE) != BASE_SHA:
        raise ValueError('0.4.0 baseline changed')
    coverage = read(coverage_path)
    rows = admit_coverage(coverage)
    composition = read(OUT / 'integration/composition-report.json')
    source = Path(composition['archive'])
    if composition['status'] != 'passed' or sha(source) != composition['archive_sha256']:
        raise ValueError('Current candidate has not passed final composition verification')
    if not composition.get('source_hashes'):
        raise ValueError('Final composition has no frozen authoring input hashes')
    for path, expected in composition['source_hashes'].items():
        if sha(path) != expected:
            raise ValueError(f'Authoring inputs changed after composition: {path}')
    for row in composition['payloads']:
        if sha(row['file']) != row['sha256']:
            raise ValueError(f"Admitted payload changed: {row['member']}")
    preservation = read(OUT / 'baseline-preservation.json')
    for relative, expected in preservation['source_files'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f'Original source changed outside private candidate: {relative}')
    destination = OUT / 'package'
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination / 'Berber_future_kingdom.sga')
    manifest = read(BASE.parent / 'garrison.json')
    manifest['members'][0]['sha256'] = sha(source)
    manifest['details'].update(version='0.5.0', updated='2026-10-16',
        summary='Berber land-unit visual overhaul with age variants',
        description='Donor-derived Berber land-unit art and age appearances. '
                    'Accepted Tuareg and 0.4.0 buildings preserved. Siege and navy unchanged. '
                    'Native appearance, animation and player-color acceptance pending.',
        changelog='Private unit models, age appearances and visual-only bindings; gameplay preserved.')
    write(destination / 'garrison.json', manifest)
    write(destination / 'COVERAGE.json', coverage)
    evidence = {'version': '0.5.0', 'guid': GUID, 'baseline_sha256': BASE_SHA,
                'sga_sha256': sha(source), 'coverage_entries': len(rows),
                'composition': composition, 'native_appearance': 'pending',
                'native_player_colour': 'pending', 'native_animations': 'pending',
                'import_and_lobby_selection': 'pending',
                'cleanup_report': 'Retained beside delivery after verified release cleanup.'}
    write(destination / 'EVIDENCE.json', evidence)
    shutil.copy2(review_path, destination / 'MODEL_REVIEW.html')
    shutil.copy2(rebuild_path, destination / 'REBUILD_050.md')
    for image in review_images:
        target = destination / 'review' / Path(image).name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and sha(target) != sha(image):
            raise ValueError(f'Conflicting review image filename: {image}')
        shutil.copy2(image, target)
    (destination / 'INSTALL_AND_TEST.txt').write_text(
        'BERBER 0.5.0 CANDIDATE — native acceptance pending\n\n'
        'Close AoE4, import this ZIP into Garrison and enable Berber. Start a fresh '
        'match selecting Tuning Pack The Berber Dynasties, Game Mode Berber Civilization '
        'and civilization Malians. Retain the packaged 0.4.0 ZIP for rollback.\n\n'
        'Test every COVERAGE.json entry in two different player colors. Check training, '
        'military tier upgrades, existing civilian age transitions, near/far LODs, '
        'idle/move/turn/stop, weapons/attacks/reload/charge/brace/torch/death as applicable. '
        'Check villager tasks/tools/carry loads, trader cargo/routes and Imam relic '
        'pickup/carry/drop/deposit/healing/conversion. Check rider/mount seat, saddle, '
        'harness and weapon contact during movement. For civilian aging, verify '
        'entity identity and gameplay remain intact. Verify existing buildings and '
        'accepted Tuareg remain unchanged.\n\n'
        'Cook/readback/ZIP checks do not prove import, lobby selection, native '
        'appearance, dynamic player color or animation behavior.\n', encoding='utf8')
    archive_path = OUT / 'berber_future_kingdom-0.5.0.zip'
    with ZipFile(archive_path, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(destination).as_posix())
    result = verify_zip(archive_path, sha(source))
    result.update(status='passed', zip=str(archive_path), zip_sha256=sha(archive_path),
                  sga=str(destination / 'Berber_future_kingdom.sga'), baseline_sha256=BASE_SHA)
    write(OUT / 'release-validation.json', result)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coverage', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--rebuild', type=Path, required=True)
    parser.add_argument('--review-images', nargs='*', type=Path, default=[])
    args = parser.parse_args()
    package(args.coverage, args.review, args.rebuild, args.review_images)
