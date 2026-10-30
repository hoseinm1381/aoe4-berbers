"""Release regression: all22 resources must have finite UV0 after repair."""
import unittest
from pathlib import Path
from repair import OUT, read, write, groups, restore_uv, rc

class ReleaseUVs(unittest.TestCase):
    def test_all_22_have_finite_uvs(self):
        rows = read(OUT/'input-audit.json')['models']
        self.assertEqual(len(rows),22)
        for row in rows:
            with self.subTest(member=row['member']):
                root = OUT/'work/repaired' if (OUT/'work/repaired').exists() else OUT/'work/baseline'
                _, meshes = groups((root/row['member']).read_bytes())
                self.assertEqual(sum(len(x['bad']) for x in meshes),0)

    def test_topology_mismatch_is_rejected(self):
        row=read(OUT/'input-audit.json')['models'][-1]
        original=(OUT/'work/baseline'/row['member']).read_bytes()
        donor=Path(row['donor']).read_bytes();doc,meshes=groups(donor)
        index=meshes[0]['index'];payload=bytearray(index.payload);payload[-1]^=1
        broken=rc.rebuild(doc,lambda c:bytes(payload) if c.offset==index.offset else None)
        with self.assertRaisesRegex(AssertionError,'topology|Nonvertex'):
            restore_uv(original,broken)

    def test_nonfinite_donor_is_rejected(self):
        row=read(OUT/'input-audit.json')['models'][-1]
        original=(OUT/'work/baseline'/row['member']).read_bytes()
        donor=Path(row['donor']).read_bytes();doc,meshes=groups(donor)
        vertex=meshes[0]['chunk'];payload=bytearray(vertex.payload);payload[28:30]=b'\x00\x7e'
        broken=rc.rebuild(doc,lambda c:bytes(payload) if c.offset==vertex.offset else None)
        with self.assertRaisesRegex(AssertionError,'non-finite'):
            restore_uv(original,broken)

if __name__ == '__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseUVs))
    rows=read(OUT/'input-audit.json')['models']
    write(OUT/'test-validation.json',{'status':'passed' if result.wasSuccessful() else 'failed',
      'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
      'baseline_regression_failures_reproduced':len([r for r in rows if r['observed_invalid_uv_vertices']]),
      'baseline_nonfinite_uv_vertices':sum(r['observed_invalid_uv_vertices'] for r in rows),
      'cases':['all22finiteUVs','mismatchedTopologyRejected','nonfiniteDonorRejected']})
    raise SystemExit(0 if result.wasSuccessful() else 1)
