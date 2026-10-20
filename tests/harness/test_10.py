from pathlib import Path
import tempfile
import unittest
import json
from runtime.codex_host import CodexHost
from workflows.harness.install import install

class NativeVerificationLoop(unittest.TestCase):
    def test_native_tool_verification_rejects_empty_test_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            workspace=root/'project'
            workspace.mkdir()
            (workspace/'tests').mkdir()
            home=root/'codex'
            home.mkdir()
            (home/'config.toml').write_text('[projects.'+json.dumps(str(workspace))+']\ntrust_level = \"trusted\"\n')
            install(workspace,Path.cwd())
            with CodexHost(codex_home=home) as host:
                thread=host.request('thread/start',{'cwd':str(workspace),'ephemeral':True})['thread']['id']
                host.request('mcpServerStatus/list',{'threadId':thread})
                def call(tool,arguments):
                    reply=host.request('mcpServer/tool/call',{'threadId':thread,'server':'exploration-lab','tool':tool,'arguments':arguments})
                    self.assertFalse(reply.get('isError',False),reply)
                    return reply['structuredContent']
                task=call('exploration_start',{'workspace':str(workspace),'session_id':thread,'objective':'verify real tests','verifier':['python3','-m','unittest','discover','-s','tests'],
                                             'acceptance_paths':['tests'],'verify_seconds':90})
                self.assertEqual(task['verify_seconds'],90)
                self.assertEqual(len(task['acceptance_digest']),64)
                call('exploration_next',{'task_id':task['task_id'],'hypothesis':'run acceptance'})
                result=call('exploration_verify',{'task_id':task['task_id']})
                self.assertEqual(result['phase'],'blocked')
                self.assertEqual(result['feedback']['status'],'invalid')
