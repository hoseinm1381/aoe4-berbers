"""Assemble compact mounted source review contact sheets from saved PNGs."""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from berber_050_common import ART, ROOT

OUT=ART/'mounted'
rows=json.loads((OUT/'mounted-manifest.json').read_text(encoding='utf8'))['variants']


def grid(items,output,columns=5):
    width,height=280,320
    sheet=Image.new('RGB',(width*columns,height*math.ceil(len(items)/columns)),'#d9d9d9')
    draw=ImageDraw.Draw(sheet)
    for index,(label,file) in enumerate(items):
        x=(index%columns)*width
        y=(index//columns)*height
        image=Image.open(file).convert('RGB')
        image.thumbnail((width-8,height-35))
        sheet.paste(image,(x+(width-image.width)//2,y+28))
        draw.text((x+4,y+5),label,fill='black')
    sheet.save(output)


for lod in (1,2,3):
    key='preview_candidate_lod1' if lod==1 else f'preview_candidate_lod{lod}'
    grid([(row['private_variant_name'],ROOT/row[key]) for row in rows],
         OUT/f'mounted-candidate-lod{lod}-contact.png')

riders=[row for row in rows if row['family'] in ('mehari','sanhaja')]
grid([(row['private_variant_name']+' donor',ROOT/row['preview_donor_rider_only']) for row in riders]+
     [(row['private_variant_name']+' Berber',ROOT/row['preview_candidate_rider_only']) for row in riders],
     OUT/'mounted-camel-rider-only-contact.png',columns=4)

print('MOUNTED_CONTACT_SHEETS',len(rows),len(riders))
