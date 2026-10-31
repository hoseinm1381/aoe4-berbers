from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/berber_update_0_2_2/previews'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
def crop(path):
    im=Image.open(path).convert('RGB');mask=Image.new('L',im.size);mask.putdata([255 if max(p)-min(p)>16 else 0 for p in im.getdata()]);box=mask.getbbox()
    if box:
        x0,y0,x1,y1=box;pad=55;box=(max(0,x0-pad),max(0,y0-pad),min(im.width,x1+pad),min(im.height,y1+pad));im=im.crop(box)
    im.thumbnail((680,600));return im
sheet=Image.new('RGB',(1440,1380),(34,33,31));draw=ImageDraw.Draw(sheet)
for age in range(1,5):
    x=((age-1)%2)*720;y=((age-1)//2)*690;im=crop(OUT/f'age{age}_after.png');sheet.paste(im,(x+(720-im.width)//2,y+(625-im.height)//2));draw.text((x+35,y+635),f'Berber House — Age {age}',font=font,fill=(232,202,156))
sheet.save(OUT/'Berber_Houses_Ages_I_IV.png')
comparison=Image.new('RGB',(1440,2760),(34,33,31));draw=ImageDraw.Draw(comparison)
for age in range(1,5):
    y=(age-1)*690
    for x,label in [(0,'before'),(720,'after')]:
        im=crop(OUT/f'age{age}_{label}.png');comparison.paste(im,(x+(720-im.width)//2,y+(625-im.height)//2));draw.text((x+35,y+635),f'Age {age} — '+('stock Abbasid' if label=='before' else 'Berber remix'),font=font,fill=(232,202,156))
comparison.save(OUT/'Stock_to_Berber_Comparison.png')
print('HOUSE_PREVIEW_SHEETS_READY')
