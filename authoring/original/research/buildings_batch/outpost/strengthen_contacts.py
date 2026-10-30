from pathlib import Path
p=Path('research/buildings_batch/outpost/audit_saved.py');s=p.read_text();mark="   front=[o for o in mesh if o.name.startswith('lookout_parapet_front')]"
insert="""   for prefix in ['springald_stock_runner','cannon_ground_skid','arrow_cover_frame','arrow_shield_panel']:
    for o in mesh:
     if o.name.startswith(prefix):
      gap=bounds(o)[0][2]-bounds(roof)[1][2];assert abs(gap)<1e-5
      sourcechecks.append({'child':o.name,'parent':'lookout_floor','measured_signed_gap':gap,'pass':True})
   for o in [o for o in mesh if o.name.startswith('canopy_long_beam')]:
    gap=bounds(can)[0][2]-bounds(o)[1][2];assert abs(gap)<1e-5
    sourcechecks.append({'child':'fitted_flat_canopy','parent':o.name,'measured_signed_gap':gap,'pass':True})
"""
s=s.replace(mark,insert+mark);p.write_text(s)
