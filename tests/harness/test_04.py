import json
import subprocess
import sys
import tempfile
import unittest

class McpProtocol(unittest.TestCase):
    def test_stdio_discovery_and_error_are_real_protocol_messages(self):
        with tempfile.TemporaryDirectory() as folder:
            messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}},
                      {'jsonrpc':'2.0','method':'notifications/initialized'},
                      {'jsonrpc':'2.0','id':2,'method':'tools/list'},
                      {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'exploration_verify','arguments':{'task_id':'bad'}}}]
            result=subprocess.run([sys.executable,'-m','runtime.harness_mcp','--state-dir',folder],input='\n'.join(json.dumps(m) for m in messages)+'\n',text=True,capture_output=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            replies=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(replies[0]['result']['protocolVersion'],'2024-11-05')
            self.assertIn('exploration_start',[tool['name'] for tool in replies[1]['result']['tools']])
            self.assertTrue(replies[2]['result']['isError'])
