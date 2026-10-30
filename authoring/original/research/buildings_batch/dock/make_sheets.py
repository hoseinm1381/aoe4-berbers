from pathlib import Path
import sys
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parents[3]/'output/buildings_batch/dock'
for age in [int(x) for x in sys.argv[1:]]:
 s=Image.new('RGB',(1200,800),'#292e31');d=ImageDraw.Draw(s)
 for i,name in enumerate(['front','back','left','right','top','bottom']):
  s.paste(Image.open(O/f'age{age}_{name}.png').convert('RGB'),((i%3)*400,(i//3)*400));d.text(((i%3)*400+8,(i//3)*400+8),name,fill='white')
 s.save(O/f'age{age}_sixside.png')
