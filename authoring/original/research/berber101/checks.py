"""Run reported regressions and the existing AI suite against the patched source."""
from pathlib import Path
import importlib.util,io,json,sys,unittest,hashlib
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
OUT=ROOT/'output/berber_update_1_0_1'

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def run():
 sys.path.insert(0,str(SOURCE));sys.path.insert(0,str(ROOT/'research/berber0110/tests'))
 fixes=load('fixes101',SOURCE/'test_fixes.py')
 music=load('music101',SOURCE/'music/test_music.py')
 # Existing military tests use the new military module and strict squad costs.
 military=load('military101',ROOT/'research/berber0110/tests/test_military.py')
 military.ROOT=SOURCE;military.FIXTURE+=fixes.SQUAD_COST_FIXTURE
 suite=unittest.defaultTestLoader.discover(str(ROOT/'research/berber0110/tests'))
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(military))
 for m in (fixes,music):suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(m))
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 OUT.mkdir(exist_ok=True);(OUT/'tests.log').write_text(stream.getvalue(),encoding='utf8')
 report={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.rglob('*.scar')},'native_runtime':'fresh-match acceptance pending'}
 (OUT/'test-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 if not result.wasSuccessful():print(stream.getvalue()[-18000:]);raise AssertionError('Tests failed')
 print('TESTS_PASSED',result.testsRun)
 return result.testsRun

if __name__=='__main__':run()
