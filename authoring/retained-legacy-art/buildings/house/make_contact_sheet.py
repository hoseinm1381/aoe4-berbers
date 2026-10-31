from pathlib import Path
from PIL import Image,ImageDraw
import json
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/buildings_batch/house';ART=ROOT/'art/buildings/house'
sheet=Image.new('RGB',(1536,1616),(28,30,34));draw=ImageDraw.Draw(sheet)
for age in range(1,5):
    im=Image.open(OUT/f'age{age}_preview.png').convert('RGB');x=((age-1)%2)*768;y=((age-1)//2)*808
    sheet.paste(im,(x,y));draw.text((x+20,y+775),f'BERBER HOUSE — AGE {age} | source preview; native owner colour pending',fill=(235,231,218))
sheet.save(OUT/'contact_sheet.png')
pattern=Image.open(ART/'pattern.png').convert('RGB');r,g,b=pattern.split();assert g.getextrema()==(0,0) and b.getextrema()==(0,0) and r.getextrema()==(0,255)
(OUT/'texture_audit.json').write_text(json.dumps({'dimensions':pattern.size,'green_range':g.getextrema(),'blue_range':b.getextrema(),'red_range':r.getextrema(),'red_nonzero_pixels':sum(n for v,n in enumerate(r.histogram()) if v),'atlas_uv':'same for albedo and pattern; owner cloth tile 4','native_support':'pending'},indent=2))
