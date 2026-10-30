"""Rebuildable original earthen architecture atlas, no external imagery or fixed team colour."""
from pathlib import Path
import numpy as np
from PIL import Image
import sys
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'art/landmarks_0_2_7/funduq/textures'
OUT.mkdir(parents=True,exist_ok=True)
N=2048; S=512
rng=np.random.default_rng(2702)
y,x=np.mgrid[:S,:S]
color=np.zeros((N,N,3),np.uint8); height=np.zeros((N,N),np.float32); rough=np.zeros((N,N),np.float32)
palette=[(184,136,92),(208,162,114),(167,130,92),(83,58,36),(118,107,85),(145,115,79),(179,143,92),(213,182,135),(180,130,87),(202,153,106),(164,120,82),(69,49,33),(117,107,88),(147,122,88),(166,123,78),(201,165,112)]
labels=['earth','plaster','roof','timber','stone','woven','motif','lighttrim']*2
for i,base in enumerate(palette):
 r,c=divmod(i,4); label=labels[i]
 grain=rng.normal(0,2.6,(S,S)); broad=7*np.sin(x/61)*np.sin(y/83)+4*np.sin((x+y)/97)
 h=grain*.10+broad*.08; shade=grain+broad
 if label in ['earth','plaster']:
  # Original weathering: low-frequency plaster mottling, runoff, small hairline cracks.
  blot=rng.normal(0,1,(24,24));blot=np.asarray(Image.fromarray(blot.astype(np.float32)).resize((S,S),Image.Resampling.BICUBIC))*4.5
  runoff=np.maximum(np.sin(x/19+np.sin(y/93)),0)**16*(.2+.8*y/S)
  patina=(y/S)**5*13
  shade+=blot-runoff*12-patina;h+=blot*.04-runoff*.12
  cracks=np.zeros((S,S),bool)
  for q in range(7):
   cx=int(rng.integers(24,S-24));cy=int(rng.integers(40,S-100));length=int(rng.integers(35,95))
   for j in range(length):
    xx=int(cx+2*np.sin(j/8)+j*.055);yy=cy+j
    if 0<=xx<S and 0<=yy<S:cracks[yy,xx]=True
  shade-=cracks*23;h-=cracks*.45
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
dy,dx=np.gradient(height);vec=np.stack((-dx*.12,-dy*.12,np.ones_like(height)),axis=-1);vec/=np.linalg.norm(vec,axis=-1)[:,:,None]
Image.fromarray(color).save(OUT/'funduq_basecolor.png')
Image.fromarray(np.clip((vec*.5+.5)*255,0,255).astype(np.uint8)).save(OUT/'funduq_normal.png')
Image.fromarray((rough*255).astype(np.uint8)).save(OUT/'funduq_roughness.png')
Image.fromarray(np.zeros((N,N),np.uint8)).save(OUT/'funduq_metallic.png')
print('Original atlas maps rebuilt',OUT)




