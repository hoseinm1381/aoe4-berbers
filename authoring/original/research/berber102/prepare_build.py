from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE.parent/'berber101/build.py').read_text()
s=s.replace('1.0.0','BASE101TOKEN').replace('1_0_0','BASE101UNDERSCORE')
s=s.replace('1.0.1','1.0.2').replace('1_0_1','1_0_2').replace('pipeline101','pipeline102')
s=s.replace('BASE101TOKEN','1.0.1').replace('BASE101UNDERSCORE','1_0_1')
s=s.replace('a96adced078ff7a1d97a7e22e6980165f723a1551abb8794b9a016738c68d42a','a3ddb9da9f1078a9dbcb4d1fd62ff9ba7d243dd830e715d10a3658f00e0c8f31')
s=s.replace('86425e4746cd1bdcf1b4fb66e73de0b5148c60b853ca5fd72c35596e8e70da09','e1f3f794f0acdd75b2a6d717c76ad608de84b8ecece6058c45ca09e21d6d5a9e')
a=s.index('PATCHES=');b=s.index('sha=pipeline.sha',a)
s=s[:a]+"PATCHES={n:SOURCE/n for n in ('scar/ai/berber_ai_navigation.scar','scar/ai/berber_ai_military.scar')}\n"+s[b:]
a=s.index("NOTES='''");b=s.index('\ndef checks():',a)
s=s[:a]+"NOTES=(SOURCE/'RELEASE_NOTES.md').read_text(encoding='utf8')\n\n"+s[b:]
a=s.index('def checks():');b=s.index('\ndef compose():',a)
s=s[:a]+'''def checks():
 import checks as suite
 count=suite.run()
 files=sorted((SOURCE/'scar').rglob('*.scar'))
 p=subprocess.run([sys.executable,'-B','C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/validate_scar.py',*map(str,files),'--project-root',str(SOURCE/'scar'),'--json',str(OUT/'static-validation.json')],capture_output=True,text=True,encoding='utf8',errors='replace')
 (OUT/'static-validation.log').write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
 audit=json.loads((OUT/'function-audit.json').read_text());assert not audit['arity_review']
 assert len(audit['files'])==34
 for f in audit['files']:assert sha(SOURCE/f['file'])==f['sha256']
 assert all(i['resolution'] in ('packaged','official') for i in audit['imports'])
 mcp=json.loads((OUT/'mcp-file-checks.json').read_text());assert len(mcp)==34
 for row in mcp:
  data=row['result'].get('structuredContent')
  if data is None:data=json.loads(row['result']['content'][0]['text'])
  assert data['status']=='ok' and not data['missing_locdb_ids']
 assert json.loads((OUT/'simulation-validation.json').read_text())['status']=='passed'
 return count
''' +s[b:]
s=s.replace('len(before)-3','len(before)-2').replace("'unchanged_existing_members':8519","'unchanged_existing_members':8520")
s=s.replace("summary='AI cost crash fix, cumulative individual trader speed,25% music and Original/Berber toggle.'","summary='Fix AI navigation and garrison AISquad handle crashes; retains 25% music, Original toggle and individual trader progression.'")
s=s.replace("description='Berber Dynasty with fixed AI observation, per-trader +0.08m/s per30seconds, all-age custom music and original-game music toggle. Fresh-match candidate.'","description='Berber Dynasty1.0.2 with typed AI navigation and garrison path checks. All1.0.1 gameplay, art and audio retained. Fresh-match candidate.'")
s=s.replace("changelog='Fixes arbitrary entity cost_ext crash and one-time trader bonus. Sets25percent music default and adds native/custom toggle. Models,22UVrepairs, voices and playback files unchanged.'","changelog='Fixes AISquad pointer/table mismatch in scout navigation and villager garrison selection. Audits all34shipped SCAR files through AoE4 MCP. Native acceptance pending.'")
s=s.replace('Exact1.0.1 base+3retained source SCARs','Exact1.0.1 base+2retained source SCARs')
s=s.replace('exactly3SCAR','exactly2SCAR')
(HERE/'build.py').write_text(s,encoding='utf8')
