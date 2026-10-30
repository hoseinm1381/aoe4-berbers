"""Build an explicitly unqualified071 two-unit pilot, never a full-release claim."""
import hashlib,json,sys,zipfile,uuid
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(ROOT/'research/berber060'))
from common import OUT as OLD,ARCH,EXT,read,write,sha,run
from release import member_hashes
from mute_pilot import explicit_candidate
ROOT_OUT=ROOT/'output/berber_update_0_7_1'
OUT=ROOT_OUT/'pilot2';BASE=ROOT/'output/berber_update_0_6_1/Berber_future_kingdom.sga'
BASE_SHA='48f09ed61020740932b0a653e165710fda49d25aa7739d05f6486b79dbe661bb'
HERE=Path(__file__).absolute().parent
INSTRUCTIONS='''BERBER0.7.1 — PILOT2, NOT THE COMPLETE RELEASE

This Garrison-importable ZIP contains13 PCM voice clips for Villager and Tuareg.
No voice installer or new loose audio files are required for these two families.
Other24families are unchanged0.6.1 content and are NOT part of this external-audio test.

Close AoE4. Import this PILOT ZIP into Garrison, enable the Berber mod, restart
the game, and use the existing Berber game mode, tuning pack and Malians choice.
Train a Tuareg spearman. Keep existing native voice files installed for the first
test: no automatic uninstall, rename or cleanup is performed by this package.

Test each unit individually: select, move, attack, stop, gather with Villager,
take damage and die. Leave at least3seconds between initial individual tests.
Then test groups/mixed selections, rapid orders, pause/resume, menu return and
a second match. Use an unchanged English/other stock unit as an audible control.
Report whether new clips play, native voices overlap, a unit becomes silent,
or ordinary stock controls lose voices. Old installed profiles must not double-play.

Pilot1 FAILED: only Villager movement played, Malian speech overlapped, Tuareg silent.
Pilot2 unions entity and squad selections, handles only our known GUID-qualified
Tuareg names, and logs actual runtime blueprint/selection data.
Runtime native-speech suppression is an UNVERIFIED candidate: existing entity/squad
speech extensions are retained with explicit new private speaker codes b71vmute
and b71tmute, whose native profiles are deliberately not installed or packaged.
Only speaker-code fields change; all other native semantics are restored in undo
checks. Stock fallback remains possible: this is a controlled test, NOT proven mute.
Local selection and command states are polled at0.25s; repeated same selection or
same command and short stop commands can be missed. Move/combat state may infer
responses rather than acknowledge the original issued order. Vanishing/despawned
entities do not count as deaths without a still-valid dead entity handle.
No Tuareg work clip is substituted. Work is gathering only in this pilot.
Pilot clips are age1/shared test material, not final all-age/variation coverage.

Full26family expansion is held until the audible pilot passes. No new paid audio,
stock archive changes, extra installer or cleanup. To rollback, close the game and
reimport Berber0.7.0 MAIN or0.6.1 in Garrison; retained native files are untouched.
'''

def build():
 OUT.mkdir(exist_ok=True)
 with zipfile.ZipFile(ROOT/'output/berber_update_0_7_0/Berber-0.7.0-MAIN-GARRISON.zip') as z:
  manifest=json.loads(z.read('garrison.json'))
  with z.open('Berber_future_kingdom.sga') as stream:basezipsha=hashlib.file_digest(stream,'sha256').hexdigest()
 if sha(BASE)!=BASE_SHA or basezipsha!=BASE_SHA or manifest['members'][0]['sha256']!=BASE_SHA:raise ValueError('070 ZIP/061 authoritative archive differ')
 write(OUT/'base-validation.json',{'status':'passed','main070_sga_sha256':basezipsha,'base061_sga_sha256':BASE_SHA,'zip_manifest_sga_sha256':manifest['members'][0]['sha256']})
 _,baseline=member_hashes(BASE,ROOT/'output/berber_update_0_6_1/readback')
 assets=read(ROOT_OUT/'pilot/audio-assets-manifest.json');payloads=[]
 for p in assets['payloads']:
  if sha(p['file'])!=p['sha256']:raise ValueError('Pilot clip changed')
  payloads.append(p)
 clips={}
 for row in assets['sources']:clips.setdefault(row['family'],{})[row['action']]={'clip':row['member'],'duration':row['duration_seconds']}
 text='Berber071PilotClips = {\n'
 for family,actions in sorted(clips.items()):
  text+='  '+family+' = {\n'
  for action,row in sorted(actions.items()):text+='    '+action+' = {clip='+json.dumps(row['clip'])+',duration='+str(row['duration'])+'},\n'
  text+='  },\n'
 text+='}\n';generated=OUT/'pilot/clips.scar';generated.parent.mkdir(parents=True,exist_ok=True);generated.write_text(text,encoding='utf8')
 source_files={'scar/garrison/garrison.scar':EXT/'garrison_shared/scar_modules/garrison.scar','scar/berber071/clips.scar':generated,'scar/berber071/dispatcher.scar':HERE/'dispatcher.scar','scar/berber071/pilot.scar':HERE/'pilot.scar'}
 gm_member='scar/winconditions/berber_future_kingdom_gm.scar'
 gm=(ROOT/'output/berber_update_0_6_1/readback'/gm_member).read_text(encoding='utf8')
 if gm.count('import("cardinal.scar")')!=1:raise ValueError('Unexpected game-mode entry')
 gm=gm.replace('import("cardinal.scar")','import("cardinal.scar")\nimport("berber071/pilot.scar")',1)
 target=OUT/'pilot/berber_future_kingdom_gm.scar';target.write_text(gm,encoding='utf8');source_files[gm_member]=target
 for member,path in source_files.items():payloads.append({'member':member,'file':str(path),'sha256':sha(path)})
 audit=read(OLD/'binding-audit.json');owners=[]
 for family in audit['families']:
  if family['family'] in ('villager','tuareg'):owners.extend(family['owners'])
 owners.append('attrib/sbps/races/malian/unit_villager_1_mal.rgd')
 mutes=[]
 for member in sorted(set(owners)):
  original=ROOT/'output/berber_update_0_6_1/readback'/member
  if sha(original)!=baseline[member]:raise ValueError('Native source readback changed')
  data,proof=explicit_candidate(original.read_bytes(),member,Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/audio'))
  target=OUT/'pilot/payloads'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  row={'member':member,'file':str(target),'sha256':sha(target),'source_sha256':sha(original),'native_mute_candidate':proof,'all_other_semantics_undo':'passed'}
  payloads.append(row);mutes.append(row)
 write(OUT/'pilot/native-mute-candidates.json',{'status':'structural_undo_passed_runtime_UNVERIFIED','payloads':mutes})
 current=BASE;run_id=uuid.uuid4().hex[:12]
 work=OUT/'pilot';output=OUT/'Berber071-PILOT.sga'
 if output.exists():raise FileExistsError('Prior pilot retained')
 for alias,prefixes in [('attrib',('attrib/',)),('data',('audio/','scar/'))]:
  chosen=[p for p in payloads if p['member'].startswith(prefixes)]
  listing=work/(alias+'-members.txt');listing.write_text(''.join(p['member']+'='+p['file']+'\n' for p in chosen),encoding='utf8')
  target=work/('attrib-pilot-'+run_id+'.sga') if alias=='attrib' else output
  if target.exists():raise FileExistsError('Existing staging archive retained')
  run(ARCH,'set-members',current,listing,target,'--alias',alias);current=target
 _,candidate=member_hashes(output,OUT/'pilot/readback')
 expected={p['member']:p['sha256'] for p in payloads}
 if len(expected)!=len(payloads) or set(candidate)!=set(baseline)|set(expected):raise ValueError('Pilot archive members differ')
 if {p for p,h in candidate.items() if baseline.get(p)!=h}!=set(expected) or any(candidate[p]!=h for p,h in expected.items()):raise ValueError('Non-admitted pilot archive difference')
 manifest['members'][0]['sha256']=sha(output)
 manifest['details'].update(version='0.7.1',summary='PILOT2: selection/name fixes and explicit native mute probe',description='Isolated Villager/Tuareg pilot2. NOT the full26family release. No native audio installer for the two test families; read START-HERE.',changelog='13embedded PCM clips; entity+squad selection union, own-GUID Tuareg matching, runtime diagnostics and explicit speaker override probe.061art/gameplay preserved.')
 zip_path=ROOT_OUT/'Berber-0.7.1-PILOT-2.zip'
 if zip_path.exists():raise FileExistsError('Existing pilotZIP retained')
 data={'garrison.json':(json.dumps(manifest,indent=2)+'\n').encode('utf8'),'START-HERE.txt':INSTRUCTIONS.encode('utf8')}
 ziphashes={'Berber_future_kingdom.sga':sha(output)}
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(output,'Berber_future_kingdom.sga')
  for name,value in data.items():z.writestr(name,value);ziphashes[name]=hashlib.sha256(value).hexdigest()
 with zipfile.ZipFile(zip_path) as z:
  if set(z.namelist())!=set(ziphashes) or z.testzip():raise ValueError('Pilot ZIP integrity failure')
  for name,digest in ziphashes.items():
   with z.open(name) as stream:
    if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('PilotZIP memberSHA differs')
 report={'status':'pilot_built_awaiting_audible_qualification','zip':str(zip_path),'sha256':sha(zip_path),'bytes':zip_path.stat().st_size,'sga_sha256':sha(output),'base_sha256':BASE_SHA,'archive_changed_members':sorted(expected),'zip_members':ziphashes,'crc_member_sha':'passed','families':2,'clips':len(assets['sources']),'source_audio_bytes':sum(p['bytes'] for p in assets['payloads']),'native_mute':'UNVERIFIED','audible_playback':'pending','garrison_import':'pending','all26_expansion':'held_by_required_pilot_gate','paid_requests':0,'cleanup':'not performed'}
 write(OUT/'pilot-validation.json',report)
 print('071_PILOT_ZIP_VERIFIED',report['sha256'],flush=True)
 return report
if __name__=='__main__':build()
