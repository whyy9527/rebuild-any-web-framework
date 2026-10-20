"""Explicit local entry point; never creates a public artifact or edits a test."""
import argparse
import json
import math
from pathlib import Path
import sys
import time

from capabilities.rebuild.contracts import coverage, freeze, load, local_file, verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['check', 'verify', 'freeze', 'coverage'])
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--spec', required=True)
    parser.add_argument('--targets', required=True)
    parser.add_argument('--target', choices=['reference', 'candidate'])
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--max-seconds', type=float, default=1800)
    parser.add_argument('--frozen')
    parser.add_argument('--receipt')
    parser.add_argument('--parent')
    parser.add_argument('--out')
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    def read(name):
        return json.loads(local_file(root, name).read_text()) if name else None
    try:
        output = None
        if args.out:
            output = root / args.out
            if Path(args.out).is_absolute() or '..' in Path(args.out).parts or not output.resolve().is_relative_to(root):
                raise ValueError('output must be relative to workspace')
            if output.exists():
                raise ValueError('output already exists; choose a new attempt path')
        contract = load(root, args.spec, args.targets)
        if args.operation == 'check':
            result = coverage(contract)
        elif args.operation == 'coverage':
            result = coverage(contract, read(args.receipt))
        elif args.operation == 'freeze':
            if not args.receipt or not args.out:
                raise ValueError('freeze requires --receipt and --out')
            result = freeze(contract, read(args.receipt), read(args.parent))
        else:
            if not args.target:
                raise ValueError('verify requires --target')
            if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
                raise ValueError('positive finite batch budget required')
            result = verify(root, contract, args.target, args.timeout, read(args.frozen), deadline=time.time()+args.max_seconds)
        if args.out:
            output.parent.mkdir(parents=True, exist_ok=True)
            # Do not overwrite a prior failed attempt or frozen batch.
            with output.open('x') as stream:
                stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps({'operation': args.operation, 'status': result.get('status'), 'out': args.out}))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('status', 'pass') == 'pass' else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error).replace(str(root), '<workspace>')}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
