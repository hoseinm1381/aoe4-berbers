"""Native model-variant cook qualification; no final art or runtime claim."""
import json
import subprocess
from pathlib import Path
from berber_050_common import CORE, EDITOR, GUID, OUT, read, run, sha, write

PROJECT = OUT / 'pilot-library/Mods/berber_units_050_pilot'
SOURCE = 'art/civilizations/malian/humans/mal_ranged_bow_age02/mal_ranged_bow_age02'

def main():
    if not (PROJECT / 'mod-project.json').exists():
        run(CORE, 'mod-project', 'create', '--library', OUT / 'pilot-library', '--name', PROJECT.name)
    run(CORE, 'mod-project', 'settings', '--project', PROJECT, '--live-reload', 'off', '--mod-id', GUID)
    if 'archer_native_contract' not in {row['name'] for row in read(PROJECT / 'mod-project.json').get('model_variants', [])}:
        run(CORE, 'mod-project', 'variant', '--project', PROJECT, '--source', SOURCE, '--name', 'archer_native_contract')
    logfile = OUT / 'pilot-native-variant-cook.log'
    command = [str(CORE), 'mod-project', 'cook', '--project', str(PROJECT), '--editor', str(EDITOR), '--timeout', '600']
    with logfile.open('w', encoding='utf8') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=660)
    record = {'status': 'failed' if result.returncode else 'passed', 'exit_code': result.returncode,
              'project': str(PROJECT), 'log': str(logfile), 'source': SOURCE,
              'scope': 'stock native unit model-variant cook only; no authored art acceptance',
              'native_acceptance': 'unverified'}
    cooks = read(PROJECT / 'mod-project.json').get('cooks', [])
    if not result.returncode:
        if not cooks:
            raise ValueError('Successful command produced no cook record')
        cook = cooks[-1]
        if cook.get('live_reload') is not False or sha(cook['archive']) != cook['sha256']:
            raise ValueError('Cook record or archive freshness invalid')
        record['cook'] = cook
    write(OUT / 'pilot-native-variant-cook.json', record)
    print(json.dumps({k: v for k, v in record.items() if k != 'cook'}, indent=2), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
