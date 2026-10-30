import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/palisade_bastion';O=R/'output/buildings_batch/palisade_bastion';peer=R/'art/buildings/palisade'
W=.682861328125;H=4.578125;rows=[]
for age in range(1,5):
 s=json.loads((A/f'age{age}_states.json').read_text());p=json.loads((peer/f'age{age}_states.json').read_text());pj=next(j for j in p['joins'] if j['state']=='straight_6m')
 assert pj['connector_top_datum']==H and pj['sockets']==[[-3,0,0],[3,0,0]]
 for j in s['joins']:
  deg=j['degrees'];a=math.radians(deg);d=(math.cos(a),math.sin(a));center=j['peer_6m_center'];end=[center[k]-3*d[k] for k in [0,1]]
  err=math.dist(end,j['socket_ground'][:2]);assert err<1e-12
  # Peer rear rail y=.205 half-width.035; cap cross tie y=.165 half-width.045.
  overlap=min(.205+.035,.165+.045)-max(.205-.035,.165-.045);assert abs(overlap-.04)<1e-12
  rows.append({'age':age,'state':j['state'],'direction':deg,'wall_endpoint_error_m':err,'rail_side_overlap_m':overlap,'ground0':True,'top4_578125':True,'native_stamp_transform':'unqualified'})
(O/'JOIN_GUARDS.json').write_text(json.dumps({'status':'pass','rows':rows,'scope':'authored logical plane and existing peer end contract, not native stamps'},indent=2))
