"""Register currency tests write temporary fixtures only."""
import csv,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import review_script as rs
from common import write,read,sha

class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.art=Path(self.temp.name)
        self.plan={'jobs':[{'id':'j','family':'archer','voice_id':'current','age':'med','event':'attack','delivery':'high','take':1,
          'generation_text':'[angry] current synthesis','performance_override_reason':'controlled high delivery',
          'script':{'language':'Arabic','text':'current synthesis','english':'meaning','source':'authored reference','review_status':'pending'}}],
          'estimate':{'unique_recordings':1}}
        self.cast={'archer':{'voice_id':'current','name':'Actor','gender':'male','accent':'MSA'}}
        write(self.art/'recording-plan.json',self.plan);write(self.art/'casting.json',self.cast)
        self.patch=patch.object(rs,'ART',self.art);self.patch.start();self.addCleanup(self.patch.stop)
    def test_current_prompt_override_row_count_and_hash_proof(self):
        target=rs.export()
        with target.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['synthesis_prompt'],'[angry] current synthesis')
        self.assertEqual(rows[0]['performance_override_reason'],'controlled high delivery')
        proof=read(target.with_suffix('.manifest.json'))
        self.assertEqual(proof['rows'],1);self.assertEqual(proof['csv_sha256'],sha(target));self.assertEqual(proof['performance_override_rows'],1)
        rs.validate_export(proof,target)
        self.cast['archer']['voice_id']='changed';write(self.art/'casting.json',self.cast)
        with self.assertRaises(ValueError):rs.validate_export(proof,target)
    def test_cast_change_during_export_is_not_published(self):
        original=rs.csv.DictWriter.writerow
        def mutate(writer,row):
            result=original(writer,row)
            if row.get('job_id')=='j':
                self.cast['archer']['voice_id']='concurrent change';write(self.art/'casting.json',self.cast)
            return result
        with patch.object(rs.csv.DictWriter,'writerow',mutate):
            with self.assertRaisesRegex(ValueError,'changed during export'):rs.export()
        self.assertFalse((self.art/'voice-script.csv').exists())
    def test_stale_actor_is_rejected_before_csv_write(self):
        self.cast['archer']['voice_id']='superseded';write(self.art/'casting.json',self.cast)
        with self.assertRaises(ValueError):rs.export()
        self.assertFalse((self.art/'voice-script.csv').exists())
    def test_duplicate_ids_or_stale_expected_count_are_rejected(self):
        self.plan['jobs']*=2;write(self.art/'recording-plan.json',self.plan)
        with self.assertRaises(ValueError):rs.export()
        self.plan['jobs']=self.plan['jobs'][:1];self.plan['estimate']['unique_recordings']=2;write(self.art/'recording-plan.json',self.plan)
        with self.assertRaises(ValueError):rs.export()

    def test_documented_reason_fallback_and_explicit_performance_precedence(self):
        for performance,documented,pronunciation,expected in [
            ('','explicit documented text revision','older pronunciation note','explicit documented text revision'),
            ('','','legacy pronunciation revision','legacy pronunciation revision'),
            ('controlled performance','documented text revision','older pronunciation note','controlled performance')]:
            with self.subTest(expected=expected):
                job=self.plan['jobs'][0]
                job.update(performance_override_reason=performance,documented_override_reason=documented,
                    pronunciation_revision=pronunciation)
                write(self.art/'recording-plan.json',self.plan)
                target=rs.export()
                with target.open(encoding='utf-8-sig',newline='') as stream:row=next(csv.DictReader(stream))
                self.assertEqual(row['performance_override_reason'],expected)
                proof=read(target.with_suffix('.manifest.json'))
                self.assertEqual(proof['documented_override_rows'],1)
                self.assertEqual(proof['performance_override_rows'],int(bool(performance)))

if __name__=='__main__':unittest.main()
