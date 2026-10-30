from pathlib import Path
q=Path('research/buildings_batch/palisade');s=(q/'run_hidden.py').read_text().replace("ROOT/'art/buildings/palisade/build_palisade.py'","ROOT/'research/buildings_batch/palisade/audit_saved.py'").replace("'blender.log'","'audit.log'").replace("'process.json'","'audit_process.json'");(q/'run_audit.py').write_text(s)
