from berber_051_mounted_skin import entries,OUT
from berber_050_common import ROOT,read,write
rows=[]
for kind,row,rider in entries():
 d=read(ROOT/row['decoded_manifest']);slots=[{'material':m['name'],'slot':'skinTintLUT','source':t['logical_path'],'target':'art/scenario/garrison/berber_skin_051/fair_skin_lut.rrtex'} for m in d['material']['materials'] for t in m['textures'] if t['name']=='skinTintLUT']
 rows.append({'name':row['private_variant_name'],'state':kind,'private_stem':row['private_stem'],'route':'native_skinTintLUT_reference_only' if slots else 'baked_albedo_skin_mask','skin_slots':slots,'skin_only_png':'art/unit_skin_0_5_1/mounted/zenata_age04/rider-albedo.png' if not slots else None,'geometry_unchanged':True,'albedo_png_unchanged':bool(slots),'reason':'Native shader selects skin through pattern G; owner R and hair B preserved.' if slots else 'Saladin donor has baked face/hands and no native skinTintLUT slot; bounded fair-skin PNG only.'})
assert len(rows)==26 and sum(bool(r['skin_slots']) for r in rows)==25
write(OUT/'mounted-skin-routes.json',{'resources':rows,'resource_count':26,'lut_resource_count':25,'baked_resource_count':1})
print('26 routes,25 LUT,1 baked')
