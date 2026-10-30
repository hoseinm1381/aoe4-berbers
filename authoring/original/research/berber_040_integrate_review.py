"""Compact retained source/cook contract review; no duplicated preview images."""
import html
from pathlib import Path
from berber_040_integrate import ROOT,OUT,read,write,sha
from berber_040_integrate_models import ART,static_source

def main():
 targets=read(OUT/'new-targets.json')['targets'];lines=['# Berber 0.4.0 model review','','Native acceptance: UNVERIFIED. Source reviews and cook/readback checks do not establish in-game appearance or behavior.','']
 for target in targets:
  kind=target['kind'];folder=ART/('wonder' if kind=='koutoubia' else kind)
  lines += ['## '+kind.replace('_',' ').title(),'']
  previews=sorted(folder.glob('*gamecamera*.png'),key=lambda p:p.stat().st_mtime,reverse=True)
  if previews:lines += [f'[Current source preview]({previews[0].as_posix()})','']
  lines += [f'Source: `{folder}`. Consuming actor scale: {target["animator_scale"]}. Native marker payload and lifecycle graph must match the consuming donor. Footprint fields are preserved.','']
  if kind!='university':
   source=static_source(kind);lines += [f'Authoritative export: `{source}`.']
   if (source/'building.json').exists():
    data=read(source/'building.json');stages=sorted({p['first_stage'] for p in data['parts']})
    lines += [f'Parts: {len(data["parts"])}. Source stage fields: {stages}. FBX SHA256: `{sha(source/"model.fbx")}`.']
  else:lines += [f'Native remix recipe SHA256: `{sha(folder/"recipe.json")}`. Separate14-part courtyard supplement: `{ART/"university_details/export_lod0"}`.']
  binding=OUT/'integration/model-manifests'/f'{kind}-binding.json'
  lines += [f'Binding evidence: `{binding}`; status: '+(read(binding)['status'] if binding.exists() else 'pending')+'.','']
 lines += ['## Native checks remaining','','Two owner colours; preview/construction/completion/age transitions; damage/destruction; entrances/exits/rally; garrison/fire/research/landmark functionality; accepted market/mosque controls.','']
 text='\n'.join(lines);(OUT/'MODEL_REVIEW.md').write_text(text,encoding='utf8')
 # HTML retains direct linked previews and readable preformatted evidence.
 body=html.escape(text)
 for target in targets:
  folder=ART/('wonder' if target['kind']=='koutoubia' else target['kind'])
  previews=sorted(folder.glob('*gamecamera*.png'),key=lambda p:p.stat().st_mtime,reverse=True)
  if previews:body=body.replace(html.escape(f'[Current source preview]({previews[0].as_posix()})'),f'<a href="{previews[0].as_uri()}">Current source preview</a>')
 (OUT/'MODEL_REVIEW.html').write_text('<!doctype html><meta charset="utf-8"><title>Berber 0.4.0 model review</title><style>body{font:15px system-ui;max-width:1100px;margin:32px auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.5}</style><pre>'+body+'</pre>',encoding='utf8')
 print('040_MODEL_REVIEW_WRITTEN')

if __name__=='__main__':main()
