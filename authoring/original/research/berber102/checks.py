from pathlib import Path
import importlib.util,io,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent;OUT=ROOT/'output/berber_update_1_0_2'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def run():
 sys.path[:0]=[str(SOURCE),str(ROOT/'research/berber0110/tests')]
 handles=load('handles102',SOURCE/'test_handles.py')
 military=load('military102',ROOT/'research/berber0110/tests/test_military.py');military.ROOT=SOURCE/'scar'
 previous=load('fixes101_for102',ROOT/'research/berber101/test_fixes.py')
 military.FIXTURE+=handles.STRICT+previous.SQUAD_COST_FIXTURE
 fixes=load('fixes102',ROOT/'research/berber101/test_fixes.py')
 # Adapt retained101behavior tests to actual102 source paths without copying.
 class SourceLayout:
  def __truediv__(self,name):
   if str(name).startswith('ai'):return SOURCE/'scar'/name
   if name=='saharan_trader.scar':return SOURCE/'scar/units/saharan_trader.scar'
   return SOURCE/name
 fixes.ROOT=SourceLayout()
 # Cost test fixture needs typed lookup for callers reaching navigation.
 fixes.SQUAD_COST_FIXTURE+=handles.STRICT
 music=load('music102',ROOT/'research/berber101/music/test_music.py')
 class MusicLayout:
  def __truediv__(self,name):return SOURCE/name if str(name).startswith('fixtures') else SOURCE/'scar/music'/name
 music.ROOT=MusicLayout()
 # Endpoint fixture is an exact immutable copy from the package.
 suite=unittest.defaultTestLoader.discover(str(ROOT/'research/berber0110/tests'))
 for m in (military,handles,fixes,music):suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(m))
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 (OUT/'tests.log').write_text(stream.getvalue(),encoding='utf8')
 report={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'sources':{str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE/'scar').rglob('*.scar')},'native_match':'pending'}
 (OUT/'test-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 if not result.wasSuccessful():print(stream.getvalue()[-20000:]);raise AssertionError('102checksfailed')
 print('TESTS_PASSED',result.testsRun)
 return result.testsRun
if __name__=='__main__':run()
