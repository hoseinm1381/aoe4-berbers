"""Compose admitted private unit payloads onto the immutable packaged 0.4.0."""
from __future__ import annotations
import argparse
import json
from pathlib import Path, PurePosixPath
from berber_050_common import ARCH, BASE, BASE_SHA, GUID, OUT, read, run, sha, write
from berber_050_admission import admit_coverage, admit_cook, changed_members


def gather_payloads(manifests):
    payloads = {}
    for manifest in manifests:
        for row in read(manifest)['payloads']:
            member = row['member']
            parsed = PurePosixPath(member)
            if ('\\' in member or parsed.is_absolute() or '..' in parsed.parts
                    or parsed.as_posix() != member or not member.startswith(('art/', 'attrib/'))):
                raise ValueError(f'Invalid release payload member: {member}')
            key = member.lower()
            if key in payloads:
                old = payloads[key]
                if old['member'] != member or old['sha256'] != row['sha256']:
                    raise ValueError(f'Conflicting payload: {member}')
            if sha(row['file']) != row['sha256']:
                raise ValueError(f'Stale payload bytes: {member}')
            payloads[key] = dict(row)
    if not payloads:
        raise ValueError('No admitted unit payloads')
    return payloads


def compose(coverage_path, cook_path, source_hashes_path, semantic_path, manifests):
    if sha(BASE) != BASE_SHA:
        raise ValueError('Packaged 0.4.0 baseline changed')
    coverage = read(coverage_path)
    admit_coverage(coverage)
    recorded_sources = read(source_hashes_path)
    current_sources = {path: sha(path) for path in recorded_sources}
    if current_sources != recorded_sources:
        raise ValueError('Authoring inputs changed after their source snapshot')
    admit_cook(read(cook_path), current_sources)
    semantic = read(semantic_path)
    if semantic.get('status') != 'passed':
        raise ValueError('Compiled unit gameplay/visual-only semantic check required')
    payloads = gather_payloads(manifests)
    expected_payloads = {row['member']: row['sha256'] for row in payloads.values()}
    if semantic.get('payload_hashes') != expected_payloads:
        raise ValueError('Semantic validation does not cover the exact current payloads')
    working = OUT / 'integration'
    current = BASE
    for alias, prefix in (('data', 'art/'), ('attrib', 'attrib/')):
        rows = [r for r in payloads.values() if r['member'].startswith(prefix)]
        if not rows:
            continue
        mapping = working / (alias + '-members.txt')
        mapping.write_text(''.join(f"{r['member']}={r['file']}\n" for r in rows), encoding='utf8')
        candidate = working / (alias + '-candidate.sga')
        run(ARCH, 'set-members', current, mapping, candidate, '--alias', alias)
        current = candidate
    inventory = json.loads(run(ARCH, 'list', current, '--verify'))
    if not inventory['archive']['verification']['verified']:
        raise ValueError('Candidate archive verification failed')
    if inventory['archive']['name'].replace('-', '').lower() != GUID.replace('-', ''):
        raise ValueError('Candidate project identity changed')
    readback = working / ('candidate-readback-' + sha(current)[:12])
    if not readback.exists():
        run(ARCH, 'unpack', current, '--output', readback)
    members = {r['path']: sha(readback / r['path']) for r in inventory['members']}
    baseline = read(OUT / 'baseline-member-sha256.json')
    differences = changed_members(baseline, members, set(expected_payloads))
    if set(members) != set(baseline) | set(expected_payloads):
        raise ValueError('Candidate archive member set differs from admitted payloads')
    for member, digest in expected_payloads.items():
        if members[member] != digest:
            raise ValueError(f'Final readback mismatch: {member}')
    result = {'status': 'passed', 'version': '0.5.0', 'baseline': str(BASE),
              'baseline_sha256': BASE_SHA, 'archive': str(current), 'archive_sha256': sha(current),
              'readback': str(readback), 'project_guid': GUID,
              'baseline_members': len(baseline), 'candidate_members': len(members),
              'payloads': list(payloads.values()), 'differences': differences,
              'source_hashes': current_sources,
              'unaffected_members_sha256_identical': True,
              'archive_crc_sha1_verified': True, 'native_acceptance': 'pending'}
    write(working / 'composition-report.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coverage', type=Path, required=True)
    parser.add_argument('--cook', type=Path, required=True)
    parser.add_argument('--source-hashes', type=Path, required=True)
    parser.add_argument('--semantics', type=Path, required=True)
    parser.add_argument('manifests', nargs='+', type=Path)
    args = parser.parse_args()
    result = compose(args.coverage, args.cook, args.source_hashes, args.semantics, args.manifests)
    print('050_COMPOSITION_VERIFIED', result['archive_sha256'])
