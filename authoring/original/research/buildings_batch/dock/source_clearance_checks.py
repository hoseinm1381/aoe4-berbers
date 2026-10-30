from pathlib import Path
import json
O=Path(__file__).resolve().parents[3]/'output/buildings_batch/dock'
report=[]
for age in [1,2,3,4]:
 d=json.loads((O/f'age{age}_validation.json').read_text())
 # Bounding-box swept-hull probes test source geometry only; these are not real vessel hulls.
 probes=[]
 for name,xlo,xhi,yhi,must_clear in [('central_small_hull',-1.25,1.25,-.31,True),('offset_wide_hull_apron',-1.40,2.40,-.31,False),('offset_wide_hull_open_berth',-1.40,2.40,-.56,True)]:
  obstacles=[]
  for ob in d['objects']:
   lo,hi=ob['bounds']
   if lo[0]<xhi and hi[0]>xlo and lo[1]<yhi and hi[1]>-4.30:obstacles.append(ob['object'])
  if must_clear:assert not obstacles,obstacles
  probes.append({'probe':name,'width':xhi-xlo,'x_interval':[xlo,xhi],'sweep_y':[-4.30,yhi],'art_obstacles':obstacles,'clear':not obstacles,'actual_native_vessel':False})
 report.append({'age':age,'probes':probes,'interpretation':'Swept source art envelopes only. Native layout spawn markers, hull/turning radius, waterline and path cells remain required match checks.'})
(O/'source_ship_clearance_probes.json').write_text(json.dumps(report,indent=2))
print('SOURCE_CLEARANCE_CHECKS_PASS')
