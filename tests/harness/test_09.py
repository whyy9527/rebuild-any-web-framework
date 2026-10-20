from pathlib import Path
import tempfile
import unittest
import json
from runtime.codex_host import CodexHost
from workflows.harness.install import install

class NativeCodexDiscovery(unittest.TestCase):
    def test_real_host_discovers_manual_tools_without_legacy_hooks(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace=Path(folder)/'project'
            workspace.mkdir()
            home=Path(folder)/'home'
            home.mkdir()
            (home/'config.toml').write_text('[projects.'+json.dumps(str(workspace))+']\ntrust_level = \"trusted\"\n')
            install(workspace,Path.cwd())
            with CodexHost(codex_home=home) as host:
                hooks=host.request('hooks/list',{'cwds':[str(workspace)]})
                self.assertIn('data',hooks)
                own=[h for entry in hooks['data'] for h in entry['hooks'] if h.get('statusMessage')=='Exploration Lab']
                self.assertEqual(own,[])
                thread=host.request('thread/start',{'cwd':str(workspace),'ephemeral':True})['thread']['id']
                status=host.request('mcpServerStatus/list',{'threadId':thread})
                server=next(s for s in status['data'] if s['name']=='exploration-lab')
                self.assertIn('exploration_verify',server['tools'])
                outside=Path(folder)/'outside'
                outside.mkdir()
                other=host.request('thread/start',{'cwd':str(outside),'ephemeral':True})['thread']['id']
                servers=host.request('mcpServerStatus/list',{'threadId':other})['data']
                self.assertNotIn('exploration-lab',[server['name'] for server in servers])
