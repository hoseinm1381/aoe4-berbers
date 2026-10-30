from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=root/'art/buildings/market/build_market.py';s=p.read_text()
prefix=s[:s.index('def build(age):')].replace('/market','/barracks').replace('Market','Barracks').replace('market','barracks')
tail=s[s.index('    bpy.context.view_layer.update();objects='):].replace('Market','Barracks').replace('MARKET','BARRACKS').replace('market','barracks').replace('Age2_Reference','Age1_Reference').replace('Age II','Age I').replace("for age in [2,3,4]","for age in [1,2,3,4]").replace("'ages':[2,3,4]","'ages':[1,2,3,4]").replace('>=-4.001','>=-3.001').replace('<=4.001','<=3.001').replace("'footprint_m':[8,8]","'footprint_m':[6,6]").replace("'clear_gateway_m':1.8","'clear_gateway_m':1.4").replace("'central_transit_corridor_m':1.8","'central_transit_corridor_m':1.4").replace('x=8 y=8','x=6 y=6').replace('cam.data.ortho_scale=12.2','cam.data.ortho_scale=9.5').replace('scene.cycles.samples=4','scene.cycles.samples=8')
body=(Path(__file__).parent/'build_body.txt').read_text()
(root/'art/buildings/barracks/build_barracks.py').write_text(prefix+body+tail)
