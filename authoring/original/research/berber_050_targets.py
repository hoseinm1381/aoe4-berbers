"""Build a read-only 0.5.0 unit consumer inventory from shipped 0.4.0 RGD XML.

The generated report records exact mod-owned compiled actors and their visual
consumer fields. Official-base actors (villager/monk) are marked as such; this
script never fabricates their absent mod RGD, nor treats tier labels as models.
"""
from __future__ import annotations
import hashlib, json, re
import os, subprocess
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/berber_update_0_5_0'
BASE = OUT / 'integration/baseline-readback'
MAL = ROOT / 'assets/attrib/instances/ebps/races/malian/units'
SBPS = ROOT / 'assets/attrib/instances/sbps/races/malian'
CORE = Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe'
FAMILIES = {
    'villager': (1, 2, 3, 4), 'scout': (1, 2, 3, 4), 'tuareg': (1, 2, 3, 4),
    'trader': (2, 3, 4), 'mehari': (2, 3, 4), 'sanhaja': (2, 3, 4),
    'zenata': (2, 3, 4), 'archer': (2, 3, 4), 'masmuda': (2, 3, 4),
    'lancer': (3, 4), 'imam': (3, 4), 'handgunner': (4,),
}
ACTORS = {
    'villager': {1: ('official', 'ebps/races/malian/units/unit_villager_1_mal'), 2: ('official', 'ebps/races/malian/units/unit_villager_1_mal'), 3: ('official', 'ebps/races/malian/units/unit_villager_1_mal'), 4: ('official', 'ebps/races/malian/units/unit_villager_1_mal')},
    'scout': {1: ('malian', 'unit_scout_1_mal'), 2: ('malian', 'unit_scout_2_mal'), 3: ('malian', 'unit_scout_1_mal'), 4: ('malian', 'unit_scout_1_mal')},
    'tuareg': {a: ('malian', f'unit_spearman_tuareg_{a}_ber') for a in range(1, 5)},
    'trader': {a: ('malian', 'unit_trade_cart_mal') for a in range(2, 5)},
    'mehari': {a: ('malian', f'mehari_{a}_ber') for a in range(2, 5)},
    'sanhaja': {a: ('malian', f'unit_sanhaja_ca_{a}_ber') for a in range(2, 5)},
    'zenata': {a: ('malian', f'unit_horseman_{a}_mal') for a in range(2, 5)},
    'archer': {a: ('malian', f'unit_archer_{a}_mal') for a in range(2, 5)},
    'masmuda': {a: ('malian', f'unit_masmuda_cb_{a}_ber') for a in range(2, 5)},
    'lancer': {a: ('malian', f'unit_knight_{a}_song_cmp') for a in range(3, 5)},
    'imam': {3: ('official', 'ebps/races/malian/units/unit_monk_3_mal'), 4: ('official', 'ebps/races/malian/units/unit_monk_3_mal')},
    'handgunner': {4: ('malian', 'unit_handcannon_4_mal')},
}
CONTRACT = {
    'villager': 'male-only; task/build tools and carry/task state; age appearance must be visual-only',
    'scout': 'preserve scout melee/hunt/siege-torch weapons, saddle/props, horse body, tier I-IV attachments',
    'tuareg': 'accepted existing unique spearman; preserve existing age I-IV bodies/shields/weapons exactly',
    'trader': 'preserve cart/mount, cargo/harness and state; visual-only age II-IV appearance',
    'mehari': 'preserve camel+rider assembly, camel animator and weapon attachments',
    'sanhaja': 'preserve camel+rider assembly, camel animator, bow and equipment attachments',
    'zenata': 'preserve horse body/rider assembly and age II-IV equipment',
    'archer': 'preserve bow/quiver/weapon state and poison/incendiary weapon conversions',
    'masmuda': 'preserve crossbow, carried equipment and tier II-IV attachments',
    'lancer': 'preserve horse/rider assembly, lance/melee weapon state and tiers III-IV',
    'imam': 'male-only; preserve monk/relic pickup, carry, deposit and drop states; IV appearance only',
    'handgunner': 'preserve hand cannon, reload/ammunition state, equipment and tier IV attachments',
}
SQUADS = {
    'villager': 'sbps/races/malian/berbers/unit_villager_1_mal',
    'scout': 'sbps/races/malian/berbers/unit_scout_1_mal',
    'tuareg': 'sbps/races/malian/berbers/unit_spearman_tuareg_1_ber',
    'trader': 'sbps/races/malian/unit_trade_cart_mal',
    'mehari': 'sbps/races/malian/berbers/mehari_2_ber',
    'sanhaja': 'sbps/races/malian/berbers/unit_sanhaja_ca_2_ber',
    'zenata': 'sbps/races/malian/berbers/unit_horseman_2_mal',
    'archer': 'sbps/races/malian/unit_archer_2_mal',
    'masmuda': 'sbps/races/malian/berbers/unit_masmuda_cb_2_ber',
    'lancer': 'sbps/races/malian/berbers/unit_knight_3_song_cmp',
    'imam': 'sbps/races/malian/unit_monk_3_mal',
    'handgunner': 'sbps/races/malian/berbers/unit_handcannon_4_mal',
}
REACHABILITY = {
    'villager': ['building_town_center_mal', 'building_town_center_capital_mal'],
    'scout': ['building_town_center_mal', 'building_town_center_capital_mal', 'building_unit_cavalry_mal', 'Ribat of Sanhaja'],
    'tuareg': ['building_unit_infantry_mal'],
    'trader': ['building_econ_market_mal', 'tribal_tent.scar resolves trade-cart squad (does not spawn one)'],
    'mehari': ['building_unit_cavalry_mal', 'Ribat of Sanhaja'],
    'sanhaja': ['building_econ_market_mal', 'Marrakech landmark'],
    'zenata': ['building_econ_market_mal', 'Zenata_Lancer.scar upgrade path'],
    'archer': ['building_unit_ranged_mal'],
    'masmuda': ['building_econ_market_mal', 'Marrakech landmark'],
    'lancer': ['building_unit_cavalry_mal', 'Ribat of Sanhaja'],
    'imam': ['building_unit_religious_mal', 'Great Mosque of Tlemcen'],
    'handgunner': ['building_unit_ranged_mal'],
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm(value: str) -> str:
    return value.replace('\\', '/')

def read_mod_actor(stem: str) -> dict:
    member = f'attrib/ebps/races/malian/units/{stem}'
    compiled = BASE / (member + '.rgd')
    xml = BASE / (member + '.xml')
    if not compiled.exists() or not xml.exists():
        raise FileNotFoundError(member)
    root = ET.parse(xml).getroot()
    def children(node):
        return [n for n in node if n.tag == 'RGDNode']
    def pbg(node):
        name = next((n.get('Value') for n in children(node) if n.get('Key') == '$PBGNAME'), None)
        pmap = next((n.get('Value') for n in children(node) if n.get('Key') == '$PBGMAP'), None)
        return (norm(pmap or '') + '/' + norm(name or '')).strip('/') if name else None
    refs=[]
    tiers=[]
    def field_ref(node, key):
        parent=next((n for n in node.iter('RGDNode') if n.get('Key')==key and n.get('Type') in ('List','List2')),None)
        if parent is None:return None
        name=next((n.get('Value') for n in children(parent) if n.get('Key')=='$PBGNAME'),None)
        pmap=next((n.get('Value') for n in children(parent) if n.get('Key')=='$PBGMAP'),None)
        return (norm(pmap or '')+'/'+norm(name)).strip('/') if name else None
    for node in root.iter('RGDNode'):
        key=node.get('Key')
        if key in ('animator_attachments','attachments') and node.get('Type') == 'List':
            value=pbg(node)
            if value:
                refs.append({'field':key,'value':value})
        if key == 'tier' and node.get('Type') == 'List':
            attachment=field_ref(node,'attachments')
            requirement=field_ref(node,'statetree_tier_requirements_pbg')
            possible=Path(requirement).name if requirement else None
            age_requirement=possible if possible in ('dark_age','feudal_age','castle_age','imperial_age') else None
            if attachment: tiers.append({'age_requirement':age_requirement,'attachments':[attachment]})
    nodes=list(root.iter('RGDNode'))
    scale=[n.get('Value') for n in nodes if n.get('Key') == 'animator_scale' and n.get('Value')]
    main_animators=[r['value'] for r in refs if r['field']=='animator_attachments']
    return {
        'compiled_member': member + '.rgd', 'compiled_sha256': sha(compiled),
        'compiled_decompile_member': member + '.xml', 'decompile_sha256': sha(xml),
        'animator_attachments': main_animators,
        'animator_scale': scale,
        'all_attachment_lists': refs,
        'tier_attachment_lists': tiers,
        'model_refs': [],
        'model_ref_status': 'not-in-actor-RGD; resolve tier attachment-list RDO and its stamp/model before production binding',
    }

def source_contract(stem: str) -> dict:
    path = MAL / (stem + '.xml')
    if not path.exists():
        return {'source_xml': None, 'source_status': 'no Malian live-source XML; official base actor'}
    tree = ET.parse(path).getroot()
    refs = []
    parent=None
    for n in tree.iter():
        if n.tag in ('instance_reference', 'template_reference') and n.get('value'):
            v = norm(n.get('value', ''))
            if n.get('name')=='parent_pbg': parent=v
            if n.get('name') in ('attachments', 'animator_attachments', 'non_entity_weapon_wrapper_pbg', 'state_tree_node') or n.get('name','').startswith('statetree_tier_'):
                refs.append({'field': n.get('name'), 'value': v, 'mod': n.get('mod')})
    return {'source_xml': str(path.relative_to(ROOT)).replace('\\', '/'),
            'source_sha256': sha(path), 'source_parent_pbg': parent,
            'source_visual_and_attachment_refs': refs}

@lru_cache(maxsize=None)
def core_fields(blueprint: str, table: str='default') -> dict:
    """Read typed stock fields through Garrison's indexed official RGD path."""
    command=[str(CORE),'mod-project','attrib-fields','--file',blueprint,'--table',table]
    result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
    line=next((x for x in result.stdout.splitlines() if x.startswith('GARRISON_MOD_PROJECT=')),None)
    if result.returncode or not line:
        raise RuntimeError(f'Official RGD lookup failed: {blueprint} [{table}] {result.stdout[-1000:]} {result.stderr[-1000:]}')
    return json.loads(line.split('=',1)[1])

@lru_cache(maxsize=None)
def find_blueprints(query: str) -> list[str]:
    result=subprocess.run([str(CORE),'mod-project','attrib-find','--search',query,'--limit','100'],capture_output=True,text=True,encoding='utf-8',errors='replace')
    line=next((x for x in result.stdout.splitlines() if x.startswith('GARRISON_MOD_PROJECT=')),None)
    return json.loads(line.split('=',1)[1]).get('blueprints',[]) if line else []

@lru_cache(maxsize=None)
def official_actor(blueprint: str) -> dict:
    entity=core_fields(blueprint,'default/entity_blueprint_ext')
    tiers=core_fields(blueprint,'default/tier_ext')
    all_fields=core_fields(blueprint,'default')
    values={r['field']:r.get('value') for r in all_fields['fields']}
    refs={r['field']:r.get('value') for r in entity['fields']}
    tier_fields=tiers['fields']
    tier_names=[]
    for i in range(4):
        prefix='tier_group_list/tier_group/tier'+(f'[{i}]' if i else '')
        name=next((r.get('value') for r in tier_fields if r['field']==prefix+'/attachments/$PBGNAME'),None)
        age=next((r.get('value') for r in tier_fields if r['field']==prefix+'/statetree_tier_requirements_pbg/$PBGNAME'),None)
        if name:
            consumer=resolve_attachment(name)
            tier_names.append({'index':i+1,'name':name,'age_requirement':age,
                               'blueprint':consumer.get('blueprint'), 'consumer':consumer,
                               'lookup_candidates':consumer.get('lookup_candidates')})
    return {'official_actor':blueprint,
            'official_animator_attachment_ref':{'name':refs.get('animator_attachments/$PBGNAME'),'map':refs.get('animator_attachments/$PBGMAP')},
            'official_animator_scale':refs.get('animator_scale'),
            'official_parent_pbg':{'name':values.get('parent_pbg/$PBGNAME'),'map':values.get('parent_pbg/$PBGMAP')},
            'official_tier_route':tier_names,
            'official_source':'Garrison `mod-project attrib-fields` reads from current indexed official typed RGD; no XML reconstruction'}

@lru_cache(maxsize=None)
def official_attachment(blueprint: str) -> dict:
    data=core_fields(blueprint,'default')
    fields=data['fields']
    parent=next((r.get('value') for r in fields if r['field']=='attachment_lists/parent_animator'),None)
    model_refs=[]
    for field in fields:
        name=field['field']
        value=field.get('value')
        if value and (str(value).replace('\\','/').startswith('art/') or name.endswith('/animator0') or name.endswith('/animator1') or name.endswith('/animator2') or name.endswith('/animator3') or name.endswith('/animator')):
            model_refs.append({'field':name,'value':norm(value)})
    return {'blueprint':blueprint,'parent_animator':norm(parent or ''),'model_refs':model_refs,
            'typed_field_count':len(fields),'official_source':'Garrison `mod-project attrib-fields`'}

@lru_cache(maxsize=None)
def resolve_attachment(name: str) -> dict:
    refs=find_blueprints(name)
    candidates=[p for p in refs if p.startswith('attachments/attachment_lists/') and p.rsplit('/',1)[-1]==name]
    preferred=[p for p in candidates if '/civilizations/malian/' in p or '/races/malian/' in p or '/races/core/' in p]
    for candidate in preferred+candidates:
        try: return official_attachment(candidate)
        except RuntimeError: continue
    return {'blueprint_name':name,'lookup_candidates':candidates,'lookup_status':'no typed official attachment RGD resolved'}

def resolve_parent_actor(stem: str, source_info: dict) -> dict | None:
    source='ebps/races/malian/units/'+stem
    try: return official_actor(source)
    except RuntimeError: pass
    parent=source_info.get('source_parent_pbg')
    if parent:
        try: return official_actor(parent)
        except RuntimeError: pass
    return None

def main():
    rows=[]
    for family, ages in FAMILIES.items():
        for age in ages:
            source_kind, stem = ACTORS[family][age]
            if source_kind == 'official':
                actor=official_actor(stem)
                actor['compiled_member_status']='official actor decoded as typed RGD by current indexed Garrison core; not present in mod archive'
                source_info={'source_xml': None, 'source_status': 'official base actor; current typed RGD evidence recorded below'}
            else:
                actor=read_mod_actor(stem)
                source_info=source_contract(stem)
                actor['official_typed_crosscheck']=resolve_parent_actor(stem,source_info)
            for route in actor.get('official_tier_route', actor.get('official_typed_crosscheck',{}).get('official_tier_route',[])):
                if not route.get('consumer') and route.get('blueprint'):
                    route['consumer']=official_attachment(route['blueprint'])
            direct=actor.get('official_animator_attachment_ref')
            if direct and direct.get('name'):
                actor['direct_animator_consumer']=resolve_attachment(direct['name'])
            else:
                typed=actor.get('official_typed_crosscheck',{})
                direct=typed.get('official_animator_attachment_ref',{})
                if direct.get('name'):
                    actor['inherited_official_animator_consumer']=resolve_attachment(direct['name'])
                body_refs=actor.get('animator_attachments',[])
                if body_refs:
                    actor['compiled_body_consumer']=resolve_attachment(body_refs[0].rsplit('/',1)[-1])
            actor['resolved_tier_consumers']=[]
            for listref in actor.get('tier_attachment_lists',[]):
                for blueprint in listref.get('attachments',[]):
                    actor['resolved_tier_consumers'].append({'age_requirement':listref.get('age_requirement'),**resolve_attachment(blueprint.rsplit('/',1)[-1])})
            if not actor.get('direct_animator_consumer'):
                names=actor.get('animator_attachments',[])
                if not names:
                    typed=actor.get('official_typed_crosscheck') or {}
                    ref=typed.get('official_animator_attachment_ref',{})
                    if ref.get('name'): names=[ref['name']]
                actor['direct_animator_consumers']=[resolve_attachment(name.rsplit('/',1)[-1]) for name in names]
            if not actor['resolved_tier_consumers']:
                actor['resolved_tier_consumers']=[{'age_requirement':r.get('age_requirement'),**r['consumer']} for r in actor.get('official_tier_route',[]) if r.get('consumer')]
                actor['resolved_tier_consumers'] += [{'age_requirement':r.get('age_requirement'),**r['consumer']} for r in (actor.get('official_typed_crosscheck') or {}).get('official_tier_route',[]) if r.get('consumer')]
            required_age=('dark_age','feudal_age','castle_age','imperial_age')[age-1]
            def target_age(consumer):
                pbg=(consumer.get('blueprint') or consumer.get('blueprint_name') or '').rsplit('/',1)[-1]
                match=re.match(r'tier([1-4])(?:_|$)',pbg)
                if match: return int(match.group(1))
                req=consumer.get('age_requirement')
                return {'dark_age':1,'feudal_age':2,'castle_age':3,'imperial_age':4}.get(req)
            matching=[x for x in actor['resolved_tier_consumers'] if target_age(x)==age]
            selected_age_tier=matching if matching else None
            rows.append({'family': family, 'age': age, 'actor_kind': source_kind,
                         'actor': stem,
                         'reachable_squad': SQUADS[family],
                         'reachability_sources': REACHABILITY[family],
                         'age_tier_consumer': selected_age_tier,
                         'baseline_040_actor': actor, **source_info,
                         'preservation_contract': CONTRACT[family],
                         'route_status': 'existing stock age/tier visual route when the official or compiled tier PBG label names this age; actor conversion behavior is separately retained'})
    king='ebps/races/malian/units/unit_king_1_mal'
    king_actor=official_actor(king)
    for route in king_actor['official_tier_route']:
        if not route.get('consumer') and route.get('blueprint'): route['consumer']=official_attachment(route['blueprint'])
    king_actor['direct_animator_consumer']=resolve_attachment(king_actor['official_animator_attachment_ref']['name'])
    conditional_rows=[]
    king_start=king_actor['official_tier_route'][:1]
    for age in (1,2,3,4):
        native=king_start if age==1 else []
        conditional_rows.append({'family':'king','age':age,'conditional_mode':'Regicide or FFA8 match type','reachable_squad':'sbps/races/malian/unit_king_1_mal','reachability_evidence':{'source':'output/berber_update_0_5_0/official-inputs/scar/winconditions/regicide.scar','official_scar_ranges':['149-165','368-370','415'],'local_squad_source':'assets/attrib/instances/sbps/races/malian/unit_king_1_mal.xml','loadout_entity':king,'squad_types':['king','scar_age1']},'current_actor':king,'current_visual_actor':king_actor,'current_age_visual_tier':native if native else None,'gap':'age II-IV visual-only appearance tiers are not present on the current actor; add conditional visual routes without altering Regicide spawn or squad behavior'})
    report={'schema':'berber-0.5.0-unit-targets/v1','baseline':{'archive':'output/berber_update_0_4_0/package/Berber_future_kingdom.sga','sha256':'a23d308c4dda1af40fc6138e40b97904afd73c0a0a0816d0f3e4b1130d8718ec','compiled_archive_readback':'output/berber_update_0_5_0/integration/baseline-readback','readback_members_manifest':'output/berber_update_0_5_0/baseline-member-sha256.json'},'rows':rows,'row_count':len(rows),'family_count':len(FAMILIES),'conditional_rows':conditional_rows,'conditional_row_count':len(conditional_rows),'reachability_scope':'12 approved human land-unit families plus the official conditional Malian Regicide King; siege/naval excluded','unresolved':['King II-IV visual-only tiers are a new extension to a current single-tier age-I actor; do not infer these from the existing tier without a typed editor-authored mutation','confirm trader and each mod-owned tier list row against squad conversion requirements; native tier PBGs are recorded without assuming list order equals age','no model candidate XML is emitted; candidate actors are editor-derived in a private Garrison research project with allocated identity']}
    target=OUT/'targets.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'{target}: {len(rows)} rows / {len(FAMILIES)} families')

if __name__=='__main__': main()
