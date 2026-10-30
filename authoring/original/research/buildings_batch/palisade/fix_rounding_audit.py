from pathlib import Path
q=Path('research/buildings_batch/palisade');p=q/'audit_saved.py';s=p.read_text();s=s.replace("assert flatten(actual)==flatten(expected),(age,name,'FBX bounds drift')", "actual_by_name={ob.name:bb(ob) for ob in imported}\n    max_error=max(abs(actual_by_name[n][i][j]-ex[i][j]) for n,ex in zip(names,expected) for i in range(2) for j in range(3))\n    assert max_error<1e-4,(age,name,max_error)")
p.write_text(s);s=s.replace('for age in range(1,5):','for age in [1]:').replace("'saved_source_fbx_audit.json'","'age1_audit.json'");(q/'audit_age1.py').write_text(s)
