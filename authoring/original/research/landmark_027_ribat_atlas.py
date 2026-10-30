"""Rebuildable original earthen architecture atlas, no external imagery or fixed team colour."""
from pathlib import Path
import numpy as np
from PIL import Image
import sys
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'art/landmarks_0_2_7/ribat/textures'
OUT.mkdir(parents=True,exist_ok=True)
N=2048; S=512
rng=np.random.default_rng(2701)
y,x=np.mgrid[:S,:S]
color=np.zeros((N,N,3),np.uint8); height=np.zeros((N,N),np.float32); rough=np.zeros((N,N),np.float32)
palette=[(164,102,60),(191,133,82),(132,87,53),(83,58,36),(118,107,85),(145,115,79),(179,143,92),(213,182,135),(153,102,67),(173,121,78),(137,88,52),(69,49,33),(117,107,88),(147,122,88),(166,123,78),(201,165,112)]
labels=['earth','plaster','roof','timber','stone','woven','motif','lighttrim']*2
for i,base in enumerate(palette):
 r,c=divmod(i,4); label=labels[i]
 grain=rng.normal(0,1.7,(S,S)); broad=2*np.sin(x/51)*np.sin(y/47)
 cloudseed=(rng.random((16,16))*255).astype(np.uint8);cloud=np.asarray(Image.fromarray(cloudseed).resize((S,S),Image.Resampling.BICUBIC)).astype(float)/255-.5
 broad+=cloud*15
 h=grain*.10+broad*.08; shade=grain+broad
 if label in ['earth','plaster']:
  dirt=(1-y/S)**4*(8+5*np.sin(x/38)**2); streaks=(np.sin(x/23+.4*np.sin(y/41))> .91)*(1-y/S)**2*6
  crack=np.zeros((S,S))
  for k in range(5):
   line=40+k*97+4*np.sin(y/25+k)+.045*y;crack+=(abs(x-line)<.85)*(y<160+k*32)
  shade-=dirt+streaks+crack*9;h-=crack*.14;h+=cloud*.5
 if label=='earth':
  joints=(y%68<2); h-=joints*.18; shade-=joints*7
 elif label=='timber':
  veins=np.sin(y/2.8+2*np.sin(x/57))+np.sin(y/8+x/92); seams=(y%74<3)
  h+=veins*.5-seams*.5;shade+=veins*9-seams*18
 elif label=='stone':
  mortar=(y%90<5)|((x+(y//90%2)*93)%186<5);h-=mortar*.75;shade-=mortar*24
 elif label=='woven':
  weave=np.sin(x*np.pi/3)*np.sin(y*np.pi/3);h+=weave*.45;shade+=weave*9
 elif label=='motif':
  diamond=(abs((x%128)-64)+abs((y%128)-64)); motif=(diamond>43)&(diamond<49)
  h+=motif*.5;shade-=motif*32
 yy=slice(r*S,(r+1)*S);xx=slice(c*S,(c+1)*S)
 color[yy,xx]=np.clip(np.array(base)+shade[:,:,None],0,255).astype(np.uint8)
 height[yy,xx]=h;rough[yy,xx]=np.clip(.88+grain*.009 if label!='timber' else .72+grain*.02,0,1)
dy,dx=np.gradient(height);vec=np.stack((-dx*.45,-dy*.45,np.ones_like(height)),axis=-1);vec/=np.linalg.norm(vec,axis=-1)[:,:,None]
Image.fromarray(color).save(OUT/'ribat_basecolor.png')
Image.fromarray(np.clip((vec*.5+.5)*255,0,255).astype(np.uint8)).save(OUT/'ribat_normal.png')
Image.fromarray((rough*255).astype(np.uint8)).save(OUT/'ribat_roughness.png')
Image.fromarray(np.zeros((N,N),np.uint8)).save(OUT/'ribat_metallic.png')
print('Original atlas maps rebuilt',OUT)


