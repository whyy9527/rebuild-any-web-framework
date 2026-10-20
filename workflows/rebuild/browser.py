"""CLI for explicit browser observations; does not certify reconstruction."""
import argparse
import json
from pathlib import Path
import sys

from capabilities.rebuild.contracts import local_file
from runtime.browser import capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--scenario', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    try:
        scenario = json.loads(local_file(root, args.scenario).read_text())
        result = capture(root, scenario, args.out)
        print(json.dumps({'status': result['status'], 'steps': len(result['steps']),
                          'cleanup': result['cleanup'], 'out': args.out}, ensure_ascii=False))
        return 0 if result['status'] == 'captured' else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error).replace(str(root), '<workspace>')}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
