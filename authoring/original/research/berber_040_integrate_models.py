"""Serial shared040 art project, separate from all previous-release sources."""
import sys
from pathlib import Path
from berber_040_integrate import ROOT,OUT,CORE,ARCH,EDITOR,read,write,run,sha
PROJECT=OUT/'garrison-library/Mods/berber_buildings_040'
ART=ROOT/'art/building_remix_0_4_0'
TIER_NAMES={'university':'v040_university_age04_tier','koutoubia':'v040_koutoubia_tier','fez':'v040_fez_tier','grand_keep':'v040_grand_keep_tier'}
SOURCE_DIRS={'koutoubia':'wonder'}
EXPORT_DIRS={'fez':'export_lod0_v2','grand_keep':'export_lod0_v2'}

def static_source(kind):
 return ART/SOURCE_DIRS.get(kind,kind)/EXPORT_DIRS.get(kind,'export_lod0')

def validate_texture_dimensions(source):
 from PIL import Image
 for path in Path(source).rglob('*.png'):
  with Image.open(path) as image:width,height=image.size
  assert all(v>0 and v&(v-1)==0 for v in (width,height)),('Native texture mipmaps require power-of-two dimensions',str(path),width,height)

def single_lod0_geometry(raw_levels):
 """040 has one authored compiler LOD0; never synthesize lower LOD buffers."""
 import struct,hashlib
 from garrison_shared import relic_chunky as rc
 assert len(raw_levels)==3 and all(raw==raw_levels[0] for raw in raw_levels)
 raw=raw_levels[0];doc=rc.parse(raw)
 assert len(doc.roots)==1 and doc.roots[0].tag==b'RRGO'
 root=doc.roots[0];meshes=[c for c in root.children if c.tag==b'MESH'];counts=[c for c in root.children if c.tag==b'NBME']
 assert len(counts)==1 and struct.unpack('<I',counts[0].payload)[0]==len(meshes)
 triangles=vertices=0
 for mesh in meshes:
  assert [c.tag for c in mesh.children]==[b'NBLO',b'LOD '] and struct.unpack('<I',mesh.children[0].payload)==(1,)
  for geometry in [c for c in mesh.children[1].children if c.tag==b'GEOM']:
   buffers=[c for c in rc.walk([geometry]) if c.tag==b'GEOB'];assert len(buffers)==2
   vertex,index=[struct.unpack_from('<4I',c.payload) for c in buffers]
   assert vertex[2]==20 and index[2] in (2,4)
   assert all(len(c.payload)==16+info[0]*info[2] for c,info in zip(buffers,(vertex,index)))
   assert index[0]%3==0
   indices=struct.unpack_from('<'+('H' if index[2]==2 else 'I')*index[0],buffers[1].payload,16)
   assert indices and max(indices)<vertex[0]
   vertices+=vertex[0];triangles+=index[0]//3
 assert triangles>0
 digest=hashlib.sha256(raw).hexdigest()
 return raw,{'mode':'native-compatible-single','native_lod_count':1,'authored_lods_three':False,'source_levels':[{'source_sha256':digest,'native_mesh_count':len(meshes),'triangles':triangles,'vertices':vertices}],'runtime_geometry_sha256':digest,'runtime_geometry_byte_identical_to_fresh_lod0':True,'limitation':'Only freshly compiled authored LOD0 is installed; lower LOD activation unsupported and unclaimed.'}

def verify_prepared_source(kind):
 source=static_source(kind);prepared=read(OUT/(kind+'-prepare.json'))
 assert Path(prepared['source'])==source,(kind,'prepared export path is stale')
 assert {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}==prepared['source_files_sha256'],(kind,'prepared export bytes changed')
 if prepared.get('flag_transform_sha256'):
  assert sha(source.parent/'flag-transform.json')==prepared['flag_transform_sha256'],(kind,'flag transform changed after preparation')
 return source

def project():
 if not (PROJECT/'mod-project.json').exists():run(CORE,'mod-project','create','--library',OUT/'garrison-library','--name','berber_buildings_040')
 run(CORE,'mod-project','settings','--project',PROJECT,'--live-reload','off','--mod-id','1d3145e8-f1b2-427f-8bb0-067851fcf0f1')
 return read(PROJECT/'mod-project.json')

def university_prepare():
 record=project();recipe=read(ART/'university/recipe.json');model=recipe['models'][0]
 existing={m['name'] for m in record.get('model_variants',[])}
 source=model.get('source_rgm',model.get('source')).removesuffix('.rgm')
 if 'university_age04' not in existing:run(CORE,'mod-project','variant','--project',PROJECT,'--source',source,'--name','university_age04')
 carriers=read(ART/'university/material-repaint.json')
 for carrier in carriers:
  assert sha(carrier['png'])==carrier['png_sha256']
  if carrier['carrier'] not in existing:run(CORE,'mod-project','variant','--project',PROJECT,'--source','art/civilizations/abbasids/structures/market/abb_market_control_age02/abb_market_control_age02','--name',carrier['carrier'])
  run(CORE,'mod-project','variant-set','--project',PROJECT,'--name',carrier['carrier'],'--slot',carrier.get('carrier_slot','albedoTex'),'--image',carrier['png'])
 if 'v040_university_age04_tier' not in {d['name'] for d in record.get('derived_blueprints',[])}:
  run(CORE,'mod-project','derive','--project',PROJECT,'--source','attachments/attachment_lists/civilizations/malian/buildings/tech_university_mal/tier4_tech_university_control_mal','--name','v040_university_age04_tier')
 write(OUT/'university-prepare.json',{'status':'prepared; cook not started','project':str(PROJECT),'native_geometry':model['native_geometry'],'native_geometry_sha256':sha(model['native_geometry']),'carriers':carriers})
 print('040_UNIVERSITY_PREPARED')

def static_prepare(kind):
 record=project();source=static_source(kind)
 assert (source/'building.json').exists(),source
 run(CORE,'mod-project','building','--project',PROJECT,'--source',source,'--name',kind+'_lod0','--profile','english-house','--integration','script')
 prepared={'status':'prepared; cook not started','source':str(source),'source_files_sha256':{str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}}
 if (source.parent/'flag-transform.json').exists():prepared['flag_transform_sha256']=sha(source.parent/'flag-transform.json')
 write(OUT/(kind+'-prepare.json'),prepared)

def prepare_targets():
 record=project();existing={d['name'] for d in record.get('derived_blueprints',[])}
 for target in read(OUT/'new-targets.json')['targets']:
  name=TIER_NAMES[target['kind']]
  if name not in existing:run(CORE,'mod-project','derive','--project',PROJECT,'--source',target['primary_tier_source'],'--name',name)
 print('040_TARGETS_DERIVED',len(TIER_NAMES))

def cook():
 sources={};image_hashes={}
 for prep in OUT.glob('*-prepare.json'):
  entry=read(prep)
  if 'source_files_sha256' in entry:
   source=Path(entry['source']);observed={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
   validate_texture_dimensions(source)
   assert observed==entry['source_files_sha256'],'Source changed after preparation: '+str(source)
   sources[str(source)]=observed
  if 'native_geometry' in entry:assert sha(entry['native_geometry'])==entry['native_geometry_sha256']
  for carrier in entry.get('carriers',[]):assert sha(carrier['png'])==carrier['png_sha256'];image_hashes[carrier['png']]=carrier['png_sha256']
 write(OUT/'art-cook-inputs.json',{'sources':sources,'university_recipe_sha256':sha(ART/'university/recipe.json'),'carrier_image_hashes':image_hashes})
 run(CORE,'mod-project','cook','--project',PROJECT,'--editor',EDITOR,'--timeout','600')
 record=read(PROJECT/'mod-project.json');cook=record['cooks'][-1]
 assert cook['live_reload'] is False and sha(cook['archive'])==cook['sha256']
 readback=OUT/('art-cook-readback-'+cook['sha256'][:16]);run(ARCH,'unpack',cook['archive'],'--output',readback)
 for source,expected in sources.items():assert {str(p.relative_to(source)):sha(p) for p in Path(source).rglob('*') if p.is_file()}==expected
 assert sha(ART/'university/recipe.json')==read(OUT/'art-cook-inputs.json')['university_recipe_sha256']
 for path,expected in image_hashes.items():assert sha(path)==expected,path
 write(OUT/'art-cook.json',{'status':'passed','cook':cook,'readback':str(readback),'source_files_sha256':sources,'university_recipe_sha256':read(OUT/'art-cook-inputs.json')['university_recipe_sha256'],'carrier_image_hashes':image_hashes})
 print('040_ART_COOK_PASSED',cook['sha256'])

def university_media():
 import garrison_shared
 sys.modules['garrison.garrison_shared']=garrison_shared
 sys.path.insert(0,str(ROOT/'art/economy_remix_0_2_5/mill'))
 from native_materials import rewrite_scoped
 from garrison_shared import model_variants as mv,relic_chunky as rc
 from landmark_027_stock_cache import stock
 from landmark_027_export_codec import copy_native_markers
 record=read(OUT/'art-cook.json');assert record['status']=='passed'
 cooked=Path(record['readback']);recipe=read(ART/'university/recipe.json');model=recipe['models'][0]
 assert sha(model['native_geometry'])==model['native_geometry_sha256']
 stem=mv.art_stem(PROJECT.name,'university_age04').replace('\\','/');payloads=[]
 def save(member,raw):
  target=OUT/'integration/payload'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  payloads.append({'member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
 edits={}
 for entry in read(ART/'university/material-repaint.json'):
  texture=mv.texture_member(PROJECT.name,entry['carrier'],entry.get('carrier_slot','albedoTex')).replace('\\','/')+'.rrtex'
  save(texture,(cooked/texture).read_bytes())
  edits.setdefault(entry['material'],{'textures':{},'parameters':{}})['textures'][entry['slot']]=texture
 stockmaterial=Path(model['stock_material']).read_bytes();remixed=rewrite_scoped(stockmaterial,edits)
 target=next(t for t in read(OUT/'new-targets.json')['targets'] if t['kind']=='university')
 raw,markers=copy_native_markers((cooked/(stem+'.rgm')).read_bytes(),stock(target['stock_principal']+'.rgm').read_bytes())
 save(stem+'.rgm',raw);save(stem+'.rgo',stock(target['stock_principal']+'.rgo').read_bytes())
 assert sha(cooked/(stem+'.rrgeom'))==model['stock_geometry_sha256']
 save(stem+'.rrgeom',Path(model['native_geometry']).read_bytes());save(stem+'.rrmaterial',remixed)
 before=rc.parse(stockmaterial);after=rc.parse(remixed)
 for lhs,rhs in zip(before.roots,after.roots):
  def single(c):return rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)])
  old=mv.material_slots(single(lhs));new=mv.material_slots(single(rhs));name=lhs.decoded_name.removesuffix('_collection')
  for slot,value in old['textures'].items():
   if slot not in edits.get(name,{}).get('textures',{}):assert new['textures'][slot]==value,(name,slot)
  assert new['parameters']==old['parameters']
 write(OUT/'integration/model-manifests/university-media.json',{'status':'fresh art cook+native remixed geometry; binding pending','principal':stem,'payloads':payloads,'native_geometry_sha256':model['native_geometry_sha256'],'native_owner_mask_shader_and_nonrepaint_fields':'identical','native_marker_payload_preserved':markers,'native_target_rgo_sha256':sha(stock(target['stock_principal']+'.rgo')),'runtime':'unverified'})
 print('040_UNIVERSITY_MEDIA',len(payloads))

def static_assemble(kind):
 import landmark_027_export_assemble as adapter
 DONORS=adapter.DONORS
 target=next(t for t in read(OUT/'new-targets.json')['targets'] if t['kind']==kind)
 donor=target['stock_principal'];DONORS[kind]=donor
 cook=read(OUT/'art-cook.json');back=Path(cook['readback']);source=verify_prepared_source(kind)
 parts=read(source/'building.json')['parts']
 stamp=PROJECT/f'project/source/art/stamps/garrison/{PROJECT.name}/{kind}_lod0.rdo'
 assert stamp.exists(),stamp
 flag=read(ART/SOURCE_DIRS.get(kind,kind)/'flag-transform.json')
 original=adapter.native_single_geometry
 try:
  adapter.native_single_geometry=single_lod0_geometry
  report=adapter.assemble(kind,PROJECT.name,[back]*3,parts,OUT/'assembled'/kind,flag,stamp_source=stamp,model_names=[kind+'_lod0']*3,geometry_mode='native-compatible-single')
 finally:adapter.native_single_geometry=original
 report.update(authored_lods_three=False,source_lod_count=1,source_cook=cook['cook'],target_contract=target)
 write(OUT/'integration/model-manifests'/(kind+'-media.json'),report)
 print('040_STATIC_ASSEMBLED',kind,len(report['payloads']))

def university_details_media():
 from garrison_shared import building_project as bp,relic_chunky as rc,model_variants as mv
 from landmark_027_stock_cache import stock
 from landmark_027_export_codec import intact_damage_conditions,visibility_evidence
 cook=read(OUT/'art-cook.json');back=Path(cook['readback'])
 stem=f'art/scenario/garrison/{PROJECT.name}/buildings/university_details_lod0/model'
 final='art/scenario/b040/ud/model';parts=read(ART/'university_details/export_lod0/building.json')['parts']
 donor='art/civilizations/malian/structures/university/mal_university_control_age04/mal_university_control_age04'
 raw=bp.construction_model((back/(stem+'.rgm')).read_bytes(),stock(donor+'.rgm').read_bytes(),parts,profile_id='english-barracks')
 raw,damage=intact_damage_conditions(raw);visibility=visibility_evidence(raw,parts)
 raw=mv.rewrite_model_path(raw,stem.replace('/','\\'),final.replace('/','\\'))
 payloads=[]
 def save(member,raw):
  target=OUT/'integration/payload'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  payloads.append({'member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
 save(final+'.rgm',raw);save(final+'.rgo',stock(donor+'.rgo').read_bytes())
 for ext in ('.rrgeom','.rrmaterial'):save(final+ext,(back/(stem+ext)).read_bytes())
 for path in (back/Path(stem).parent).glob('*.rrtex'):save(path.relative_to(back).as_posix(),path.read_bytes())
 write(OUT/'integration/model-manifests/university-details-media.json',{'status':'fresh static nativeLOD0/stage graph assembled','principal':final,'payloads':payloads,'visibility':visibility,'damage':damage,'source_cook':cook['cook'],'known_limit':'Native construction/FX interaction requires match acceptance; detail geometry intentionally supplements the complete University donor.'})
 print('040_UNIVERSITY_DETAILS_MEDIA',len(payloads))

def university_flag_media():
 from landmark_027_stock_cache import stock
 from landmark_027_export_codec import owner_flag
 source='art/civilizations/common/flags/flag_rectangle/flag_rectangle';target='art/scenario/b040/uf/model';payloads=[]
 flag,report=owner_flag(stock(source+'.rgm').read_bytes(),target)
 for ext in ('.rgm','.rgo','.rrgeom','.rrmaterial'):
  raw=flag if ext=='.rgm' else stock(source+ext).read_bytes()
  path=OUT/'integration/payload'/(target+ext);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  payloads.append({'member':target+ext,'file':str(path),'sha256':sha(path),'bytes':len(raw)})
 transform=read(ART/'university/flag-transform.json')
 write(OUT/'integration/model-manifests/university-flag-media.json',{'status':'qualified native flag media; fresh reference cook pending','principal':target,'payloads':payloads,'owner_flag':report,'flag_transform':transform})
 print('040_UNIVERSITY_FLAG_MEDIA')

def bind_tier_actor(kind,stamp_member,stamp_row):
 import copy
 from garrison_shared import rgd
 from build_berber_update_0_2_5 import encode,semantics
 from berber_040_integrate import extract
 target=next(t for t in read(OUT/'new-targets.json')['targets'] if t['kind']==kind)
 cooked=Path(read(OUT/'art-cook.json')['readback']);name=TIER_NAMES[kind]
 private_tier=f'attrib/attachments/attachment_lists/garrison/{PROJECT.name}/{name}.rgd'
 original=rgd.read((OUT/'official-inputs'/target['tier_member']).read_bytes());tier=copy.deepcopy(original)
 identity=rgd.find(rgd.read((cooked/private_tier).read_bytes()).nodes,'default/pbgid').value
 stock=target['stock_stamp'].removesuffix('.bin').replace('/','\\');changed=[]
 for path,node in rgd.flatten(tier.nodes):
  if node.key=='pbgid':node.value=identity
  elif node.key=='stamp' and node.kind=='CString' and node.value.lower()==stock.lower():changed.append(path);node.value=stamp_member.removesuffix('.bin').replace('/','\\')
 assert changed,kind
 restored=copy.deepcopy(tier)
 for path,node in rgd.flatten(restored.nodes):
  if node.key=='pbgid':node.value=rgd.find(original.nodes,path).value
  elif path in changed:node.value=rgd.find(original.nodes,path).value
 assert semantics(restored.nodes)==semantics(original.nodes)
 actor_original=rgd.read(extract(target['actor']).read_bytes());actor=copy.deepcopy(actor_original);actor_changes=[]
 for ref in target['actor_attachment_paths']:
  node=rgd.find(actor.nodes,ref['path']);assert node.value==ref['old'];node.value='1d3145e8f1b2427f8bb0067851fcf0f1:'+name
  actor_changes.append({**ref,'new':node.value})
 # The inspected secondary contracts contain only clearable native terrain dressing.
 # Emptying these visual attachment references prevents old outskirt buildings/props
 # from layering over the entirely new complete architecture.
 for path,value in target['secondary_fields']:
  assert path.endswith('/attachment_category') or path.endswith('/inventory_category') or path.endswith('/stamp'),(kind,path)
 for ref in target['other_attachments']:
  node=rgd.find(actor.nodes,ref['path']);assert node.value==ref['old'];node.value='';actor_changes.append({**ref,'new':''})
 restored=copy.deepcopy(actor)
 for ref in actor_changes:rgd.find(restored.nodes,ref['path']).value=ref['old']
 assert semantics(restored.nodes)==semantics(actor_original.nodes)
 payloads=[]
 for member,raw in [(private_tier,encode(tier)),(target['actor'],encode(actor))]:
  path=OUT/'integration/payload'/member;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  payloads.append({'member':member,'file':str(path),'sha256':sha(path),'bytes':len(raw)})
 payloads.append(stamp_row)
 return {'status':'passed','layer':'source identity/semantic preservation, fresh native stamp cook and compiled readback','kind':kind,'payloads':payloads,'private_tier':private_tier,'allocated_pbgid':identity,'stamp_fields_changed':changed,'actor_visual_changes':actor_changes,'nonvisual_actor_semantics':'identical after restoring named visual attachment refs','footprint_and_scale':target['footprint_fields']+[('animator_scale',target['animator_scale'])],'outskirts':'inspected clearable visual stamp dressing removed','native_runtime':'unverified'}

def static_bind(kind):
 from berber_040_integrate import NativeTree,active_visuals
 media=read(OUT/'integration/model-manifests'/(kind+'-media.json'));keys=read(OUT/'native-model-key-table.json')
 assert keys['status']=='passed';stamp=next(r for r in keys['compiled_stamps'] if r['member']==media['primary_stamp']+'.bin')
 visuals=active_visuals(NativeTree(stamp['file']));assert len(visuals)==2
 assert any('/owner_flag/' in r['model'] for r in visuals)
 path=OUT/'integration/payload'/stamp['member'];path.parent.mkdir(parents=True,exist_ok=True);shutil=__import__('shutil');shutil.copy2(stamp['file'],path)
 row={**stamp,'file':str(path)}
 report=bind_tier_actor(kind,stamp['member'],row)
 report.update(native_marker_payload_preserved=media['marker_evidence']['byte_identical'],native_lifecycle_rgo_preserved=media['native_graph_preserved'],fresh_native_stamp_cook=keys['native_run'],owner_flag='independent native flag, native materials/masks retained; runtime two-owner probe pending')
 write(OUT/'integration/model-manifests'/(kind+'-binding.json'),report)
 print('040_STATIC_BOUND',kind)

def university_bind():
 import math,struct
 from berber_040_integrate import NativeTree,active_visuals,prune_native_visuals
 from building_026_native_rebind import rebind
 from garrison_shared import relic_chunky as rc
 target=next(t for t in read(OUT/'new-targets.json')['targets'] if t['kind']=='university')
 media=read(OUT/'integration/model-manifests/university-media.json');details=read(OUT/'integration/model-manifests/university-details-media.json');flag=read(OUT/'integration/model-manifests/university-flag-media.json')
 keys=read(OUT/'native-model-key-table.json');assert keys['status']=='passed'
 models=[media['principal'],details['principal'],flag['principal']]
 for model in models:assert model.replace('/','\\') in keys['keys']
 original=NativeTree(OUT/'official-inputs'/target['stock_stamp'])
 raw,_=rebind(original,{target['stock_principal']:models[0]},keys['keys'])
 tmp=OUT/'integration/university-rebound.bin';tmp.write_bytes(raw);tree=NativeTree(tmp);rows=active_visuals(tree)
 principal=next(r for r in rows if r['model']==models[0]);extras=[r for r in rows if r['id']!=principal['id']][:2];assert len(extras)==2
 chosen=[principal]+extras;memory=bytearray(tree.memory.payload)
 transform=flag['flag_transform'];anchor=transform['location'];scale=transform['scale'];rotation=transform['rotation']
 if len(rotation)==3:
  cx,cy,cz=[math.cos(v/2) for v in rotation];sx,sy,sz=[math.sin(v/2) for v in rotation]
  w,x,y,z=cx*cy*cz+sx*sy*sz,sx*cy*cz-cx*sy*sz,cx*sy*cz+sx*cy*sz,cx*cy*sz-sx*sy*cz
 else:w,x,y,z=rotation
 flag_native=[x,-z,y,w,-anchor[0],anchor[2],-anchor[1],scale[0],scale[2],scale[1]]
 transformations=[]
 for index,(row,model) in enumerate(zip(chosen,models)):
  obj=tree.objects[row['id']];field=obj['fields']['m_blueprint'];at=obj['offset']+int(field.get('Offset'))-tree.memory.payload_offset
  assert field.get('FieldTypeName')=='util::ReflectString<StdTraits>'
  displacement,count=struct.unpack_from('<qQ',memory,at);encoded=model.replace('/','\\').encode();assert len(encoded)<=count,(model,count)
  memory[at+displacement:at+displacement+count]=encoded+b'\0'*(count-len(encoded));struct.pack_into('<Q',memory,at+8,len(encoded))
  at=obj['offset']+int(obj['fields']['m_transform'].get('Offset'))-tree.memory.payload_offset
  final=flag_native if index==2 else [0,0,0,1,0,0,0,1,1,1];struct.pack_into('<10f',memory,at,*final)
  transformations.append({'id':row['id'],'model':model,'before':row['transform'],'after':final})
 raw=rc.rebuild(tree.document,lambda c:bytes(memory) if c.offset==tree.memory.offset else None);tmp.write_bytes(raw)
 raw,pruning=prune_native_visuals(NativeTree(tmp),{r['id'] for r in chosen})
 member=f'art/stamps/garrison/{PROJECT.name}/university.bin';path=OUT/'integration/payload'/member;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 final=active_visuals(NativeTree(path));assert {r['model'] for r in final}==set(models)
 row={'member':member,'file':str(path),'sha256':sha(path),'bytes':len(raw)};report=bind_tier_actor('university',member,row)
 report.update(native_marker_payload_preserved=media['native_marker_payload_preserved']['byte_identical'],native_target_rgo_sha256=media['native_target_rgo_sha256'],native_principal_geometry_sha256=media['native_geometry_sha256'],transformations=transformations,pruning=pruning,fresh_native_reference_cook=keys['native_run'],owner_flag='independent qualified native flag with preserved material/masks; two-owner runtime pending',stamp_route='native byte-preserving record/array mutation with fresh model-key reference cook; final native stamp not Reflect-round-tripped')
 write(OUT/'integration/model-manifests/university-binding.json',report);print('040_UNIVERSITY_BOUND',len(final),'explicit visuals')

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
