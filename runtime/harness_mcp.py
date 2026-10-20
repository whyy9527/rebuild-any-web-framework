"""Small stdio MCP adapter; state and judgment stay outside transport."""
import argparse
import json
from pathlib import Path
import sys
from capabilities.exploration.harness import Harness
from capabilities.exploration.storage import digest

S={'type':'string','minLength':1}
TOOLS=[
    ('exploration_start','Start an explicitly requested bounded task. Freeze verifier argv and test files; Codex performs edits.',
     {'workspace':S,'session_id':S,'objective':S,'verifier':{'type':'array','items':S,'minItems':1},
      'max_iterations':{'type':'integer'},'max_failures':{'type':'integer'},'max_seconds':{'type':'number'},
      'acceptance_paths':{'type':'array','items':S,'minItems':1},'verify_seconds':{'type':'number'}},
     ['workspace','session_id','objective','verifier']),
    ('exploration_next','Reserve one attempt after reading feedback. Do the actual work with native Codex tools, then verify.',
     {'task_id':S,'hypothesis':S},['task_id','hypothesis']),
    ('exploration_verify','Execute the previously frozen local verifier with OS process permissions; cannot accept a claimed success.',
     {'task_id':S},['task_id']),
    ('exploration_status','Read task state and most recent measured feedback.',{'task_id':S},['task_id']),
    ('exploration_pause','Pause on user request or required external input.',{'task_id':S,'reason':S},['task_id','reason']),
    ('exploration_resume','Resume a paused task only when the user explicitly resumes it; never resets budgets.',{'task_id':S},['task_id']),
    ('exploration_adopt','Transfer a user-selected paused task to this explicit workspace/session; preserve budget and do not auto-resume.',
     {'task_id':S,'workspace':S,'session_id':S},['task_id','workspace','session_id'])]


def inventory():
    return [{'name':name,'description':description,'inputSchema':{'type':'object','properties':properties,
             'required':required,'additionalProperties':False},
             'annotations':{'readOnlyHint':name=='exploration_status','destructiveHint':name=='exploration_verify',
                            'openWorldHint':False}}
            for name,description,properties,required in TOOLS]


def summary(state):
    last=state['attempts'][-1] if state['attempts'] else None
    feedback=last['evaluation'] if last else None
    return {'task_id':state['id'],'objective':state['objective'],'phase':state['phase'],
            'iterations':state['iterations'],'remaining_iterations':max(0,state['max_iterations']-state['iterations']),
            'verifier':state['verifier'],'last_error':state['last_error'],
            'verify_seconds':state.get('verify_seconds',30),'acceptance_digest':digest(state['acceptance_files']),
            'feedback':({k:feedback[k] for k in ('status','exit_code','source_digest','integrity') if k in feedback}
                        | {'output':feedback.get('output','')[:4096]} if feedback else None)}


def invoke(harness,name,arguments):
    tool=next((t for t in inventory() if t['name']==name),None)
    if tool is None: raise ValueError('unknown tool')
    schema=tool['inputSchema']
    if not isinstance(arguments,dict) or set(arguments)-set(schema['properties']) or set(schema['required'])-set(arguments):
        raise ValueError('invalid tool argument fields')
    for key,value in arguments.items():
        kind=schema['properties'][key]['type']
        if ((kind=='string' and (not isinstance(value,str) or not value)) or
            (kind=='array' and not isinstance(value,list)) or
            (kind in ('integer','number') and (isinstance(value,bool) or not isinstance(value,int if kind=='integer' else (int,float))))):
            raise ValueError('invalid tool argument type')
    if name=='exploration_start': state=harness.start(**arguments)
    elif name=='exploration_next': state=harness.begin(arguments['task_id'],arguments['hypothesis'])
    elif name=='exploration_verify': state=harness.verify(arguments['task_id'])
    elif name=='exploration_pause': state=harness.pause(arguments['task_id'],arguments['reason'])
    elif name=='exploration_resume': state=harness.resume(arguments['task_id'])
    elif name=='exploration_adopt': state=harness.adopt(**arguments)
    else: state=harness.read(arguments['task_id'])
    return summary(state)


def serve(harness,source,sink):
    for line in source:
        identifier=None
        try:
            if len(line)>1048576: raise ValueError('request too large')
            request=json.loads(line)
            identifier=request.get('id')
            method=request['method']
            if method.startswith('notifications/'): continue
            if method=='initialize':
                version=request.get('params',{}).get('protocolVersion','2024-11-05')
                if version not in ('2024-11-05','2025-03-26','2025-06-18'): version='2024-11-05'
                result={'protocolVersion':version,'capabilities':{'tools':{}},'serverInfo':{'name':'exploration-lab','version':'0.4.0'}}
            elif method=='ping': result={}
            elif method=='tools/list': result={'tools':inventory()}
            elif method=='tools/call':
                try:
                    params=request['params']
                    value=invoke(harness,params['name'],params.get('arguments',{}))
                    result={'content':[{'type':'text','text':json.dumps(value)}],'structuredContent':value,'isError':False}
                except Exception as error:
                    result={'content':[{'type':'text','text':str(error)}],'isError':True}
            else:
                sink.write(json.dumps({'jsonrpc':'2.0','id':identifier,'error':{'code':-32601,'message':'method not found'}})+'\n')
                sink.flush()
                continue
            reply={'jsonrpc':'2.0','id':identifier,'result':result}
        except Exception:
            reply={'jsonrpc':'2.0','id':identifier,'error':{'code':-32600,'message':'invalid request'}}
        sink.write(json.dumps(reply)+'\n')
        sink.flush()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state-dir',default=str(Path.home()/'.codex/exploration-lab/state'))
    args=parser.parse_args()
    serve(Harness(args.state_dir),sys.stdin,sys.stdout)


if __name__=='__main__': main()
