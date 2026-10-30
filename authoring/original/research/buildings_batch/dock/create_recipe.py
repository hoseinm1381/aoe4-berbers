from pathlib import Path
s=Path('art/buildings/house/build_house.py').read_text();s=s[:s.index('def build(age):')].replace('/house','/dock').replace('House','Dock').replace('house','dock')
Path('art/buildings/dock/build_dock.py').write_text(s)
s=Path('research/buildings_batch/market/run_hidden.py').read_text().replace('/market','/dock').replace('build_market','build_dock');Path('research/buildings_batch/dock/run_hidden.py').write_text(s)
