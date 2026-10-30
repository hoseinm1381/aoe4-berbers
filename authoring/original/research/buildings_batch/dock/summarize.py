import json,xml.etree.ElementTree as ET,sqlite3,subprocess
from pathlib import Path
O=Path(__file__).parent
def node(n,k):return n.find(f"RGDNode[@Key='{k}']")
def tree(n):
 return {'key':n.get('Key'),'value':n.get('Value'),'children':[tree(x) for x in n]} if len(n) else {n.get('Key'):n.get('Value')}
result={}
for key in ['core','mal']:
 d=node(ET.parse(O/(key+'.xml')).getroot(),'default')
 result[key]={k:tree(node(d,k)) for k in ['site_ext','requirement_ext','simbox','sim_entity_ext','spawner_ext','placement_ext','entity_blueprint_ext','upgrade_ext'] if node(d,k) is not None}
(O/'native_datum_evidence.json').write_text(json.dumps(result,indent=2))
d=json.loads(next((O/'stock').rglob('decoded-static.json')).read_text())
print('manifest keys',list(d));print(json.dumps({k:v for k,v in d.items() if k not in ['geometry','materials']},indent=2)[:4500])
g=d['geometry'];(O/'donor_geometry.json').write_text(json.dumps({'geometry':g}))
summ=[]
for x in g['groups']:
 p=x['positions'];summ.append({'name':x['name'],'vertices':len(p),'bounds':[[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]})
(O/'donor_summary.json').write_text(json.dumps(summ,indent=2));print(json.dumps(summ,indent=2))
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
r=c.execute("select logical_path,archive_path from resolved_assets where extension='.rgd' and (logical_path like '%building_unit_naval%' or logical_path like '%layout_dock%' or logical_path like '%tier2_unit_naval_control_mal%')").fetchall();c.close()
(O/'attachment_catalog.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
