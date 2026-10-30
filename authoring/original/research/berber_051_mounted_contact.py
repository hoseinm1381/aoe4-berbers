from pathlib import Path
from PIL import Image,ImageDraw
R=Path('art/unit_skin_0_5_1/mounted');names=['zenata_age04','scout_age01','mehari_age02','sanhaja_age03','lancer_age04'];canvas=Image.new('RGB',(1000,5*350),'#dddddd');d=ImageDraw.Draw(canvas)
for j,n in enumerate(names):
 for i,state in enumerate(['before','after']):
  im=Image.open(R/n/f'skin-{state}-face.png').convert('RGB');im.thumbnail((500,325));canvas.paste(im,(i*500,j*350+25));d.text((i*500+10,j*350+5),n+' '+state,fill='black')
canvas.save(R/'mounted-skin-face-comparison.png')
