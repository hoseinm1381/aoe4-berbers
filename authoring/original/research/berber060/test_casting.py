import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import jobs
from common import write


class FixedCharacters(unittest.TestCase):
    def test_replacing_archer_cannot_reassign_other_recorded_families(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);art=root/'art';out=root/'out'
            voices=[{'voice_id':vid,'name':vid,'category':'professional','gender':'male','rate':1,'accent':accent}
                for vid,accent in [('A','modern standard'),('DWzI1mgotR4xUap1D5w3','tunisian'),('Znew','modern standard')]]
            write(out/'account/shared-arabic.json',{'voices':voices})
            write(out/'account/arabic-voices.json',{'voices':[]})
            write(art/'casting-lock.json',{'villager':'A','archer':'DWzI1mgotR4xUap1D5w3'})
            write(art/'casting-overrides.json',{'archer':{'voice_id':'Znew','reason':'Independent pronunciation pilot'}})
            with patch.object(jobs,'ART',art),patch.object(jobs,'OUT',out),patch.object(jobs,'PERSONAS',{'villager':{'gender':'male'},'archer':{'gender':'male'}}):
                result=jobs.casting()
            self.assertEqual(result['villager']['voice_id'],'A')
            self.assertEqual(result['archer']['voice_id'],'Znew')
            self.assertEqual(len({r['voice_id'] for r in result.values()}),2)


if __name__=='__main__':unittest.main()
