"""Diagnostic decomposition of real overlapping speech/effect; not an equality gate."""
import importlib.util,json,tempfile,hashlib
from pathlib import Path
import numpy as np
B=Path(__file__).resolve().parent;E=B/'evidence/english-unit12-lesson3-v1';R=B.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
spec=importlib.util.spec_from_file_location('audio',B/'compare-feedback-audio.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
q=next(q for q in json.loads((B/'fixture-reference-en-zh-unit12-lesson3-v1.json').read_text())['data']['candidate_course']['lessons'][0]['questions'] if q['id']=='unit12-q13')
paths=dict(speech=R/q['pairs'][0]['audioResource'],effect=R/q['matchedAudioResources'][0]);result=dict(scope='One actual right-click with overlapping original speech and match effect; speech subtraction is diagnostic, not source/native acoustic equality',method='Mono48k FFT alignment fit to original speech, then subtract fitted speech and measure original effect in residual. No masking or pass threshold.',references={k:dict(path=str(p.relative_to(Path.cwd())),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for k,p in paths.items()},limitations=['Unconstrained fitted delay/gain; not calibrated loudness or timing equality','Source play/playing receipt is not a browser acoustic capture','Not an RSI mechanism or product ablation'])
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp);speech=m.decode(paths['speech'],tmp);effect=m.decode(paths['effect'],tmp)
 for folder in ['native-before','native-final']:
  p=E/folder/'matching-right0.wav';data=m.decode(p,tmp);fit=m.measure(speech,data);residual=data.copy();offset=round(fit['alignment_seconds']*m.RATE);residual[offset:offset+len(speech)]-=fit['fitted_gain']*speech
  left=json.loads((E/folder/'matching-left0.wav.json').read_text());right=json.loads(p.with_suffix('.wav.json').read_text())
  assert left['microphone'] is False and right['microphone'] is False and len(left['ui_actions'])==len(right['ui_actions'])==1
  result[folder]=dict(original_speech_fit=fit,original_effect_in_residual=m.measure(effect,residual),left_click_output_rms=left['rms'],left_click_output_peak=left['peak'],left_ui_action=left['ui_actions'],right_ui_action=right['ui_actions'])
(E/'matching-audio-decomposition.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['native-before','native-final']}))
