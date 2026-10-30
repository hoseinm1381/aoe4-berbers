from pathlib import Path
p=Path('art/buildings/house/build_house.py');s=p.read_text();s=s[:s.index('def build(age):')].replace('/house','/market').replace('House','Market').replace('house','market')
Path('art/buildings/market/build_market.py').write_text(s)
