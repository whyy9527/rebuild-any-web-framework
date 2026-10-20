"""Stage entry point for the current Codex; no additional model service."""
import argparse
import json
import sys
from capabilities.rebuild.pipeline import Pipeline


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('operation',choices=['start','step','status'])
    parser.add_argument('--workspace',required=True)
    parser.add_argument('--spec')
    parser.add_argument('--targets')
    parser.add_argument('--run')
    parser.add_argument('--audit')
    parser.add_argument('--timeout',type=float,default=30)
    parser.add_argument('--max-steps',type=int,default=50)
    parser.add_argument('--max-seconds',type=int,default=3600)
    parser.add_argument('--require-complete',action='store_true')
    args=parser.parse_args()
    try:
        pipeline=Pipeline(args.workspace)
        if args.operation=='start':
            if not args.spec or not args.targets: raise ValueError('explicit spec and targets required')
            result=pipeline.start(args.spec,args.targets,args.max_steps,args.max_seconds)
        elif args.operation=='step':
            if not args.run: raise ValueError('explicit run required')
            result=pipeline.step(args.run,args.audit,args.timeout)
        else:
            if not args.run: raise ValueError('explicit run required')
            result=pipeline.status(args.run)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if args.require_complete: return 0 if result['stage']=='complete' else 1
        return 1 if result.get('last_error') or result['stage']=='budget_exhausted' else 0
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(json.dumps({'status':'invalid','error':str(error)}),file=sys.stderr)
        return 2


if __name__=='__main__': sys.exit(main())
