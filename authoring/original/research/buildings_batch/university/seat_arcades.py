from pathlib import Path
p=Path('art/buildings/university/build_university.py');s=p.read_text().replace("o.location=(x/abs(x)*1.78,yy,0)","o.location=(x/abs(x)*1.78,yy,1.46)").replace("((.85,.85,.85) if slot==5 else (0,0,0))","(0,0,0)");p.write_text(s)
