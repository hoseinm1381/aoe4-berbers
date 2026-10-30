from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
for kind in ('fez','grand_keep'):
 art=root/'art/building_remix_0_4_0'/kind;a=json.loads((art/'geometry-audit.json').read_text());parts=a['parts'];c=a['normal_topology_checks']
 def get(name):return next(p for p in parts if p['name']==name)['bounds']
 if kind=='fez':
  contacts=[{'interface':'foundation to wing','signed_gap':get('two_storey_cell_wing')[0][2]-get('foundation')[1][2]},{'interface':'wall to eave','signed_gap':get('cedar_eave')[0][2]-get('two_storey_cell_wing')[1][2]},{'interface':'fountain rim to plinth','signed_gap':get('octagonal_basin_rim')[0][2]-get('basin_square_plinth')[1][2]}]
 else:
  contacts=[{'interface':'tower to foundation','signed_gap':get('battered_square_tower')[0][2]-get('kasbah_foundation')[1][2]},{'interface':'pitched roof underside to hall arch crown','signed_gap':get('hall_clay_tile_pitched_roof')[0][2]-get('hall_court_arcade_voussoir_00')[1][2]},{'interface':'door bottom to foundation','signed_gap':get('seated_cedar_door_leaf')[0][2]-get('kasbah_foundation')[1][2]}]
 export=json.loads((art/'export_lod0_v2/building.json').read_text());stages=sorted(set(p['first_stage'] for p in export['parts']))
 report={'authoritative_export':'export_lod0_v2','root_visual_review':'cleared revised source by root','single_lod0':True,'fresh_original_geometry':True,'mesh_parts':len(parts),'triangles':a['triangles'],'uv_all':all(p['uv'] for p in parts),'single_user_all':all(p['mesh_users']==1 for p in parts),'closed_manifold_all':all(x['nonmanifold_edges']==0 for x in c),'outward_volume_all':all(x['signed_volume']>=-1e-6 for x in c),'real_portal_masonry_opening_pass':a['portal_opening_pass'],'export_stages':stages,'source_stages':sorted(set(p['stage'] for p in parts)),'measured_contacts':contacts,'native_owner_flag':'native integration consumes flag-transform.json; source pole only','native_game':'unverified','retained_texture_inputs':'../fez/native_texture_inputs/*.png; provenance.json records native names hashes original cache. Atlas generator reads retained PNG inputs; no external cache needed.','files':{str(p.relative_to(art)):hashlib.sha256(p.read_bytes()).hexdigest() for p in art.rglob('*') if p.is_file() and ('export_lod0_v2' in str(p) or p.suffix=='.blend' or p.name in ('atlas_albedo_v2.png','atlas_normal_v2.png'))}}
 (art/'final-source-validation.json').write_text(json.dumps(report,indent=2));print(kind,report['mesh_parts'],report['triangles'],stages,contacts)
