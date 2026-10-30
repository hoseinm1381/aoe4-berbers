from html.parser import HTMLParser
from pathlib import Path
import os, json, hashlib
ROOT=Path(__file__).resolve().parents[2]
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
OUT=ROOT/'output/tuareg_art_guard_trial/docs'; OUT.mkdir(parents=True,exist_ok=True)
class Reader(HTMLParser):
    def __init__(self): super().__init__(); self.active=False; self.parts=[]
    def handle_starttag(self,t,a):
        if t=='main': self.active=True
        if self.active and t in ('p','li','h1','h2','h3','tr','pre'): self.parts.append('\n')
    def handle_endtag(self,t):
        if t=='main': self.active=False
    def handle_data(self,s):
        if self.active:self.parts.append(s)
rows=[]
for src in sorted((EXT/'guide').glob('*.html')):
    if src.stem in ('print','404','toc'):continue
    r=Reader();r.feed(src.read_text(encoding='utf-8'));txt=''.join(r.parts)
    (OUT/(src.stem+'.txt')).write_text(txt,encoding='utf-8')
    rows.append({'chapter':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'text_characters':len(txt)})
(OUT/'provenance.json').write_text(json.dumps(rows,indent=2))
print(len(rows),'installed chapters captured')
