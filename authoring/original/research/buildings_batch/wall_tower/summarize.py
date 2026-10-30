import json, pathlib,subprocess
q=pathlib.Path('research/buildings_batch/wall_tower');d=json.loads(next((q/'stock').glob('*/decoded-static.json')).read_text())
print(list(d))
for k in ['entity_binding','building_boundary_binding','skeleton','model']:
 if k in d:
  (q/(k+'.json')).write_text(json.dumps(d[k],indent=2)); print(k,str(d[k])[:2500])
groups=d['geometry']['groups'];summary=[]
for g in groups:
 p=g['positions'];summary.append({'name':g['name'],'bounds':[[min(v[k] for v in p)for k in range(3)],[max(v[k] for v in p)for k in range(3)]],'verts':len(p)})
(q/'donor_dimensions.json').write_text(json.dumps(summary,indent=2));print(summary[:12])
a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for key in ['arrowslits','springald','cannon']:
 p=q/(key+'.rgd'); x=p.with_suffix('.xml'); name='attrib/upgrade/races/common/research/upgrade_tower_'+key+'.rgd'
 if not p.exists():subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',name,str(p)],check=True,capture_output=True)
 if not x.exists():subprocess.run([a,'decode-rgd',str(p),str(x)],check=True,capture_output=True)
