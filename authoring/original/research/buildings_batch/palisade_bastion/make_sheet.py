from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];O=R/'output/buildings_batch/palisade_bastion'
sheet=Image.new('RGB',(1536,1600),(35,35,35));d=ImageDraw.Draw(sheet)
for age in range(1,5):
 im=Image.open(O/f'age{age}_preview.png').convert('RGB').resize((768,768));x=((age-1)%2)*768;y=((age-1)//2)*800;sheet.paste(im,(x,y+32));d.text((x+16,y+9),f'AGE {age} - CORNER / compact automatic cap',fill='white')
sheet.save(O/'contact_sheet.png');sheet.save(O/'contact_sheet_final.png');sheet.save(O/'contact_sheet_final_002.png')
for age in range(1,5):
 s=Image.new('RGB',(768,560),(35,35,35));d=ImageDraw.Draw(s)
 for i,n in enumerate(['front','back','left','right','top','bottom']):
  x=(i%3)*256;y=(i//3)*280;s.paste(Image.open(O/f'age{age}_{n}.png').convert('RGB'),(x,y+24));d.text((x+8,y+6),n,fill='white')
 s.save(O/f'age{age}_six_side_sheet.png');s.save(O/f'age{age}_six_side_final.png');s.save(O/f'age{age}_six_side_final_002.png')
