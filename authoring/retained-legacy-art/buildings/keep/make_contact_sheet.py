from pathlib import Path
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parents[3]/'output/buildings_batch/keep'
names=['front','back','left','right','top','bottom'];im=Image.new('RGB',(1800,1200),(40,40,40));d=ImageDraw.Draw(im)
for age in [3,4]:
 for i,n in enumerate(names):
  t=Image.open(O/f'age{age}_solid_{n}.png').convert('RGB').resize((300,300));x=i*300;y=(age-3)*600;im.paste(t,(x,y+25));d.text((x+8,y+8),f'Age {age} {n}',fill='white')
 for i,n in enumerate(['preview','top']):
  t=Image.open(O/f'age{age}_{n}.png').convert('RGB').resize((300,275));im.paste(t,(i*300,(age-3)*600+325))
im.save(O/'six_side_contact_sheet.png');p=Image.new('RGB',(1536,768))
for i,age in enumerate([3,4]):p.paste(Image.open(O/f'age{age}_preview.png').convert('RGB'),(i*768,0))
p.save(O/'contact_sheet.png')
