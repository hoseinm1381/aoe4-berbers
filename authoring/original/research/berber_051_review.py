"""Rebuild compact matched-angle civilian/infantry skin review contacts."""
from PIL import Image, ImageDraw
from berber_051_skin import ART

names=['trader_age02','trader_age02_female','villager_age01','imam_age03','archer_age02','handgunner_age04']
base=ART/'infantry_civilian/previews'
for filename,columns in [('skin-comparison.png',['before-face-hands','after-face-hands']),
                         ('owner-colour-preview.png',['after-team-red-face-hands','after-team-blue-face-hands'])]:
    page=Image.new('RGB',(1000,len(names)*440),(220,220,220));draw=ImageDraw.Draw(page)
    for row,name in enumerate(names):
        for col,kind in enumerate(columns):
            im=Image.open(base/name/(kind+'.png')).convert('RGB');im.thumbnail((490,410))
            page.paste(im,(col*500,row*440+25));draw.text((col*500+8,row*440+6),name+' '+kind,fill='black')
    page.save(ART/'infantry_civilian'/filename)
