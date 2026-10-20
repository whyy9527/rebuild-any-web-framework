import json
from pathlib import Path
import shlex
import tempfile
import tomllib
import unittest
from workflows.harness.install import install


class PreserveConfiguration(unittest.TestCase):
    def test_migration_removes_owned_hooks_and_preserves_other_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            local=root/'.codex'
            local.mkdir()
            retired=local/'exploration-lab/hook.sh'
            retired.parent.mkdir()
            retired.write_text('# old hook')
            other={'type':'command','command':'echo existing'}
            existing={'hooks':{event:[{'hooks':[other,{'type':'command','command':shlex.quote(str(retired))}]}]
                               for event in ('SessionStart','Stop','UserPromptSubmit')}}
            (local/'hooks.json').write_text(json.dumps(existing))
            original='[features]\nhooks=false\n[mcp_servers.other]\ncommand="other"\n'
            (local/'config.toml').write_text(original)
            result=install(root,Path.cwd())
            hooks=json.loads((local/'hooks.json').read_text())
            self.assertEqual(hooks,{'hooks':{event:[{'hooks':[other]}] for event in existing['hooks']}})
            self.assertFalse(retired.exists())
            config=tomllib.loads((local/'config.toml').read_text())
            self.assertFalse(config['features']['hooks'])
            self.assertEqual(config['mcp_servers']['other']['command'],'other')
            self.assertIn('exploration-lab',config['mcp_servers'])
            self.assertTrue(result['retired_hooks_removed'])
            before=(local/'hooks.json').read_bytes()
            self.assertFalse(install(root,Path.cwd())['retired_hooks_removed'])
            self.assertEqual((local/'hooks.json').read_bytes(),before)

    def test_new_install_does_not_create_hooks_or_enable_hook_feature(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            result=install(root,Path.cwd())
            self.assertEqual(result['events'],[])
            self.assertFalse((root/'.codex/hooks.json').exists())
            config=tomllib.loads((root/'.codex/config.toml').read_text())
            self.assertNotIn('features',config)
