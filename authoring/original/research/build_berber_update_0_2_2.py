"""House-only native stock-remix integration, fresh readback and 0.2.1 rollback."""
import os,sys,json,hashlib,subprocess,shutil,copy,zipfile,struct,time,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_2';ART=ROOT/'art/house_remix_0_2_2'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT));sys.path.insert(0,str(ART))
from garrison_shared import rgd,relic_chunky as rc,model_variants as mv,building_project as bp
from native_materials import rewrite_scoped
from archive_contract import validate_house_namespaces
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe';PROJECT=Path('E:/bh22/Mods/berber_house_022');STAMPS=Path('E:/bhs22')
STAMP_RUN=OUT/'stamp-build-v4'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1';KEY='berber_house_022';ACTOR='attrib/ebps/races/malian/buildings/building_house_mal.rgd'
OFFICIAL=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label,args,timeout=900):
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as f:p=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    assert p.returncode==0,(label,p.returncode)
    return (OUT/(label+'.log')).read_text(encoding='utf-8')
def verify_baseline():
    old=read(ROOT/'output/berber_update_0_2_1/delivery.json');base=Path(old['archive']);assert sha(base)==old['archive_sha256']=='348378e6562cd5bc16bb9167a4e2596c9691209383a470d43e4273b21c3d800e'
    return base
def stages():
    verify_baseline();recipe=read(ART/'recipe.json')
    record=read(PROJECT/'mod-project.json');names={b['name'] for b in record.get('derived_blueprints',[])}
    for age in range(2,5):
        name=f'house_age{age}_tier'
        if name not in names:run('derive-age'+str(age),[CORE,'mod-project','derive','--project',PROJECT,'--source',f'attachments/attachment_lists/civilizations/malian/buildings/house_mal/tier{age}_house_a_mal','--name',name])
    # Stamp-only source build. Stock native selectors supply construction states.
    src=STAMPS/'source';src.mkdir(parents=True,exist_ok=True)
    shutil.copy2(PROJECT/'project/berber_house_022.aoe4mod',STAMPS/'house_stamps.aoe4mod')
    shutil.copytree(PROJECT/'project/source/locdb',src/'locdb',dirs_exist_ok=True)
    shutil.copytree(PROJECT/'project/source/attrib',src/'attrib',dirs_exist_ok=True)
    native=OUT/'donor-final-readbacks'/sha(read(OUT/'cook.json')['cook']['archive'])[:16]
    if not native.exists():
        run('restore-native-model-readback',[ARCH,'unpack',read(OUT/'cook.json')['cook']['archive'],'--output',native])
        (native.parent/(native.name+'.archive-sha256')).write_text(sha(read(OUT/'cook.json')['cook']['archive']))
    shutil.copytree(native/'art',src/'art',dirs_exist_ok=True)
    for path in (PROJECT/'project/source').iterdir():
        if path.is_file():shutil.copy2(path,src/path.name)
    # Preserve lexical xmlns declarations used inside i:type attribute values.
    # ElementTree drops these otherwise, producing an invalid DataContract file.
    burnpath=src/'_default.burnproj';burntext=burnpath.read_text(encoding='utf-8')
    rules=''
    for age in range(1,5):
        rules+=f'''<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true" /><Includes>art\\stamps\\garrison\\{KEY}\\house_age{age}.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true" /><Target>Archive</Target></BurnRule>'''
    assert burntext.count('</Rules>')==1;burnpath.write_text(burntext.replace('</Rules>',rules+'</Rules>'),encoding='utf-8')
    for age in range(1,5):
        doc=ET.fromstring(bp.stamp_source(KEY,f'house_age{age}'))
        visual=next(x for x in doc.iter('DataObject') if x.get('Type')=='VisualStampBlueprint')
        next(x for x in visual.findall('DataProperty') if x.get('Name')=='m_blueprint').set('Value',rf'art\scenario\garrison\{KEY}\house_age{age}\house_age{age}')
        next(x for x in visual.findall('DataProperty') if x.get('Name')=='m_addToPathfinding').set('Value','false')
        scale=next(x for x in doc.iter('DataProperty') if x.get('Name')=='m_scale')
        for item in scale.iter('DataProperty'):
            if item.get('Name') in ('x','y','z'):item.set('Value',str(recipe['scale']))
        dest=src/f'art/stamps/garrison/{KEY}/house_age{age}.rdo';dest.parent.mkdir(parents=True,exist_ok=True)
        ET.indent(doc,space='  ');ET.ElementTree(doc).write(dest,encoding='utf-8')
    stamp_record=STAMP_RUN/'run.json'
    if not stamp_record.exists():
        run('stamp-cook',[CORE,'essence','build-mod','--editor',Path('E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe'),'--mod',STAMPS/'house_stamps.aoe4mod','--run-root',STAMP_RUN,'--timeout','600'])
    assert read(stamp_record)['status']=='succeeded' and read(stamp_record)['exit_code']==0,read(stamp_record)['status']
    # Fresh native variants + generated private PBG identities.
    if not (OUT/'cook.json').exists():
        run('house-final-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor',Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--timeout','600'])
    record=read(PROJECT/'mod-project.json');cook=record['cooks'][-1]
    assert not cook['live_reload'] and sha(cook['archive'])==cook['sha256']
    write(OUT/'cook.json',{'status':'passed','cook':cook,'geometry':'native stock buffers retained; not a regenerated static mesh','stamp_build':'fresh native RDO build'})
    print('HOUSE_AND_STAMPS_FRESH_COOK_PASSED',flush=True)

def semantic(nodes):return [(n.key,n.hash,n.kind,semantic(n.value) if isinstance(n.value,list) else n.value) for n in nodes]
def nvalue(nodes,path):
    n=rgd.find(nodes,path);assert n is not None,path;return n.value
def put(nodes,path,value):
    n=rgd.find(nodes,path);assert n is not None,path;n.value=value
def encode(doc):
    keys={h:k for h,k in doc.keys}
    for _,n in rgd.flatten(doc.nodes):
        if n.key is not None:keys[n.hash]=n.key
    doc.keys=list(keys.items());data=rgd.write(doc);assert semantic(rgd.read(data).nodes)==semantic(doc.nodes);return data

def compose():
    base=verify_baseline();recipe=read(ART/'recipe.json');cook=read(OUT/'cook.json')['cook'];assert sha(cook['archive'])==cook['sha256']
    baseline=OUT/'baseline-readback';donor=OUT/'donor-final-readbacks'/sha(cook['archive'])[:16]
    for label,path,destination in [('baseline',base,baseline),('donor',Path(cook['archive']),donor)]:
        marker=destination.parent/(destination.name+'.archive-sha256')
        if not destination.exists():
            run(label+'-final-unpack',[ARCH,'unpack',path,'--output',destination]);marker.write_text(sha(path))
        assert marker.is_file() and marker.read_text()==sha(path),('Unproven cached readback',destination)
    payload=OUT/'payload';payload.mkdir(exist_ok=True)
    report={'status':'running','payloads':[],'materials':[],'house_bindings':[]}
    def save(member,data):
        path=payload/member;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        report['payloads'].append({'member':member,'file':str(path),'sha256':sha(path)})
    # Isolate per-material rewrites so repeated slot names cannot overwrite team/wood layers.
    for row in recipe['ages']:
        age=row['age'];decoded=read(row['decode']);stockmaterial=Path(decoded['material']['source']['path']).read_bytes();edits={}
        for m in row['materials']:
            textures={e['slot']:mv.texture_member(KEY,m['carrier'],e['slot'])+'.rrtex' for e in m['textures']}
            edits[m['name']]={'textures':textures,'parameters':{k:list(map(str,v)) for k,v in m['parameters'].items()}}
            for member in textures.values():save(member,(donor/member).read_bytes())
        scoped=rewrite_scoped(stockmaterial,edits);stem=mv.art_stem(KEY,f'house_age{age}').replace('\\','/')
        for ext in ['.rgm','.rgo','.rrgeom']:save(stem+ext,(donor/(stem+ext)).read_bytes())
        assert sha(donor/(stem+'.rrgeom'))==decoded['resources']['geometry']['sha256']
        save(stem+'.rrmaterial',scoped)
        originals={c.decoded_name:c for c in rc.parse(stockmaterial).roots};modified={c.decoded_name:c for c in rc.parse(scoped).roots}
        for mat in row['materials']:
            for name in (mat['name'],mat['name']+'_collection'):
                if name not in originals:continue
                one=lambda c:rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)])
                before=mv.material_slots(one(originals[name]));after=mv.material_slots(one(modified[name]))
                for slot in mat['team_slots_preserved']:
                    assert before['textures'][slot]==after['textures'][slot]
                    layer=1 if slot=='albedoTex' else int(slot.removeprefix('albedoTex'))
                    for key in before['parameters']:
                        if key in [f'{label}Color{layer}' for label in ['highlight','midtone','shadow']]:assert before['parameters'][key]==after['parameters'][key]
                for slot,value in before['textures'].items():
                    if slot not in edits[mat['name']]['textures']:assert after['textures'][slot]==value
        report['materials'].append({'age':age,'native_geometry_byte_preserved':True,'all_masks_normals_team_and_charred_maps_preserved':True,'per_material_editing':True})
    # Only the four newly cooked stamps; never install the donor's generated gameplay.
    stamp_archives=list((STAMP_RUN/'output').rglob('*.sga'));assert len(stamp_archives)==1,stamp_archives
    stamps=OUT/'stamp-readbacks'/sha(stamp_archives[0])[:16]
    if not stamps.exists():run('stamp-unpack',[ARCH,'unpack',stamp_archives[0],'--output',stamps])
    for p in (stamps/f'art/stamps/garrison/{KEY}').iterdir():
        assert p.suffix in ('.bin','.rdo')
        if p.suffix=='.bin':save(p.relative_to(stamps).as_posix(),p.read_bytes())
        if p.suffix=='.rdo':
            # Native Reflect serializes vectors/quaternions as raw float bytes
            # and normalizes empty/default properties. Verify the resulting wire values.
            cooked=ET.parse(p).getroot();source=ET.parse(STAMPS/'source'/p.relative_to(stamps)).getroot()
            get=lambda root,key:next(n for n in root.iter('DataProperty') if n.get('Name')==key)
            assert get(cooked,'m_blueprint').get('Value')==get(source,'m_blueprint').get('Value')
            assert get(cooked,'m_addToPathfinding').get('Value')=='false'
            assert get(cooked,'m_isSelectable').get('Value')=='true'
            assert {n.get('Id') for n in cooked.iter('DataObject')}=={n.get('Id') for n in source.iter('DataObject')}
            for key,expected in [('m_scale',(recipe['scale'],)*3),('m_translation',(0,0,0)),('m_rotation',(0,0,0,1))]:
                prop=get(cooked,key);raw=next(n for n in prop.iter('DataProperty') if n.get('Name')=='#Raw')
                actual=struct.unpack('<'+str(len(expected))+'f',bytes.fromhex(raw.get('Value')))
                assert all(abs(a-b)<1e-7 for a,b in zip(actual,expected)),(p,key,actual)
    stock={r['path'].lower():r['path'] for r in read(OUT/'official-inventory.json')['members']}
    for age in range(1,5):
        member=f'attrib/attachments/attachment_lists/civilizations/malian/buildings/house_mal/tier{age}_house_a_mal.rgd'
        original=OUT/'official'/member;original.parent.mkdir(parents=True,exist_ok=True)
        if not original.exists():run('extract-tier'+str(age),[ARCH,'extract-member',OFFICIAL,stock[member],original])
        tier=rgd.read(original.read_bytes());generated_member=f'attrib/attachments/attachment_lists/garrison/{KEY}/house_age{age}_tier.rgd'
        generated=rgd.read((donor/generated_member).read_bytes());pbg=nvalue(generated.nodes,'default/pbgid');count=0
        for table in [n for n in tier.nodes if n.kind=='List' and n.key!='instance_version']:
            put(table.value,'pbgid',pbg)
            for path,node in rgd.flatten(table.value):
                if node.kind=='CString' and node.key=='stamp' and node.value.startswith(r'art\stamps\civ_mal\mal_house_'):
                    node.value=rf'art\stamps\garrison\{KEY}\house_age{age}';count+=1
        assert count==3,(age,count)
        save(generated_member,encode(tier));report['house_bindings'].append({'age':age,'private_tier':generated_member,'healthy_variants_replaced':count,'stock_construction_wreck_stamps_retained':True,'new_pbgid':pbg})
    actor=rgd.read((baseline/ACTOR).read_bytes());before=copy.deepcopy(actor)
    for table in [n for n in actor.nodes if n.kind=='List' and n.key!='instance_version']:
        ext=rgd.find(table.value,'tier_ext');assert ext
        groups=rgd.find(ext.value,'tier_group_list');assert len(groups.value)==2
        for age,item in enumerate(groups.value[0].value,1):
            assert age<=4;ref=rgd.find(item.value,'attachments');put(ref.value,'$PBGNAME',GUID+f':house_age{age}_tier');put(ref.value,'$PBGMAP',r'attachments\attachment_lists')
        # The second visual group selects independent Malian outskirts house models.
        # Remove it to avoid mixed-civilization duplicate houses around the new house.
        removed=groups.value[1]
        for item in removed.value:
            assert nvalue(item.value,'statetree_tier_requirements_pbg/$PBGNAME') in ('','castle_age')
            assert nvalue(item.value,'statetree_tier_requirements_pbg/$PBGMAP') in ('','upgrade')
            for field in ['statetree_tier_pgb_upgrade_target_entity','statetree_tier_pgb_upgrade_target_squad']:
                assert nvalue(item.value,field+'/$PBGNAME')==''
            assert nvalue(item.value,'tier_attachment_action')==''
            assert nvalue(item.value,'statetree_tier_reached_actions/ActionTree_OpeningBranch')==''
        groups.value=groups.value[:1]
    def nongraphics(doc):
        for table in [n for n in doc.nodes if n.kind=='List']:
            table.value=[n for n in table.value if n.key!='tier_ext']
        return semantic(doc.nodes)
    assert nongraphics(copy.deepcopy(before))==nongraphics(copy.deepcopy(actor))
    # Age requirements/actions and every other value inside the retained group are identical.
    oldgroup=rgd.find(before.nodes,'default/tier_ext/tier_group_list').value[0]
    newgroup=rgd.find(actor.nodes,'default/tier_ext/tier_group_list').value[0]
    oldcopy=copy.deepcopy(oldgroup);newcopy=copy.deepcopy(newgroup)
    for group in (oldcopy,newcopy):
        for item in group.value:
            ref=rgd.find(item.value,'attachments')
            for n in ref.value:
                if n.kind=='CString':n.value=''
    assert semantic(oldcopy.value)==semantic(newcopy.value)
    save(ACTOR,encode(actor));report.update(status='passed',nonvisual_actor_fields='identical',age_requirements_and_actions='identical',outskirts_house_group='removed visual-only; stock healthy duplicates prevented')
    assert len({x['member'] for x in report['payloads']})==len(report['payloads'])
    write(OUT/'bindings-report.json',report);print('HOUSE_PRIVATE_BINDINGS_AND_NATIVE_MATERIALS_PASSED',len(report['payloads']),flush=True)

def package():
    base=verify_baseline();assert read(OUT/'source-validation.json')['status']=='passed';bindings=read(OUT/'bindings-report.json');assert bindings['status']=='passed'
    folder=OUT/'package';folder.mkdir(exist_ok=True);final=folder/'Berber_future_kingdom.sga'
    candidate=OUT/'package-candidates'/f'house-{time.time_ns()}.sga';candidate.parent.mkdir(exist_ok=True)
    lines=OUT/'payload-list.txt';lines.write_text('\n'.join(x['member']+'='+x['file'] for x in bindings['payloads'])+'\n',encoding='utf-8')
    # New attribute blueprints must be admitted through the attrib TOC. Byte
    # existence under the wrong TOC is insufficient for native PBG resolution.
    media=OUT/'media-payload-list.txt';attributes=OUT/'attrib-payload-list.txt'
    for destination,prefix in [(media,'art/'),(attributes,'attrib/')]:
        destination.write_text('\n'.join(x['member']+'='+x['file'] for x in bindings['payloads'] if x['member'].startswith(prefix))+'\n',encoding='utf-8')
    with_art=candidate.with_name(candidate.stem+'-with-art.sga')
    run('set-house-media',[ARCH,'set-members',base,media,with_art,'--alias','data'])
    run('set-house-members',[ARCH,'set-members',with_art,attributes,candidate,'--alias','attrib'])
    inventory=json.loads(run('final-inventory',[ARCH,'list',candidate,'--verify']));assert inventory['archive']['verification']['verified'];assert inventory['archive']['name'].replace('-','').lower()==GUID
    validate_house_namespaces(inventory)
    fresh=OUT/'final-readbacks'/sha(candidate)[:16];run('final-unpack',[ARCH,'unpack',candidate,'--output',fresh])
    baseline=OUT/'baseline-readback';allowed={x['member'] for x in bindings['payloads']};changed=[];unchanged=[]
    before_inventory=json.loads(run('baseline-inventory',[ARCH,'list',base,'--verify']))
    actual_before={r['path'] for r in before_inventory['members']};actual_after={r['path'] for r in inventory['members']}
    # Unpack also creates decoded XML/RDO diagnostics. Compare archive members,
    # not those derived diagnostic files.
    for name in sorted(actual_before):
        p=baseline/name;assert (fresh/name).exists()
        if sha(p)!=sha(fresh/name):assert name in allowed;changed.append(name)
        else:unchanged.append(name)
    assert changed==[ACTOR],changed
    assert actual_after==actual_before|allowed
    for item in bindings['payloads']:assert sha(fresh/item['member'])==item['sha256']
    # Decode compiled private tiers and consuming actor from the final archive.
    run('final-house-actor-decode',[ARCH,'decode-rgd',fresh/ACTOR,OUT/'final-house-actor.xml'])
    for age in range(1,5):
        member=f'attrib/attachments/attachment_lists/garrison/{KEY}/house_age{age}_tier.rgd';run('final-tier'+str(age)+'-decode',[ARCH,'decode-rgd',fresh/member,OUT/f'final-tier{age}.xml'])
    shutil.copy2(candidate,final)
    evidence={'version':'0.2.2','status':'fresh native texture/stamp cooks and final archive readback passed','archive':str(final),'archive_sha256':sha(final),'changed_existing_members':changed,'unchanged_existing_members':len(unchanged),'new_house_members':len(allowed)-1,'tent_Tuareg_SCAR_audio_and_other_existing_members':'byte-preserved from 0.2.1','native_acceptance':'pending user','owner_colour':'original native team textures masks parameters and shaders retained; two-owner match test pending','geometry':'stock Abbasid geometry/topology retained; native uniform stamp scale 0.46; material surface remix, no rebuilt walls','known_limits':['Retained generic Malian construction and wreck stamps may appear stock.','Existing house footprint and gameplay are preserved; placement, scale and orientation need native testing.','Blender layered-material preview is approximate; native shader appearance and two-owner behaviour require testing.']}
    manifest=read(ROOT/'output/berber_update_0_2_1/package/garrison.json');manifest['members'][0]['sha256']=sha(final);manifest['details'].update(version='0.2.2',updated='2026-10-13',summary='Earthen Berber house remixes across Ages I-IV',description='Stock Abbasid houses repainted with earthen plaster, timber and geometric trim. Native house geometry, selectors and team-colour layers retained. Complete 0.2.1 tent and Tuareg content preserved. Native test pending.',changelog='House-only visual update: four age variants, private scaled stamps and private tier bindings. Remove competing Malian outskirts-house visuals; preserve gameplay and previous assets.')
    write(folder/'garrison.json',manifest);write(folder/'EVIDENCE.json',evidence)
    (folder/'INSTALL_AND_TEST.txt').write_text('''BERBER 0.2.2 — HOUSE TEST
Close AoE4. Import berber_future_kingdom-0.2.2.zip into Garrison. Confirm version 0.2.2, enable it and launch with Play.
Start a fresh match: Tuning Pack The Berber Dynasties; Game Mode Berber Civilization; Civilization Malians.

Build a HOUSE (not Tribal Tent) in Age I. Check earthen walls, dark timber, doorway, terraces, ground contact and footprint. Upgrade through Ages II-IV and check both the existing house and a newly built house at each age. Check construction/cancel/rebuild, damage/burning/destruction, selection, close/far views and villagers moving beside adjacent houses. Check two player colours.
The house is a native stock Abbasid model surface remix, uniformly scaled within the existing 4x4 placement footprint; it is not a rebuilt primitive house. Native texture masks, team layers, topology and construction selectors remain. Auxiliary stock Malian construction and wreck stamps remain, so temporary scaffold/wreck visuals may be stock. Geometry changes are limited to visual scale; cultural changes are textures/materials.
The competing Malian outskirts-house visual group is removed; costs, population, health, influence, production, age actions and pathfinding data remain identical to 0.2.1.
Check Tribal Tent appearance, influence and free villagers; check Tuareg age visuals, training, movement/combat and Q. Their archive members are byte-preserved from 0.2.1.
Send screenshots with age and whether the house existed before age-up. Include warnings.log for crashes/missing assets. Native and multiplayer acceptance have not been claimed.
ROLLBACK: close AoE4 and import your preserved 0.2.1 ZIP again. The original archive and all other package files remain unchanged.
''',encoding='utf-8')
    for name in ['source-validation.json','cook.json','bindings-report.json']:shutil.copy2(OUT/name,folder/name)
    zipname=OUT/'berber_future_kingdom-0.2.2.zip'
    with zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.iterdir():
            if p.is_file():z.write(p,p.name)
    with zipfile.ZipFile(zipname) as z:assert z.testzip() is None;assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
    evidence.update(zip=str(zipname),zip_sha256=sha(zipname));write(OUT/'delivery.json',evidence)
    rollback=OUT/'rollback';rollback.mkdir(exist_ok=True);shutil.copy2(base,rollback/'Berber_future_kingdom-0.2.1.sga')
    # Do not overwrite the user's active archive or other pending production work.
    print('BERBER_0_2_2_READY',str(zipname),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
