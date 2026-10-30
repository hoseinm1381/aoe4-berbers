"""Durable authoring coverage, asset hashes and review index; never cooks."""
import json,hashlib,html,base64,io
from PIL import Image
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DESIGN=ROOT/'Design/asset_overhaul';OUT=ROOT/'output/buildings_batch'
inventory=json.loads((DESIGN/'ASSET_INVENTORY.json').read_text(encoding='utf-8'))
cards=[x for x in inventory['items'] if x['category'] in ('Buildings','Landmarks')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def candidates(directory):
    priority=['delivery.json','DELIVERY_VALIDATION.json','BUILD_COMPLETE.json']
    return [directory/n for n in priority if (directory/n).exists()]
rows=[]
for card in cards:
    key=card['id'].split('.')[1];art=ROOT/'art/buildings'/key;output=OUT/key
    if key=='tent':
        rows.append({'id':card['id'],'name':card['name'],'status':'accepted_model_0.2.1_colour_blocked','ages':[1,2,3,4],'source':card['next_build_source'],'player_colour':'blocked native static route; 4 saved source masks','preview':'output/tribal_tent/iteration002/four_age_comparison.png'});continue
    found=candidates(output);documents=[]
    for file in found:
        try:documents.append(json.loads(file.read_text(encoding='utf-8')))
        except (ValueError,UnicodeError):pass
    ages=set()
    for doc in documents:
        for v in doc.get('required_ages',doc.get('ages',[])):
            value=v.get('age') if isinstance(v,dict) else v
            if str(value) in ('1','2','3','4'):ages.add(int(value))
    sources=[p for p in art.glob('*.blend') if not any(w in p.name.lower() for w in ('reference','untouched','donor'))]
    exports=list(art.glob('*.fbx'));mask=list(art.glob('*pattern*.png'))+list(art.glob('*mask*.png'))
    previews=[p for p in output.glob('*.png') if ('contact' in p.name or 'sheet' in p.name) and 'side' not in p.name and 'stock' not in p.name]
    previews.sort(key=lambda p:('final' in p.name, p.name in ('contact_sheet.png','age_contact_sheet.png','wall_contact_sheet.png','contact_preview.png'),p.stat().st_mtime),reverse=True)
    if not previews:
        previews=[p for p in output.glob('*.png') if not any(w in p.name.lower() for w in ('side','stock','donor','reference','mask','normal','rough','albedo','metal','interior'))]
        previews.sort(key=lambda p:('preview' in p.name.lower(), 'age' in p.name.lower(), p.stat().st_mtime),reverse=True)
    row={'id':card['id'],'name':card['name'],'key':key,'status':'source_delivery_present' if found and sources and exports else 'pending',
         'ages':sorted(ages),'source_paths':card['source_paths'],'blueprint_targets':card['blueprint_targets'],
         'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sources],
         'fbx_count':len(exports),'delivery_records':[p.relative_to(ROOT).as_posix() for p in found],
         'owner_masks':[p.relative_to(ROOT).as_posix() for p in sorted(set(mask))],
         'player_colour':'source masks only; mandatory native integration remains blocked',
         'preview':previews[0].relative_to(ROOT).as_posix() if previews else None}
    rows.append(row)
result={'recorded':'2026-10-13','scope':'all 26 building and 6 landmark families; source-only batch, no mod build','families':len(rows),
        'source_deliveries':sum(x['status']=='source_delivery_present' for x in rows),'native_colour_status':'blocked; no native-complete claim',
        'rows':rows}
(DESIGN/'BUILDINGS_BATCH.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Building batch review — 2026-10-13','',
    'Sources are separate from the production mod. Native player-colour support is a mandatory unresolved gate; saved owner masks do not prove it.',
    '', '| Asset | Ages reported | Source delivery | Review |','|---|---|---|---|']
for row in rows:
    preview=f"[Preview](<{(ROOT/row['preview']).as_posix()}>)" if row.get('preview') else 'pending'
    lines.append(f"| {row['name']} | {', '.join(map(str,row.get('ages',[]))) or 'pending audit'} | {row['status']} | {preview} |")
(DESIGN/'BUILDINGS_REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
cards_html=[]
for row in rows:
    image_html=''
    if row.get('preview') and (ROOT/row['preview']).exists():
        with Image.open(ROOT/row['preview']) as im:
            im=im.convert('RGB');im.thumbnail((900,900));buf=io.BytesIO();im.save(buf,format='JPEG',quality=86)
        image_html=f'<a href="{(ROOT/row["preview"]).as_uri()}"><img loading="lazy" src="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}" alt="{html.escape(row["name"])} source previews"></a>'
    links=' '.join(f'<a href="{(ROOT/p).as_uri()}">Delivery evidence</a>' for p in row.get('delivery_records',[]))
    sources='<br>'.join(html.escape(x['path']) for x in row.get('sources',[]))
    cards_html.append(f'<article><h2>{html.escape(row["name"])}</h2><p>Ages: {", ".join(map(str,row.get("ages",[]))) or "see source audit"} · {html.escape(row["status"])}</p>{image_html}<p>{links}</p><details><summary>Source files</summary><p>{sources}</p></details></article>')
page='''<!doctype html><meta charset="utf-8"><title>Berber building source review</title><style>
body{background:#181a1e;color:#ebe6da;font:16px system-ui;margin:24px}header{max-width:1100px}h1{margin-bottom:8px}.notice{background:#4b351d;border:1px solid #bf8c45;padding:16px;border-radius:8px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:20px;margin-top:24px}article{background:#24282e;padding:18px;border-radius:10px}h2{margin:0 0 8px}p{color:#c5c4bb;overflow-wrap:anywhere}img{width:100%;object-fit:contain;background:#30343c}a{color:#dbc58b}details{margin-top:12px}summary{cursor:pointer}</style>
<header><h1>Berber buildings — source review</h1><p>2026-10-13 · building and landmark families · current production release stays 0.2.1</p><div class="notice"><strong>Native player colour remains unfinished.</strong> All new sources have owner-colour zones and masks. The installed static exporter does not provide a qualified native structure material/geometry route. Stock structure team colour has been identified, but custom encoding and game acceptance remain pending. These are authoring previews, not in-game proof.</div><p>Click an image for its full-resolution sheet. Construction, animations, walls/navigation, dock exits, scale and LODs need separate integration and game testing. Landmarks reuse their first completed-age source during the preceding construction age.</p></header><main>'''+''.join(cards_html)+'</main>'
(DESIGN/'BUILDINGS_REVIEW.html').write_text(page,encoding='utf-8')
print(json.dumps({'families':len(rows),'delivered_sources':result['source_deliveries'],'pending':[x['key'] for x in rows if x['status']=='pending']}))
