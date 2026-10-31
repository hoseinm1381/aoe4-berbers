"""Record source-only style revision; preserve accepted source and production."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/tribal_tent/iteration002'
ART = ROOT / 'art/tribal_tent/iterations/002'
DESIGN = ROOT / 'Design/asset_overhaul'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path):
    return path.relative_to(ROOT).as_posix()

accepted = read(ROOT / 'art/tribal_tent/iterations/001/iteration.json')
assert accepted['approval_status'] == 'accepted'
assert sha(ROOT / accepted['blend']) == accepted['blend_sha256']
for preview in accepted['previews']:
    assert sha(ROOT / preview['path']) == preview['sha256']
verification = read(OUT / 'saved-source-verification.json')
assert verification['status'] == 'passed'
source_check = read(OUT / 'source-validation.json')
assert source_check['status'] == 'source passed'
snapshot = read(DESIGN / 'SOURCE_INVENTORY.json')
changed = [x['source'] for x in snapshot['instances'] if sha(ROOT / x['source']) != x['sha256']]
assert not changed, changed
manifest = read(DESIGN / 'BUILD_MANIFEST.json')
assert sha(ROOT / manifest['production_project']) == manifest['production_project_sha256']

board = Image.new('RGB', (1748, 1730), (29, 27, 24))
draw = ImageDraw.Draw(board)
title = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 26)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 20)
draw.text((24, 15), 'BERBER TRIBAL TENT — ITERATION 002', font=title, fill=(245, 224, 187))
draw.text((24, 53), 'AoE4-inspired finish revision · approved designs retained · source previews', font=small, fill=(218, 209, 193))
labels = ['AGE I · Portable woven camp', 'AGE II · Tribal council tent', 'AGE III · Dynastic council pavilion', 'AGE IV · Imperial council pavilion']
for i, label in enumerate(labels):
    x, y = 24 + (i % 2) * 874, 98 + (i // 2) * 804
    draw.text((x, y), label, font=small, fill=(245, 224, 187))
    with Image.open(OUT / f'age{i+1}.png') as preview:
        assert preview.size == (850, 750)
        board.paste(preview.convert('RGB'), (x, y + 33))
board.save(OUT / 'four_age_comparison.png')

blend = ART / 'Berber_Tribal_Tent_Ages_I_IV_002.blend'
record = {
    'asset_id': 'building.tent', 'iteration': '002', 'recorded': '2026-10-12',
    'approval_status': 'awaiting_style_review', 'approved_design_baseline': '001',
    'approval_scope': 'General four-age designs accepted in 001; this finish revision awaits user review.',
    'age_approvals': {str(i): 'style_review_pending' for i in range(1, 5)},
    'blend': rel(blend), 'blend_sha256': sha(blend),
    'comparison': rel(OUT / 'four_age_comparison.png'),
    'previews': [{'age': i, 'path': rel(OUT / f'age{i}.png'), 'sha256': sha(OUT / f'age{i}.png')} for i in range(1, 5)],
    'verification': rel(OUT / 'saved-source-verification.json'),
    'changes': ['Thicker poles, ropes and trim for distance readability',
                'Warmer material palette and reduced fabric noise contrast',
                'Exterior water jar and rolled mat on each age',
                'Higher presentation view for roof and silhouette review'],
    'export_status': 'not exported; atlas bake, owner colours and LOD preparation pending',
    'integration_status': 'pending; native scale, footprint, age selection and construction/damage/ruins remain unverified',
    'mod_build': 'not started',
    'historical_status': accepted['historical_status'],
    'freeze_policy': 'On acceptance preserve numbered source and hashes; make later revisions in a new numbered directory.'
}
write(ART / 'iteration.json', record)
for name in ['build_source_002.py', 'finish_source_002.py', 'fresh_source_and_preview_002.py', 'verify_source_002.py']:
    shutil.copyfile(ROOT / 'art/tribal_tent' / name, ART / (name + '.txt'))
write(DESIGN / 'tribal_tent/ITERATIONS.json', {'active_iteration': '002', 'accepted_iteration': '001', 'iterations': [accepted, record]})

inventory = read(DESIGN / 'ASSET_INVENTORY.json')
tent = next(x for x in inventory['items'] if x['id'] == 'building.tent')
tent.update(visual_status='general_design_approved_style_revision_ready', integration_status='pending', iteration='002',
            accepted_iteration='001', design='Design/asset_overhaul/tribal_tent/DESIGN_002.md',
            art_sources=[accepted['blend'], record['blend']], preview=record['comparison'], iteration_record=rel(ART / 'iteration.json'))
write(DESIGN / 'ASSET_INVENTORY.json', inventory)
pending = next(x for x in manifest['pending_assets'] if x['asset_id'] == 'building.tent')
pending.update(iteration='002', source=record['blend'], source_sha256=record['blend_sha256'],
               approval='General designs approved as 001; 002 style finish awaits review', accepted_source=accepted['blend'],
               accepted_source_sha256=accepted['blend_sha256'])
write(DESIGN / 'BUILD_MANIFEST.json', manifest)

progress_path = DESIGN / 'PROGRESS.md'
progress = progress_path.read_text(encoding='utf-8')
progress = progress.replace('Current asset: Tribal Tent, four age variants. Iteration 001 now has four saved Blender source variants and reviewed previews; user approval is pending.',
    'Current asset: Tribal Tent, four age variants. Iteration 001 general designs are approved and preserved; iteration 002 AoE4-inspired finish is saved and awaits style review. No export or mod build.')
entry = '- 2026-10-12: User approved all four general tent designs and requested slight AoE4-style adjustments. Preserved accepted 001 source/preview hashes. Saved 002 with clearer framing/trim, warmer quieter materials and exterior furnishings; saved-source checks passed. Style acceptance and native integration remain pending. Production project and 173 XML hashes unchanged; no export/cook/package.'
if entry not in progress:
    progress += '\n' + entry + '\n'
progress_path.write_text(progress, encoding='utf-8')
inventory_md = DESIGN / 'ASSET_INVENTORY.md'
text = inventory_md.read_text(encoding='utf-8')
text = text.replace('iteration 001 ready for visual review', '001 general designs approved; 002 style review pending')
inventory_md.write_text(text, encoding='utf-8')
write(OUT / 'delivery-record.json', {
    'status': 'ready for user style review', 'iteration': '002', 'source_sha256': record['blend_sha256'],
    'accepted_001_hashes_preserved': True, 'production_xml_files_unchanged': len(snapshot['instances']),
    'production_project_unchanged': True, 'approval': record['approval_status'], 'mod_build': False,
    'saved_source_checks': verification['status'], 'native_acceptance': 'not tested'
})
print(json.dumps({'record': rel(ART / 'iteration.json'), 'board': record['comparison'], 'unchanged_xml': len(snapshot['instances']), 'source_checks': verification['status']}))
