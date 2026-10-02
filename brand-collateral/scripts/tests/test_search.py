import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'scripts/search.py'
CONFIG=json.loads((ROOT/'data/domains.json').read_text(encoding='utf-8'))

class SearchContracts(unittest.TestCase):
    def run_search(self,*args,cwd=None):
        return subprocess.run([sys.executable,'-X','utf8','-B',str(SCRIPT),*args],capture_output=True,text=True,encoding='utf-8',cwd=cwd)

    def test_all_datasets_have_search_and_output_columns_and_unique_ids(self):
        for domain,config in CONFIG.items():
            with self.subTest(domain=domain), (ROOT/'data'/config['file']).open(encoding='utf-8-sig',newline='') as handle:
                reader=csv.DictReader(handle);rows=list(reader)
                self.assertTrue(rows)
                self.assertTrue(set(config['search_cols']+config['output_cols']+['No'])<=set(reader.fieldnames))
                self.assertTrue(all(None not in row for row in rows),'CSV overflow columns')
                ids=[r['No'] for r in rows]
                self.assertTrue(all(ids));self.assertEqual(len(ids),len(set(ids)))

    def test_specific_canonical_item_is_retrievable(self):
        domain,query,field,expected=('style','wordmark','Style Name','Wordmark') if ROOT.name=='logo-design' else ('deliverable','business card','Deliverable','Business Card')
        result=self.run_search(query,'--domain',domain,'--json')
        self.assertEqual(result.returncode,0,result.stderr)
        rows=json.loads(result.stdout)['domains'][0]['results']
        self.assertTrue(rows);self.assertEqual(rows[0][field],expected)

    def test_empty_or_irrelevant_queries_return_no_matches(self):
        for query in ['', 'zzzznonexistentlookup']:
            result=self.run_search(query,'--json');self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(all(item['count']==0 for item in json.loads(result.stdout)['domains']))

    def test_unknown_domain_and_invalid_limits_fail(self):
        for args in [('test','--domain','unknown'),('test','-n','0'),('test','-n','-1'),('test','-n','21')]:
            self.assertEqual(self.run_search(*args).returncode,2)

    def test_all_domain_brief_is_bounded_and_preserves_user_brand(self):
        result=self.run_search('modern business','-n','1','--brand','用户原始品牌','--json')
        self.assertEqual(result.returncode,0,result.stderr);payload=json.loads(result.stdout)
        self.assertEqual(payload['brand'],'用户原始品牌');self.assertTrue(payload['guidance_only'])
        self.assertEqual({x['domain'] for x in payload['domains']},set(CONFIG))
        self.assertTrue(all(x['count']<=1 for x in payload['domains']))

    def test_any_working_directory_and_read_only_behavior(self):
        original={p.name:p.read_bytes() for p in (ROOT/'data').iterdir() if p.is_file()}
        with tempfile.TemporaryDirectory(prefix='codex-design-search-') as temp:
            result=self.run_search('minimal','--json',cwd=temp)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(list(Path(temp).iterdir()),[])
        self.assertEqual(original,{p.name:p.read_bytes() for p in (ROOT/'data').iterdir() if p.is_file()})

if __name__=='__main__':unittest.main()
