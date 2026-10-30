from pathlib import Path
R=Path.cwd();Q=R/'research/buildings_batch/fez'
p=(Q/'run_hidden.py').read_text().replace("script=ROOT/'art/buildings/fez/build_fez.py'","script=ROOT/'research/buildings_batch/fez/audit_saved.py'").replace("'blender.log'","'audit.log'").replace("'process.json'","'audit_process.json'");(Q/'run_audit.py').write_text(p)
s=(R/'research/buildings_batch/university/make_contact_sheet.py').read_text().replace('university','fez');(Q/'make_contact_sheet.py').write_text(s)
