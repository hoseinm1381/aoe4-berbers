from pathlib import Path
p=Path('research/buildings_batch/tc/verify_delivery.py');s=p.read_text();needle=" records.append({'age':age,"
replacement=" av=next(o['positive_volume'] for o in d['objects'] if o['object']=='courtyard_arcade_wall'); uncut=.32*3.5*(2.55+age*.3-.50)*(8/9.6)*(8/8.8); assert av<uncut*.80\n records.append({'arcade_remaining_solid_fraction':av/uncut,'age':age,"
assert needle in s;s=s.replace(needle,replacement);p.write_text(s)
