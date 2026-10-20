"""Register reviewed local launchers without replacing unrelated Codex configuration."""
import argparse
import json
from pathlib import Path
import shlex
import sys
import time
import tomllib
from capabilities.exploration.storage import save

NAME='exploration-lab'


def install(workspace,repo_root):
    workspace,repo=Path(workspace).resolve(),Path(repo_root).resolve()
    if not workspace.is_dir(): raise ValueError("existing target project required")
    home=workspace/".codex"
    if not (repo/'runtime/harness_mcp.py').is_file(): raise ValueError('validated harness repository required')
    home.mkdir(parents=True,exist_ok=True)
    package=home/NAME
    package.mkdir(exist_ok=True)
    config_path=home/'config.toml'
    config=tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    launcher=package/'mcp.sh'
    old=config.get('mcp_servers',{}).get(NAME)
    if old and (old.get('command')!=str(launcher) or old.get('args',[])!=[]):
        raise ValueError('existing MCP name has another owner')
    hook_path=home/'hooks.json'
    hooks=json.loads(hook_path.read_text()) if hook_path.exists() else {'hooks':{}}
    if not isinstance(hooks.get('hooks'),dict): raise ValueError('invalid existing hooks configuration')
    backup=package/'backups'/str(time.time_ns())
    backup.mkdir(parents=True)
    for path in (config_path,hook_path):
        if path.exists():
            target=backup/path.name
            target.write_bytes(path.read_bytes())
            target.chmod(0o600)
    state=package/'state'
    content='#!/bin/sh\ncd '+shlex.quote(str(repo))+' || exit 1\nexec '+shlex.quote(sys.executable)+' -m runtime.harness_mcp --state-dir '+shlex.quote(str(state))+'\n'
    launcher.write_text(content)
    launcher.chmod(0o700)
    # Remove only commands belonging to this project's retired launcher.
    retired=package/'hook.sh'
    command=shlex.quote(str(retired))
    changed=False
    for event,entries in hooks['hooks'].items():
        kept=[]
        for entry in entries:
            children=entry.get('hooks',[])
            remaining=[h for h in children if h.get('command') not in (command,str(retired))]
            if len(remaining)!=len(children):
                changed=True
                if remaining: kept.append({**entry,'hooks':remaining})
            else: kept.append(entry)
        hooks['hooks'][event]=kept
    if changed: save(hook_path,hooks)
    if retired.exists(): retired.unlink()
    # Native CLI rewriting can normalize unrelated server definitions. Append only
    # this owned TOML table, preserving every existing byte and semantic value.
    original=config_path.read_text() if config_path.exists() else ''
    updated=original
    if old is None:
        updated+='\n[mcp_servers.exploration-lab]\ncommand = '+json.dumps(str(launcher))+'\nargs = []\n'
    tomllib.loads(updated)
    temporary=config_path.with_suffix('.exploration.tmp')
    temporary.write_text(updated)
    temporary.chmod(config_path.stat().st_mode & 0o777 if config_path.exists() else 0o600)
    temporary.replace(config_path)
    after=tomllib.loads(config_path.read_text())
    for key,value in config.items():
        if key=='mcp_servers':
            for server,settings in value.items():
                if server!=NAME and after['mcp_servers'].get(server)!=settings: raise ValueError('unrelated MCP settings changed')
        elif key=='features':
            for feature,setting in value.items():
                if after['features'].get(feature)!=setting: raise ValueError('unrelated feature changed')
        elif after.get(key)!=value: raise ValueError('unrelated Codex configuration changed')
    return {'mcp_server':NAME,'registered':True,'scope':'project','events':[],
            'retired_hooks_removed':changed,'state_directory':str(state),'backup_directory':str(backup)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace',required=True)
    parser.add_argument('--repo',default=str(Path.cwd()))
    parser.add_argument('--out')
    args=parser.parse_args()
    result=install(args.workspace,args.repo)
    if args.out: Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('directory')}))


if __name__=='__main__': main()
