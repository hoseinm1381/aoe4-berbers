from pathlib import Path
from PIL import Image,ImageDraw
O=Path('output/buildings_batch/outpost')
def sheet(items,cols,size,name):
 w,h=size;im=Image.new('RGB',(w*cols,(h+30)*((len(items)+cols-1)//cols)),(220,220,210));d=ImageDraw.Draw(im)
 for i,(label,file) in enumerate(items):
  p=Image.open(O/file).convert('RGB');p.thumbnail((w,h));x=(i%cols)*w;y=(i//cols)*(h+30);im.paste(p,(x+(w-p.width)//2,y));d.text((x+10,y+h+8),label,fill='black')
 im.save(O/name)
sheet([(f'Age {a}',f'age{a}_preview.png') for a in range(1,5)],2,(512,512),'age_contact_sheet.png')
sheet([(f'Age {a} {side}',f'age{a}_{side}.png') for a in range(1,5) for side in ['front','back','left','right','top','bottom']],6,(256,256),'sixside_contact_sheet.png')
sheet([(f'Age {a} {state}',f'age{a}_{state}_preview.png') for a,state in [(2,'stone'),(2,'arrowslits'),(3,'springald'),(4,'cannon')]],2,(512,512),'upgrade_contact_sheet.png')
