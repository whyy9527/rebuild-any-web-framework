"""Inspect actual native host inventory; never infer automatic continuation from registration."""
import argparse
import json
from pathlib import Path
from runtime.codex_host import CodexHost


def diagnose(workspace):
    with CodexHost() as host:
        inventory=host.request('hooks/list',{'cwds':[str(Path(workspace).resolve())]})
        own=[{k:h[k] for k in ('eventName','trustStatus','enabled','currentHash')}
             for entry in inventory['data'] for h in entry['hooks'] if h.get('statusMessage')=='Exploration Lab']
        thread=host.request('thread/start',{'cwd':str(Path(workspace).resolve()),'ephemeral':True})['thread']['id']
        servers=host.request('mcpServerStatus/list',{'threadId':thread})['data']
        server=next((s for s in servers if s['name']=='exploration-lab'),None)
        return {'mcp_registered':server is not None,'tools':sorted(server['tools']) if server else [],
                'native_hooks':own,'hook_errors':sum(len(e['errors']) for e in inventory['data']),
                'retired_hooks_present':bool(own),
                'automatic_stop_continuation':'removed','model_calls':0}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=diagnose(args.workspace)
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__': main()
