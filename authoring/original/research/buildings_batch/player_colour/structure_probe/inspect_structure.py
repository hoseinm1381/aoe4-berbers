"""Read-only stock/material inspection. Run with Blender's matching Python 3.13."""
import hashlib
import inspect
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXT = Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
sys.path.insert(0, str(EXT))
from garrison_shared import model_variants

fixture = ROOT / 'research/buildings_batch/wall_tower/stock/ca0f7e2869034461016a/decoded-static.json'
decoded = json.loads(fixture.read_text(encoding='utf-8'))
materials = decoded['material']['materials']
team = [m for m in materials if any('team' in t.get('texture_name', '').lower() for b in m['blocks'] for t in b.get('textures', []))]
assert {m['name'] for m in team} == {'main', 'main_collection'}
material_path = Path(decoded['material']['source']['path'])
slots = model_variants.material_slots(material_path.read_bytes())
slot_conflicts = {}
for material in materials:
    for block in material['blocks']:
        for texture in block.get('textures', []):
            slot_conflicts.setdefault(texture['name'], {})[material['name']] = texture.get('logical_path')
slot_conflicts = {name: refs for name, refs in slot_conflicts.items() if len(set(refs.values())) > 1}
connection = sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro', uri=True)
try:
    team_assets = connection.execute("select logical_path, size from resolved_assets where logical_path like '%gen7_team%' or logical_path like '%str_debug_team_color%' limit 30").fetchall()
    source_defs = connection.execute("select logical_path, size from resolved_assets where logical_path like '%structure%' and extension in ('.fx','.fxo','.material','.edfm','.shader','.xml') limit 30").fetchall()
finally:
    connection.close()
summary = {
    'schema': 'berber.structure-owner-contract-inspection/v1',
    'status': 'native_team_layer_found_authoring_producer_unqualified',
    'fixture': str(fixture.relative_to(ROOT)),
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'material_source': decoded['material']['source'],
    'team_materials': team,
    'stock_collection_effect': decoded['structure_collection_contract']['effect'],
    'native_channel_layouts': decoded['encoder_contract']['confirmed_stock_channel_layouts'],
    'encoder_contract': decoded['encoder_contract'],
    'stock_slot_collisions': slot_conflicts,
    'variant_api_flattened_slots': slots,
    'variant_api': {name: str(inspect.signature(value)) for name, value in vars(model_variants).items() if inspect.isfunction(value) and name in ('material_slots', 'rewrite_material', 'set_texture', 'set_parameter', 'build')},
    'variant_api_layer7_is_first_material_not_main': slots['textures']['albedoTex7'].replace('\\', '/') != next(t['logical_path'] for b in team[0]['blocks'] for t in b.get('textures', []) if t['name'] == 'albedoTex7'),
    'indexed_native_team_assets': team_assets,
    'indexed_structure_source_definitions': source_defs,
    'source_export_evidence': {
        'static_material_adoption': str(EXT / 'material_adoption.py'),
        'static_export': str(EXT / 'asset_authoring.py'),
        'decoder_owner_mix': 'preview only; adoption follows unblended base input',
        'export_semantics': ['albedo', 'normal', 'roughness', 'metalness'],
        'native_source_material_schema_confirmed': False,
        'structure_producer_texture_packing_confirmed': False,
        'native_options_bit_semantics_confirmed': False,
    },
    'new_cook_attempted': False,
    'native_two_owner_acceptance': 'pending',
}
target = Path(__file__).with_name('native-material-evidence.json')
target.write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({k: summary[k] for k in ('status', 'stock_collection_effect', 'variant_api_layer7_is_first_material_not_main', 'indexed_native_team_assets', 'indexed_structure_source_definitions', 'new_cook_attempted')}, indent=2))
