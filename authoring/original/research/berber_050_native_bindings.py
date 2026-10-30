"""Visual-only actor patches from frozen native RGDs, without source rebuilding."""
from __future__ import annotations
import argparse
import copy
import sys
from pathlib import Path
from berber_050_common import CORE, ARCH, EXT, GUID, OUT, ROOT, read, run, sha, write
from berber_050_project import PROJECT, ensure_project
sys.path.insert(0, str(EXT))
from garrison_shared import rgd

OFFICIAL = Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga')
KING = 'ebps/races/malian/units/unit_king_1_mal'
PBG_GUID = GUID.replace('-', '')
TIER = 'default/tier_ext/tier_group_list/tier_group/tier'


def semantics(nodes):
    return [(n.key, n.hash, n.kind, semantics(n.value) if isinstance(n.value, list) else n.value) for n in nodes]


def encode(doc):
    keys = {h: k for h, k in doc.keys}
    for _, node in rgd.flatten(doc.nodes):
        if node.key is not None:
            keys[node.hash] = node.key
    doc.keys = list(keys.items())
    data = rgd.write(doc)
    if semantics(rgd.read(data).nodes) != semantics(doc.nodes):
        raise ValueError('Native RGD roundtrip changed semantics')
    return data


def nodes(doc):
    return dict(rgd.flatten(doc.nodes))


def field(doc, path):
    lookup = nodes(doc)
    if path not in lookup and 'default/' + path in lookup:
        path = 'default/' + path
    if path not in lookup:
        raise ValueError(f'Exact native field absent: {path}')
    return path, lookup[path]


def source_actor(actor):
    member = 'attrib/' + actor + '.rgd'
    source = OUT / 'integration/baseline-readback' / member
    if not source.exists():
        source = OUT / 'official-inputs' / member
        if not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            run(ARCH, 'extract-member', OFFICIAL, member, source)
    return member, source


def candidate_manifest():
    data = read(OUT / 'bindings/private-source/derive-candidates.json')
    candidates = copy.deepcopy(data['candidates'])
    # Keep the native trader male/female selectors and distinct body contracts.
    for row in candidates:
        if row['family'] == 'trader':
            for change in row['field_changes']:
                if '_female_' in change['source_value']:
                    name = f"trader_age0{row['target_age']}_female"
                    change['value'] = f'art/scenario/garrison/berber_units_050/{name}/{name}'
    # King uses one official attachment schema; only its body reference changes.
    for age in range(1, 5):
        name = f'king_age0{age}'
        candidates.append({'family': 'king', 'target_age': age,
            'source_blueprint': 'attachments/attachment_lists/races/malian/units/unit_king_1_mal',
            'derived_name': f'bind_king_a{age}_unit_king_1_mal',
            'field_changes': [{'field': 'attachment_lists/attachment_lists/attachment_list/attachment_list/animator_skin_attachment/animator',
                'source_value': 'art/civilizations/malian/humans/mal_infantry_light_age04/mal_infantry_light_age04',
                'value': f'art/scenario/garrison/berber_units_050/{name}/{name}'}]})
    # A native list can contain campaign/xp3 variants whose model differs from
    # default. Retain each distinct native body/state instead of collapsing its
    # rig or equipment into a shared alias. Garrison's derive-change applies a
    # relative field to every native table; exact table overrides are restored
    # from this manifest after the native cook and verified during readback.
    allocations = {}
    model_rows = {}
    scoped_sources = {}
    for candidate in candidates:
        for change in candidate['field_changes']:
            base_name = change['value'].rsplit('/', 1)[-1]
            scoped_sources.setdefault(base_name, set()).add(change['source_value'].replace('\\', '/').removesuffix('.rgm'))
    for candidate in candidates:
        _, source = source_actor(candidate['source_blueprint'])
        doc = rgd.read(source.read_bytes())
        lookup = nodes(doc)
        tables = [n.key for n in doc.nodes if isinstance(n.value, list)]
        resolved = {}
        for change in candidate['field_changes']:
            base_name = change['value'].rsplit('/', 1)[-1]
            for table in tables:
                path = table + '/' + change['field']
                if path not in lookup:
                    continue
                native_source = lookup[path].value.replace('\\', '/').removesuffix('.rgm')
                if table != 'default' and native_source not in scoped_sources[base_name]:
                    # E.g. campaign King Harold is not the Malian Regicide
                    # actor appearance. Preserve unselected native alternate
                    # content exactly; do not turn it into a new mod unit.
                    resolved[path] = {'table': table, 'field': change['field'],
                        'source_value': native_source, 'value': lookup[path].value,
                        'preserve_unselected_native_variant': True}
                    continue
                allocation_source = native_source
                if candidate['family'] == 'lancer' and '/chinese/' in native_source:
                    # This very same frozen actor already consumes the regional
                    # donor in its default table. Use that qualified native body
                    # for the Cordoba visual branch too; retain Chinese weapon
                    # selectors and every nonbody field in the private list.
                    age = candidate['target_age']
                    civ, prefix = ('abbasids', 'abb') if age == 3 else ('sultanate', 'sul')
                    allocation_source = f'art/civilizations/{civ}/animals/{prefix}_horse_combined_armor_age0{age}/{prefix}_horse_combined_armor_age0{age}'
                sources = allocations.setdefault(base_name, [])
                if allocation_source not in sources:
                    sources.append(allocation_source)
                part = sources.index(allocation_source) + 1
                name = base_name if part == 1 else base_name + f'_part{part:02}'
                stem = f'art/scenario/garrison/berber_units_050/{name}/{name}'
                resolved[path] = {'table': table, 'field': change['field'],
                    'source_value': native_source, 'value': stem}
                record = model_rows.setdefault(name, {'private_variant_name': name,
                    'family': candidate['family'], 'age': candidate['target_age'],
                    'source_model': allocation_source, 'source_consumer_models': [], 'private_stem': stem,
                    'state': 'upgrade' if '_upgrade' in base_name else 'body', 'consumers': []})
                record['consumers'].append({'attachment': candidate['derived_name'], 'field': path})
                if native_source not in record['source_consumer_models']:
                    record['source_consumer_models'].append(native_source)
                if table == 'default':
                    change['value'] = stem
        candidate['resolved_field_changes'] = list(resolved.values())
    write(OUT / 'bindings/model-routes.json', {'status': 'native_routes_resolved',
        'models': list(model_rows.values()),
        'policy': 'Distinct native models and conditional states have distinct private variants; no cross-donor skin/rest transplantation.'})
    data['candidates'] = candidates
    data['candidate_count'] = len(candidates)
    data['project'] = str(PROJECT)
    data['native_actor_patch_policy'] = 'Frozen native RGD actor identity and all nonvisual fields preserved; King alone adds visual-only age gates.'
    write(OUT / 'bindings/final-candidates.json', data)
    return data


def actor_changes(data):
    changes = {}
    candidates = {(r['family'], r['target_age'], r['source_blueprint']): r for r in data['candidates']}
    plan = read(OUT / 'bindings/plan.json')
    for row in plan['rows']:
        if row['family'] == 'tuareg':
            continue
        actor = row['actor']['actor_pbg']
        for route in row['visual_routes']:
            source = route.get('typed_source_blueprint') or route['attachment_ref']
            candidate = candidates[(row['family'], route['target_age'], source)]
            value = PBG_GUID + ':' + candidate['derived_name']
            entry = changes.setdefault(actor, {})
            path = route['actor_tier_field']
            if path in entry and entry[path] != value:
                raise ValueError(f'Conflicting actor stage: {actor}:{path}')
            entry[path] = value
    return changes


def patch_actor(source, changes, king=False):
    original = rgd.read(Path(source).read_bytes())
    doc = copy.deepcopy(original)
    applied = {}
    for path, value in changes.items():
        canonical, node = field(doc, path)
        if not canonical.endswith('/attachments/$PBGNAME') or '/tier_ext/' not in canonical:
            raise ValueError('Only native tier attachment references may change')
        if node.kind != 'CString':
            raise ValueError('Native attachment reference type changed')
        applied[canonical] = {'before': node.value, 'after': value}
        node.value = value
    if king:
        _, group = field(doc, TIER.rsplit('/', 1)[0])
        tiers = [n for n in group.value if n.key == 'tier']
        if len(tiers) != 1:
            raise ValueError('Expected one original King visual tier')
        template = tiers[0]
        for age, requirement in ((2, 'feudal_age'), (3, 'castle_age'), (4, 'imperial_age')):
            tier = copy.deepcopy(template)
            local = dict(rgd.flatten([tier]))
            local['tier/attachments/$PBGNAME'].value = PBG_GUID + f':bind_king_a{age}_unit_king_1_mal'
            local['tier/statetree_tier_requirements_pbg/$PBGNAME'].value = requirement
            local['tier/statetree_tier_requirements_pbg/$PBGMAP'].value = 'upgrade'
            for target in ('entity', 'squad'):
                assert local[f'tier/statetree_tier_pgb_upgrade_target_{target}/$PBGNAME'].value == ''
            group.value.append(tier)
    verify_actor(original, doc, applied, king)
    return encode(doc), applied


def verify_actor(original, candidate, applied, king=False):
    restored = copy.deepcopy(candidate)
    if king:
        _, group = field(restored, TIER.rsplit('/', 1)[0])
        tiers = [n for n in group.value if n.key == 'tier']
        if len(tiers) != 4:
            raise ValueError('King must have exactly four visual tiers')
        template = copy.deepcopy(tiers[0])
        for age, tier in enumerate(tiers[1:], 2):
            local = dict(rgd.flatten([tier]))
            expected = {2: 'feudal_age', 3: 'castle_age', 4: 'imperial_age'}[age]
            if (local['tier/attachments/$PBGNAME'].value != PBG_GUID + f':bind_king_a{age}_unit_king_1_mal'
                or local['tier/statetree_tier_requirements_pbg/$PBGNAME'].value != expected
                or local['tier/statetree_tier_requirements_pbg/$PBGMAP'].value != 'upgrade'):
                raise ValueError('King visual attachment or native age requirement invalid')
            normalized = copy.deepcopy(tier)
            norm = dict(rgd.flatten([normalized]))
            ref = dict(rgd.flatten([template]))
            for path in ('tier/attachments/$PBGNAME', 'tier/statetree_tier_requirements_pbg/$PBGNAME', 'tier/statetree_tier_requirements_pbg/$PBGMAP'):
                norm[path].value = ref[path].value
            if semantics([normalized]) != semantics([template]):
                raise ValueError('King added tier modifies behavior beyond visual age requirements')
        group.value = [n for n in group.value if n not in tiers[1:]]
    for path, change in applied.items():
        _, node = field(restored, path)
        if node.value != change['after']:
            raise ValueError(f'Actor reference differs from expected binding: {path}')
        node.value = change['before']
    if semantics(restored.nodes) != semantics(original.nodes):
        raise ValueError('Actor gameplay/identity changed outside admitted visual tier references')


def prepare_actors(data):
    changes = actor_changes(data)
    changes[KING] = {TIER + '/attachments/$PBGNAME': PBG_GUID + ':bind_king_a1_unit_king_1_mal'}
    rows = []
    for actor, fields in sorted(changes.items()):
        member, source = source_actor(actor)
        payload, applied = patch_actor(source, fields, actor == KING)
        dest = OUT / 'integration/actor-payloads' / member
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        rows.append({'member': member, 'file': str(dest), 'sha256': sha(dest),
            'source': str(source), 'source_sha256': sha(source), 'changed_fields': applied,
            'semantic_undo_proof': 'passed', 'king_visual_age_extension': actor == KING})
    write(OUT / 'bindings/actor-payloads.json', {'status': 'passed', 'payloads': rows})
    return rows


def register_bindings(data):
    ensure_project()
    for candidate in data['candidates']:
        known = {r['name']: r for r in read(PROJECT / 'mod-project.json').get('derived_blueprints', [])}
        name, source = candidate['derived_name'], candidate['source_blueprint']
        if name in known and known[name]['source'] != source:
            raise ValueError(f'Private blueprint collision: {name}')
        if name not in known:
            run(CORE, 'mod-project', 'derive', '--project', PROJECT, '--source', source, '--name', name)
        for change in candidate['field_changes']:
            run(CORE, 'mod-project', 'derive-change', '--project', PROJECT, '--name', name,
                '--field', change['field'], '--value', change['value'])
    write(OUT / 'bindings/registration.json', {'status': 'passed', 'count': len(data['candidates']),
        'project_sha256': sha(PROJECT / 'mod-project.json'), 'native_cook': 'pending'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', action='store_true')
    args = parser.parse_args()
    data = candidate_manifest()
    result = prepare_actors(data)
    if args.register:
        register_bindings(data)
    print(f'Native actor patches with gameplay undo proof: {len(result)}')
