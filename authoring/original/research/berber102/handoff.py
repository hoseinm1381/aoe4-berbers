from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'output/berber_update_1_0_2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((OUT/'release-validation.json').read_text());rows=[]
for name in ('berber_ai_navigation.scar','berber_ai_military.scar'):
 target=ROOT/'assets/scar/ai'/name;source=HERE/'scar/ai'/name;baseline=HERE/'baseline-source'/name
 assert sha(target)==sha(baseline),('editable drift',target)
 backup=HERE/'pre-promotion-source'/name;backup.parent.mkdir(exist_ok=True);assert not backup.exists();shutil.copyfile(target,backup)
 before=sha(target);shutil.copyfile(source,target);assert sha(target)==sha(source)
 rows.append({'file':str(target.relative_to(ROOT)),'before':before,'after':sha(target),'backup':str(backup.relative_to(ROOT))})
(HERE/'promotion.json').write_text(json.dumps({'promoted':rows,'authoritative':'Frozen1.0.1 + research/berber102/scar two patches; raw editor cook still not equivalent'},indent=2)+'\n')
note=f'''Current release candidate: **Berber 1.0.2**. Import
`output/berber_update_1_0_2/Berber-1.0.2.zip` ({r['zip_bytes']:,} bytes).
ZIP SHA-256: `{r['zip_sha256']}`.
SGA SHA-256: `{r['sga_sha256']}`.
Use this final archive for future patches; retain 1.0.1 as rollback.
Exactly navigation and military SCAR changed; 8,520 other members are identical.
All34shipped SCARs have MCP, signature/import and Lua5.3 syntax evidence.
236regression tests and two deterministic mock30minute8slot traces pass.
Fresh native-match startup/pathfinding/garrison/save/multiplayer proof is pending.
API docs do not fully establish native AISquad lookup/type behavior.
Inherited music25percent/Original toggle, per-entity trader speed, art/22UV
repairs, voices, tuning and soundtrack bytes remain unchanged.
Rebuild: `research/berber102/REBUILD.md`; audit evidence:
`output/berber_update_1_0_2/audit-resolution.json`. Patched editable AI sources
are promoted with prior bytes retained in berber102/pre-promotion-source.
Earlier sections below describe historical releases.

'''
for name in ('STORAGE.md','REBUILD_NEXT.md','PORTING.md'):
 p=ROOT/name;text=p.read_text(encoding='utf8');head,sep,body=text.partition('\n');p.write_text(head+'\n\n'+note+body,encoding='utf8')
print('HANDOFF_PROMOTED',len(rows))
