"""Initialize the overhaul checklist from its retained source inventory.

Writes only new tracker files. Do not rerun to replace manually maintained progress.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Design/asset_overhaul'
RAW=json.loads((OUT/'SOURCE_INVENTORY.json').read_text())
TABLE='''Land units|unit.villager|Villager|Active male body, age appearance, tools, work outfits and carry loads|unit_villager_1_mal
Land units|unit.scout|Scout|All reachable tiers, rider, horse, tack, weapon and animal carry|unit_scout_
Land units|unit.trader|Saharan Trader|Trader, camel/mount, cargo, harness and route motion|unit_trade_cart_mal
Land units|unit.imam|Imam|Religious clothing, staff, relic carrying, healing and conversion|unit_monk_3_mal
Land units|unit.tuareg|Tuareg Spearman|Ages I-IV, 4.375m spear, low-profile shield, charge/brace/torch and Raise Shields|unit_spearman_tuareg_
Land units|unit.mehari|Mehari Rider|Ages II-IV; rider, camel, weapon, tack and charge|mehari_
Land units|unit.sanhaja|Sanhaja Camel Archer|Ages II-IV; rider, camel, bow/quiver and Desert Hunt|unit_sanhaja_ca_
Land units|unit.zenata|Zenata Lancer|Ages II-IV; rider, mount, lance, armor, charge and Blood Fury|unit_horseman_
Land units|unit.masmuda|Masmuda Crossbowman|Ages II-IV; crossbow/bolts, deployable shield and deployment|unit_masmuda_cb_
Land units|unit.handgunner|Almohad Handgunner|Age IV; firearm, powder fittings, reload and Concussive Shot|unit_handcannon_4_mal
Land units|unit.archer|Archer|Ages II-IV; dress, bow/quiver and projectile|unit_archer_
Land units|unit.lancer|Standard Lancer|Castle/Imperial production profiles; armor, horse/tack and lance|unit_knight_
Conditional units|unit.king|Berber King|Dominion/Regicide ruler appearance, equipment and portrait|unit_king_1_mal
Buildings|building.tc|Town Center|Capital/start/Nomad and additional Town Center variants|Town Center;Town Center Capital (Nomad Start)
Buildings|building.house|House|Age progression and population silhouette|House
Buildings|building.farm|Farm|Crop plot/props and construction|Farm
Buildings|building.mill|Mill|Food drop-off building|Mill
Buildings|building.lumber|Lumber Camp|Wood drop-off building|Lumber Camp
Buildings|building.mining|Mining Camp|Gold/stone drop-off building|Stone Mining Camp
Buildings|building.tent|Tribal Tent|Tribal influence hub and free-villager production|Pit Mine
Buildings|building.market|Tribal Market|Trader and alliance-unit production|Market
Buildings|building.barracks|Barracks|Infantry production|Barracks
Buildings|building.range|Archery Range|Archer/handgunner production|Archery Range
Buildings|building.stable|Stable|Mehari, scout and lancer production|Stable
Buildings|building.siege|Siege Workshop|Siege production and exits|Siege Workshop
Buildings|building.mosque|Mosque|Imam production, relic slots and Minbar presentation|Mosque
Buildings|building.dock|Dock|Ship berth/launch and naval production|Dock
Buildings|building.blacksmith|Blacksmith|Military technology presentation|Blacksmith
Buildings|building.university|University|Imperial research|University
Buildings|building.outpost|Outpost|Upgrade/emplacement variants|Outpost
Buildings|building.keep|Keep|Arrow/springald/cannon/oil attachments|Keep
Buildings|building.palisade|Palisade|Straight, corner and terrain joining pieces|Palisade
Buildings|building.palisade_gate|Palisade Gate|Open/closed gate and connectors|Palisade Gate
Buildings|building.palisade_bastion|Palisade Bastion|End/corner/connection pieces|Palisade Bastion
Buildings|building.wall|Stone Wall|Straight, corner, joining and walk surface|Wall
Buildings|building.wall_gate|Stone Wall Gate|Open/closed gate and connectors|Wall Gate
Buildings|building.wall_bastion|Stone Wall Bastion|End/corner/connection pieces|Wall Bastion
Buildings|building.wall_tower|Wall Tower|Tower, emplacements and wall integration|Tower
Buildings|building.wonder|Wonder|Separate end-game victory building|End Game Wonder
Landmarks|landmark.ribat|Ribat of the Sanhaja|Age II landmark|ribat_of_sanhaja
Landmarks|landmark.funduq|Funduq of Sijilmasa|Age II landmark|funduq
Landmarks|landmark.tlemcen|Great Mosque of Tlemcen|Age III landmark|great_mosque_of_tlemcen
Landmarks|landmark.marrakech|Dar al-Jihad of Marrakech|Age III landmark|marrakech
Landmarks|landmark.fez|Madrasa of Fez|Age IV landmark|madrasa_fez
Landmarks|landmark.grand_keep|Almohad Grand Keep|Age IV landmark|almohad_keep
Siege|siege.ram|Battering Ram|Workshop and field-built versions|unit_ram_3_mal;unit_workshop_ram_3_mal
Siege|siege.tower|Siege Tower|Field-built production references|unit_siege_tower_3_mal
Siege|siege.springald|Springald|Workshop production|unit_springald_3_mal
Siege|siege.mangonel|Mangonel|Workshop production|unit_mangonel_3_mal
Siege|siege.trebuchet|Counterweight Trebuchet|Workshop production|unit_trebuchet_4_cw_mal
Siege|siege.bombard|Bombard|Workshop production|unit_bombard_4_mal
Navy|naval.fishing|Fishing Boat|Hull, gear and fishing state|unit_naval_fishing_boat_2_mal
Navy|naval.trade|Trade Ship|Hull, sails and cargo|unit_naval_trade_ship_3_mal
Navy|naval.transport|Transport Ship|Hull, sails and passenger presentation|unit_naval_transport_ship_2_mal
Navy|naval.arrow|Arrow Ship|Hull, sails and bow/projectile states|unit_naval_light_combat_ship_2_mal
Navy|naval.combat|Combat Ship / combat dhow|Resolve inherited display label; combat hull and weapon states|unit_naval_combat_ship_2_abb
Navy|naval.fire|Fire Ship|Hull, sails and explosion/death|unit_naval_fireship_3_mal
Navy|naval.warship|Xebec / Age IV Warship|Hull, sails, artillery and crew|unit_naval_combat_warship_4_abb
Availability audit|audit.traction|Traction Trebuchet|Local override; no direct ordinary producer found|unit_trebuchet_4_tr_mal
Availability audit|audit.cannon|Cannon|Local override; no direct ordinary producer found|unit_cannon_4_mal
Availability audit|audit.culverin|Culverin|Local override; no direct ordinary producer found|unit_culverin_4_mal
Availability audit|audit.ribauldequin|Ribauldequin|Local override; no direct ordinary producer found|unit_ribauldequin_4_mal
Availability audit|audit.naval_scout|Naval Scout|Local override; no direct Dock producer found|unit_naval_scout_2_mal
Availability audit|audit.gbeto|Gbeto / original Malian infantry slots|Resolve exclusions and inherited/script availability|unit_gbeto_
Availability audit|audit.cattle|Cattle and livestock|Determine actual civ mechanic vs shared Gaia/companion warning placeholder|herdable_cattle
Shared work|work.style|Art direction|Architecture, fabrics, materials, tribal/regional variety, age progression and historical reference policy|
Shared work|work.motion|Rigging and animation coverage|Every reachable action per unit; custom motion remains separately qualified|
Shared work|work.effects|Ability/combat visuals|Raise Shields, Deploy Shield, Desert Hunt, Blood Fury, Concussive Shot, Desert Pathfinding, Desert Pace and Minbar|
Shared work|work.ui|Civilization UI and identity|Emblem, banners/flags, civ panel, tech tree, tent/alliance UI, overview/loading art and localization|
Shared work|work.icons|Portraits and research icons|Unit/building/landmark, ability, alliance, tribal and relevant shared upgrade icons|
Shared work|work.voices|Native unit voices|Selection, move, attack, work, trade, heal/convert, alerts and efforts across unit lines|
Shared work|work.sfx|Sound effects and ambience|Civ-owned ability/combat/building sounds through qualified routing; shared-global suppression unresolved|
Shared work|work.music|Music|Existing six tracks; exploration/combat/victory/defeat routing, loops, seams, volume and age arrangements|
Shared work|work.integration|Production source integration|Private references, current-source merge, original GUID, dependency manifest and stock isolation|
Shared work|work.release|Requested consolidated build|Cook approved work on user request; readback, sidecars, hashes, rollback and native acceptance|'''
items=[]
for row in TABLE.splitlines():
    category,key,name,coverage,pattern=row.split('|');sources=[];targets=[]
    if category=='Buildings':
        refs=[x for x in RAW['villager_construction_entries'] if x['menu_comment'].strip() in pattern.split(';')]
        sources=sorted({x['local_source'] for x in refs if x['local_source']});targets=[x['target'] for x in refs]
    elif category=='Landmarks':sources=[x['source'] for x in RAW['instances'] if '/landmarks/'+pattern+'/' in x['source']]
    elif pattern:sources=[x['source'] for x in RAW['instances'] if x['category'] in ('ebps','sbps') and any(p in Path(x['source']).stem for p in pattern.split(';'))]
    items.append({'id':key,'name':name,'category':category,'coverage':coverage,'visual_status':'appearance_approved' if key=='unit.tuareg' else 'not_started','integration_status':'pending_main_project' if key=='unit.tuareg' else 'not_started','source_paths':sources,'blueprint_targets':targets})
inventory={'recorded':'2026-10-12','project_guid':RAW['project_guid'],'scope':'Unique presentation on existing gameplay roster; no automatic build or experimental release per asset.','items':items}
p=OUT/'ASSET_INVENTORY.json';assert not p.exists(),'Preserve manually updated inventory';p.write_text(json.dumps(inventory,indent=2),encoding='utf-8')
lines=['# Berber civilization overhaul inventory','','Recorded 2026-10-12 from 173 attribute XMLs, 33 villager construction entries, 65 explicit building production entries, gameplay modules and design v2. Counts refer to source records, not distinct playable units. Inherited stock and requirement/script paths need per-item resolution.','','Work one selected unit/building at a time. Save source, previews, decisions and integration recipes; build the approved set only when the user asks.','','## Asset families','']
for category in dict.fromkeys(x['category'] for x in items):
    lines+=['### '+category,'','| ID | Asset | Coverage | Status |','|---|---|---|---|']
    lines += ['| '+x['id']+' | '+x['name']+' | '+x['coverage']+' | '+x['visual_status']+' |' for x in items if x['category']==category]
    lines+=['']
lines+=['## Required coverage for every selected asset','','- Agree on silhouette, historical/regional references and age progression; decisions remain per asset.','- Retain editable Blender source, packed/source textures and original references.','- Review UVs/PBR, player colours, scale, sockets/contact, weights, hierarchy and LODs.','- Units: mounts/riders, weapons, shields, tools, load/carry/torch/relic states; idle, directional move/turn/stop, attack, charge, brace, deployment, reactions and death as applicable.','- Buildings: footprint, entrance/production exits, rally space, construction stages, age/emplacement upgrades, damage and ruins; wall connections/gate motion where applicable.','- Siege/navy: crews, packed/deployed and firing states, projectiles, flags, damage and wrecks/sinking.','- Save private references, tier/variant mappings, portraits/icons and audio needs.','- Track source approval, integration readiness, cook/readback and native acceptance separately. Source checks/previews continue; no per-item trial ZIP by default.','','## Mapping/availability and presentation audits','','- The Tent is in a construction slot commented "Pit Mine"; the target is the mod tent. Internal comments are not UI names.','- Madrasa menu path is stock-root while its customized source is under `landmarks/madrasa_fez/`; resolve compiled consumers before porting.','- Several producers reference stock-root aliases while edited squads are under `berbers/`; resolve owner/PBG identity, not filenames alone.','- Existing description and design v2 disagree about cumulative Enduring Generations HP. Verify authoritative gameplay before correcting text; no rebalance is authorized here.','- Seven Dock entries and dormant siege/naval override files must not be collapsed into the shorter design-summary roster.','- Standard Men-at-Arms and standard Crossbowmen are unavailable by design. Audit Gbeto reachability rather than adding it back for an art overhaul.','- Common Gaia animals, other civilizations and the whole global HUD are outside the default civ-owned asset scope. Optional expansion must be discussed.','','## Accepted Tuareg work','','The user accepted `0.1.7-tuareg-lowprofile-shield.1` as looking good on 2026-10-12. Four refined age bodies, 4.375m spear and low-profile shield are queued for selective main-project port. That report is not exhaustive all-age/action acceptance. Instant moving Q and the full custom motion set remain unresolved. Native voice routing has a prior user-confirmed probe, while full speech/effort coverage and music audibility remain pending.','','See [Progress](PROGRESS.md), [queued build manifest](BUILD_MANIFEST.json), and [raw source inventory](SOURCE_INVENTORY.json).']
(OUT/'ASSET_INVENTORY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Inventory initialized:',len(items),'asset families and shared work items')
