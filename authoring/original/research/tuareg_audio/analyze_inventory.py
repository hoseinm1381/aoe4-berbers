"""Summarize installed-game Donso speech inventory without exporting voice audio."""
import collections
import json
from pathlib import Path
import re
import hashlib

root = Path(__file__).resolve().parent
inventory = json.loads((root / 'donso-archive-inventory.json').read_text(encoding='utf-8-sig'))
parsed = []
unparsed = []
for member in inventory['members']:
    name = Path(member['path']).stem
    if not member['path'].endswith('.wem'):
        continue
    match = re.fullmatch(r'malian_donso_(.+?)_([ic])([^_]+)_c([^_]+)_(\d+)(?:_alt(\d+))?', name)
    if not match:
        unparsed.append(member['path'])
        continue
    event, delivery_axis, delivery, era, take, alternate = match.groups()
    parsed.append(dict(event=event, delivery=delivery, delivery_axis=delivery_axis, era=era, take=int(take),
                       alternate=int(alternate) if alternate else 0, path=member['path'], size=member['size']))
events = []
for event in sorted({row['event'] for row in parsed}):
    rows = [r for r in parsed if r['event'] == event]
    forms = collections.Counter((r['delivery'], r['era']) for r in rows)
    events.append(dict(event=event, files=len(rows), base_takes=sum(not r['alternate'] for r in rows),
                       alternate_takes=sum(bool(r['alternate']) for r in rows),
                       forms=[dict(delivery=d, era=e, files=n) for (d,e),n in sorted(forms.items())]))
summary = dict(archive=inventory['archive'], speech_files=len(parsed), unparsed=unparsed,
               deliveries=sorted({r['delivery'] for r in parsed}), eras=sorted({r['era'] for r in parsed}), events=events)
(root / 'donso-event-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
(root / 'donso-file-map.json').write_text(json.dumps(parsed, indent=2), encoding='utf-8')
print('Parsed:',len(parsed),'Unparsed:',len(unparsed))
print('Delivery labels:',summary['deliveries'],'Era labels:',summary['eras'])
for e in events:
    print(e['event'], e['files'], 'forms=' + ','.join(sorted({r['delivery'] for r in e['forms']})))
print('Unparsed paths:',unparsed[:15])
spd = (root / 'malian_donso.spd').read_bytes()
strings = [s.decode('ascii') for s in re.findall(rb'[\x20-\x7e]{5,}', spd)]
(root / 'donso-spd-strings.txt').write_text('\n'.join(strings),encoding='utf-8')
print('SPD header:',spd[:64].hex(),'strings:',len(strings))
print('SPD examples:',strings[:20])
actual_paths = {r['path'].lower().replace('\\','/') for r in parsed}
spd_paths = {s.lower().replace('\\','/') for s in strings if s.lower().endswith('.wem')}
print('SPD referenced paths:',len(spd_paths),'archive paths absent from SPD:',len(actual_paths-spd_paths),
      'SPD paths absent from Donso archive inventory:',len(spd_paths-actual_paths))
summary['spd_crosscheck'] = {'referenced_paths':len(spd_paths), 'archive_paths_absent_from_spd':sorted(actual_paths-spd_paths),
                            'spd_paths_absent_from_inventory':sorted(spd_paths-actual_paths)}
(root / 'donso-event-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

meaning = {
 'acknowledge':'General command confirmation', 'acknowledgegmr':'Group response variant (GMR engine code)',
 'ambientcombat':'Combat chatter', 'attack':'Attack order response',
 'attackmovegc':'Attack-move response, GC engine variant', 'attackmovesu':'Attack-move response, SU engine variant',
 'attacksametypegc':'Attack response for a same-type group, GC variant', 'brace':'Brace / spearwall call',
 'celebrate':'Celebration', 'changeformation':'Formation-change response', 'enemyspotted':'Enemy sighting',
 'engage':'Engaging in combat', 'garrison':'Garrison order response', 'hold':'Hold-position response',
 'marchingidle':'Marching / movement idle chatter', 'movegc':'Move order response, GC engine variant',
 'movesametypegc':'Move response for a same-type group, GC variant', 'movesu':'Move response, SU engine variant',
 'reactproud':'Proud reaction', 'resourcehunt':'Hunting order response (bank presence; Tuareg usage unverified)',
 'select':'Selection response', 'selectgc':'Selection response, GC engine variant',
 'selectsametypegc':'Same-type group selection response, GC variant', 'stop':'Stop order response',
 'structurebuild':'Structure construction response (bank presence; Tuareg usage unverified)',
 'targetdestroyed':'Target destroyed reaction', 'underattack':'Under-attack call',
 'effortattack':'Attack grunt', 'effortattackbig':'Strong attack grunt', 'effortcough':'Cough',
 'effortdeath':'Death vocalization', 'effortexertion':'Exertion', 'effortexertionbig':'Strong exertion',
 'effortfear':'Fear reaction', 'efforthealed':'Healed reaction', 'effortincomingprojectile':'Incoming projectile reaction',
 'effortinspired':'Inspired reaction', 'effortpain':'Pain', 'effortpainbig':'Strong pain',
 'effortpanic':'Panic', 'effortstretch':'Stretch effort', 'effortthroatclear':'Throat clearing', 'effortwarcry':'War cry',
}
lines = ['DONSO / TUAREG AUDIO RECORDING CHECKLIST', 'Installed-game inventory collected 2026-10-09.', '',
 'Evidence: SoundSpeechMalian.sga, filtered to donso; all 1,278 WEM members parsed.',
 '43 asset families: 27 spoken response families and 16 effort families.',
 'This is asset coverage, not proof that every family is reachable by this Tuareg unit.',
 'The accompanying JSON files contain exact member paths, forms, and counts.', '',
 'DELIVERY AND AGE FORMS',
 'iNorm = normal delivery label; iHigh = heightened delivery label; iStealth = stealth delivery label.',
 'cLowest/cLow/cMed/cHigh are four bank variation labels, plausibly the voice forms for ages I/II/III/IV.',
 'This age interpretation is an inference from naming and stock age_mapping [1,2,3,4]; native scheduling was not traced.',
 'cNone appears in efforts. Ten celebrate filenames use cNone as the first axis instead of an i token;',
 'keep those legacy labels explicit rather than silently treating them as iNorm.',
 'GC, SU, and GMR are retained as engine codes. Their full acronym expansions were not established.',
 'ALT01 is an alternate recorded take. You may supply a smaller variant pool to reuse for these slots.', '',
 'WHAT TO SUPPLY',
 'Provide original WAV, FLAC, MP3, OGG, M4A/AAC, or other ordinary decodable audio; WAV conversion can be done later.',
 'Target playback WAV: mono, 48,000 Hz, signed 16-bit PCM. Preserve original masters.',
 'One file per phrase or effort, without background music or baked reverb. Include a text transcript and pronunciation notes.',
 'Use filenames such as tuareg_select_normal_01.wav and tuareg_effortpain_01.wav.',
 'Use the same actor/character across families; state whether one voice set should cover all four ages.',
 'For a compact complete category pack, supply 2-3 distinct takes for every family; 4-6 for frequent selection/move/attack.',
 'Record normal and heightened delivery for applicable dialogue; add stealth to acknowledge and select.',
 'Four age-specific language versions are optional unless historically evolving speech is desired.',
 'This compact plan reuses takes across native slots; it is not 1,278 unique recordings.', '',
 'EXACT INVENTORY BY FAMILY', 'Each form is delivery / chronological label : existing file count. Counts include alternates.', '']
for e in events:
    rows=[r for r in parsed if r['event']==e['event']]
    lines.extend([f"{e['event']} - {meaning[e['event']]}",
                  f"  Existing files: {e['files']} (base {e['base_takes']}, alternate {e['alternate_takes']})",
                  '  Forms: '+', '.join(f"{f['delivery']}/{f['era']}:{f['files']}" for f in e['forms']), ''])
lines.extend(['ADDITIONAL SOUND EFFECTS OUTSIDE THE DONSO VOICE BANK',
 'Footsteps on different surfaces; cloth, leather, and equipment movement; spear swings/thrusts;',
 'ordinary spear impacts and spearwall impacts against flesh/leather/metal; torch launch/impact/fire;',
 'body falls/death Foley; unit production/creation cue and shared interface cues.',
 'These are candidate coverage classes from shared sound resources, not all confirmed per-unit bindings.',
 'The Tuareg no longer carries the Donso ranged javelin weapon in its visible hardpoint list;',
 'javelin launch/impact is conditional on a reachable retained behavior or future weapon.', '',
 'REPLACEMENT / SILENCING STATUS',
 'Current Tuareg ages 1-4 use entity speaker_code=donso and squad_speaker_code/squad_name_code=donso.',
 'The unit_action_apply/units/spearman/audio/sul/1 state tree is also used by the current stock Donso.',
 'Speech routing, action state trees, squad audio RTPC events, and weapon/animation sound events are separate sources.',
 'No complete per-Tuareg mute patch was created or tested. Blank codes or removed trees must not be assumed sufficient.',
 'Garrison external WAV playback does not replace a native speech database or soundbank.',
 'Native custom WEM/SPD routing or complete silence plus externally routed cues still needs a proof in a solo match.',
 'Converting a recording to WAV does not produce a native WEM or implement selection/command triggers.'])
(root/'recording-checklist.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

game=Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal')
bank=game/'audiohigh'/'card_events_00.txt'
candidates=[]
for line_number,line in enumerate(bank.read_text(encoding='utf-8-sig').splitlines(),1):
    cells=line.split('\t')
    if len(cells)<3: continue
    event=cells[2]
    if re.search(r'spear|torch|footsteps_infantry|infantry.*footstep',event,re.I):
        candidates.append(dict(event=event,id=cells[1],source=str(bank),line=line_number,notes=cells[-1]))
(root/'shared-sfx-candidates.json').write_text(json.dumps(candidates,indent=2),encoding='utf-8')
provenance={ 'collected_date':'2026-10-09', 'scope':'Inventory and read-only metadata; no native mute or replacement test',
             'archives':[] }
for name in ['SoundSpeechMalian.sga','Attrib.sga','Data.sga']:
    path=game/'archives'/name
    with path.open('rb') as handle:
        digest=hashlib.file_digest(handle,'sha256').hexdigest()
    provenance['archives'].append(dict(path=str(path),size=path.stat().st_size,sha256=digest))
(root/'source-provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
print('Created recording checklist and shared SFX candidate ledger:',len(candidates))
