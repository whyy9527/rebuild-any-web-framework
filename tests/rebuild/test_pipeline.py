import json
import subprocess
import sys
from pathlib import Path
import unittest

from capabilities.exploration.storage import digest
from capabilities.rebuild.pipeline import CATEGORIES, Pipeline
from tests.rebuild import test_contracts as fixture_module

APP=fixture_module.APP


class EvidenceGatedPipeline(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture_module.SharedBusinessContracts('test_shared_assertions_detect_candidate_bug_and_accept_real_repair')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root
        self.pipeline=Pipeline(self.root)
        self.run=self.pipeline.start('spec.json','targets.json')

    def step(self, expected, **arguments):
        result=self.pipeline.step(self.run['id'],**arguments)
        self.assertEqual(result['stage'],expected,result)
        return result

    def reach_discovery(self):
        for stage in ['specify','reference','freeze','implement']:
            self.step(stage)
        failed=self.step('implement')
        self.assertIn('candidate verification failed',failed['last_error'])
        self.assertEqual(json.loads((self.root/failed['candidate_receipt']).read_text())['status'],'fail')
        (self.root/'candidate.py').write_text(APP)
        return self.step('discover')

    def discover(self, state):
        batch=json.loads((self.root/state['batch']).read_text())
        self.fixture.spec['revision']='v2'
        self.fixture.spec['parent_digest']=digest(batch)
        self.fixture.spec['behaviors'][1]={
            'id':'exit','description':'Explicit state-machine fixture restart preserves completion',
            'discovery':'observed','evidence':['observation.md'],'precondition':{},
            'steps':[{'action':{'type':'complete'},'expect':{'completed':True}},
                     {'action':{'type':'restart'},'expect':{'completed':True}}]}
        self.fixture.write()
        (self.root/'artifacts/audit.json').write_text(json.dumps({
            'parent_batch_digest':digest(batch), 'checks':{key:'observation.md' for key in CATEGORIES}}))
        return self.step('reference',audit_path='artifacts/audit.json')

    def test_real_commands_fail_repair_discover_reconfirm_and_complete_then_reject_stale_source(self):
        def gate():
            return subprocess.run([sys.executable,'-m','workflows.rebuild.pipeline','status','--workspace',str(self.root),
                                   '--run',self.run['id'],'--require-complete'],capture_output=True,text=True,timeout=5)
        self.assertEqual(gate().returncode,1)
        state=self.reach_discovery()
        self.assertEqual(self.step('discover')['last_error'],'independent discovery audit is required')
        self.discover(state)
        for stage in ['freeze','implement','review','complete']:
            self.step(stage)
        reopened=Pipeline(self.root)
        status=reopened.status(self.run['id'])
        self.assertEqual(status['coverage']['known_total'],2)
        self.assertEqual(status['coverage']['unknown_total'],0)
        self.assertEqual(status['discovered_ids'],['exit'])
        self.assertEqual(gate().returncode,0)
        (self.root/'candidate.py').write_text(APP+'\n# A subsequent implementation change invalidates historical success.\n')
        with self.assertRaisesRegex(ValueError,'stale artifact'):
            reopened.status(self.run['id'])

    def test_budget_is_not_reset_by_reopening_pipeline(self):
        limited=self.pipeline.start('spec.json','targets.json',max_steps=1)
        self.pipeline.step(limited['id'])
        reopened=Pipeline(self.root)
        exhausted=reopened.step(limited['id'])
        self.assertEqual(exhausted['stage'],'budget_exhausted')
        self.assertEqual(exhausted['steps'],1)
        self.assertEqual(exhausted['deadline'],limited['deadline'])

    def test_decisions_alone_cannot_claim_reference_exploration(self):
        self.fixture.spec['behaviors'][0]['discovery']='decision'
        self.fixture.spec['behaviors'][0]['rationale']='A planned behavior without original observation'
        self.fixture.write()
        result=self.step('explore')
        self.assertIn('actual reference evidence',result['last_error'])

    def test_specification_revision_returns_to_exploration_without_resetting_budget(self):
        before=self.step('specify')
        self.fixture.spec['revision']='v1-corrected'
        self.fixture.write()
        revised=self.step('explore')
        self.assertEqual(revised['deadline'],before['deadline'])
        self.assertEqual(revised['steps'],before['steps']+1)
        self.step('specify')
        self.step('reference')
