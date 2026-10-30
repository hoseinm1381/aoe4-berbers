"""Fail-closed release admission; these checks do not establish native acceptance."""
from __future__ import annotations
import re

EXPECTED = {
    'villager': (1, 2, 3, 4), 'scout': (1, 2, 3, 4), 'tuareg': (1, 2, 3, 4),
    'trader': (2, 3, 4), 'mehari': (2, 3, 4), 'sanhaja': (2, 3, 4),
    'zenata': (2, 3, 4), 'archer': (2, 3, 4), 'masmuda': (2, 3, 4),
    'lancer': (3, 4), 'imam': (3, 4), 'handgunner': (4,), 'king': (1, 2, 3, 4),
}

def admit_coverage(report):
    rows = report['rows']
    seen = set()
    for row in rows:
        key = (row['family'], row['age'])
        if key in seen:
            raise ValueError(f'Duplicate coverage: {key}')
        seen.add(key)
        if row['family'] == 'tuareg' and row['status'] == 'preserved_accepted':
            continue
        if row['status'] != 'export_verified' or row.get('geometry_modified') is not True:
            raise ValueError(f'Unqualified unique geometry: {key}')
        if not re.fullmatch('[0-9a-f]{64}', row.get('donor_sha256', '')):
            raise ValueError(f'Missing donor provenance: {key}')
        if row.get('owner_colour_contract') != 'native_dynamic':
            raise ValueError(f'Unqualified dynamic owner colour: {key}')
        if not row.get('resources'):
            raise ValueError(f'Missing model resources: {key}')
    required = {(family, age) for family, ages in EXPECTED.items() for age in ages}
    if required - seen:
        raise ValueError(f'Missing coverage: {sorted(required - seen)}')
    return rows

def admit_cook(report, current_sources):
    if report.get('status') != 'passed' or report.get('live_reload') is not False:
        raise ValueError('Fresh successful Live Reload-off cook required')
    if not current_sources or report.get('source_hashes') != current_sources:
        raise ValueError('Cook source hashes are stale or absent')
    return True

def changed_members(baseline, candidate, allowlist):
    removed = set(baseline) - set(candidate)
    if removed:
        raise ValueError(f'Baseline members removed: {sorted(removed)}')
    changed = {name for name in baseline if baseline[name] != candidate[name]}
    new = set(candidate) - set(baseline)
    unexpected = (changed | new) - set(allowlist)
    if unexpected:
        raise ValueError(f'Archive changes outside allowlist: {sorted(unexpected)}')
    return {'changed': sorted(changed), 'new': sorted(new),
            'unchanged': len(baseline) - len(changed)}
