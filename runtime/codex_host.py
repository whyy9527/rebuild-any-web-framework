"""Bounded native app-server client for integration probes, not a model emulator."""
import json
import os
import queue
import signal
import subprocess
import threading
import time


class CodexHost:
    def __init__(self,*,codex_home=None,timeout=20):
        environment=os.environ.copy()
        if codex_home is not None: environment['CODEX_HOME']=str(codex_home)
        self.process=subprocess.Popen(['codex','app-server','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,text=True,env=environment,start_new_session=True)
        self.messages=queue.Queue()
        self.notifications=[]
        self.diagnostics=[]
        self.counter=0
        self.timeout=timeout
        def reader():
            for line in self.process.stdout:
                try: self.messages.put(json.loads(line))
                except ValueError: pass
        def diagnostics():
            for line in self.process.stderr:
                if len(self.diagnostics)<100: self.diagnostics.append(line)
        threading.Thread(target=reader,daemon=True).start()
        threading.Thread(target=diagnostics,daemon=True).start()
        try:
            self.initialize=self.request('initialize',{'clientInfo':{'name':'exploration-lab-probe','version':'0.4.0'},
                                                       'capabilities':{'experimentalApi':True}})
            self.send({'method':'initialized','params':{}})
        except BaseException:
            self.close()
            raise

    def send(self,message):
        self.process.stdin.write(json.dumps(message)+'\n')
        self.process.stdin.flush()

    def request(self,method,params):
        self.counter+=1
        identifier=self.counter
        self.send({'id':identifier,'method':method,'params':params})
        deadline=time.monotonic()+self.timeout
        while time.monotonic()<deadline:
            try: message=self.messages.get(timeout=max(.01,deadline-time.monotonic()))
            except queue.Empty: break
            if message.get('id')==identifier and ('result' in message or 'error' in message):
                if 'error' in message: raise RuntimeError(json.dumps(message['error']))
                return message['result']
            if 'id' in message and 'method' in message:
                self.send({'id':message['id'],'error':{'code':-32601,'message':'probe cannot authorize unexpected server requests'}})
            else: self.notifications.append(message)
        raise TimeoutError('native app-server request deadline: '+method)

    def close(self):
        if self.process.poll() is None:
            os.killpg(self.process.pid,signal.SIGTERM)
            try: self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid,signal.SIGKILL)
                self.process.wait()
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr): stream.close()

    def __enter__(self): return self
    def __exit__(self,*args): self.close()
