from pathlib import Path
from PIL import Image,ImageDraw
O=Path('output/buildings_batch/university');sheet=Image.new('RGB',(768,550),(235,232,224));d=ImageDraw.Draw(sheet)
for i,n in enumerate(['front','back','left','right','top','bottom']):
 im=Image.open(O/f'age4_{n}.png').convert('RGB');x=(i%3)*256;y=(i//3)*275;sheet.paste(im,(x,y));d.text((x+8,y+256),n,fill=(30,30,30))
sheet.save(O/'age4_six_views.png')
