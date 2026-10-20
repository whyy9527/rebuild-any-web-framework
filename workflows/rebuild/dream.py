"""Run Dream-RSI online/dream/redeploy work units through the project workflow."""
import argparse
import json
from pathlib import Path
import sys

from capabilities.rebuild.contracts import local_file
from runtime.dream import cycle, load_pool, read, replay_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('collect', 'replay', 'cycle', 'dream', 'inspect'))
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--config')
    parser.add_argument('--pool')
    parser.add_argument('--out')
    parser.add_argument('--iterations', type=int, default=1)
    parser.add_argument('--candidate', action='append', default=[])
    args = parser.parse_args()
    try:
        root = Path(args.workspace).resolve()
        if args.operation == 'inspect':
            if not args.pool:
                raise ValueError('inspect requires --pool')
            pool, worlds, _ = load_pool(root, args.pool)
            result = {'worlds': len(worlds), 'nodes': [len(w['nodes']) for w in worlds],
                      'protocol': pool['protocol'], 'policy': pool['policy'],
                      'completion': 'not evaluated; a replay score is not app acceptance'}
        else:
            if not args.config or not args.out:
                raise ValueError(args.operation + ' requires --config and a fresh --out')
            config = read(local_file(root, args.config))
            if args.operation == 'replay':
                if not args.pool:
                    raise ValueError('replay requires --pool')
                result = replay_candidates(root, config, args.pool, args.candidate, args.out)
            else:
                result = cycle(root, config, args.out, iterations=args.iterations,
                               pool=args.pool, offline=args.operation == 'dream',
                               collect_only=args.operation == 'collect')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
