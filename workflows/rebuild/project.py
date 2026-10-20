"""Read one rebuild project; prepare a native Goal or call its existing commands.

No task state, hooks, model process or implicit Goal creation lives here.
All project paths are relative to the explicitly selected workspace.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from string import Template
import subprocess
import sys

from capabilities.exploration.storage import digest
from capabilities.rebuild.contracts import local_file, require_text
from capabilities.rebuild.discovery import frontier
from runtime.dream import Commands, load_pool


def load_project(workspace, name):
    root = Path(workspace).resolve()
    project = json.loads(local_file(root, name).read_text())
    if not isinstance(project, dict):
        raise ValueError('project must be a JSON object')
    if type(project.get('schema_version')) is not int or project['schema_version'] != 1:
        raise ValueError('project schema_version 1 required')
    for field in ('name', 'source', 'target', 'objective'):
        require_text(project.get(field), 'project.' + field)
    completion = project.get('completion')
    if not isinstance(completion, list) or not completion:
        raise ValueError('project completion criteria required')
    for item in completion:
        require_text(item, 'completion criterion')
    inputs = project.get('inputs', {})
    if not isinstance(inputs, dict):
        raise ValueError('project.inputs must map names to existing workspace files')
    for path in inputs.values():
        local_file(root, path)
    commands = project.get('commands', {})
    if not isinstance(commands, dict):
        raise ValueError('project.commands must map names to argv lists')
    for key, argv in commands.items():
        require_text(key, 'command name')
        if not isinstance(argv, list) or not argv:
            raise ValueError('project command must be a nonempty argv list')
        for argument in argv:
            require_text(argument, 'command argument')
    return root, project


def goal_payload(project, name, workspace):
    workflow = Path(__file__).resolve().with_name('WORKFLOW.md')
    template = workflow.with_name('GOAL.template.md').read_text()
    values = {key: project[key] for key in ('name', 'source', 'target', 'objective')}
    method = method_report(workspace, project)
    method_text = '\n'.join(f"- {row['code']}：{row['action']}" for row in method['gaps'])
    values.update(workspace=str(workspace), project=str(workspace / name),
                  method=method_text or '入口已连接；仍需检查本轮真实执行与完整用户目标覆盖。',
                  workflow=str(workflow), research=str(workflow.parents[2] / 'docs/RESEARCH.md'),
                  completion='\n'.join(
        f'{index}. {text}' for index, text in enumerate(project['completion'], 1)))
    # Values are substituted once, so dollar signs in user content remain literal.
    return {'objective': Template(template).substitute(values).strip()}


def method_report(root, project):
    """Read method wiring and immutable RSI receipts; never run or repair them.

    Connected methods are prerequisites, not an acceptance verdict. In
    particular a historical frontend pass cannot satisfy any missing RSI link.
    """
    inputs, commands = project.get('inputs', {}), project.get('commands', {})
    gaps = []
    def missing(code, action):
        gaps.append({'code': code, 'action': action})
    if 'rsi_config' not in inputs:
        missing('rsi.config', '准备可恢复原版状态及固定发现／独立评价协议，在 inputs.rsi_config 连接真实配置。')
    for key in ('rsi_collect', 'rsi_replay'):
        if key not in commands:
            missing('rsi.command.' + key, '在 commands.' + key + ' 连接 RSI 的显式工作调用。')
    rsi = None
    if 'rsi_config' in inputs:
        config = json.loads(local_file(root, inputs['rsi_config']).read_text())
        rsi = Commands(root, config)
    pool = worlds = None
    if 'rsi_pool' not in inputs:
        missing('rsi.pool', '实际执行 collect，保存真实历史树及不可覆写的池，在 inputs.rsi_pool 引用。')
    else:
        pool, worlds, _ = load_pool(root, inputs['rsi_pool'], rsi.protocol if rsi else None)
    if 'rsi_evaluation' not in inputs:
        missing('rsi.replay', '在完整冻结池上比较原策略和修订策略，inputs.rsi_evaluation 引用真实 evaluation.json。')
    elif pool is not None:
        receipt = json.loads(local_file(root, inputs['rsi_evaluation']).read_text())
        selected = receipt['selected_version']
        versions = receipt['feedback']
        hashes = receipt['candidate_sha256']
        if (type(selected) is not int or not isinstance(versions, list)
                or not isinstance(hashes, list) or len(hashes) != len(versions)
                or not 0 <= selected < len(versions)
                or not all(isinstance(value, str) for value in hashes)
                or not all(isinstance(row, dict) and isinstance(row.get('worlds', []), list)
                           and all(isinstance(world, dict) for world in row.get('worlds', []))
                           for row in versions)):
            raise ValueError('invalid RSI evaluation versions or selected_version')
        feedback = versions[selected]
        evaluated = feedback.get('worlds', [])
        count = len(evaluated)
        frozen = worlds[:count]
        if (feedback.get('status') != 'evaluated' or not count
                or receipt.get('pool_digest') != digest(frozen)
                or [w.get('world_digest') for w in evaluated] != [digest(w) for w in frozen]
                or hashes[selected] != receipt.get('policy_sha256')
                or receipt.get('policy_sha256') != pool['policy']['sha256']):
            missing('rsi.replay.mismatch', '回放回执未对应当前池的完整历史前缀及选中策略；核对真实回执，不手填通过。')
        elif (len({hashes[i] for i, row in enumerate(versions)
                   if row.get('status') == 'evaluated'}) < 2
                or any([w.get('world_digest') for w in row.get('worlds', [])]
                       != [digest(w) for w in frozen]
                       for row in versions if row.get('status') == 'evaluated')):
            missing('rsi.comparison', '至少用原策略及一个不同的可执行修订在同一完整冻结池回放；保留无效候选反馈。')
        elif (len(worlds) <= count or worlds[-1].get('policy_sha256') != pool['policy']['sha256']
                or len(worlds[-1]['nodes']) <= 1):
            missing('rsi.deployment', '使用选中池 collect --pool，实际执行新探针并保留策略哈希匹配的新世界。')
    if not any(key in inputs for key in ('fixture', 'frontend_scenarios')):
        missing('e2e.scenarios', '连接两端共享的场景／共同夹具；场景范围由完整用户目标决定。')
    if 'frontend_contract' not in inputs:
        missing('e2e.frontend', '连接有原版来源的共同前端契约，与业务场景一起验收。')
    if 'replay' not in commands:
        missing('e2e.driver', '连接实际两端 UI 回放驱动 commands.replay；驱动采集事实，不自报通过。')
    if not any(key in commands for key in ('compare', 'compare_frontend')):
        missing('e2e.compare', '连接共同断言比较命令；构建或单元测试不能替代 E2E。')
    return {'status': 'gaps' if gaps else 'connected', 'gaps': gaps,
            'completion': 'not evaluated; method wiring and RSI receipts do not prove full product acceptance'}


def project_status(root, project):
    inputs = project.get('inputs', {})
    read = lambda key: json.loads(local_file(root, inputs[key]).read_text())
    result = {'name': project['name'], 'commands': sorted(project.get('commands', {})),
              'method': method_report(root, project),
              'completion': 'not evaluated; this is an evidence index, not a Goal verifier'}
    contract = None
    if 'frontend_contract' in inputs:
        contract = read('frontend_contract')
        result['mold'] = {'path': inputs['frontend_contract'],
                          'requirements': len(contract['requirements']),
                          'by_kind': dict(Counter(row['kind'] for row in contract['requirements']))}
    if 'exploration_history' in inputs:
        history = read('exploration_history')
        pending = frontier(root, history)
        result['exploration'] = {'states': len(history['states']),
                                 'transitions': len(history['transitions']),
                                 'pending_probes': len(pending['pending']),
                                 'completion': pending['completion']}
    if 'rsi_pool' in inputs:
        pool, worlds, _ = load_pool(root, inputs['rsi_pool'])
        result['rsi'] = {'worlds': len(worlds), 'nodes': [len(w['nodes']) for w in worlds],
                         'policy': pool['policy'], 'protocol': pool['protocol'],
                         'completion': 'not evaluated; replay score is not product acceptance'}
    if 'historical_frontend_result' in inputs:
        receipt = read('historical_frontend_result')
        result['historical_frontend'] = {
            'path': inputs['historical_frontend_result'], 'status': receipt['status'],
            'counts': dict(Counter(row['status'] for row in receipt['rows'])),
            'contract_matches': contract is not None and receipt.get('contract_digest') == digest(contract),
            'freshness': 'historical only; current source and binary have not been verified by this command'}
    return result


def command_argv(root, project, command, *, out=None, observed=None):
    if command not in project.get('commands', {}):
        raise ValueError('unknown project command: ' + command)
    values = {}
    if out is not None:
        target = local_file(root, out, must_exist=False)
        if target.exists():
            raise ValueError('choose a fresh output path; existing evidence is preserved')
        values['out'] = out
    if observed is not None:
        local_file(root, observed)
        values['observed'] = observed
    def substitute(match):
        key = match.group(1)
        if key not in values:
            raise ValueError('command requires --' + key)
        return values[key]
    return [re.sub(r'\{(out|observed)\}', substitute, argument)
            for argument in project['commands'][command]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('goal', 'status', 'preflight', 'run'))
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--command')
    parser.add_argument('--out')
    parser.add_argument('--observed')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        root, project = load_project(args.workspace, args.project)
        if args.operation == 'goal':
            result = goal_payload(project, args.project, root)
        elif args.operation == 'status':
            result = project_status(root, project)
        elif args.operation == 'preflight':
            result = method_report(root, project)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result['gaps'] else 0
        else:
            if not args.command:
                raise ValueError('run requires --command')
            argv = command_argv(root, project, args.command, out=args.out, observed=args.observed)
            if not args.dry_run:
                # Trusted local argv; preserve the actual command's exit code.
                return subprocess.run(argv, cwd=root).returncode
            result = {'argv': argv, 'executed': False}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
