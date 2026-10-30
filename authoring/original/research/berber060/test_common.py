import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import common


class AtomicWriteTests(unittest.TestCase):
    def test_transient_replace_denial_retries_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'receipt.json';common.write(target,{'old':1})
            original=Path.replace;calls=[]
            def replace(source,destination):
                calls.append(1)
                self.assertEqual(common.read(target),{'old':1})
                if len(calls)<3:raise PermissionError(5,'Access denied')
                return original(source,destination)
            with patch.object(Path,'replace',replace),patch.object(common.time,'sleep') as sleep:
                common.write(target,{'new':2})
            self.assertEqual(common.read(target),{'new':2});self.assertEqual(sleep.call_count,2)

    def test_exhausted_denial_retains_old_file_and_recoverable_tmp(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'receipt.json';common.write(target,{'old':1})
            with patch.object(Path,'replace',side_effect=PermissionError(5,'Access denied')) as replace,patch.object(common.time,'sleep'):
                with self.assertRaises(PermissionError):common.write(target,{'new':2})
            self.assertEqual(replace.call_count,8)
            self.assertEqual(common.read(target),{'old':1})
            self.assertEqual(common.read(target.with_suffix('.json.tmp')),{'new':2})

    def test_nonpermission_error_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Path,'replace',side_effect=OSError('other failure')) as replace,patch.object(common.time,'sleep') as sleep:
                with self.assertRaises(OSError):common.write(Path(directory)/'test.json',{})
            self.assertEqual(replace.call_count,1);sleep.assert_not_called()


if __name__=='__main__':unittest.main()
