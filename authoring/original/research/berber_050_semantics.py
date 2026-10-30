"""Read back cooked attachments and prove only admitted visual fields changed."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from berber_050_common import ARCH, OUT, read, run, sha, write
from berber_050_native_bindings import OFFICIAL, PBG_GUID, encode, field, nodes, rgd, semantics
from berber_050_admission import EXPECTED, admit_coverage


def attachments(cook_path):
    receipt = read(cook_path)
    if receipt['status'] != 'passed' or receipt['live_reload'] is not False:
        raise ValueError('Fresh successful native cook required')
    cook = receipt['cook']
    if sha(cook['archive']) != cook['sha256']:
        raise ValueError('Cook archive changed')
    rb = OUT / 'integration' / ('semantic-cook-readback-' + cook['sha256'][:12])
    if not rb.exists():
        run(ARCH, 'unpack', cook['archive'], '--output', rb)
    cooked = {r['name']: r for r in cook['derived_blueprints']}
    candidates = {r['derived_name']: r for r in read(OUT / 'bindings/final-candidates.json')['candidates']}
    if set(cooked) != set(candidates):
        raise ValueError('Cooked private attachments differ from the full routed candidate set')
    rows = []
    ids = set()
    for name, expected in candidates.items():
        actual = cooked[name]
        if actual['reference'] != PBG_GUID + ':' + name or actual['source'] != expected['source_blueprint']:
            raise ValueError(f'Cooked private blueprint identity mismatch: {name}')
        member = 'attrib/' + actual['file'] + '.rgd'
        cooked_path = rb / member
        source_member = 'attrib/' + expected['source_blueprint'] + '.rgd'
        source = OUT / 'official-inputs' / source_member
        if not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            run(ARCH, 'extract-member', OFFICIAL, source_member, source)
        original = rgd.read(source.read_bytes())
        candidate = rgd.read(cooked_path.read_bytes())
        scoped_patches = {}
        for change in expected['resolved_field_changes']:
            canonical = change['table'] + '/' + change['field']
            _, node = field(candidate, canonical)
            if node.kind != 'CString' or '/attachment_lists/' not in canonical:
                raise ValueError('Scoped native override must be a selected mesh model CString')
            if node.value != change['value']:
                scoped_patches[canonical] = {'cooked': node.value, 'scoped': change['value']}
                node.value = change['value']
        path = OUT / 'integration/attachment-payloads' / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(candidate))
        restored = copy.deepcopy(candidate)
        source_nodes = nodes(original)
        restored_nodes = nodes(restored)
        changed = {}
        for change in expected['resolved_field_changes']:
            canonical, node = field(restored, change['table'] + '/' + change['field'])
            if not canonical.startswith(change['table'] + '/attachment_lists/'):
                raise ValueError('Unadmitted attachment change outside native mesh model fields')
            if node.kind != 'CString' or node.value != change['value']:
                raise ValueError(f'Private model binding mismatch: {name}:{canonical}')
            before = source_nodes[canonical].value
            if before.replace('\\', '/') != change['source_value'].replace('\\', '/'):
                raise ValueError(f'Source native model provenance mismatch: {name}:{canonical}')
            if not change.get('preserve_unselected_native_variant'):
                changed[canonical] = {'before': before, 'after': change['value']}
            elif node.value != before:
                raise ValueError('Unselected native content variant changed')
            node.value = before
        private_id = restored_nodes['default/pbgid'].value
        if private_id in ids:
            raise ValueError(f'Private PBG identity collision: {name}')
        ids.add(private_id)
        tables = [n.key for n in original.nodes if isinstance(n.value, list)]
        for table in tables:
            identity = restored_nodes[table + '/pbgid']
            if identity.kind != 'Int' or identity.value != private_id or identity.value == source_nodes[table + '/pbgid'].value:
                raise ValueError(f'Private PBG identity allocation invalid: {name}:{table}')
            identity.value = source_nodes[table + '/pbgid'].value
        # Garrison clears editor inheritance metadata when cloning a complete
        # compiled RGD. Restore just these two lineage fields for the proof;
        # every native selector/mesh/socket/state field must otherwise match.
        for table in tables:
            for suffix in ('/parent_pbg/$PBGNAME', '/parent_pbg/$PBGMAP'):
                key = table + suffix
                if key in source_nodes:
                    if restored_nodes[key].value != '':
                        raise ValueError('Unexpected private clone parent metadata')
                    restored_nodes[key].value = source_nodes[key].value
        if semantics(restored.nodes) != semantics(original.nodes):
            raise ValueError(f'Native attachment changed outside selected mesh refs/clone identity: {name}')
        rows.append({'member': member, 'file': str(path), 'sha256': sha(path), 'source': str(source),
            'source_sha256': sha(source), 'private_reference': actual['reference'], 'private_pbgid': private_id,
            'family': expected['family'], 'age': expected['target_age'], 'changed_fields': changed,
            'semantic_undo_proof': 'passed', 'clone_metadata': 'new pbgid; native compiler clears parent_pbg editor lineage',
            'cook_source': str(cooked_path), 'cook_source_sha256': sha(cooked_path),
            'scoped_native_mesh_overrides': scoped_patches,
            'override_method': 'same native Garrison RGD codec; exact table fields prevent CLI all-table alias collapse'})
    result = {'status': 'passed', 'payloads': rows, 'cook_archive_sha256': cook['sha256'],
        'native_acceptance': 'pending'}
    write(OUT / 'integration/attachment-payloads.json', result)
    return result


def final_report(model_manifest, actor_manifest, attachment_manifest):
    models = read(model_manifest)
    actors = read(actor_manifest)
    lists = read(attachment_manifest)
    for report in (models, actors, lists):
        if report['status'] != 'passed':
            raise ValueError('Passed model, actor and attachment reports required')
    payloads = {}
    for report in (models, actors, lists):
        for row in report['payloads']:
            if sha(row['file']) != row['sha256'] or row['member'] in payloads:
                raise ValueError('Stale or conflicting final native payload')
            payloads[row['member']] = row['sha256']
    references = {r['private_reference'] for r in lists['payloads']}
    body_resources = {r['member'].removesuffix('.rgm') for r in models['payloads'] if r['member'].endswith('.rgm')}
    for row in actors['payloads']:
        if row['semantic_undo_proof'] != 'passed':
            raise ValueError('Actor semantic proof missing')
        for change in row['changed_fields'].values():
            if change['after'] not in references:
                raise ValueError('Actor references an uncompiled private attachment')
        if row['king_visual_age_extension']:
            for age in (2, 3, 4):
                if PBG_GUID + f':bind_king_a{age}_unit_king_1_mal' not in references:
                    raise ValueError('King visual age attachment missing')
    for row in lists['payloads']:
        if row['semantic_undo_proof'] != 'passed':
            raise ValueError('Attachment semantic proof missing')
        for change in row['changed_fields'].values():
            if change['after'] not in body_resources:
                raise ValueError(f"Private attachment lacks an authored native model: {change['after']}")
    report = {'status': 'passed', 'payload_hashes': payloads,
        'native_actor_identity_and_gameplay_undo': True, 'native_attachment_selectors_states_equipment_undo': True,
        'private_actor_attachment_model_closure': True,
        'king_visual_age_only_extension': True, 'native_runtime': 'pending'}
    write(OUT / 'integration/gameplay-semantics.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cook', type=Path, required=True)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    result = attachments(args.cook)
    if args.final:
        final_report(OUT / 'integration/model-payloads.json', OUT / 'bindings/actor-payloads.json', OUT / 'integration/attachment-payloads.json')
    print(f'Cooked native attachment semantic proofs passed: {len(result["payloads"])}')
