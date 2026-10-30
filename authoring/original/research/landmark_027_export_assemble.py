"""Assemble fresh native geometry/materials with private actual landmark graphs."""
import os,sys,json,hashlib,copy,math,re,struct,sqlite3,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from landmark_027_export_codec import EXT,rc,bp,sha,three_lod_geometry,native_single_geometry,intact_damage_conditions,copy_native_markers,owner_flag,remove_forge_smoke,visibility_evidence
ROOT=Path(__file__).resolve().parents[1]
DONORS={'ribat':'art/civilizations/malian/structures/landmark_2b/mal_landmark_b_age02/mal_landmark_b_age02','funduq':'art/civilizations/abbasids/structures/arsenal/abb_arsenal_control_age03/abb_arsenal_control_age03'}
FLAG='art/civilizations/common/flags/flag_rectangle/flag_rectangle'
from landmark_027_stock_cache import stock

def put(root,member,data,payloads):
 p=Path(root)/'payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 payloads.append({'member':member,'file':str(p.resolve()),'sha256':sha(data)})
def rebase_ids(node,seed,owner):
 ids={n.get('Id'):str(int.from_bytes(hashlib.sha256((seed+n.get('Id')).encode()).digest()[:8],'little')) for n in node.iter('DataObject')}
 for n in node.iter():
  for a in ['Id','OwnerId']:
   if n.get(a) in ids:n.set(a,ids[n.get(a)])
  if n.tag=='DataValue' and n.text in ids:n.text=ids[n.text]
  if n.tag=='DataProperty' and n.get('Name')=='m_objectID' and n.get('Value') in ids:n.set('Value',ids[n.get('Value')])
 if owner is not None:node.set('OwnerId',owner)
 return node
def add_flag_stamp(source,primary,flag,flag_transform,seed):
 if 'rotation' not in flag_transform and 'rotation_euler' in flag_transform:
  flag_transform={**flag_transform,'rotation':flag_transform['rotation_euler']}
 assert set(flag_transform)>={'location','rotation','scale'}
 anchor=flag_transform['location'];rotation=flag_transform['rotation'];scale=flag_transform['scale']
 assert len(anchor)==len(scale)==3 and len(rotation) in [3,4]
 assert all(math.isfinite(x) for x in [*anchor,*rotation,*scale]) and all(x>0 for x in scale)
 doc=ET.parse(source);root=doc.getroot()
 visual=next(n for n in root.iter('DataObject') if n.get('Type')=='VisualStampBlueprint')
 next(p for p in visual.findall('DataProperty') if p.get('Name')=='m_blueprint').set('Value',primary.replace('/','\\'))
 parent=next(n for n in root.iter('DataProperty') if n.get('Name')=='m_blueprints');owner=root.find('DataObject').get('Id')
 cloned=rebase_ids(copy.deepcopy(visual),seed,owner)
 for p in cloned.findall('DataProperty'):
  if p.get('Name')=='m_blueprint':p.set('Value',flag.replace('/','\\'))
  if p.get('Name') in ['m_isSelectable','m_addToPathfinding']:p.set('Value','false')
  # m_attachmentName is an optional Object in the supported core RDO;
  # assigning a string Value to it makes the source invalid.
 transform=next(n for n in cloned.iter('DataProperty') if n.get('Name')=='m_translation')
 # Native coordinates x,y(up),z; caller gives author x,y,z(up).
 native=(-anchor[0],anchor[2],-anchor[1])
 xyz=[n for n in transform.iter('DataProperty') if n.get('Name') in ['x','y','z']]
 assert len(xyz)==3 and all(p.get('Type')=='Float' for p in xyz),'Use ORIGINAL generated core RDO, not binary-decompiled raw-byte transforms'
 for p,value in zip(xyz,native):p.set('Value',str(value))
 transform=next(n for n in cloned.iter('DataProperty') if n.get('Name')=='m_scale')
 xyz=[n for n in transform.iter('DataProperty') if n.get('Name') in ['x','y','z']]
 assert len(xyz)==3 and all(p.get('Type')=='Float' for p in xyz)
 for p,value in zip(xyz,(scale[0],scale[2],scale[1])):p.set('Value',str(value))
 if len(rotation)==3:
  cx,cy,cz=[math.cos(v/2) for v in rotation];sx,sy,sz=[math.sin(v/2) for v in rotation]
  w,x,y,z=cx*cy*cz+sx*sy*sz,sx*cy*cz-cx*sy*sz,cx*sy*cz+sx*cy*sz,cx*cy*sz-sx*sy*cz
 else:w,x,y,z=rotation
 length=math.sqrt(w*w+x*x+y*y+z*z);assert abs(length-1)<1e-4
 transform=next(n for n in cloned.iter('DataProperty') if n.get('Name')=='m_rotation')
 native_q={'s':w,'x':x,'y':-z,'z':y}
 quaternion=[p for p in transform.iter('DataProperty') if p.get('Name') in native_q]
 assert len(quaternion)==4 and all(p.get('Type')=='Float' for p in quaternion)
 for p in transform.iter('DataProperty'):
  if p.get('Name') in native_q:p.set('Value',str(native_q[p.get('Name')]))
 ET.SubElement(parent,'DataValue',Name='VisualStampBlueprint').text=cloned.get('Id');parent.append(cloned)
 # Every privately cloned stamp needs its own graph IDs, including its root.
 rebase_ids(root.find('DataObject'),seed+':private-stamp:',None)
 ET.indent(root);return ET.tostring(root,encoding='utf8')
def assemble(kind,key,cookedLODreadbacks,sourcePartRows,outputRoot,flag_transform,stamp_source=None,model_names=None,geometry_mode='native-compatible-single'):
 payloads=[];base=f'art/scenario/garrison/{key}/buildings/{kind}_lod0/model';flag=f'art/scenario/garrison/{key}/owner_flag/model'
 paths=[]
 model_names=model_names or [f'{kind}_lod{lod}' for lod in range(3)]
 for lod,readback in enumerate(cookedLODreadbacks):paths.append(next(Path(readback).rglob(f'{model_names[lod]}/model.rgm')).parent)
 palettes=[]
 for p in paths:
  chunks=[c for c in rc.walk(rc.load(p/'model.rgm').roots) if c.tag==b'DATA']
  assert len(chunks)==1
  names=list(dict.fromkeys(m.decode() for m in re.findall(rb'garrison_part_[0-9]{4}',chunks[0].payload)))
  assert len(names)==len(sourcePartRows) and len(set(names))==len(names)
  palettes.append(names)
 assert palettes[0]==palettes[1]==palettes[2]
 assert set(palettes[0])=={p['name'] for p in sourcePartRows}
 assert geometry_mode=='native-compatible-single','Typed multiLOD container decoding does not qualify native per-LOD collection membership. Production must retain the fresh compiler contract.'
 newgeom,lodreport=native_single_geometry([(p/'model.rrgeom').read_bytes() for p in paths])
 donor=stock(DONORS[kind]+'.rgm');raw=bp.construction_model((paths[0]/'model.rgm').read_bytes(),donor.read_bytes(),sourcePartRows,profile_id='english-barracks')
 raw,damages=intact_damage_conditions(raw)
 visibility=visibility_evidence(raw,sourcePartRows)
 raw,markers=copy_native_markers(raw,donor.read_bytes())
 # fresh native BANA already addresses the retained LOD0 model/material stem.
 doc=rc.parse(raw);bana=[c for c in rc.walk(doc.roots) if c.tag==b'BANA'];assert len(bana)==1
 raw=rc.rebuild(doc,lambda c:rc.lp_string(base.replace('/','\\')) if c.offset==bana[0].offset else None)
 source_collection=next(c.payload for c in rc.walk(rc.load(paths[0]/'model.rgm').roots) if c.tag==b'DATA')
 actual_collection=next(c.payload for c in rc.walk(rc.parse(raw).roots) if c.tag==b'DATA')
 assert source_collection==actual_collection,'Fresh LOD0 per-triangle collection data must remain exact'
 graph=stock(DONORS[kind]+'.rgo').read_bytes();fx={'exact_native_rgo':True}
 if kind=='funduq':graph,fx=remove_forge_smoke(graph)
 put(outputRoot,base+'.rgm',raw,payloads);put(outputRoot,base+'.rgo',graph,payloads);put(outputRoot,base+'.rrgeom',newgeom,payloads)
 for p in paths[0].iterdir():
  if p.suffix=='.rrmaterial':put(outputRoot,base+'.rrmaterial',p.read_bytes(),payloads)
  if p.suffix=='.rrtex':
   # Fresh material's texture path is retained, including fixture alias tests.
   texture_member=p.relative_to(Path(cookedLODreadbacks[0])).as_posix();put(outputRoot,texture_member,p.read_bytes(),payloads)
 stockflag=stock(FLAG+'.rgm');flagraw,flagreport=owner_flag(stockflag.read_bytes(),flag)
 put(outputRoot,flag+'.rgm',flagraw,payloads)
 for suffix in ['.rgo','.rrgeom','.rrmaterial']:put(outputRoot,flag+suffix,stock(FLAG+suffix).read_bytes(),payloads)
 assert stamp_source is not None,'Explicit ORIGINAL Garrison project/source stamp RDO required; archiver-decompiled RDO is not a safe authoring template'
 stamp=Path(stamp_source)
 primary_stamp=f'art/stamps/garrison/{key}/{kind}'
 stampdata=add_flag_stamp(stamp,base,flag,flag_transform,primary_stamp)
 p=Path(outputRoot)/'source'/Path(primary_stamp+'.rdo');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(stampdata)
 report={'status':'source-assembled; fresh reflect stamp cook pending','payloads':payloads,'primary_stamp':primary_stamp,'stamp_source':str(p.resolve()),'stamp_source_sha256':sha(stamp.read_bytes()),'lod_count_three':True,'authored_lods_three':True,'native_declared_lod_count':3,'native_camera_lod_selection':'pending user game acceptance','lod_evidence':lodreport,'damage_evidence':damages,'marker_evidence':markers,'owner_flag':flagreport,'effect_evidence':fx,'flag_transform':flag_transform,'native_graph_preserved':True,'source_part_rows':sourcePartRows,'fresh_cooks_verified':False,'dependencies_resolved':False,'construction_visibility_verified':True,'construction_visibility_evidence':visibility,'dynamic_owner_colour_preserved':True,'palettes_logical_part_names_same_all_lods':True,'native_game':'pending'}
 report.update(lod_count_three=False,native_declared_lod_count=1,native_lod_count=1,geometry_mode=geometry_mode,native_camera_lod_selection='Unsupported lower LOD activation; native compiler LOD0 only',native_geometry_collection_contract_preserved=True,collection_data_sha256=sha(actual_collection),collection_data_byte_identical_to_fresh_lod0=True)
 Path(outputRoot).mkdir(parents=True,exist_ok=True);(Path(outputRoot)/'media-manifest.json').write_text(json.dumps(report,indent=2));return report
