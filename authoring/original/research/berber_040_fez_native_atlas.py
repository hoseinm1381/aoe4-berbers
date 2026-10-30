from pathlib import Path
from PIL import Image,ImageEnhance,ImageOps,ImageDraw
import numpy as np
art=Path('art/building_remix_0_4_0/fez/native_texture_inputs');atlas=Image.new('RGB',(2048,1024))
def tone(name,color,contrast=.5):
 im=Image.open(art/(name+'.png')).convert('RGB').resize((512,512));a=np.asarray(im).astype(float)/255;g=a.mean(2);g=(g-g.mean())*contrast+.83;return Image.fromarray(np.uint8(np.clip(g[:,:,None]*np.array(color)*255,0,255)))
slots=[tone('str_stone_floor_07_alb',(0.78,.68,.53),.85),tone('str_plaster_daub_01_alb',(1,.94,.81),.32),tone('str_wood_abb_planks_01_alb',(.39,.25,.14),.65),tone('str_shingle_clay_sul_04_alb',(.29,.47,.35),.85),tone('str_stone_floor_07_alb',(.95,.89,.72),.65),Image.new('RGB',(512,512),(64,100,102)),tone('str_trim_stone_abbasid_01_alb',(.96,.88,.68),.7),Image.new('RGB',(512,512),(226,218,182))]
# Small ceramic zellij stars retained as designed original texture; native grain overlaid.
im=slots[7];dr=ImageDraw.Draw(im)
for y in range(0,512,32):
 for x in range(0,512,32):
  dr.polygon([(x+16,y+1),(x+20,y+11),(x+31,y+16),(x+20,y+21),(x+16,y+31),(x+11,y+21),(x+1,y+16),(x+11,y+11)],fill=(48,94,77),outline=(151,152,115))
for i,im in enumerate(slots):atlas.paste(im,((i%4)*512,(i//4)*512))
for kind in ('fez','grand_keep'):
 final=atlas.copy()
 if kind=='grand_keep':
  final.paste(tone('str_plaster_daub_01_alb',(.83,.66,.45),.55),(512,0));final.paste(Image.new('RGB',(512,512),(55,52,46)),(512,512))
 final.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(Path('art/building_remix_0_4_0')/kind/'atlas_albedo_v2.png')

# Low strength tangent normals from retained native albedo relief, for compatible static export.
g=np.asarray(atlas).astype(float).mean(2)/255;dy,dx=np.gradient(g);normal=np.stack((-dx*2,-dy*2,np.ones_like(g)),2);normal/=np.linalg.norm(normal,axis=2)[:,:,None];normim=Image.fromarray(np.uint8((normal*.5+.5)*255)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
for kind in ('fez','grand_keep'):normim.save(Path('art/building_remix_0_4_0')/kind/'atlas_normal_v2.png')
