"""Generate a compact source-art gallery with separately supplied build evidence.

The strict model collector remains the source authority. Report status is shown
only when its report is supplied; rendered shaders never imply native tests.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from berber_050_admission import EXPECTED, admit_coverage
from berber_050_common import ART, BASE_SHA, GUID, OUT, ROOT, read, sha
from berber_050_model_payloads import absolute, collect


HISTORY = [
    ('Met: Almoravid and Almohad art', 'https://www.metmuseum.org/fr/essays/the-art-of-the-almoravid-and-almohad-periods-ca-1062-1269'),
    ('Sijilmasa archaeology and caravan context', 'https://caravans.library.northwestern.edu/tour/saharan-frontiers/sijilmasa/'),
    ('Met: Sahel and trans-Saharan trade', 'https://www.metmuseum.org/de/exhibitions/sahel-art-empire-sahara/inside-the-exhibition'),
    ('Almoravid dress study', 'https://www.tandfonline.com/doi/full/10.1080/09503110.2024.2306087'),
]


def esc(value):
    return html.escape(str(value), quote=True)


def load_report(path):
    if path is None:
        return None
    report = read(path)
    # A present archive must agree with the supplied report. Absent disposable
    # cook/readback files after cleanup do not invalidate the saved receipt.
    archive = report.get('archive') or report.get('cook', {}).get('archive')
    digest = report.get('archive_sha256') or report.get('cook', {}).get('sha256')
    if archive and digest and absolute(archive).is_file() and sha(absolute(archive)) != digest:
        raise ValueError(f'Supplied evidence archive changed: {archive}')
    return {'path': str(path), 'sha256': sha(path), 'data': report}


def font(size):
    path = Path('C:/Windows/Fonts/segoeui.ttf')
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def sheet(row, destination):
    panels = [('Official donor', 'preview_donor_lod1'),
              ('Berber candidate', 'preview_candidate_lod1'),
              ('Red shader preview', 'preview_team_red'),
              ('Blue shader preview', 'preview_team_blue')]
    rider = ('preview_donor_rider_only', 'preview_candidate_rider_only')
    if all(row.get(key) and absolute(row[key]).is_file() for key in rider):
        panels.extend([('Donor isolated rider', rider[0]), ('Candidate isolated rider', rider[1])])
    width, height, gutter, label = 350, 458, 10, 30
    result = Image.new('RGB', (2*width+3*gutter, (len(panels)//2)*(height+label+gutter)+gutter), '#24272a')
    draw = ImageDraw.Draw(result)
    for index, (caption, key) in enumerate(panels):
        path = absolute(row[key])
        expected = row.get(key+'_sha256')
        if expected and sha(path) != expected:
            raise ValueError(f'Stale review image: {row["private_variant_name"]}:{key}')
        with Image.open(path) as source:
            image = ImageOps.contain(source.convert('RGB'), (width, height))
        x, y = gutter+(index%2)*(width+gutter), gutter+(index//2)*(height+label+gutter)
        draw.text((x+5, y+4), caption, fill='#f1ede4', font=font(18))
        result.paste(image, (x+(width-image.width)//2, y+label+(height-image.height)//2))
    result.save(destination, quality=82, optimize=True)


def evidence_line(title, report):
    if report is None:
        return f'<li><strong>{esc(title)}:</strong> PENDING — final report not supplied.</li>'
    data = report['data']
    status = data.get('status', 'supplied; no pass status')
    if title == 'Coverage':
        try:
            admit_coverage(data)
            status = '39 entries admitted by coverage checks'
        except (ValueError, KeyError) as error:
            status = f'NOT ADMITTED: {error}'
    return (f'<li><strong>{esc(title)}:</strong> {esc(status)} '
            f'<details><summary>Report identity</summary><code>{esc(report["path"])}</code>'
            f'<p>SHA-256 <code>{esc(report["sha256"])}</code></p></details></li>')


def generate(manifests, *, coverage=None, composition=None, cook=None, output=None):
    models = collect(manifests)
    output = Path(output or OUT/'MODEL_REVIEW.html')
    # Keep generated output within the release-owned review locations.
    if output.absolute() != (OUT/'MODEL_REVIEW.html').absolute():
        raise ValueError('Review HTML output must be release-owned OUT/MODEL_REVIEW.html')
    review = OUT/'review'
    review.mkdir(parents=True, exist_ok=True)
    reports = {key:load_report(value) for key,value in [('coverage',coverage),('composition',composition),('cook',cook)]}
    coverage_rows = {(r['family'],r['age']):r for r in reports['coverage']['data']['rows']} if reports['coverage'] else {}
    grouped = {}
    for row in models.values():
        key = (row['family'],row['age'])
        if row['family'] not in EXPECTED or row['age'] not in EXPECTED[row['family']]:
            raise ValueError(f'Unexpected family-age source: {key}')
        grouped.setdefault(key,[]).append(row)
    required = {(f,a) for f,ages in EXPECTED.items() for a in ages if f!='tuareg'}
    if set(grouped)!=required:
        raise ValueError(f'Source roster differs: missing={required-set(grouped)}, extra={set(grouped)-required}')
    if len(models)!=49:
        raise ValueError(f'Expected 49 active native model resources; found {len(models)}')
    coverage_html = []
    for family,ages in EXPECTED.items():
        for age in ages:
            key=(family,age)
            approved=coverage_rows.get(key,{})
            if family=='tuareg':
                status='Preserved accepted 0.4.0 art; no new 0.5.0 source.'
                status+=' Baseline archive preservation recorded.' if approved.get('status')=='preserved_accepted' else ' Final archive preservation report pending.'
                count='preserved'
            else:
                count=str(len(grouped[key]))
                status=approved.get('status','Source prepared; final coverage report pending')
            coverage_html.append(f'<tr data-family="{esc(family)}" data-age="{age}"><td>{esc(family.title())}</td><td>{age}</td><td>{count}</td><td>{esc(status)}</td></tr>')
    cards=[]
    images=[]
    for name,row in sorted(models.items(),key=lambda pair:(pair[1]['family'],pair[1]['age'],pair[0])):
        recipe=read(absolute(row['geometry_recipe']))
        description=row.get('design') or recipe.get('design') or 'Bounded donor-derived garment and silhouette treatment; native rig and equipment retained.'
        if not isinstance(description,str):
            description=json.dumps(description,ensure_ascii=False)
        image=review/(name+'.jpg')
        sheet(row,image)
        images.append(image)
        lods=all(row.get(f'preview_candidate_lod{lod}') and absolute(row[f'preview_candidate_lod{lod}']).is_file() for lod in (2,3))
        cards.append(f'''<article class="model" data-family="{esc(row['family'])}" data-age="{row['age']}">
<h3>{esc(name)}</h3><p class="meta">{esc(row['family'].title())} · Age {row['age']} · {esc(row.get('state','body'))}</p>
<a href="review/{esc(image.name)}" target="_blank"><img src="review/{esc(image.name)}" loading="lazy" alt="Matched donor, candidate and two shader colour previews of {esc(name)}"></a>
<p>{esc(description)}</p><p class="meta">{'LOD2/3 source images recorded.' if lods else 'Additional LOD image evidence is in the authoring ledger when available.'} Player-colour panels simulate the native shader in Blender.</p>
<details><summary>Exact donor and source provenance</summary><dl>
<dt>Official model</dt><dd><code>{esc(row['official_donor_rgm'])}</code></dd>
<dt>Official RGM SHA-256</dt><dd><code>{esc(row['official_donor_rgm_sha256'])}</code></dd>
<dt>Native RRGeom SHA-256</dt><dd><code>{esc(row['native_source_rrgeom_sha256'])}</code></dd>
<dt>Authored RRGeom SHA-256</dt><dd><code>{esc(row['authored_rrgeom_sha256'])}</code></dd>
<dt>Recipe</dt><dd><code>{esc(row['geometry_recipe'])}</code></dd>
<dt>Packed Blender source</dt><dd><code>{esc(row['editable_blend'])}</code></dd>
<dt>Decoded native source manifest</dt><dd><code>{esc(row['decoded_manifest'])}</code></dd>
</dl></details></article>''')
    family_options=''.join(f'<option value="{esc(f)}">{esc(f.title())}</option>' for f in EXPECTED)
    history=''.join(f'<li><a href="{esc(url)}">{esc(title)}</a></li>' for title,url in HISTORY)
    supplied=''.join(evidence_line(title,reports[key]) for title,key in [('Coverage','coverage'),('Fresh native cook','cook'),('Final archive composition','composition')])
    document=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Berber 0.5.0 candidate model review</title><style>
:root{{color-scheme:dark}}body{{font:16px/1.5 system-ui,sans-serif;margin:0;background:#171b1e;color:#e6e5df}}main{{max-width:1440px;margin:auto;padding:24px}}h1,h2,h3{{line-height:1.2}}a{{color:#9bc7ee}}code{{overflow-wrap:anywhere;font-size:.8em}}.pending{{padding:20px;border:2px solid #d9a34a;background:#392d19;border-radius:8px}}.meta{{font-size:14px;color:#c1c7ca}}.filters{{position:sticky;top:0;background:#20272cf5;padding:14px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;z-index:1}}select{{font:inherit;padding:6px}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:7px;border-bottom:1px solid #41484c;text-align:left}}.table-wrap{{overflow:auto;max-height:520px}}.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(340px,100%),1fr));gap:20px}}.model{{background:#242b30;padding:14px;border:1px solid #414b51;border-radius:8px}}.model h3{{overflow-wrap:anywhere}}img{{width:100%;height:auto;display:block}}details{{margin:8px 0}}dt{{margin-top:8px;font-weight:bold}}dd{{margin:0}}[hidden]{{display:none!important}}section{{margin:28px 0}}
</style><main><h1>Berber 0.5.0 candidate model review</h1>
<div class="pending"><strong>NATIVE TESTS PENDING</strong><p>Import, lobby selection, appearance, dynamic player colour, animation and gameplay have not been accepted in a fresh native match. These are Blender source reviews and separately reported build checks.</p></div>
<p>49 active model resources cover 35 new family-age combinations. Four accepted Tuareg age entries are preserved from the packaged 0.4.0 baseline: 39 total roster entries. Siege, navy and existing building art remain outside this unit-art change.</p>
<section><h2>Evidence boundaries</h2><ul><li><strong>Source/native format:</strong> hash-pinned donor geometry, packed editable Blender files, bounded native vertex-stream recipes and source previews collected. Geometry checks preserve native skeleton, rest/bind data, skin, UVs, topology and opaque resource bytes; their exact receipts remain in authoring ledgers.</li>{supplied}<li><strong>Native appearance / colour / animation:</strong> PENDING. Static rest views can place a rider beneath its mount; isolated rider panels expose clothing without changing native coordinates. Viewport colour panels do not prove native team colour.</li></ul></section>
<div class="filters"><label>Family <select id="family"><option value="">All families</option>{family_options}</select></label><label>Age <select id="age"><option value="">All ages</option><option>1</option><option>2</option><option>3</option><option>4</option></select></label><span id="count">49 model resources</span></div>
<section><h2>39 family-age entries</h2><div class="table-wrap"><table><thead><tr><th>Family</th><th>Age</th><th>Resources</th><th>Evidence status</th></tr></thead><tbody>{''.join(coverage_html)}</tbody></table></div></section>
<section><h2>Matched source comparisons</h2><p>Open a sheet for its original resolution. Panels preserve source render angles and proportions. The donor's recognizable role and equipment remain; edited-vertex fractions are diagnostics and do not measure the requested qualitative 10–50% design change.</p><div class="gallery">{''.join(cards)}</div></section>
<section><h2>Historical context</h2><p>Broad Maghrebi, Andalusi and trans-Saharan context informs the design; these sources do not document an exact uniform for every gameplay role or tribe. Evidence is strongest around the eleventh through fifteenth centuries. Ages show game progression; later firearm treatments are not claimed as verified Almohad uniforms.</p><ul>{history}</ul></section>
<section><h2>Rebuild identity</h2><p>Candidate version 0.5.0 · project GUID <code>{GUID}</code><br>Protected packaged 0.4.0 baseline SHA-256 <code>{BASE_SHA}</code></p><p>See the accompanying REBUILD_050.md for retained sources, regeneration and native acceptance steps.</p></section>
</main><script>const family=document.getElementById('family'),age=document.getElementById('age');function filter(){{for(const item of document.querySelectorAll('[data-family]'))item.hidden=!!((family.value&&item.dataset.family!==family.value)||(age.value&&item.dataset.age!==age.value));document.getElementById('count').textContent=[...document.querySelectorAll('.model')].filter(x=>!x.hidden).length+' model resources';}}family.onchange=filter;age.onchange=filter;</script></html>'''
    output.write_text(document,encoding='utf8')
    return {'review':str(output),'review_sha256':sha(output),'models':len(models),'family_age_entries':39,
            'review_images':[str(p) for p in images],'review_image_bytes':sum(p.stat().st_size for p in images),
            'native_acceptance':'pending'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifests',nargs='+',type=Path,required=True)
    parser.add_argument('--coverage',type=Path)
    parser.add_argument('--composition',type=Path)
    parser.add_argument('--cook',type=Path)
    args=parser.parse_args()
    print(json.dumps(generate(args.manifests,coverage=args.coverage,composition=args.composition,cook=args.cook),indent=2))
