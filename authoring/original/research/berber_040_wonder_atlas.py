"""Native surface sampling only; Koutoubia geometry remains original."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
root=Path(__file__).resolve().parents[1];src=root/'art/building_remix_0_4_0/fez/native_texture_inputs';out=root/'art/building_remix_0_4_0/wonder';atlas=Image.new('RGB',(2560,1024));proof=[]
for i,(name,color,repeats) in enumerate([('str_brick_wall_19_alb',(.76,.61,.43),(2,3)),('str_plaster_daub_01_alb',(.95,.87,.71),(2,2)),('str_wood_abb_planks_01_alb',(.43,.27,.14),(2,2)),('str_trim_stone_abbasid_01_alb',(.42,.58,.47),(1,2)),('str_shingle_clay_sul_04_alb',(.25,.47,.34),(3,5))]):
 p=src/(name+'.png');im=Image.open(p).convert('RGB');a=np.asarray(im).astype(float)/255;g=a.mean(2);g=(g-g.mean())*.65+.86;a=np.uint8(np.clip(g[:,:,None]*np.array(color)*255,0,255));im=Image.fromarray(a).resize((512//repeats[0],1024//repeats[1]));tile=Image.new('RGB',(512,1024))
 for y in range(0,1024,im.height):
  for x in range(0,512,im.width):tile.paste(im,(x,y))
 atlas.paste(tile,(i*512,0));proof.append({'slot':i,'native_source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'repeat':repeats})
# Native texture cooker requires power-of-two extents. Resize the complete atlas;
# normalized strip UVs remain unchanged, including their one-fifth boundaries.
atlas.resize((2048,1024),Image.Resampling.LANCZOS).save(out/'native_surface_atlas.png');(out/'native-texture-provenance.json').write_text(json.dumps(proof,indent=2))
