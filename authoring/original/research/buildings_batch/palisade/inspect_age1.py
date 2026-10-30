from pathlib import Path
from PIL import Image,ImageDraw
p=Path('output/buildings_batch/palisade');im=Image.new('RGB',(768,560),'#ddd7ca');d=ImageDraw.Draw(im)
for i,s in enumerate(['front','back','left','right','top','bottom']):
 pic=Image.open(p/f'age1_{s}.png').convert('RGB');x=i%3*256;y=i//3*280;im.paste(pic,(x,y));d.text((x+8,y+261),s,fill='black')
im.save(p/'age1_six.png')
