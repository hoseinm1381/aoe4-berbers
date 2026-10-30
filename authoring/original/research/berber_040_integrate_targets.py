"""Resolve four actual031 actor/official visual contracts without broad decode."""
import struct,sys,xml.etree.ElementTree as ET
from pathlib import Path
from berber_040_integrate import ROOT,OUT,ARCH,NativeTree,active_visuals,read,write,run,sha,extract
from garrison_shared import rgd,relic_chunky as rc
from landmark_027_stock_cache import stock
from landmark_027_export_codec import copy_native_markers
ACTORS={'university':'building_tech_university_mal','koutoubia':'building_wonder_age4_great_mosque_control_mal','fez':'landmarks/madrasa_fez/building_landmark_age3_landmarke_mal','grand_keep':'landmarks/almohad_keep/building_landmark_age3_landmarkf_mal'}
OFFICIAL=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives')
def official(member):
 path=OUT/'official-inputs'/member;path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():run(ARCH,'extract-member',OFFICIAL/('Attrib.sga' if member.startswith('attrib/') else 'Data.sga'),member,path)
 return path

def main():
 result=[]
 for kind,stem in ACTORS.items():
  actor='attrib/ebps/races/malian/buildings/'+stem+'.rgd';compiled=extract(actor);doc=rgd.read(compiled.read_bytes())
  source=ROOT/'assets/attrib/instances/ebps/races/malian/buildings'/(stem+'.xml')
  refs=[n.get('value').replace('\\','/') for n in ET.parse(source).iter('instance_reference') if n.get('name')=='attachments' and n.get('value')]
  assert len(refs)==2,(kind,refs);primary,secondary=refs
  tier_member='attrib/'+primary+'.rgd';tier=official(tier_member);tierdoc=rgd.read(tier.read_bytes())
  stamps=[(p,n.value) for p,n in rgd.flatten(tierdoc.nodes) if n.key=='stamp']
  primary_stamps=[v for p,v in stamps if p.startswith('default/') and p.endswith('/stamp_attachment/stamp')]
  assert len(primary_stamps)==1,(kind,stamps)
  stamp_member=primary_stamps[0].replace('\\','/')+'.bin';stamp=official(stamp_member);tree=NativeTree(stamp);visuals=active_visuals(tree)
  mainmodels=[r for r in visuals if '/structures/' in r['model'] and '/debris/' not in r['model']]
  assert len(mainmodels)==1,(kind,mainmodels)
  principal=mainmodels[0]['model'];native=stock(principal+'.rgm');_,markers=copy_native_markers(native.read_bytes(),native.read_bytes())
  geometry=stock(principal+'.rrgeom');bounds=[[float('inf')]*3,[float('-inf')]*3];counts=[]
  for c in rc.walk(rc.load(geometry).roots):
   if c.tag!=b'GEOB' or len(c.payload)<16:continue
   count,_,stride,_=struct.unpack_from('<4I',c.payload)
   if stride!=24 or len(c.payload)!=16+24*count:continue
   counts.append(count)
   for i in range(count):
    x,y,z,w=struct.unpack_from('<4e',c.payload,16+24*i);p=(-x,-z,y)
    for k in range(3):bounds[0][k]=min(bounds[0][k],p[k]);bounds[1][k]=max(bounds[1][k],p[k])
  scale=rgd.find(doc.nodes,'default/entity_blueprint_ext/animator_scale').value
  primaryname=Path(primary).name;secondaryname=Path(secondary).name
  mainpaths=[{'path':p,'old':n.value} for p,n in rgd.flatten(doc.nodes) if p.endswith('/attachments/$PBGNAME') and n.value==primaryname]
  otherpaths=[{'path':p,'old':n.value} for p,n in rgd.flatten(doc.nodes) if p.endswith('/attachments/$PBGNAME') and n.value==secondaryname]
  outside=official('attrib/'+secondary+'.rgd');outsidevalues=[(p,n.value) for p,n in rgd.flatten(rgd.read(outside.read_bytes()).nodes) if n.kind not in ('List','List2') and n.key not in ('$REF','pbgid','instance_version') and n.value not in ('',False,0)]
  footprint=[(p,n.value) for p,n in rgd.flatten(doc.nodes) if '/footprint_scale/' in p]
  row={'kind':kind,'actor':actor,'actor_sha256':sha(compiled),'animator_scale':scale,'primary_tier_source':primary,'tier_member':tier_member,'tier_sha256':sha(tier),'stock_stamp':stamp_member,'stock_stamp_sha256':sha(stamp),'stock_stamp_fields':stamps,'stock_principal':principal,'stock_principal_transform':mainmodels[0]['transform'],'actor_attachment_paths':mainpaths,'other_attachments':otherpaths,'secondary_tier_source':secondary,'secondary_fields':outsidevalues,'footprint_fields':footprint,'marker_contract':markers,'stock_all_state_geometry_bounds_local':bounds,'stock_all_state_geometry_bounds_world_scaled_only':[[v*scale/100 for v in side] for side in bounds],'geometry_counts':counts,'bounds_limit':'all decoded native24-byte geometry streams, not healthy-only draw bounds','native_game':'unverified'}
  result.append(row);write(OUT/(kind+'-target-contract.json'),row)
  print('040_TARGET',kind,'scale',scale,'footprint',footprint,'bounds',bounds,flush=True)
 write(OUT/'new-targets.json',{'targets':result,'baseline':'actual shipped031 actors; official native tiers/stamps/models','native_game':'unverified'})

if __name__=='__main__':main()
