"""Measure original-effect presence in actual UI-triggered owned output; no equality gate."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
import numpy as np
RATE=48000
def decode(path,tmp):
 out=tmp/(path.stem+'-'+hashlib.sha256(str(path).encode()).hexdigest()[:8]+'.f32')
 subprocess.run(['ffmpeg','-v','error','-i',str(path),'-ar',str(RATE),'-ac','1','-f','f32le',str(out)],check=True)
 return np.fromfile(out,dtype='<f4').astype(np.float64)
def measure(reference,output):
 if len(output)<len(reference) or not len(reference):raise ValueError('Recording shorter than original effect')
 n=1<<(len(output)+len(reference)-2).bit_length()
 dot=np.fft.irfft(np.fft.rfft(output,n)*np.conj(np.fft.rfft(reference,n)),n)[:len(output)-len(reference)+1]
 energy=np.concatenate(([0.],np.cumsum(output*output)));energy=energy[len(reference):]-energy[:-len(reference)]
 ref_energy=float(reference@reference);denom=np.sqrt(np.maximum(energy,0)*ref_energy)
 corr=np.divide(dot,denom,out=np.zeros_like(dot),where=denom>1e-10)
 lag=int(np.argmax(corr));segment=output[lag:lag+len(reference)];gain=float(segment@reference/ref_energy)
 return dict(alignment_seconds=lag/RATE,normalized_correlation=float(corr[lag]),fitted_gain=gain,residual_rms=float(np.sqrt(np.mean((segment-gain*reference)**2))),reference_samples=len(reference),recorded_samples=len(output))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',required=True);p.add_argument('--before',required=True);p.add_argument('--after',required=True);p.add_argument('--out',required=True);p.add_argument('--scope',default='One actually triggered eighth-course q3 correct feedback; alignment search measures effect presence, not full acoustic equality');a=p.parse_args()
 paths={k:Path(getattr(a,k)) for k in ['reference','before','after']}
 with tempfile.TemporaryDirectory() as folder:
  signals={k:decode(v,Path(folder)) for k,v in paths.items()}
  self_check=measure(signals['reference'],signals['reference']);assert abs(self_check['normalized_correlation']-1)<1e-8 and self_check['alignment_seconds']==0
  result={'scope':a.scope,'sample_rate':RATE,'reference_self_check':self_check,'files':{k:{'path':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in paths.items()},'before':measure(signals['reference'],signals['before']),'after':measure(signals['reference'],signals['after']),'limitations':['Mono 48kHz ffmpeg decode; fitted timing/gain are reported, not treated as exact match','Mix/order/latency/volume and other cues remain unverified','Not an RSI mechanism ablation']}
  for key in ['before','after']:
   receipt=json.loads(paths[key].with_suffix('.wav.json').read_text());assert not receipt.get('failure') and receipt['microphone'] is False and len(receipt['ui_actions'])==1 and receipt['samples']>0
   result[key]['owned_capture_receipt']=receipt
 Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['before','after']},ensure_ascii=False))
if __name__=='__main__':main()
